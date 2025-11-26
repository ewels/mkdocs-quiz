"""Tests for the translation system."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File
from mkdocs.structure.pages import Page

from mkdocs_quiz.plugin import MkDocsQuizPlugin
from mkdocs_quiz.translations import TranslationManager


@pytest.fixture
def temp_po_file() -> Generator[Path, None, None]:
    """Create a temporary .po file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".po", delete=False) as f:
        po_content = """
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Submit"
msgstr "Soumettre"

msgid "Correct answer!"
msgstr "Bonne réponse!"

msgid "Question {n}"
msgstr "Question {n}"
"""
        f.write(po_content)
        f.flush()
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


def test_translation_manager_fallback_to_english() -> None:
    """Test that missing translations fall back to English key."""
    t = TranslationManager(language="en_US")

    # Should return the key itself if no translation exists
    assert t.get("Non-existent key") == "Non-existent key"


def test_translation_manager_builtin_english() -> None:
    """Test loading built-in English translation."""
    t = TranslationManager(language="en_US")

    # Should load English translations
    assert t.get("Submit") == "Submit"
    assert t.get("Correct answer!") == "Correct answer!"


def test_translation_manager_builtin_french() -> None:
    """Test loading built-in French translation."""
    t = TranslationManager(language="fr_FR")

    # Should load French translations
    assert t.get("Submit") != "Submit"  # Should be translated
    assert "Soumettre" in t.get("Submit") or "Envoyer" in t.get("Submit")


def test_translation_manager_format_substitution() -> None:
    """Test format string substitution with placeholders."""
    t = TranslationManager(language="en_US")

    # Should substitute {n} placeholder
    assert t.get("Question {n}", n=5) == "Question 5"
    assert t.get("Question {n}", n=10) == "Question 10"


def test_translation_manager_custom_override(temp_po_file: Path) -> None:
    """Test custom translation overriding built-in."""
    t = TranslationManager(language="en_US", custom_path=temp_po_file)

    # Custom translation should override built-in
    assert t.get("Submit") == "Soumettre"
    assert t.get("Correct answer!") == "Bonne réponse!"


def test_translation_manager_missing_custom_file() -> None:
    """Test graceful handling when custom file doesn't exist."""
    non_existent = Path("/tmp/non_existent_translation.po")
    t = TranslationManager(language="en_US", custom_path=non_existent)

    # Should fall back to built-in English
    assert t.get("Submit") == "Submit"


def test_translation_manager_missing_language() -> None:
    """Test fallback when language doesn't exist."""
    t = TranslationManager(language="xx_XX")  # Non-existent language

    # Should fall back to English keys
    assert t.get("Submit") == "Submit"


def test_translation_manager_to_dict() -> None:
    """Test exporting translations as dictionary."""
    t = TranslationManager(language="en_US")

    trans_dict = t.to_dict()

    # Should be a dictionary
    assert isinstance(trans_dict, dict)
    # Should contain translations
    assert "Submit" in trans_dict
    # Should be a copy (modifying shouldn't affect original)
    trans_dict["Submit"] = "Modified"
    assert t.get("Submit") != "Modified"


