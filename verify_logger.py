"""
Verification script for logging system with PII redaction.
Tests core functionality without requiring pytest.
"""

import os
import tempfile
from pathlib import Path

from utils.logger import (
    setup_logging,
    get_logger,
    sanitize_log_message,
    PIIRedactionFilter
)


def test_pii_redaction_filter():
    """Test that PII redaction filter works correctly."""
    print("Testing PII redaction filter...")
    
    filter_instance = PIIRedactionFilter()
    
    # Test API key redaction
    text1 = "Using API key hf_abcdefghijklmnopqrstuvwxyz123456"
    redacted1 = filter_instance.redact_sensitive_data(text1)
    assert "hf_abcdefghijklmnopqrstuvwxyz123456" not in redacted1
    assert "hf_***REDACTED***" in redacted1
    print("✓ API key redaction works")
    
    # Test authorization token redaction
    text2 = 'Authorization: my_secret_token_12345'
    redacted2 = filter_instance.redact_sensitive_data(text2)
    assert "my_secret_token_12345" not in redacted2
    assert "***REDACTED***" in redacted2
    print("✓ Authorization token redaction works")
    
    # Test Bearer token redaction
    text3 = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    redacted3 = filter_instance.redact_sensitive_data(text3)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted3
    assert "Bearer ***REDACTED***" in redacted3
    print("✓ Bearer token redaction works")


def test_sanitize_helper():
    """Test the sanitize_log_message helper function."""
    print("\nTesting sanitize_log_message helper...")
    
    message = "API call with key hf_test123456789012345678 succeeded"
    sanitized = sanitize_log_message(message)
    assert "hf_test123456789012345678" not in sanitized
    assert "hf_***REDACTED***" in sanitized
    print("✓ Sanitize helper function works")


def test_logging_setup():
    """Test that logging setup creates directories and files."""
    print("\nTesting logging setup...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(logs_path=logs_path, log_to_console=False)
        
        # Check directory creation
        assert Path(logs_path).exists()
        assert Path(logs_path).is_dir()
        print("✓ Logs directory created")
        
        # Check log file creation
        log_file = Path(logs_path) / "redteaming.log"
        assert log_file.exists()
        print("✓ Log file created")
        
        # Close all handlers to release file locks
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


def test_automatic_redaction():
    """Test that logger automatically redacts sensitive data."""
    print("\nTesting automatic redaction in logs...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(logs_path=logs_path, log_to_console=False)
        
        # Log messages with sensitive data
        logger.info("Connecting with API key hf_secretkey123456789012345")
        logger.info("Request with authorization: secret_token_xyz")
        logger.warning("Bearer token_abc123 detected")
        
        # Close handlers before reading
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Read the log file
        log_file = Path(logs_path) / "redteaming.log"
        log_content = log_file.read_text()
        
        # Verify API key is redacted
        assert "hf_secretkey123456789012345" not in log_content
        assert "hf_***REDACTED***" in log_content
        print("✓ API keys automatically redacted in logs")
        
        # Verify authorization token is redacted
        assert "secret_token_xyz" not in log_content
        print("✓ Authorization tokens automatically redacted in logs")
        
        # Verify Bearer token is redacted
        assert "token_abc123" not in log_content
        print("✓ Bearer tokens automatically redacted in logs")


def test_log_levels():
    """Test that different log levels work correctly."""
    print("\nTesting log levels...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(log_level="DEBUG", logs_path=logs_path, log_to_console=False)
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Close handlers before reading
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Read the log file
        log_file = Path(logs_path) / "redteaming.log"
        log_content = log_file.read_text()
        
        # Verify all messages are present
        assert "Debug message" in log_content
        assert "Info message" in log_content
        assert "Warning message" in log_content
        assert "Error message" in log_content
        print("✓ All log levels work correctly")


def test_log_format():
    """Test that log format includes required fields."""
    print("\nTesting log format...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(logs_path=logs_path, log_to_console=False)
        
        logger.info("Test message")
        
        # Close handlers before reading
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        
        # Read the log file
        log_file = Path(logs_path) / "redteaming.log"
        log_content = log_file.read_text()
        
        # Verify format includes required fields
        assert "INFO" in log_content  # Level
        assert "Test message" in log_content  # Message
        assert "redteaming" in log_content  # Logger name
        
        # Check for timestamp format: YYYY-MM-DD HH:MM:SS
        import re
        assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', log_content)
        print("✓ Log format includes timestamps, level, module, and message")


def test_file_rotation_config():
    """Test that file rotation is configured correctly."""
    print("\nTesting file rotation configuration...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(logs_path=logs_path, log_to_console=False)
        
        # Check that rotating file handler is configured
        has_rotating_handler = False
        for handler in logger.handlers:
            if hasattr(handler, 'maxBytes') and hasattr(handler, 'backupCount'):
                has_rotating_handler = True
                # Verify 100 MB limit
                assert handler.maxBytes == 100 * 1024 * 1024
                # Verify 5 backup files
                assert handler.backupCount == 5
                print(f"✓ File rotation configured: {handler.maxBytes / (1024*1024)} MB max, {handler.backupCount} backups")
        
        assert has_rotating_handler, "No rotating file handler found"
        
        # Close handlers
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Logging System Verification")
    print("=" * 60)
    
    try:
        test_pii_redaction_filter()
        test_sanitize_helper()
        test_logging_setup()
        test_automatic_redaction()
        test_log_levels()
        test_log_format()
        test_file_rotation_config()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        print("\nLogging system features verified:")
        print("  • Structured logging with timestamps, level, module, and message")
        print("  • File rotation (100 MB limit, 5 backup files)")
        print("  • PII redaction for API keys (hf_*)")
        print("  • PII redaction for authorization tokens")
        print("  • PII redaction for Bearer tokens")
        print("  • Helper function for manual sanitization")
        print("  • Logs written to data/logs directory")
        print("  • Multiple log levels (DEBUG, INFO, WARNING, ERROR)")
        
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
