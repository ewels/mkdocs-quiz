"""Fetch quizzes from remote URLs or local files."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.parse import urlparse

import requests  # type: ignore[import-untyped]

from ..qti.extractor import extract_quizzes_from_directory, extract_quizzes_from_file
from ..qti.models import Quiz

logger = logging.getLogger(__name__)

# Pattern to extract quiz source from HTML comments
QUIZ_SOURCE_PATTERN = re.compile(
    r"<!-- mkdocs-quiz-source\n(.*?)\n-->",
    re.DOTALL,
)


def is_url(path: str) -> bool:
    """Check if the given path is a URL.

    Args:
        path: The path to check.

    Returns:
        True if the path is a URL, False otherwise.
    """
    try:
        result = urlparse(path)
        return result.scheme in ("http", "https")
    except ValueError:
        return False


def extract_quiz_sources_from_html(html: str) -> list[str]:
    """Extract quiz source markdown from HTML comments.

    Looks for <!-- mkdocs-quiz-source ... --> comments in the HTML
    and extracts the quiz markdown content.

    Args:
        html: The HTML content to parse.

    Returns:
        List of quiz source strings (including <quiz>...</quiz> tags).
    """
    sources = []
    for match in QUIZ_SOURCE_PATTERN.finditer(html):
        sources.append(match.group(1))
    return sources


def parse_quiz_from_source(source: str, source_url: str, index: int) -> Quiz | None:
    """Parse a quiz from its source markdown.

    Args:
        source: The quiz source markdown (including <quiz>...</quiz> tags).
        source_url: The URL where the quiz was found (for identification).
        index: The index of the quiz on the page.

    Returns:
        A Quiz object, or None if parsing fails.
    """
    from ..parsing import FILL_BLANK_REGEX, find_quizzes

    # Find quiz content within the source
    matches = list(find_quizzes(source))
    if not matches:
        return None

    match = matches[0]
    content = match.group(1).strip()

    # Generate identifier from URL and index
    identifier = f"{urlparse(source_url).path.replace('/', '_')}_{index}"

    # Check if fill-in-the-blank
    if re.search(FILL_BLANK_REGEX, content):
        return _parse_fill_in_blank_quiz(content, identifier, source_url)
    return _parse_multiple_choice_quiz(content, identifier, source_url)


def _parse_fill_in_blank_quiz(content: str, identifier: str, source_url: str) -> Quiz:
    """Parse a fill-in-the-blank quiz from content.

    Args:
        content: The quiz content (without <quiz> tags).
        identifier: Unique identifier for the quiz.
        source_url: The URL where the quiz was found.

    Returns:
        A Quiz object.
    """
    from ..parsing import FILL_BLANK_REGEX
    from ..qti.models import Blank, Quiz

    lines = content.split("\n")

    # Find content section separator (---)
    question_lines = []
    content_lines = []
    found_separator = False

    for line in lines:
        if line.strip() == "---" and not found_separator:
            found_separator = True
            continue
        if found_separator:
            content_lines.append(line)
        else:
            question_lines.append(line)

    question_text = "\n".join(question_lines).strip()
    content_text = "\n".join(content_lines).strip() if content_lines else None

    # Extract blanks
    blanks = []
    for i, match in enumerate(re.finditer(FILL_BLANK_REGEX, question_text)):
        blanks.append(Blank(correct_answer=match.group(1).strip(), identifier=f"blank_{i}"))

    return Quiz(
        question=question_text,
        answers=[],
        blanks=blanks,
        content=content_text,
        identifier=identifier,
        source_file=Path(source_url),
        source_line=0,
    )


def _parse_multiple_choice_quiz(content: str, identifier: str, source_url: str) -> Quiz:
    """Parse a multiple-choice quiz from content.

    Args:
        content: The quiz content (without <quiz> tags).
        identifier: Unique identifier for the quiz.
        source_url: The URL where the quiz was found.

    Returns:
        A Quiz object.
    """
    from ..parsing import parse_answer
    from ..qti.models import Answer, Quiz

    lines = content.split("\n")

    question_lines: list[str] = []
    answers: list[Answer] = []
    content_lines: list[str] = []
    found_first_answer = False

    for line in lines:
        parsed = parse_answer(line)
        if parsed:
            found_first_answer = True
            is_correct, answer_text = parsed
            answers.append(
                Answer(
                    text=answer_text,
                    is_correct=is_correct,
                    identifier=f"answer_{len(answers)}",
                )
            )
        elif not found_first_answer:
            question_lines.append(line)
        elif found_first_answer and line.strip() and not parsed:
            # Content after answers
            content_lines.append(line)

    question_text = "\n".join(question_lines).strip()
    content_text = "\n".join(content_lines).strip() if content_lines else None

    return Quiz(
        question=question_text,
        answers=answers,
        blanks=[],
        content=content_text,
        identifier=identifier,
        source_file=Path(source_url),
        source_line=0,
    )


def fetch_quizzes_from_url(url: str, timeout: int = 30) -> list[Quiz]:
    """Fetch and parse quizzes from a remote URL.

    The URL should point to a page rendered by mkdocs-quiz with
    embed_source enabled. The quiz source is extracted from HTML comments.

    Args:
        url: The URL to fetch quizzes from.
        timeout: Request timeout in seconds.

    Returns:
        List of Quiz objects found on the page.

    Raises:
        requests.RequestException: If the HTTP request fails.
        ValueError: If no quizzes are found on the page.
    """
    # Fetch the page
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    html = response.text

    # Extract quiz sources from HTML comments
    sources = extract_quiz_sources_from_html(html)

    if not sources:
        raise ValueError(
            f"No quizzes found at {url}. "
            "Make sure the page was built with mkdocs-quiz and embed_source enabled."
        )

    # Parse each quiz source
    quizzes = []
    for i, source in enumerate(sources):
        quiz = parse_quiz_from_source(source, url, i)
        if quiz:
            quizzes.append(quiz)
        else:
            logger.warning("Failed to parse quiz %d from %s", i + 1, url)

    return quizzes


def fetch_quizzes(path: str) -> list[Quiz]:
    """Fetch quizzes from a URL or local path.

    Automatically detects whether the path is a URL or local file/directory.

    Args:
        path: URL or local file/directory path.

    Returns:
        List of Quiz objects.

    Raises:
        ValueError: If no quizzes are found.
        FileNotFoundError: If local path doesn't exist.
        requests.RequestException: If URL fetch fails.
    """
    if is_url(path):
        return fetch_quizzes_from_url(path)

    # Local path
    local_path = Path(path)

    if not local_path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    if local_path.is_file():
        return extract_quizzes_from_file(local_path)

    collection = extract_quizzes_from_directory(local_path)
    return collection.quizzes
