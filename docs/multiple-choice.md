# Multiple Choice Quizzes

Multiple choice quizzes use checkbox syntax to define questions with selectable answers. The plugin automatically detects whether to display radio buttons or checkboxes based on the number of correct answers.

## Single Choice (Radio Buttons)

When there's **one correct answer**, radio buttons are displayed:

=== "Example"

    <quiz>
    What is the answer to the following sum?
    ```
    2 + 2
    ```
    - [ ] 3
    - [x] 4 _(not `four`)_
    - [ ] 5
    </quiz>

=== "Syntax"

    ~~~markdown
    <quiz>
    What is the answer to the following sum?
    ```
    2 + 2
    ```
    - [ ] 3
    - [x] 4 _(not `four`)_
    - [ ] 5
    </quiz>
    ~~~

With single-choice quizzes, the answer is submitted automatically when selected (unless `auto_submit` is disabled).

## Multiple Choice (Checkboxes)

When there are **multiple correct answers**, checkboxes are displayed:

=== "Example"

    <quiz>
    Which of these are even numbers?
    - [x] 2
    - [ ] 3
    - [x] 4
    - [ ] 5
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    Which of these are even numbers?
    - [x] 2
    - [ ] 3
    - [x] 4
    - [ ] 5
    </quiz>
    ```

All correct answers, and only correct answers, must be selected to get the question correct. A submit button is always shown for multiple-choice quizzes.

## Content Section

The content section is an optional block of markdown that appears after the answers are submitted:

=== "Example"

    <quiz>
    Is Python a programming language?
    - [x] Yes
    - [ ] No

    Did you know that Python was named after
    [Monty Python](https://en.wikipedia.org/wiki/Monty_Python)?
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    Is Python a programming language?
    - [x] Yes
    - [ ] No

    Did you know that Python was named after
    [Monty Python](https://en.wikipedia.org/wiki/Monty_Python)?
    </quiz>
    ```

The content section can include any markdown formatting - see [Advanced Formatting](advanced-formatting.md) for examples with code blocks, tables, images, and more.

## Answer Syntax Variations

All of these checkbox formats are supported:

| Syntax  | Meaning                          |
| ------- | -------------------------------- |
| `- [x]` | Correct answer (lowercase x)     |
| `- [X]` | Correct answer (uppercase X)     |
| `- [ ]` | Incorrect answer (with space)    |
| `- []`  | Incorrect answer (without space) |

You can also use asterisks instead of hyphens:

```markdown
- [x] Correct answer
- [ ] Incorrect answer
```

## Markdown in Questions

Questions can include markdown formatting like bold, italics, and code:

=== "Example"

    <quiz>
    What is the result of `2 ** 3` in **Python**?
    - [ ] 6
    - [x] 8
    - [ ] 9

    The `**` operator is exponentiation: 2<sup>3</sup> = 8
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    What is the result of `2 ** 3` in **Python**?
    - [ ] 6
    - [x] 8
    - [ ] 9

    The `**` operator is exponentiation: 2<sup>3</sup> = 8
    </quiz>
    ```

## Markdown in Answers

Answers can also include markdown formatting:

=== "Example"

    <quiz>
    Which is the correct Python syntax?
    - [ ] `print "Hello"`
    - [x] `print("Hello")`
    - [ ] `echo "Hello"`

    In Python 3, `print()` is a function, not a statement.
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    Which is the correct Python syntax?
    - [ ] `print "Hello"`
    - [x] `print("Hello")`
    - [ ] `echo "Hello"`

    In Python 3, `print()` is a function, not a statement.
    </quiz>
    ```

## Important Notes

1. **At least one correct answer required**: Every quiz must have at least one `- [x]` answer
2. **Empty lines are ignored**: Blank lines between answers are fine
3. **Question comes first**: Everything before the first checkbox is the question
4. **Content comes last**: Everything after the last answer is the content section

## Next Steps

- Learn about [Fill-in-the-Blank](fill-in-blank.md) quizzes for text input questions
- See [Advanced Formatting](advanced-formatting.md) for code blocks, tables, and images in quizzes
- Configure quiz behavior in [Configuration](configuration.md)
