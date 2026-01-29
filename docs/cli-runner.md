# CLI Quiz Runner

MkDocs Quiz includes an interactive command-line quiz runner that lets you take quizzes directly in your terminal.

![CLI Demo](assets/cli-demo.gif)

This is useful for:

- Doing quizzes within training environments where users are already working in the terminal
- Quick self-assessment while developing documentation
- Taking quizzes from any deployed MkDocs site

!!! tip "Standalone Usage"

    While mkdocs-quiz is designed as an MkDocs plugin, the CLI runner can be used independently.
    You can run quizzes from markdown files without needing MkDocs installed or configured.
    Use `.mkdocs-quiz.yml` to organize your quizzes if you're not using MkDocs.

## Quick Start

Run quizzes interactively by selecting from discovered files:

```bash
mkdocs-quiz
```

Or specify a path directly:

```bash
mkdocs-quiz run path/to/quiz.md
```

Or run quizzes from a deployed MkDocs site:

```bash
mkdocs-quiz run https://example.com/docs/quiz-page/
```

## Usage

### Interactive Mode

If your current working directory is within a git repository, running `mkdocs-quiz` without arguments will attempt to enter an interactive mode:

1. **Config-based selection**: If a `cli_run` config is found (see [Configuration](#configuration)), you'll see a hierarchical menu to select quizzes
2. **File scanning**: Otherwise, the CLI scans for markdown files containing `<quiz>` tags in your git repository

```
$ mkdocs-quiz

mkdocs-quiz • https://github.com/ewels/mkdocs-quiz
───────────────────────────────────────────────────

? Select a quiz:
❯ Chapter 1: Introduction
  Chapter 2: Advanced Topics
  Chapter 3: Final Review
```

### Direct Path

Specify a file or directory:

```bash
# Single file
mkdocs-quiz run docs/chapter1/quiz.md

# Directory (runs all quizzes found)
mkdocs-quiz run docs/quizzes/
```

### From URL

Run quizzes from any deployed MkDocs Quiz site:

```bash
mkdocs-quiz run https://ewels.github.io/mkdocs-quiz/examples/
```

The CLI extracts quiz content from the rendered HTML page using special source comments that MkDocs Quiz embeds during build.

## Configuration

### Organizing Quizzes with `cli_run`

Add the `cli_run` config to your `mkdocs.yml` to define a menu structure. You can nest categories to any depth:

```yaml title="mkdocs.yml"
plugins:
  - mkdocs_quiz:
      cli_run:
        "Module 1 - Basics":
          "Introduction": docs/module1/intro.md
          "Core Concepts": docs/module1/concepts.md
        "Module 2 - Advanced":
          "Deep Dive": docs/module2/deep-dive.md
          "Final Quiz": docs/module2/final.md
```

This creates a nested menu in interactive mode:

```
? Select a quiz:
❯ Module 1 - Basics
  Module 2 - Advanced

? Select a quiz:
❯ Introduction
  Core Concepts
  ← Back
```

### Standalone Configuration

If you prefer to keep your `mkdocs.yml` clean, or are using the CLI runner without MkDocs, you can create a `.mkdocs-quiz.yml` file in your project root instead:

```yaml title=".mkdocs-quiz.yml"
cli_run:
  "Chapter 1": docs/chapter1.md
  "Chapter 2": docs/chapter2.md
```

The CLI checks `.mkdocs-quiz.yml` first, then falls back to `mkdocs.yml`.

## Features

### Progress Tracking

The CLI tracks your quiz history locally. When you revisit a quiz, you'll see your previous score:

```
Previous result: 8/10 (80%) - 2 days ago
```

History is stored in `~/.local/share/mkdocs-quiz/history.json` (Linux/macOS) or the equivalent [XDG data directory](https://specifications.freedesktop.org/basedir/latest/).

### Answer Shuffling

Randomize answer order to prevent memorization:

```bash
mkdocs-quiz run docs/quiz.md --shuffle
```

Or shuffle answers within questions only:

```bash
mkdocs-quiz run docs/quiz.md --shuffle-answers
```

## Quiz History

View your quiz history:

```bash
mkdocs-quiz history
```

Output formats:

```bash
mkdocs-quiz history --format table  # Default, rich table
mkdocs-quiz history --format json   # JSON output
mkdocs-quiz history --format csv    # CSV output
```

Clear history:

```bash
mkdocs-quiz history --clear
```
