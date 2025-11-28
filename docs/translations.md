---
quiz:
  language: fr_FR
  auto_number: true
---

# Translations

MkDocs Quiz supports multiple languages for all user-facing text (buttons, messages, progress tracking, etc.). This page is configured to render quizzes in French:

!!! info

    <!-- mkdocs-quiz intro -->

<quiz>
Quelles sont les meilleures pâtisseries ?
- [ ] Brioches à la cannelle
- [x] Croissant
- [x] Pain au chocolat
- [ ] Brioches glacées
</quiz>

<!-- mkdocs-quiz results -->

## Built-in Languages

- **English** (`en_US`) - Default
- **French** (`fr_FR`)

!!! note "Want to add a language?"
See the [Contributing Translations](contributing-translations.md) guide to add a new language to the plugin.

## Basic Configuration

### Set Global Language

```yaml
plugins:
  - mkdocs_quiz:
      language: fr_FR
```

### Set Per-Page Language

Override the language for specific pages:

```md
---
quiz:
  language: fr_FR
---

# Ma Page de Quiz

!!! info

    <!-- mkdocs-quiz intro -->

<quiz>
Quelles sont les meilleures pâtisseries ?
- [ ] Brioches à la cannelle
- [x] Croissant
- [x] Pain au chocolat
- [ ] Brioches glacées
</quiz>

<!-- mkdocs-quiz results -->
```

### Set Language by Path

Useful for multilingual sites organized by directory:

```yaml
plugins:
  - mkdocs_quiz:
      language: en_US # Default
      language_patterns:
        - pattern: "fr/**/*"
          language: fr_FR
        - pattern: "es/**/*"
          language: es_ES
```

With this configuration:

- Files in `docs/fr/` automatically use French
- Files in `docs/es/` automatically use Spanish
- All others use English

**Language Resolution Order:**

1. Page frontmatter (`quiz.language`)
2. Pattern matching (`language_patterns`)
3. Global config (`language`)
4. Default (`en_US`)

## Custom Translations

You can add new languages or customize existing ones.

### Add a New Language

1. **Create translation file:**

```bash
mkdocs-quiz translations init ja_JP
```

This creates `ja_JP.po` with all strings to translate.

2. **Translate the strings:**

Edit the `.po` file using a text editor or [Poedit](https://poedit.net/):

```po
msgid "Submit"
msgstr "送信"

msgid "Correct answer!"
msgstr "正解！"
```

3. **Configure it:**

```yaml
plugins:
  - mkdocs_quiz:
      language: ja_JP
      custom_translations:
        ja_JP: translations/ja_JP.po
```

### Override Built-in Text

Customize specific strings without changing the language:

```yaml
plugins:
  - mkdocs_quiz:
      language: en_US
      custom_translations:
        en_US: translations/custom.po
```

```po
# translations/custom.po
msgid "Submit"
msgstr "Check Answer"

msgid "Outstanding! You aced it!"
msgstr "Perfect score! You're a quiz master!"
```

## Examples

### Multilingual Documentation Site

```yaml
plugins:
  - mkdocs_quiz:
      language_patterns:
        - pattern: "en/**/*"
          language: en_US
        - pattern: "fr/**/*"
          language: fr_FR
        - pattern: "es/**/*"
          language: es_ES
```

Directory structure:

```
docs/
  en/
    getting-started.md  # English
  fr/
    demarrage.md        # French
  es/
    comenzar.md         # Spanish
```

### Custom Branding

Override messages to match your brand voice:

```yaml
# mkdocs.yml
plugins:
  - mkdocs_quiz:
      custom_translations:
        en_US: translations/brand.po
```

```po
# translations/brand.po
msgid "Outstanding! You aced it!"
msgstr "Excellent! You're ready for the next level!"

msgid "Try Again"
msgstr "Give it another shot"
```

## Translatable Strings

All user-facing text can be translated:

**Buttons:** Submit, Try Again, Reset quiz, Reset

**Feedback:** Correct answer!, Incorrect answer., Incorrect answer. Please try again.

**Progress:** Quiz Progress, Answered:, Correct:, questions answered, correct

**Question Numbering:** Question {n}

**Results:** Quiz Complete!, Outstanding! You aced it!, Great job! You really know your stuff!, Good effort! Keep learning!, Not bad, but there's room for improvement!, Better luck next time! Keep trying!

**Prompts:** Are you sure you want to reset the quiz? This will clear your progress.

**Intro:** Quiz results are saved to your browser's local storage and will persist between sessions.

## Troubleshooting

### Translation not loading

1. Check the file path in `custom_translations` is relative to `mkdocs.yml`
2. Verify the `.po` file format is valid
3. Check language code matches (e.g., `fr_FR` not `fr`)
4. Run `mkdocs serve -v` for verbose output

### English text appears instead of translation

1. Verify language code is correct
2. Check pattern matching if using `language_patterns`
3. Ensure all strings in `.po` file have translations (non-empty `msgstr`)

### Special characters not displaying

Ensure your `.po` file has UTF-8 encoding:

```po
"Content-Type: text/plain; charset=UTF-8\n"
```

## Technical Details

- **Format:** Standard gettext `.po` files
- **Loading:** Translations load at build time (no runtime overhead)
- **Fallback:** Missing translations fall back to English
- **JavaScript:** Translations embedded as JSON in generated HTML

Translation files use the industry-standard gettext format, compatible with [Poedit](https://poedit.net/), [Weblate](https://weblate.org/), [Crowdin](https://crowdin.com/), and other translation tools.

## Contributing

Want to add support for your language? See [Contributing Translations](contributing-translations.md) for the complete guide.
