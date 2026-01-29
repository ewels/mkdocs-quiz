# Fill-in-the-Blank Quizzes

Fill-in-the-blank quizzes allow users to type answers into text fields. These are perfect for recall-based questions where users need to remember specific terms, values, or concepts.

!!! note "Case Insensitive"
Answers are case-insensitive and whitespace is trimmed. So "Paris", "paris", and " PARIS " are all accepted as correct.

## Basic Syntax

Use double square brackets `[[answer]]` to create a blank:

=== "Example"

    <quiz>
    The capital of France is [[Paris]].
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    The capital of France is [[Paris]].
    </quiz>
    ```

The text inside the brackets is the correct answer. Users see a text input field where they type their response.

## Multiple Blanks

You can include multiple blanks in a single question:

=== "Example"

    <quiz>
    Python was created by [[Guido van Rossum]] and first released in [[1991]].
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    Python was created by [[Guido van Rossum]] and first released in [[1991]].
    </quiz>
    ```

All blanks must be answered correctly for the quiz to be marked as correct.

## Content Section

To add explanatory content that appears after submission, use a horizontal rule `---` to separate the question from the content:

=== "Example"

    <quiz>
    2 + 2 = [[4]]

    ---
    That's correct! Basic arithmetic is fundamental to programming.
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    2 + 2 = [[4]]

    ---
    That's correct! Basic arithmetic is fundamental to programming.
    </quiz>
    ```

!!! info "Different from Multiple Choice"
Fill-in-the-blank quizzes use `---` to separate content, while multiple choice quizzes just use a blank line after the last answer.

## Complex Examples

Fill-in-the-blank quizzes support full markdown formatting around the blanks:

=== "Example"

    <quiz>
    In Python, use the [[print]] function to output text:

    ```python
    print("Hello, world!")
    ```

    The function was named **after** the [[printing press]].

    ---
    !!! tip
        You can also use `print()` with f-strings for formatting!

    ```python
    name = "World"
    print(f"Hello, {name}!")
    ```
    </quiz>

=== "Syntax"

    ~~~markdown
    <quiz>
    In Python, use the [[print]] function to output text:

    ```python
    print("Hello, world!")
    ```

    The function was named **after** the [[printing press]].

    ---
    !!! tip
        You can also use `print()` with f-strings for formatting!

    ```python
    name = "World"
    print(f"Hello, {name}!")
    ```
    </quiz>
    ~~~

## Wrong Answer Feedback

When `show_correct` is enabled (the default), incorrect answers show the correct answer as a placeholder hint:

<quiz>
The largest planet in our solar system is [[Jupiter]].
</quiz>

Try entering a wrong answer above to see how the feedback works!

## Use Cases

Fill-in-the-blank quizzes work well for:

- **Terminology**: "The process of converting code to machine language is called [[compilation]]."
- **Facts**: "HTML stands for [[HyperText Markup Language]]."
- **Code completion**: "To create a list in Python, use [[square brackets]] or the `list()` function."
- **Math**: "The square root of 144 is [[12]]."

## Differences from Multiple Choice

| Feature           | Multiple Choice              | Fill-in-the-Blank           |
| ----------------- | ---------------------------- | --------------------------- |
| Answer format     | `- [x]` / `- [ ]` checkboxes | `[[answer]]` brackets       |
| Content separator | Blank line after answers     | Horizontal rule `---`       |
| Auto-submit       | Yes (single choice)          | No, always requires submit  |
| Answer validation | Exact match of selections    | Case-insensitive text match |

## Next Steps

- Learn about [Multiple Choice](multiple-choice.md) quizzes
- See [Advanced Formatting](advanced-formatting.md) for code blocks, tables, and images
- Configure quiz behavior in [Configuration](configuration.md)
