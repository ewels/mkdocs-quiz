"""Command-line interface for mkdocs-quiz."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import polib


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
        print(f"  Error reading {file_path}: {e}")
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


def migrate(directory: str, dry_run: bool = False) -> None:
    """Migrate quiz blocks from old syntax to new markdown-style syntax.

    Converts old question:/answer:/content: syntax to the new cleaner
    markdown checkbox syntax (- [x] / - [ ]).

    Args:
        directory: Directory to search for markdown files.
        dry_run: Show what would be changed without modifying files.
    """
    # Convert string to Path and validate
    dir_path = Path(directory)

    if not dir_path.exists():
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)

    if not dir_path.is_dir():
        print(f"Error: '{directory}' is not a directory")
        sys.exit(1)

    print("MkDocs Quiz Syntax Migration")
    print(f"Searching for quiz blocks in: {dir_path}")
    if dry_run:
        print("DRY RUN MODE - No files will be modified")
    print()

    # Find all markdown files
    md_files = list(dir_path.rglob("*.md"))

    if not md_files:
        print("No markdown files found")
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
                print(
                    f"  Would convert {quiz_count} {quiz_text} in: {file_path.relative_to(dir_path)}"
                )
            else:
                print(f"  Converted {quiz_count} {quiz_text} in: {file_path.relative_to(dir_path)}")

    print()
    if total_files_modified == 0:
        print("No quiz blocks found to migrate")
    else:
        print("Migration complete!")
        action = "would be" if dry_run else "were"
        print(f"  Files {action} modified: {total_files_modified}")
        print(f"  Quizzes {action} converted: {total_quizzes}")

        if dry_run:
            print()
            print("Run without --dry-run to apply changes")


def init_translation(language: str, output: str | None = None) -> None:
    """Initialize a new translation file from the template.

    Args:
        language: Language code (e.g., 'fr_FR', 'es_ES').
        output: Output path (defaults to {language}.po).
    """
    # Get path to built-in template
    module_dir = Path(__file__).parent
    template_path = module_dir / "locales" / "mkdocs_quiz.pot"

    if not template_path.exists():
        print(f"Error: Built-in template not found at {template_path}")
        sys.exit(1)

    # Determine output path
    if output is None:
        output = f"{language}.po"
    output_path = Path(output)

    # Check if file already exists
    if output_path.exists():
        response = input(f"File {output_path} already exists. Overwrite? [y/N]: ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)

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

    print(f"Created {output_path} ({language})")
    print("Edit the file to add translations, then configure in mkdocs.yml")


def extract_strings() -> None:
    """Extract translatable strings from source code to update .pot template.

    Uses babel to extract strings from Python code and update the mkdocs_quiz.pot
    template file with all translatable strings.

    Requires: babel (install with `pip install babel`)
    """
    # Lazy import babel (it's only in dev dependencies)
    try:
        from babel.messages.catalog import Catalog
        from babel.messages.extract import extract_from_dir
        from babel.messages.pofile import write_po
    except ImportError:
        print("Error: babel is required for the extract-strings command")
        print("Install with: pip install babel")
        sys.exit(1)

    # Get paths
    module_dir = Path(__file__).parent
    locales_dir = module_dir / "locales"
    pot_file = locales_dir / "mkdocs_quiz.pot"

    # Ensure locales directory exists
    locales_dir.mkdir(exist_ok=True)

    print("Extracting translatable strings from source code...")

    # Create a new catalog
    catalog = Catalog(project="mkdocs-quiz", version="1.1.0")

    # Extract strings from Python files
    method_map = [("**.py", "python")]
    extracted = extract_from_dir(
        str(module_dir),
        method_map=method_map,
        keywords={"get": None},  # Look for t.get() calls
    )

    # Add extracted messages to catalog
    count = 0
    for filename, lineno, message, _comments, _context in extracted:
        if message:
            catalog.add(message, locations=[(filename, lineno)])
            count += 1

    # Write catalog to .pot file
    with open(pot_file, "wb") as f:
        write_po(f, catalog, width=100)

    print(f"✓ Extracted {count} strings to {pot_file.name}")
    print("Run 'mkdocs-quiz update-translations' to sync .po files")


def update_translations() -> None:
    """Update all .po translation files from the .pot template.

    Uses babel to sync all .po files with the latest .pot template,
    adding new strings and marking obsolete ones.

    Requires: babel (install with `pip install babel`)
    """
    # Lazy import babel (it's only in dev dependencies)
    try:
        from babel.messages.pofile import read_po, write_po
    except ImportError:
        print("Error: babel is required for the update-translations command")
        print("Install with: pip install babel")
        sys.exit(1)

    # Get paths
    module_dir = Path(__file__).parent
    locales_dir = module_dir / "locales"
    pot_file = locales_dir / "mkdocs_quiz.pot"

    if not pot_file.exists():
        print(f"Error: Template file not found: {pot_file}")
        print("Run 'mkdocs-quiz extract-strings' first")
        sys.exit(1)

    # Find all .po files
    po_files = list(locales_dir.glob("*.po"))

    if not po_files:
        print("No translation files found")
        print("Use 'mkdocs-quiz init-translation <language>' first")
        sys.exit(0)

    print(f"Updating {len(po_files)} translation file(s)...")

    # Load template catalog
    with open(pot_file, "rb") as f:
        template = read_po(f)

    # Update each .po file
    for po_file in po_files:
        with open(po_file, "rb") as f:
            catalog = read_po(f)
        catalog.update(template)
        with open(po_file, "wb") as f:
            write_po(f, catalog, width=100)

    print(f"✓ Updated {len(po_files)} file(s). Translate new strings and run check-translations.")


def check_translations() -> None:
    """Check translation completeness and validity."""
    # Get path to locales directory
    module_dir = Path(__file__).parent
    locales_dir = module_dir / "locales"

    if not locales_dir.exists():
        print(f"Error: Locales directory not found at {locales_dir}")
        sys.exit(1)

    # Find all .po files
    po_files = list(locales_dir.glob("*.po"))

    if not po_files:
        print("No translation files found")
        sys.exit(0)

    print("Checking translation files...\n")

    all_valid = True
    for po_file in po_files:
        po = polib.pofile(str(po_file))
        language = po_file.stem

        total = len(po)
        translated = len(po.translated_entries())
        untranslated = len(po.untranslated_entries())
        fuzzy = len(po.fuzzy_entries())
        obsolete = len(po.obsolete_entries())

        percentage = (translated / total * 100) if total > 0 else 0

        print(f"Language: {language}")
        print(f"  File: {po_file.name}")
        print(f"  Total strings: {total}")
        print(f"  Translated: {translated} ({percentage:.1f}%)")
        print(f"  Untranslated: {untranslated}")
        print(f"  Fuzzy: {fuzzy}")
        print(f"  Obsolete: {obsolete}")

        if untranslated > 0 or fuzzy > 0 or obsolete > 0:
            all_valid = False
            if obsolete > 0:
                print("  Status: ⚠️  Has obsolete entries (orphaned translation keys)")
                print("  Fix: Remove obsolete entries marked with #~ prefix")
            else:
                print("  Status: ⚠️  Incomplete")
        else:
            print("  Status: ✓ Complete")

        print()

    if not all_valid:
        print("Some translation files are incomplete or have errors")
        sys.exit(1)
    else:
        print("All translation files are complete!")


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="mkdocs-quiz",
        description="MkDocs Quiz CLI - Tools for managing quizzes and translations",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Migrate subcommand
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate quiz blocks from old syntax to new markdown-style syntax",
    )
    migrate_parser.add_argument(
        "directory",
        nargs="?",
        default="docs",
        help="Directory to search for markdown files (default: docs)",
    )
    migrate_parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )

    # Initialize translation subcommand
    init_parser = subparsers.add_parser(
        "init-translation", help="Initialize a new translation file"
    )
    init_parser.add_argument("language", help="Language code (e.g., fr_FR, es_ES)")
    init_parser.add_argument("-o", "--output", help="Output file path (default: {language}.po)")

    # Extract strings subcommand
    subparsers.add_parser(
        "extract-strings", help="Extract translatable strings to update .pot template"
    )

    # Update translations subcommand
    subparsers.add_parser("update-translations", help="Update all .po files from .pot template")

    # Check translations subcommand
    subparsers.add_parser("check-translations", help="Check translation completeness")

    args = parser.parse_args()

    if args.command == "migrate":
        migrate(args.directory, dry_run=args.dry_run)
    elif args.command == "init-translation":
        init_translation(language=args.language, output=args.output)
    elif args.command == "extract-strings":
        extract_strings()
    elif args.command == "update-translations":
        update_translations()
    elif args.command == "check-translations":
        check_translations()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
