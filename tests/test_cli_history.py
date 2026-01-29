"""Tests for mkdocs_quiz.cli.history module."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from mkdocs_quiz.cli.history import (
    QUIZ_KEY_LENGTH,
    QuizResult,
    _get_quiz_key,
    format_time_ago,
    get_history_dir,
    get_history_file,
    get_previous_result,
    load_history,
    save_history,
    save_result,
)


class TestQuizResult:
    """Tests for QuizResult dataclass."""

    def test_create_result(self) -> None:
        """Test creating a QuizResult."""
        result = QuizResult(
            quiz_path="/path/to/quiz.md",
            correct=8,
            total=10,
            percentage=80.0,
            timestamp="2024-01-15T10:30:00+00:00",
        )
        assert result.quiz_path == "/path/to/quiz.md"
        assert result.correct == 8
        assert result.total == 10
        assert result.percentage == 80.0

    def test_result_to_dict(self) -> None:
        """Test converting QuizResult to dict."""
        from dataclasses import asdict

        result = QuizResult(
            quiz_path="/path/to/quiz.md",
            correct=5,
            total=5,
            percentage=100.0,
            timestamp="2024-01-15T10:30:00+00:00",
        )
        d = asdict(result)
        assert d["quiz_path"] == "/path/to/quiz.md"
        assert d["correct"] == 5


class TestGetQuizKey:
    """Tests for _get_quiz_key function."""

    def test_key_length(self) -> None:
        """Test that key has correct length."""
        key = _get_quiz_key("/some/path/to/quiz.md")
        assert len(key) == QUIZ_KEY_LENGTH

    def test_key_is_hex(self) -> None:
        """Test that key is valid hex string."""
        key = _get_quiz_key("/some/path.md")
        assert all(c in "0123456789abcdef" for c in key)

    def test_same_path_same_key(self) -> None:
        """Test that same path produces same key."""
        path = "/path/to/quiz.md"
        assert _get_quiz_key(path) == _get_quiz_key(path)

    def test_different_paths_different_keys(self) -> None:
        """Test that different paths produce different keys."""
        key1 = _get_quiz_key("/path/one.md")
        key2 = _get_quiz_key("/path/two.md")
        assert key1 != key2

    def test_normalizes_path(self) -> None:
        """Test that paths are normalized."""
        # These should produce the same key
        key1 = _get_quiz_key("/path/to/quiz.md")
        key2 = _get_quiz_key("/path/to/../to/quiz.md")
        assert key1 == key2


class TestHistoryDir:
    """Tests for history directory functions."""

    def test_get_history_dir_default(self) -> None:
        """Test default history directory."""
        with patch.dict("os.environ", {}, clear=True):
            history_dir = get_history_dir()
            assert history_dir.name == "mkdocs-quiz"
            assert ".local/share" in str(history_dir) or "Library" in str(history_dir)

    def test_get_history_dir_xdg(self, tmp_path: Path) -> None:
        """Test XDG_DATA_HOME is respected."""
        with patch.dict("os.environ", {"XDG_DATA_HOME": str(tmp_path)}):
            history_dir = get_history_dir()
            assert history_dir == tmp_path / "mkdocs-quiz"

    def test_get_history_file(self, tmp_path: Path) -> None:
        """Test history file path."""
        with patch.dict("os.environ", {"XDG_DATA_HOME": str(tmp_path)}):
            history_file = get_history_file()
            assert history_file.name == "history.json"
            assert history_file.parent.name == "mkdocs-quiz"


class TestLoadSaveHistory:
    """Tests for loading and saving history."""

    def test_load_empty_history(self, tmp_path: Path) -> None:
        """Test loading when no history file exists."""
        with patch.dict("os.environ", {"XDG_DATA_HOME": str(tmp_path)}):
            history = load_history()
            assert history == {}

    def test_save_and_load_history(self, tmp_path: Path) -> None:
        """Test saving and loading history."""
        with patch.dict("os.environ", {"XDG_DATA_HOME": str(tmp_path)}):
            result = QuizResult(
                quiz_path="/test.md",
                correct=5,
                total=10,
                percentage=50.0,
                timestamp="2024-01-15T10:30:00+00:00",
            )
            history = {"test_key": result}
            save_history(history)

            loaded = load_history()
            assert "test_key" in loaded
            assert loaded["test_key"].correct == 5

    def test_load_corrupted_history(self, tmp_path: Path) -> None:
        """Test loading corrupted history file returns empty dict."""
        with patch.dict("os.environ", {"XDG_DATA_HOME": str(tmp_path)}):
            history_dir = tmp_path / "mkdocs-quiz"
            history_dir.mkdir(parents=True)
            history_file = history_dir / "history.json"
            history_file.write_text("not valid json {{{")

            history = load_history()
            assert history == {}


class TestSaveResult:
    """Tests for save_result function."""

    def test_save_result(self, tmp_path: Path) -> None:
        """Test saving a quiz result."""
        with patch.dict("os.environ", {"XDG_DATA_HOME": str(tmp_path)}):
            save_result("/path/to/quiz.md", correct=7, total=10)

            result = get_previous_result("/path/to/quiz.md")
            assert result is not None
            assert result.correct == 7
            assert result.total == 10
            assert result.percentage == 70.0

    def test_save_result_overwrites(self, tmp_path: Path) -> None:
        """Test that saving overwrites previous result."""
        with patch.dict("os.environ", {"XDG_DATA_HOME": str(tmp_path)}):
            save_result("/path/to/quiz.md", correct=5, total=10)
            save_result("/path/to/quiz.md", correct=10, total=10)

            result = get_previous_result("/path/to/quiz.md")
            assert result is not None
            assert result.correct == 10


class TestGetPreviousResult:
    """Tests for get_previous_result function."""

    def test_no_previous_result(self, tmp_path: Path) -> None:
        """Test when no previous result exists."""
        with patch.dict("os.environ", {"XDG_DATA_HOME": str(tmp_path)}):
            result = get_previous_result("/nonexistent/quiz.md")
            assert result is None


class TestFormatTimeAgo:
    """Tests for format_time_ago function."""

    def test_just_now(self) -> None:
        """Test formatting time from just now."""
        now = datetime.now(timezone.utc)
        assert format_time_ago(now) == "just now"

    def test_minutes_ago(self) -> None:
        """Test formatting minutes ago."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=5)
        assert format_time_ago(past) == "5 minutes ago"

    def test_one_minute_ago(self) -> None:
        """Test singular minute."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=1)
        assert format_time_ago(past) == "1 minute ago"

    def test_hours_ago(self) -> None:
        """Test formatting hours ago."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=3)
        assert format_time_ago(past) == "3 hours ago"

    def test_days_ago(self) -> None:
        """Test formatting days ago."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        past = now - timedelta(days=2)
        assert format_time_ago(past) == "2 days ago"

    def test_weeks_ago(self) -> None:
        """Test formatting weeks ago."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        past = now - timedelta(weeks=2)
        assert format_time_ago(past) == "2 weeks ago"

    def test_months_ago(self) -> None:
        """Test formatting months ago."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        past = now - timedelta(days=60)
        assert format_time_ago(past) == "2 months ago"

    def test_naive_datetime(self) -> None:
        """Test that naive datetime is handled."""
        from datetime import timedelta

        now = datetime.now(timezone.utc)
        past = (now - timedelta(hours=2)).replace(tzinfo=None)
        result = format_time_ago(past)
        assert "hour" in result
