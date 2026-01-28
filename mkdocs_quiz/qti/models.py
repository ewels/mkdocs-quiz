"""Data models for quiz representation.

These models provide a clean, format-agnostic representation of quiz data
that can be serialized to various QTI formats.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Answer:
    """Represents a single answer option in a quiz question.

    Attributes:
        text: The answer text (may contain HTML/markdown).
        is_correct: Whether this is a correct answer.
        identifier: Unique identifier for this answer (auto-generated if not provided).
    """

    text: str
    is_correct: bool
    identifier: str = field(default_factory=lambda: f"answer_{uuid.uuid4().hex[:8]}")

    def __post_init__(self) -> None:
        """Strip whitespace from text."""
        self.text = self.text.strip()


@dataclass
class Blank:
    """Represents a single fill-in-the-blank placeholder.

    Attributes:
        correct_answer: The correct answer for this blank.
        identifier: Unique identifier for this blank (auto-generated if not provided).
    """

    correct_answer: str
    identifier: str = field(default_factory=lambda: f"blank_{uuid.uuid4().hex[:8]}")

    def __post_init__(self) -> None:
        """Strip whitespace from answer."""
        self.correct_answer = self.correct_answer.strip()


@dataclass
class Quiz:
    """Represents a single quiz question.

    Attributes:
        question: The question text (may contain HTML/markdown).
        answers: List of possible answers (for multiple-choice quizzes).
        blanks: List of blanks (for fill-in-the-blank quizzes).
        content: Optional explanation/content shown after answering.
        identifier: Unique identifier for this quiz (auto-generated if not provided).
        source_file: The source file this quiz was extracted from.
        source_line: The line number in the source file.
    """

    question: str
    answers: list[Answer] = field(default_factory=list)
    blanks: list[Blank] = field(default_factory=list)
    content: str | None = None
    identifier: str = field(default_factory=lambda: f"quiz_{uuid.uuid4().hex[:8]}")
    source_file: Path | None = None
    source_line: int | None = None

    def __post_init__(self) -> None:
        """Validate quiz structure."""
        self.question = self.question.strip()
        if self.content:
            self.content = self.content.strip()

    @property
    def is_fill_in_blank(self) -> bool:
        """Check if this is a fill-in-the-blank quiz."""
        return len(self.blanks) > 0

    @property
    def is_multiple_choice(self) -> bool:
        """Check if this quiz has multiple correct answers (for multiple-choice quizzes)."""
        return sum(1 for a in self.answers if a.is_correct) > 1

    @property
    def correct_answers(self) -> list[Answer]:
        """Get list of correct answers (for multiple-choice quizzes)."""
        return [a for a in self.answers if a.is_correct]

    @property
    def incorrect_answers(self) -> list[Answer]:
        """Get list of incorrect answers (for multiple-choice quizzes)."""
        return [a for a in self.answers if not a.is_correct]

    def validate(self) -> list[str]:
        """Validate the quiz structure and return any errors.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []
        if not self.question:
            errors.append("Quiz must have a question")

        # Fill-in-blank validation
        if self.blanks:
            if not self.blanks:
                errors.append("Fill-in-blank quiz must have at least one blank")
        # Multiple-choice validation
        elif self.answers:
            if not any(a.is_correct for a in self.answers):
                errors.append("Quiz must have at least one correct answer")
        else:
            errors.append("Quiz must have either answers or blanks")

        return errors


@dataclass
class QuizCollection:
    """A collection of quizzes, typically from one or more files.

    Attributes:
        title: Title for the quiz collection/assessment.
        quizzes: List of Quiz objects.
        description: Optional description of the quiz collection.
        identifier: Unique identifier for the collection.
    """

    title: str
    quizzes: list[Quiz] = field(default_factory=list)
    description: str | None = None
    identifier: str = field(default_factory=lambda: f"assessment_{uuid.uuid4().hex[:8]}")

    def add_quiz(self, quiz: Quiz) -> None:
        """Add a quiz to the collection."""
        self.quizzes.append(quiz)

    def validate(self) -> dict[str, list[str]]:
        """Validate all quizzes and return errors by quiz identifier.

        Returns:
            Dictionary mapping quiz identifiers to their validation errors.
        """
        errors = {}
        for quiz in self.quizzes:
            quiz_errors = quiz.validate()
            if quiz_errors:
                errors[quiz.identifier] = quiz_errors
        return errors

    @property
    def total_questions(self) -> int:
        """Get total number of questions."""
        return len(self.quizzes)

    @property
    def single_choice_count(self) -> int:
        """Get count of single-choice questions."""
        return sum(1 for q in self.quizzes if not q.is_fill_in_blank and not q.is_multiple_choice)

    @property
    def multiple_choice_count(self) -> int:
        """Get count of multiple-choice questions."""
        return sum(1 for q in self.quizzes if not q.is_fill_in_blank and q.is_multiple_choice)

    @property
    def fill_in_blank_count(self) -> int:
        """Get count of fill-in-the-blank questions."""
        return sum(1 for q in self.quizzes if q.is_fill_in_blank)
