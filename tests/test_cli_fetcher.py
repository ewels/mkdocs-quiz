"""Tests for mkdocs_quiz.cli.fetcher module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mkdocs_quiz.cli.fetcher import (
    extract_quiz_sources_from_html,
    fetch_quizzes,
    is_url,
    parse_quiz_from_source,
)


class TestIsUrl:
    """Tests for is_url function."""

    def test_http_url(self) -> None:
        """Test HTTP URLs are detected."""
        assert is_url("http://example.com") is True
        assert is_url("http://example.com/path/to/page") is True

    def test_https_url(self) -> None:
        """Test HTTPS URLs are detected."""
        assert is_url("https://example.com") is True
        assert is_url("https://example.com/quiz.html") is True

    def test_local_path(self) -> None:
        """Test local paths are not URLs."""
        assert is_url("/path/to/file.md") is False
        assert is_url("./relative/path.md") is False
        assert is_url("file.md") is False

    def test_file_url(self) -> None:
        """Test file:// URLs are not treated as remote URLs."""
        assert is_url("file:///path/to/file") is False

    def test_empty_string(self) -> None:
        """Test empty string is not a URL."""
        assert is_url("") is False


class TestExtractQuizSourcesFromHtml:
    """Tests for extract_quiz_sources_from_html function."""

    def test_extract_single_source(self) -> None:
        """Test extracting a single quiz source."""
        # Note: Pattern requires newline after "mkdocs-quiz-source" and before "-->"
        html = """<!-- mkdocs-quiz-source
<quiz>
What is 2+2?
- [ ] 3
- [x] 4
- [ ] 5
</quiz>
-->"""
        sources = extract_quiz_sources_from_html(html)
        assert len(sources) == 1
        assert "What is 2+2?" in sources[0]

    def test_extract_multiple_sources(self) -> None:
        """Test extracting multiple quiz sources."""
        html = """<!-- mkdocs-quiz-source
<quiz>Quiz 1
- [x] A
</quiz>
-->
<div>Some content</div>
<!-- mkdocs-quiz-source
<quiz>Quiz 2
- [x] B
</quiz>
-->"""
        sources = extract_quiz_sources_from_html(html)
        assert len(sources) == 2
        assert "Quiz 1" in sources[0]
        assert "Quiz 2" in sources[1]

    def test_no_quiz_sources(self) -> None:
        """Test HTML with no quiz sources."""
        html = "<html><body>No quizzes here</body></html>"
        sources = extract_quiz_sources_from_html(html)
        assert sources == []

    def test_preserves_quiz_content(self) -> None:
        """Test that quiz content is preserved correctly."""
        html = """<!-- mkdocs-quiz-source
<quiz>
What is Python?
- [x] A programming language
- [ ] A snake

---
Python is both!
</quiz>
-->"""
        sources = extract_quiz_sources_from_html(html)
        assert len(sources) == 1
        assert "A programming language" in sources[0]
        assert "Python is both!" in sources[0]


