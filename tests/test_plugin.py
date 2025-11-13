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
    """Test that invalid quiz format raises ValueError and crashes build."""
    markdown = """
<quiz>
This is not a valid quiz format
</quiz>
"""

    # Should raise ValueError (no answers found) and crash the build
    with pytest.raises(ValueError, match=r"Quiz must have at least one answer"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


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
    assert (
        "<!-- MKDOCS_QUIZ_PLACEHOLDER_0 -->" in markdown_result
    )  # Real quiz was converted to placeholder

    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)

    # The real quiz should be processed
    assert "What is 3+3?" in result
    assert 'type="radio"' in result
    assert 'id="quiz-0"' in result  # Only one quiz was processed


def test_xss_prevention_special_characters(plugin, mock_page, mock_config):
    """Test that special HTML characters in input values are properly escaped."""
    markdown = """
<quiz>
Test question?
- [x] Answer 1
- [ ] Answer 2
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # The value attribute should be escaped (our html.escape fix)
    # Values are numeric but we escape them anyway for defense-in-depth
    assert 'value="0"' in html_result
    assert 'value="1"' in html_result
    # Verify no script injection in values
    assert 'value="<script>"' not in html_result


def test_empty_question_validation(plugin, mock_page, mock_config):
    """Test that quizzes with empty questions raise ValueError and crash build."""
    markdown = """
<quiz>

- [x] Answer 1
- [ ] Answer 2
</quiz>
"""
    # Should raise ValueError and crash the build
    with pytest.raises(ValueError, match=r"Quiz must have a question"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_quiz_no_correct_answers(plugin, mock_page, mock_config):
    """Test that quizzes with no correct answers raise ValueError and crash build."""
    markdown = """
<quiz>
What is the answer?
- [ ] Wrong 1
- [ ] Wrong 2
</quiz>
"""
    # Should raise ValueError and crash the build
    with pytest.raises(ValueError, match=r"Quiz must have at least one correct answer"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_quiz_all_correct_answers(plugin, mock_page, mock_config):
    """Test that quizzes with all correct answers work properly."""
    markdown = """
<quiz>
Select all that apply:
- [x] Correct 1
- [x] Correct 2
- [x] Correct 3
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Should use checkboxes since multiple correct answers
    assert 'type="checkbox"' in html_result
    # All three inputs should have the correct attribute (without quotes, just the word "correct")
    assert html_result.count(" correct>") == 3  # All three have correct attribute


def test_results_div_generation(plugin, mock_page, mock_config):
    """Test that results div is properly generated and injected."""
    markdown = """
<quiz>
Question 1?
- [x] Yes
- [ ] No
</quiz>

<!-- mkdocs-quiz results -->
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Results div should be injected
    assert 'id="quiz-results"' in html_result
    assert "quiz-results-progress" in html_result
    assert "quiz-results-complete" in html_result
    assert "quiz-results-reset" in html_result


def test_intro_generation(plugin, mock_page, mock_config):
    """Test that intro text with reset button is generated."""
    markdown = """
<!-- mkdocs-quiz intro -->

<quiz>
Question 1?
- [x] Yes
- [ ] No
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Intro div should be injected
    assert 'class="quiz-intro"' in html_result
    assert "quiz-intro-reset" in html_result
    assert "local storage" in html_result.lower()


def test_confetti_config_injection(plugin, mock_page, mock_config):
    """Test that confetti configuration is properly injected."""
    plugin.config["confetti"] = True
    markdown = """
<quiz>
Question?
- [x] Yes
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Confetti library should be included (bundled locally)
    assert "JSConfetti" in html_result
    # Config should indicate confetti is enabled
    assert "mkdocsQuizConfig" in html_result
    assert "confetti: true" in html_result


def test_confetti_disabled(plugin, mock_page, mock_config):
    """Test that confetti can be disabled."""
    plugin.config["confetti"] = False
    markdown = """
<quiz>
Question?
- [x] Yes
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Config should indicate confetti is disabled
    assert "mkdocsQuizConfig" in html_result
    assert "confetti: false" in html_result
    # Note: The confetti library is bundled and included, but won't be initialized
    # when confetti config is false


