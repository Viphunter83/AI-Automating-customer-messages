import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.middleware.logging import LoggingMiddleware
from app.middleware.security import SecurityMiddleware

logger = logging.getLogger(__name__)

# Optional imports for rate limiting
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    logger.warning("slowapi not available, rate limiting disabled")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    # Initialize rate limiter
    if settings.rate_limit_enabled and SLOWAPI_AVAILABLE:
        try:
            limiter = Limiter(
                key_func=get_remote_address,
                default_limits=[
                    f"{settings.rate_limit_per_hour}/hour",
                    f"{settings.rate_limit_per_minute}/minute",
                ],
                storage_uri="memory://",
            )
            # Add stricter rate limit for auth endpoints
            # This will be applied via decorator in routes/auth.py if needed
            app.state.limiter = limiter
            app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
            logger.info("✅ Rate limiting enabled")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize rate limiter: {e}")
            app.state.limiter = None
    else:
        app.state.limiter = None
        if not SLOWAPI_AVAILABLE:
            logger.warning("⚠️ Rate limiting disabled: slowapi not available")
        else:
            logger.info("⚠️ Rate limiting disabled by configuration")

    # Add security middleware first
    app.add_middleware(SecurityMiddleware)

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Lifespan events
    @app.on_event("startup")
    async def startup():
        logger.info("🚀 Starting up application...")

        # Validate configuration before proceeding
        try:
            settings.validate_required_secrets()
        except ValueError as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            if not settings.debug:
                raise RuntimeError(f"Invalid configuration: {e}")
            logger.warning("⚠️ Continuing in debug mode despite configuration issues")

        # Check database connectivity and perform basic query
        try:
            await init_db()
            # Perform a test query to ensure database is responsive
            from app.database import async_session_maker

            async with async_session_maker() as test_session:
                from sqlalchemy import text

                await test_session.execute(text("SELECT 1"))
            logger.info("✅ Database connection established and responsive")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            if not settings.debug:
                raise RuntimeError(f"Database connection failed: {e}")
            logger.warning("⚠️ Continuing in debug mode despite database issues")

        from sqlalchemy.ext.asyncio import AsyncSession

        from app.database import async_session_maker
        from app.services.reminder_scheduler import ReminderScheduler
        from app.services.response_manager import ResponseManager

        # Initialize default templates
        try:
            async with async_session_maker() as session:
                response_manager = ResponseManager(session)
                await response_manager.initialize_default_templates()
            logger.info("✅ Default templates initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize templates: {e}")
            if not settings.debug:
                raise

        # Check OpenAI API availability (non-blocking)
        try:
            from app.services.ai_classifier import AIClassifier

            ai_classifier = AIClassifier()
            # Quick test - just check if client is initialized
            if not ai_classifier.client:
                raise ValueError("OpenAI client not initialized")
            logger.info("✅ OpenAI API client initialized")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI API check failed: {e}")
            if not settings.debug:
                logger.error("OpenAI API is required for production")
            # Don't fail startup, but log warning

        # Check Redis cache availability (non-blocking)
        try:
            from app.utils.redis_cache import get_redis_cache

            redis_cache = await get_redis_cache()
            # Test Redis connection
            test_client = await redis_cache._get_client()
            if test_client:
                await test_client.ping()
                logger.info("✅ Redis cache connected")
            else:
                logger.info("✅ Redis cache unavailable, using in-memory fallback")
        except Exception as e:
            logger.warning(f"⚠️ Redis cache check failed: {e}, will use in-memory fallback")
            # Don't fail startup - fallback to in-memory cache

        # Start reminder scheduler
        try:
            reminder_scheduler = ReminderScheduler()
            reminder_scheduler.start()
            app.state.reminder_scheduler = reminder_scheduler
            logger.info("✅ Reminder scheduler started")
        except Exception as e:
            logger.error(f"❌ Failed to start reminder scheduler: {e}")
            if not settings.debug:
                raise

        # Initialize Telegram bot (if enabled)
        if settings.telegram_enabled and settings.telegram_bot_token:
            try:
                from app.integrations.telegram.bot import TelegramBot
                from app.routes.telegram import set_telegram_bot
                
                telegram_bot = TelegramBot(token=settings.telegram_bot_token)
                set_telegram_bot(telegram_bot)
                
                # Start bot in polling mode (for development)
                # In production, use webhook mode
                if not settings.telegram_webhook_url:
                    # Start polling in background task
                    async def start_bot():
                        try:
                            await telegram_bot.start_polling()
                        except Exception as e:
                            logger.error(f"Telegram bot polling error: {e}", exc_info=True)
                    
                    import asyncio
                    asyncio.create_task(start_bot())
                    logger.info("✅ Telegram bot started (polling mode)")
                else:
                    # Setup webhook for production
                    telegram_bot.setup_webhook(
                        webhook_url=settings.telegram_webhook_url,
                        secret_token=settings.telegram_webhook_secret,
                    )
                    logger.info(f"✅ Telegram bot webhook configured: {settings.telegram_webhook_url}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Telegram bot: {e}")
                if not settings.debug:
                    logger.warning("⚠️ Continuing without Telegram bot")
                else:
                    raise

        logger.info("✅ Application startup complete")

    @app.on_event("shutdown")
    async def shutdown():
        logger.info("🛑 Shutting down application...")

        # Stop reminder scheduler
        if hasattr(app.state, "reminder_scheduler"):
            app.state.reminder_scheduler.stop()

        await close_db()

        # Close Redis cache connection
        try:
            from app.utils.redis_cache import close_redis_cache
            await close_redis_cache()
        except Exception as e:
            logger.debug(f"Redis cache cleanup: {e}")

        # Stop Telegram bot
        try:
            from app.routes.telegram import get_telegram_bot
            telegram_bot = get_telegram_bot()
            if telegram_bot:
                await telegram_bot.stop_polling()
        except Exception as e:
            logger.debug(f"Telegram bot cleanup: {e}")

    return app
