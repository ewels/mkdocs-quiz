"""CLI subpackage for mkdocs-quiz interactive quiz runner."""

from __future__ import annotations

from .fetcher import fetch_quizzes, is_url
from .main import main
from .runner import console, display_final_results, run_quiz_session

__all__ = [
    "console",
    "display_final_results",
    "fetch_quizzes",
    "is_url",
    "main",
    "run_quiz_session",
]
