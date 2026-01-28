"""QTI (Question and Test Interoperability) export module.

This module provides functionality to export mkdocs-quiz questions to QTI format
for import into Learning Management Systems like Canvas, Blackboard, Moodle, etc.

Supported formats:
- QTI 1.2: Widest compatibility (Canvas Classic Quizzes, Blackboard, older LMS)
- QTI 2.1: Modern standard (Canvas New Quizzes, newer LMS)
"""

from __future__ import annotations

from .base import QTIExporter, QTIVersion
from .extractor import extract_quizzes_from_directory, extract_quizzes_from_file
from .models import Answer, Blank, Quiz, QuizCollection

__all__ = [
    "Answer",
    "Blank",
    "QTIExporter",
    "QTIVersion",
    "Quiz",
    "QuizCollection",
    "extract_quizzes_from_directory",
    "extract_quizzes_from_file",
]
