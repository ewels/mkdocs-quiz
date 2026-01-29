"""Tests for CLI entry points (mkdocs-quiz and quiz aliases)."""

from __future__ import annotations

from click.testing import CliRunner

from mkdocs_quiz import __version__
from mkdocs_quiz.cli.main import cli


class TestCLIEntryPoints:
    """Tests for CLI entry point aliases."""

    def test_cli_version(self) -> None:
        """Test that --version outputs correctly."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.output
        assert "mkdocs-quiz" in result.output

    def test_cli_help(self) -> None:
        """Test that --help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "MkDocs Quiz CLI" in result.output

    def test_cli_subcommands_available(self) -> None:
        """Test that main subcommands are available."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # Check that main subcommands are listed
        assert "run" in result.output
        assert "history" in result.output
        assert "export" in result.output
        assert "migrate" in result.output
        assert "translations" in result.output

    def test_quiz_alias_uses_same_entry_point(self) -> None:
        """Test that 'quiz' entry point is registered to the same function."""
        # Import the entry point function from both locations
        from mkdocs_quiz.cli import main
        from mkdocs_quiz.cli.main import main as main_direct

        # Both should be the same function
        assert main is main_direct

    def test_both_entry_points_defined_in_pyproject(self) -> None:
        """Test that both mkdocs-quiz and quiz entry points are defined."""
        # Read pyproject.toml and verify both entry points exist
        import sys
        from pathlib import Path

        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib

        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        scripts = pyproject.get("project", {}).get("scripts", {})

        # Both entry points should be defined
        assert "mkdocs-quiz" in scripts, "mkdocs-quiz entry point not found"
        assert "quiz" in scripts, "quiz entry point not found"

        # Both should point to the same module
        assert scripts["mkdocs-quiz"] == "mkdocs_quiz.cli:main"
        assert scripts["quiz"] == "mkdocs_quiz.cli:main"

    def test_run_subcommand_help(self) -> None:
        """Test that 'run' subcommand help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "Run quizzes interactively" in result.output

    def test_history_subcommand_help(self) -> None:
        """Test that 'history' subcommand help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["history", "--help"])
        assert result.exit_code == 0
        assert "Show quiz results history" in result.output

    def test_translations_subcommand_help(self) -> None:
        """Test that 'translations' subcommand help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["translations", "--help"])
        assert result.exit_code == 0
        assert "Manage translation files" in result.output
