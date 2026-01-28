# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MkDocs Quiz is a plugin for MkDocs that creates interactive quizzes directly in markdown documentation. It processes custom `<quiz>` tags in markdown files and converts them to interactive HTML/JS quiz elements. Supports both multiple-choice and fill-in-the-blank question types.

## Architecture

### Plugin System Integration

This is a MkDocs plugin that hooks into the MkDocs build pipeline:

- **Entry point**: `mkdocs_quiz.plugin:MkDocsQuizPlugin` (registered in `pyproject.toml`)
- **Plugin class**: Extends `mkdocs.plugins.BasePlugin`
- **Hook lifecycle**:
  1. `on_env()` - Adds template overrides for Material theme's TOC sidebar integration
  2. `on_page_markdown()` - Processes markdown to convert quiz tags to placeholders and stores quiz HTML
  3. `on_page_content()` - Replaces placeholders with actual quiz HTML and injects CSS/JS assets

### Quiz Types

The plugin supports two types of quizzes:

1. **Multiple-choice quizzes**: Use checkbox syntax (`- [x]` for correct, `- [ ]` for incorrect)
   - Single correct answer → radio buttons
   - Multiple correct answers → checkboxes
   - Auto-submit option for single-choice (default: enabled)

2. **Fill-in-the-blank quizzes**: Use double square brackets (`[[answer]]`) to mark blanks
   - Supports single or multiple blanks in one question
   - Case-insensitive validation (trimmed whitespace)
   - Markdown formatting works around blanks
   - Always requires explicit submit button

The plugin automatically detects which type based on the content:

- If `[[...]]` patterns are found → fill-in-the-blank
- Otherwise → multiple-choice (requires checkbox items)

### Quiz Processing Flow

