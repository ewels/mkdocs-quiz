"""MkDocs Quiz Plugin - Main plugin module."""

from __future__ import annotations

import html
import logging
import re
import sys
import threading
from pathlib import Path
from textwrap import dedent
from typing import Any

import markdown as md
from mkdocs.config import config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

# Compatibility import for Python 3.8
if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

from . import css, js

log = logging.getLogger("mkdocs.plugins.mkdocs_quiz")

# Load CSS and JS resources at module level
try:
    inp_file = files(css) / "quiz.css"
    with inp_file.open("r") as f:
        style = f.read()
    style = f'<style type="text/css">{style}</style>'

    js_file = files(js) / "quiz.js"
    with js_file.open("r") as f:
        js_content = f.read()
    js_script = f'<script type="text/javascript" defer>{js_content}</script>'

    # Load confetti library from vendor directory (v0.12.0)
    confetti_file = files(js) / "vendor" / "js-confetti.browser.js"
    with confetti_file.open("r") as f:
        confetti_content = f.read()
    confetti_lib_script = f'<script type="text/javascript">{confetti_content}</script>'
except OSError as e:
    log.error(f"Failed to load CSS/JS resources: {e}")
    style = ""
    js_script = ""
    confetti_lib_script = ""

# Thread-local storage for markdown converter (thread-safe for parallel builds)
_markdown_converter_local = threading.local()


def get_markdown_converter() -> md.Markdown:
    """Get or create a thread-local markdown converter instance.

    Returns:
        A thread-local Markdown converter instance.
    """
    if not hasattr(_markdown_converter_local, "converter"):
        _markdown_converter_local.converter = md.Markdown(extensions=["extra", "codehilite", "toc"])
    return _markdown_converter_local.converter  # type: ignore[no-any-return]


# Quiz tag format:
# <quiz>
# Are you ready?
# - [x] Yes!
# - [ ] No!
# - [ ] Maybe!
#
# Optional content section (supports full markdown)
# Can include **bold**, *italic*, `code`, etc.
# </quiz>

QUIZ_START_TAG = "<quiz>"
QUIZ_END_TAG = "</quiz>"
QUIZ_REGEX = r"<quiz>(.*?)</quiz>"


def convert_inline_markdown(text: str) -> str:
    """Convert markdown to HTML for inline content (questions/answers).

    Args:
        text: The markdown text to convert.

    Returns:
        The HTML string with wrapping <p> tags removed.
    """
    # Reset the converter state
    converter = get_markdown_converter()
    converter.reset()
    html_content = converter.convert(text)
    # Remove wrapping <p> tags for inline content
    if html_content.startswith("<p>") and html_content.endswith("</p>"):
        html_content = html_content[3:-4]
    return html_content


