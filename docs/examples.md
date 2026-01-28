# Writing quiz questions

This page demonstrates the different ways that you can build questions with mkdocs-quiz. Each example shows a working quiz in the "Example" tab and the markdown source code in the "Syntax" tab.

## Basic Examples

### Single Choice Quiz

A quiz with one correct answer displays as radio buttons:

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

### Multiple Choice Quiz

A quiz with multiple correct answers displays as checkboxes:

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

    **Key difference:** When there are multiple `- [x]` correct answers, checkboxes are displayed instead of radio buttons, and users must select all correct answers.

### Content after answering

The content section is an optional block of markdown that comes after the answers. It shows after the question has been submitted:

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

## Fill-in-the-Blank Quizzes

Fill-in-the-blank quizzes allow users to type answers into text fields. These are perfect for recall-based questions where users need to remember specific terms, values, or concepts.

### Single Blank

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

### Multiple Blanks

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

### Fill-in-the-Blank with Content

To add optional content (explanations, additional information) to fill-in-the-blank quizzes, use a horizontal rule `---` to separate the question from the content:

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

### Complex Fill-in-the-Blank

Fill-in-the-blank quizzes support markdown formatting around the blanks and rich content after the horizontal rule:

=== "Example"

    <quiz>
    Some markdown:

    The answer is [[foo]].

    Another answer is [[bar]].

    ---
    This *content* is only shown after answering.

    It can have **bold**, `code`, and other markdown formatting.
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    Some markdown:

    The answer is [[foo]].

    Another answer is [[bar]].

    ---
    This *content* is only shown after answering.

    It can have **bold**, `code`, and other markdown formatting.
    </quiz>
    ```

**Note:** Answers are case-insensitive and whitespace is trimmed. So "Paris", "paris", and " PARIS " are all accepted.

## Answer Syntax Variations

All of these checkbox formats are supported:

- `- [x]` - Correct answer (with lowercase x)
- `- [X]` - Correct answer (uppercase X also works)
- `- [ ]` - Incorrect answer (with space)
- `- []` - Incorrect answer (without space)

## Markdown in Questions and Answers

### Markdown in Questions

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

### Markdown in Answers

Answers can also include markdown:

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

## Rich Content Section

The content section supports full markdown formatting including headers, bold/italic text, lists, links, code blocks, images, and tables.

### Example with Rich Content

=== "Example"

    <quiz>
    What is MkDocs?
    - [x] A static site generator
    - [ ] A database
    - [ ] A web server
    - [ ] A framework

    ## About MkDocs

    MkDocs is a **fast**, **simple** and **downright gorgeous** static site generator.

    Key features:

    - Written in Python
    - Uses Markdown for content
    - Includes live preview server
    - Themeable with many themes available

    [Learn more at mkdocs.org](https://www.mkdocs.org)
    </quiz>

=== "Syntax"

    ````markdown
    <quiz>
    What is MkDocs?
    - [x] A static site generator
    - [ ] A database
    - [ ] A web server
    - [ ] A framework

    ## About MkDocs

    MkDocs is a **fast**, **simple** and **downright gorgeous** static site generator.

    Key features:

    - Written in Python
    - Uses Markdown for content
    - Includes live preview server
    - Themeable with many themes available

    [Learn more at mkdocs.org](https://www.mkdocs.org)
    </quiz>
    ````

### Example with Code Blocks

You can include code examples in the content section:

=== "Example"

    <quiz>
    Which loop syntax is correct in Python?
    - [x] `for item in items:`
    - [ ] `for (item in items)`
    - [ ] `foreach item in items`

    Here's a complete example:

    ```python
    fruits = ["apple", "banana", "cherry"]
    for fruit in fruits:
        print(fruit)
    ```

    This will print each fruit on a new line.
    </quiz>

=== "Syntax"

    `````markdown
    <quiz>
    Which loop syntax is correct in Python?
    - [x] `for item in items:`
    - [ ] `for (item in items)`
    - [ ] `foreach item in items`

    Here's a complete example:

    ```python
    fruits = ["apple", "banana", "cherry"]
    for fruit in fruits:
        print(fruit)
    ```

    This will print each fruit on a new line.
    </quiz>
    `````

### Example with Images

=== "Example"

    <quiz>
    Which programming language has this logo? 🐍
    - [x] Python
    - [ ] JavaScript
    - [ ] Ruby

    ![Random cat photo](https://cataas.com/cat)

    Python's logo features two intertwined snakes!
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    Which programming language has this logo? 🐍
    - [x] Python
    - [ ] JavaScript
    - [ ] Ruby

    ![Random cat photo](https://cataas.com/cat)

    Python's logo features two intertwined snakes!
    </quiz>
    ```

