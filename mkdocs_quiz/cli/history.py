"""Quiz history storage and retrieval."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Length of hash prefix used for quiz keys. 16 hex chars = 64 bits,
# giving ~4 billion possible keys before 50% collision probability.
QUIZ_KEY_LENGTH = 16


@dataclass
class QuizResult:
    """A single quiz result."""

    quiz_path: str
    correct: int
    total: int
    percentage: float
    timestamp: str  # ISO format

    @property
    def datetime(self) -> datetime:
        """Parse timestamp to datetime."""
        return datetime.fromisoformat(self.timestamp)


def get_history_dir() -> Path:
    """Get the directory for storing quiz history.

    Uses XDG_DATA_HOME on Linux, appropriate paths on macOS/Windows.

    Returns:
        Path to the mkdocs-quiz data directory.
    """
    # Check XDG_DATA_HOME first (Linux standard)
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        base = Path(xdg_data)
    elif os.name == "nt":
        # Windows: use LOCALAPPDATA
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    else:
        # macOS/Linux fallback: ~/.local/share
        base = Path.home() / ".local" / "share"

    return base / "mkdocs-quiz"


def get_history_file() -> Path:
    """Get the path to the history JSON file."""
    return get_history_dir() / "history.json"


def _get_quiz_key(quiz_path: str) -> str:
    """Generate a unique key for a quiz path.

    Uses a hash to handle long paths and special characters.

    Args:
        quiz_path: The path to the quiz file.

    Returns:
        A unique key string.
    """
    # Normalize the path and create a hash
    normalized = os.path.normpath(quiz_path)
    return hashlib.sha256(normalized.encode()).hexdigest()[:QUIZ_KEY_LENGTH]


def load_history() -> dict[str, QuizResult]:
    """Load quiz history from disk.

    Returns:
        Dictionary mapping quiz keys to QuizResult objects.
    """
    history_file = get_history_file()
    if not history_file.exists():
        return {}

    try:
        data = json.loads(history_file.read_text(encoding="utf-8"))
        return {
            key: QuizResult(**result) for key, result in data.items() if isinstance(result, dict)
        }
    except (json.JSONDecodeError, OSError, TypeError) as e:
        logger.warning("Failed to load quiz history from %s: %s", history_file, e)
        return {}


def save_history(history: dict[str, QuizResult]) -> None:
    """Save quiz history to disk.

    Args:
        history: Dictionary mapping quiz keys to QuizResult objects.
    """
    history_dir = get_history_dir()
    history_dir.mkdir(parents=True, exist_ok=True)

    history_file = get_history_file()
    data = {key: asdict(result) for key, result in history.items()}

    history_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_previous_result(quiz_path: str) -> QuizResult | None:
    """Get the previous result for a quiz.

    Args:
        quiz_path: The path to the quiz file.

    Returns:
        QuizResult if found, None otherwise.
    """
    history = load_history()
    key = _get_quiz_key(quiz_path)
    return history.get(key)


def save_result(quiz_path: str, correct: int, total: int) -> None:
    """Save a quiz result.

    Args:
        quiz_path: The path to the quiz file.
        correct: Number of correct answers.
        total: Total number of questions.
    """
    history = load_history()
    key = _get_quiz_key(quiz_path)

    percentage = (correct / total * 100) if total > 0 else 0.0
    result = QuizResult(
        quiz_path=quiz_path,
        correct=correct,
        total=total,
        percentage=percentage,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    history[key] = result
    save_history(history)


def format_time_ago(dt: datetime) -> str:
    """Format a datetime as a human-readable 'time ago' string.

    Args:
        dt: The datetime to format.

    Returns:
        Human-readable string like "2 hours ago" or "3 days ago".
    """
    now = datetime.now(timezone.utc)

    # Ensure dt is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    seconds = (now - dt).total_seconds()

    if seconds < 60:
        return "just now"

    # (threshold_seconds, divisor, unit_name)
    thresholds = [
        (3600, 60, "minute"),
        (86400, 3600, "hour"),
        (604800, 86400, "day"),
        (2592000, 604800, "week"),
        (float("inf"), 2592000, "month"),
    ]

    for threshold, divisor, unit in thresholds:
        if seconds < threshold:
            value = int(seconds / divisor)
            plural = "s" if value != 1 else ""
            return f"{value} {unit}{plural} ago"

    return "a long time ago"  # Unreachable but satisfies type checker
