"""Tests for the MkDocs Quiz plugin."""

import pytest
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.pages import Page

from mkdocs_quiz.plugin import MkDocsQuizPlugin


@pytest.fixture
def plugin():
    """Create a plugin instance for testing."""
    return MkDocsQuizPlugin()


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


def test_plugin_initialization(plugin):
    """Test that the plugin initializes correctly."""
    assert plugin.enabled is True
    assert plugin.dirty is False


def test_on_startup(plugin):
    """Test the on_startup hook."""
    plugin.on_startup(command="serve", dirty=True)
    assert plugin.dirty is True


def test_disabled_page(plugin, mock_page, mock_config):
    """Test that quiz processing is disabled when page meta is set."""
    mock_page.meta["quiz"] = "disable"
    markdown = "<?quiz?>question: Test?<?/quiz?>"

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    assert result == markdown  # Should return unchanged


def test_single_choice_quiz(plugin, mock_page, mock_config):
    """Test processing a single choice quiz."""
    markdown = """
<?quiz?>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5

<p>Correct! 2+2 equals 4.</p>
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    assert "quiz" in result
    assert "What is 2+2?" in result
    assert 'type="radio"' in result
    assert "correct" in result


def test_multiple_choice_quiz(plugin, mock_page, mock_config):
    """Test processing a multiple choice quiz."""
    markdown = """
<?quiz?>
Which are even numbers?
- [x] 2
- [ ] 3
- [x] 4

<p>2 and 4 are even!</p>
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    assert "quiz" in result
    assert "Which are even numbers?" in result
    assert 'type="checkbox"' in result


def test_multiple_quizzes(plugin, mock_page, mock_config):
    """Test processing multiple quizzes on the same page."""
    markdown = """
<?quiz?>
First quiz?
- [x] Yes
- [ ] No

<p>First content</p>
<?/quiz?>

Some text between quizzes.

<?quiz?>
Second quiz?
- [x] Yes
- [ ] No

<p>Second content</p>
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

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
<?quiz?>
Which is <strong>bold</strong>?
- [x] <code>Code</code>
- [ ] Plain text

<p>HTML works!</p>
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    assert "<strong>bold</strong>" in result
    assert "<code>Code</code>" in result


def test_quiz_without_content_section(plugin, mock_page, mock_config):
    """Test that content section is optional."""
    markdown = """
<?quiz?>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    assert "quiz" in result
    assert "What is 2+2?" in result
    assert 'type="radio"' in result
    assert "correct" in result
    # Content section should be present but empty
    assert '<section class="content hidden"></section>' in result


def test_markdown_in_questions_and_answers(plugin, mock_page, mock_config):
    """Test that markdown is parsed in questions and answers."""
    markdown = """
<?quiz?>
What is **bold** text?
- [x] Text with `<strong>` tags
- [ ] Text with *emphasis*
- [ ] Normal text

<p>Correct!</p>
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    # Check that markdown in question is converted
    assert "<strong>bold</strong>" in result
    # Check that markdown in answers is converted
    assert "<code>&lt;strong&gt;</code>" in result
    assert "<em>emphasis</em>" in result


def test_show_correct_disabled(plugin, mock_page, mock_config):
    """Test that show-correct can be disabled (defaults to true)."""
    markdown = """
<?quiz?>
What is 2+2?
show-correct: false
- [x] 4
- [ ] 3
- [ ] 5

<p>Correct!</p>
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    # Should NOT have the data attribute when disabled
    assert 'data-show-correct="true"' not in result
    assert "What is 2+2?" in result


def test_auto_submit_disabled(plugin, mock_page, mock_config):
    """Test that auto-submit can be disabled (defaults to true)."""
    markdown = """
<?quiz?>
What is 2+2?
auto-submit: false
- [x] 4
- [ ] 3
- [ ] 5
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    # Should NOT have the data attribute when disabled
    assert 'data-auto-submit="true"' not in result
    assert "What is 2+2?" in result
    # Submit button SHOULD be present when auto-submit is disabled
    assert "Submit" in result


def test_opt_in_mode_enabled(mock_config):
    """Test that opt-in mode only processes when quiz: enable is set."""
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
    page.meta = {"quiz": "enable"}

    markdown = """
<?quiz?>
What is 2+2?
- [x] 4
- [ ] 3
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, page, mock_config)

    # Quiz should be processed
    assert "quiz" in result
    assert "What is 2+2?" in result


def test_opt_in_mode_not_enabled(mock_config):
    """Test that opt-in mode does not process when quiz: enable is not set."""
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
<?quiz?>
What is 2+2?
- [x] 4
- [ ] 3
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, page, mock_config)

    # Quiz should NOT be processed
    assert "<?quiz?>" in result


def test_quiz_header_ids(plugin, mock_page, mock_config):
    """Test that quiz headers have IDs with links."""
    markdown = """
<?quiz?>
First question?
- [x] Yes
- [ ] No
<?/quiz?>

<?quiz?>
Second question?
- [x] Yes
- [ ] No
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    # Check that both quiz headers have IDs
    assert 'id="quiz-0"' in result
    assert 'id="quiz-1"' in result
    # Check that header links are present
    assert 'href="#quiz-0"' in result
    assert 'href="#quiz-1"' in result


def test_invalid_quiz_format(plugin, mock_page, mock_config):
    """Test that invalid quiz format is handled gracefully."""
    markdown = """
<?quiz?>
This is not a valid quiz format
<?/quiz?>
"""

    # Should not raise an exception
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    # Original markdown should remain since quiz processing failed
    assert "<?quiz?>" in result
