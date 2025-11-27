# Contributing Translations

We welcome community translations! This guide explains how to contribute new languages or improve existing translations to mkdocs-quiz.

## Quick Start

To contribute a new language:

1. Fork the repository on GitHub
2. Create a translation file
3. Translate all strings
4. Verify completeness
5. Submit a pull request

## Creating a New Translation

### 1. Initialize Translation File

```bash
cd mkdocs-quiz
mkdocs-quiz translations init <language_code> -o mkdocs_quiz/locales/<language_code>.po
```

Examples:

```bash
mkdocs-quiz translations init es_ES -o mkdocs_quiz/locales/es_ES.po
mkdocs-quiz translations init de_DE -o mkdocs_quiz/locales/de_DE.po
mkdocs-quiz translations init ja_JP -o mkdocs_quiz/locales/ja_JP.po
```

**Note:** The `-o` flag places the file in the plugin's locales directory. Without it, the file is created in your current directory.

### 2. Translate Strings

Edit the `.po` file with your translations. You can use:

- **Text editor** - Any editor works with `.po` files
- **[Poedit](https://poedit.net/)** - Free GUI application for translation
- **Online tools** - [POEditor](https://poeditor.com/), [Weblate](https://weblate.org/), [Crowdin](https://crowdin.com/)

Example `.po` file structure:

```po
msgid "Submit"
msgstr "送信"  # Your translation here

msgid "Correct answer!"
msgstr "正解！"

msgid "Question {n}"
msgstr "質問 {n}"  # Preserve placeholders like {n}
```

### 3. Verify Completeness

Run the validation tool to ensure all strings are translated:

```bash
mkdocs-quiz translations check
```

Expected output:

```
Checking translation files...

Language: es_ES
  File: es_ES.po
  Total strings: 21
  Translated: 21 (100.0%)
  Untranslated: 0
  Fuzzy: 0
  Status: ✓ Complete
```

If you see untranslated or fuzzy entries, edit the `.po` file to complete them.

### 4. Test Locally

Test your translation by building the docs site:

```bash
pip install -e ".[docs]"
mkdocs serve
```

Configure a test page to use your language:

```yaml
---
quiz:
  language: es_ES
---
<quiz>
¿Pregunta de prueba?
- [x] Sí
- [ ] No
</quiz>
```

### 5. Submit Pull Request

Once your translation is complete and tested:

1. Commit your changes: `git add mkdocs_quiz/locales/<language>.po`
2. Create a descriptive commit message: `Add Spanish (es_ES) translation`
3. Push to your fork and open a pull request

## Translation Guidelines

### Tone and Style

- Use the formal/informal tone appropriate for your language and educational contexts
- Maintain consistency throughout the translation
- Keep the tone friendly and encouraging (especially for feedback messages)

### Technical Requirements

- **Preserve placeholders**: Keep `{n}` and other placeholders intact
  - ✅ `"Question {n}"` → `"Pregunta {n}"`
  - ❌ `"Question {n}"` → `"Pregunta número"`

- **Keep it concise**: Translations should fit UI elements
  - Buttons, labels, and short messages need to be brief
  - Longer messages (like intro text) have more flexibility

- **Character encoding**: Ensure your `.po` file uses UTF-8 encoding
  ```po
  "Content-Type: text/plain; charset=UTF-8\n"
  ```

## CLI Tools for Contributors

### `mkdocs-quiz translations check`

Validates translation completeness and detects issues:

```bash
mkdocs-quiz translations check
```

This command is also run automatically in pre-commit hooks.

### `mkdocs-quiz translations init`

Creates a new translation file from the template:

```bash
mkdocs-quiz translations init <language_code>
```

By default creates `{language}.po` in current directory. Use `-o` to specify output path.

### `mkdocs-quiz translations update`

Extracts strings from source code and updates all translation files:

```bash
mkdocs-quiz translations update
```

**Requires:** `pip install babel`

This command:

1. Scans Python source files for translatable strings
2. Extracts strings to `mkdocs_quiz/locales/mkdocs_quiz.pot` template
3. Updates all `.po` files with new strings
4. Marks obsolete strings for removal
5. Preserves existing translations

### Workflow for Adding New Strings

When new translatable text is added to the codebase:

1. Run `mkdocs-quiz translations update` to extract and sync strings
2. Translate new strings in each `.po` file
3. Remove obsolete entries (marked with `#~`)
4. Verify: `mkdocs-quiz translations check`

## Technical Details

### Translation File Format

MkDocs Quiz uses the standard **gettext `.po` format**:

- `.pot` files are templates (extracted from source code)
- `.po` files contain translations for specific languages
- Format is compatible with all standard translation tools

### How Translations Work

1. **Build Time**: Plugin loads translations when processing each page
2. **Resolution**: Language is determined from configuration and page context
3. **Fallback**: If a translation is missing, the English source string is used
4. **JavaScript Delivery**: Translations are embedded in generated HTML as JSON
5. **Runtime**: JavaScript uses translations for dynamic UI updates

### File Locations

```
mkdocs_quiz/
  locales/
    mkdocs_quiz.pot   # Template (source strings)
    fr_FR.po          # French
    es_ES.po          # Spanish (your contribution)
```

**Note:** English (`en_US`) does not have a `.po` file because English strings in the source code are used as the fallback.

## FAQ

### Do I need to translate the template (`.pot`) file?

No, only translate `.po` files. The `.pot` file is a template generated from source code.

### What if I want to update an existing translation?

Fork the repo, edit the existing `.po` file, test your changes, and submit a PR.

### Can I translate only part of the strings?

Incomplete translations are not accepted. All strings must be translated before submission.

### What language codes should I use?

Use standard locale codes: `{language}_{COUNTRY}` (e.g., `es_ES`, `pt_BR`, `zh_CN`).

### How do I handle plural forms?

MkDocs Quiz currently doesn't use plural forms in translatable strings. All messages use singular or count-based phrasing.

## Getting Help

If you have questions about contributing translations:

- Open an issue on GitHub: https://github.com/ewels/mkdocs-quiz/issues
- Check existing translations for reference
- Ask in your pull request if you're unsure about something

Thank you for helping make mkdocs-quiz accessible to more people! 🌍
