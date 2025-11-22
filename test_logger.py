"""
Test suite for logging system with PII redaction.
"""

import logging
import os
import tempfile
from pathlib import Path
import pytest

from utils.logger import (
    setup_logging,
    get_logger,
    sanitize_log_message,
    PIIRedactionFilter
)


def test_pii_redaction_filter_api_keys():
    """Test that API keys are properly redacted."""
    filter_instance = PIIRedactionFilter()
    
    # Test Hugging Face API key redaction
    text = "Using API key hf_abcdefghijklmnopqrstuvwxyz123456"
    redacted = filter_instance.redact_sensitive_data(text)
    assert "hf_abcdefghijklmnopqrstuvwxyz123456" not in redacted
    assert "hf_***REDACTED***" in redacted


def test_pii_redaction_filter_auth_tokens():
    """Test that authorization tokens are properly redacted."""
    filter_instance = PIIRedactionFilter()
    
    # Test authorization token redaction
    text = 'Authorization: my_secret_token_12345'
    redacted = filter_instance.redact_sensitive_data(text)
    assert "my_secret_token_12345" not in redacted
    assert "***REDACTED***" in redacted
    
    # Test with different formats
    text2 = 'authorization="another_token"'
    redacted2 = filter_instance.redact_sensitive_data(text2)
    assert "another_token" not in redacted2


def test_pii_redaction_filter_bearer_tokens():
    """Test that Bearer tokens are properly redacted."""
    filter_instance = PIIRedactionFilter()
    
    text = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    redacted = filter_instance.redact_sensitive_data(text)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in redacted
    assert "Bearer ***REDACTED***" in redacted


def test_sanitize_log_message():
    """Test the sanitize_log_message helper function."""
    message = "API call with key hf_test123456789012345678 succeeded"
    sanitized = sanitize_log_message(message)
    assert "hf_test123456789012345678" not in sanitized
    assert "hf_***REDACTED***" in sanitized


def test_setup_logging_creates_directory():
    """Test that setup_logging creates the logs directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(logs_path=logs_path, log_to_console=False)
        
        assert Path(logs_path).exists()
        assert Path(logs_path).is_dir()


def test_setup_logging_creates_log_file():
    """Test that setup_logging creates a log file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(logs_path=logs_path, log_to_console=False)
        
        log_file = Path(logs_path) / "redteaming.log"
        assert log_file.exists()


def test_logger_redacts_api_keys_in_messages():
    """Test that logger automatically redacts API keys from log messages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(logs_path=logs_path, log_to_console=False)
        
        # Log a message with an API key
        logger.info("Connecting with API key hf_secretkey123456789012345")
        
        # Read the log file
        log_file = Path(logs_path) / "redteaming.log"
        log_content = log_file.read_text()
        
        # Verify API key is redacted
        assert "hf_secretkey123456789012345" not in log_content
        assert "hf_***REDACTED***" in log_content


def test_logger_redacts_auth_tokens_in_messages():
    """Test that logger automatically redacts authorization tokens."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(logs_path=logs_path, log_to_console=False)
        
        # Log a message with an authorization token
        logger.info("Request with authorization: secret_token_xyz")
        
        # Read the log file
        log_file = Path(logs_path) / "redteaming.log"
        log_content = log_file.read_text()
        
        # Verify token is redacted
        assert "secret_token_xyz" not in log_content
        assert "***REDACTED***" in log_content


def test_logger_levels():
    """Test that different log levels work correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(log_level="DEBUG", logs_path=logs_path, log_to_console=False)
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Read the log file
        log_file = Path(logs_path) / "redteaming.log"
        log_content = log_file.read_text()
        
        # Verify all messages are present
        assert "Debug message" in log_content
        assert "Info message" in log_content
        assert "Warning message" in log_content
        assert "Error message" in log_content


def test_get_logger():
    """Test that get_logger returns a logger instance."""
    logger = get_logger("test_module")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "redteaming.test_module"


def test_log_format_includes_required_fields():
    """Test that log format includes timestamps, level, module, and message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logs_path = os.path.join(tmpdir, "test_logs")
        logger = setup_logging(logs_path=logs_path, log_to_console=False)
        
        logger.info("Test message")
        
        # Read the log file
        log_file = Path(logs_path) / "redteaming.log"
        log_content = log_file.read_text()
        
        # Verify format includes required fields
        assert "INFO" in log_content  # Level
        assert "Test message" in log_content  # Message
        assert "-" in log_content  # Separators
        # Timestamp format: YYYY-MM-DD HH:MM:SS
        import re
        assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', log_content)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
