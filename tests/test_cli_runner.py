"""Tests for mkdocs_quiz.cli.runner module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from mkdocs_quiz.cli.runner import (
    get_score_color,
    shorten_path,
    strip_html_tags,
)
from mkdocs_quiz.qti.models import Answer, Blank, Quiz


class TestGetScoreColor:
    """Tests for get_score_color function."""

    def test_excellent_score(self) -> None:
        """Test green color for 80%+ scores."""
        assert get_score_color(100) == "green"
        assert get_score_color(80) == "green"
        assert get_score_color(95.5) == "green"

    def test_good_score(self) -> None:
        """Test yellow color for 60-79% scores."""
        assert get_score_color(79.9) == "yellow"
        assert get_score_color(60) == "yellow"
        assert get_score_color(70) == "yellow"

    def test_poor_score(self) -> None:
        """Test red color for <60% scores."""
        assert get_score_color(59.9) == "red"
        assert get_score_color(0) == "red"
        assert get_score_color(50) == "red"


class TestStripHtmlTags:
    """Tests for strip_html_tags function."""

    def test_strip_simple_tags(self) -> None:
        """Test stripping simple HTML tags."""
        assert strip_html_tags("<p>Hello</p>") == "Hello"
        assert strip_html_tags("<b>Bold</b>") == "Bold"

    def test_strip_nested_tags(self) -> None:
        """Test stripping nested HTML tags."""
        assert strip_html_tags("<div><p>Nested</p></div>") == "Nested"

    def test_strip_with_attributes(self) -> None:
        """Test stripping tags with attributes."""
        assert strip_html_tags('<a href="url">Link</a>') == "Link"
        assert strip_html_tags('<div class="test">Content</div>') == "Content"

    def test_decode_html_entities(self) -> None:
        """Test HTML entity decoding."""
        assert strip_html_tags("&lt;code&gt;") == "<code>"
        assert strip_html_tags("&amp;") == "&"
        assert strip_html_tags("&quot;quoted&quot;") == '"quoted"'
        assert strip_html_tags("&#39;apostrophe&#39;") == "'apostrophe'"
        # &nbsp; decodes to non-breaking space, which gets stripped
        assert strip_html_tags("a&nbsp;b") == "a\xa0b"

    def test_strip_preserves_text(self) -> None:
        """Test that plain text is preserved."""
        assert strip_html_tags("No tags here") == "No tags here"

    def test_strip_whitespace(self) -> None:
        """Test that result is stripped."""
        assert strip_html_tags("  <p>Padded</p>  ") == "Padded"


class TestShortenPath:
    """Tests for shorten_path function."""

    def test_absolute_path_becomes_relative(self) -> None:
        """Test that absolute paths become relative to cwd."""
        import os

        cwd = os.getcwd()
        path = f"{cwd}/subdir/quiz.md"
        shortened = shorten_path(path)
        assert shortened == "./subdir/quiz.md"

    def test_sibling_path_uses_dotdot(self) -> None:
        """Test that sibling directory paths use ../"""
        import os

        # Parent dir + different subdir
        parent = os.path.dirname(os.getcwd())
        path = f"{parent}/other/quiz.md"
        shortened = shorten_path(path)
        assert shortened.startswith("../")
        assert "other/quiz.md" in shortened

    def test_relative_path_unchanged(self) -> None:
        """Test relative path stays unchanged."""
        path = "relative/path/quiz.md"
        assert shorten_path(path) == path


class TestQuizRunning:
    """Tests for quiz running functions (mocked user input)."""

    def test_run_single_choice_correct(self) -> None:
        """Test running single-choice quiz with correct answer."""
        from mkdocs_quiz.cli.runner import run_multiple_choice_quiz

        correct_answer = Answer(text="4", is_correct=True)
        quiz = Quiz(
            question="What is 2+2?",
            answers=[
                Answer(text="3", is_correct=False),
                correct_answer,
                Answer(text="5", is_correct=False),
            ],
            blanks=[],
            content=None,
            identifier="test",
            source_file=Path("test.md"),
            source_line=1,
        )

        # For single-choice, questionary.select returns the Answer object directly
        with patch("mkdocs_quiz.cli.runner.questionary") as mock_q:
            mock_q.select.return_value.unsafe_ask.return_value = correct_answer

            is_correct, correct_texts = run_multiple_choice_quiz(quiz, shuffle=False)

            assert is_correct is True
            assert "4" in correct_texts

    def test_run_single_choice_wrong(self) -> None:
        """Test running single-choice quiz with wrong answer."""
        from mkdocs_quiz.cli.runner import run_multiple_choice_quiz

        wrong_answer = Answer(text="3", is_correct=False)
        quiz = Quiz(
            question="What is 2+2?",
            answers=[
                wrong_answer,
                Answer(text="4", is_correct=True),
                Answer(text="5", is_correct=False),
            ],
            blanks=[],
            content=None,
            identifier="test",
            source_file=Path("test.md"),
            source_line=1,
        )

        with patch("mkdocs_quiz.cli.runner.questionary") as mock_q:
            mock_q.select.return_value.unsafe_ask.return_value = wrong_answer

            is_correct, _ = run_multiple_choice_quiz(quiz, shuffle=False)

            assert is_correct is False

    def test_run_multiple_choice_correct(self) -> None:
        """Test running multi-select quiz with all correct answers."""
        from mkdocs_quiz.cli.runner import run_multiple_choice_quiz

        answer_a = Answer(text="Apple", is_correct=True)
        answer_b = Answer(text="Banana", is_correct=True)
        answer_c = Answer(text="Carrot", is_correct=False)

        quiz = Quiz(
            question="Which are fruits?",
            answers=[answer_a, answer_b, answer_c],
            blanks=[],
            content=None,
            identifier="test",
            source_file=Path("test.md"),
            source_line=1,
        )

        # For multi-choice, questionary.checkbox returns list of Answer objects
        with patch("mkdocs_quiz.cli.runner.questionary") as mock_q:
            mock_q.checkbox.return_value.unsafe_ask.return_value = [answer_a, answer_b]

            is_correct, _ = run_multiple_choice_quiz(quiz, shuffle=False)

            assert is_correct is True

    def test_run_multiple_choice_wrong(self) -> None:
        """Test running multi-select quiz with incorrect selection."""
        from mkdocs_quiz.cli.runner import run_multiple_choice_quiz

        answer_a = Answer(text="Apple", is_correct=True)
        answer_b = Answer(text="Banana", is_correct=True)
        answer_c = Answer(text="Carrot", is_correct=False)

        quiz = Quiz(
            question="Which are fruits?",
            answers=[answer_a, answer_b, answer_c],
            blanks=[],
            content=None,
            identifier="test",
            source_file=Path("test.md"),
            source_line=1,
        )

        # Selected wrong answer or missing correct answer
        with patch("mkdocs_quiz.cli.runner.questionary") as mock_q:
            mock_q.checkbox.return_value.unsafe_ask.return_value = [answer_a, answer_c]

            is_correct, _ = run_multiple_choice_quiz(quiz, shuffle=False)

            assert is_correct is False

    def test_run_fill_in_blank_correct(self) -> None:
        """Test running fill-in-the-blank quiz with correct answer."""
        from mkdocs_quiz.cli.runner import run_fill_in_blank_quiz

        quiz = Quiz(
            question="The capital of France is [[Paris]].",
            answers=[],
            blanks=[Blank(correct_answer="Paris")],
            content=None,
            identifier="test",
            source_file=Path("test.md"),
            source_line=1,
        )

        with patch("mkdocs_quiz.cli.runner.questionary") as mock_q:
            mock_q.text.return_value.unsafe_ask.return_value = "Paris"

            is_correct, answers = run_fill_in_blank_quiz(quiz)

            assert is_correct is True
            assert "Paris" in answers

    def test_run_fill_in_blank_case_insensitive(self) -> None:
        """Test fill-in-the-blank is case insensitive."""
        from mkdocs_quiz.cli.runner import run_fill_in_blank_quiz

        quiz = Quiz(
            question="The capital of France is [[Paris]].",
            answers=[],
            blanks=[Blank(correct_answer="Paris")],
            content=None,
            identifier="test",
            source_file=Path("test.md"),
            source_line=1,
        )

        with patch("mkdocs_quiz.cli.runner.questionary") as mock_q:
            mock_q.text.return_value.unsafe_ask.return_value = "PARIS"

            is_correct, _ = run_fill_in_blank_quiz(quiz)

            assert is_correct is True

    def test_run_fill_in_blank_strips_whitespace(self) -> None:
        """Test fill-in-the-blank strips whitespace."""
        from mkdocs_quiz.cli.runner import run_fill_in_blank_quiz

        quiz = Quiz(
            question="The capital of France is [[Paris]].",
            answers=[],
            blanks=[Blank(correct_answer="Paris")],
            content=None,
            identifier="test",
            source_file=Path("test.md"),
            source_line=1,
        )

        with patch("mkdocs_quiz.cli.runner.questionary") as mock_q:
            mock_q.text.return_value.unsafe_ask.return_value = "  Paris  "

            is_correct, _ = run_fill_in_blank_quiz(quiz)

            assert is_correct is True


class TestRunQuizSession:
    """Tests for run_quiz_session function."""

    def test_empty_quiz_list(self) -> None:
        """Test running session with no quizzes."""
        from mkdocs_quiz.cli.runner import run_quiz_session

        with patch.dict("os.environ", {"XDG_DATA_HOME": "/tmp/test-quiz-history"}):
            correct, total = run_quiz_session([])
            assert correct == 0
            assert total == 0

    def test_keyboard_interrupt(self) -> None:
        """Test handling keyboard interrupt during session."""
        from mkdocs_quiz.cli.runner import run_quiz_session

        quiz = Quiz(
            question="Test?",
            answers=[Answer(text="Yes", is_correct=True)],
            blanks=[],
            content=None,
            identifier="test",
            source_file=Path("test.md"),
            source_line=1,
        )

        with patch("mkdocs_quiz.cli.runner.run_single_quiz") as mock_run:
            mock_run.side_effect = KeyboardInterrupt()

            with pytest.raises(KeyboardInterrupt):
                run_quiz_session([quiz])
