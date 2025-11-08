"""MkDocs Quiz Plugin - Main plugin module."""

from __future__ import annotations

import logging
import re
from importlib import resources as impresources
from pathlib import Path
from textwrap import dedent
from typing import Any

import markdown as md
from mkdocs.config import config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from . import css, js

log = logging.getLogger("mkdocs.plugins.mkdocs_quiz")

# Load CSS and JS resources at module level
try:
    inp_file = impresources.files(css) / "quiz.css"
    with inp_file.open("rt") as f:
        style = f.read()
    style = f'<style type="text/css">{style}</style>'

    js_file = impresources.files(js) / "quiz.js"
    with js_file.open("rt") as f:
        js_content = f.read()
    js_script = f'<script type="text/javascript" defer>{js_content}</script>'
except Exception as e:
    log.error(f"Failed to load CSS/JS resources: {e}")
    style = ""
    js_script = ""

# Initialize markdown converter for inline content (questions and answers)
markdown_converter = md.Markdown(extensions=["extra", "codehilite", "toc"])

# Quiz tag format:
# <?quiz?>
# Are you ready?
# - [x] Yes!
# - [ ] No!
# - [ ] Maybe!
#
# Optional content section (supports full markdown)
# Can include **bold**, *italic*, `code`, etc.
# <?/quiz?>

QUIZ_START_TAG = "<?quiz?>"
QUIZ_END_TAG = "<?/quiz?>"
QUIZ_REGEX = r"<\?quiz\?>(.*?)<\?/quiz\?>"


def convert_inline_markdown(text: str) -> str:
    """Convert markdown to HTML for inline content (questions/answers).

    Args:
        text: The markdown text to convert.

    Returns:
        The HTML string with wrapping <p> tags removed.
    """
    # Reset the converter state
    markdown_converter.reset()
    html = markdown_converter.convert(text)
    # Remove wrapping <p> tags for inline content
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]
    return html


class MkDocsQuizPlugin(BasePlugin):
    """MkDocs plugin to create interactive quizzes in markdown documents."""

    config_scheme = (
        ("enabled_by_default", config_options.Type(bool, default=True)),
        ("auto_number", config_options.Type(bool, default=False)),
        ("question_tag", config_options.Type(str, default="h4")),
        ("show_correct", config_options.Type(bool, default=True)),
        ("auto_submit", config_options.Type(bool, default=True)),
        ("disable_after_submit", config_options.Type(bool, default=True)),
    )

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        # Store quiz HTML for each page to be injected later
        self._quiz_storage: dict[str, dict[str, str]] = {}

    def on_env(self, env, config, files):
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
            return quiz_meta.get("enabled", enabled_by_default)

        # No page-level override, use plugin default
        return enabled_by_default

    def _get_quiz_options(self, page: Page) -> dict[str, bool | str]:
        """Get quiz options from page frontmatter or plugin config.

        Args:
            page: The current page object.

        Returns:
            Dictionary with show_correct, auto_submit, disable_after_submit, auto_number, and question_tag options.
        """
        # Start with plugin defaults
        options = {
            "show_correct": self.config.get("show_correct", True),
            "auto_submit": self.config.get("auto_submit", True),
            "disable_after_submit": self.config.get("disable_after_submit", True),
            "auto_number": self.config.get("auto_number", False),
            "question_tag": self.config.get("question_tag", "h4"),
        }

        # Override with page-level settings if present
        quiz_meta = page.meta.get("quiz")
        if isinstance(quiz_meta, dict):
            options.update({k: v for k, v in quiz_meta.items() if k in options})

        return options

    def _parse_quiz_answers(
        self, quiz_lines: list[str], start_index: int = 1
    ) -> tuple[list[str], list[str], int]:
        """Parse quiz answers from quiz lines.

        Args:
            quiz_lines: The lines of the quiz content.
            start_index: The index to start parsing from (default: 1, after question).

        Returns:
            A tuple of (all_answers, correct_answers, content_start_index).
        """
        all_answers = []
        correct_answers = []
        content_start_index = start_index

        for i, line in enumerate(quiz_lines[start_index:], start=start_index):
            # Check if this is a checkbox list item: - [x], - [X], - [ ], or - []
            match = re.match(r"^- \[([xX ]?)\] (.*)$", line)
            if match:
                checkbox_content = match.group(1)
                is_correct = checkbox_content.lower() == "x"
                answer_text = match.group(2)
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

        return all_answers, correct_answers, content_start_index

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

            answer_html = (
                f'<div><input type="{input_type}" name="answer" value="{i}" '
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

        # Mask code blocks to prevent processing quiz tags inside them
        masked_markdown, placeholders = self._mask_code_blocks(markdown)

        # Process quizzes and replace with placeholders
        quiz_id = 0
        options = self._get_quiz_options(page)

        # Process in reverse to maintain string positions
        matches = list(re.finditer(QUIZ_REGEX, masked_markdown, re.DOTALL))
        for match in reversed(matches):
            try:
                # Generate quiz HTML
                quiz_html = self._process_quiz(match.group(1), quiz_id, options)

                # Create a markdown-safe placeholder
                # Using a format that won't be affected by markdown processing
                placeholder = f"<!-- MKDOCS_QUIZ_PLACEHOLDER_{quiz_id} -->"

                # Store the quiz HTML for later injection
                self._quiz_storage[page_key][placeholder] = quiz_html

                # Replace quiz tag with placeholder
                masked_markdown = (
                    masked_markdown[: match.start()] + placeholder + masked_markdown[match.end() :]
                )

                quiz_id += 1
            except Exception as e:
                log.error(f"Failed to process quiz {quiz_id}: {e}")
                quiz_id += 1
                continue

        # Restore code blocks
        markdown = self._unmask_code_blocks(masked_markdown, placeholders)

        return markdown

    def _process_quiz(self, quiz_content: str, quiz_id: int, options: dict[str, bool | str]) -> str:
        """Process a single quiz and convert it to HTML.

        Args:
            quiz_content: The content inside the quiz tags.
            quiz_id: The unique ID for this quiz.
            options: Quiz options (show_correct, auto_submit, disable_after_submit, auto_number, question_tag).

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

        # First line is the question
        question = quiz_lines[0]
        question = convert_inline_markdown(question)

        # Get question_tag from options
        question_tag = options["question_tag"]

        # Parse answers
        all_answers, correct_answers, content_start_index = self._parse_quiz_answers(quiz_lines)

        if not all_answers:
            raise ValueError("Quiz must have at least one answer")
        if not correct_answers:
            raise ValueError("Quiz must have at least one correct answer")

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
            markdown_converter.reset()
            content_html = markdown_converter.convert(content_text)

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

        quiz_html = dedent(f"""
            <div class="quiz" {attrs}>
                <{question_tag} id="{quiz_header_id}">
                    {question}
                    <a href="#{quiz_header_id}" class="quiz-header-link">#</a>
                </{question_tag}>
                <form>
                    <fieldset>{answers_html}</fieldset>
                    <div class="quiz-feedback hidden"></div>
                    {submit_button}
                </form>
                <section class="content hidden">{content_html}</section>
            </div>
        """).strip()

        return quiz_html

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

        # Get quiz options to check auto_number setting
        options = self._get_quiz_options(page)

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

        return html + style + js_script + auto_number_script
