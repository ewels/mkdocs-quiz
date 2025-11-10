# MkDocs Quiz Plugin

[![PyPI version](https://badge.fury.io/py/mkdocs-quiz.svg)](https://badge.fury.io/py/mkdocs-quiz)
[![Python versions](https://img.shields.io/pypi/pyversions/mkdocs-quiz.svg)](https://pypi.org/project/mkdocs-quiz/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A modern MkDocs plugin to create interactive quizzes directly in your markdown documentation. Perfect for educational content, tutorials, and documentation that requires user engagement.


## Features

- ✨ **Simple markdown syntax** - Create quizzes using GitHub-flavored markdown checkboxes
- 🎯 **Single and multiple choice** - One correct answer = radio buttons, multiple = checkboxes
- ⚡ **Instant feedback** - Visual indicators show correct/incorrect answers
- 📊 **Progress tracking** - Automatic progress sidebar and results panel, with confetti :tada:

```html
<quiz>
What's the best static site generator? <!-- (1)! -->
- [x] mkdocs <!-- (2)! -->
- [ ] Jekyll <!-- (3)! -->
- [ ] Sphinx

You've come to the right place! <!-- (4)! -->
![Random cat photo](https://cataas.com/cat)
</quiz>
```

1.  Your question (supports markdown)
2.  Correct answers are 'checked'
3.  Incorrect answers are unchecked
4.  Additional content at the bottom that shows after the question has been answered (supports arbitrary markdown and HTML).

<quiz>
What's the best static site generator? <!-- (1)! -->
- [x] mkdocs <!-- (2)! -->
- [ ] Jekyll <!-- (3)! -->
- [ ] Sphinx

You've come to the right place! <!-- (4)! -->

![Random cat photo](https://cataas.com/cat){ width="200" }
</quiz>

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Credits

- Original author: [Sebastian Jörz](https://github.com/skyface753)
- Co-maintained by: [Phil Ewels](https://github.com/ewels)