def test_material_theme_integration(plugin):
    """Test that Material theme template overrides are added."""
    from unittest.mock import Mock

    from jinja2 import ChoiceLoader, DictLoader, Environment
    from mkdocs.config.defaults import MkDocsConfig

    # Create a mock environment
    env = Environment(loader=DictLoader({}))

    # Create proper config with mocked Material theme
    config = MkDocsConfig()
    mock_theme = Mock()
    mock_theme.name = "material"
    config["theme"] = mock_theme

    # Call on_env
    result_env = plugin.on_env(env, config, None)

    # Should add our template loader
    assert result_env is not None
    assert isinstance(result_env.loader, ChoiceLoader)  # ChoiceLoader was added


def test_show_progress_config(plugin, mock_page, mock_config):
    """Test that show_progress configuration works."""
    plugin.config["show_progress"] = False
    markdown = """
<quiz>
Question?
- [x] Yes
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Config should indicate progress is disabled
    assert "mkdocsQuizConfig" in html_result
    assert "showProgress: false" in html_result


def test_auto_number_config(plugin, mock_page, mock_config):
    """Test that auto_number configuration generates proper elements."""
    plugin.config["auto_number"] = True
    mock_page.meta["quiz"] = {"auto_number": True}

    markdown = """
<quiz>
First question?
- [x] Yes
</quiz>

<quiz>
Second question?
- [x] Yes
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Should have question numbers
    assert "Question 1" in html_result
    assert "Question 2" in html_result
    assert "quiz-auto-number" in html_result


def test_special_characters_in_answers(plugin, mock_page, mock_config):
    """Test that quotes and special chars in answers work correctly."""
    markdown = """
<quiz>
What's the answer?
- [x] It's "correct" & <valid>
- [ ] Wrong answer
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Should process without errors
    assert 'type="radio"' in html_result
    # Markdown converter should handle escaping
    assert "correct" in html_result


def test_code_in_quiz_content(plugin, mock_page, mock_config):
    """Test that code blocks in quiz content section work."""
    markdown = """
<quiz>
What is this?
- [x] Python code
- [ ] Java code

Here's the code:
```python
def hello():
    print("world")
```
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Code block should be present in content section (with syntax highlighting)
    assert "hello" in html_result  # Function name should be there
    assert "codehilite" in html_result  # Syntax highlighting div
    assert '<section class="content hidden">' in html_result


def test_multiple_quizzes_same_question(plugin, mock_page, mock_config):
    """Test that multiple quizzes with identical questions get unique IDs."""
    markdown = """
<quiz>
Same question?
- [x] Yes
</quiz>

<quiz>
Same question?
- [x] Yes
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Each quiz should have unique ID
    assert 'id="quiz-0"' in html_result
    assert 'id="quiz-1"' in html_result
    assert 'id="quiz-0-0"' in html_result  # First answer of first quiz
    assert 'id="quiz-1-0"' in html_result  # First answer of second quiz


def test_quiz_with_only_answers_no_question(plugin, mock_page, mock_config):
    """Test that quiz with missing question raises ValueError and crashes build."""
    markdown = """
<quiz>
- [x] Answer 1
- [ ] Answer 2
</quiz>
"""
    # Should raise ValueError and crash the build
    with pytest.raises(ValueError, match=r"Quiz must have a question"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_capital_x_in_checkbox(plugin, mock_page, mock_config):
    """Test that capital X in checkboxes is recognized as correct."""
    markdown = """
<quiz>
Capital X test?
- [X] Correct with capital X
- [ ] Wrong
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Should recognize capital X as correct
    assert "correct" in html_result
    assert 'type="radio"' in html_result


