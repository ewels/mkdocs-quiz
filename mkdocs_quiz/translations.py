"""Translation management for mkdocs-quiz plugin."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import polib

log = logging.getLogger("mkdocs.plugins.mkdocs_quiz")


class TranslationManager:
    """Manage translations for mkdocs-quiz plugin.

    Loads translations from .po files with fallback to English source strings.
    English strings in the code are the single source of truth - if a translation
    is missing, the English key is used as-is.

    Loading order:
    1. Built-in .po files from plugin's locales/ directory
    2. User's custom .po files from their project (if configured)
    3. Falls back to English key if translation not found
    """

    def __init__(
        self,
        language: str = "en",
        custom_path: Path | None = None,
    ):
        """Initialize translation manager.

        Args:
            language: Language code (e.g., 'en', 'fr', 'pt-BR').
            custom_path: Optional path to user's custom .po file.
        """
        self.language = language
        self.custom_path = custom_path
        self.translations: dict[str, str] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """Load translations from .po files."""
        # 1. Load built-in translation from plugin's locales/ directory
        builtin_po = Path(__file__).parent / "locales" / f"{self.language}.po"
        if builtin_po.exists():
            self.translations = self._parse_po_file(builtin_po)
            log.debug(f"Loaded built-in translation: {self.language}")
        elif self.language != "en":
            log.warning(
                f"Built-in translation for '{self.language}' not found. "
                f"Available languages: en, fr, pt-BR. "
                f"Using English strings as fallback."
            )

        # 2. Merge custom translations from user's project (if provided)
        if self.custom_path:
            if self.custom_path.exists():
                custom_trans = self._parse_po_file(self.custom_path)
                self.translations.update(custom_trans)
                log.debug(f"Loaded custom translations from {self.custom_path}")
            else:
                log.warning(f"Custom translation file not found: {self.custom_path}")

    def _parse_po_file(self, po_path: Path) -> dict[str, str]:
        """Parse a .po file into a dictionary.

        Args:
            po_path: Path to the .po file.

        Returns:
            Dictionary mapping msgid (English source) to msgstr (translation).
            Only includes entries that have translations.
        """
        po = polib.pofile(str(po_path))
        translations = {}

        for entry in po:
            # Only include translated entries
            # If msgstr is empty, we'll fall back to the English key in get()
            if entry.msgstr:
                translations[entry.msgid] = entry.msgstr

        return translations

    def get(self, key: str, **kwargs: Any) -> str:
        """Get translated string with optional formatting.

        Args:
            key: Translation key (the English source string).
            **kwargs: Optional format parameters (e.g., n=5 for "Question {n}").

        Returns:
            Translated and formatted string.
        """
        text = self.translations.get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text

    def to_dict(self) -> dict[str, str]:
        """Export translations as dictionary for JavaScript.

        Returns:
            Copy of translations dictionary.
        """
        return self.translations.copy()
