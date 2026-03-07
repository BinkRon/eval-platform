"""Unified error message sanitization.

Strips URLs, IP addresses, and file paths from error messages
to prevent leaking internal infrastructure details to users.
"""
import re


def sanitize_error(msg: str, max_length: int = 500) -> str:
    """Remove URLs, IPs, and file paths from error messages."""
    msg = re.sub(r'https?://\S+', '[URL]', msg)
    msg = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?', '[IP]', msg)
    msg = re.sub(r'/[\w./\\-]+', '[path]', msg)
    return msg[:max_length]
