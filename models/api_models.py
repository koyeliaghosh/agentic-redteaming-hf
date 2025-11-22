"""
Pydantic models for API requests and responses.
Contains validation models for FastAPI endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl, validator


class MissionRequest(BaseModel):
    """Request model for creating a new red-teaming mission."""
    target_system_url: HttpUrl = Field(
        ...,
        description="URL of the target AI system to test"
    )
    attack_categories: List[str] = Field(
        ...,
        min_items=1,
        description="List of attack categories to test (e.g., 'prompt_injection', 'jailbreak')"
    )
    max_prompts: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of adversarial prompts to generate and execute"
    )
    authorization_token: str = Field(
        ...,
        min_length=1,
        description="Authorization token for mission execution"
    )

    @validator('attack_categories')
    def validate_attack_categories(cls, v):
        """Validate that attack categories are from allowed list."""
        allowed_categories = {
            'prompt_injection',
            'jailbreak',
            'data_extraction',
            'bias_exploitation',
            'hallucination_induction',
            'context_confusion',
            'role_manipulation'
        }
        for category in v:
            if category not in allowed_categories:
                raise ValueError(
                    f"Invalid attack category: {category}. "
                    f"Allowed categories: {', '.join(sorted(allowed_categories))}"
                )
        return v

    class Config:
        schema_extra = {
            "example": {
                "target_system_url": "https://api.example.com/chat",
                "attack_categories": ["prompt_injection", "jailbreak"],
                "max_prompts": 20,
                "authorization_token": "your_secret_token_here"
            }
        }


class MissionResponse(BaseModel):
    """Response model for mission creation and status."""
    mission_id: str = Field(..., description="Unique identifier for the mission")
    status: str = Field(
        ...,
        description="Current status: pending, running, completed, failed, stopped"
    )
    created_at: str = Field(..., description="ISO 8601 timestamp of mission creation")
    progress: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Mission progress as a fraction (0.0 to 1.0)"
    )
    results: Optional[Dict[str, Any]] = Field(
        None,
        description="Vulnerability report results (available when status is completed)"
    )

    class Config:
        schema_extra = {
            "example": {
                "mission_id": "mission_abc123",
                "status": "running",
                "created_at": "2025-11-12T10:30:00Z",
                "progress": 0.45,
                "results": None
            }
        }


class StopRequest(BaseModel):
    """Request model for emergency stop."""
    authorization_token: str = Field(
        ...,
        min_length=1,
        description="Authorization token to confirm stop request"
    )

    class Config:
        schema_extra = {
            "example": {
                "authorization_token": "your_secret_token_here"
            }
        }


class StopResponse(BaseModel):
    """Response model for stop request."""
    status: str = Field(..., description="Status of the stop request")
    message: str = Field(..., description="Human-readable message about the stop action")

    class Config:
        schema_extra = {
            "example": {
                "status": "stopped",
                "message": "Emergency stop activated. All missions will terminate."
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Overall system status: healthy, degraded, unhealthy")
    services: Dict[str, str] = Field(
        ...,
        description="Status of individual services (e.g., huggingface_api, faiss_index)"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp of health check")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "services": {
                    "huggingface_api": "connected",
                    "faiss_index": "loaded",
                    "storage": "available"
                },
                "timestamp": "2025-11-12T10:30:00Z"
            }
        }
