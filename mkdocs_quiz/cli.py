"""Command-line interface for mkdocs-quiz."""

from __future__ import annotations

import re
from pathlib import Path

import typer
from rich.console import Console

console = Console()

app = typer.Typer(rich_markup_mode="rich")


def convert_quiz_block(quiz_content: str) -> str:
    """Convert old quiz syntax to new markdown-style syntax.

    Args:
        quiz_content: The content inside <?quiz?> tags in old format.

    Returns:
        The converted quiz content in new format.
    """
    lines = quiz_content.strip().split("\n")

    question = None
    answers: list[tuple[str, str]] = []  # (type, text)
    content_lines: list[str] = []
    options: list[str] = []
    in_content = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse question
        if line.startswith("question:"):
            question = line.split("question:", 1)[1].strip()
        # Parse options that should be preserved
        elif line.startswith(("show-correct:", "auto-submit:", "disable-after-submit:")):
            options.append(line)
        # Parse content separator
        elif line == "content:":
            in_content = True
        # Parse answers
        elif line.startswith("answer-correct:"):
            answer_text = line.split("answer-correct:", 1)[1].strip()
            answers.append(("correct", answer_text))
        elif line.startswith("answer:"):
            answer_text = line.split("answer:", 1)[1].strip()
            answers.append(("incorrect", answer_text))
        # Content section
        elif in_content:
            content_lines.append(line)

    # Build new quiz format
    result = ["<quiz>"]

    # Add question
    if question:
        result.append(question)

    # Add options
    for opt in options:
        result.append(opt)

    # Add answers in new format
    for answer_type, answer_text in answers:
        if answer_type == "correct":
            result.append(f"- [x] {answer_text}")
        else:
            result.append(f"- [ ] {answer_text}")

    # Add content if present
    if content_lines:
        result.append("")  # Empty line before content
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
    except Exception as e:
        console.print(f"  [red]❌ Error reading {file_path}: {e}[/red]")
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


@app.command()
def migrate(
    directory: str = typer.Argument("docs", help="Directory to search for markdown files"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be changed without modifying files"
    ),
) -> None:
    """Migrate quiz blocks from old syntax to new markdown-style syntax.

    Converts old question:/answer:/content: syntax to the new cleaner
    markdown checkbox syntax (- [x] / - [ ]).

    Example:
        mkdocs-quiz migrate docs/
        mkdocs-quiz migrate docs/ --dry-run
    """
    # Convert string to Path and validate
    dir_path = Path(directory)

    if not dir_path.exists():
        console.print(f"[red]❌ Error: Directory '{directory}' does not exist[/red]")
        raise typer.Exit(1)

    if not dir_path.is_dir():
        console.print(f"[red]❌ Error: '{directory}' is not a directory[/red]")
        raise typer.Exit(1)

    console.print("🔄 MkDocs Quiz Syntax Migration")
    console.print(f"📁 Searching for quiz blocks in: {dir_path}")
    if dry_run:
        console.print("[yellow]🔍 DRY RUN MODE - No files will be modified[/yellow]")
    console.print()

    # Find all markdown files
    md_files = list(dir_path.rglob("*.md"))

    if not md_files:
        console.print("[yellow]⚠️  No markdown files found[/yellow]")
        raise typer.Exit(0)

    total_files_modified = 0
    total_quizzes = 0

    for file_path in md_files:
        quiz_count, modified = migrate_file(file_path, dry_run=dry_run)

        if modified:
            total_files_modified += 1
            total_quizzes += quiz_count
            if dry_run:
                console.print(
                    f"[blue]🔍 Would convert {quiz_count} quiz(es) in: {file_path.relative_to(dir_path)}[/blue]"
                )
            else:
                console.print(
                    f"[green]✅ Converted {quiz_count} quiz(es) in: {file_path.relative_to(dir_path)}[/green]"
                )

    console.print()
    if total_files_modified == 0:
        console.print("[blue]🤷🏻‍♂️ No quiz blocks found to migrate[/blue]")
    else:
        console.print("[green bold]✨ Migration complete![/green bold]")
        action = "would be" if dry_run else "were"
        console.print(f"  📝 Files {action} modified: {total_files_modified}")
        console.print(f"  🎯 Quizzes {action} converted: {total_quizzes}")

        if dry_run:
            console.print()
            console.print("[blue]💡 Run without --dry-run to apply changes[/blue]")


@app.callback()
def callback():
    """Required to keep subcommand even when there's only one for now."""
    pass


if __name__ == "__main__":
    app()
