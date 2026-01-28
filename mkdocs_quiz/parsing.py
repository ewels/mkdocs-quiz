"""Shared quiz parsing utilities.

Common regex patterns and functions used for parsing quiz syntax
in both the MkDocs plugin and QTI export functionality.
"""

from __future__ import annotations

import re

# Quiz tag patterns
QUIZ_START_TAG = "<quiz>"
QUIZ_END_TAG = "</quiz>"
QUIZ_REGEX = r"<quiz>(.*?)</quiz>"

# Pattern to match fill-in-the-blank placeholders: [[answer]]
FILL_BLANK_REGEX = r"\[\[([^\]]+)\]\]"

# Checkbox answer pattern: - [x] Answer or * [x] Answer
ANSWER_PATTERN = re.compile(r"^[-*]\s*\[([xX ]?)\]\s*(.*)$")

# Old v0.x syntax patterns (no longer supported)
OLD_SYNTAX_PATTERNS = [
    r"<\?quiz\?>",  # Old quiz opening tag
    r"<\?/quiz\?>",  # Old quiz closing tag
]

__all__ = [
    "ANSWER_PATTERN",
    "FILL_BLANK_REGEX",
    "OLD_SYNTAX_PATTERNS",
    "QUIZ_END_TAG",
    "QUIZ_REGEX",
    "QUIZ_START_TAG",
    "find_quizzes",
    "mask_code_blocks",
    "parse_answer",
    "unmask_code_blocks",
]


def mask_code_blocks(markdown: str) -> tuple[str, dict[str, str]]:
    """Temporarily mask fenced code blocks to prevent processing quiz tags inside them.

    Only masks code blocks that are NOT inside quiz tags, to avoid breaking quizzes
    that contain code examples in their content sections.

    Args:
        markdown: The markdown content.

    Returns:
        A tuple of (masked markdown, dictionary of placeholders to original content).
    """
    placeholders: dict[str, str] = {}
    counter = 0

    # Find all quiz blocks first
    quiz_ranges = []
    for match in re.finditer(QUIZ_REGEX, markdown, re.DOTALL):
        quiz_ranges.append((match.start(), match.end()))

    # Mask fenced code blocks (```...``` or ~~~...~~~)
    def replace_fenced(match: re.Match[str]) -> str:
        nonlocal counter
        # Check if this code block is inside a quiz
        match_start = match.start()
        match_end = match.end()
        for quiz_start, quiz_end in quiz_ranges:
            if quiz_start < match_start < quiz_end or quiz_start < match_end < quiz_end:
                # Code block is inside a quiz, don't mask it
                return match.group(0)

        # Code block is outside quizzes, mask it
        placeholder = f"__CODEBLOCK_{counter}__"
        placeholders[placeholder] = match.group(0)
        counter += 1
        return placeholder

    # Match fenced code blocks with optional language specifier
    # Supports ``` and ~~~ delimiters (3 or more), with optional indentation
    markdown = re.sub(
        r"^[ \t]*`{3,}.*?\n.*?^[ \t]*`{3,}|^[ \t]*~{3,}.*?\n.*?^[ \t]*~{3,}",
        replace_fenced,
        markdown,
        flags=re.MULTILINE | re.DOTALL,
    )

    return markdown, placeholders


def unmask_code_blocks(markdown: str, placeholders: dict[str, str]) -> str:
    """Restore code blocks that were temporarily masked.

    Args:
        markdown: The markdown content with placeholders.
        placeholders: Dictionary of placeholders to original content.

    Returns:
        The markdown with code blocks restored.
    """
    for placeholder, original in placeholders.items():
        markdown = markdown.replace(placeholder, original)
    return markdown


def find_quizzes(markdown: str) -> list[re.Match[str]]:
    """Find all quiz blocks in markdown content.

    Args:
        markdown: The markdown content (should be pre-processed with mask_code_blocks).

    Returns:
        List of regex match objects for each quiz found.
    """
    return list(re.finditer(QUIZ_REGEX, markdown, re.DOTALL))


def parse_answer(line: str) -> tuple[bool, str] | None:
    """Parse a checkbox answer line.

    Args:
        line: A line that may be a checkbox answer.

    Returns:
        Tuple of (is_correct, answer_text) if line is an answer, None otherwise.
    """
    match = ANSWER_PATTERN.match(line.strip())
    if not match:
        return None
    checkbox_content = match.group(1)
    answer_text = match.group(2).strip()
    is_correct = checkbox_content.lower() == "x"
    return is_correct, answer_text