class TestParseQuizFromSource:
    """Tests for parse_quiz_from_source function."""

    def test_parse_multiple_choice_quiz(self) -> None:
        """Test parsing a multiple choice quiz."""
        source = """
        <quiz>
        What is 2+2?
        - [ ] 3
        - [x] 4
        - [ ] 5
        </quiz>
        """
        quiz = parse_quiz_from_source(source, "http://example.com", 0)
        assert quiz is not None
        assert "2+2" in quiz.question
        assert len(quiz.answers) == 3
        assert quiz.answers[1].is_correct is True
        assert quiz.answers[0].is_correct is False

    def test_parse_fill_in_blank_quiz(self) -> None:
        """Test parsing a fill-in-the-blank quiz."""
        source = """
        <quiz>
        The capital of France is [[Paris]].
        </quiz>
        """
        quiz = parse_quiz_from_source(source, "http://example.com", 0)
        assert quiz is not None
        assert "capital of France" in quiz.question
        assert len(quiz.blanks) == 1
        assert quiz.blanks[0].correct_answer == "Paris"

    def test_parse_quiz_with_content(self) -> None:
        """Test parsing quiz with explanation content."""
        source = """
        <quiz>
        What is Python?
        - [x] A programming language
        - [ ] A snake

        ---
        Python was created by Guido van Rossum.
        </quiz>
        """
        quiz = parse_quiz_from_source(source, "http://example.com", 0)
        assert quiz is not None
        assert quiz.content is not None
        assert "Guido" in quiz.content

    def test_parse_quiz_no_correct_answer(self) -> None:
        """Test parsing quiz with no correct answer still parses (validation separate)."""
        source = """<quiz>
No correct answer?
- [ ] A
- [ ] B
</quiz>"""
        quiz = parse_quiz_from_source(source, "http://example.com", 0)
        # Quiz parses but has no correct answers (validation is separate)
        assert quiz is not None
        assert len(quiz.answers) == 2
        assert all(not a.is_correct for a in quiz.answers)

    def test_parse_no_quiz_tags(self) -> None:
        """Test parsing content without quiz tags."""
        source = "Just some text without quiz tags"
        quiz = parse_quiz_from_source(source, "http://example.com", 0)
        assert quiz is None

    def test_multiple_correct_answers(self) -> None:
        """Test parsing quiz with multiple correct answers."""
        source = """
        <quiz>
        Which are fruits?
        - [x] Apple
        - [ ] Carrot
        - [x] Banana
        </quiz>
        """
        quiz = parse_quiz_from_source(source, "http://example.com", 0)
        assert quiz is not None
        correct_count = sum(1 for a in quiz.answers if a.is_correct)
        assert correct_count == 2


class TestFetchQuizzes:
    """Tests for fetch_quizzes function."""

    def test_fetch_from_local_file(self, tmp_path: Path) -> None:
        """Test fetching quizzes from a local markdown file."""
        quiz_file = tmp_path / "quiz.md"
        quiz_file.write_text("""
# Test Quiz

<quiz>
What is 1+1?
- [ ] 1
- [x] 2
- [ ] 3
</quiz>
        """)

        quizzes = fetch_quizzes(str(quiz_file))
        assert len(quizzes) == 1
        assert "1+1" in quizzes[0].question

    def test_fetch_from_local_directory(self, tmp_path: Path) -> None:
        """Test fetching quizzes from a directory."""
        (tmp_path / "quiz1.md").write_text("""
<quiz>
Question 1?
- [x] Yes
- [ ] No
</quiz>
        """)
        (tmp_path / "quiz2.md").write_text("""
<quiz>
Question 2?
- [ ] Yes
- [x] No
</quiz>
        """)

        quizzes = fetch_quizzes(str(tmp_path))
        assert len(quizzes) == 2

    def test_fetch_nonexistent_path(self) -> None:
        """Test fetching from nonexistent path raises error."""
        with pytest.raises(FileNotFoundError):
            fetch_quizzes("/nonexistent/path/to/quiz.md")

    def test_fetch_from_url(self) -> None:
        """Test fetching quizzes from a URL."""
        mock_html = """<!-- mkdocs-quiz-source
<quiz>
URL Quiz?
- [x] Yes
- [ ] No
</quiz>
-->"""
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.raise_for_status = MagicMock()

        with patch("mkdocs_quiz.cli.fetcher.requests.get", return_value=mock_response):
            quizzes = fetch_quizzes("https://example.com/quiz.html")
            assert len(quizzes) == 1
            assert "URL Quiz" in quizzes[0].question

    def test_fetch_empty_directory(self, tmp_path: Path) -> None:
        """Test fetching from empty directory returns empty list."""
        quizzes = fetch_quizzes(str(tmp_path))
        assert quizzes == []

    def test_fetch_url_no_quizzes(self) -> None:
        """Test fetching from URL with no quizzes raises ValueError."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>No quizzes</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("mkdocs_quiz.cli.fetcher.requests.get", return_value=mock_response):  # noqa: SIM117
            with pytest.raises(ValueError, match="No quizzes found"):
                fetch_quizzes("https://example.com/page.html")
