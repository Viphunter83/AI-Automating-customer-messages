from fastapi import FastAPI
from app import create_app
from app.routes import health, messages, feedback, ws, admin, search, reminders, dialogs, auth, telegram, monitoring, operator, unread
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
app.include_router(auth.router)  # Authentication routes
app.include_router(messages.router)
app.include_router(feedback.router)
app.include_router(admin.router)
app.include_router(search.router)
app.include_router(reminders.router)
app.include_router(dialogs.router)
app.include_router(ws.router)
app.include_router(telegram.router)
app.include_router(monitoring.router)  # Monitoring and metrics
app.include_router(operator.router)  # Operator endpoints
app.include_router(unread.router)  # Unread messages tracking

@app.get("/")
async def root():
    return {
        "message": "AI Customer Support API v1.0",
        "docs": "/docs",
        "health": "/health",
        "admin": "/api/admin",
        "search": "/api/search",
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

