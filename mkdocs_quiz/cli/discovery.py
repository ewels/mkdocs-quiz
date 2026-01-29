"""Discovery and interactive selection for quiz files."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import questionary
import yaml  # type: ignore[import-untyped]

from .runner import console

logger = logging.getLogger(__name__)

BACK_OPTION = "← Back"


def get_git_root() -> Path | None:
    """Get the root of the current git repository.

    Returns:
        Path to git root, or None if not in a git repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def find_cli_run_config(git_root: Path) -> dict | None:
    """Look for cli_run config in config files.

    Checks in order of priority:
    1. .mkdocs-quiz.yml (takes priority if exists)
    2. mkdocs.yml under plugins.mkdocs_quiz.cli_run

    Args:
        git_root: Path to the git repository root.

    Returns:
        The cli_run config dict, or None if not found.
    """
    # Check .mkdocs-quiz.yml first (takes priority)
    quiz_config_path = git_root / ".mkdocs-quiz.yml"
    if quiz_config_path.exists():
        try:
            data = yaml.safe_load(quiz_config_path.read_text(encoding="utf-8"))
            if data and isinstance(data, dict) and "cli_run" in data:
                cli_run = data["cli_run"]
                return cli_run if isinstance(cli_run, dict) else None
        except (yaml.YAMLError, OSError) as e:
            console.print(f"[yellow]Warning: Failed to parse .mkdocs-quiz.yml: {e}[/yellow]")

    # Check mkdocs.yml
    mkdocs_config_path = git_root / "mkdocs.yml"
    if mkdocs_config_path.exists():
        try:
            # Create a custom loader that ignores unknown tags (like !!python/name)
            # This is needed because MkDocs configs often use Python-specific tags
            class _SafeLoaderIgnoreUnknown(yaml.SafeLoader):
                pass

            def _ignore_unknown(loader: yaml.SafeLoader, tag_suffix: str, node: yaml.Node) -> None:
                return None

            _SafeLoaderIgnoreUnknown.add_multi_constructor("", _ignore_unknown)

            data = yaml.load(
                mkdocs_config_path.read_text(encoding="utf-8"),
                Loader=_SafeLoaderIgnoreUnknown,
            )
            if data and isinstance(data, dict):
                plugins = data.get("plugins", [])
                for plugin in plugins:
                    if isinstance(plugin, dict) and "mkdocs_quiz" in plugin:
                        plugin_config = plugin["mkdocs_quiz"]
                        if isinstance(plugin_config, dict) and "cli_run" in plugin_config:
                            cli_run = plugin_config["cli_run"]
                            return cli_run if isinstance(cli_run, dict) else None
        except (yaml.YAMLError, OSError) as e:
            console.print(f"[yellow]Warning: Failed to parse mkdocs.yml: {e}[/yellow]")

    return None


def _file_has_quizzes(file_path: Path) -> bool:
    """Check if a file contains quiz tags.

    Args:
        file_path: Path to the markdown file.

    Returns:
        True if the file contains <quiz> tags.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return "<quiz>" in content
    except OSError:
        return False


def validate_config_paths(config: dict, git_root: Path) -> dict | None:
    """Recursively validate config paths and prune invalid entries.

    Checks that each file path exists and contains quizzes.
    Logs warnings for invalid paths.
    Prunes empty branches after removing invalid paths.

    Args:
        config: The terminal_run config dict.
        git_root: Path to the git repository root.

    Returns:
        Filtered config with only valid paths, or None if all invalid.
    """

    def validate_recursive(node: dict | str, path_prefix: str = "") -> dict | str | None:
        if isinstance(node, str):
            # Leaf node - this is a file path
            file_path = git_root / node
            if not file_path.exists():
                console.print(f"[yellow]Warning: Quiz file not found: {node}[/yellow]")
                return None
            if not _file_has_quizzes(file_path):
                console.print(f"[yellow]Warning: File contains no quizzes: {node}[/yellow]")
                return None
            return node

        if isinstance(node, dict):
            # Branch node - recurse into children
            validated: dict = {}
            for key, value in node.items():
                result = validate_recursive(value, f"{path_prefix}/{key}")
                if result is not None:
                    validated[key] = result

            # Return None if all children were pruned
            return validated if validated else None

        return None

    result = validate_recursive(config)
    return result if isinstance(result, dict) else None


def scan_for_quiz_files(git_root: Path) -> list[Path]:
    """Find all tracked markdown files containing quiz tags.

    Uses 'git ls-files' to respect .gitignore and only scan tracked files.

    Args:
        git_root: Path to the git repository root.

    Returns:
        Sorted list of relative paths to files containing quizzes.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "*.md"],
            cwd=git_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug("git ls-files failed: %s", e)
        return []

    quiz_files = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        md_file = git_root / line
        if _file_has_quizzes(md_file):
            quiz_files.append(Path(line))

    return sorted(quiz_files)


