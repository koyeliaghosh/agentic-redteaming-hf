"""
Main application entry point for the Agentic AI Red-Teaming Assistant.
Initializes FastAPI application and starts the server.
"""

from fastapi import FastAPI
from config import get_config

# Initialize configuration on startup
config = get_config()

# Create FastAPI application
app = FastAPI(
    title="Agentic AI Red-Teaming Assistant",
    description="Multi-agent system for automated security testing of AI systems",
    version="1.0.0",
)


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
