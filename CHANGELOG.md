# Changelog

## **Version 1.2.1** (unreleased)

- Add translations for sidebar progress strings (`Answered`, `Correct`, `Reset`) - [#20](https://github.com/ewels/mkdocs-quiz/issues/20)
- Add HTML template extraction to `mkdocs-quiz translations update` CLI command
  - Ensures `data-quiz-translate` attributes in HTML templates are tracked in translation files
- Revised Norwegian translations - [#19](https://github.com/ewels/mkdocs-quiz/pull/19) by @remiolsen

## **Version 1.2.0** (2025-11-29)

- Add internationalisation
  - All UI-element strings are now wrapped in translation functions
  - Translations handled with `.po` files, plus `mkdocs-quiz translations` helper CLI commands
  - Initially released with translations for a subset of those [supported by mkdocs-material](https://squidfunk.github.io/mkdocs-material/setup/changing-the-language/):
    - Brazilian Portugese by @dunossauro - [#17](https://github.com/ewels/mkdocs-quiz/issues/17)
    - French, Spanish, Swedish, German, Norwegian, Chinese (simplified), Korean, Esperanto, Hindi, Indonesian, Japanese all done automatically by @Claude - please submit a PR if something sounds wrong!
    - New language contributions welcome!
- Fixed plugin name in documentation - [#12](https://github.com/ewels/mkdocs-quiz/issues/12)

## **Version 1.1.0** (2025-11-13)

- Add `progress_sidebar_position` configuration option [#6](https://github.com/ewels/mkdocs-quiz/issues/6)
  - Allows positioning the progress tracker either above or below the Table of Contents in Material theme
  - Set to `"top"` (default) to place above TOC, or `"bottom"` to place below TOC
  - Useful for pages with substantial content where quiz appears at the end
  - Move sidebar progress inside ToC `<nav>` for cleaner theme/plugin integration

## **Version 1.0.2** (2025-11-13)

- Refactor the migration script to not use `rich` and `typer`
  - Typer requires Python 3.10 and the dependencies were complicating the conda-forge build
  - The migration script is a bonus helper utility only, and these weren't needed for functionality

## **Version 1.0.1** (2025-11-13)

- Add check for old v0 quiz syntax [#8](https://github.com/ewels/mkdocs-quiz/pull/8)
  - If found, triggers an exception that stops the build with an error message explaining and pointing to the CLI migration command
  - Should prevent silent failures with unparsed v0 quiz markup going unnoticed
- Clean up readme for better presentation on pypi.org
- Stronger typing: added types for functions

## **Version 1.0.0** (2025-11-13)

v1.0.0 of mkdocs-quiz is a **complete rewrite** of the original plugin. It modernises the codebase, changes the quiz markdown syntax, and adds a lot of new functionality.

The plugin was originally written by [@skyface753](https://github.com/skyface753/), who has graciously passed the repository over to [@ewels](https://github.com/ewels/) for future development after this rewrite. [@skyface753](https://github.com/skyface753/) will stay on as a maintainer.

### 🚨 Breaking Changes

#### New Quiz Syntax

The quiz syntax has been completely redesigned to use a cleaner, markdown-style format. The old `question:`, `answer:`, `answer-correct:`, and `content:` syntax is **no longer supported**. The opening and closing tags no longer have the `?` characters.

**Old Syntax (v1.x):**

<!-- prettier-ignore-start -->
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
<!-- prettier-ignore-end -->

**New Syntax (v1.0):**

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
- **Plugin configuragion** - Both site-wise in `mkdocs.yml` or page-specific in the YAML frontmatter.
- **Auto-submit answers** - No need to press 'Submit' for single-choice questions
- **Quiz header IDs** - Each quiz gets a unique ID (`quiz-0`, `quiz-1`, etc.) with hover anchor link for direct navigation. Optionally also include a numbered heading for each question.
- **Global progress tracking** - Tracks answered/correct status across all quizzes on the page. Progress trackers in the sidebar (desktop) or top of page (mobile) show progress.
- **LocalStorage persistence** - Progress automatically saved per-page and restored on reload
- **Reset button** - Ability to clear localStorage and current answers, to start again
- **Results panel** - Add a placeholder to the page to show results and fire confetti when the quiz is complete 🎉
- _and many more small additions.._

## Pre-1.0.0

[Previous versions 0.1 to 0.41](https://pypi.org/project/mkdocs-quiz/#history) were all written by the original plugin author [Sebastian Jörz](https://github.com/skyface753).
See original GitHub history for details: https://github.com/skyface753/mkdocs-quiz/