def interactive_config_selection(config: dict) -> str | None:
    """Recursively prompt user through nested config until a file is selected.

    Shows a questionary.select() at each level with a "← Back" option
    (except at the root level).

    Args:
        config: The validated terminal_run config dict.

    Returns:
        Selected file path, or None if user backs out of root.
    """
    history: list[dict] = []  # Stack of parent nodes
    current = config

    while True:
        choices = list(current.keys())

        # Add back option if not at root
        if history:
            choices = [*choices, BACK_OPTION]

        try:
            selected = questionary.select(
                "Select a quiz:",
                choices=choices,
            ).unsafe_ask()
        except KeyboardInterrupt:
            return None

        if selected == BACK_OPTION:
            current = history.pop()
            continue

        value = current[selected]

        if isinstance(value, str):
            # Leaf node - return the file path
            return value

        # Branch node - go deeper
        history.append(current)
        current = value


def interactive_file_selection(quiz_files: list[Path]) -> str | None:
    """Show a select menu for choosing a quiz file.

    Args:
        quiz_files: List of relative paths to quiz files.

    Returns:
        Selected file path as string, or None if cancelled.
    """
    if not quiz_files:
        return None

    choices = [str(f) for f in quiz_files]

    try:
        selected = questionary.select(
            "Select a quiz file:",
            choices=choices,
        ).unsafe_ask()
        return selected if selected else None
    except KeyboardInterrupt:
        return None


def _print_header() -> None:
    """Print the mkdocs-quiz header with branding."""
    from .runner import display_quiz_header

    # Use runner's header but without quiz_path (no previous result lookup)
    display_quiz_header(quiz_path=None)


def interactive_quiz_selection() -> str | None:
    """Main entry point for interactive quiz selection.

    Orchestrates the full discovery and selection flow:
    1. Check if in git repository
    2. Look for terminal_run config
    3. If config found, validate and show nested menu
    4. Otherwise scan for quiz files and show select menu
    5. Return selected path or None

    Returns:
        Absolute path to selected quiz file, or None to show help.
    """
    # Check if we're in a git repository
    git_root = get_git_root()
    if git_root is None:
        console.print("[yellow]Not in a git repository.[/yellow]")
        console.print("[dim]Run with a path argument, or run from within a git repository.[/dim]")
        return None

    # Print header before showing selection
    _print_header()

    # Look for config file
    config = find_cli_run_config(git_root)

    if config is not None:
        # Validate config paths
        validated_config = validate_config_paths(config, git_root)

        if validated_config:
            # Show interactive config selection
            selected = interactive_config_selection(validated_config)
            if selected:
                return str(git_root / selected)
            return None

        # Config was found but all paths invalid - fall through to scanning
        console.print(
            "[yellow]No valid quiz files found in config, scanning repository...[/yellow]"
        )

    # Scan for quiz files
    quiz_files = scan_for_quiz_files(git_root)

    if not quiz_files:
        console.print("[yellow]No quiz files found in repository.[/yellow]")
        return None

    # Show file selection
    selected = interactive_file_selection(quiz_files)
    if selected:
        return str(git_root / selected)

    return None
