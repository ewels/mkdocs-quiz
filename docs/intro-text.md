# Intro Text

The intro text panel provides users with helpful information about quiz progress storage and a convenient reset button to clear their progress.

## Basic Usage

Add the special comment anywhere in your markdown:

```markdown
<!-- mkdocs-quiz intro -->
```

This generates a panel that includes:

- **Information text**: Explains that quiz results are saved to the browser's local storage
- **Reset button**: Clears all quiz progress on the current page

## Example

The intro text looks best inside an admonition box:

=== "Example"

    !!! info "Quiz Progress"
        <!-- mkdocs-quiz intro -->

=== "Syntax"

    ```markdown
    !!! info "Quiz Progress"
        <!-- mkdocs-quiz intro -->
    ```

## Placement Suggestions

### At the Top of a Quiz Page

Place the intro text before any quizzes to set expectations:

```markdown
# Chapter 5 Quiz

!!! info "Before You Begin"

<!-- mkdocs-quiz intro -->

<quiz>
First question...
</quiz>
```

### In a Collapsible Section

Use with `pymdownx.details` for a collapsible info box:

=== "Example"

    ??? info "About This Quiz"
        <!-- mkdocs-quiz intro -->

        This quiz covers material from chapters 1-5.

=== "Syntax"

    ```markdown
    ??? info "About This Quiz"
        <!-- mkdocs-quiz intro -->

        This quiz covers material from chapters 1-5.
    ```

### Standalone

Without an admonition, the intro text renders as plain text with a reset link:

<!-- mkdocs-quiz intro -->

## When to Use Intro Text

The intro text is particularly useful when:

- Users might return to a quiz page and wonder why their answers are pre-filled
- You want to give users an easy way to retry quizzes
- Pages have multiple quizzes and users need to reset them all at once

!!! tip "Progress Sidebar"
On pages with multiple quizzes, the [Progress Tracking](progress-tracking.md) sidebar also includes a reset link. You may not need intro text if using the progress sidebar.

## Customizing the Text

The intro text content is translatable. See [Translations](translations.md) for details on customizing or translating the text.

## Related Features

- **[Progress Tracking](progress-tracking.md)**: Learn about the sidebar progress tracker
- **[Results Screen](results-screen.md)**: Add a completion summary with confetti
- **[Configuration](configuration.md)**: All available plugin options
