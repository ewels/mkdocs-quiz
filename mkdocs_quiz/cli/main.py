"""Command-line interface for mkdocs-quiz."""

from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import polib
import rich_click as click

from mkdocs_quiz import __version__

from .runner import console, get_score_color, shorten_path

if TYPE_CHECKING:
    from ..qti.models import Quiz

# Configure rich-click
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.COMMAND_GROUPS = {
    "mkdocs-quiz": [
        {
            "name": "Commands",
            "commands": ["run", "history", "export", "migrate", "translations"],
        }
    ]
}


def _fetch_quizzes_or_exit(path: str) -> list[Quiz]:
    """Fetch quizzes from path, printing errors and exiting on failure."""
    from requests import RequestException  # type: ignore[import-untyped]

    from .fetcher import fetch_quizzes

    try:
        return fetch_quizzes(path)
    except (FileNotFoundError, ValueError, RequestException) as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def convert_quiz_block(quiz_content: str) -> str:
    """Convert old quiz syntax to new markdown-style syntax.

    Args:
        quiz_content: The content inside <?quiz?> tags in old format.

    Returns:
        The converted quiz content in new format.
    """
    question = None
    answers: list[tuple[bool, str]] = []  # (is_correct, text)
    content_lines: list[str] = []
    options: list[str] = []
    in_content = False

    # Map of line prefixes to their handlers
    preserved_options = ("show-correct:", "auto-submit:", "disable-after-submit:")

    for line in quiz_content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("question:"):
            question = line.split(":", 1)[1].strip()
        elif line.startswith(preserved_options):
            options.append(line)
        elif line == "content:":
            in_content = True
        elif line.startswith("answer-correct:"):
            answers.append((True, line.split(":", 1)[1].strip()))
        elif line.startswith("answer:"):
            answers.append((False, line.split(":", 1)[1].strip()))
        elif in_content:
            content_lines.append(line)

    # Build new quiz format
    result = ["<quiz>"]
    if question:
        result.append(question)
    result.extend(options)
    result.extend(f"- [{'x' if is_correct else ' '}] {text}" for is_correct, text in answers)
    if content_lines:
        result.append("")
        result.extend(content_lines)
    result.append("</quiz>")

    return "\n".join(result)


