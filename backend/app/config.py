import json
import logging
import os
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # App
    app_name: str = "AI Customer Support"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Database - Supabase (прямое PostgreSQL подключение через параметры)
    # Конфигурация соответствует примеру заказчика
    supabase_url: str = ""  # URL для REST API Gateway (http://kong:8000 или внешний URL)
    supabase_key: str = ""  # Role Key (для REST API, опционально)
    supabase_user: str = "postgres"  # Пользователь БД
    supabase_password: str = ""  # Пароль БД (может быть пустым, если не требуется)
    supabase_host: str = ""  # Имя сервиса БД в Docker сети (если пусто, используется "db")
    supabase_port: int = 5437  # Порт БД (обязательно 5437!)
    supabase_db: str = "postgres"  # Имя базы данных
    database_echo: bool = False  # Логирование SQL запросов
    
    # Legacy: DATABASE_URL для обратной совместимости (если указан, используется напрямую)
    database_url: str = ""

    # OpenAI
    openai_api_key: str
    openai_api_base: str = "https://api.proxyapi.ru/openai/v1"
    openai_model: str = "gpt-4o-mini"

    # AI Settings
    ai_classification_timeout: int = 30
    ai_confidence_threshold: float = 0.85

    # Security
    secret_key: str
    allowed_origins: Union[
        str, List[str]
    ] = "http://localhost:3000,http://localhost:8000"

    # Redis (optional, falls back to in-memory cache if not available)
    redis_url: str = "redis://localhost:6379/0"

    # Telegram Bot (optional, for testing before CRM integration)
    telegram_bot_token: Optional[str] = None
    telegram_enabled: bool = False
    telegram_webhook_url: Optional[str] = None
    telegram_webhook_secret: Optional[str] = None

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60  # Requests per minute per IP
    rate_limit_per_hour: int = 1000  # Requests per hour per IP
    rate_limit_message_per_minute: int = 10  # Messages per minute per client_id

    # Message Delivery Delays (for better UX - simulate "typing...")
    response_delay_seconds: float = (
        3.0  # Delay before sending bot response (2-5 seconds)
    )
    farewell_delay_seconds: float = 10.0  # Delay before sending farewell message
    delays_enabled: bool = True  # Enable/disable delays

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try to parse as JSON first
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fallback to comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["http://localhost:3000", "http://localhost:8000"]

    def validate_required_secrets(self) -> None:
        """
        Validate that all required secrets are set and not using default/placeholder values.
        Raises ValueError if any required secret is missing or invalid.
        """
        errors = []

        # Check database configuration (соответствует примеру заказчика)
        # Вариант 1: DATABASE_URL указан напрямую
        if self.database_url:
            if not self.database_url.startswith("postgresql"):
                errors.append("DATABASE_URL must start with 'postgresql' or 'postgresql+asyncpg'")
        
        # Вариант 2: Используются параметры Supabase
        # В примере заказчика SUPABASE_HOST и SUPABASE_PASSWORD могут быть пустыми
        # Если SUPABASE_HOST пустой - используется "db" по умолчанию
        # Если SUPABASE_PASSWORD пустой - подключаемся без пароля (если разрешено)
        else:
            # Проверяем только обязательные параметры
            if not self.supabase_db:
                errors.append(
                    "SUPABASE_DB is required. "
                    "Get it from Supabase Service → Environment Variables → POSTGRES_DB"
                )

        # Check OpenAI API key
        if (
            not self.openai_api_key
            or self.openai_api_key.startswith("sk-xxxxx")
            or len(self.openai_api_key) < 10
        ):
            errors.append("OPENAI_API_KEY is required and must be a valid API key")

        # Check secret key
        if (
            not self.secret_key
            or self.secret_key
            in [
                "dev-secret-key-change-in-production",
                "your-secret-key-here-change-in-production",
                "change-in-production",
            ]
            or len(self.secret_key) < 32
        ):
            errors.append(
                "SECRET_KEY is required and must be at least 32 characters long"
            )

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  - {e}" for e in errors
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("✅ Configuration validation passed")


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    # Validate secrets on first load
    try:
        settings.validate_required_secrets()
    except ValueError as e:
        # In production, fail fast
        if not settings.debug:
            raise
        # In development, log warning but continue
        logger.warning(f"⚠️ Configuration warning: {e}")
    return settings
