from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
from functools import lru_cache
import json
import os

class Settings(BaseSettings):
    # App
    app_name: str = "AI Customer Support"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database
    database_url: str
    supabase_url: str
    supabase_anon_key: str
    
    # OpenAI
    openai_api_key: str
    openai_api_base: str = "https://api.proxyapi.ru/openai/v1"
    openai_model: str = "gpt-4o-mini"
    
    # AI Settings
    ai_classification_timeout: int = 30
    ai_confidence_threshold: float = 0.85
    
    # Security
    secret_key: str
    allowed_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000"
    
    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try to parse as JSON first
            if v.startswith('['):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fallback to comma-separated
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

