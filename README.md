# MkDocs Quiz Plugin

[![PyPI version](https://badge.fury.io/py/mkdocs-quiz.svg)](https://badge.fury.io/py/mkdocs-quiz)
![PyPI - Downloads](https://img.shields.io/pypi/dm/mkdocs-quiz)
![Python versions](https://img.shields.io/badge/python-3.8%E2%80%933.14-blue)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A modern MkDocs plugin to create interactive quizzes directly in your markdown documentation. Perfect for educational content, tutorials, and documentation that requires user engagement.

**📚 Documentation and examples: [https://ewels.github.io/mkdocs-quiz/](https://ewels.github.io/mkdocs-quiz/)**

## Features

- ✨ **Simple markdown syntax** - Create quizzes using GitHub-flavored markdown checkboxes
- 🎯 **Multiple quiz types** - Single choice (radio), multiple choice (checkboxes), and fill-in-the-blank
- ⚡ **Instant feedback** - Visual indicators show correct/incorrect answers
- 📊 **Progress tracking** - Automatic progress sidebar and results panel, with confetti 🎉
- 💾 **Results saved** - Answers are saved to the browser's local storage
- 🌐 **Internationalization** - Quiz elements support multi-lingual sites
- 📤 **LMS Export** - Export quizzes to QTI format for Canvas, Blackboard, Moodle
- 🖥️ **CLI Quiz Runner** - Take quizzes in your terminal, from local files or website URLs

> [!TIP]
> Check out the [documentation](https://ewels.github.io/mkdocs-quiz/) to see the plugin in action.

```markdown
<quiz>
What's the best static site generator?
- [x] mkdocs
- [ ] Jekyll
- [ ] Sphinx

If you entered mkdocs, you've come to the right place!

![Random cat photo](https://cataas.com/cat)
</quiz>
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/ewels/mkdocs-quiz/main/docs/images/quiz_readme_dark.png">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/ewels/mkdocs-quiz/main/docs/images/quiz_readme.png">
  <img src="https://raw.githubusercontent.com/ewels/mkdocs-quiz/main/docs/images/quiz_readme.png" alt="mkdocs-quiz">
</picture>

## Installation

Install the package with pip:

```bash
pip install mkdocs-quiz
```

## Quick Start

### 1. Enable the plugin

Add the plugin to your `mkdocs.yml`:

```yaml
plugins:
  - mkdocs_quiz
```

### 2. Add your first question

Create a quiz with radio buttons (only one correct answer):

```markdown
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5

Correct! Basic math is important.
</quiz>
```

Use `- [x]` for correct answers and `- [ ]` for incorrect answers.
If multiple answers are correct, checkboxes instead of radio buttons will be shown (the user has to select all correct answers).

### 3. Intro text and results

Insert these placeholder comments for some intro text with a reset button and a final results panel (which shoots confetti when you finish):

```html
<!-- mkdocs-quiz intro -->

..quiz content here..

<!-- mkdocs-quiz results -->
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/ewels/mkdocs-quiz/main/docs/images/results_confetti_dark.gif">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/ewels/mkdocs-quiz/main/docs/images/results_confetti.gif">
  <img src="https://raw.githubusercontent.com/ewels/mkdocs-quiz/main/docs/images/results_confetti.gif" alt="mkdocs-quiz">
</picture>

## CLI Quiz Runner

Take quizzes directly in your terminal:

```bash
# Interactive mode - select from discovered quizzes in the current repository
# (you can also use `mkdocs-quiz` instead of `quiz`)
quiz

# Run from a website URL
quiz run https://ewels.github.io/mkdocs-quiz/multiple-choice/

# Run a specific file
mkdocs-quiz run docs/quiz.md
```

![CLI Demo](https://raw.githubusercontent.com/ewels/mkdocs-quiz/main/docs/assets/cli-demo.gif)

See the [CLI Runner documentation](https://ewels.github.io/mkdocs-quiz/cli-runner/) for more details.

## Contributing

Contributions are welcome! Please see [the contribution guidelines](https://ewels.github.io/mkdocs-quiz/contributing/) for details.

## License

This project is licensed under the Apache License 2.0 - see the [`LICENSE` file](https://github.com/ewels/mkdocs-quiz/blob/main/LICENSE) for details.

## Credits

- Original author: [Sebastian Jörz](https://github.com/skyface753)
- Rewritten by: [Phil Ewels](https://github.com/ewels)

## Changelog

See [CHANGELOG.md](https://ewels.github.io/mkdocs-quiz/changelog/) for version history and changes.
