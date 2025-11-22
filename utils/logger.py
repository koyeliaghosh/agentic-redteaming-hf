"""
Logging utilities with PII redaction for the Agentic AI Red-Teaming Assistant.
Provides structured logging with automatic redaction of sensitive information.
"""

import logging
import logging.handlers
import os
import re
from pathlib import Path
from typing import Optional


class PIIRedactionFilter(logging.Filter):
    """
    Custom logging filter that redacts sensitive information from log messages.
    Redacts API keys, authorization tokens, and other PII.
    """
    
    # Patterns for sensitive data
    API_KEY_PATTERN = re.compile(r'hf_[a-zA-Z0-9]{20,}')
    AUTH_TOKEN_PATTERN = re.compile(r'(authorization["\s:=]+)([a-zA-Z0-9_\-\.]+)', re.IGNORECASE)
    BEARER_TOKEN_PATTERN = re.compile(r'(Bearer\s+)([a-zA-Z0-9_\-\.]+)', re.IGNORECASE)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record by redacting sensitive information.
        
        Args:
            record: The log record to filter
            
        Returns:
            True to allow the record to be logged
        """
        # Redact sensitive data from the message
        if isinstance(record.msg, str):
            record.msg = self.redact_sensitive_data(record.msg)
        
        # Redact sensitive data from arguments
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact_sensitive_data(str(v)) if isinstance(v, str) else v 
                              for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact_sensitive_data(str(arg)) if isinstance(arg, str) else arg 
                                   for arg in record.args)
        
        return True
    
    @classmethod
    def redact_sensitive_data(cls, text: str) -> str:
        """
        Redact sensitive information from text.
        
        Args:
            text: The text to redact
            
        Returns:
            Text with sensitive information redacted
        """
        # Redact Hugging Face API keys
        text = cls.API_KEY_PATTERN.sub('hf_***REDACTED***', text)
        
        # Redact authorization tokens
        text = cls.AUTH_TOKEN_PATTERN.sub(r'\1***REDACTED***', text)
        
        # Redact Bearer tokens
        text = cls.BEARER_TOKEN_PATTERN.sub(r'\1***REDACTED***', text)
        
        return text


def sanitize_log_message(message: str) -> str:
    """
    Helper function to sanitize log messages before logging.
    Useful for manual sanitization when needed.
    
    Args:
        message: The message to sanitize
        
    Returns:
        Sanitized message with sensitive data redacted
    """
    return PIIRedactionFilter.redact_sensitive_data(message)


def setup_logging(
    log_level: str = "INFO",
    logs_path: str = "./data/logs",
    log_to_console: bool = True,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Set up structured logging with file rotation and PII redaction.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        logs_path: Directory path for log files
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    logs_dir = Path(logs_path)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger("redteaming")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter with timestamps, level, module, and message
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add PII redaction filter
    pii_filter = PIIRedactionFilter()
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(pii_filter)
        logger.addHandler(console_handler)
    
    # File handler with rotation (100 MB limit, 5 backup files)
    if log_to_file:
        log_file = logs_dir / "redteaming.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=100 * 1024 * 1024,  # 100 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
        file_handler.setFormatter(formatter)
        file_handler.addFilter(pii_filter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    logger.info("Logging system initialized", extra={
        "log_level": log_level,
        "logs_path": logs_path,
        "log_to_console": log_to_console,
        "log_to_file": log_to_file
    })
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (defaults to 'redteaming')
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"redteaming.{name}")
    return logging.getLogger("redteaming")


# Initialize default logger on module import
_default_logger: Optional[logging.Logger] = None


def init_default_logger(config=None) -> logging.Logger:
    """
    Initialize the default logger with configuration.
    
    Args:
        config: Configuration object (optional)
        
    Returns:
        Configured logger instance
    """
    global _default_logger
    
    if config:
        logs_path = getattr(config, 'logs_path', './data/logs')
    else:
        logs_path = os.getenv('LOGS_PATH', './data/logs')
    
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    _default_logger = setup_logging(
        log_level=log_level,
        logs_path=logs_path,
        log_to_console=True,
        log_to_file=True
    )
    
    return _default_logger


def get_default_logger() -> logging.Logger:
    """
    Get the default logger instance, initializing if necessary.
    
    Returns:
        Default logger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = init_default_logger()
    return _default_logger
