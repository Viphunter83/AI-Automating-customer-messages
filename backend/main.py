from fastapi import FastAPI
from app import create_app
from app.routes import health, messages, feedback, ws
import logging
import asyncio
import subprocess
import os

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = create_app()

# Include routers
app.include_router(health.router)
app.include_router(messages.router)
app.include_router(feedback.router)
app.include_router(ws.router)

@app.get("/")
async def root():
    return {
        "message": "AI Customer Support API v1.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running"
    }

# Script for manual migrations
async def run_migrations():
    """Run Alembic migrations"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=backend_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info("✅ Migrations completed successfully")
    else:
        logger.error(f"❌ Migration error: {result.stderr}")
    
    return result.returncode == 0

if __name__ == "__main__":
    import uvicorn
    
    # You can run migrations before starting:
    # asyncio.run(run_migrations())
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

