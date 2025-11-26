from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
from app.database import Base
from app.models.database import *

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    
    # Convert asyncpg URL to psycopg2 for synchronous alembic operations
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg2")
    elif url.startswith("postgresql://") and "+" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    
    # Get database URL and convert asyncpg to psycopg2 for synchronous migrations
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://support_user:support_pass@localhost:5432/ai_support"
    )
    
    # Convert asyncpg URL to psycopg2 for synchronous alembic operations
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "+psycopg2")
    elif db_url.startswith("postgresql://") and "+" not in db_url:
        # Add psycopg2 driver if not specified
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
    elif db_url.startswith("postgresql+psycopg2://"):
        pass  # Already psycopg2
    
    configuration["sqlalchemy.url"] = db_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
