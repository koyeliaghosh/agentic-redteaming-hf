"""
Test script for report generation and local storage functionality.
Verifies task 9 implementation.
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, '.')

from agents.coordinator import CoordinatorAgent
from models.data_models import (
    Mission, VulnerabilityReport, Vulnerability,
    AdversarialPrompt, ExecutionResult
)
from config import Config


def test_report_to_dict():
    """Test conversion of VulnerabilityReport to dictionary."""
    print("Testing report to dictionary conversion...")
    
    try:
        # Create test data
        vulnerability = Vulnerability(
            vulnerability_id="vuln_001",
            prompt_id="prompt_001",
            severity="HIGH",
            severity_score=8.5,
            category="Prompt Injection",
            description="Test vulnerability",
            evidence="Test evidence",
            remediation_suggestion="Test remediation"
        )
        
        report = VulnerabilityReport(
            mission_id="test_mission_001",
            timestamp=datetime.utcnow(),
            total_prompts=10,
            successful_executions=8,
            vulnerabilities_found=1,
            vulnerabilities=[vulnerability],
            summary="Test summary",
            metadata={"test_key": "test_value"}
        )
        
        # Create coordinator with temp config
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                huggingface_api_key="hf_test_key_placeholder",
                results_path=tmpdir
            )
            coordinator = CoordinatorAgent(config)
            
            # Convert to dict
            report_dict = coordinator._report_to_dict(report)
            
            # Verify structure
            assert "mission_id" in report_dict
            assert "timestamp" in report_dict
            assert "vulnerabilities" in report_dict
            assert len(report_dict["vulnerabilities"]) == 1
            assert report_dict["vulnerabilities"][0]["vulnerability_id"] == "vuln_001"
            
            coordinator.close()
            
        print("✓ Report to dictionary conversion works")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_save_report_local():
    """Test saving report to local file storage."""
    print("\nTesting local report storage...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config with temp directory
            config = Config(
                huggingface_api_key="hf_test_key_placeholder",
                results_path=tmpdir
            )
            coordinator = CoordinatorAgent(config)
            
            # Create test report
            report = VulnerabilityReport(
                mission_id="test_mission_002",
                timestamp=datetime.utcnow(),
                total_prompts=5,
                successful_executions=5,
                vulnerabilities_found=0,
                vulnerabilities=[],
                summary="Test mission with no vulnerabilities",
                metadata={"test": True}
            )
            
            # Save report
            filepath = coordinator._save_report_local(report)
            
            # Verify file exists
            assert os.path.exists(filepath), f"Report file not created: {filepath}"
            print(f"✓ Report file created: {filepath}")
            
            # Verify filename pattern
            filename = os.path.basename(filepath)
            assert filename.startswith("report_test_mission_002_")
            assert filename.endswith(".json")
            print(f"✓ Filename pattern correct: {filename}")
            
            # Verify file content
            with open(filepath, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data["mission_id"] == "test_mission_002"
            assert loaded_data["total_prompts"] == 5
            assert loaded_data["vulnerabilities_found"] == 0
            print("✓ Report content correct")
            
            # Verify JSON is pretty-printed (human-readable)
            with open(filepath, 'r') as f:
                content = f.read()
            assert "\n" in content, "JSON should be pretty-printed"
            assert "  " in content, "JSON should have indentation"
            print("✓ Report is human-readable (pretty-printed)")
            
            coordinator.close()
            
        print("✓ Local report storage works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_mission_summary():
    """Test mission summary generation."""
    print("\nTesting mission summary generation...")
    
    try:
        config = Config(
            huggingface_api_key="hf_test_key_placeholder"
        )
        coordinator = CoordinatorAgent(config)
        
        # Test with no vulnerabilities
        mission = Mission(
            mission_id="test_003",
            target_system_url="http://test.example.com",
            attack_categories=["Prompt Injection", "Jailbreak"],
            max_prompts=10,
            authorization_token="test_token",
            status="completed"
        )
        
        vulnerabilities = []
        
        summary = coordinator._generate_mission_summary(
            mission=mission,
            total_prompts=10,
            successful_executions=10,
            vulnerabilities_found=0,
            vulnerabilities=vulnerabilities
        )
        
        assert "test_003" in summary
        assert "No vulnerabilities" in summary
        print("✓ Summary for clean mission correct")
        
        # Test with vulnerabilities
        vulnerabilities = [
            Vulnerability(
                vulnerability_id="v1",
                prompt_id="p1",
                severity="CRITICAL",
                severity_score=9.5,
                category="Test",
                description="Test",
                evidence="Test",
                remediation_suggestion="Test"
            ),
            Vulnerability(
                vulnerability_id="v2",
                prompt_id="p2",
                severity="HIGH",
                severity_score=7.5,
                category="Test",
                description="Test",
                evidence="Test",
                remediation_suggestion="Test"
            )
        ]
        
        summary = coordinator._generate_mission_summary(
            mission=mission,
            total_prompts=10,
            successful_executions=10,
            vulnerabilities_found=2,
            vulnerabilities=vulnerabilities
        )
        
        assert "2 vulnerabilities" in summary
        assert "CRITICAL" in summary
        assert "immediate attention" in summary
        print("✓ Summary for vulnerable mission correct")
        
        coordinator.close()
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_report_with_metadata():
    """Test comprehensive report generation with metadata."""
    print("\nTesting comprehensive report generation...")
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                huggingface_api_key="hf_test_key_placeholder",
                results_path=tmpdir,
                hf_llm_model="test/model",
                hf_embed_model="test/embed"
            )
            coordinator = CoordinatorAgent(config)
            
            # Create test data
            mission = Mission(
                mission_id="test_004",
                target_system_url="http://test.example.com",
                attack_categories=["Prompt Injection"],
                max_prompts=5,
                authorization_token="test_token",
                status="completed",
                completed_at=datetime.utcnow()
            )
            
            prompts = [
                AdversarialPrompt(
                    prompt_id=f"p{i}",
                    attack_type="Prompt Injection",
                    prompt_text=f"Test prompt {i}",
                    severity_estimate="MEDIUM"
                )
                for i in range(5)
            ]
            
            results = [
                ExecutionResult(
                    prompt_id=f"p{i}",
                    prompt_text=f"Test prompt {i}",
                    response_text=f"Test response {i}",
                    status_code=200,
                    execution_time_ms=100
                )
                for i in range(5)
            ]
            
            base_report = VulnerabilityReport(
                mission_id="test_004",
                timestamp=datetime.utcnow(),
                total_prompts=5,
                successful_executions=5,
                vulnerabilities_found=0,
                vulnerabilities=[],
                summary="Base summary",
                metadata={}
            )
            
            # Set mission start time
            coordinator.mission_start_time = datetime.utcnow()
            
            # Generate comprehensive report
            report = coordinator._generate_report(
                mission=mission,
                prompts=prompts,
                results=results,
                report=base_report
            )
            
            # Verify metadata
            assert "model_versions" in report.metadata
            assert report.metadata["model_versions"]["llm_model"] == "test/model"
            assert report.metadata["model_versions"]["embed_model"] == "test/embed"
            print("✓ Model versions in metadata")
            
            assert "execution_time_seconds" in report.metadata
            print("✓ Execution time in metadata")
            
            assert "prompts_generated" in report.metadata
            assert report.metadata["prompts_generated"] == 5
            print("✓ Prompt counts in metadata")
            
            assert "configuration" in report.metadata
            print("✓ Configuration in metadata")
            
            # Verify summary was generated
            assert len(report.summary) > 50
            assert "test_004" in report.summary
            print("✓ Summary generated correctly")
            
            coordinator.close()
            
        print("✓ Comprehensive report generation works")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Report Generation and Storage Tests (Task 9)")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Report to Dict", test_report_to_dict()))
    results.append(("Save Report Local", test_save_report_local()))
    results.append(("Generate Summary", test_generate_mission_summary()))
    results.append(("Generate Report with Metadata", test_generate_report_with_metadata()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
