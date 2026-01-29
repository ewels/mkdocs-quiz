"""Tests for mkdocs_quiz.cli.history module."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from mkdocs_quiz.cli.history import (
    QuizResult,
    format_time_ago,
    get_all_results,
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
            correct=8,
            total=10,
            percentage=80.0,
            timestamp="2024-01-15T10:30:00+00:00",
        )
        assert result.correct == 8
        assert result.total == 10
        assert result.percentage == 80.0

    def test_result_to_dict(self) -> None:
        """Test converting QuizResult to dict."""
        from dataclasses import asdict

        result = QuizResult(
            correct=5,
            total=5,
            percentage=100.0,
            timestamp="2024-01-15T10:30:00+00:00",
        )
        d = asdict(result)
        assert d["correct"] == 5


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
                correct=5,
                total=10,
                percentage=50.0,
                timestamp="2024-01-15T10:30:00+00:00",
            )
            history = {"/test.md": [result]}
            save_history(history)

            loaded = load_history()
            assert "/test.md" in loaded
            assert len(loaded["/test.md"]) == 1
            assert loaded["/test.md"][0].correct == 5

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

    def test_save_result_appends(self, tmp_path: Path) -> None:
        """Test that saving appends to history (keeps all results)."""
        with patch.dict("os.environ", {"XDG_DATA_HOME": str(tmp_path)}):
            save_result("/path/to/quiz.md", correct=5, total=10)
            save_result("/path/to/quiz.md", correct=10, total=10)

            # get_previous_result returns the most recent
            result = get_previous_result("/path/to/quiz.md")
            assert result is not None
            assert result.correct == 10

            # get_all_results returns all results
            all_results = get_all_results("/path/to/quiz.md")
            assert len(all_results) == 2
            assert all_results[0].correct == 5
            assert all_results[1].correct == 10


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
