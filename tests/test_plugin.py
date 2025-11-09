"""Tests for the MkDocs Quiz plugin."""

import pytest
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.pages import Page

from mkdocs_quiz.plugin import MkDocsQuizPlugin


@pytest.fixture
def plugin():
    """Create a plugin instance for testing."""
    plugin = MkDocsQuizPlugin()
    # Initialize config with default values to match plugin behavior
    plugin.config = {
        "enabled_by_default": True,
        "auto_number": False,
        "show_correct": True,
        "auto_submit": True,
        "disable_after_submit": True,
    }
    return plugin


@pytest.fixture
def mock_config():
    """Create a mock config object."""
    return MkDocsConfig()


@pytest.fixture
def mock_page(mock_config):
    """Create a mock page object."""
    from mkdocs.structure.files import File

    file = File(
        path="test.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page = Page(None, file, mock_config)
    page.meta = {}
    return page


def test_disabled_page(plugin, mock_page, mock_config):
    """Test that quiz processing is disabled when page meta is set."""
    mock_page.meta["quiz"] = {"enabled": False}
    markdown = """
<quiz>
Test question?
- [x] Yes
- [ ] No
</quiz>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    assert result == markdown  # Should return unchanged


def test_single_choice_quiz(plugin, mock_page, mock_config):
    """Test processing a single choice quiz."""
    markdown = """
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5

<p>Correct! 2+2 equals 4.</p>
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    assert "quiz" in result
    assert "What is 2+2?" in result
    assert 'type="radio"' in result
    assert "correct" in result
    # Single choice with auto-submit (default) should NOT have a submit button element
    assert '<button type="submit"' not in result


def test_multiple_choice_quiz(plugin, mock_page, mock_config):
    """Test processing a multiple choice quiz."""
    markdown = """
<quiz>
Which are even numbers?
- [x] 2
- [ ] 3
- [x] 4

<p>2 and 4 are even!</p>
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    assert "quiz" in result
    assert "Which are even numbers?" in result
    assert 'type="checkbox"' in result
    # Multiple choice should always have a submit button (even with auto-submit enabled by default)
    assert 'type="submit"' in result
    assert "Submit" in result


def test_multiple_quizzes(plugin, mock_page, mock_config):
    """Test processing multiple quizzes on the same page."""
    markdown = """
<quiz>
First quiz?
- [x] Yes
- [ ] No

<p>First content</p>
</quiz>

Some text between quizzes.

<quiz>
Second quiz?
- [x] Yes
- [ ] No

<p>Second content</p>
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    # Check both quizzes are present
    assert "First quiz?" in result
    assert "Second quiz?" in result
    # Check that we have inputs from both quizzes
    assert 'id="quiz-0-0"' in result
    assert 'id="quiz-0-1"' in result
    assert 'id="quiz-1-0"' in result
    assert 'id="quiz-1-1"' in result


def test_quiz_with_html_in_answers(plugin, mock_page, mock_config):
    """Test that HTML in answers is preserved."""
    markdown = """
<quiz>
Which is <strong>bold</strong>?
- [x] <code>Code</code>
- [ ] Plain text

<p>HTML works!</p>
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    assert "<strong>bold</strong>" in result
    assert "<code>Code</code>" in result


def test_quiz_without_content_section(plugin, mock_page, mock_config):
    """Test that content section is optional."""
    markdown = """
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    assert "quiz" in result
    assert "What is 2+2?" in result
    assert 'type="radio"' in result
    assert "correct" in result
    # Content section should be present but empty
    assert '<section class="content hidden"></section>' in result


def test_markdown_in_questions_and_answers(plugin, mock_page, mock_config):
    """Test that markdown is parsed in questions and answers."""
    markdown = """
<quiz>
What is **bold** text?
- [x] Text with `<strong>` tags
- [ ] Text with *emphasis*
- [ ] Normal text

<p>Correct!</p>
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    # Check that markdown in question is converted
    assert "<strong>bold</strong>" in result
    # Check that markdown in answers is converted
    assert "<code>&lt;strong&gt;</code>" in result
    assert "<em>emphasis</em>" in result


def test_show_correct_disabled(plugin, mock_page, mock_config):
    """Test that show-correct can be disabled via page frontmatter (defaults to true)."""
    mock_page.meta["quiz"] = {"show_correct": False}
    markdown = """
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5

<p>Correct!</p>
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    # Should NOT have the data attribute when disabled
    assert 'data-show-correct="true"' not in result
    assert "What is 2+2?" in result


def test_auto_submit_disabled(plugin, mock_page, mock_config):
    """Test that auto-submit can be disabled via page frontmatter (defaults to true)."""
    mock_page.meta["quiz"] = {"auto_submit": False}
    markdown = """
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    # Should NOT have the data attribute when disabled
    assert 'data-auto-submit="true"' not in result
    assert "What is 2+2?" in result
    # Submit button SHOULD be present when auto-submit is disabled
    assert "Submit" in result


def test_opt_in_mode_enabled(mock_config):
    """Test that opt-in mode only processes when quiz.enabled: true is set."""
    plugin = MkDocsQuizPlugin()
    plugin.config = {"enabled_by_default": False}

    from mkdocs.structure.files import File

    file = File(
        path="test.md",
        src_dir="docs",
        dest_dir="site",
        use_directory_urls=True,
    )
    page = Page(None, file, mock_config)
    page.meta = {"quiz": {"enabled": True}}

    markdown = """
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=page, config=mock_config, files=None)

    # Quiz should be processed
    assert "quiz" in result
    assert "What is 2+2?" in result


