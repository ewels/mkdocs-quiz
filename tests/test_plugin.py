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
question: What is 2+2?
answer-correct: 4
answer: 3
answer: 5
content:
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
question: Which are even numbers?
answer-correct: 2
answer: 3
answer-correct: 4
content:
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
question: First quiz?
answer-correct: Yes
answer: No
content:
<p>First content</p>
<?/quiz?>

Some text between quizzes.

<?quiz?>
question: Second quiz?
answer-correct: Yes
answer: No
content:
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
question: Which is <strong>bold</strong>?
answer-correct: <code>Code</code>
answer: Plain text
content:
<p>HTML works!</p>
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    assert "<strong>bold</strong>" in result
    assert "<code>Code</code>" in result


def test_quiz_without_content_section(plugin, mock_page, mock_config):
    """Test that content: section is optional."""
    markdown = """
<?quiz?>
question: What is 2+2?
answer-correct: 4
answer: 3
answer: 5
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    assert "quiz" in result
    assert "What is 2+2?" in result
    assert 'type="radio"' in result
    assert "correct" in result
    # Content section should still be present but empty
    assert '<section class="content hidden"></section>' in result


def test_markdown_in_questions_and_answers(plugin, mock_page, mock_config):
    """Test that markdown is parsed in questions and answers."""
    markdown = """
<?quiz?>
question: What is **bold** text?
answer-correct: Text with `<strong>` tags
answer: Text with *emphasis*
answer: Normal text
content:
<p>Correct!</p>
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    # Check that markdown in question is converted
    assert "<strong>bold</strong>" in result
    # Check that markdown in answers is converted
    assert "<code>&lt;strong&gt;</code>" in result
    assert "<em>emphasis</em>" in result


def test_show_correct_option(plugin, mock_page, mock_config):
    """Test that show-correct option adds the data attribute."""
    markdown = """
<?quiz?>
question: What is 2+2?
show-correct: true
answer-correct: 4
answer: 3
answer: 5
content:
<p>Correct!</p>
<?/quiz?>
"""

    result = plugin.on_page_markdown(markdown, mock_page, mock_config)

    assert 'data-show-correct="true"' in result
    assert "What is 2+2?" in result


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
