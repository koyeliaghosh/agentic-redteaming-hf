"""
Test script for CoordinatorAgent implementation.
Verifies basic functionality without requiring external API calls.
"""

import asyncio
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from agents.coordinator import CoordinatorAgent
from models.data_models import Mission
from config import Config


def test_coordinator_initialization():
    """Test that CoordinatorAgent initializes correctly."""
    print("Testing CoordinatorAgent initialization...")
    
    try:
        # Create minimal config for testing
        config = Config(
            huggingface_api_key="hf_test_key_placeholder",
            stop_test=False
        )
        
        # Initialize coordinator
        coordinator = CoordinatorAgent(config)
        
        # Verify sub-agents are initialized
        assert coordinator.attack_planner is not None, "AttackPlannerAgent not initialized"
        assert coordinator.retriever is not None, "RetrieverAgent not initialized"
        assert coordinator.executor is not None, "ExecutorAgent not initialized"
        assert coordinator.evaluator is not None, "EvaluatorAgent not initialized"
        
        # Verify stop flag is initialized
        assert coordinator.stop_flag is not None, "Stop flag not initialized"
        assert not coordinator.check_stop_flag(), "Stop flag should be clear initially"
        
        # Verify mission state
        assert coordinator.current_mission is None, "Current mission should be None"
        assert coordinator.mission_start_time is None, "Mission start time should be None"
        
        print("✓ CoordinatorAgent initialized successfully")
        print(f"  - AttackPlannerAgent: OK")
        print(f"  - RetrieverAgent: OK")
        print(f"  - ExecutorAgent: OK")
        print(f"  - EvaluatorAgent: OK")
        print(f"  - Stop flag: OK (cleared)")
        
        # Test stop flag functionality
        print("\nTesting stop flag functionality...")
        coordinator.activate_stop_flag()
        assert coordinator.check_stop_flag(), "Stop flag should be set"
        print("✓ Stop flag activation works")
        
        coordinator.clear_stop_flag()
        assert not coordinator.check_stop_flag(), "Stop flag should be cleared"
        print("✓ Stop flag clearing works")
        
        # Clean up
        coordinator.close()
        print("✓ CoordinatorAgent closed successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_mission_timeout_check():
    """Test mission timeout detection."""
    print("\nTesting mission timeout detection...")
    
    try:
        config = Config(
            huggingface_api_key="hf_test_key_placeholder",
            max_mission_duration_minutes=1  # 1 minute for testing
        )
        
        coordinator = CoordinatorAgent(config)
        
        # No mission running - should not timeout
        assert not coordinator._is_mission_timeout(), "Should not timeout without mission"
        print("✓ No timeout when no mission running")
        
        # Set mission start time to now - should not timeout
        coordinator.mission_start_time = datetime.utcnow()
        assert not coordinator._is_mission_timeout(), "Should not timeout immediately"
        print("✓ No timeout for fresh mission")
        
        # Set mission start time to past - should timeout
        from datetime import timedelta
        coordinator.mission_start_time = datetime.utcnow() - timedelta(minutes=2)
        assert coordinator._is_mission_timeout(), "Should timeout for old mission"
        print("✓ Timeout detected for expired mission")
        
        coordinator.close()
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_context_manager():
    """Test context manager functionality."""
    print("\nTesting context manager...")
    
    try:
        config = Config(
            huggingface_api_key="hf_test_key_placeholder"
        )
        
        with CoordinatorAgent(config) as coordinator:
            assert coordinator.attack_planner is not None
            print("✓ Context manager entry works")
        
        print("✓ Context manager exit works")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("CoordinatorAgent Implementation Tests")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Initialization", test_coordinator_initialization()))
    results.append(("Timeout Detection", test_mission_timeout_check()))
    results.append(("Context Manager", test_context_manager()))
    
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
