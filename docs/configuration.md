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

```yaml title="mkdocs.yml"
plugins:
  - mkdocs-quiz:
      enabled_by_default: true    # Enable quizzes by default on all pages
      auto_number: false          # Auto-number questions (Question 1:, Question 2:, etc.)
      show_correct: true          # Show correct answers when user gets it wrong
      auto_submit: true           # Auto-submit single-choice quizzes on selection
      disable_after_submit: true  # Disable question after first submission
```

The syntax is very similar when overriding these defaults at individual-page level:

```yaml title="my-content.md"
---
quiz:
  enabled: false
  auto_number: true
  show_correct: false
  auto_submit: false
  disable_after_submit: false
---

# Your Page Content

<quiz>
...
</quiz>
```

!!! info

    Page-specific configuration always takes priority over site-wide configuration.