def test_malformed_checkbox_y_raises_error(plugin, mock_page, mock_config):
    """Test that malformed checkbox with 'y' raises ValueError and crashes build."""
    markdown = """
<quiz>
Question?
- [y] This should raise an error
- [x] Correct answer
- [ ] Wrong
</quiz>
"""
    # Should raise ValueError and prevent build from completing
    with pytest.raises(
        ValueError,
        match=r"Invalid checkbox format.*\[y\].*Only.*\[x\].*\[X\].*\[ \].*\[\].*allowed",
    ):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_malformed_checkbox_checkmark_raises_error(plugin, mock_page, mock_config):
    """Test that checkmark symbol raises ValueError."""
    markdown = """
<quiz>
Question?
- [✓] Check mark should raise error
- [x] Correct
</quiz>
"""
    with pytest.raises(ValueError, match=r"Invalid checkbox format.*\[✓\]"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_malformed_checkbox_star_raises_error(plugin, mock_page, mock_config):
    """Test that star symbol raises ValueError."""
    markdown = """
<quiz>
Question?
- [*] Star should raise error
- [x] Correct
</quiz>
"""
    with pytest.raises(ValueError, match=r"Invalid checkbox format.*\[\*\]"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_malformed_checkbox_lowercase_o_raises_error(plugin, mock_page, mock_config):
    """Test that lowercase 'o' raises ValueError."""
    markdown = """
<quiz>
Question?
- [o] Should raise error
- [x] Correct
</quiz>
"""
    with pytest.raises(ValueError, match=r"Invalid checkbox format.*\[o\]"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_all_valid_checkbox_formats(plugin, mock_page, mock_config):
    """Test that all valid checkbox formats are accepted: [x], [X], [ ], []."""
    markdown = """
<quiz>
Which are valid?
- [x] Lowercase x (correct)
- [X] Uppercase X (correct)
- [ ] Space (incorrect)
- [] Empty (incorrect)
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Should process successfully with all 4 formats
    assert 'type="checkbox"' in html_result  # Multiple correct = checkboxes
    assert html_result.count('type="checkbox"') == 4
    # Both [x] and [X] should be marked as correct
    assert html_result.count(" correct>") == 2


def test_very_long_quiz_content(plugin, mock_page, mock_config):
    """Test that very long quiz content is handled properly (stress test)."""
    # Generate a long question and many answers
    long_question = "Question? " + ("This is a very long question. " * 50)
    # Use text without hyphens to avoid confusion with list items
    answers = "\n".join(
        [
            f"- [{'x' if i == 0 else ' '}] Answer {i} with lots of words " + ("word " * 20)
            for i in range(20)
        ]
    )
    long_content = "\n\nContent section with lots of text.\n\n" + ("This is content. " * 100)

    markdown = f"""
<quiz>
{long_question}
{answers}
{long_content}
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Should process successfully despite large size
    assert 'type="radio"' in html_result
    # At least 20 radio buttons (exact count may vary based on parsing)
    assert html_result.count('type="radio"') >= 20
    assert "correct" in html_result
    assert "Content section with lots of text" in html_result


def test_special_characters_in_question(plugin, mock_page, mock_config):
    """Test special HTML characters in question text."""
    markdown = """
<quiz>
What does <div class="test"> & "quotes" do?
- [x] It's HTML & markup
- [ ] Nothing
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Markdown should escape HTML in question
    # The exact escaping depends on markdown processor, but should be safe
    assert 'type="radio"' in html_result
    assert "quiz-question" in html_result


def test_quiz_with_only_empty_checkboxes(plugin, mock_page, mock_config):
    """Test quiz with all empty checkboxes raises ValueError and crashes build."""
    markdown = """
<quiz>
Question?
- [ ] Answer 1
- [ ] Answer 2
- [ ] Answer 3
</quiz>
"""
    # Should raise ValueError (no correct answers) and crash the build
    with pytest.raises(ValueError, match=r"Quiz must have at least one correct answer"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_nested_lists_in_quiz_content(plugin, mock_page, mock_config):
    """Test nested lists in quiz content section."""
    markdown = """
<quiz>
What is this?
- [x] A list
- [ ] Not a list

Content with list:

- Item 1
- Item 2
- Item 3
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Should process successfully
    assert 'type="radio"' in html_result
    # Content section should have the list converted to HTML
    assert "Item 1" in html_result
    assert "Item 2" in html_result


def test_markdown_formatting_in_question(plugin, mock_page, mock_config):
    """Test markdown formatting (bold, italic, code) in question."""
    markdown = """
<quiz>
What does **bold** and *italic* and `code` mean?
- [x] Markdown formatting
- [ ] Nothing
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)

    # Should process markdown in question
    assert "<strong>bold</strong>" in html_result
    assert "<em>italic</em>" in html_result
    assert "<code>code</code>" in html_result
