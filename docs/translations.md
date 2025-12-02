---
quiz:
  language: fr
  auto_number: true
---

# Translations

MkDocs Quiz supports internationalization (i18n) with multiple languages for all user-facing text. Language codes follow [MkDocs Material conventions](https://squidfunk.github.io/mkdocs-material/setup/changing-the-language/): 2-letter ISO 639-1 codes (e.g., `fr`, `de`) with hyphens for regional variants (e.g., `pt-BR`, `zh-TW`).

For example, this page uses French:

!!! info

    <!-- mkdocs-quiz intro -->

<quiz>
Quelles sont les meilleures pâtisseries ?
- [ ] Brioches à la cannelle
- [x] Croissant
- [x] Pain au chocolat
- [ ] Brioches glacées
</quiz>

<!-- mkdocs-quiz results -->

## Built-in Languages

- **English** (`en`) - Default
- **Chinese (Simplified)** (`zh`)
- **Esperanto** (`eo`)
- **French** (`fr`)
- **German** (`de`)
- **Hindi** (`hi`)
- **Indonesian** (`id`)
- **Japanese** (`ja`)
- **Korean** (`ko`)
- **Norwegian** (`no`)
- **Portuguese (Brazilian)** (`pt-BR`)
- **Spanish** (`es`)
- **Swedish** (`sv`)

!!! note "Want to add a language?"

    See [Contributing Translations](contributing-translations.md) to add a new language.

## Configuration

### Language Resolution Order

MkDocs Quiz automatically detects the language (later overrides earlier):

1. **Default**: `en`
2. **Theme language**: `theme.language`
3. **Language selector**: Active language from `extra.alternate` (Material multi-language sites)
4. **Plugin config**: `mkdocs_quiz.language`
5. **Pattern matching**: `mkdocs_quiz.language_patterns`
6. **Page frontmatter**: `quiz.language` (highest priority)

If using Material's theme language or language selector, MkDocs Quiz automatically uses the correct language.

### Use Theme Language

```yaml
theme:
  name: material
  language: fr # MkDocs Quiz uses this automatically

plugins:
  - mkdocs_quiz # No language config needed
```

### Use Theme Language Selector

See the [mkdocs material docs](https://squidfunk.github.io/mkdocs-material/setup/changing-the-language/#site-language-selector) for more information.

```yaml
theme:
  name: material

extra:
  alternate: # MkDocs Quiz uses this automatically
    - name: English
      link: /en/
      lang: en
    - name: Français
      link: /fr/
      lang: fr

plugins:
  - mkdocs_quiz # No language config needed
```

### Set Global Language via Plugin Config

```yaml
plugins:
  - mkdocs_quiz:
      language: fr
```

### Set Plugin Language by Path

```yaml
plugins:
  - mkdocs_quiz:
      language_patterns:
        - pattern: "fr/**/*"
          language: fr
        - pattern: "pt/**/*"
          language: pt-BR
```

### Set Per-Page Language

```yaml
---
quiz:
  language: fr
---
```

## Custom Translations

### Add a New Language

1. **Create translation file:**

```bash
mkdocs-quiz translations init ja
```

This creates `ja.po` with all strings to translate.

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
      language: ja
      custom_translations:
        ja: translations/ja.po
```

### Override Built-in Text

```yaml
plugins:
  - mkdocs_quiz:
      language: en
      custom_translations:
        en: translations/custom.po
```

```po
# translations/custom.po
msgid "Submit"
msgstr "Check Answer"

msgid "Outstanding! You aced it!"
msgstr "Perfect score! You're a quiz master!"
```

## Troubleshooting

### Translation not loading

1. Check file path in `custom_translations` is relative to `mkdocs.yml`
2. Verify `.po` file format is valid
3. Run `mkdocs serve -v` for verbose output

### English text appears

1. Verify language code is correct
2. Check pattern matching if using `language_patterns`
3. Ensure all strings in `.po` file have translations (non-empty `msgstr`)

### Special characters not displaying

Ensure your `.po` file has UTF-8 encoding:

```po
"Content-Type: text/plain; charset=UTF-8\n"
```

## Technical Details

- **Format:** Standard gettext `.po` files compatible with [Poedit](https://poedit.net/), [Weblate](https://weblate.org/), [Crowdin](https://crowdin.com/)
- **Loading:** Translations load at build time (no runtime overhead)
- **Fallback:** Missing translations fall back to English
- **JavaScript:** Translations embedded as JSON in generated HTML

## Contributing

Want to add support for your language? See [Contributing Translations](contributing-translations.md) for the complete guide.
