"""
Configuration management for the Agentic AI Red-Teaming Assistant.
Uses Pydantic for validation and environment variables for configuration.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """
    Application configuration loaded from environment variables.
    Validates all required settings on startup.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Hugging Face Configuration (FREE TIER)
    huggingface_api_key: str = Field(
        ...,
        description="Hugging Face API key for model access"
    )
    hf_llm_model: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.2",
        description="Hugging Face LLM model for text generation"
    )
    hf_embed_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Hugging Face embedding model"
    )
    hf_base_url: str = Field(
        default="https://api-inference.huggingface.co/models",
        description="Base URL for Hugging Face Inference API"
    )
    
    # Storage Configuration (LOCAL - NO S3)
    results_path: str = Field(
        default="./data/reports",
        description="Local directory for storing vulnerability reports"
    )
    logs_path: str = Field(
        default="./data/logs",
        description="Local directory for storing logs"
    )
    faiss_index_path: str = Field(
        default="./data/faiss_index",
        description="Local directory for FAISS vector store"
    )
    
    # Safety Configuration
    stop_test: bool = Field(
        default=False,
        description="Emergency stop flag - blocks all missions when True"
    )
    max_mission_duration_minutes: int = Field(
        default=60,
        description="Maximum duration for a single mission in minutes"
    )
    
    # Execution Configuration
    executor_timeout_seconds: int = Field(
        default=45,
        description="Timeout for individual prompt execution"
    )
    executor_delay_seconds: float = Field(
        default=2.0,
        description="Delay between prompt executions to respect rate limits"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed operations"
    )
    
    # API Configuration
    api_port: int = Field(
        default=8080,
        description="Port for the FastAPI application"
    )
    api_host: str = Field(
        default="0.0.0.0",
        description="Host address for the FastAPI application"
    )
    
    # Authorization
    authorized_tokens: str = Field(
        default="",
        description="Comma-separated list of authorized tokens"
    )
    
    @field_validator("huggingface_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key is not empty and has correct format."""
        if not v or v.strip() == "":
            raise ValueError("HUGGINGFACE_API_KEY must be provided")
        if not v.startswith("hf_"):
            raise ValueError("HUGGINGFACE_API_KEY must start with 'hf_'")
        return v
    
    @field_validator("max_mission_duration_minutes")
    @classmethod
    def validate_mission_duration(cls, v: int) -> int:
        """Validate mission duration is reasonable."""
        if v <= 0 or v > 180:
            raise ValueError("max_mission_duration_minutes must be between 1 and 180")
        return v
    
    @field_validator("executor_timeout_seconds")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is reasonable."""
        if v <= 0 or v > 300:
            raise ValueError("executor_timeout_seconds must be between 1 and 300")
        return v
    
    def get_authorized_tokens_list(self) -> list[str]:
        """Parse and return list of authorized tokens."""
        if not self.authorized_tokens:
            return []
        return [token.strip() for token in self.authorized_tokens.split(",") if token.strip()]
    
    def is_token_authorized(self, token: str) -> bool:
        """Check if a token is in the authorized list."""
        authorized = self.get_authorized_tokens_list()
        if not authorized:
            return True  # If no tokens configured, allow all
        return token in authorized


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create the global configuration instance.
    Validates configuration on first access.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config() -> Config:
    """
    Force reload of configuration from environment.
    Useful for testing or runtime configuration updates.
    """
    global _config
    _config = Config()
    return _config
