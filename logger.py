"""
Centralized logging for the math tutor app.
Logs to both console and a file for debugging and monitoring.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Log directory and file
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"

# Create logger
logger = logging.getLogger("math_tutor")
logger.setLevel(logging.DEBUG)

# Avoid duplicate handlers
if not logger.handlers:
    # File handler: detailed logs
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler: info and above (less noisey in streamlit)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(levelname)-8s | %(funcName)s | %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


def get_logger() -> logging.Logger:
    """Get the configured logger."""
    return logger
