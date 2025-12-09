import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def build_database_url() -> str:
    """
    Построить DATABASE_URL из параметров подключения Supabase
    
    Соответствует примеру заказчика:
    - Если DATABASE_URL указан напрямую - используется он
    - Иначе строится из параметров Supabase
    - Если SUPABASE_HOST пустой - используется "db" по умолчанию
    - Если SUPABASE_PASSWORD пустой - подключается без пароля (если разрешено)
    """
    # Если DATABASE_URL указан напрямую - используем его
    if settings.database_url:
        logger.info("Using DATABASE_URL from environment")
        return settings.database_url
    
    # Определяем хост (если пустой, используем "db" по умолчанию)
    host = settings.supabase_host if settings.supabase_host else "db"
    
    # Строим URL из параметров Supabase
    # Если пароль пустой, подключаемся без пароля (как в примере заказчика)
    if settings.supabase_password:
        database_url = (
            f"postgresql+asyncpg://{settings.supabase_user}:{settings.supabase_password}"
            f"@{host}:{settings.supabase_port}/{settings.supabase_db}"
        )
    else:
        # Подключение без пароля (если разрешено настройками БД)
        database_url = (
            f"postgresql+asyncpg://{settings.supabase_user}"
            f"@{host}:{settings.supabase_port}/{settings.supabase_db}"
        )
    
    logger.info(f"Built DATABASE_URL from Supabase parameters: {host}:{settings.supabase_port}/{settings.supabase_db}")
    return database_url


# Create async engine
database_url = build_database_url()
engine = create_async_engine(
    database_url,
    echo=settings.database_echo or settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
)

# Session factory
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base class for all models
Base = declarative_base()


# Dependency for FastAPI
async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")