def migrate_file(file_path: Path, dry_run: bool = False) -> tuple[int, bool]:
    """Migrate quiz blocks in a single file.

    Args:
        file_path: Path to the markdown file.
        dry_run: If True, don't write changes to disk.

    Returns:
        Tuple of (number of quizzes converted, whether file was modified).
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        console.print(f"  [red]Error reading {file_path}: {e}[/red]")
        return 0, False

    # Pattern to match quiz blocks
    quiz_pattern = r"<\?quiz\?>(.*?)<\?/quiz\?>"

    def replace_quiz(match: re.Match[str]) -> str:
        return convert_quiz_block(match.group(1))

    # Count how many quizzes will be converted
    quiz_count = len(re.findall(quiz_pattern, content, re.DOTALL))

    if quiz_count == 0:
        return 0, False

    # Replace all quiz blocks
    new_content = re.sub(quiz_pattern, replace_quiz, content, flags=re.DOTALL)

    if new_content == content:
        return 0, False

    if not dry_run:
        # Write new content
        file_path.write_text(new_content, encoding="utf-8")

    return quiz_count, True


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="mkdocs-quiz")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """MkDocs Quiz CLI - Tools for managing quizzes and translations.

    Run without arguments to interactively select and run a quiz.
    """
    # If no subcommand provided, run interactive quiz selection
    if ctx.invoked_subcommand is None:
        from .discovery import interactive_quiz_selection
        from .runner import display_final_results, run_quiz_session

        path = interactive_quiz_selection()
        if path is None:
            # User cancelled or no quizzes found - show help
            click.echo(ctx.get_help())
            sys.exit(0)

        quizzes = _fetch_quizzes_or_exit(path)

        if not quizzes:
            console.print("[yellow]No quizzes found.[/yellow]")
            sys.exit(0)

        try:
            # show_header=False because header was already shown during interactive selection
            correct, total = run_quiz_session(quizzes, quiz_path=path, show_header=False)
            display_final_results(correct, total, quiz_path=path)
        except KeyboardInterrupt:
            console.print("\n")
            sys.exit(0)


@cli.command()
@click.argument("directory", default="docs", type=click.Path(exists=True))
@click.option(
    "-n",
    "--dry-run",
    is_flag=True,
    help="Show what would be changed without modifying files.",
)
def migrate(directory: str, dry_run: bool) -> None:
    """Migrate quiz blocks from old syntax to new markdown-style syntax.

    Converts old question:/answer:/content: syntax to the new cleaner
    markdown checkbox syntax (- [x] / - [ ]).
    """
    dir_path = Path(directory)

    if not dir_path.is_dir():
        console.print(f"[red]Error: '{directory}' is not a directory[/red]")
        sys.exit(1)

    console.print("[bold]MkDocs Quiz Syntax Migration[/bold]")
    console.print(f"Searching for quiz blocks in: {dir_path}")
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No files will be modified[/yellow]")
    console.print()

    # Find all markdown files
    md_files = list(dir_path.rglob("*.md"))

    if not md_files:
        console.print("No markdown files found")
        sys.exit(0)

    total_files_modified = 0
    total_quizzes = 0

    for file_path in md_files:
        quiz_count, modified = migrate_file(file_path, dry_run=dry_run)

        if modified:
            total_files_modified += 1
            total_quizzes += quiz_count
            quiz_text = "quiz" if quiz_count == 1 else "quizzes"
            if dry_run:
                console.print(
                    f"  Would convert {quiz_count} {quiz_text} in: "
                    f"{file_path.relative_to(dir_path)}"
                )
            else:
                console.print(
                    f"  Converted {quiz_count} {quiz_text} in: {file_path.relative_to(dir_path)}"
                )

    console.print()
    if total_files_modified == 0:
        console.print("No quiz blocks found to migrate")
    else:
        console.print("[green]Migration complete![/green]")
        action = "would be" if dry_run else "were"
        console.print(f"  Files {action} modified: {total_files_modified}")
        console.print(f"  Quizzes {action} converted: {total_quizzes}")

        if dry_run:
            console.print()
            console.print("Run without --dry-run to apply changes")


@cli.command()
@click.option(
    "-c",
    "--clear",
    is_flag=True,
    help="Clear all quiz history.",
)
@click.option(
    "--json",
    "output_format",
    flag_value="json",
    help="Output history as JSON.",
)
@click.option(
    "--yaml",
    "output_format",
    flag_value="yaml",
    help="Output history as YAML.",
)
def history(clear: bool, output_format: str | None) -> None:
    """Show quiz results history.

    Displays a table of previously completed quizzes with their scores and dates.
    """
    import json

    import yaml  # type: ignore[import-untyped]
    from rich.table import Table

    from .history import QuizResult, get_history_file, load_history

    if clear:
        history_file = get_history_file()
        if history_file.exists():
            history_file.unlink()
            console.print("[green]Quiz history cleared.[/green]")
        else:
            console.print("[yellow]No history to clear.[/yellow]")
        return

    quiz_history = load_history()

    if not quiz_history:
        if output_format:
            # Output empty data structure for machine-readable formats
            click.echo("[]")
        else:
            console.print("[yellow]No quiz history found.[/yellow]")
            console.print("[dim]Run some quizzes first![/dim]")
        return

    # Flatten all results into a list of (path, result) tuples
    all_results: list[tuple[str, QuizResult]] = []
    for quiz_path, results in quiz_history.items():
        for result in results:
            all_results.append((quiz_path, result))

    # Sort by timestamp (most recent first)
    sorted_results = sorted(
        all_results,
        key=lambda r: r[1].timestamp,
        reverse=True,
    )

    # Handle machine-readable output formats
    if output_format:
        data = [
            {
                "quiz_path": path,
                "correct": r.correct,
                "total": r.total,
                "percentage": r.percentage,
                "timestamp": r.timestamp,
            }
            for path, r in sorted_results
        ]
        if output_format == "json":
            click.echo(json.dumps(data, indent=2))
        elif output_format == "yaml":
            click.echo(yaml.dump(data, default_flow_style=False))
        return

    # Create table
    table = Table(
        title="Quiz History",
        caption="[dim link=https://ewels.github.io/mkdocs-quiz/]https://ewels.github.io/mkdocs-quiz/[/dim link]",
    )
    table.add_column("Quiz", style="cyan", no_wrap=False)
    table.add_column("Date", style="dim")
    table.add_column("Score", justify="right")

    for quiz_path, result in sorted_results:
        # Format the date nicely
        dt = result.datetime
        date_str = dt.strftime("%Y-%m-%d %H:%M")

        # Shorten path relative to cwd or home directory
        display_path = shorten_path(quiz_path)

        score_style = get_score_color(result.percentage)

        table.add_row(
            display_path,
            date_str,
            f"[{score_style}]{result.correct}/{result.total}[/{score_style}]",
        )

    console.print()
    console.print(table)
    console.print()


# Export command group
@cli.group()
def export() -> None:
    """Export quizzes to various formats."""
    pass


@export.command("qti")
@click.argument("path", default="docs", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    help="Output ZIP file path (default: quizzes.zip).",
)
@click.option(
    "-q",
    "--qti-version",
    default="1.2",
    type=click.Choice(["1.2", "2.1"]),
    help="QTI version to export (default: 1.2 for widest compatibility).",
)
@click.option(
    "-t",
    "--title",
    help="Title for the quiz package.",
)
@click.option(
    "--no-recursive",
    is_flag=True,
    help="Don't search directories recursively.",
)
def export_qti(
    path: str,
    output: str | None,
    qti_version: str,
    title: str | None,
    no_recursive: bool,
) -> None:
    """Export quizzes to QTI format for LMS import (Canvas, Blackboard, Moodle)."""
    from .qti import (
        QTIExporter,
        QTIVersion,
        extract_quizzes_from_directory,
        extract_quizzes_from_file,
    )
    from .qti.models import QuizCollection

    # Validate and parse QTI version
    try:
        qti_ver = QTIVersion.from_string(qti_version)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)

    # Convert path to Path object
    source_path = Path(path)

    console.print(f"[bold]MkDocs Quiz QTI Export (version {qti_ver})[/bold]")
    console.print(f"Source: {source_path}")
    console.print()

    # Extract quizzes
    if source_path.is_file():
        if source_path.suffix.lower() != ".md":
            console.print(f"[red]Error: File must be a markdown file (.md): {source_path}[/red]")
            sys.exit(1)

        quizzes = extract_quizzes_from_file(source_path)
        collection = QuizCollection(
            title=title or source_path.stem,
            quizzes=quizzes,
            description=f"Exported from {source_path.name}",
        )
    else:
        collection = extract_quizzes_from_directory(
            source_path,
            recursive=not no_recursive,
        )
        if title:
            collection.title = title

    # Check if we found any quizzes
    if not collection.quizzes:
        console.print("No quizzes found in the specified path")
        sys.exit(0)

    # Validate quizzes
    errors = collection.validate()
    if errors:
        console.print("[yellow]Warning: Some quizzes have validation errors:[/yellow]")
        for quiz_id, quiz_errors in errors.items():
            for error in quiz_errors:
                console.print(f"  - {quiz_id}: {error}")
        console.print()

    # Determine output path
    if output is None:
        output = "quizzes.zip"
    output_path = Path(output)

    # Ensure .zip extension
    if output_path.suffix.lower() != ".zip":
        output_path = output_path.with_suffix(".zip")

    # Export
    console.print(f"Found {collection.total_questions} quiz question(s):")
    console.print(f"  - Single choice: {collection.single_choice_count}")
    console.print(f"  - Multiple choice: {collection.multiple_choice_count}")
    console.print()

    exporter = QTIExporter.create(collection, qti_ver)
    result_path = exporter.export_to_zip(output_path)

    console.print(f"[green]Exported to: {result_path}[/green]")
    console.print()
    console.print("Import this ZIP file into your LMS (Canvas, Blackboard, Moodle, etc.)")


# Translations command group
@cli.group()
def translations() -> None:
    """Manage translation files."""
    pass


@translations.command("init")
@click.argument("language")
@click.option("-o", "--output", help="Output file path (default: {language}.po).")
def init_translation(language: str, output: str | None) -> None:
    """Initialize a new translation file from the template."""
    # Don't create en translation files - English is the fallback
    if language.lower() == "en":
        console.print("[red]Error: 'en' translation file is not needed[/red]")
        console.print("English strings in the source code are used as the fallback.")
        console.print("No translation file is required for English.")
        sys.exit(1)

    # Get path to built-in template
    module_dir = Path(__file__).parent
    template_path = module_dir / "locales" / "mkdocs_quiz.pot"

    # Determine output path
    if output is None:
        output = f"{language}.po"
    output_path = Path(output)

    # Check if file already exists
    if output_path.exists():
        console.print(f"[red]Error: File {output_path} already exists.[/red]")
        sys.exit(1)

    # Load template
    pot = polib.pofile(str(template_path))

    # Update metadata
    pot.metadata = {
        "Project-Id-Version": "mkdocs-quiz",
        "Report-Msgid-Bugs-To": "https://github.com/ewels/mkdocs-quiz/issues",
        "Language": language,
        "MIME-Version": "1.0",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
    }

    # Save as new .po file
    pot.save(str(output_path))

    console.print(f"[green]Created {output_path}[/green]")
    console.print("Edit the file to add translations, then configure in mkdocs.yml")


def _get_translator_info() -> str | None:
    """Get translator info from git config.

    Returns:
        Translator name and email in format "Name <email@example.com>", or None if not available.
    """
    import subprocess

    try:
        # Get git user name and email
        name = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        ).stdout.strip()

        email = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        ).stdout.strip()

        if name and email:
            return f"{name} <{email}>"
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None


def _extract_python_strings(py_file: Path, catalog: Any) -> int:
    """Extract translatable strings from Python files.

    Looks for t.get() patterns in Python code (not docstrings/comments).

    Args:
        py_file: Path to Python file.
        catalog: Babel catalog to add strings to.

    Returns:
        Number of strings extracted.
    """
    content = py_file.read_text(encoding="utf-8")

    # Remove triple-quoted docstrings to avoid extracting example code
    content_no_docstrings = re.sub(r'""".*?"""', "", content, flags=re.DOTALL)
    content_no_docstrings = re.sub(r"'''.*?'''", "", content_no_docstrings, flags=re.DOTALL)
    # Remove line comments
    content_no_docstrings = re.sub(r"#.*?$", "", content_no_docstrings, flags=re.MULTILINE)

    # Pattern to match t.get() - must be t.get() specifically
    pattern = r't\.get\(\s*(["\'])((?:[^\1\\]|\\.)*?)\1'

    count = 0
    search_start = 0

    for match in re.finditer(pattern, content_no_docstrings):
        match_text = match.group(0)
        # Find in original content starting from last found position
        pos = content.find(match_text, search_start)
        if pos == -1:
            continue  # Was in a docstring/comment

        # Calculate line number from start of file
        line_number = content[:pos].count("\n") + 1
        search_start = pos + len(match_text)

        # Extract and unescape the string content
        string_content = match.group(2)
        string_content = string_content.replace(r"\"", '"').replace(r"\'", "'").replace(r"\\", "\\")

        relative_path = py_file.relative_to(Path(__file__).parent)
        catalog.add(string_content, locations=[(str(relative_path), line_number)])
        count += 1

    return count


def _extract_js_strings(js_file: Path, catalog: Any) -> int:
    """Extract translatable strings from JavaScript files.

    Looks for t() patterns in JavaScript code (not comments).

    Args:
        js_file: Path to JavaScript file.
        catalog: Babel catalog to add strings to.

    Returns:
        Number of strings extracted.
    """
    content = js_file.read_text(encoding="utf-8")

    # Remove comments
    content_no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content_no_comments = re.sub(r"//.*?$", "", content_no_comments, flags=re.MULTILINE)

    # Pattern to match t("...") or t('...')
    pattern = r'(?<![a-zA-Z_])t\((["\'])(?:(?=(\\?))\2.)*?\1\)'

    count = 0
    search_start = 0

    for match in re.finditer(pattern, content_no_comments):
        matched_text = match.group(0)
        pos = content.find(matched_text, search_start)
        if pos == -1:
            continue

        line_number = content[:pos].count("\n") + 1
        search_start = pos + len(matched_text)

        # Extract string content (quote char is after 't(')
        quote_char = matched_text[2]
        string_match = re.search(
            rf"{quote_char}((?:[^{quote_char}\\]|\\.)*){quote_char}", matched_text
        )
        if string_match:
            string_content = string_match.group(1)
            string_content = (
                string_content.replace(r"\"", '"').replace(r"\'", "'").replace(r"\\", "\\")
            )

            relative_path = js_file.relative_to(Path(__file__).parent)
            catalog.add(string_content, locations=[(str(relative_path), line_number)])
            count += 1

    return count


def _extract_html_strings(html_file: Path, catalog: Any) -> int:
    """Extract translatable strings from HTML template files.

    Looks for data-quiz-translate attributes in HTML elements.

    Args:
        html_file: Path to HTML file.
        catalog: Babel catalog to add strings to.

    Returns:
        Number of strings extracted.
    """
    content = html_file.read_text(encoding="utf-8")
    content_no_comments = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

    pattern = r'data-quiz-translate="([^"]+)"'

    count = 0
    search_start = 0

    for match in re.finditer(pattern, content_no_comments):
        match_text = match.group(0)
        pos = content.find(match_text, search_start)
        if pos == -1:
            continue

        line_number = content[:pos].count("\n") + 1
        search_start = pos + len(match_text)

        relative_path = html_file.relative_to(Path(__file__).parent)
        catalog.add(match.group(1), locations=[(str(relative_path), line_number)])
        count += 1

    return count


@translations.command("update")
def update_translations() -> None:
    """Extract strings from source and update all translation files.

    This combines extraction and updating into a single command.
    Uses babel to extract strings from source code and sync all .po files.

    Requires: babel (install with `pip install babel`)
    """
    # Lazy import babel (it's only in dev dependencies)
    try:
        from babel.messages.catalog import Catalog
        from babel.messages.pofile import write_po
    except ImportError:
        console.print("[red]Error: babel is required for updating translations[/red]")
        console.print("Install with: pip install babel")
        sys.exit(1)

    # Get paths
    module_dir = Path(__file__).parent
    locales_dir = module_dir / "locales"
    pot_file = locales_dir / "mkdocs_quiz.pot"

    # Step 1: Extract strings from Python source code
    console.print("Extracting strings from source code...")
    catalog = Catalog(project="mkdocs-quiz", version=__version__)

    # Extract from Python files using custom pattern
    py_files = list(module_dir.rglob("*.py"))
    count = 0
    for py_file in py_files:
        count += _extract_python_strings(py_file, catalog)

    console.print(f"[green]Extracted {count} strings from Python files[/green]")

    # Step 2: Extract strings from JavaScript files
    js_count = 0
    js_files = list(module_dir.glob("js/**/*.js"))
    if js_files:
        console.print("Extracting strings from JavaScript files...")
        for js_file in js_files:
            js_count += _extract_js_strings(js_file, catalog)
        console.print(f"[green]Extracted {js_count} strings from JavaScript files[/green]")

    # Step 3: Extract strings from HTML template files
    html_count = 0
    html_files = list(module_dir.glob("overrides/**/*.html"))
    if html_files:
        console.print("Extracting strings from HTML template files...")
        for html_file in html_files:
            html_count += _extract_html_strings(html_file, catalog)
        console.print(f"[green]Extracted {html_count} strings from HTML template files[/green]")

    total_count = count + js_count + html_count

    # Update catalog metadata
    now = datetime.now(timezone.utc)
    catalog.revision_date = now
    catalog.msgid_bugs_address = "Phil Ewels <phil.ewels@seqera.io>"
    catalog.last_translator = "Phil Ewels <phil.ewels@seqera.io>"

    # Write catalog to .pot file
    with open(pot_file, "wb") as f:
        write_po(f, catalog, width=120)

    # Remove Language-Team from .pot file using polib
    pot = polib.pofile(str(pot_file))
    if "Language-Team" in pot.metadata:
        del pot.metadata["Language-Team"]
    pot.save(str(pot_file))

    console.print(f"[green]Total: {total_count} strings extracted to template[/green]")

    # Step 4: Update all .po files
    po_files = list(locales_dir.glob("*.po"))
    console.print(f"Updating {len(po_files)} translation file(s)...")
    for po_file in po_files:
        # Use polib directly instead of babel for updating
        po = polib.pofile(str(po_file))

        # Merge new strings from catalog
        for entry in catalog:
            if entry.id:
                existing = po.find(str(entry.id))
                if not existing:
                    po.append(
                        polib.POEntry(msgid=str(entry.id), msgstr="", occurrences=entry.locations)
                    )

        # Update revision date
        now = datetime.now(timezone.utc)
        po.metadata["PO-Revision-Date"] = now.strftime("%Y-%m-%d %H:%M%z")

        # Update Last-Translator from git config if available
        translator = _get_translator_info()
        if translator:
            po.metadata["Last-Translator"] = translator

        # Remove Language-Team placeholder (not needed for most projects)
        if "Language-Team" in po.metadata:
            del po.metadata["Language-Team"]

        po.save(str(po_file))

    console.print(f"[green]Updated {len(po_files)} file(s)[/green]")
    console.print("Translate new strings and run 'mkdocs-quiz translations check' to verify")


@translations.command("check")
def check_translations() -> None:
    """Check translation completeness and validity."""
    module_dir = Path(__file__).parent
    locales_dir = module_dir / "locales"
    pot_file = locales_dir / "mkdocs_quiz.pot"

    # Load template to get expected strings
    pot = polib.pofile(str(pot_file))
    expected_strings = {entry.msgid for entry in pot if entry.msgid}

    # Find all .po files (excluding en if it exists)
    po_files = [f for f in locales_dir.glob("*.po") if f.stem.lower() != "en"]

    console.print("[bold]Checking translation files...[/bold]\n")

    all_valid = True
    for po_file in po_files:
        po = polib.pofile(str(po_file))
        language = po_file.stem

        # Get strings present in .po file (non-obsolete)
        po_strings = {entry.msgid for entry in po if entry.msgid and not entry.obsolete}

        # Find missing strings (in template but not in .po)
        missing_strings = expected_strings - po_strings

        # Standard polib checks
        total = len(po)
        translated = len(po.translated_entries())
        untranslated = len(po.untranslated_entries())
        fuzzy = len(po.fuzzy_entries())
        obsolete = len(po.obsolete_entries())

        percentage = (translated / total * 100) if total > 0 else 0

        console.print(f"[bold]Language: {language}[/bold]")
        console.print(f"  File: {po_file.name}")
        console.print(f"  Total strings: {total}")
        console.print(f"  Translated: {translated} ({percentage:.1f}%)")
        console.print(f"  Untranslated: {untranslated}")
        console.print(f"  Fuzzy: {fuzzy}")
        console.print(f"  Obsolete: {obsolete}")

        if missing_strings:
            console.print(f"  Missing: {len(missing_strings)} (not in .po file)")
            all_valid = False

        if untranslated > 0 or fuzzy > 0 or obsolete > 0 or missing_strings:
            all_valid = False
            if missing_strings:
                console.print("  Status: [yellow]Missing strings from source code[/yellow]")
                console.print("  Fix: Run 'mkdocs-quiz translations update' to sync")
            elif obsolete > 0:
                console.print(
                    "  Status: [yellow]Has obsolete entries (orphaned translation keys)[/yellow]"
                )
                console.print("  Fix: Remove obsolete entries marked with #~ prefix")
            else:
                console.print("  Status: [yellow]Incomplete[/yellow]")
        else:
            console.print("  Status: [green]Complete[/green]")

        console.print()

    if not all_valid:
        console.print("[red]Some translation files are incomplete or have errors[/red]")
        sys.exit(1)
    else:
        console.print("[green]All translation files are complete![/green]")


@cli.command()
@click.argument("path", required=False, default=None)
@click.option(
    "-s",
    "--shuffle",
    is_flag=True,
    help="Shuffle the order of questions.",
)
@click.option(
    "-a",
    "--shuffle-answers",
    is_flag=True,
    help="Shuffle the order of answers within each question.",
)
def run(path: str | None, shuffle: bool, shuffle_answers: bool) -> None:
    """Run quizzes interactively in the terminal.

    PATH can be a local markdown file, a directory containing markdown files,
    or a URL to a page built with mkdocs-quiz (with embed_source enabled).

    If no PATH is provided and you're in a git repository, an interactive
    file picker will be shown to select a quiz file.

    Examples:

        mkdocs-quiz run

        mkdocs-quiz run docs/quiz.md

        mkdocs-quiz run docs/

        mkdocs-quiz run https://example.com/docs/quiz/
    """
    from .discovery import interactive_quiz_selection
    from .runner import display_final_results, run_quiz_session

    # If no path provided, try interactive selection
    used_interactive_selection = False
    if path is None:
        path = interactive_quiz_selection()
        if path is None:
            # User cancelled or no quizzes found - show help
            ctx = click.get_current_context(silent=True)
            if ctx:
                click.echo(ctx.get_help())
            sys.exit(0)
        used_interactive_selection = True

    quizzes = _fetch_quizzes_or_exit(path)

    if not quizzes:
        console.print("[yellow]No quizzes found.[/yellow]")
        sys.exit(0)

    try:
        correct, total = run_quiz_session(
            quizzes,
            shuffle_questions=shuffle,
            shuffle_answers=shuffle_answers,
            quiz_path=path,
            show_header=not used_interactive_selection,
        )

        # Display final results
        display_final_results(correct, total, quiz_path=path)

    except KeyboardInterrupt:
        console.print("\n")
        sys.exit(0)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
