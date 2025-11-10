# Configuration

The mkdocs-quiz plugin can be configured both at plugin-wide level or page-level (YAML front matter).

!!! tip

    All configuration options are listed here with their defaults.
    You only need to specify the options that you want to override.
    In most cases, you'll not need the per-page frontmatter at all and not need to
    provide any options in `mkdocs.yml`:

    ```yaml
    plugins:
      - mkdocs-quiz
    ```

The full plugin-wide options in `mkdocs.yml` with their default values are as follows:

<!-- prettier-ignore-start -->
```yaml title="mkdocs.yml"
plugins:
  - mkdocs-quiz:
      enabled_by_default: true    # Enable quizzes by default on all pages
      auto_number: false          # Auto-number questions (Question 1:, Question 2:, etc.)
      show_correct: true          # Show correct answers when user gets it wrong
      auto_submit: true           # Auto-submit single-choice quizzes on selection
      disable_after_submit: true  # Disable question after first submission
      show_progress: true         # Show progress tracker sidebar and mobile bar
      confetti: true              # Show confetti animation when all quizzes completed
```
<!-- prettier-ignore-end -->

The syntax is very similar when _overriding_ any of these defaults at individual-page level:

```yaml title="my-content.md"
---
quiz:
  enabled: false
  auto_number: true
  show_correct: false
  auto_submit: false
  disable_after_submit: false
  show_progress: false
---
# Your Page Content

<quiz>
[...]
</quiz>
```

!!! info

    Page-specific configuration always takes priority over site-wide configuration.

## Configuration Options

### `enabled_by_default`

**Type:** `bool` | **Default:** `true`

Controls whether quizzes are processed on all pages by default. When set to `false`, quizzes will only be processed on pages where `quiz.enabled: true` is explicitly set in the frontmatter.

### `auto_number`

**Type:** `bool` | **Default:** `false`

When enabled, automatically numbers questions with headers like "Question 1", "Question 2", etc. See [Auto-Numbering](auto-numbering.md) for examples.

### `show_correct`

**Type:** `bool` | **Default:** `true`

When enabled, shows the correct answers when a user selects an incorrect answer. When disabled, users only see feedback that their answer was wrong without revealing the correct options.

### `auto_submit`

**Type:** `bool` | **Default:** `true`

Automatically submits single-choice quizzes (radio buttons) when the user selects an answer. For multiple-choice quizzes, a submit button is always shown regardless of this setting.

### `disable_after_submit`

**Type:** `bool` | **Default:** `true`

When enabled, disables the quiz after the first submission. Users cannot change their answers or retry. When disabled, a "Try Again" button appears allowing users to retry the quiz.

### `show_progress`

**Type:** `bool` | **Default:** `true`

Controls the visibility of the progress tracker. When enabled, displays:

- **Desktop**: Progress tracker in the right sidebar (TOC area) on Material theme
- **Mobile**: Sticky progress bar at the top of the page
- **Statistics**: Shows answered/total questions and correct/incorrect counts

Set to `false` to hide progress tracking entirely on pages where you don't want it visible.

### `confetti`

**Type:** `bool` | **Default:** `true`

Enables the confetti animation when all quizzes are completed with a score of 10% or higher. See [Results Screen](results-screen.md) for more details.
