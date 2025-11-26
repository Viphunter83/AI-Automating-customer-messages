from fastapi import FastAPI
from app import create_app
from app.routes import health, messages, feedback
import logging

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

@app.get("/")
async def root():
    return {
        "message": "AI Customer Support API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

