"""Tests for mkdocs_quiz.cli.discovery module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from mkdocs_quiz.cli.discovery import (
    _file_has_quizzes,
    find_cli_run_config,
    get_git_root,
    scan_for_quiz_files,
    validate_config_paths,
)


class TestGetGitRoot:
    """Tests for get_git_root function."""

    def test_in_git_repo(self, tmp_path: Path) -> None:
        """Test finding git root in a git repository."""
        # Create a fake .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=str(tmp_path) + "\n", stderr="")
            root = get_git_root()
            assert root is not None

    def test_not_in_git_repo(self) -> None:
        """Test when not in a git repository."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(128, "git")
            root = get_git_root()
            assert root is None

    def test_git_command_fails(self) -> None:
        """Test when git command fails."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            root = get_git_root()
            assert root is None


class TestFileHasQuizzes:
    """Tests for _file_has_quizzes function."""

    def test_file_with_quiz(self, tmp_path: Path) -> None:
        """Test detecting file with quiz tag."""
        quiz_file = tmp_path / "quiz.md"
        quiz_file.write_text("# Test\n\n<quiz>\nQuestion?\n</quiz>")

        assert _file_has_quizzes(quiz_file) is True

    def test_file_without_quiz(self, tmp_path: Path) -> None:
        """Test detecting file without quiz tag."""
        normal_file = tmp_path / "normal.md"
        normal_file.write_text("# Just a normal file\n\nNo quizzes here.")

        assert _file_has_quizzes(normal_file) is False

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        """Test handling nonexistent file."""
        assert _file_has_quizzes(tmp_path / "nonexistent.md") is False

    def test_binary_file(self, tmp_path: Path) -> None:
        """Test handling binary file."""
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03")

        # Should not raise, just return False
        assert _file_has_quizzes(binary_file) is False


class TestFindCliRunConfig:
    """Tests for find_cli_run_config function."""

    def test_find_config_in_mkdocs_quiz_yml(self, tmp_path: Path) -> None:
        """Test finding config in .mkdocs-quiz.yml."""
        config_file = tmp_path / ".mkdocs-quiz.yml"
        config_file.write_text("""
cli_run:
  chapter1: docs/chapter1.md
  chapter2: docs/chapter2.md
        """)

        config = find_cli_run_config(tmp_path)
        assert config is not None
        assert "chapter1" in config
        assert config["chapter1"] == "docs/chapter1.md"

    def test_find_config_in_mkdocs_yml(self, tmp_path: Path) -> None:
        """Test finding config in mkdocs.yml plugins section."""
        config_file = tmp_path / "mkdocs.yml"
        config_file.write_text("""
site_name: Test Site
plugins:
  - mkdocs_quiz:
      cli_run:
        quiz1: docs/quiz1.md
        """)

        config = find_cli_run_config(tmp_path)
        assert config is not None
        assert "quiz1" in config

    def test_mkdocs_quiz_yml_takes_precedence(self, tmp_path: Path) -> None:
        """Test that .mkdocs-quiz.yml takes precedence over mkdocs.yml."""
        (tmp_path / ".mkdocs-quiz.yml").write_text("""
cli_run:
  from_quiz_yml: quiz.md
        """)
        (tmp_path / "mkdocs.yml").write_text("""
plugins:
  - mkdocs_quiz:
      cli_run:
        from_mkdocs_yml: other.md
        """)

        config = find_cli_run_config(tmp_path)
        assert config is not None
        assert "from_quiz_yml" in config
        assert "from_mkdocs_yml" not in config

    def test_no_config_found(self, tmp_path: Path) -> None:
        """Test when no config file exists."""
        config = find_cli_run_config(tmp_path)
        assert config is None

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        """Test handling invalid YAML."""
        config_file = tmp_path / ".mkdocs-quiz.yml"
        config_file.write_text("invalid: yaml: content: [[[")

        config = find_cli_run_config(tmp_path)
        assert config is None

    def test_cli_run_not_dict(self, tmp_path: Path) -> None:
        """Test when cli_run is not a dict."""
        config_file = tmp_path / ".mkdocs-quiz.yml"
        config_file.write_text("""
