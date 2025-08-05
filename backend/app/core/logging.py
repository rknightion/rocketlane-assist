"""
Logging utilities for the application
"""

import logging
import sys

from .config import settings


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with appropriate configuration"""
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)

        # Set format based on debug mode
        if getattr(settings, "debug_mode", False):
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            )
            logger.setLevel(logging.DEBUG)
        else:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            logger.setLevel(logging.INFO)

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    return logger


def log_request_details(
    logger: logging.Logger,
    method: str,
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
):
    """Log HTTP request details when in debug mode"""
    if getattr(settings, "debug_mode", False):
        logger.debug(f"Request: {method} {url}")
        if headers:
            # Mask sensitive headers
            safe_headers = headers.copy()
            if "api-key" in safe_headers:
                safe_headers["api-key"] = (
                    safe_headers["api-key"][:10] + "..." if safe_headers["api-key"] else "None"
                )
            logger.debug(f"Headers: {safe_headers}")
        if params:
            logger.debug(f"Params: {params}")


def log_response_details(
    logger: logging.Logger, status_code: int, response_text: str | None = None
):
    """Log HTTP response details when in debug mode"""
    if getattr(settings, "debug_mode", False):
        logger.debug(f"Response Status: {status_code}")
        if response_text:
            # Truncate long responses
            truncated = response_text[:1000] + "..." if len(response_text) > 1000 else response_text
            logger.debug(f"Response Body: {truncated}")
