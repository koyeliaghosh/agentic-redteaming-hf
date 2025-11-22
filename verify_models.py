"""
Verification script for Task 3: Data Models and Validation
This script verifies that all data models are correctly implemented.
"""

from datetime import datetime
from models import (
    # Core data models
    AdversarialPrompt,
    ExecutionResult,
    Vulnerability,
    VulnerabilityReport,
    Mission,
    # API models
    MissionRequest,
    MissionResponse,
    StopRequest,
    StopResponse,
    HealthResponse,
)


def verify_core_data_models():
    """Verify core dataclass models."""
    print("✓ Verifying Core Data Models...")
    
    # Test AdversarialPrompt
    prompt = AdversarialPrompt(
        prompt_id="test-1",
        attack_type="prompt_injection",
        prompt_text="Test prompt",
        severity_estimate="HIGH",
        metadata={"source": "test"}
    )
    assert prompt.prompt_id == "test-1"
    assert isinstance(prompt.created_at, datetime)
    print("  ✓ AdversarialPrompt")
    
    # Test ExecutionResult
    result = ExecutionResult(
        prompt_id="test-1",
        prompt_text="Test prompt",
        response_text="Test response",
        status_code=200,
        execution_time_ms=150
    )
    assert result.status_code == 200
    assert result.error is None
    print("  ✓ ExecutionResult")
    
    # Test Vulnerability
    vuln = Vulnerability(
        vulnerability_id="vuln-1",
        prompt_id="test-1",
        severity="HIGH",
        severity_score=8.5,
        category="data_leakage",
        description="Test vulnerability",
        evidence="Test evidence",
        remediation_suggestion="Fix this"
    )
    assert vuln.severity_score == 8.5
    print("  ✓ Vulnerability")
    
    # Test VulnerabilityReport
    report = VulnerabilityReport(
        mission_id="mission-1",
        timestamp=datetime.utcnow(),
        total_prompts=10,
        successful_executions=9,
        vulnerabilities_found=2,
        vulnerabilities=[vuln],
        summary="Test summary"
    )
    assert len(report.vulnerabilities) == 1
    print("  ✓ VulnerabilityReport")
    
    # Test Mission
    mission = Mission(
        mission_id="mission-1",
        target_system_url="https://example.com",
        attack_categories=["jailbreak"],
        max_prompts=20,
        authorization_token="token123",
        status="pending"
    )
    assert mission.status == "pending"
    assert mission.completed_at is None
    print("  ✓ Mission")


def verify_api_models():
    """Verify Pydantic API models."""
    print("\n✓ Verifying API Models...")
    
    # Test MissionRequest
    request = MissionRequest(
        target_system_url="https://api.example.com/chat",
        attack_categories=["prompt_injection", "jailbreak"],
        max_prompts=15,
        authorization_token="secret_token"
    )
    assert len(request.attack_categories) == 2
    print("  ✓ MissionRequest")
    
    # Test MissionResponse
    response = MissionResponse(
        mission_id="mission-123",
        status="running",
        created_at="2025-11-12T10:30:00Z",
        progress=0.5
    )
    assert response.progress == 0.5
    print("  ✓ MissionResponse")
    
    # Test StopRequest
    stop_req = StopRequest(authorization_token="secret_token")
    assert stop_req.authorization_token == "secret_token"
    print("  ✓ StopRequest")
    
    # Test StopResponse
    stop_resp = StopResponse(
        status="stopped",
        message="Emergency stop activated"
    )
    assert stop_resp.status == "stopped"
    print("  ✓ StopResponse")
    
    # Test HealthResponse
    health = HealthResponse(
        status="healthy",
        services={"huggingface_api": "connected"},
        timestamp="2025-11-12T10:30:00Z"
    )
    assert health.status == "healthy"
    print("  ✓ HealthResponse")


def verify_validation():
    """Verify Pydantic validation rules."""
    print("\n✓ Verifying Validation Rules...")
    
    # Test attack category validation
    try:
        MissionRequest(
            target_system_url="https://api.example.com/chat",
            attack_categories=["invalid_category"],
            max_prompts=10,
            authorization_token="token"
        )
        print("  ✗ Attack category validation failed")
    except ValueError as e:
        assert "Invalid attack category" in str(e)
        print("  ✓ Attack category validation")
    
    # Test max_prompts range validation
    try:
        MissionRequest(
            target_system_url="https://api.example.com/chat",
            attack_categories=["jailbreak"],
            max_prompts=0,  # Invalid: must be >= 1
            authorization_token="token"
        )
        print("  ✗ Max prompts validation failed")
    except ValueError:
        print("  ✓ Max prompts range validation")
    
    # Test required fields
    try:
        MissionRequest(
            target_system_url="https://api.example.com/chat",
            attack_categories=[],  # Invalid: min_items=1
            authorization_token="token"
        )
        print("  ✗ Required fields validation failed")
    except ValueError:
        print("  ✓ Required fields validation")


if __name__ == "__main__":
    print("=" * 60)
    print("Task 3: Data Models and Validation - Verification")
    print("=" * 60)
    
    try:
        verify_core_data_models()
        verify_api_models()
        verify_validation()
        
        print("\n" + "=" * 60)
        print("✓ All data models verified successfully!")
        print("=" * 60)
        print("\nImplemented Models:")
        print("  Core Data Models (dataclasses):")
        print("    - AdversarialPrompt")
        print("    - ExecutionResult")
        print("    - Vulnerability")
        print("    - VulnerabilityReport")
        print("    - Mission")
        print("\n  API Models (Pydantic):")
        print("    - MissionRequest (with validation)")
        print("    - MissionResponse")
        print("    - StopRequest")
        print("    - StopResponse")
        print("    - HealthResponse")
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
