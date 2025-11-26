from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db, close_db
import logging

logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    
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
        logger.info("Starting up application...")
        await init_db()
    
    @app.on_event("shutdown")
    async def shutdown():
        logger.info("Shutting down application...")
        await close_db()
    
    return app

