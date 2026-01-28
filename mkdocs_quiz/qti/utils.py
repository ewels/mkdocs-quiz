"""Shared utilities for QTI export.

Common helper functions used across different QTI format versions.
"""

from __future__ import annotations

import re
from xml.sax.saxutils import escape as xml_escape


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text for plain-text contexts.

    Args:
        text: Text that may contain HTML tags.

    Returns:
        Text with HTML tags removed.
    """
    return re.sub(r"<[^>]+>", "", text)


def to_html_content(text: str) -> str:
    """Convert text to safe HTML content for QTI.

    If text contains HTML, wraps in CDATA. Otherwise, escapes special characters.

    Args:
        text: The text content.

    Returns:
        Safe HTML/XML content.
    """
    if re.search(r"<[^>]+>", text):
        # CDATA sections cannot contain the sequence "]]>" as it would end the CDATA.
        # The standard workaround is to split the CDATA section at each occurrence:
        # "]]>" becomes "]]]]><![CDATA[>"
        safe_text = text.replace("]]>", "]]]]><![CDATA[>")
        return f"<![CDATA[{safe_text}]]>"
    else:
        return xml_escape(text)


def make_title(question: str, max_length: int = 50) -> str:
    """Create a safe XML title from a question.

    Args:
        question: The question text (may contain HTML).
        max_length: Maximum length for the title.

    Returns:
        XML-escaped plain text title.
    """
    return xml_escape(strip_html_tags(question)[:max_length])