### Example with Tables

=== "Example"

    <quiz>
    What's special about this formula: E = mc²?
    - [ ] It calculates electricity
    - [x] It relates mass and energy
    - [ ] It describes gravity

    Einstein's famous equation shows:

    | Symbol | Meaning |
    |--------|---------|
    | E | Energy |
    | m | Mass |
    | c | Speed of light |

    The equation reveals that mass and energy are interchangeable!
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    What's special about this formula: E = mc²?
    - [ ] It calculates electricity
    - [x] It relates mass and energy
    - [ ] It describes gravity

    Einstein's famous equation shows:

    | Symbol | Meaning |
    |--------|---------|
    | E | Energy |
    | m | Mass |
    | c | Speed of light |

    The equation reveals that mass and energy are interchangeable!
    </quiz>
    ```

## Markdown Extensions Support

Quizzes automatically use the same `markdown_extensions` configured in your `mkdocs.yml`. This means you can use advanced markdown features like syntax highlighting with line numbers, admonitions, and more.

### Code with Line Highlighting

If you have `pymdownx.highlight` configured, you can use line highlighting in quiz code blocks:

=== "Example"

    <quiz>
    Testing `markdown_extentions`. Python code `#!py int | str`:

    ```python title="test_file.py" linenums="42" hl_lines="3"
    def checksum(a):
        assert 2 + 2 == 4
    ```

    - [ ] 3
    - [x] 4 *(not `four`)*
    - [ ] 5

    </quiz>

=== "Syntax"

    ~~~markdown
    <quiz>
    Testing `markdown_extentions`. Python code `#!py int | str`:

    ```python title="test_file.py" linenums="42" hl_lines="3"
    def checksum(a):
        assert 2 + 2 == 4
    ```

    - [ ] 3
    - [x] 4 *(not `four`)*
    - [ ] 5

    </quiz>
    ~~~

=== "mkdocs.yml"

    ```yaml
    markdown_extensions:
      - pymdownx.highlight:
          anchor_linenums: true
          line_spans: __span
          pygments_lang_class: true
      - pymdownx.superfences
    ```

### Code blocks in the extra content

Markdown extensions also work in the extra content that is shown after questions are answered:

=== "Example"

    <quiz>
    What line prints `"hello"`?
    - [x] Line 2
    - [ ] Line 1
    - [ ] Line 3

    ```python hl_lines="2"
    def greet():
        print("hello")
        return True
    ```
    </quiz>

=== "Syntax"

    ~~~markdown
    <quiz>
    What line prints `"hello"`?
    - [x] Line 2
    - [ ] Line 1
    - [ ] Line 3

    ```python hl_lines="2"
    def greet():
        print("hello")
        return True
    ```
    </quiz>
    ~~~

=== "mkdocs.yml"

    ```yaml
    markdown_extensions:
      - pymdownx.highlight:
          anchor_linenums: true
          line_spans: __span
          pygments_lang_class: true
      - pymdownx.superfences
    ```

### Admonitions in Quizzes

If you have the `admonition` extension configured, you can use admonitions in quiz content:

=== "Example"

    <quiz>
    What type of admonition is shown below?
    - [x] A warning
    - [ ] An error
    - [ ] A note

    !!! warning
        This is a warning admonition!
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    What type of admonition is shown below?
    - [x] A warning
    - [ ] An error
    - [ ] A note

    !!! warning
        This is a warning admonition!
    </quiz>
    ```

### Other Extensions

All markdown extensions configured in your `mkdocs.yml` work within quizzes, including:

- `pymdownx.superfences` - Enhanced code blocks
- `pymdownx.highlight` - Syntax highlighting with options
- `pymdownx.inlinehilite` - Inline code highlighting
- `admonition` - Callout boxes
- `attr_list` - Add attributes to elements
- `tables` - Markdown tables
- And any other extensions you have configured!

## Important Notes

1. **Content must be valid markdown/HTML**: The content section is processed as markdown and must be valid
2. **Checkbox syntax is recognized**: Use `- [x]`, `- [X]`, `- [ ]`, or `- []`
3. **At least one correct answer required**: Every quiz must have at least one `- [x]` answer
4. **Empty lines are ignored**: Blank lines between answers are okay
5. **Question comes first**: The first block of lines after `<quiz>` until the first checkbox is always the question
