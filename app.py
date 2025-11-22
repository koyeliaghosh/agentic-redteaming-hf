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


@app.post("/demo/mock-ai")
async def mock_ai_endpoint(request: dict):
    """Mock AI endpoint for demo purposes."""
    return {
        "response": "This is a mock AI response for demonstration purposes.",
        "model": "demo-model",
        "usage": {"tokens": 42}
    }


# Demo mission endpoints (simplified for demonstration)
from datetime import datetime
import uuid
from typing import Dict
from models.api_models import MissionRequest, MissionResponse

# In-memory storage for demo missions
demo_missions: Dict[str, dict] = {}


@app.post("/missions/start", response_model=MissionResponse)
async def start_mission(request: MissionRequest):
    """Start a new red-teaming mission (demo version)."""
    mission_id = f"mission_{uuid.uuid4().hex[:8]}"
    
    # Store mission info
    demo_missions[mission_id] = {
        "mission_id": mission_id,
        "status": "running",
        "created_at": datetime.now().isoformat(),
        "progress": 0.0,
        "vulnerabilities_found": 0,
        "target_url": str(request.target_system_url),
        "categories": request.attack_categories,
        "max_prompts": request.max_prompts
    }
    
    return MissionResponse(
        mission_id=mission_id,
        status="running",
        created_at=datetime.now().isoformat(),
        progress=0.0
    )


@app.get("/missions/{mission_id}/status")
async def get_mission_status(mission_id: str):
    """Get the status of a mission (demo version)."""
    if mission_id not in demo_missions:
        return {"error": "Mission not found"}, 404
    
    mission = demo_missions[mission_id]
    
    # Simulate progress
    if mission["progress"] < 1.0:
        mission["progress"] = min(1.0, mission["progress"] + 0.1)
        mission["vulnerabilities_found"] = int(mission["progress"] * 5)
        
        if mission["progress"] >= 1.0:
            mission["status"] = "completed"
    
    return {
        "mission_id": mission_id,
        "status": mission["status"],
        "progress": mission["progress"],
        "vulnerabilities_found": mission["vulnerabilities_found"],
        "created_at": mission["created_at"]
    }


@app.get("/missions/{mission_id}/report")
async def get_mission_report(mission_id: str):
    """Get the vulnerability report for a mission (demo version)."""
    if mission_id not in demo_missions:
        return {"error": "Mission not found"}, 404
    
    mission = demo_missions[mission_id]
    
    return {
        "mission_id": mission_id,
        "status": mission["status"],
        "target_url": mission["target_url"],
        "attack_categories": mission["categories"],
        "total_prompts": mission["max_prompts"],
        "vulnerabilities_found": mission["vulnerabilities_found"],
        "vulnerabilities": [
            {
                "id": f"vuln_{i}",
                "severity": "HIGH" if i % 3 == 0 else "MEDIUM",
                "category": mission["categories"][i % len(mission["categories"])],
                "description": f"Successfully bypassed safety filters using {mission['categories'][i % len(mission['categories'])]} technique",
                "evidence": f"Model response: 'I will comply with your request...' - Safety guardrails circumvented with adversarial prompt #{i+1}"
            }
            for i in range(mission["vulnerabilities_found"])
        ],
        "summary": f"Found {mission['vulnerabilities_found']} vulnerabilities in demo mission"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=config.api_host,
        port=config.api_port,
        reload=False
    )
