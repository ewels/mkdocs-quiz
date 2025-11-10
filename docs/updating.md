---
title: Updating
---

# Migration from Old Syntax

If you have quizzes using the old pre-v1 mkdocs-quiz syntax (`question:`, `answer-correct:`, etc.), you can use the migration CLI tool to update your docs:

```bash
# Preview changes
mkdocs-quiz migrate docs/ --dry-run

# Apply changes
mkdocs-quiz migrate docs/
```

This converts:

```markdown
<?quiz?>
question: What is 2+2?
answer-correct: 4
answer: 3
answer: 5
content:
Correct!
<?/quiz?>
```

To:

```html
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5

Correct!
</quiz>
```
