from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db, close_db
from app.middleware.logging import LoggingMiddleware
from app.middleware.security import SecurityMiddleware
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    
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
        await init_db()
        
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.database import async_session_maker
        from app.services.response_manager import ResponseManager
        from app.services.reminder_scheduler import ReminderScheduler
        
        # Initialize default templates
        async with async_session_maker() as session:
            response_manager = ResponseManager(session)
            await response_manager.initialize_default_templates()
        
        # Start reminder scheduler
        reminder_scheduler = ReminderScheduler()
        reminder_scheduler.start()
        app.state.reminder_scheduler = reminder_scheduler
        
        logger.info("✅ Application startup complete")
    
    @app.on_event("shutdown")
    async def shutdown():
        logger.info("🛑 Shutting down application...")
        
        # Stop reminder scheduler
        if hasattr(app.state, 'reminder_scheduler'):
            app.state.reminder_scheduler.stop()
        
        await close_db()
    
    return app