def test_opt_in_mode_not_enabled(mock_config):
    """Test that opt-in mode does not process when quiz.enabled is not set."""
    plugin = MkDocsQuizPlugin()
    plugin.config = {"enabled_by_default": False}

    from mkdocs.structure.files import File

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

    result = plugin.on_page_markdown(markdown, page, mock_config)

    # Quiz should NOT be processed
    assert "<quiz>" in result


def test_quiz_header_ids(plugin, mock_page, mock_config):
    """Test that quiz headers have IDs with links."""
    markdown = """
<quiz>
First question?
- [x] Yes
- [ ] No
</quiz>

<quiz>
Second question?
- [x] Yes
- [ ] No
</quiz>
"""

    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    # Check that both quiz headers have IDs
    assert 'id="quiz-0"' in result
    assert 'id="quiz-1"' in result
    # Check that header links are present
    assert 'href="#quiz-0"' in result
    assert 'href="#quiz-1"' in result


def test_invalid_quiz_format(plugin, mock_page, mock_config):
    """Test that invalid quiz format is handled gracefully."""
    markdown = """
<quiz>
This is not a valid quiz format
</quiz>
"""

    # Should not raise an exception
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    # Original markdown should remain since quiz processing failed
    assert "<quiz>" in result


def test_quiz_in_fenced_code_block(plugin, mock_page, mock_config):
    """Test that quiz tags inside fenced code blocks (``` or ~~~) are not processed."""
    markdown = """
Here's an example of quiz syntax with backticks:

```markdown
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
</quiz>
```

And with tildes:

~~~
<quiz>
What is 1+1?
- [x] 2
- [ ] 3
</quiz>
~~~

This is a real quiz:

<quiz>
What is 3+3?
- [x] 6
- [ ] 7
</quiz>
"""

    # Process markdown phase only - should mask code blocks
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    # The quizzes in the code blocks should remain unchanged
    assert "```markdown" in markdown_result
    assert "~~~" in markdown_result
    assert markdown_result.count("<quiz>") == 2  # Two in code blocks
    assert markdown_result.count("</quiz>") == 2  # Two in code blocks
    assert "<!-- MKDOCS_QUIZ_PLACEHOLDER_0 -->" in markdown_result  # Real quiz was converted to placeholder

    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    # The real quiz should be processed
    assert "What is 3+3?" in result
    assert 'type="radio"' in result
    assert 'id="quiz-0"' in result  # Only one quiz was processed
