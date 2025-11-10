# Quick Start

Quizzes are created using special <code>&lt;quiz&gt;</code> tags in your markdown files. The basic structure is:

```html
<quiz> <!-- (1)! -->
Question text goes here <!-- (2)! -->
- [x] Correct answer <!-- (3)! -->
- [ ] Incorrect answer <!-- (4)! -->
- [ ] Another incorrect answer <!-- (5)! -->

Optional content revealed after correct answer <!-- (6)! -->
</quiz> <!-- (7)! -->
```

1.  Opening tag for the quiz, denotes where it starts (as long as it's not within a code block)
2.  The question. Can be multi-line and markdown.
3.  The correct answer, as indicated by the x in the checkbox.
    Multiple correct answers turn the radio buttons into checkboxes.
4.  An incorrect answer, as the checkbox has no tick
5.  Another incorrect answer. You can have as many as you want.
6.  Additional content, only shown after the answer is submitted (correctly or incorrectly).
7.  Closing tag for the quiz signifies the end.

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

## Intro Text

Add this comment to display an info message that explains that quiz results are saved to the browser's local storage and provides a "Reset quiz" button to clear all progress on the page.

```markdown
<!-- mkdocs-quiz intro -->
```

!!! info
    <!-- mkdocs-quiz intro -->

## Results Screen

Add this comment to display a results box (complete with confetti :tada:):

```markdown
<!-- mkdocs-quiz results -->
```

<!-- mkdocs-quiz results -->

## Next steps

- Check out [the examples](examples.md) to see more quiz variations
- Read more about the [intro text](intro-text.md) and [results screen](results-screen.md)
- Read about [auto numbering](auto-numbering.md)
- Learn about [configuration options](configuration.md)