class MkDocsQuizPlugin(BasePlugin):
    """MkDocs plugin to create interactive quizzes in markdown documents."""

    config_scheme = (
        ("enabled_by_default", config_options.Type(bool, default=True)),
        ("auto_number", config_options.Type(bool, default=False)),
        ("show_correct", config_options.Type(bool, default=True)),
        ("auto_submit", config_options.Type(bool, default=True)),
        ("disable_after_submit", config_options.Type(bool, default=True)),
        ("show_progress", config_options.Type(bool, default=True)),
        ("confetti", config_options.Type(bool, default=True)),
    )

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        # Store quiz HTML for each page to be injected later
        self._quiz_storage: dict[str, dict[str, str]] = {}
        # Track if results div is present on each page
        self._has_results_div: dict[str, bool] = {}
        # Track if intro is present on each page
        self._has_intro: dict[str, bool] = {}

    def on_env(self, env: Any, config: MkDocsConfig, files: Files) -> Any:
        """Add our template directory to the Jinja2 environment.

        This allows us to override the toc.html partial to add the quiz progress sidebar.
        Only runs if using mkdocs material

        Args:
            env: The Jinja2 environment.
            config: The MkDocs config object.
            files: The files collection.

        Returns:
            The modified Jinja2 environment.
        """
        if config.theme.name == "material":
            from jinja2 import ChoiceLoader, FileSystemLoader

            # Get the path to our overrides directory
            overrides_dir = Path(__file__).parent / "overrides"

            # Add our templates with HIGHER priority so they're found first
            # The ! prefix in our template will then load the next one in the chain
            env.loader = ChoiceLoader([FileSystemLoader(str(overrides_dir)), env.loader])

            log.info(
                "mkdocs-quiz: Added template overrides to integrate quiz progress sidebar into TOC"
            )

        return env

    def _should_process_page(self, page: Page) -> bool:
        """Check if quizzes should be processed on this page.

        Args:
            page: The current page object.

        Returns:
            True if quizzes should be processed, False otherwise.
        """
        enabled_by_default = self.config.get("enabled_by_default", True)
        quiz_meta = page.meta.get("quiz", None)

        # Handle frontmatter: quiz: { enabled: true/false }
        if isinstance(quiz_meta, dict):
            return quiz_meta.get("enabled", enabled_by_default)  # type: ignore[no-any-return]

        # No page-level override, use plugin default
        return enabled_by_default  # type: ignore[no-any-return]

    def _get_quiz_options(self, page: Page) -> dict[str, bool]:
        """Get quiz options from page frontmatter or plugin config.

        Args:
            page: The current page object.

        Returns:
            Dictionary with show_correct, auto_submit, disable_after_submit, auto_number, and show_progress options.
        """
        # Start with plugin defaults
        options = {
            "show_correct": self.config.get("show_correct", True),
            "auto_submit": self.config.get("auto_submit", True),
            "disable_after_submit": self.config.get("disable_after_submit", True),
            "auto_number": self.config.get("auto_number", False),
            "show_progress": self.config.get("show_progress", True),
        }

        # Override with page-level settings if present
        quiz_meta = page.meta.get("quiz")
        if isinstance(quiz_meta, dict):
            options.update({k: v for k, v in quiz_meta.items() if k in options})

        return options

    def _parse_quiz_question_and_answers(
        self, quiz_lines: list[str]
    ) -> tuple[str, list[str], list[str], int]:
        """Parse quiz question and answers from quiz lines.

        The question is everything up to the first checkbox answer.
        Answers are checkbox items (- [x] or - [ ]).
        Content is everything after the last answer.

        Args:
            quiz_lines: The lines of the quiz content.

        Returns:
            A tuple of (question_text, all_answers, correct_answers, content_start_index).
        """
        # Find the first answer line and validate checkbox format
        first_answer_index = None
        for i, line in enumerate(quiz_lines):
            # Check if this looks like a checkbox list item (any character in brackets)
            checkbox_check = re.match(r"^- \[(.?)\] (.*)$", line)
            if checkbox_check:
                checkbox_content = checkbox_check.group(1)
                # Strictly validate: only accept x, X, space, or empty
                if checkbox_content not in ["x", "X", " ", ""]:
                    raise ValueError(
                        f"Invalid checkbox format: '- [{checkbox_content}]'. "
                        f"Only '- [x]', '- [X]', '- [ ]', or '- []' are allowed. "
                        f"Found in line: {line}"
                    )
                first_answer_index = i
                break

        if first_answer_index is None:
            # No answers found - invalid quiz structure
            question_text = "\n".join(quiz_lines).strip()
            log.warning(f"Quiz has no checkbox answers: {question_text[:50]}...")
            return question_text, [], [], len(quiz_lines)

        # Everything before the first answer is the question
        question_lines = quiz_lines[:first_answer_index]
        question_text = "\n".join(question_lines).strip()

        # Parse answers starting from first_answer_index
        all_answers = []
        correct_answers = []
        content_start_index = first_answer_index

        for i, line in enumerate(quiz_lines[first_answer_index:], start=first_answer_index):
            # First check if this looks like a checkbox item (any character in brackets)
            checkbox_pattern = re.match(r"^- \[(.?)\] (.*)$", line)
            if checkbox_pattern:
                checkbox_content = checkbox_pattern.group(1)
                # Strictly validate: only accept x, X, space, or empty
                if checkbox_content not in ["x", "X", " ", ""]:
                    raise ValueError(
                        f"Invalid checkbox format: '- [{checkbox_content}]'. "
                        f"Only '- [x]', '- [X]', '- [ ]', or '- []' are allowed. "
                        f"Found in line: {line}"
                    )
                is_correct = checkbox_content.lower() == "x"
                answer_text = checkbox_pattern.group(2)
                answer_html = convert_inline_markdown(answer_text)
                all_answers.append(answer_html)
                if is_correct:
                    correct_answers.append(answer_html)
                content_start_index = i + 1
            elif not line.strip():
                # Empty line, continue
                continue
            else:
                # Not a checkbox item and not empty, must be content
                break

        return question_text, all_answers, correct_answers, content_start_index

    def _generate_answer_html(
        self, all_answers: list[str], correct_answers: list[str], quiz_id: int
    ) -> tuple[list[str], bool]:
        """Generate HTML for quiz answers.

        Args:
            all_answers: List of all answer texts.
            correct_answers: List of correct answer texts.
            quiz_id: The unique ID for this quiz.

        Returns:
            A tuple of (list of answer HTML strings, whether to use checkboxes).
        """
        # Determine if multiple choice (checkboxes) or single choice (radio)
        as_checkboxes = len(correct_answers) > 1

        # Generate answer HTML
        answer_html_list = []
        for i, answer in enumerate(all_answers):
            is_correct = answer in correct_answers
            input_id = f"quiz-{quiz_id}-{i}"
            input_type = "checkbox" if as_checkboxes else "radio"
            correct_attr = "correct" if is_correct else ""

            # Escape the value attribute for defense-in-depth (i is numeric, but escape anyway)
            escaped_value = html.escape(str(i))

            answer_html = (
                f'<div><input type="{input_type}" name="answer" value="{escaped_value}" '
                f'id="{input_id}" {correct_attr}>'
                f'<label for="{input_id}">{answer}</label></div>'
            )
            answer_html_list.append(answer_html)

        return answer_html_list, as_checkboxes

    def _mask_code_blocks(self, markdown: str) -> tuple[str, dict[str, str]]:
        """Temporarily mask fenced code blocks to prevent processing quiz tags inside them.

        Only masks code blocks that are NOT inside quiz tags, to avoid breaking quizzes
        that contain code examples in their content sections.

        Args:
            markdown: The markdown content.

        Returns:
            A tuple of (masked markdown, dictionary of placeholders to original content).
        """
        placeholders = {}
        counter = 0

        # Find all quiz blocks first
        quiz_ranges = []
        for match in re.finditer(QUIZ_REGEX, markdown, re.DOTALL):
            quiz_ranges.append((match.start(), match.end()))

        # Mask fenced code blocks (```...``` or ~~~...~~~)
        def replace_fenced(match):
            nonlocal counter
            # Check if this code block is inside a quiz
            match_start = match.start()
            match_end = match.end()
            for quiz_start, quiz_end in quiz_ranges:
                if quiz_start < match_start < quiz_end or quiz_start < match_end < quiz_end:
                    # Code block is inside a quiz, don't mask it
                    return match.group(0)

            # Code block is outside quizzes, mask it
            placeholder = f"__CODEBLOCK_{counter}__"
            placeholders[placeholder] = match.group(0)
            counter += 1
            return placeholder

        # Match fenced code blocks with optional language specifier
        # Supports ``` and ~~~ delimiters (3 or more), with optional indentation
        markdown = re.sub(
            r"^[ \t]*`{3,}.*?\n.*?^[ \t]*`{3,}|^[ \t]*~{3,}.*?\n.*?^[ \t]*~{3,}",
            replace_fenced,
            markdown,
            flags=re.MULTILINE | re.DOTALL,
        )

        return markdown, placeholders

    def _unmask_code_blocks(self, markdown: str, placeholders: dict[str, str]) -> str:
        """Restore code blocks that were temporarily masked.

        Args:
            markdown: The markdown content with placeholders.
            placeholders: Dictionary of placeholders to original content.

        Returns:
            The markdown with code blocks restored.
        """
        for placeholder, original in placeholders.items():
            markdown = markdown.replace(placeholder, original)
        return markdown

    def on_page_markdown(
        self, markdown: str, page: Page, config: MkDocsConfig, **kwargs: Any
    ) -> str:
        """Process markdown to convert quiz tags to placeholders.

        The quiz HTML is generated and stored, then placeholders are inserted.
        The actual HTML is injected later in on_page_content.

        Args:
            markdown: The markdown content of the page.
            page: The current page object.
            config: The MkDocs config object.
            **kwargs: Additional keyword arguments.

        Returns:
            The processed markdown with quiz placeholders.
        """
        # Check if quizzes should be processed on this page
        if not self._should_process_page(page):
            return markdown

        # Initialize storage for this page
        page_key = page.file.src_path
        self._quiz_storage[page_key] = {}

        # Check for results div comment
        results_comment = "<!-- mkdocs-quiz results -->"
        self._has_results_div[page_key] = results_comment in markdown

        # Check for intro comment and mark for later replacement
        intro_comment = "<!-- mkdocs-quiz intro -->"
        self._has_intro[page_key] = intro_comment in markdown

        # Mask code blocks to prevent processing quiz tags inside them
        masked_markdown, placeholders = self._mask_code_blocks(markdown)

        # Process quizzes and replace with placeholders
        options = self._get_quiz_options(page)

        # Find all quiz matches
        matches = list(re.finditer(QUIZ_REGEX, masked_markdown, re.DOTALL))

        # Build replacement segments efficiently (O(n) instead of O(n²))
        segments = []
        last_end = 0

        for quiz_id, match in enumerate(matches):
            try:
                # Generate quiz HTML
                quiz_html = self._process_quiz(match.group(1), quiz_id, options)

                # Create a markdown-safe placeholder
                placeholder = f"<!-- MKDOCS_QUIZ_PLACEHOLDER_{quiz_id} -->"

                # Store the quiz HTML for later injection
                self._quiz_storage[page_key][placeholder] = quiz_html

                # Add the text before this match and the placeholder
                segments.append(masked_markdown[last_end : match.start()])
                segments.append(placeholder)
                last_end = match.end()

            except ValueError:
                # Re-raise ValueError to crash the build (malformed quiz)
                raise
            except Exception as e:
                # Log other errors but continue
                log.error(f"Failed to process quiz {quiz_id} in {page.file.src_path}: {e}")
                # On error, include the original quiz text
                segments.append(masked_markdown[last_end : match.end()])
                last_end = match.end()

        # Add any remaining text after the last match
        segments.append(masked_markdown[last_end:])

        # Join all segments at once (single operation)
        masked_markdown = "".join(segments)

        # Restore code blocks
        markdown = self._unmask_code_blocks(masked_markdown, placeholders)

        return markdown

    def _process_quiz(self, quiz_content: str, quiz_id: int, options: dict[str, bool]) -> str:
        """Process a single quiz and convert it to HTML.

        Args:
            quiz_content: The content inside the quiz tags.
            quiz_id: The unique ID for this quiz.
            options: Quiz options (show_correct, auto_submit, disable_after_submit, auto_number).

        Returns:
            The HTML representation of the quiz.

        Raises:
            ValueError: If the quiz format is invalid.
        """
        # Dedent the quiz content to handle indented quizzes (e.g., in content tabs)
        quiz_content = dedent(quiz_content)

        quiz_lines = quiz_content.splitlines()

        # Remove empty lines at start and end
        while quiz_lines and quiz_lines[0] == "":
            quiz_lines = quiz_lines[1:]
        while quiz_lines and quiz_lines[-1] == "":
            quiz_lines = quiz_lines[:-1]

        if not quiz_lines:
            raise ValueError("Quiz content is empty")

        # Parse question and answers
        # Question is everything up to the first checkbox answer
        question_text, all_answers, correct_answers, content_start_index = (
            self._parse_quiz_question_and_answers(quiz_lines)
        )

        # Validate quiz structure
        if not question_text.strip():
            raise ValueError("Quiz must have a question")
        if not all_answers:
            raise ValueError("Quiz must have at least one answer")
        if not correct_answers:
            raise ValueError("Quiz must have at least one correct answer")

        # Convert question markdown to HTML (supports multi-line questions with markdown)
        converter = get_markdown_converter()
        converter.reset()
        question = converter.convert(question_text)

        # Generate answer HTML
        answer_html_list, as_checkboxes = self._generate_answer_html(
            all_answers, correct_answers, quiz_id
        )

        # Get quiz content (everything after the last answer)
        content_lines = quiz_lines[content_start_index:]
        # Convert content markdown to HTML
        content_html = ""
        if content_lines:
            content_text = "\n".join(content_lines)
            # Use full markdown conversion for content section
            converter = get_markdown_converter()
            converter.reset()
            content_html = converter.convert(content_text)

        # Build data attributes for quiz options
        data_attrs = []
        if options["show_correct"]:
            data_attrs.append('data-show-correct="true"')
        if options["auto_submit"]:
            data_attrs.append('data-auto-submit="true"')
        if options["disable_after_submit"]:
            data_attrs.append('data-disable-after-submit="true"')
        attrs = " ".join(data_attrs)

        # Hide submit button only if auto-submit is enabled AND it's a single-choice quiz
        # For multiple-choice (checkboxes), always show the submit button
        submit_button = (
            ""
            if options["auto_submit"] and not as_checkboxes
            else '<button type="submit" class="quiz-button">Submit</button>'
        )
        # Generate quiz ID for linking
        quiz_header_id = f"quiz-{quiz_id}"
        answers_html = "".join(answer_html_list)

        # If auto_number is enabled, add a header with the question number
        question_header = ""
        if options["auto_number"]:
            # quiz_id is 0-indexed, so add 1 for display
            question_number = quiz_id + 1
            question_header = f'<h4 class="quiz-number">Question {question_number}</h4>'

        quiz_html = dedent(f"""
            <div class="quiz" {attrs} id="{quiz_header_id}">
                <a href="#{quiz_header_id}" class="quiz-header-link">#</a>
                {question_header}
                <div class="quiz-question">
                    {question}
                </div>
                <form>
                    <fieldset>{answers_html}</fieldset>
                    <div class="quiz-feedback hidden"></div>
                    {submit_button}
                </form>
                <section class="content hidden">{content_html}</section>
            </div>
        """).strip()

        return quiz_html

    def _generate_results_html(self) -> str:
        """Generate HTML for the quiz results end screen.

        Returns:
            The HTML representation of the results div.
        """
        results_html = dedent(
            """
            <div id="quiz-results" class="quiz-results">
                <div class="quiz-results-progress">
                    <h3>Quiz Progress</h3>
                    <p class="quiz-results-stats">
                        <span class="quiz-results-answered">0</span> of <span class="quiz-results-total">0</span> questions answered
                        (<span class="quiz-results-percentage">0%</span>)
                    </p>
                    <p class="quiz-results-correct-stats">
                        <span class="quiz-results-correct">0</span> correct
                    </p>
                </div>
                <div class="quiz-results-complete hidden">
                    <h2 class="quiz-results-title">Quiz Complete!</h2>
                    <div class="quiz-results-score-display">
                        <span class="quiz-results-score-value">0%</span>
                    </div>
                    <p class="quiz-results-message"></p>
                    <button type="button" class="md-button md-button--primary quiz-results-reset">Reset quiz</button>
                </div>
            </div>
        """
        ).strip()
        return results_html

    def _generate_intro_html(self) -> str:
        """Generate HTML for the quiz intro text with reset button.

        Returns:
            The HTML representation of the intro div.
        """
        intro_html = dedent(
            """
            <div class="quiz-intro">
                <p>Quiz results are saved to your browser's local storage and will persist between sessions.</p>
                <button type="button" class="md-button quiz-intro-reset">Reset quiz</button>
            </div>
        """
        ).strip()
        return intro_html

    def on_page_content(
        self, html: str, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        """Replace quiz placeholders with actual HTML and add CSS/JS to the page.

        Args:
            html: The HTML content of the page.
            page: The current page object.
            config: The MkDocs config object.
            files: The files object.

        Returns:
            The HTML with quiz content, styles and scripts.
        """
        # Check if quizzes should be processed on this page
        if not self._should_process_page(page):
            return html

        # Replace placeholders with actual quiz HTML
        page_key = page.file.src_path
        if page_key in self._quiz_storage:
            for placeholder, quiz_html in self._quiz_storage[page_key].items():
                html = html.replace(placeholder, quiz_html)

            # Clean up storage for this page
            del self._quiz_storage[page_key]

        # Get quiz options to check settings
        options = self._get_quiz_options(page)

        # Handle results div if present
        if self._has_results_div.get(page_key, False):
            results_html = self._generate_results_html()
            html = html.replace("<!-- mkdocs-quiz results -->", results_html)
            # Clean up
            del self._has_results_div[page_key]

        # Handle intro if present
        if self._has_intro.get(page_key, False):
            intro_html = self._generate_intro_html()
            html = html.replace("<!-- mkdocs-quiz intro -->", intro_html)
            # Clean up
            del self._has_intro[page_key]

        # Add auto-numbering class if enabled
        auto_number_script = ""
        if options["auto_number"]:
            auto_number_script = dedent(
                """
                <script type="text/javascript">
                document.addEventListener("DOMContentLoaded", function() {
                  var article = document.querySelector("article") || document.querySelector("main") || document.body;
                  article.classList.add("quiz-auto-number");
                });
                </script>
            """
            ).strip()

        # Add confetti library if enabled
        confetti_enabled = self.config.get("confetti", True)
        confetti_script = ""
        if confetti_enabled:
            # Use bundled confetti library (v0.12.0) instead of external CDN
            confetti_script = confetti_lib_script

        # Add configuration object for JavaScript
        show_progress = options.get("show_progress", True)
        config_script = dedent(
            f"""
            <script type="text/javascript">
            window.mkdocsQuizConfig = {{
              confetti: {str(confetti_enabled).lower()},
              showProgress: {str(show_progress).lower()}
            }};
            </script>
        """
        ).strip()

        return html + style + confetti_script + config_script + js_script + auto_number_script  # type: ignore[no-any-return]
