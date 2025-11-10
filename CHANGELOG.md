# Changelog

## **Version 1.0.0** (2025-11-10)

v1.0.0 of mkdocs-quiz is a complete rewrite of the original plugin.
It modernises the codebase, changes the quiz markdown syntax, and adds a bunch of new features.

### 🚨 Breaking Changes

#### New Quiz Syntax (Migration Required)

The quiz syntax has been completely redesigned to use a cleaner, markdown-style format. The old `question:`, `answer:`, `answer-correct:`, and `content:` syntax is **no longer supported**.

**Old Syntax (v1.x):**
```markdown
<?quiz?>
question: Are you ready?
answer-correct: Yes!
answer: No!
answer: Maybe!
content:
<h2>Some additional content</h2>
<?/quiz?>
```

**New Syntax (v2.0):**
```markdown
<quiz>
Are you ready?
- [x] Yes!
- [ ] No!
- [ ] Maybe!

Some additional content here
</quiz>
```

**Migration:**
- A CLI migration tool is provided: `mkdocs-quiz migrate`
- Run: `mkdocs-quiz migrate docs/` to automatically convert all quiz blocks
- Use `--dry-run` flag to preview changes without modifying files
- Use git tracked changes to review before committing

### ✨ Added Features

#### Core Functionality

- **Markdown support in questions and answers** - Full markdown parsing including bold, italic, code, links, images, etc.
- **Optional content section** - No longer required to include content when there's nothing additional to show
- **Full markdown in content section** - Content area now supports complete markdown syntax, not just HTML

#### Per-Quiz Options

- **Show correct answers option** - `show-correct: true` reveals all correct answers in green when user selects wrong answer (defaults to true)
- **Auto-submit option** - `auto-submit: true` automatically submits quiz when radio button is selected, no Submit button needed (defaults to true)
- **Disable after submit option** - `disable-after-submit: true` locks the quiz after first submission, prevents changing answers (defaults to true)

#### Navigation & UX

- **Quiz header IDs** - Each quiz gets a unique ID (`quiz-0`, `quiz-1`, etc.) with hover anchor link for direct navigation
- **Try Again button** - Automatically appears after quiz submission to reset answers and retry
  - Hidden when `disable-after-submit: true`
  - Clears all selections and resets quiz state
  - Updates progress tracker when used

#### Plugin Configuration

All plugin options are configured in `mkdocs.yml`:

```yaml
plugins:
  - mkdocs_quiz:
      enabled_by_default: true    # Set to false for opt-in mode
      auto_number: false          # Set to true to auto-number questions
```

- **Opt-in/opt-out mode** - `enabled_by_default: false` requires pages to explicitly enable quizzes with `quiz: enable` in front matter
- **Auto-numbering** - `auto_number: true` automatically numbers questions as "Question 1:", "Question 2:", etc.

#### Progress Tracking & Persistence

- **Global progress tracking** - Tracks answered/correct status across all quizzes on the page
- **LocalStorage persistence** - Progress automatically saved per-page and restored on reload
- **Progress sidebar widget** - Floating sidebar displays:
  - Answered questions count (e.g., "3 / 5")
  - Progress bar with percentage
  - Correct answers count and percentage
  - Only appears when there are 2+ quizzes on the page
  - Automatically hidden on mobile/small screens
- **Custom event dispatching** - Emits `quizProgressUpdate` event for custom integrations

## Pre-1.0.0

Previous versions by original author [Sebastian Jörz](https://github.com/skyface753).
See original GitHub history for details: https://github.com/skyface753/mkdocs-quiz/
