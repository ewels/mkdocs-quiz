# Intro Text

The quiz intro text provides a helpful explanation to users about how quiz progress is saved, along with a convenient reset button to clear all progress on the page.

## How It Works

Add the special comment anywhere in your markdown to insert an intro text panel with a reset button:

```markdown
<!-- mkdocs-quiz intro -->
```

This will automatically generate a panel that includes:

- **Information text** explaining that quiz results are saved to the browser's local storage
- **Reset button** to clear all quiz progress on the current page

## Example

You can put the comment anywhere, but it looks great if you put it inside an [admonition box](https://squidfunk.github.io/mkdocs-material/reference/admonitions/):

=== "Example"

    !!! info "Quiz Progress"
        <!-- mkdocs-quiz intro -->

=== "Syntax"

    ```html
    !!! info "Quiz Progress"
        <!-- mkdocs-quiz intro -->
    ```
