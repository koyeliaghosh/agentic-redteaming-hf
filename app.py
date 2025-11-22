"""
Main application entry point for the Agentic AI Red-Teaming Assistant.
Initializes FastAPI application and starts the server.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from config import get_config
from pathlib import Path

# Initialize configuration on startup
config = get_config()

# Create FastAPI application
app = FastAPI(
    title="Agentic AI Red-Teaming Assistant",
    description="Multi-agent system for automated security testing of AI systems",
    version="1.0.0",
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the frontend."""
    static_file = static_dir / "index.html"
    if static_file.exists():
        return FileResponse(str(static_file))
    return {"message": "Welcome to Agentic AI Red-Teaming Assistant API"}


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "agentic-redteaming-assistant",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=config.api_host,
        port=config.api_port,
        reload=False
    )
