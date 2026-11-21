"""
Formatting and utility functions.
"""

from typing import Any, Dict


def format_markdown_body(content: str) -> Dict[str, Any]:
    """Wraps string into WeCom markdown payload."""
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }


def format_text_body(content: str) -> Dict[str, Any]:
    """Wraps string into WeCom text payload."""
    return {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
