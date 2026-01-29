"""Tests for the MkDocs Quiz plugin."""

from __future__ import annotations

import pytest
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.pages import Page

from mkdocs_quiz.plugin import MkDocsQuizPlugin


@pytest.fixture
def plugin() -> MkDocsQuizPlugin:
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
def mock_config() -> MkDocsConfig:
    """Create a mock config object."""
    return MkDocsConfig()


@pytest.fixture
def mock_page(mock_config: MkDocsConfig) -> Page:
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


def test_disabled_page(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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


def test_single_choice_quiz(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None
    assert "quiz" in result
    assert "What is 2+2?" in result
    assert 'type="radio"' in result
    assert "correct" in result
    # Single choice with auto-submit (default) should NOT have a submit button element
    assert '<button type="submit"' not in result


def test_multiple_choice_quiz(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    assert "quiz" in result
    assert "Which are even numbers?" in result
    assert 'type="checkbox"' in result
    # Multiple choice should always have a submit button (even with auto-submit enabled by default)
    assert 'type="submit"' in result
    assert "Submit" in result


def test_multiple_quizzes(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Check both quizzes are present
    assert "First quiz?" in result
    assert "Second quiz?" in result
    # Check that we have inputs from both quizzes
    assert 'id="quiz-0-0"' in result
    assert 'id="quiz-0-1"' in result
    assert 'id="quiz-1-0"' in result
    assert 'id="quiz-1-1"' in result


def test_quiz_with_html_in_answers(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    assert "<strong>bold</strong>" in result
    assert "<code>Code</code>" in result


def test_quiz_without_content_section(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    assert "quiz" in result
    assert "What is 2+2?" in result
    assert 'type="radio"' in result
    assert "correct" in result
    # Content section should be present but empty
    assert '<section class="content hidden"></section>' in result


def test_markdown_in_questions_and_answers(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Check that markdown in question is converted
    assert "<strong>bold</strong>" in result
    # Check that markdown in answers is converted
    assert "<code>&lt;strong&gt;</code>" in result
    assert "<em>emphasis</em>" in result


def test_show_correct_disabled(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should NOT have the data attribute when disabled
    assert 'data-show-correct="true"' not in result
    assert "What is 2+2?" in result


def test_auto_submit_disabled(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should NOT have the data attribute when disabled
    assert 'data-auto-submit="true"' not in result
    assert "What is 2+2?" in result
    # Submit button SHOULD be present when auto-submit is disabled
    assert "Submit" in result


def test_opt_in_mode_enabled(mock_config: MkDocsConfig) -> None:
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
    result = plugin.on_page_content(markdown_result, page=page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Quiz should be processed
    assert "quiz" in result
    assert "What is 2+2?" in result


def test_opt_in_mode_not_enabled(mock_config: MkDocsConfig) -> None:
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


def test_quiz_header_ids(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Check that both quiz headers have IDs
    assert 'id="quiz-0"' in result
    assert 'id="quiz-1"' in result
    # Check that header links are present
    assert 'href="#quiz-0"' in result
    assert 'href="#quiz-1"' in result


def test_invalid_quiz_format(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that invalid quiz format raises ValueError and crashes build."""
    markdown = """
<quiz>
This is not a valid quiz format
</quiz>
"""

    # Should raise ValueError (no answers found) and crash the build
    with pytest.raises(ValueError, match=r"Quiz must have at least one answer"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_quiz_in_fenced_code_block(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # The real quiz should be processed
    assert "What is 3+3?" in result
    assert 'type="radio"' in result
    assert 'id="quiz-0"' in result  # Only one quiz was processed


def test_xss_prevention_special_characters(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that special HTML characters in input values are properly escaped."""
    markdown = """
<quiz>
Test question?
- [x] Answer 1
- [ ] Answer 2
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # The value attribute should be escaped (our html.escape fix)
    # Values are numeric but we escape them anyway for defense-in-depth
    assert 'value="0"' in html_result
    assert 'value="1"' in html_result
    # Verify no script injection in values
    assert 'value="<script>"' not in html_result


def test_empty_question_validation(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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


def test_quiz_no_correct_answers(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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


def test_quiz_all_correct_answers(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should use checkboxes since multiple correct answers
    assert 'type="checkbox"' in html_result
    # All three inputs should have the correct attribute (without quotes, just the word "correct")
    assert html_result.count(" correct>") == 3  # All three have correct attribute


def test_results_div_generation(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Results div should be injected
    assert 'id="quiz-results"' in html_result
    assert "quiz-results-progress" in html_result
    assert "quiz-results-complete" in html_result
    assert "quiz-results-reset" in html_result


def test_intro_generation(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Intro div should be injected
    assert 'class="quiz-intro"' in html_result
    assert "quiz-intro-reset" in html_result
    assert "local storage" in html_result.lower()


def test_confetti_config_injection(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that confetti configuration is properly injected."""
    plugin.config["confetti"] = True
    markdown = """
<quiz>
Question?
- [x] Yes
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Confetti library should be included (bundled locally)
    assert "JSConfetti" in html_result
    # Config should indicate confetti is enabled
    assert "mkdocsQuizConfig" in html_result
    assert "confetti: true" in html_result


def test_confetti_disabled(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that confetti can be disabled."""
    plugin.config["confetti"] = False
    markdown = """
<quiz>
Question?
- [x] Yes
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Config should indicate confetti is disabled
    assert "mkdocsQuizConfig" in html_result
    assert "confetti: false" in html_result
    # Note: The confetti library is bundled and included, but won't be initialized
    # when confetti config is false


def test_material_theme_integration(plugin: MkDocsQuizPlugin) -> None:
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
    result_env = plugin.on_env(env, config, None)  # type: ignore[arg-type]

    # Should add our template loader
    assert result_env is not None
    assert isinstance(result_env.loader, ChoiceLoader)  # ChoiceLoader was added


def test_show_progress_config(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that show_progress configuration works."""
    plugin.config["show_progress"] = False
    markdown = """
<quiz>
Question?
- [x] Yes
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Config should indicate progress is disabled
    assert "mkdocsQuizConfig" in html_result
    assert "showProgress: false" in html_result


def test_auto_number_config(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should have question numbers
    assert "Question 1" in html_result
    assert "Question 2" in html_result
    assert "quiz-auto-number" in html_result


def test_progress_sidebar_position_config(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that progress_sidebar_position configuration is injected."""
    # Test default value (top)
    plugin.config["progress_sidebar_position"] = "top"
    markdown = """
<quiz>
Question?
- [x] Yes
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Config should include progressSidebarPosition
    assert "mkdocsQuizConfig" in html_result
    assert 'progressSidebarPosition: "top"' in html_result

    # Test bottom value
    plugin.config["progress_sidebar_position"] = "bottom"
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Config should indicate bottom position
    assert "mkdocsQuizConfig" in html_result
    assert 'progressSidebarPosition: "bottom"' in html_result


def test_special_characters_in_answers(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that quotes and special chars in answers work correctly."""
    markdown = """
<quiz>
What's the answer?
- [x] It's "correct" & <valid>
- [ ] Wrong answer
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should process without errors
    assert 'type="radio"' in html_result
    # Markdown converter should handle escaping
    assert "correct" in html_result


def test_code_in_quiz_content(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Code block should be present in content section (with syntax highlighting)
    assert "hello" in html_result  # Function name should be there
    assert "codehilite" in html_result  # Syntax highlighting div
    assert '<section class="content hidden">' in html_result


def test_multiple_quizzes_same_question(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Each quiz should have unique ID
    assert 'id="quiz-0"' in html_result
    assert 'id="quiz-1"' in html_result
    assert 'id="quiz-0-0"' in html_result  # First answer of first quiz
    assert 'id="quiz-1-0"' in html_result  # First answer of second quiz


def test_quiz_with_only_answers_no_question(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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


def test_capital_x_in_checkbox(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that capital X in checkboxes is recognized as correct."""
    markdown = """
<quiz>
Capital X test?
- [X] Correct with capital X
- [ ] Wrong
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should recognize capital X as correct
    assert "correct" in html_result
    assert 'type="radio"' in html_result


def test_malformed_checkbox_y_raises_error(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
        match=r"Invalid checkbox format.*\[y\].*Only.*\[x\].*\[X\].*\[ \].*\[\].*allowed.*- or \* bullet",
    ):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_malformed_checkbox_checkmark_raises_error(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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


def test_malformed_checkbox_star_raises_error(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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


def test_malformed_checkbox_lowercase_o_raises_error(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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


def test_all_valid_checkbox_formats(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should process successfully with all 4 formats
    assert 'type="checkbox"' in html_result  # Multiple correct = checkboxes
    assert html_result.count('type="checkbox"') == 4
    # Both [x] and [X] should be marked as correct
    assert html_result.count(" correct>") == 2


def test_very_long_quiz_content(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should process successfully despite large size
    assert 'type="radio"' in html_result
    # At least 20 radio buttons (exact count may vary based on parsing)
    assert html_result.count('type="radio"') >= 20
    assert "correct" in html_result
    assert "Content section with lots of text" in html_result


def test_special_characters_in_question(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test special HTML characters in question text."""
    markdown = """
<quiz>
What does <div class="test"> & "quotes" do?
- [x] It's HTML & markup
- [ ] Nothing
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Markdown should escape HTML in question
    # The exact escaping depends on markdown processor, but should be safe
    assert 'type="radio"' in html_result
    assert "quiz-question" in html_result


def test_quiz_with_only_empty_checkboxes(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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


def test_nested_lists_in_quiz_content(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
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
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should process successfully
    assert 'type="radio"' in html_result
    # Content section should have the list converted to HTML
    assert "Item 1" in html_result
    assert "Item 2" in html_result


def test_markdown_formatting_in_question(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test markdown formatting (bold, italic, code) in question."""
    markdown = """
<quiz>
What does **bold** and *italic* and `code` mean?
- [x] Markdown formatting
- [ ] Nothing
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should process markdown in question
    assert "<strong>bold</strong>" in html_result
    assert "<em>italic</em>" in html_result
    assert "<code>code</code>" in html_result


def test_old_syntax_detection_opening_tag(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that old v0.x <?quiz?> opening tag is detected and build fails."""
    markdown = """
<?quiz?>
question: Are you ready?
answer-correct: Yes!
answer: No!
<?/quiz?>
"""
    # Should raise ValueError with migration instructions
    with pytest.raises(
        ValueError,
        match=r"ERROR: Old mkdocs-quiz syntax detected",
    ):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_old_syntax_detection_closing_tag(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that old v0.x <?/quiz?> closing tag is detected and build fails."""
    markdown = """
Some text with old closing tag: <?/quiz?>
"""
    # Should raise ValueError with migration instructions
    with pytest.raises(
        ValueError,
        match=r"ERROR: Old mkdocs-quiz syntax detected",
    ):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_old_syntax_error_message_content(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that error message contains helpful migration instructions."""
    markdown = """
<?quiz?>
question: Test
answer-correct: Yes
<?/quiz?>
"""
    try:
        plugin.on_page_markdown(markdown, mock_page, mock_config)
        pytest.fail("Expected ValueError to be raised")
    except ValueError as e:
        error_msg = str(e)
        # Check that error message contains key information
        assert "mkdocs-quiz migrate docs/" in error_msg
        assert "v1 release" in error_msg
        assert "ewels.github.io/mkdocs-quiz/migration" in error_msg


def test_new_syntax_not_detected_as_old(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that new v1.0 syntax is not incorrectly flagged as old syntax."""
    markdown = """
<quiz>
Are you ready?
- [x] Yes!
- [ ] No!
</quiz>
"""
    # Should process without errors
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None
    assert "Are you ready?" in html_result


def test_old_syntax_in_code_block_not_detected(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that old syntax inside code blocks is ignored (documentation example)."""
    markdown = """
Here's the old syntax for reference:

```markdown
<?quiz?>
question: Are you ready?
answer-correct: Yes!
<?/quiz?>
```

And here's a new quiz:

<quiz>
Real question?
- [x] Yes
- [ ] No
</quiz>
"""
    # Should NOT raise an error because old syntax is in a code block
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None
    assert "Real question?" in html_result
    # Old syntax should remain in code block
    assert "<?quiz?>" in html_result


def test_fill_in_blank_single(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test processing a fill-in-the-blank quiz with a single blank."""
    markdown = """
<quiz>
2 + 2 = [[4]]
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should contain fill-blank quiz marker
    assert 'data-quiz-type="fill-blank"' in result
    # Should contain text input
    assert 'type="text"' in result
    assert 'class="quiz-blank-input"' in result
    # Should contain the correct answer in data attribute
    assert 'data-answer="4"' in result
    # Should have the question text
    assert "2 + 2 =" in result


def test_fill_in_blank_multiple(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test processing a fill-in-the-blank quiz with multiple blanks."""
    markdown = """
<quiz>
The capital of France is [[Paris]] and the capital of Spain is [[Madrid]].
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should contain fill-blank quiz marker
    assert 'data-quiz-type="fill-blank"' in result
    # Should contain two text inputs
    assert result.count('type="text"') == 2
    assert result.count('class="quiz-blank-input"') == 2
    # Should contain both correct answers
    assert 'data-answer="Paris"' in result
    assert 'data-answer="Madrid"' in result
    # Should have the question text
    assert "The capital of France is" in result
    assert "and the capital of Spain is" in result


def test_fill_in_blank_with_markdown(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test fill-in-the-blank with markdown formatting around blanks."""
    markdown = """
<quiz>
The **bold** answer is [[correct]] and the *italic* one is [[also correct]].
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should process markdown
    assert "<strong>bold</strong>" in result
    assert "<em>italic</em>" in result
    # Should contain correct answers
    assert 'data-answer="correct"' in result
    assert 'data-answer="also correct"' in result


def test_fill_in_blank_with_content(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test fill-in-the-blank with content section separated by horizontal rule."""
    markdown = """
<quiz>
2 + 2 = [[4]]

---
That's correct! Basic arithmetic.
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should contain fill-blank quiz marker
    assert 'data-quiz-type="fill-blank"' in result
    # Should have content section with the explanation
    assert "Basic arithmetic" in result
    assert '<section class="content hidden">' in result


def test_fill_in_blank_with_content_and_markdown(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test fill-in-the-blank with content section containing markdown."""
    markdown = """
<quiz>
Some markdown:

The answer is [[foo]].

Another answer is [[bar]].

---
This *content* is only shown after answering.

It can have **bold** and `code`.
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should contain fill-blank quiz marker
    assert 'data-quiz-type="fill-blank"' in result
    # Should have both blanks
    assert 'data-answer="foo"' in result
    assert 'data-answer="bar"' in result
    # Should have content section with markdown converted to HTML
    assert "<em>content</em>" in result
    assert "<strong>bold</strong>" in result
    assert "<code>code</code>" in result
    assert '<section class="content hidden">' in result


def test_fill_in_blank_html_escaping(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that fill-in-the-blank answers are properly HTML escaped."""
    markdown = """
<quiz>
The HTML tag for bold is [[<strong>]].
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Answer should be HTML escaped in the data attribute
    assert 'data-answer="&lt;strong&gt;"' in result
    # Should not contain unescaped HTML tag
    assert 'data-answer="<strong>"' not in result


def test_fill_in_blank_no_blanks_error(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that quiz without blanks or checkboxes raises ValueError."""
    markdown = """
<quiz>
This has no blanks in it.
</quiz>
"""
    # Should raise ValueError (no answers found - treated as multiple-choice quiz)
    with pytest.raises(ValueError, match=r"Quiz must have at least one answer"):
        plugin.on_page_markdown(markdown, mock_page, mock_config)


def test_fill_in_blank_autocomplete_off(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that fill-in-the-blank inputs have autocomplete disabled."""
    markdown = """
<quiz>
Answer: [[test]]
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should have autocomplete="off" attribute
    assert 'autocomplete="off"' in result


def test_fill_in_blank_with_special_characters(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test fill-in-the-blank with special characters in answers."""
    markdown = """
<quiz>
The answer with quotes is [["hello"]] and with ampersand is [[a & b]].
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Answers should be properly escaped
    assert 'data-answer="&quot;hello&quot;"' in result
    assert 'data-answer="a &amp; b"' in result


def test_fill_in_blank_unique_ids(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that multiple fill-in-the-blank inputs get unique IDs."""
    markdown = """
<quiz>
First [[answer]] and second [[answer]].
</quiz>

<quiz>
Third [[answer]].
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should have unique IDs for each input
    assert 'id="quiz-0-blank-0"' in result
    assert 'id="quiz-0-blank-1"' in result
    assert 'id="quiz-1-blank-0"' in result


def test_fill_in_blank_show_correct_option(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that fill-in-the-blank respects show_correct option."""
    mock_page.meta["quiz"] = {"show_correct": False}
    markdown = """
<quiz>
Answer: [[test]]
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should NOT have show-correct data attribute when disabled
    assert 'data-show-correct="true"' not in result
    # Should still be a fill-blank quiz
    assert 'data-quiz-type="fill-blank"' in result


def test_fill_in_blank_auto_number(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that fill-in-the-blank supports auto_number option."""
    mock_page.meta["quiz"] = {"auto_number": True}
    markdown = """
<quiz>
First: [[answer]]
</quiz>

<quiz>
Second: [[answer]]
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should have question numbers
    assert "Question 1" in result
    assert "Question 2" in result


def test_fill_in_blank_markdown_extensions(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that fill-in-the-blank quizzes use markdown extensions from config."""
    # Configure markdown extensions
    mock_config["markdown_extensions"] = ["extra"]

    markdown = """
<quiz>
The answer is **bold** and the blank is [[answer]].

---
This *content* has `code` and uses extensions.
</quiz>
"""
    # Process markdown phase
    markdown_result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    # Process content phase (convert placeholders to actual HTML)
    result = plugin.on_page_content(markdown_result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert result is not None

    # Should convert markdown in question text
    assert "<strong>bold</strong>" in result
    # Should convert markdown in content section
    assert "<em>content</em>" in result
    assert "<code>code</code>" in result
    # Should still have fill-blank quiz functionality
    assert 'data-quiz-type="fill-blank"' in result
    assert 'data-answer="answer"' in result


def test_markdown_extensions_from_config(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that markdown extensions from mkdocs.yml config are used in quizzes."""
    # Configure admonition extension in mock config
    mock_config["markdown_extensions"] = ["admonition"]

    markdown = """
<quiz>
What is this?
- [x] An admonition
- [ ] A paragraph

!!! note
    This is a note admonition.
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should have admonition processed
    assert "admonition" in html_result
    assert "note" in html_result


def test_markdown_extensions_with_config_options(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that markdown extension configs are passed through."""
    # Configure toc extension with a custom option
    mock_config["markdown_extensions"] = ["toc"]
    mock_config["mdx_configs"] = {"toc": {"permalink": True}}

    markdown = """
<quiz>
## What is this heading?
- [x] A quiz question with heading
- [ ] Nothing
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should have heading with permalink (toc extension config applied)
    assert "What is this heading?" in html_result
    # The heading should be converted
    assert "<h2" in html_result


def test_default_extensions_when_config_empty(plugin: MkDocsQuizPlugin, mock_page: Page) -> None:
    """Test that default extensions are used when config has no extensions."""
    # Create a config with no extensions explicitly set
    empty_config = MkDocsConfig()
    assert empty_config.markdown_extensions == []

    markdown = """
<quiz>
What is `inline code`?
- [x] Code with **bold** text
- [ ] Plain text

```python
def hello():
    print("world")
```
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, empty_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=empty_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Default extensions should be used:
    # - extra: processes inline code and bold
    # - codehilite: syntax highlighting for code blocks
    assert "<code>" in html_result
    assert "<strong>bold</strong>" in html_result
    # codehilite should be active for syntax highlighting
    assert "codehilite" in html_result


def test_tables_extension_in_quiz(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that tables extension works in quiz content section."""
    # The 'extra' extension includes tables
    mock_config["markdown_extensions"] = ["extra"]

    markdown = """
<quiz>
What is shown below?
- [x] A table
- [ ] A list

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Table should be converted to HTML
    assert "<table>" in html_result
    assert "<th>" in html_result or "Header 1" in html_result


def test_pymdownx_superfences_if_installed(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that pymdownx.superfences works if installed."""
    try:
        import pymdownx  # noqa: F401
    except ImportError:
        pytest.skip("pymdownx not installed")

    mock_config["markdown_extensions"] = ["pymdownx.superfences"]

    markdown = """
<quiz>
What does this code do?
- [x] Prints hello
- [ ] Nothing

```python
print("hello")
```
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Superfences should wrap code blocks
    assert "print" in html_result
    # Superfences uses highlight class by default
    assert (
        "highlight" in html_result
        or "codehilite" in html_result
        or "language-python" in html_result
    )


def test_asterisk_bullet_single_choice(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that asterisk bullets work for single choice quizzes."""
    markdown = """
<quiz>
What is 2+2?
* [x] 4
* [ ] 3
* [ ] 5
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    assert "What is 2+2?" in html_result
    assert 'type="radio"' in html_result
    assert "correct" in html_result


def test_asterisk_bullet_multiple_choice(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that asterisk bullets work for multiple choice quizzes."""
    markdown = """
<quiz>
Which are even numbers?
* [x] 2
* [ ] 3
* [x] 4
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    assert "Which are even numbers?" in html_result
    assert 'type="checkbox"' in html_result
    # Two correct answers
    assert html_result.count(" correct>") == 2


def test_mixed_bullet_styles(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that mixing hyphen and asterisk bullets works within same quiz."""
    markdown = """
<quiz>
Mixed bullets?
- [x] Hyphen correct
* [ ] Asterisk wrong
- [ ] Hyphen wrong
* [x] Asterisk correct
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should have all 4 answers
    assert html_result.count('type="checkbox"') == 4
    # Two correct answers
    assert html_result.count(" correct>") == 2
    assert "Hyphen correct" in html_result
    assert "Asterisk wrong" in html_result
    assert "Hyphen wrong" in html_result
    assert "Asterisk correct" in html_result


def test_asterisk_bullet_all_valid_formats(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that all valid checkbox formats work with asterisk bullets."""
    markdown = """
<quiz>
Which are valid?
* [x] Lowercase x (correct)
* [X] Uppercase X (correct)
* [ ] Space (incorrect)
* [] Empty (incorrect)
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    # Should process successfully with all 4 formats
    assert 'type="checkbox"' in html_result
    assert html_result.count('type="checkbox"') == 4
    # Both [x] and [X] should be marked as correct
    assert html_result.count(" correct>") == 2


def test_asterisk_bullet_with_content(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that asterisk bullets work with content section."""
    markdown = """
<quiz>
What is Python?
* [x] A programming language
* [ ] A snake

Python is a high-level programming language.
</quiz>
"""
    result = plugin.on_page_markdown(markdown, mock_page, mock_config)
    html_result = plugin.on_page_content(result, page=mock_page, config=mock_config, files=None)  # type: ignore[arg-type]
    assert html_result is not None

    assert "What is Python?" in html_result
    assert "A programming language" in html_result
    assert "high-level programming language" in html_result
    assert '<section class="content hidden">' in html_result


def test_asterisk_bullet_malformed_checkbox_raises_error(
    plugin: MkDocsQuizPlugin, mock_page: Page, mock_config: MkDocsConfig
) -> None:
    """Test that malformed checkbox with asterisk bullet raises ValueError."""
    markdown = """
<quiz>
Question?
* [y] This should raise an error
* [x] Correct answer
</quiz>
"""
    with pytest.raises(
        ValueError,
        match=r"Invalid checkbox format.*\[y\]",
    ):
        plugin.on_page_markdown(markdown, mock_page, mock_config)
