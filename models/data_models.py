"""
Core data models for red-teaming operations.
Contains dataclasses for internal system operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AdversarialPrompt:
    """Represents an adversarial prompt for testing."""
    prompt_id: str
    attack_type: str
    prompt_text: str
    severity_estimate: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionResult:
    """Represents the result of executing an adversarial prompt."""
    prompt_id: str
    prompt_text: str
    response_text: str
    status_code: int
    execution_time_ms: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None


@dataclass
class Vulnerability:
    """Represents an identified vulnerability."""
    vulnerability_id: str
    prompt_id: str
    severity: str
    severity_score: float
    category: str
    description: str
    evidence: str
    remediation_suggestion: str


@dataclass
class VulnerabilityReport:
    """Comprehensive report of all vulnerabilities found in a mission."""
    mission_id: str
    timestamp: datetime
    total_prompts: int
    successful_executions: int
    vulnerabilities_found: int
    vulnerabilities: List[Vulnerability]
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Mission:
    """Represents a red-teaming mission."""
    mission_id: str
    target_system_url: str
    attack_categories: List[str]
    max_prompts: int
    authorization_token: str
    status: str  # pending, running, completed, failed, stopped
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
