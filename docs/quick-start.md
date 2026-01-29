# Quick Start

Quizzes are created using special <code>&lt;quiz&gt;</code> tags in your markdown files. The basic structure is:

<!-- prettier-ignore-start -->
```html
<quiz> <!-- (1)! -->
Question text goes here <!-- (2)! -->
- [x] Correct answer <!-- (3)! -->
- [ ] Incorrect answer <!-- (4)! -->
- [ ] Another incorrect answer <!-- (5)! -->

Optional content revealed after correct answer <!-- (6)! -->
</quiz> <!-- (7)! -->
```
<!-- prettier-ignore-end -->

1.  Opening tag for the quiz, denotes where it starts (as long as it's not within a code block)
2.  The question. Can be multi-line and markdown.
3.  The correct answer, as indicated by the x in the checkbox.
    Multiple correct answers turn the radio buttons into checkboxes.
4.  An incorrect answer, as the checkbox has no tick
5.  Another incorrect answer. You can have as many as you want.
6.  Additional content, only shown after the answer is submitted (correctly or incorrectly).
7.  Closing tag for the quiz signifies the end.

!!! tip "Asterisk bullets"

    You can also use asterisk bullets (`*`) instead of hyphens (`-`) for answers.
    This is equally valid:

    ```markdown
    * [x] Correct answer
    * [ ] Incorrect answer
    * [ ] Another incorrect answer
    ```

This results in:

<quiz>
Question text goes here
- [x] Correct answer
- [ ] Incorrect answer
- [ ] Another incorrect answer

Optional content revealed after correct answer
</quiz>

## Multiple correct answers

When there's **one correct answer**, radio buttons are displayed as above.

When there are **multiple correct answers**, checkboxes are displayed:

```markdown
<quiz>
Which of these are programming languages?
- [x] Python
- [ ] HTML
- [x] JavaScript
- [ ] CSS

Python and JavaScript are programming languages, while HTML and CSS are markup/styling languages.
</quiz>
```

<quiz>
Which of these are programming languages?
- [x] Python
- [ ] HTML
- [x] JavaScript
- [ ] CSS

Python and JavaScript are programming languages, while HTML and CSS are markup/styling languages.
</quiz>

All correct answers, and only correct answers, must be selected to get the question correct.

## Content section

The content section is an optional block of markdown that comes after the answers.
It shows after the question has been submitted.

The content section can be useful for providing explanations, or additional context.

```markdown
<quiz>
What is MkDocs?
- [x] A static site generator
- [ ] A database
- [ ] A web server

## Learn More About MkDocs

MkDocs is a **fast**, **simple** static site generator built with Python.

- [Official Documentation](https://www.mkdocs.org)
- [GitHub Repository](https://github.com/mkdocs/mkdocs)

</quiz>
```

<quiz>
What is MkDocs?
- [x] A static site generator
- [ ] A database
- [ ] A web server

## Learn More About MkDocs

MkDocs is a **fast**, **simple** static site generator built with Python.

- [Official Documentation](https://www.mkdocs.org)
- [GitHub Repository](https://github.com/mkdocs/mkdocs)

</quiz>

## Fill-in-the-Blank

For questions where users type the answer, use double square brackets:

```markdown
<quiz>
The capital of France is [[Paris]].
</quiz>
```

<quiz>
The capital of France is [[Paris]].
</quiz>

!!! tip "Case Insensitive"
Answers are case-insensitive, so "Paris", "paris", and "PARIS" are all accepted.

See [Fill-in-the-Blank](fill-in-blank.md) for multiple blanks, content sections, and more.

## Next Steps

Now that you know the basics, explore further:

- **[Multiple Choice](multiple-choice.md)** - Radio buttons, checkboxes, and answer syntax
- **[Fill-in-the-Blank](fill-in-blank.md)** - Text input questions
- **[Advanced Formatting](advanced-formatting.md)** - Code blocks, tables, and images in quizzes
- **[Progress Tracking](progress-tracking.md)** - How quiz progress is saved
- **[Configuration](configuration.md)** - All available options
