"""
Example demonstrating how to integrate the logging system with agents.
Shows proper usage of the logger with PII redaction.
"""

from utils.logger import setup_logging, get_logger, sanitize_log_message


def example_agent_usage():
    """Example of how agents should use the logging system."""
    
    # Initialize logging (typically done once at application startup)
    main_logger = setup_logging(
        log_level="INFO",
        logs_path="./data/logs",
        log_to_console=True,
        log_to_file=True
    )
    
    # Get a logger for a specific agent
    planner_logger = get_logger("attack_planner")
    executor_logger = get_logger("executor")
    evaluator_logger = get_logger("evaluator")
    
    # Example 1: Logging with automatic PII redaction
    print("\n=== Example 1: Automatic PII Redaction ===")
    api_key = "hf_abcdefghijklmnopqrstuvwxyz123456"
    planner_logger.info(f"Initializing with API key {api_key}")
    print("✓ API key automatically redacted in logs")
    
    # Example 2: Logging authorization attempts
    print("\n=== Example 2: Authorization Logging ===")
    auth_token = "secret_token_12345"
    executor_logger.info(f"Request with authorization: {auth_token}")
    print("✓ Authorization token automatically redacted")
    
    # Example 3: Logging different severity levels
    print("\n=== Example 3: Different Log Levels ===")
    evaluator_logger.debug("Starting vulnerability analysis")
    evaluator_logger.info("Found 3 potential vulnerabilities")
    evaluator_logger.warning("High severity vulnerability detected")
    evaluator_logger.error("Failed to classify vulnerability")
    print("✓ All log levels working")
    
    # Example 4: Manual sanitization when needed
    print("\n=== Example 4: Manual Sanitization ===")
    sensitive_message = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    sanitized = sanitize_log_message(sensitive_message)
    planner_logger.info(f"Sanitized message: {sanitized}")
    print("✓ Manual sanitization helper works")
    
    # Example 5: Structured logging with extra fields
    print("\n=== Example 5: Structured Logging ===")
    executor_logger.info(
        "Prompt execution completed",
        extra={
            "prompt_id": "prompt_123",
            "execution_time_ms": 1234,
            "status_code": 200
        }
    )
    print("✓ Structured logging with metadata")
    
    # Example 6: Exception logging (sensitive data in tracebacks)
    print("\n=== Example 6: Exception Logging ===")
    try:
        # Simulate an error with sensitive data
        raise ValueError(f"API call failed with key hf_secret123456789012345678")
    except Exception as e:
        # The exception message will be redacted automatically
        evaluator_logger.error(f"Error occurred: {e}", exc_info=False)
    print("✓ Exception messages redacted")
    
    print("\n" + "=" * 60)
    print("Integration examples completed!")
    print("Check logs at: ./data/logs/redteaming.log")
    print("=" * 60)


def example_coordinator_integration():
    """Example of how CoordinatorAgent would use logging."""
    
    logger = get_logger("coordinator")
    
    print("\n=== Coordinator Agent Logging Example ===")
    
    # Mission start
    mission_id = "mission_abc123"
    logger.info(f"Starting mission {mission_id}")
    
    # Phase transitions
    logger.info(f"Mission {mission_id}: Planning phase started")
    logger.info(f"Mission {mission_id}: Generated 15 adversarial prompts")
    logger.info(f"Mission {mission_id}: Execution phase started")
    logger.info(f"Mission {mission_id}: Executed 15/15 prompts successfully")
    logger.info(f"Mission {mission_id}: Evaluation phase started")
    logger.warning(f"Mission {mission_id}: Found 3 HIGH severity vulnerabilities")
    logger.info(f"Mission {mission_id}: Report generated and saved")
    
    # Mission completion
    logger.info(
        f"Mission {mission_id} completed",
        extra={
            "total_prompts": 15,
            "vulnerabilities_found": 5,
            "duration_seconds": 180
        }
    )
    
    print("✓ Coordinator logging example completed")


if __name__ == "__main__":
    print("=" * 60)
    print("Logging System Integration Examples")
    print("=" * 60)
    
    try:
        example_agent_usage()
        example_coordinator_integration()
        
        print("\n✓ All integration examples completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
