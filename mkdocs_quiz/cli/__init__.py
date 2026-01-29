"""CLI subpackage for mkdocs-quiz interactive quiz runner."""

from __future__ import annotations

from .discovery import interactive_quiz_selection
from .fetcher import fetch_quizzes, is_url
from .main import main
from .runner import console, display_final_results, get_score_color, run_quiz_session

__all__ = [
    "console",
    "display_final_results",
    "fetch_quizzes",
    "get_score_color",
    "interactive_quiz_selection",
    "is_url",
    "main",
    "run_quiz_session",
]
