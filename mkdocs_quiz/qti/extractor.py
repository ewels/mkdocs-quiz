"""Quiz extraction from markdown files.

This module provides functions to parse mkdocs-quiz markdown syntax and
extract quiz data into the model format for QTI export.
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import Answer, Quiz, QuizCollection

# Quiz tag patterns (same as in plugin.py)
QUIZ_REGEX = r"<quiz>(.*?)</quiz>"

# Checkbox answer pattern
ANSWER_PATTERN = re.compile(r"^[-*]\s*\[([xX ]?)\]\s*(.*)$")


def _parse_quiz_content(
    content: str,
    source_file: Path | None = None,
    source_line: int | None = None,
) -> Quiz | None:
    """Parse the content inside a <quiz> tag into a Quiz object.

    Args:
        content: The raw content between <quiz> and </quiz> tags.
        source_file: Optional source file path for error reporting.
        source_line: Optional line number for error reporting.

    Returns:
        A Quiz object, or None if parsing fails.
    """
    lines = content.strip().splitlines()

    # Remove empty lines at start and end
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]

    if not lines:
        return None

    # Find the first answer line
    first_answer_idx = None
    for i, line in enumerate(lines):
        if ANSWER_PATTERN.match(line.strip()):
            first_answer_idx = i
            break

    if first_answer_idx is None:
        # No answers found
        return None

    # Question is everything before first answer
    question_lines = lines[:first_answer_idx]
    question_text = "\n".join(question_lines).strip()

    if not question_text:
        return None

    # Parse answers
    answers: list[Answer] = []
    content_start_idx = len(lines)

    for i, line in enumerate(lines[first_answer_idx:], start=first_answer_idx):
        stripped = line.strip()
        match = ANSWER_PATTERN.match(stripped)

        if match:
            checkbox_content = match.group(1)
            answer_text = match.group(2).strip()
            is_correct = checkbox_content.lower() == "x"
            answers.append(Answer(text=answer_text, is_correct=is_correct))
            content_start_idx = i + 1
        elif stripped:
            # Non-empty, non-answer line = start of content section
            break

    if not answers:
        return None

    # Content is everything after the last answer
    content_lines = lines[content_start_idx:]
    content_text = "\n".join(content_lines).strip() if content_lines else None

    return Quiz(
        question=question_text,
        answers=answers,
        content=content_text,
        source_file=source_file,
        source_line=source_line,
    )


def _mask_code_blocks(markdown: str) -> tuple[str, dict[str, str]]:
    """Temporarily mask fenced code blocks outside quiz tags.

    This prevents processing quiz tags shown as examples in code blocks.

    Args:
        markdown: The markdown content.

    Returns:
        Tuple of (masked markdown, placeholder->original mapping).
    """
    placeholders: dict[str, str] = {}
    counter = 0

    # Find all quiz blocks first
    quiz_ranges = []
    for match in re.finditer(QUIZ_REGEX, markdown, re.DOTALL):
        quiz_ranges.append((match.start(), match.end()))

    def replace_fenced(match: re.Match[str]) -> str:
        nonlocal counter
        match_start = match.start()
        match_end = match.end()

        # Check if this code block is inside a quiz
        for quiz_start, quiz_end in quiz_ranges:
            if quiz_start < match_start < quiz_end or quiz_start < match_end < quiz_end:
                return match.group(0)

        placeholder = f"__CODEBLOCK_{counter}__"
        placeholders[placeholder] = match.group(0)
        counter += 1
        return placeholder

    # Match fenced code blocks
    markdown = re.sub(
        r"^[ \t]*`{3,}.*?\n.*?^[ \t]*`{3,}|^[ \t]*~{3,}.*?\n.*?^[ \t]*~{3,}",
        replace_fenced,
        markdown,
        flags=re.MULTILINE | re.DOTALL,
    )

    return markdown, placeholders


def extract_quizzes_from_file(file_path: Path) -> list[Quiz]:
    """Extract all quizzes from a single markdown file.

    Args:
        file_path: Path to the markdown file.

    Returns:
        List of Quiz objects extracted from the file.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise ValueError(f"Failed to read file {file_path}: {e}") from e

    # Mask code blocks to avoid false positives
    masked_content, _ = _mask_code_blocks(content)

    quizzes: list[Quiz] = []

    for match in re.finditer(QUIZ_REGEX, masked_content, re.DOTALL):
        # Calculate line number
        line_number = content[: match.start()].count("\n") + 1

        quiz = _parse_quiz_content(
            match.group(1),
            source_file=file_path,
            source_line=line_number,
        )

        if quiz:
            quizzes.append(quiz)

    return quizzes


def extract_quizzes_from_directory(
    directory: Path,
    recursive: bool = True,
    pattern: str = "*.md",
) -> QuizCollection:
    """Extract all quizzes from markdown files in a directory.

    Args:
        directory: Path to the directory to search.
        recursive: Whether to search recursively (default: True).
        pattern: Glob pattern for files to include (default: "*.md").

    Returns:
        QuizCollection containing all extracted quizzes.
    """
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")

    # Use rglob for recursive, glob for non-recursive
    files = list(directory.rglob(pattern)) if recursive else list(directory.glob(pattern))

    collection = QuizCollection(
        title=f"Quizzes from {directory.name}",
        description=f"Exported from {len(files)} markdown files",
    )

    for file_path in sorted(files):
        try:
            quizzes = extract_quizzes_from_file(file_path)
            for quiz in quizzes:
                collection.add_quiz(quiz)
        except ValueError:
            # Skip files that can't be read
            continue

    return collection
