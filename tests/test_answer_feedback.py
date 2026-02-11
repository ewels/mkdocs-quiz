"""Tests for per-answer feedback rendering in multiple-choice quizzes."""

from __future__ import annotations

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.pages import Page
from mkdocs.structure.files import Files

from mkdocs_quiz.plugin import MkDocsQuizPlugin


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


def test_per_answer_feedback_rendering():
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


def test_feedback_blank_line_stops_collection():
    """Test that blank lines between answer and feedback prevent feedback collection."""
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
    html_result = plugin.on_page_content(md_result, page=page, config=mock_config, files=files)

    assert html_result is not None
    assert "This feedback won't be collected" not in html_result


def test_multiple_feedback_lines():
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


def test_mixed_feedback_and_no_feedback():
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
    assert html_result.count('class="answer-feedback') == 2