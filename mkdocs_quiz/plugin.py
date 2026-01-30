"""MkDocs Quiz Plugin - Main plugin module."""

from __future__ import annotations

import fnmatch
import html
import json
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

from .parsing import (
    FILL_BLANK_REGEX,
    OLD_SYNTAX_PATTERNS,
    find_quizzes,
    mask_code_blocks,
    unmask_code_blocks,
)
from .translations import TranslationManager

# Compatibility import for Python 3.8
if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

from . import css, js

log = logging.getLogger("mkdocs.plugins.mkdocs_quiz")

# Load CSS and JS resources at module level
style: str
js_script: str
confetti_lib_script: str

try:
    inp_file = files(css) / "quiz.css"
    with inp_file.open("r") as f:
        style_content = f.read()
    style = f'<style type="text/css">{style_content}</style>'

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


def get_markdown_converter(config: MkDocsConfig | None = None) -> md.Markdown:
    """Get or create a thread-local markdown converter instance.

    When config is provided, uses the same markdown extensions configured
    in mkdocs.yml. This enables features like pymdownx.superfences,
    pymdownx.highlight with line highlighting, etc.

    Args:
        config: Optional MkDocs config to get markdown extensions from.
                If None or no extensions configured, falls back to basic extensions.

    Returns:
        A thread-local Markdown converter instance.
    """
    # Default extensions used when no config is provided or config has no extensions
    default_extensions = ["extra", "codehilite", "toc"]

    # Compute a cache key based on the extensions configured
    if config is not None and config.markdown_extensions:
        # Get extensions from mkdocs config (user has explicitly configured them)
        extensions = config.markdown_extensions
        extension_configs = config.mdx_configs or {}
        # Create a hashable key for cache comparison
        cache_key = (
            tuple(extensions),
            tuple(sorted(extension_configs.keys())) if extension_configs else (),
        )
    else:
        # Fallback to basic extensions when no config or no extensions configured
        extensions = default_extensions
        extension_configs = {}
        cache_key = (tuple(extensions), ())

    # Check if we need to recreate the converter (different config)
    if (
        not hasattr(_markdown_converter_local, "converter")
        or getattr(_markdown_converter_local, "cache_key", None) != cache_key
    ):
        _markdown_converter_local.converter = md.Markdown(
            extensions=extensions, extension_configs=extension_configs
        )
        _markdown_converter_local.cache_key = cache_key

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
#
# Fill-in-the-blank format:
# <quiz>
# 2 + 2 = [[4]]
#
# ---
# Optional content section
# </quiz>
#
# Note: Asterisk bullets (* [x], * [ ]) are also supported.
# Quiz patterns are defined in parsing.py


