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

    # Process markdown and convert to HTML
    md_result = plugin.on_page_markdown(markdown, page, mock_config)
    html_result = plugin.on_page_content(md_result, page=page, config=mock_config, files=files)

    assert html_result is not None
    # Expect two inputs
    assert 'id="quiz-0-0"' in html_result
    assert 'id="quiz-0-1"' in html_result

    # Expect per-answer feedback divs present with supplied text
    assert 'class="answer-feedback' in html_result
    assert "Correct!" in html_result
    assert "No, that is wrong." in html_result
