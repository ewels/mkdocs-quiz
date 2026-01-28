"""Quiz extraction from markdown files.

This module provides functions to parse mkdocs-quiz markdown syntax and
extract quiz data into the model format for QTI export.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..parsing import ANSWER_PATTERN, FILL_BLANK_REGEX, find_quizzes, mask_code_blocks, parse_answer
from .models import Answer, Blank, Quiz, QuizCollection


def _is_fill_in_blank_quiz(content: str) -> bool:
    """Check if quiz content contains fill-in-the-blank patterns.

    Args:
        content: The raw quiz content.

    Returns:
        True if [[...]] patterns are found, False otherwise.
    """
    return bool(re.search(FILL_BLANK_REGEX, content))


def _parse_fill_in_blank_quiz(
    content: str,
    source_file: Path | None = None,
    source_line: int | None = None,
) -> Quiz | None:
    """Parse a fill-in-the-blank quiz.

    Args:
        content: The raw content between <quiz> and </quiz> tags.
        source_file: Optional source file path for error reporting.
        source_line: Optional line number for error reporting.

    Returns:
        A Quiz object with blanks populated, or None if parsing fails.
    """
    lines = content.strip().splitlines()

    # Remove empty lines at start and end
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]

    if not lines:
        return None

    # Split content into question and content sections
    # Look for a horizontal rule (---) to separate question from content
    question_lines = []
    content_start_idx = len(lines)

    for i, line in enumerate(lines):
        if line.strip() == "---":
            question_lines = lines[:i]
            content_start_idx = i + 1
            break

    # If no horizontal rule found, everything is the question
    if not question_lines:
        question_lines = lines
        content_start_idx = len(lines)

    question_text = "\n".join(question_lines)

    # Extract blanks from the question
    blanks: list[Blank] = []
    for match in re.finditer(FILL_BLANK_REGEX, question_text):
        answer = match.group(1).strip()
        blanks.append(Blank(correct_answer=answer))

    if not blanks:
        return None

    # Replace [[answer]] with placeholder markers for the question text
    # This preserves the position information for QTI export
    blank_counter = 0

    def replace_blank(match: re.Match[str]) -> str:
        nonlocal blank_counter
        placeholder = f"{{{{BLANK_{blank_counter}}}}}"
        blank_counter += 1
        return placeholder

    question_with_placeholders = re.sub(FILL_BLANK_REGEX, replace_blank, question_text)

    # Get content section
    content_lines = lines[content_start_idx:]
    content_text = "\n".join(content_lines).strip() if content_lines else None

    return Quiz(
        question=question_with_placeholders,
        blanks=blanks,
        content=content_text,
        source_file=source_file,
        source_line=source_line,
    )


def _parse_multiple_choice_quiz(
    content: str,
    source_file: Path | None = None,
    source_line: int | None = None,
) -> Quiz | None:
    """Parse a multiple-choice quiz.

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
        parsed = parse_answer(line)
        if parsed:
            is_correct, answer_text = parsed
            answers.append(Answer(text=answer_text, is_correct=is_correct))
            content_start_idx = i + 1
        elif line.strip():
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


def _parse_quiz_content(
    content: str,
    source_file: Path | None = None,
    source_line: int | None = None,
) -> Quiz | None:
    """Parse the content inside a <quiz> tag into a Quiz object.

    Automatically detects whether the quiz is fill-in-the-blank or multiple-choice
    based on the presence of [[answer]] patterns.

    Args:
        content: The raw content between <quiz> and </quiz> tags.
        source_file: Optional source file path for error reporting.
        source_line: Optional line number for error reporting.

    Returns:
        A Quiz object, or None if parsing fails.
    """
    if _is_fill_in_blank_quiz(content):
        return _parse_fill_in_blank_quiz(content, source_file, source_line)
    else:
        return _parse_multiple_choice_quiz(content, source_file, source_line)


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
    masked_content, _ = mask_code_blocks(content)

    quizzes: list[Quiz] = []

    for match in find_quizzes(masked_content):
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
