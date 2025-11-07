# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-07

### 🚨 Breaking Changes

#### New Quiz Syntax (Migration Required)

The quiz syntax has been completely redesigned to use a cleaner, markdown-style format. The old `question:`, `answer:`, `answer-correct:`, and `content:` syntax is **no longer supported**.

**Old Syntax (v1.x):**
```markdown
<?quiz?>
question: Are you ready?
answer-correct: Yes!
answer: No!
answer: Maybe!
content:
<h2>Some additional content</h2>
<?/quiz?>
```

**New Syntax (v2.0):**
```markdown
<?quiz?>
Are you ready?
- [x] Yes!
- [ ] No!
- [ ] Maybe!

Some additional content here
<?/quiz?>
```

**Migration:**
- A CLI migration tool is provided: `mkdocs-quiz migrate`
- Run: `mkdocs-quiz migrate docs/` to automatically convert all quiz blocks
- Use `--dry-run` flag to preview changes without modifying files
- Use git tracked changes to review before committing

#### Changed Defaults

The following options now default to **enabled** (opt-out instead of opt-in):

- `show-correct` - Now defaults to `true` (shows correct answers when user gets it wrong)
- `auto-submit` - Now defaults to `true` (submits automatically on selection for single-answer quizzes)
- `disable-after-submit` - Now defaults to `true` (locks quiz after first submission)

To restore v1.x behavior, explicitly disable these options:
```markdown
<?quiz?>
Your question?
show-correct: false
auto-submit: false
disable-after-submit: false
- [x] Correct answer
- [ ] Wrong answer
<?/quiz?>
```

### ✨ Added Features

#### Core Functionality

- **Markdown support in questions and answers** - Full markdown parsing including bold, italic, code, links, images, etc.
- **Optional content section** - No longer required to include content when there's nothing additional to show
- **Full markdown in content section** - Content area now supports complete markdown syntax, not just HTML

#### Per-Quiz Options

- **Show correct answers option** - `show-correct: true` reveals all correct answers in green when user selects wrong answer (defaults to true)
- **Auto-submit option** - `auto-submit: true` automatically submits quiz when radio button is selected, no Submit button needed (defaults to true)
- **Disable after submit option** - `disable-after-submit: true` locks the quiz after first submission, prevents changing answers (defaults to true)

#### Navigation & UX

- **Quiz header IDs** - Each quiz gets a unique ID (`quiz-0`, `quiz-1`, etc.) with hover anchor link for direct navigation
- **Try Again button** - Automatically appears after quiz submission to reset answers and retry
  - Hidden when `disable-after-submit: true`
  - Clears all selections and resets quiz state
  - Updates progress tracker when used

#### Plugin Configuration

All plugin options are configured in `mkdocs.yml`:

```yaml
plugins:
  - mkdocs_quiz:
      enabled_by_default: true    # Set to false for opt-in mode
      auto_number: false          # Set to true to auto-number questions
      question_tag: h3            # HTML tag for questions (h1-h6)
```

- **Opt-in/opt-out mode** - `enabled_by_default: false` requires pages to explicitly enable quizzes with `quiz: enable` in front matter
- **Auto-numbering** - `auto_number: true` automatically numbers questions as "Question 1:", "Question 2:", etc. using CSS counters
- **Customizable question heading** - `question_tag: h2` allows using any heading level (h1-h6) instead of default h3

#### Progress Tracking & Persistence

- **Global progress tracking** - Tracks answered/correct status across all quizzes on the page
- **LocalStorage persistence** - Progress automatically saved per-page and restored on reload
- **Progress sidebar widget** - Floating sidebar displays:
  - Answered questions count (e.g., "3 / 5")
  - Progress bar with percentage
  - Correct answers count and percentage
  - Only appears when there are 2+ quizzes on the page
  - Automatically hidden on mobile/small screens
- **Custom event dispatching** - Emits `quizProgressUpdate` event for custom integrations

### 🔧 Changed

- Question heading defaults to `h3` but can now be customized via `question_tag` config option
- Content section now supports full markdown conversion instead of raw HTML pass-through
- Quiz options (`show-correct`, `auto-submit`, `disable-after-submit`) now default to `true`
- Submit button is hidden after submission (Try Again button appears instead)
- CSS uses theme color variables when available (`--md-primary-fg-color`, etc.)

### 🐛 Fixed

- Improved error handling for malformed quiz blocks
- Better empty line handling in quiz content
- Fixed markdown parsing for inline code and special characters
- Consistent behavior across different MkDocs themes

### 📚 Documentation

- Updated README with new syntax examples
- Added migration guide and script
- Documented all new configuration options
- Added examples for all new features

### 🏗️ Technical

- Migrated to modern Python markdown library usage
- Improved quiz parsing logic for better maintainability
- Added CSS counters for auto-numbering
- Implemented localStorage API for persistence
- Enhanced JavaScript event handling
- Better separation of concerns (parsing vs rendering)

### 🧪 Testing

- All tests updated for new syntax
- Added tests for new features:
  - Markdown in questions/answers
  - Optional content section
  - New default behaviors
  - Progress tracking
  - Quiz options (show-correct, auto-submit, disable-after-submit)
- 15 passing tests with 100% coverage

## [1.0.0] - 2025-01-07

### Added

- Modernized codebase with Python 3.8+ support
- Migrated from deprecated `distutils` to modern `pyproject.toml` (PEP 517/518)
- Added comprehensive type hints throughout the codebase
- Improved error handling and logging
- Added proper package structure with `__init__.py` files
- Switched to Ruff for Python formatting and linting (faster than Black + Flake8)
- Added Prettier for JavaScript and CSS formatting
- Added comprehensive test suite with pytest (8 tests)
- Added pre-commit hooks for automatic code quality checks
- Automated PyPI publishing via GitHub Actions with trusted publishing
- Added GitHub Actions CI for testing on Python 3.8-3.12
- Created dedicated CHANGELOG.md file
- Created comprehensive CONTRIBUTING.md guide

### Changed

- Better code organization and documentation
- Refactored quiz processing into separate methods for clarity
- Improved README.md to be more user-focused
- Updated all dependencies to latest versions

### Removed

- Removed deprecated `setup.py` (no backwards compatibility needed)
- Removed `Makefile` (pre-commit handles everything)
- Removed `distutils` dependency

## Historical Releases

### Pre-1.0.0

Previous versions by original author [Sebastian Jörz](https://github.com/skyface753).
See original repository history for details.

[1.0.0]: https://github.com/ewels/mkdocs-quiz/releases/tag/v1.0.0
