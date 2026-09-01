"""
Logging configuration for TDEM backend
"""

import logging
import sys
from app.core.config import settings


def setup_logging():
    """Configure logging for the application"""
    
    # Create logger
    logger = logging.getLogger("tdem")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger


# Module-level logger
logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger for a module"""
    return logging.getLogger(f"tdem.{name}")