cli_run: "not a dict"
        """)

        config = find_cli_run_config(tmp_path)
        assert config is None


class TestValidateConfigPaths:
    """Tests for validate_config_paths function."""

    def test_validate_existing_paths(self, tmp_path: Path) -> None:
        """Test validating config with existing paths."""
        # Create quiz files
        (tmp_path / "quiz1.md").write_text("<quiz>Q1</quiz>")
        (tmp_path / "quiz2.md").write_text("<quiz>Q2</quiz>")

        config = {
            "Quiz 1": "quiz1.md",
            "Quiz 2": "quiz2.md",
        }

        validated = validate_config_paths(config, tmp_path)
        assert validated is not None
        assert "Quiz 1" in validated
        assert "Quiz 2" in validated

    def test_validate_removes_nonexistent_paths(self, tmp_path: Path) -> None:
        """Test that nonexistent paths are removed."""
        (tmp_path / "exists.md").write_text("<quiz>Q</quiz>")

        config = {
            "Exists": "exists.md",
            "Missing": "nonexistent.md",
        }

        validated = validate_config_paths(config, tmp_path)
        assert validated is not None
        assert "Exists" in validated
        assert "Missing" not in validated

    def test_validate_nested_config(self, tmp_path: Path) -> None:
        """Test validating nested config structure."""
        (tmp_path / "quiz1.md").write_text("<quiz>Q1</quiz>")
        (tmp_path / "quiz2.md").write_text("<quiz>Q2</quiz>")

        config = {
            "Category": {
                "Quiz 1": "quiz1.md",
                "Quiz 2": "quiz2.md",
            }
        }

        validated = validate_config_paths(config, tmp_path)
        assert validated is not None
        assert "Category" in validated
        assert "Quiz 1" in validated["Category"]

    def test_validate_empty_nested_removed(self, tmp_path: Path) -> None:
        """Test that empty nested dicts are removed."""
        config = {
            "Empty Category": {
                "Missing": "nonexistent.md",
            },
            "Valid": "also_missing.md",  # This is also missing
        }

        validated = validate_config_paths(config, tmp_path)
        assert validated is None  # All paths invalid

    def test_validate_empty_config(self, tmp_path: Path) -> None:
        """Test validating empty config."""
        validated = validate_config_paths({}, tmp_path)
        assert validated is None


class TestScanForQuizFiles:
    """Tests for scan_for_quiz_files function."""

    def test_scan_finds_quiz_files(self, tmp_path: Path) -> None:
        """Test scanning finds markdown files with quizzes."""
        # Create quiz files
        (tmp_path / "quiz1.md").write_text("<quiz>Q1</quiz>")
        (tmp_path / "quiz2.md").write_text("<quiz>Q2</quiz>")
        (tmp_path / "no_quiz.md").write_text("# No quiz here")

        # Mock git ls-files to return our files
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="quiz1.md\nquiz2.md\nno_quiz.md\n", returncode=0
            )

            files = scan_for_quiz_files(tmp_path)

            # Should find only files with quizzes
            assert len(files) == 2
            assert any("quiz1.md" in str(f) for f in files)
            assert any("quiz2.md" in str(f) for f in files)

    def test_scan_git_fails(self, tmp_path: Path) -> None:
        """Test scanning when git command fails."""
        import subprocess

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            files = scan_for_quiz_files(tmp_path)
            assert files == []

    def test_scan_no_markdown_files(self, tmp_path: Path) -> None:
        """Test scanning when no markdown files exist."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="file.txt\nimage.png\n", returncode=0)

            files = scan_for_quiz_files(tmp_path)
            assert files == []