def convert_inline_markdown(text: str, config: MkDocsConfig | None = None) -> str:
    """Convert markdown to HTML for inline content (questions/answers).

    Uses the same markdown extensions configured in mkdocs.yml when config
    is provided, enabling features like syntax highlighting in code blocks.

    Args:
        text: The markdown text to convert.
        config: Optional MkDocs config to get markdown extensions from.

    Returns:
        The HTML string with wrapping <p> tags removed.
    """
    # Reset the converter state
    converter = get_markdown_converter(config)
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
        ("shuffle_answers", config_options.Type(bool, default=False)),
        ("show_progress", config_options.Type(bool, default=True)),
        ("confetti", config_options.Type(bool, default=True)),
        ("progress_sidebar_position", config_options.Type(str, default="top")),
        ("embed_source", config_options.Type(bool, default=True)),
        # Translation options
        ("language", config_options.Type((str, type(None)), default=None)),
        ("custom_translations", config_options.Type(dict, default={})),
        ("language_patterns", config_options.Type(list, default=[])),
    )

    def __init__(self) -> None:
        """Initialize the plugin."""
        super().__init__()
        # Store quiz HTML for each page to be injected later
        self._quiz_storage: dict[str, dict[str, dict[str, str]]] = {}
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

            log.debug("mkdocs-quiz: Added template overrides for quiz progress")

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
            Dictionary with show_correct, auto_submit, disable_after_submit, auto_number,
            shuffle_answers, and show_progress options.
        """
        # Start with plugin defaults
        options = {
            "show_correct": self.config.get("show_correct", True),
            "auto_submit": self.config.get("auto_submit", True),
            "disable_after_submit": self.config.get("disable_after_submit", True),
            "auto_number": self.config.get("auto_number", False),
            "shuffle_answers": self.config.get("shuffle_answers", False),
            "show_progress": self.config.get("show_progress", True),
        }

        # Override with page-level settings if present
        quiz_meta = page.meta.get("quiz")
        if isinstance(quiz_meta, dict):
            options.update({k: v for k, v in quiz_meta.items() if k in options})

        return options

    def _get_translation_manager(self, page: Page, config: MkDocsConfig) -> TranslationManager:
        """Get translation manager for the current page.

        Language resolution order (later overrides earlier):
        1. Default: 'en'
        2. theme.language from MkDocs config
        3. extra.alternate - detect active language from page URL
        4. mkdocs_quiz.language config
        5. mkdocs_quiz.language_patterns pattern matching
        6. Page frontmatter quiz.language (highest priority)

        Args:
            page: The current page object.
            config: The MkDocs config object.

        Returns:
            TranslationManager instance for the resolved language.
        """
        # 1. Start with default
        language = "en"

        # 2. Check theme.language
        if hasattr(config, "theme") and "language" in config.theme:
            theme_lang = config.theme["language"]
            if theme_lang:
                language = theme_lang
                log.debug(f"Using theme.language: {language}")

        # 3. Check extra.alternate for multi-language sites (longest prefix match)
        if hasattr(config, "extra") and "alternate" in config.extra:
            page_url = page.url or page.file.url
            best_match = ("", None)  # (normalized_link, lang)
            for alt in config.extra["alternate"]:
                link, lang = alt.get("link", ""), alt.get("lang")
                prefix = link.lstrip("/") if link else ""
                # Skip root "/" (empty after lstrip) - matches everything
                if (
                    prefix
                    and lang
                    and page_url.startswith(prefix)
                    and len(prefix) > len(best_match[0])
                ):
                    best_match = (prefix, lang)
            if best_match[1]:
                language = best_match[1]
                log.debug(f"Matched extra.alternate '{best_match[0]}' for {page_url}: {language}")

        # 4. Check mkdocs_quiz.language config (only if explicitly set by user)
        plugin_language = self.config.get("language")
        if plugin_language is not None:
            language = plugin_language
            log.debug(f"Using mkdocs_quiz.language config: {language}")

        # 5. Check pattern matching
        if self.config.get("language_patterns"):
            for pattern_config in self.config["language_patterns"]:
                pattern = pattern_config.get("pattern", "")
                if pattern and fnmatch.fnmatch(page.file.src_path, pattern):
                    language = pattern_config.get("language")
                    log.debug(
                        f"Matched pattern '{pattern}' for {page.file.src_path}, using language: {language}"
                    )
                    break

        # 6. Check page frontmatter for language override (highest priority)
        quiz_meta = page.meta.get("quiz", {})
        if isinstance(quiz_meta, dict) and quiz_meta.get("language"):
            language = quiz_meta["language"]
            log.debug(f"Using page frontmatter language: {language}")

        # Get custom translation path for this language
        custom_translations = self.config.get("custom_translations", {})
        custom_path = None
        if custom_trans_path := custom_translations.get(language):
            # Resolve path relative to mkdocs.yml (config file directory)
            config_dir = Path(config.config_file_path).parent
            custom_path = config_dir / custom_trans_path

        return TranslationManager(language, custom_path)

    def _parse_quiz_question_and_answers(
        self, quiz_lines: list[str], config: MkDocsConfig | None = None
    ) -> tuple[str, list[str], list[str], int]:
        """Parse quiz question and answers from quiz lines.

        The question is everything up to the first checkbox answer.
        Answers are checkbox items (- [x], - [ ], * [x], or * [ ]).
        Content is everything after the last answer.

        Args:
            quiz_lines: The lines of the quiz content.
            config: Optional MkDocs config to get markdown extensions from.

        Returns:
            A tuple of (question_text, all_answers, correct_answers, content_start_index).
        """
        # Find the first answer line and validate checkbox format
        first_answer_index = None
        for i, line in enumerate(quiz_lines):
            # Check if this looks like a checkbox list item (any character in brackets)
            # Supports both hyphen (-) and asterisk (*) bullets
            checkbox_check = re.match(r"^[-*] \[(.?)\] (.*)$", line)
            if checkbox_check:
                checkbox_content = checkbox_check.group(1)
                # Strictly validate: only accept x, X, space, or empty
                if checkbox_content not in ["x", "X", " ", ""]:
                    raise ValueError(
                        f"Invalid checkbox format: '[{checkbox_content}]'. "
                        f"Only '[x]', '[X]', '[ ]', or '[]' are allowed (with - or * bullet). "
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
            # Supports both hyphen (-) and asterisk (*) bullets
            checkbox_pattern = re.match(r"^[-*] \[(.?)\] (.*)$", line)
            if checkbox_pattern:
                checkbox_content = checkbox_pattern.group(1)
                # Strictly validate: only accept x, X, space, or empty
                if checkbox_content not in ["x", "X", " ", ""]:
                    raise ValueError(
                        f"Invalid checkbox format: '[{checkbox_content}]'. "
                        f"Only '[x]', '[X]', '[ ]', or '[]' are allowed (with - or * bullet). "
                        f"Found in line: {line}"
                    )
                is_correct = checkbox_content.lower() == "x"
                answer_text = checkbox_pattern.group(2)
                answer_html = convert_inline_markdown(answer_text, config)
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

    def _is_fill_in_blank_quiz(self, quiz_content: str) -> bool:
        """Check if quiz contains fill-in-the-blank patterns.

        Args:
            quiz_content: The content inside the quiz tags.

        Returns:
            True if the quiz contains [[answer]] patterns, False otherwise.
        """
        return bool(re.search(FILL_BLANK_REGEX, quiz_content))

    def _process_fill_in_blank_quiz(
        self,
        quiz_content: str,
        quiz_id: int,
        options: dict[str, bool],
        t: TranslationManager,
        config: MkDocsConfig | None = None,
    ) -> str:
        """Process a fill-in-the-blank quiz.

        Args:
            quiz_content: The content inside the quiz tags.
            quiz_id: The unique ID for this quiz.
            options: Quiz options (show_correct, auto_submit, disable_after_submit, auto_number).
            t: Translation manager for this page.
            config: Optional MkDocs config to get markdown extensions from.

        Returns:
            The HTML representation of the fill-in-the-blank quiz.

        Raises:
            ValueError: If the quiz format is invalid.
        """
        # Dedent the quiz content to handle indented quizzes
        quiz_content = dedent(quiz_content)

        # Extract all correct answers and their positions
        answers = []
        answer_positions = []

        for match in re.finditer(FILL_BLANK_REGEX, quiz_content):
            answers.append(match.group(1).strip())
            answer_positions.append((match.start(), match.end()))

        if not answers:
            raise ValueError("Fill-in-the-blank quiz must have at least one blank")

        # Split content into question and content sections
        # Look for a horizontal rule (---) to separate question from content
        lines = quiz_content.split("\n")
        question_lines = []
        content_start_index = len(lines)

        # Find the first horizontal rule (---)
        for i, line in enumerate(lines):
            if line.strip() == "---":
                # Found separator, everything before is question, everything after is content
                question_lines = lines[:i]
                content_start_index = i + 1
                break

        # If no horizontal rule found, everything is the question
        if not question_lines:
            question_lines = lines
            content_start_index = len(lines)

        question_text = "\n".join(question_lines)

        # Replace [[answer]] patterns with input fields
        input_counter = 0

        def replace_with_input(match: re.Match[str]) -> str:
            nonlocal input_counter
            answer = match.group(1).strip()
            input_id = f"quiz-{quiz_id}-blank-{input_counter}"
            # Store the correct answer as a data attribute, HTML-escaped
            escaped_answer = html.escape(answer)
            # Calculate input size based on answer length (min 5 chars, add padding for typing)
            input_size = max(5, len(answer) + 2)
            input_html = (
                f'<input type="text" class="quiz-blank-input" '
                f'id="{input_id}" data-answer="{escaped_answer}" autocomplete="off" '
                f'size="{input_size}">'
            )
            input_counter += 1
            return input_html

        # Convert question markdown to HTML first, but preserve [[...]] patterns temporarily
        # by replacing them with placeholders
        placeholders = {}
        placeholder_counter = 0

        def create_placeholder(match: re.Match[str]) -> str:
            nonlocal placeholder_counter
            # Use HTML comment as placeholder - won't be affected by markdown
            placeholder = f"<!--BLANK_PLACEHOLDER_{placeholder_counter}-->"
            placeholders[placeholder] = match.group(0)
            placeholder_counter += 1
            return placeholder

        # Replace blanks with placeholders before markdown conversion
        question_with_placeholders = re.sub(FILL_BLANK_REGEX, create_placeholder, question_text)

        # Convert markdown to HTML using configured markdown extensions
        question_html = convert_inline_markdown(question_with_placeholders, config)

        # Now replace placeholders with actual input fields
        for placeholder, original in placeholders.items():
            blank_match: re.Match[str] | None = re.match(FILL_BLANK_REGEX, original)
            if blank_match:
                input_html = replace_with_input(blank_match)
                question_html = question_html.replace(placeholder, input_html)

        # Get content section
        content_lines = lines[content_start_index:]
        content_html = ""
        if content_lines and any(line.strip() for line in content_lines):
            content_text = "\n".join(content_lines)
            # Use configured markdown extensions for content section
            converter = get_markdown_converter(config)
            converter.reset()
            content_html = converter.convert(content_text)

        # Build data attributes
        data_attrs = ['data-quiz-type="fill-blank"']
        if options["show_correct"]:
            data_attrs.append('data-show-correct="true"')
        if options["disable_after_submit"]:
            data_attrs.append('data-disable-after-submit="true"')
        attrs = " ".join(data_attrs)

        # Generate quiz ID for linking
        quiz_header_id = f"quiz-{quiz_id}"

        # If auto_number is enabled, add a header with the question number
        question_header = ""
        if options["auto_number"]:
            question_number = quiz_id + 1
            question_text = t.get("Question {n}", n=question_number)
            question_header = f'<h4 class="quiz-number">{question_text}</h4>'

        # Get translated submit button text
        submit_text = t.get("Submit")

        quiz_html = dedent(f"""
            <div class="quiz quiz-fill-blank" {attrs} id="{quiz_header_id}">
                <a href="#{quiz_header_id}" class="quiz-header-link">#</a>
                {question_header}
                <div class="quiz-question">
                    {question_html}
                </div>
                <form action="javascript:void(0);" onsubmit="return false;">
                    <div class="quiz-feedback hidden"></div>
                    <button type="submit" class="quiz-button">{submit_text}</button>
                </form>
                <section class="content hidden">{content_html}</section>
            </div>
        """).strip()

        return quiz_html

    def _generate_answer_html(
        self,
        all_answers: list[str],
        correct_answers: list[str],
        quiz_id: int,
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

    def _check_for_old_syntax(self, markdown: str, page: Page) -> None:
        """Check if the page contains old v0.x quiz syntax and fail with helpful error.

        Args:
            markdown: The markdown content to check.
            page: The current page object.

        Raises:
            ValueError: If old syntax is detected, with migration instructions.
        """
        # Check for old quiz tags
        for pattern in OLD_SYNTAX_PATTERNS:
            if re.search(pattern, markdown):
                error_msg = dedent(
                    f"""
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    ###########  ERROR: Old mkdocs-quiz syntax detected: {page.file.src_path}
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    Quiz syntax used by mkdocs-quiz changed in the v1 release!
                    Please use the CLI migration tool to update your quizzes:

                        mkdocs-quiz migrate docs/

                    Read more: https://ewels.github.io/mkdocs-quiz/migration/
                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    """
                ).strip()
                raise ValueError(error_msg)

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
        masked_markdown, placeholders = mask_code_blocks(markdown)

        # Check for old v1.x syntax after masking code blocks
        # This prevents false positives from documentation examples in code blocks
        self._check_for_old_syntax(masked_markdown, page)

        # Process quizzes and replace with placeholders
        options = self._get_quiz_options(page)
        translation_manager = self._get_translation_manager(page, config)

        # Find all quiz matches
        matches = find_quizzes(masked_markdown)

        # Build replacement segments efficiently (O(n) instead of O(n²))
        segments = []
        last_end = 0

        for quiz_id, match in enumerate(matches):
            try:
                # Get the original quiz content (for embed_source)
                original_quiz_content = match.group(0)  # Full <quiz>...</quiz> tag

                # Generate quiz HTML
                quiz_html = self._process_quiz(
                    match.group(1), quiz_id, options, translation_manager, config
                )

                # Create a markdown-safe placeholder
                placeholder = f"<!-- MKDOCS_QUIZ_PLACEHOLDER_{quiz_id} -->"

                # Store the quiz HTML and original content for later injection
                self._quiz_storage[page_key][placeholder] = {
                    "html": quiz_html,
                    "source": original_quiz_content,
                }

                # Add the text before this match and the placeholder
                segments.append(masked_markdown[last_end : match.start()])
                segments.append(placeholder)
                last_end = match.end()

            except ValueError as e:
                # Re-raise ValueError with additional context to help identify the problematic quiz
                # Calculate line number by finding the quiz in the original markdown
                # (match position is in masked_markdown which has different offsets)
                quiz_tag = f"<quiz>{match.group(1)}</quiz>"
                original_pos = markdown.find(quiz_tag)
                if original_pos >= 0:
                    line_number = markdown[:original_pos].count("\n") + 1
                else:
                    # Fallback: use masked markdown position (may be approximate)
                    line_number = masked_markdown[: match.start()].count("\n") + 1

                # Get a preview of the quiz content (first 60 chars, single line)
                quiz_preview = match.group(1).strip()[:60].replace("\n", " ")
                if len(match.group(1).strip()) > 60:
                    quiz_preview += "..."

                # Build helpful error message
                error_msg = (
                    f"Error in quiz #{quiz_id + 1} in {page.file.src_path} "
                    f"(line {line_number}): {e}\n"
                    f"  Quiz preview: {quiz_preview}"
                )
                raise ValueError(error_msg) from e
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
        markdown = unmask_code_blocks(masked_markdown, placeholders)

        return markdown

    def _process_quiz(
        self,
        quiz_content: str,
        quiz_id: int,
        options: dict[str, bool],
        t: TranslationManager,
        config: MkDocsConfig | None = None,
    ) -> str:
        """Process a single quiz and convert it to HTML.

        Args:
            quiz_content: The content inside the quiz tags.
            quiz_id: The unique ID for this quiz.
            options: Quiz options (show_correct, auto_submit, disable_after_submit, auto_number).
            t: Translation manager for this page.
            config: Optional MkDocs config to get markdown extensions from.

        Returns:
            The HTML representation of the quiz.

        Raises:
            ValueError: If the quiz format is invalid.
        """
        # Check if this is a fill-in-the-blank quiz
        if self._is_fill_in_blank_quiz(quiz_content):
            return self._process_fill_in_blank_quiz(quiz_content, quiz_id, options, t, config)

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
            self._parse_quiz_question_and_answers(quiz_lines, config)
        )

        # Validate quiz structure
        if not question_text.strip():
            raise ValueError("Quiz must have a question")
        if not all_answers:
            raise ValueError("Quiz must have at least one answer")
        if not correct_answers:
            raise ValueError("Quiz must have at least one correct answer")

        # Convert question markdown to HTML (supports multi-line questions with markdown)
        converter = get_markdown_converter(config)
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
            converter = get_markdown_converter(config)
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
        if options["shuffle_answers"]:
            data_attrs.append('data-shuffle-answers="true"')
        attrs = " ".join(data_attrs)

        # Hide submit button only if auto-submit is enabled AND it's a single-choice quiz
        # For multiple-choice (checkboxes), always show the submit button
        submit_text = t.get("Submit")
        submit_button = (
            ""
            if options["auto_submit"] and not as_checkboxes
            else f'<button type="submit" class="quiz-button">{submit_text}</button>'
        )
        # Generate quiz ID for linking
        quiz_header_id = f"quiz-{quiz_id}"
        answers_html = "".join(answer_html_list)

        # If auto_number is enabled, add a header with the question number
        question_header = ""
        if options["auto_number"]:
            # quiz_id is 0-indexed, so add 1 for display
            question_number = quiz_id + 1
            question_text = t.get("Question {n}", n=question_number)
            question_header = f'<h4 class="quiz-number">{question_text}</h4>'

        quiz_html = dedent(f"""
            <div class="quiz" {attrs} id="{quiz_header_id}">
                <a href="#{quiz_header_id}" class="quiz-header-link">#</a>
                {question_header}
                <div class="quiz-question">
                    {question}
                </div>
                <form action="javascript:void(0);" onsubmit="return false;">
                    <fieldset>{answers_html}</fieldset>
                    <div class="quiz-feedback hidden"></div>
                    {submit_button}
                </form>
                <section class="content hidden">{content_html}</section>
            </div>
        """).strip()

        return quiz_html

    def _generate_results_html(self, t: TranslationManager) -> str:
        """Generate HTML for the quiz results end screen.

        Args:
            t: Translation manager for this page.

        Returns:
            The HTML representation of the results div.
        """
        quiz_progress_text = t.get("Quiz Progress")
        questions_answered_text = t.get("questions answered")
        correct_text = t.get("correct")
        quiz_complete_text = t.get("Quiz Complete!")
        reset_quiz_text = t.get("Reset quiz")

        results_html = dedent(
            f"""
            <div id="quiz-results" class="quiz-results">
                <div class="quiz-results-progress">
                    <h3>{quiz_progress_text}</h3>
                    <p class="quiz-results-stats">
                        <span class="quiz-results-answered">0</span> / <span class="quiz-results-total">0</span> {questions_answered_text}
                        (<span class="quiz-results-percentage">0%</span>)
                    </p>
                    <p class="quiz-results-correct-stats">
                        <span class="quiz-results-correct">0</span> {correct_text}
                    </p>
                </div>
                <div class="quiz-results-complete hidden">
                    <h2 class="quiz-results-title">{quiz_complete_text}</h2>
                    <div class="quiz-results-score-display">
                        <span class="quiz-results-score-value">0%</span>
                    </div>
                    <p class="quiz-results-message"></p>
                    <button type="button" class="md-button md-button--primary quiz-results-reset">{reset_quiz_text}</button>
                </div>
            </div>
        """
        ).strip()
        return results_html

    def _generate_intro_html(self, t: TranslationManager) -> str:
        """Generate HTML for the quiz intro text with reset button.

        Args:
            t: Translation manager for this page.

        Returns:
            The HTML representation of the intro div.
        """
        intro_text = t.get(
            "Quiz results are saved to your browser's local storage and will persist between sessions."
        )
        reset_quiz_text = t.get("Reset quiz")

        intro_html = dedent(
            f"""
            <div class="quiz-intro">
                <p>{intro_text}</p>
                <button type="button" class="md-button quiz-intro-reset">{reset_quiz_text}</button>
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
        embed_source = self.config.get("embed_source", True)

        if page_key in self._quiz_storage:
            for placeholder, quiz_data in self._quiz_storage[page_key].items():
                quiz_html = quiz_data["html"]

                # Optionally embed the original quiz source as an HTML comment
                # This allows CLI tools to extract quiz content from rendered pages
                if embed_source:
                    source_comment = f"<!-- mkdocs-quiz-source\n{quiz_data['source']}\n-->\n"
                    quiz_html = source_comment + quiz_html

                html = html.replace(placeholder, quiz_html)

            # Clean up storage for this page
            del self._quiz_storage[page_key]

        # Get quiz options to check settings
        options = self._get_quiz_options(page)

        # Get translation manager for this page
        translation_manager = self._get_translation_manager(page, config)

        # Handle results div if present
        if self._has_results_div.get(page_key, False):
            results_html = self._generate_results_html(translation_manager)
            html = html.replace("<!-- mkdocs-quiz results -->", results_html)
            # Clean up
            del self._has_results_div[page_key]

        # Handle intro if present
        if self._has_intro.get(page_key, False):
            intro_html = self._generate_intro_html(translation_manager)
            html = html.replace("<!-- mkdocs-quiz intro -->", intro_html)
            # Clean up
            del self._has_intro[page_key]

        # Add auto-numbering class if enabled
        auto_number_script: str = ""
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
        confetti_script: str = ""
        if confetti_enabled:
            # Use bundled confetti library (v0.12.0) instead of external CDN
            confetti_script = confetti_lib_script

        # Inject translations as JavaScript object
        translations_json = json.dumps(translation_manager.to_dict(), ensure_ascii=False)
        translations_script: str = dedent(
            f"""
            <script type="text/javascript">
            window.mkdocsQuizTranslations = {translations_json};
            </script>
        """
        ).strip()

        # Add configuration object for JavaScript
        show_progress = options.get("show_progress", True)
        progress_sidebar_position = self.config.get("progress_sidebar_position", "top")
        config_script: str = dedent(
            f"""
            <script type="text/javascript">
            window.mkdocsQuizConfig = {{
              confetti: {str(confetti_enabled).lower()},
              showProgress: {str(show_progress).lower()},
              progressSidebarPosition: "{progress_sidebar_position}"
            }};
            </script>
        """
        ).strip()

        return (
            html
            + style
            + confetti_script
            + translations_script
            + config_script
            + js_script
            + auto_number_script
        )
