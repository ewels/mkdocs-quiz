# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MkDocs Quiz is a plugin for MkDocs that creates interactive quizzes directly in markdown documentation. It processes custom `<?quiz?>` tags in markdown files and converts them to interactive HTML/JS quiz elements.

## Architecture

### Plugin System Integration

This is a MkDocs plugin that hooks into the MkDocs build pipeline:

- **Entry point**: `mkdocs_quiz.plugin:MkDocsQuizPlugin` (registered in `pyproject.toml`)
- **Plugin class**: Extends `mkdocs.plugins.BasePlugin`
- **Hook lifecycle**:
  1. `on_env()` - Adds template overrides for Material theme's TOC sidebar integration
  2. `on_page_markdown()` - Processes markdown to convert quiz tags to placeholders and stores quiz HTML
  3. `on_page_content()` - Replaces placeholders with actual quiz HTML and injects CSS/JS assets

### Quiz Processing Flow

1. **Code block masking** (`_mask_code_blocks`):
   - Temporarily masks fenced code blocks (``` or ~~~) outside of quiz tags to prevent processing quiz syntax shown as examples
   - Quiz ranges are identified first, then only code blocks outside quizzes are masked

2. **Markdown parsing** (`on_page_markdown`):
   - Regex pattern `<quiz>(.*?)</quiz>` finds quiz blocks
   - Each quiz is passed to `_process_quiz()` method
   - Quiz syntax uses markdown checkbox lists: `- [x]` for correct answers, `- [ ]` for incorrect
   - Question is everything before the first checkbox answer
   - Content section (optional) is everything after the last answer
   - Single correct answer = radio buttons; multiple correct = checkboxes
   - Quizzes replaced with placeholders (`<!-- MKDOCS_QUIZ_PLACEHOLDER_N -->`) in markdown

3. **HTML generation** (`_process_quiz`):
   - Parses quiz lines to extract question, answers, and content
   - Converts question and answers from markdown to HTML using `markdown_converter`
   - Generates form HTML with proper input types (radio/checkbox)
   - Adds `correct` attribute to correct answers (used by JS)
   - Content section is hidden until quiz is answered
   - Each quiz gets unique ID for deep linking (`id="quiz-N"`)
   - Quiz HTML is stored in `_quiz_storage` dict keyed by page path

4. **Asset injection** (`on_page_content`):
   - Replaces placeholders with stored quiz HTML
   - CSS and JS loaded at module level from `mkdocs_quiz/css/` and `mkdocs_quiz/js/`
   - Injected as inline `<style>` and `<script>` tags (not external files)
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
- **Validation**: Validates selected answers against `[correct]` attribute
- **Visual feedback**: Shows/hides content section, adds `.correct` and `.wrong` classes
- **Auto-submit**: If enabled and single-choice (radio), submits on selection change
- **Persistence**: Restores quiz state from localStorage on page load
- **Reset functionality**: "Try Again" button to reset individual quizzes (if not disabled after submit)
- **Helper**: `resetFieldset()` clears previous styling before re-validation

### Configuration Options

**Plugin-level** (in `mkdocs.yml`):

```yaml
plugins:
  - mkdocs-quiz:
      enabled_by_default: true # Process quizzes by default (default: true)
      auto_number: false # Auto-number questions (default: false)
      show_correct: true # Show correct answers when wrong (default: true)
      auto_submit: true # Auto-submit single-choice quizzes (default: true)
      disable_after_submit: true # Disable quiz after submission (default: true)
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
---
```

The plugin checks `_should_process_page()` to respect `enabled_by_default` and per-page `enabled` settings.

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

The plugin includes a CLI tool for migrating old quiz syntax:

```bash
# Migrate quizzes from old question:/answer: syntax to new markdown checkbox syntax
mkdocs-quiz migrate docs/

# Dry run to preview changes
mkdocs-quiz migrate docs/ --dry-run
```

The CLI tool ([mkdocs_quiz/cli.py](mkdocs_quiz/cli.py)) converts the legacy format to the current `- [x]`/`- [ ]` checkbox syntax.

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
