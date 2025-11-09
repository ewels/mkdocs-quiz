# Advanced Features

## Progress Tracking

When using the Material theme, mkdocs-quiz automatically adds a progress sidebar showing:

- Number of quizzes answered / total quizzes
- Number of correct answers / total quizzes
- Visual progress bar
- Reset button

Progress is saved in browser localStorage and persists across page reloads.

## Deep Linking to Quizzes

Each quiz automatically gets a unique ID that can be linked to:

```markdown
See [Quiz 1](#quiz-0) for more information.
```

Quizzes are numbered starting from 0: `#quiz-0`, `#quiz-1`, `#quiz-2`, etc.

## Auto-Numbering

Enable auto-numbering to prefix each question:

```yaml
# mkdocs.yml
plugins:
  - mkdocs-quiz:
      auto_number: true
```

This adds "Question 1:", "Question 2:", etc. before each quiz question.

You can also enable it per-page:

```yaml
---
quiz:
  auto_number: true
---
```

## Theming Integration

The plugin works with any MkDocs theme, but has special integration with Material theme:

- Progress sidebar in TOC
- Uses theme color variables
- Responsive design
- Dark mode support

## Migration from Old Syntax

If you have quizzes using the old mkdocs-quiz syntax (`question:`, `answer-correct:`, etc.), use the migration CLI tool to update your docs:

```bash
# Preview changes
mkdocs-quiz migrate docs/ --dry-run

# Apply changes
mkdocs-quiz migrate docs/
```

This converts:

```markdown
<quiz>
question: What is 2+2?
answer-correct: 4
answer: 3
answer: 5
content:
Correct!
</quiz>
```

To:

```markdown
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5

Correct!
</quiz>
```