def test_plugin_translation_injection(mock_config: MkDocsConfig) -> None:
    """Test that translations are injected into HTML."""
    plugin = MkDocsQuizPlugin()
    plugin.config = {
        "enabled_by_default": True,
        "auto_number": False,
        "show_correct": True,
        "auto_submit": True,
        "disable_after_submit": True,
        "language": "en_US",
        "custom_translations": {},
        "language_patterns": [],
    }

    # Create a mock page
    file = File(
        path="test.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page = Page(None, file, mock_config)
    page.meta = {}

    markdown = """
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
</quiz>
"""

    # Process markdown and content
    markdown_result = plugin.on_page_markdown(markdown, page, mock_config)
    html_result = plugin.on_page_content(markdown_result, page=page, config=mock_config, files=None)  # type: ignore[arg-type]

    assert html_result is not None
    # Should contain translation script
    assert "mkdocsQuizTranslations" in html_result
    # Should contain submit button text
    assert "Submit" in html_result


def test_plugin_per_page_language(mock_config: MkDocsConfig) -> None:
    """Test per-page language override."""
    plugin = MkDocsQuizPlugin()
    plugin.config = {
        "enabled_by_default": True,
        "auto_number": False,
        "show_correct": True,
        "auto_submit": True,
        "disable_after_submit": True,
        "language": "en_US",
        "custom_translations": {},
        "language_patterns": [],
    }

    # Create page with French language override
    file = File(
        path="test.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page = Page(None, file, mock_config)
    page.meta = {"quiz": {"language": "fr_FR"}}

    # Get translation manager for this page
    t = plugin._get_translation_manager(page, mock_config)

    # Should use French
    assert t.language == "fr_FR"


def test_plugin_pattern_matching(mock_config: MkDocsConfig) -> None:
    """Test language detection via pattern matching."""
    plugin = MkDocsQuizPlugin()
    plugin.config = {
        "enabled_by_default": True,
        "language": "en_US",
        "custom_translations": {},
        "language_patterns": [
            {"pattern": "fr/*", "language": "fr_FR"},
            {"pattern": "es/*", "language": "es_ES"},
        ],
    }

    # Create French page (matches pattern)
    file_fr = File(
        path="fr/index.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page_fr = Page(None, file_fr, mock_config)
    page_fr.meta = {}

    t_fr = plugin._get_translation_manager(page_fr, mock_config)
    assert t_fr.language == "fr_FR"

    # Create Spanish page (matches pattern)
    file_es = File(
        path="es/getting-started.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page_es = Page(None, file_es, mock_config)
    page_es.meta = {}

    t_es = plugin._get_translation_manager(page_es, mock_config)
    assert t_es.language == "es_ES"

    # Create English page (no pattern match, uses default)
    file_en = File(
        path="index.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page_en = Page(None, file_en, mock_config)
    page_en.meta = {}

    t_en = plugin._get_translation_manager(page_en, mock_config)
    assert t_en.language == "en_US"


def test_plugin_language_resolution_order(mock_config: MkDocsConfig) -> None:
    """Test language resolution priority: page > pattern > global."""
    plugin = MkDocsQuizPlugin()
    plugin.config = {
        "language": "en_US",
        "language_patterns": [
            {"pattern": "fr/**/*", "language": "fr_FR"},
        ],
        "custom_translations": {},
    }

    # Page in fr/ directory with explicit language override
    file = File(
        path="fr/test.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page = Page(None, file, mock_config)
    page.meta = {"quiz": {"language": "es_ES"}}  # Override to Spanish

    t = plugin._get_translation_manager(page, mock_config)

    # Page frontmatter should win over pattern and global
    assert t.language == "es_ES"


def test_translation_with_multiple_quizzes(mock_config: MkDocsConfig) -> None:
    """Test translations work correctly with multiple quizzes."""
    plugin = MkDocsQuizPlugin()
    plugin.config = {
        "enabled_by_default": True,
        "auto_number": True,
        "show_correct": True,
        "auto_submit": True,
        "disable_after_submit": True,
        "language": "en_US",
        "custom_translations": {},
        "language_patterns": [],
    }

    file = File(
        path="test.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page = Page(None, file, mock_config)
    page.meta = {}

    markdown = """
<quiz>
First question?
- [x] Yes
- [ ] No
</quiz>

<quiz>
Second question?
- [x] Correct
- [ ] Wrong
</quiz>
"""

    markdown_result = plugin.on_page_markdown(markdown, page, mock_config)
    html_result = plugin.on_page_content(markdown_result, page=page, config=mock_config, files=None)  # type: ignore[arg-type]

    assert html_result is not None
    # Should have auto-numbered questions
    assert "Question 1" in html_result
    assert "Question 2" in html_result


def test_translation_format_error_propagates() -> None:
    """Test that format errors propagate (no defensive catching)."""
    t = TranslationManager(language="en_US")

    # Create a translation with placeholder, call format with wrong parameter
    # This should raise KeyError since we removed defensive exception handling
    t.translations["Test {value}"] = "Test {value}"

    with pytest.raises(KeyError):
        t.get("Test {value}", wrong_param=5)  # Wrong parameter name


def test_custom_translation_malformed_raises() -> None:
    """Test that malformed .po files raise errors (no defensive catching)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".po", delete=False) as f:
        # Write invalid .po content
        f.write("this is not valid .po format at all!")
        f.flush()
        temp_path = Path(f.name)

    try:
        # Should raise an error from polib (no defensive exception handling)
        # We don't catch the specific exception type because we want any error to propagate
        TranslationManager(language="en_US", custom_path=temp_path)
        # If we get here, the test should fail
        pytest.fail("Expected TranslationManager to raise an error for malformed .po file")
    except Exception:
        # This is expected - malformed files should raise errors
        pass
    finally:
        temp_path.unlink()


def test_translated_button_text_in_html(mock_config: MkDocsConfig) -> None:
    """Test that button text is properly translated in generated HTML."""
    plugin = MkDocsQuizPlugin()
    plugin.config = {
        "enabled_by_default": True,
        "auto_number": False,
        "show_correct": True,
        "auto_submit": False,  # Show submit button
        "disable_after_submit": True,
        "language": "en_US",
        "custom_translations": {},
        "language_patterns": [],
    }

    file = File(
        path="test.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page = Page(None, file, mock_config)
    page.meta = {}

    markdown = """
<quiz>
Test?
- [x] A
- [x] B
</quiz>
"""

    markdown_result = plugin.on_page_markdown(markdown, page, mock_config)
    html_result = plugin.on_page_content(markdown_result, page=page, config=mock_config, files=None)  # type: ignore[arg-type]

    assert html_result is not None
    # Should contain Submit button (multiple choice quiz)
    assert ">Submit<" in html_result


def test_empty_translation_falls_back() -> None:
    """Test that empty translations fall back to English."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".po", delete=False) as f:
        po_content = """
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Submit"
msgstr ""

msgid "Correct answer!"
msgstr "Translated!"
"""
        f.write(po_content)
        f.flush()
        temp_path = Path(f.name)

    try:
        t = TranslationManager(language="en_US", custom_path=temp_path)

        # Empty msgstr should fall back to English key
        assert t.get("Submit") == "Submit"
        # Non-empty msgstr should use translation
        assert t.get("Correct answer!") == "Translated!"
    finally:
        temp_path.unlink()


@pytest.fixture
def mock_config() -> MkDocsConfig:
    """Create a mock config object."""
    return MkDocsConfig()
