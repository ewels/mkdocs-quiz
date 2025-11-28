"""Command-line interface for mkdocs-quiz."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polib

from mkdocs_quiz import __version__


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
    # Don't create en_US translation files - English is the fallback
    if language.lower() == "en_us":
        print("Error: en_US translation file is not needed")
        print("English strings in the source code are used as the fallback.")
        print("No translation file is required for English.")
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
        print("Error: File {output_path} already exists.")
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

    print(f"Created {output_path}")
    print("Edit the file to add translations, then configure in mkdocs.yml")


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
    # This is a simple regex-based approach
    content_no_docstrings = re.sub(r'""".*?"""', "", content, flags=re.DOTALL)
    content_no_docstrings = re.sub(r"'''.*?'''", "", content_no_docstrings, flags=re.DOTALL)
    # Remove line comments
    content_no_docstrings = re.sub(r"#.*?$", "", content_no_docstrings, flags=re.MULTILINE)

    # Pattern to match t.get()
    # Must be t.get() specifically, not any .get() call
    # Allows whitespace/newlines between t.get( and the string
    pattern = r't\.get\(\s*(["\'])((?:[^\1\\]|\\.)*?)\1'

    count = 0
    line_number = 1
    position = 0

    # Find all matches and their line numbers
    for match in re.finditer(pattern, content_no_docstrings):
        # Count newlines up to this match to get line number
        # We need to use original content for accurate line numbers
        # Find the match in the original content
        match_text = match.group(0)
        start_pos = content.find(match_text, position)
        if start_pos == -1:
            continue  # Skip if not found in original (was in docstring)

        line_number += content[position:start_pos].count("\n")
        position = start_pos

        # Extract the string content (group 2 is the string between quotes)
        string_content = match.group(2)

        # Unescape the string
        string_content = string_content.replace(r"\"", '"').replace(r"\'", "'").replace(r"\\", "\\")

        # Add to catalog
        relative_path = py_file.relative_to(Path(__file__).parent)
        catalog.add(string_content, locations=[(str(relative_path), line_number)])
        count += 1

    return count


def _extract_js_strings(js_file: Path, catalog: Any) -> int:
    """Extract translatable strings from JavaScript files.

    Looks for t() patterns in JavaScript code (not comments/docstrings).

    Args:
        js_file: Path to JavaScript file.
        catalog: Babel catalog to add strings to.

    Returns:
        Number of strings extracted.
    """
    content = js_file.read_text(encoding="utf-8")

    # Remove block comments /* */ and JSDoc comments /** */
    content_no_comments = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    # Remove line comments //
    content_no_comments = re.sub(r"//.*?$", "", content_no_comments, flags=re.MULTILINE)

    # Pattern to match t("...") or t('...')
    # Must be standalone t() function call, not part of another word
    # Handles escaped quotes and multiline strings
    pattern = r'(?<![a-zA-Z_])t\((["\'])(?:(?=(\\?))\2.)*?\1\)'

    count = 0
    line_number = 1
    position = 0

    # Find all matches and their line numbers
    for match in re.finditer(pattern, content_no_comments):
        # Count newlines up to this match to get line number
        # We need to use original content for accurate line numbers
        # Find the match in the original content
        matched_text = match.group(0)
        start_pos = content.find(matched_text, position)
        if start_pos == -1:
            continue  # Skip if not found in original (was in comment)

        line_number += content[position:start_pos].count("\n")
        position = start_pos

        # Extract the string content (without quotes)
        quote_char = matched_text[2]  # Get quote character after 't('

        # Find the string between quotes
        string_match = re.search(
            rf"{quote_char}((?:[^{quote_char}\\]|\\.)*)" + quote_char, matched_text
        )
        if string_match:
            # Unescape the string
            string_content = string_match.group(1)
            string_content = (
                string_content.replace(r"\"", '"').replace(r"\"", "'").replace(r"\\", "\\")
            )

            # Add to catalog
            relative_path = js_file.relative_to(Path(__file__).parent)
            catalog.add(string_content, locations=[(str(relative_path), line_number)])
            count += 1

    return count


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
        print("Error: babel is required for updating translations")
        print("Install with: pip install babel")
        sys.exit(1)

    # Get paths
    module_dir = Path(__file__).parent
    locales_dir = module_dir / "locales"
    pot_file = locales_dir / "mkdocs_quiz.pot"

    # Step 1: Extract strings from Python source code
    print("Extracting strings from source code...")
    catalog = Catalog(project="mkdocs-quiz", version=__version__)

    # Extract from Python files using custom pattern
    py_files = list(module_dir.rglob("*.py"))
    count = 0
    for py_file in py_files:
        count += _extract_python_strings(py_file, catalog)

    print(f"✓ Extracted {count} strings from Python files")

    # Step 2: Extract strings from JavaScript files
    js_count = 0
    js_files = list(module_dir.glob("js/**/*.js"))
    if js_files:
        print("Extracting strings from JavaScript files...")
        for js_file in js_files:
            js_count += _extract_js_strings(js_file, catalog)
        print(f"✓ Extracted {js_count} strings from JavaScript files")

    total_count = count + js_count

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

    print(f"✓ Total: {total_count} strings extracted to template")

    # Step 3: Update all .po files
    po_files = list(locales_dir.glob("*.po"))
    print(f"Updating {len(po_files)} translation file(s)...")
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

    print(f"✓ Updated {len(po_files)} file(s)")
    print("Translate new strings and run 'mkdocs-quiz translations check' to verify")


def check_translations() -> None:
    """Check translation completeness and validity."""
    module_dir = Path(__file__).parent
    locales_dir = module_dir / "locales"
    pot_file = locales_dir / "mkdocs_quiz.pot"

    # Load template to get expected strings
    pot = polib.pofile(str(pot_file))
    expected_strings = {entry.msgid for entry in pot if entry.msgid}

    # Find all .po files (excluding en_US if it exists)
    po_files = [f for f in locales_dir.glob("*.po") if f.stem.lower() != "en_us"]

    print("Checking translation files...\n")

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

        print(f"Language: {language}")
        print(f"  File: {po_file.name}")
        print(f"  Total strings: {total}")
        print(f"  Translated: {translated} ({percentage:.1f}%)")
        print(f"  Untranslated: {untranslated}")
        print(f"  Fuzzy: {fuzzy}")
        print(f"  Obsolete: {obsolete}")

        if missing_strings:
            print(f"  Missing: {len(missing_strings)} (not in .po file)")
            all_valid = False

        if untranslated > 0 or fuzzy > 0 or obsolete > 0 or missing_strings:
            all_valid = False
            if missing_strings:
                print("  Status: ⚠️  Missing strings from source code")
                print("  Fix: Run 'mkdocs-quiz translations update' to sync")
            elif obsolete > 0:
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

    # Translations subcommand group
    translations_parser = subparsers.add_parser(
        "translations",
        help="Manage translation files",
    )
    translations_subparsers = translations_parser.add_subparsers(
        dest="translations_command",
        help="Translation commands",
    )

    # translations init
    init_parser = translations_subparsers.add_parser(
        "init",
        help="Initialize a new translation file",
    )
    init_parser.add_argument("language", help="Language code (e.g., fr_FR, es_ES)")
    init_parser.add_argument("-o", "--output", help="Output file path (default: {language}.po)")

    # translations update
    translations_subparsers.add_parser(
        "update",
        help="Extract strings and update all translation files",
    )

    # translations check
    translations_subparsers.add_parser(
        "check",
        help="Check translation completeness",
    )

    args = parser.parse_args()

    if args.command == "migrate":
        migrate(args.directory, dry_run=args.dry_run)
    elif args.command == "translations":
        if args.translations_command == "init":
            init_translation(language=args.language, output=args.output)
        elif args.translations_command == "update":
            update_translations()
        elif args.translations_command == "check":
            check_translations()
        else:
            translations_parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