1. **Code block masking** (`_mask_code_blocks`):
   - Temporarily masks fenced code blocks (``` or ~~~) outside of quiz tags to prevent processing quiz syntax shown as examples
   - Quiz ranges are identified first, then only code blocks outside quizzes are masked

2. **Markdown parsing** (`on_page_markdown`):
   - Regex pattern `<quiz>(.*?)</quiz>` finds quiz blocks
   - Each quiz is passed to `_process_quiz()` method
   - `_process_quiz()` detects quiz type using `_is_fill_in_blank_quiz()`
   - **Multiple-choice**: Uses checkbox lists (`- [x]` correct, `- [ ]` incorrect)
     - Question is everything before the first checkbox answer
     - Content section (optional) is everything after the last answer
     - Single correct answer = radio buttons; multiple correct = checkboxes
   - **Fill-in-the-blank**: Uses `[[answer]]` patterns
     - Question text with blanks replaced by text inputs
     - Correct answers stored in `data-answer` attributes (HTML-escaped)
     - Content section separated by horizontal rule (`---`)
   - Quizzes replaced with placeholders (`<!-- MKDOCS_QUIZ_PLACEHOLDER_N -->`) in markdown

3. **HTML generation** (`_process_quiz` and `_process_fill_in_blank_quiz`):
   - **Multiple-choice**: Parses quiz lines to extract question, answers, and content
     - Converts question and answers from markdown to HTML using `markdown_converter`
     - Uses the same `markdown_extensions` configured in `mkdocs.yml` for conversion
     - This enables features like `pymdownx.superfences`, `pymdownx.highlight`, admonitions, etc.
     - Generates form HTML with proper input types (radio/checkbox)
     - Adds `correct` attribute to correct answers (used by JS)
   - **Fill-in-the-blank**: Replaces `[[answer]]` with text inputs
     - Uses HTML comment placeholders (`<!--BLANK_PLACEHOLDER_N-->`) during markdown conversion
     - Replaces placeholders with `<input type="text" class="quiz-blank-input">`
     - Stores correct answers in `data-answer` attributes (HTML-escaped)
     - Adds `autocomplete="off"` to prevent browser autofill
   - Content section is hidden until quiz is answered (both types)
   - Each quiz gets unique ID for deep linking (`id="quiz-N"`)
   - Quiz HTML is stored in `_quiz_storage` dict keyed by page path

4. **Asset injection** (`on_page_content`):
   - Replaces placeholders with stored quiz HTML
   - CSS and JS loaded at module level from `mkdocs_quiz/css/` and `mkdocs_quiz/js/`
   - Injected as inline `<style>` and `<script>` tags (not external files)
   - Translations passed to JavaScript as JSON via `window.mkdocsQuizTranslations`
   - If `auto_number` is enabled, adds additional script to inject numbering class
   - JS handles form submission, answer validation, visual feedback, and localStorage persistence

### JavaScript Behavior

The [quiz.js](mkdocs_quiz/js/quiz.js) file:

- **Quiz tracking**: `quizTracker` object manages progress across all quizzes on a page
  - Tracks answered/correct counts and stores state in localStorage (per-page)
  - Provides progress display and sidebar integration for Material theme
  - Creates progress sidebar automatically when multiple quizzes exist
  - Dispatches `quizProgressUpdate` custom events for integration
- **Form handling**: Attaches submit handlers to all `.quiz` forms on page load
- **Validation**:
  - **Multiple-choice**: Validates selected answers against `[correct]` attribute
  - **Fill-in-the-blank**: Compares input values with `data-answer` attributes
    - Case-insensitive comparison using `normalizeAnswer()` (trim + lowercase)
    - All blanks must be correct for quiz to pass
- **Visual feedback**: Shows/hides content section, adds `.correct` and `.wrong` classes
  - **Fill-in-the-blank**: Wrong answers show correct answer as placeholder if `show_correct` enabled
- **Auto-submit**: If enabled and single-choice (radio), submits on selection change (multiple-choice only)
- **Persistence**: Restores quiz state from localStorage on page load
  - **Fill-in-the-blank**: Saves user input values in `selectedValues` array
- **Reset functionality**: "Try Again" button to reset individual quizzes (if not disabled after submit)
  - **Fill-in-the-blank**: Clears input values and removes styling
- **Helper**: `resetFieldset()` clears previous styling before re-validation

### Configuration Options

**Plugin-level** (in `mkdocs.yml`):

```yaml
plugins:
  - mkdocs_quiz:
      enabled_by_default: true # Process quizzes by default (default: true)
      auto_number: false # Auto-number questions (default: false)
      show_correct: true # Show correct answers when wrong (default: true)
      auto_submit: true # Auto-submit single-choice quizzes (default: true)
      disable_after_submit: true # Disable quiz after submission (default: true)
      shuffle_answers: false # Randomize answer order (default: false)
      progress_sidebar_position: top # Position of progress tracker: "top" or "bottom" (default: "top")
```

**Page-level** (frontmatter overrides plugin config):

```yaml
---
quiz:
  enabled: false # Disable quiz processing on this page
  show_correct: false # Don't show correct answers
  auto_submit: false # Require explicit submit button
  disable_after_submit: false # Allow retries after submission
  auto_number: true # Number questions on this page
  shuffle_answers: true # Randomize answer order on this page
---
```

The plugin checks `_should_process_page()` to respect `enabled_by_default` and per-page `enabled` settings.

### Translation System

MkDocs Quiz supports internationalization through `.po` translation files. All user-facing text (buttons, messages, progress tracking) can be translated.

**Architecture:**

1. **Single Source of Truth**:
   - English strings are written directly in Python/JavaScript code where they're used
   - Translation keys ARE the English strings (standard gettext pattern)

2. **Translation Manager** ([mkdocs_quiz/translations.py](mkdocs_quiz/translations.py)):
   - `TranslationManager` class handles loading and resolving translations
   - Loading order: Built-in `.po` → Custom `.po` → Falls back to English key
   - Uses `polib` library to parse `.po` files (standard gettext format)
   - `polib` is a required dependency

3. **Translation Files** ([mkdocs_quiz/locales/](mkdocs_quiz/locales/)):
   - Language codes follow [MkDocs Material conventions](https://squidfunk.github.io/mkdocs-material/setup/changing-the-language/): 2-letter ISO 639-1 codes (e.g., `fr`, `de`) with hyphens for regional variants (e.g., `pt-BR`, `zh-TW`)
   - `mkdocs_quiz.pot` - Template extracted from source code
   - `fr.po`, `pt-BR.po`, etc. - Language translations
   - No `en.po` file needed - English keys in source code are the fallback
   - Standard gettext format, compatible with Poedit, Weblate, Crowdin
   - Files contain `msgid` (English source) and `msgstr` (translation)

4. **Integration Flow**:
   - `_get_translation_manager()` determines language for each page (later overrides earlier):
     - Default: `en`
     - `theme.language` from MkDocs config
     - `extra.alternate` - Active language from Material's language selector (auto-detected from page URL)
     - `language` config
     - `language_patterns` config
     - Page frontmatter (`quiz.language`) - highest priority
   - Python generates HTML with translated strings using `t.get("English text")`
   - Translations passed to JavaScript via `window.mkdocsQuizTranslations`
   - JavaScript uses `t("English text", params)` helper for dynamic text

5. **Configuration Options**:

   ```yaml
   # Automatically uses theme language if set
   theme:
     name: material
     language: fr

   # Automatically uses alternate i8n from mkdocs
   extra:
      alternate:
         - name: English
            link: /en/
            lang: en
         - name: Français
            link: /fr/
            lang: fr

   plugins:
     - mkdocs_quiz:
         language: fr # Global default (optional if theme.language is set)
         language_patterns:
           - pattern: "fr/**/*"
             language: fr
           - pattern: "pt/**/*"
             language: pt-BR
         custom_translations:
           fr: translations/fr_custom.po # Override built-in French
           ja: translations/ja.po # Add new language
   ```

6. **CLI Tools**:
   - `mkdocs-quiz translations init <language>` - Initialize new language
   - `mkdocs-quiz translations update` - Extract strings from source and update all .po files
   - `mkdocs-quiz translations check` - Validate completeness and detect orphaned keys
   - Pre-commit hook validates translations automatically

**Adding New Translatable Strings:**

When adding new user-facing text:

1. Write English text directly in code: `t.get("New message")`
2. Run `mkdocs-quiz translations update` to extract strings and update all .po files
3. Translate new strings in each `.po` file
4. Run `mkdocs-quiz translations check` to verify

**Note:** The `translations update` command wraps pybabel functionality for convenience. Babel must be installed as a dev dependency.

## Development Commands

### Setup

```bash
pip install -e ".[dev]"
pre-commit install  # Auto-formats and lints on commit
```

### Testing

```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=mkdocs_quiz --cov-report=html

# Single test
pytest tests/test_plugin.py::test_single_choice_quiz

# Test with live docs site (requires mkdocs-material)
pip install -e ".[docs]"
mkdocs serve
```

### Code Quality

Pre-commit hooks run automatically on `git commit`. To run manually:

```bash
# All checks
pre-commit run --all-files

# Individual tools
ruff format mkdocs_quiz tests  # Format Python
ruff check mkdocs_quiz tests   # Lint Python
npx prettier --write "mkdocs_quiz/**/*.{js,css}"  # Format JS/CSS
mypy mkdocs_quiz               # Type check
mkdocs-quiz translations check # Check translation completeness
```

### Translation Management

```bash
# Check translation completeness (runs in pre-commit)
mkdocs-quiz translations check

# Initialize new language
mkdocs-quiz translations init <lang_code> -o mkdocs_quiz/locales/<lang_code>.po
```

### Building

```bash
python -m build  # Creates dist/mkdocs_quiz-*.whl and .tar.gz
```

## Code Style

- **Python**: Ruff (formatter + linter), 100 char line length, Python 3.8+ compatible
- **JavaScript/CSS**: Prettier with 100 char print width
- **Type hints**: Required for all Python function signatures
- **Imports**: `from __future__ import annotations` for forward compatibility

## Testing Considerations

When writing tests:

- Mock pages need proper initialization: `Page(None, file, config)` with valid `File` object
- Page metadata accessed via `page.meta` dictionary
- Quiz processing errors are logged but don't raise exceptions (graceful degradation)
- Test both single-choice (one correct) and multiple-choice (2+ correct) scenarios

## CLI Tool

The plugin includes a CLI tool for various tasks:

```bash
# Migrate quizzes from old question:/answer: syntax to new markdown checkbox syntax
mkdocs-quiz migrate docs/

# Translation management
mkdocs-quiz translations init <lang_code>   # Create new translation file
mkdocs-quiz translations update             # Extract strings & update .po files (maintainers)
mkdocs-quiz translations check              # Validate completeness
```

The CLI tool ([mkdocs_quiz/cli.py](mkdocs_quiz/cli.py)) provides utilities for quiz migration, translation management, and validation.

## Material Theme Integration

When using Material for MkDocs theme:

- The `on_env()` hook adds template overrides from `mkdocs_quiz/overrides/`
- This extends the TOC sidebar to include a quiz progress widget
- Progress sidebar only appears when page has 2+ quizzes
- Shows answered/total count, progress bar, and correct/incorrect statistics
- Includes a "Reset" link to clear all quiz progress on the page
- The `progress_sidebar_position` option controls where the progress tracker appears in the sidebar:
  - `"top"` (default): Appears above the Table of Contents
  - `"bottom"`: Appears below the Table of Contents

## Publishing

PyPI publishing is fully automated via GitHub Actions:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create GitHub release
4. Workflow automatically builds and publishes to PyPI

See [.github/workflows/publish.yml](.github/workflows/publish.yml) for setup instructions (requires PyPI trusted publishing configuration).
