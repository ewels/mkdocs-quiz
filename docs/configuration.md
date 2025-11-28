# Configuration

The mkdocs-quiz plugin can be configured both at plugin-wide level or page-level (YAML front matter).

!!! tip

    All configuration options are listed here with their defaults.
    You only need to specify the options that you want to override.
    In most cases, you'll not need the per-page frontmatter at all and not need to
    provide any options in `mkdocs.yml`:

    ```yaml
    plugins:
      - mkdocs_quiz
    ```

The full plugin-wide options in `mkdocs.yml` with their default values are as follows:

<!-- prettier-ignore-start -->
```yaml title="mkdocs.yml"
plugins:
  - mkdocs_quiz:
      enabled_by_default: true        # Enable quizzes by default on all pages
      auto_number: false              # Auto-number questions (Question 1:, Question 2:, etc.)
      show_correct: true              # Show correct answers when user gets it wrong
      auto_submit: true               # Auto-submit single-choice quizzes on selection
      disable_after_submit: true      # Disable question after first submission
      show_progress: true             # Show progress tracker sidebar and mobile bar
      progress_sidebar_position: top  # Position of progress tracker: "top" or "bottom"
      confetti: true                  # Show confetti animation when all quizzes completed
      language: en_US                 # Default language for quiz UI
      language_patterns: []           # Auto-detect language based on file paths
      custom_translations: {}         # Custom translation files
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
  language: fr_FR
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

### `progress_sidebar_position`

**Type:** `str` | **Default:** `"top"`

Controls the position of the progress tracker in the Material theme sidebar. Options:

- `"top"` - Appears above the Table of Contents (default)
- `"bottom"` - Appears below the Table of Contents

Useful for pages with substantial content where quizzes appear at the end. Only affects desktop sidebar positioning in Material theme.

### `confetti`

**Type:** `bool` | **Default:** `true`

Enables the confetti animation when all quizzes are completed with a score of 10% or higher. See [Results Screen](results-screen.md) for more details.

### `language`

**Type:** `str` | **Default:** `"en_US"`

Sets the default language for quiz UI elements (buttons, messages, progress tracking, etc.). Built-in languages include:

- `en_US` - English (default)
- `fr_FR` - French

See [Translations](translations.md) for complete documentation on using translations, adding custom languages, and contributing new translations.

### `language_patterns`

**Type:** `list` | **Default:** `[]`

Automatically detect the language based on file path patterns. Useful for multilingual sites organized by directory.

Example:

```yaml
plugins:
  - mkdocs_quiz:
      language: en_US # Default
      language_patterns:
        - pattern: "fr/**/*"
          language: fr_FR
        - pattern: "es/**/*"
          language: es_ES
```

With this configuration, files under `docs/fr/` will automatically use French translations, files under `docs/es/` will use Spanish, and all others will use English.

See [Translations](translations.md) for more details.

### `custom_translations`

**Type:** `dict` | **Default:** `{}`

Map language codes to custom translation files (`.po` format). Use this to:

- Override built-in translations
- Add completely new languages
- Customize text for your site's branding

Example:

```yaml
plugins:
  - mkdocs_quiz:
      custom_translations:
        en_US: translations/en_custom.po # Override built-in English
        ja_JP: translations/ja_JP.po # Add Japanese
```

Translation files should be relative to your `mkdocs.yml` file. See [Translations](translations.md) for complete documentation on creating and managing custom translations.
