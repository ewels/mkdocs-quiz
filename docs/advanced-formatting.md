# Advanced Formatting

Quizzes support full markdown formatting in questions, answers, and content sections. They automatically use the same `markdown_extensions` configured in your `mkdocs.yml`, enabling features like syntax highlighting, admonitions, and more.

## Rich Content Section

The content section (revealed after answering) supports headers, lists, links, and any other markdown:

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
    - Many [cool plugins](index.md)

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

## Code Blocks

Include code examples in your quizzes and content sections:

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

## Code with Line Highlighting

If you have `pymdownx.highlight` configured, you can use line numbers and highlighting:

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

### Code in Questions

You can also include code blocks in the question itself:

=== "Example"

    <quiz>
    Testing `markdown_extensions`. Python code `#!py int | str`:

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
    Testing `markdown_extensions`. Python code `#!py int | str`:

    ```python title="test_file.py" linenums="42" hl_lines="3"
    def checksum(a):
        assert 2 + 2 == 4
    ```

    - [ ] 3
    - [x] 4 *(not `four`)*
    - [ ] 5

    </quiz>
    ~~~

## Admonitions

Use admonition callout boxes in quiz content:

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

Requires the `admonition` extension in your `mkdocs.yml`.

## Tables

Include tables in your content sections:

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

## Images

Include images in the content section:

=== "Example"

    <quiz>
    Which programming language has this logo?
    - [x] Python
    - [ ] JavaScript
    - [ ] Ruby

    ![Random cat photo](https://cataas.com/cat)

    Python's logo features two intertwined snakes!
    </quiz>

=== "Syntax"

    ```markdown
    <quiz>
    Which programming language has this logo?
    - [x] Python
    - [ ] JavaScript
    - [ ] Ruby

    ![Random cat photo](https://cataas.com/cat)

    Python's logo features two intertwined snakes!
    </quiz>
    ```

## Supported Extensions

All markdown extensions configured in your `mkdocs.yml` work within quizzes, including:

| Extension               | Features                         |
| ----------------------- | -------------------------------- |
| `pymdownx.superfences`  | Enhanced code blocks             |
| `pymdownx.highlight`    | Syntax highlighting with options |
| `pymdownx.inlinehilite` | Inline code highlighting         |
| `admonition`            | Callout boxes                    |
| `attr_list`             | Add attributes to elements       |
| `tables`                | Markdown tables                  |
| `pymdownx.tabbed`       | Content tabs                     |

## Important Notes

1. **Content must be valid markdown**: The content section is processed as markdown
2. **Extensions must be enabled**: Features like admonitions require the corresponding extension in `mkdocs.yml`
3. **Nesting code blocks**: When showing quiz syntax in documentation, use more backticks/tildes than the inner block

## Next Steps

- Learn about [Multiple Choice](multiple-choice.md) quiz syntax
- Learn about [Fill-in-the-Blank](fill-in-blank.md) quizzes
- Configure extensions in [Configuration](configuration.md)
