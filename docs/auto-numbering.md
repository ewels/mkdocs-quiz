---
quiz:
  auto_number: true
---

# Auto-Numbering

This page demonstrates the auto-numbering feature. When enabled, each quiz automatically gets a "Question N:" header.

## How It Works

Auto-numbering can be enabled globally in `mkdocs.yml`:

```yaml
plugins:
  - mkdocs_quiz:
      auto_number: true
```

Or per-page using front matter (like this page):

```yaml
---
quiz:
  auto_number: true
---
```

## Example Quizzes

Below are several quizzes to demonstrate the auto-numbering in action.

<quiz>
What is 2 + 2?
- [ ] 3
- [x] 4
- [ ] 5

That's correct! 2 + 2 = 4
</quiz>

<quiz>
Which of these is a primary color?
- [x] Red
- [ ] Green
- [x] Blue
- [ ] Purple

Primary colors are red, blue, and yellow.
</quiz>

<quiz>
What is the capital of France?
- [ ] London
- [x] Paris
- [ ] Berlin
- [ ] Madrid

Paris is the capital city of France.
</quiz>

<quiz>
Which programming language is this plugin written in?
- [ ] JavaScript
- [x] Python
- [ ] Ruby
- [ ] Go

MkDocs Quiz is a Python plugin for MkDocs, which is also written in Python.
</quiz>

<quiz>
What does HTML stand for?
- [ ] Hyper Transfer Markup Language
- [x] Hypertext Markup Language
- [ ] High-Level Text Markup Language
- [ ] Hyperlink and Text Markup Language

HTML (Hypertext Markup Language) is the standard markup language for documents designed to be displayed in a web browser.
</quiz>

## Benefits of Auto-Numbering

- **Clear progression**: Users can easily see how many questions they've completed
- **Easy reference**: Questions can be referred to by number (e.g., "See Question 3")
- **Professional appearance**: Numbered questions look more organized in educational content
- **Consistent styling**: The `<h4 class="quiz-number">` header has consistent styling across all quizzes

## Styling

The question numbers are rendered as `<h4>` headers with the class `quiz-number`. You can customize the appearance with custom CSS:

```css
.quiz-number {
  color: var(--md-primary-fg-color);
  font-size: 1.2rem;
  text-transform: uppercase;
}
```

## Disabling Auto-Numbering

If auto-numbering is enabled globally but you want to disable it for a specific page, set it to `false` in the page's front matter:

```yaml
---
quiz:
  auto_number: false
---
```
