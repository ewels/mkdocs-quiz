"""Tests for per-answer feedback rendering in multiple-choice quizzes."""

from __future__ import annotations

import re

import pytest
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from mkdocs_quiz.plugin import MkDocsQuizPlugin


def _strip_source_comments(html: str) -> str:
    """Remove <!-- mkdocs-quiz-source ... --> comments from HTML."""
    return re.sub(r"<!-- mkdocs-quiz-source\n.*?\n-->", "", html, flags=re.DOTALL)


def _strip_injected_assets(html: str) -> str:
    """Remove inline <script> and <style> tags from HTML for clean attribute counting."""
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    return html


def make_plugin() -> MkDocsQuizPlugin:
    plugin = MkDocsQuizPlugin()
    plugin.config = {
        "enabled_by_default": True,
        "auto_number": False,
        "show_correct": True,
        "auto_submit": True,
        "disable_after_submit": True,
    }
    return plugin


def make_page(mock_config: MkDocsConfig) -> Page:
    from mkdocs.structure.files import File

    file = File(path="test.md", src_dir="docs", dest_dir="site", use_directory_urls=True)
    page = Page(None, file, mock_config)
    page.meta = {}
    return page


def make_files() -> Files:
    return Files([])


def test_per_answer_feedback_rendering() -> None:
    """Test basic per-answer feedback rendering."""
    plugin = make_plugin()
    mock_config = MkDocsConfig()
    page = make_page(mock_config)
    files = make_files()

    markdown = """
<quiz>
What number is shown?
- [x] 8
  > Correct!
- [ ] 6
  > No, that is wrong.
</quiz>
"""

    md_result = plugin.on_page_markdown(markdown, page, mock_config)
    html_result = plugin.on_page_content(md_result, page=page, config=mock_config, files=files)

    assert html_result is not None
    assert 'class="answer-feedback' in html_result
    assert "Correct!" in html_result
    assert "No, that is wrong." in html_result


def test_feedback_blank_line_raises_error() -> None:
    """Test that blank lines between answer and feedback raise a build error."""
    plugin = make_plugin()
    mock_config = MkDocsConfig()
    page = make_page(mock_config)
    files = make_files()

    markdown = """
<quiz>
Question?
- [x] Correct answer

  > This feedback won't be collected
- [ ] Wrong answer
</quiz>
"""

    md_result = plugin.on_page_markdown(markdown, page, mock_config)
    with pytest.raises(ValueError, match="Orphaned feedback line"):
        plugin.on_page_content(md_result, page=page, config=mock_config, files=files)


def test_multiple_feedback_lines() -> None:
    """Test that multiple consecutive feedback lines are collected."""
    plugin = make_plugin()
    mock_config = MkDocsConfig()
    page = make_page(mock_config)
    files = make_files()

    markdown = """
<quiz>
Question?
- [x] Right
  > Line 1
  > Line 2
- [ ] Wrong
</quiz>
"""

    md_result = plugin.on_page_markdown(markdown, page, mock_config)
    html_result = plugin.on_page_content(md_result, page=page, config=mock_config, files=files)

    assert html_result is not None
    assert "Line 1" in html_result
    assert "Line 2" in html_result


def test_mixed_feedback_and_no_feedback() -> None:
    """Test quiz with some answers having feedback and others without."""
    plugin = make_plugin()
    mock_config = MkDocsConfig()
    page = make_page(mock_config)
    files = make_files()

    markdown = """
<quiz>
Question?
- [x] Correct with feedback
  > Great job!
- [ ] Wrong without feedback
- [x] Another correct
  > Well done!
</quiz>
"""

    md_result = plugin.on_page_markdown(markdown, page, mock_config)
    html_result = plugin.on_page_content(md_result, page=page, config=mock_config, files=files)

    assert html_result is not None
    assert "Great job!" in html_result
    assert "Well done!" in html_result
    clean_html = _strip_injected_assets(html_result)
    assert clean_html.count('class="answer-feedback') == 2


def test_blockquote_after_last_answer_becomes_content() -> None:
    """Test that a blockquote after a blank line following the last answer becomes content."""
    plugin = make_plugin()
    mock_config = MkDocsConfig()
    page = make_page(mock_config)
    files = make_files()

    markdown = """
<quiz>
Question?
- [x] Correct answer
- [ ] Wrong answer

> This should be content
</quiz>
"""

    md_result = plugin.on_page_markdown(markdown, page, mock_config)
    html_result = plugin.on_page_content(md_result, page=page, config=mock_config, files=files)

    assert html_result is not None
    rendered_html = _strip_source_comments(html_result)
    # The blockquote should appear in the content section, not as answer feedback
    assert "This should be content" in rendered_html
    assert 'class="answer-feedback' not in rendered_html
    # It should be in a content section (blockquote rendered)
    assert "<blockquote>" in rendered_html
