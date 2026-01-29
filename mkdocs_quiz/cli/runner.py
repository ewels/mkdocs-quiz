"""Interactive quiz runner for the terminal."""

from __future__ import annotations

import random
import re
from typing import TYPE_CHECKING

import questionary
from rich.console import Console, ConsoleOptions, RenderResult
from rich.markdown import Markdown
from rich.measure import Measurement
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from rich.rule import Rule
from rich.segment import Segment
from rich.style import StyleType

if TYPE_CHECKING:
    from ..qti.models import Quiz

console = Console()


def get_score_color(percentage: float) -> str:
    """Get the Rich color style for a score percentage.

    Args:
        percentage: Score percentage (0-100).

    Returns:
        Color name: 'green' for >= 80%, 'yellow' for >= 60%, 'red' otherwise.
    """
    if percentage >= 80:
        return "green"
    if percentage >= 60:
        return "yellow"
    return "red"


# =============================================================================
# Digits renderable for big number display
# Extracted from Textual (MIT License) and simplified.
# Source: https://github.com/Textualize/textual/blob/main/src/textual/renderables/digits.py
# =============================================================================

# fmt: off
DIGIT_CHARS = {
    " ": ("   ", "   ", "   "),
    "0": ("╭─╮", "│ │", "╰─╯"),
    "1": ("╶╮ ", " │ ", "╶┴╴"),
    "2": ("╶─╮", "┌─┘", "╰─╴"),
    "3": ("╶─╮", " ─┤", "╶─╯"),
    "4": ("╷ ╷", "╰─┤", "  ╵"),
    "5": ("╭─╴", "╰─╮", "╶─╯"),
    "6": ("╭─╴", "├─╮", "╰─╯"),
    "7": ("╶─┐", "  │", "  ╵"),
    "8": ("╭─╮", "├─┤", "╰─╯"),
    "9": ("╭─╮", "╰─┤", "╶─╯"),
    "/": ("  ╱", " ╱ ", "╱  "),  # noqa: RUF001
    "%": ("○ ╱", " ╱  ", "╱ ○ "),  # noqa: RUF001
}
# fmt: on


class Digits:
    """Renders numbers in tall 3-row unicode characters."""

    def __init__(self, text: str, style: StyleType = "") -> None:
        self._text = text
        self._style = style

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        style = console.get_style(self._style)
        rows: list[list[str]] = [[], [], []]

        for char in self._text:
            if char in DIGIT_CHARS:
                for i, part in enumerate(DIGIT_CHARS[char]):
                    rows[i].append(part)

        for row in rows:
            yield Segment("".join(row), style)
            yield Segment.line()

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        width = sum(len(DIGIT_CHARS[c][0]) for c in self._text if c in DIGIT_CHARS)
        return Measurement(width, width)


# =============================================================================
# Text processing utilities
# =============================================================================


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text for terminal display.

    Args:
        text: Text potentially containing HTML tags.

    Returns:
        Text with HTML tags removed.
    """
    import html

    # Remove HTML tags, then decode entities
    clean = re.sub(r"<[^>]+>", "", text)
    return html.unescape(clean).strip()


def strip_inline_highlight_syntax(text: str) -> str:
    """Strip Material for MkDocs inline code highlight syntax.

    Material uses `#!python code()` for inline syntax highlighting.
    Rich doesn't support this, so we strip the `#!language ` prefix.

    Args:
        text: Text potentially containing inline highlight syntax.

    Returns:
        Text with inline highlight syntax removed.
    """
    # Pattern matches `#!language code` and replaces with just `code`
    # The shebang must be at the start of inline code
    return re.sub(r"`#!\w+\s+", "`", text)


def expand_anchor_links(text: str, source_file: str | None) -> str:
    """Expand anchor-only links to include the source file path.

    Converts [text](#anchor) to [text](source_file#anchor) so that
    the link destination is visible in the terminal.

    Args:
        text: Markdown text potentially containing anchor-only links.
        source_file: The source file path to prepend to anchor links.

    Returns:
        Text with expanded anchor links.
    """
    if not source_file:
        return text

    # Pattern matches [text](#anchor) but not [text](url#anchor)
    # Captures: group 1 = link text, group 2 = anchor (including #)
    def replace_anchor(match: re.Match[str]) -> str:
        link_text = match.group(1)
        anchor = match.group(2)
        return f"[{link_text}]({source_file}{anchor})"

    return re.sub(r"\[([^\]]+)\]\((#[^)]+)\)", replace_anchor, text)


def shorten_path(path: str) -> str:
    """Shorten a file path for display as relative to cwd.

    Args:
        path: The file path to shorten.

    Returns:
        Shortened path relative to cwd, with ./ prefix if not starting with ../
    """
    import os
    from pathlib import Path

    if not Path(path).is_absolute():
        return path

    relative = os.path.relpath(path)
    return relative if relative.startswith("..") else "./" + relative


def strip_wrapping_backticks(text: str) -> str:
    """Strip backticks if the entire text is wrapped in them.

    Only removes backticks when the whole string is a single inline code span.
    Does not affect text with backticks in the middle.

    Args:
        text: Text potentially wrapped in backticks.

    Returns:
        Text with wrapping backticks removed, or original text.
    """
    stripped = text.strip()
    # Check if entire text is wrapped in backticks (single inline code span)
    if stripped.startswith("`") and stripped.endswith("`") and stripped.count("`") == 2:
        return stripped[1:-1]
    return text


def clean_markdown(text: str, source_file: str | None = None) -> str:
    """Clean markdown text for terminal rendering.

    Strips HTML tags and Material-specific syntax that Rich doesn't support.

    Args:
        text: Markdown text to clean.
        source_file: Optional source file path for expanding anchor links.

    Returns:
        Cleaned markdown text.
    """
    clean_text = strip_html_tags(text)
    clean_text = strip_inline_highlight_syntax(clean_text)
    clean_text = expand_anchor_links(clean_text, source_file)
    clean_text = strip_wrapping_backticks(clean_text)
    return clean_text


# =============================================================================
# Admonition rendering
# =============================================================================

# Admonition type to Rich style mapping
# Format: admon_type -> (border_style, title_style)
ADMONITION_STYLES: dict[str, tuple[str, str]] = {
    "note": ("blue", "bold blue"),
    "abstract": ("cyan", "bold cyan"),
    "summary": ("cyan", "bold cyan"),
    "info": ("blue", "bold blue"),
    "tip": ("green", "bold green"),
    "hint": ("green", "bold green"),
    "success": ("green", "bold green"),
    "check": ("green", "bold green"),
    "question": ("yellow", "bold yellow"),
    "help": ("yellow", "bold yellow"),
    "warning": ("yellow", "bold yellow"),
    "caution": ("yellow", "bold yellow"),
    "attention": ("yellow", "bold yellow"),
    "danger": ("red", "bold red"),
    "error": ("red", "bold red"),
    "failure": ("red", "bold red"),
    "bug": ("red", "bold red"),
    "example": ("magenta", "bold magenta"),
    "quote": ("dim", "bold"),
    "cite": ("dim", "bold"),
}


def render_admonitions(text: str) -> list[Markdown | Panel]:
    """Parse and render Material admonitions as Rich panels.

    Handles both regular (!!!) and collapsible (??? and ???+) admonitions.

    Args:
        text: Text potentially containing admonition blocks.

    Returns:
        List of Rich renderables (Text, Markdown, Panel objects).
    """
    # Pattern for admonitions: !!! type "optional title" followed by indented content
    pattern = r'^(!{3}|\?{3}\+?) (\w+)(?: "([^"]*)")?\n((?:    .+(?:\n|$))+)'

    renderables: list[Markdown | Panel] = []
    last_end = 0

    for match in re.finditer(pattern, text, re.MULTILINE):
        # Add any text before this admonition
        before_text = text[last_end : match.start()].strip()
        if before_text:
            renderables.append(Markdown(before_text))

        _marker, admon_type, title, content = match.groups()
        # Remove 4-space indent from content
        content = re.sub(r"^    ", "", content, flags=re.MULTILINE).strip()

        # Get style for this admonition type
        border_style, title_style = ADMONITION_STYLES.get(admon_type.lower(), ("blue", "bold blue"))

        # Use custom title or default to type name
        display_title = title if title else admon_type.title()

        # Render content as markdown inside the panel
        panel = Panel(
            Markdown(content),
            title=f"[{title_style}]{display_title}[/{title_style}]",
            title_align="left",
            border_style=border_style,
        )
        renderables.append(panel)

        last_end = match.end()

    # Add any remaining text after the last admonition
    after_text = text[last_end:].strip()
    if after_text:
        renderables.append(Markdown(after_text))

    # If no admonitions found, just return the text as markdown
    if not renderables:
        result: list[Markdown | Panel] = [Markdown(text)]
        return result

    return renderables


def render_markdown_with_admonitions(text: str) -> None:
    """Render markdown text with admonition support.

    Args:
        text: Markdown text to render.
    """
    renderables = render_admonitions(text)
    for item in renderables:
        console.print(item)


# =============================================================================
# Quiz display functions
# =============================================================================


def display_question_header(question_num: int, total: int, correct: int, answered: int) -> None:
    """Display the question header with progress information.

    Args:
        question_num: Current question number (1-indexed).
        total: Total number of questions.
        correct: Number of correct answers so far.
        answered: Number of questions answered so far.
    """
    score_text = f"  Score: {correct}/{answered}" if answered > 0 else ""
    with Progress(
        TextColumn("Question {task.completed} of {task.total}"),
        BarColumn(bar_width=30, complete_style="bar.complete", finished_style="bar.complete"),
        TaskProgressColumn(),
        TextColumn(score_text),
        console=console,
        transient=False,
    ) as progress:
        progress.add_task("", total=total, completed=question_num)


def _print_with_border(text: str, border_style: str) -> None:
    """Print text with a colored left border.

    Args:
        text: The text to print (can contain newlines).
        border_style: The Rich style for the border (e.g., 'green', 'red').
    """
    for line in text.split("\n"):
        console.print(f"[{border_style}]▎[/{border_style}] {line}")


def display_feedback(
    is_correct: bool,
    correct_answer: str | list[str] | None = None,
    content: str | None = None,
    source_file: str | None = None,
) -> None:
    """Display feedback after answering a question.

    Args:
        is_correct: Whether the answer was correct.
        correct_answer: The correct answer(s) to display if wrong.
        content: Optional explanation content to display.
        source_file: Optional source file path for expanding anchor links.
    """
    console.print()

    # Print the correct/incorrect status line with colored border
    if is_correct:
        _print_with_border("[green]✓ Correct[/green]", "green")
    else:
        if correct_answer:
            if isinstance(correct_answer, list):
                answer_text = (
                    correct_answer[0] if len(correct_answer) == 1 else ", ".join(correct_answer)
                )
            else:
                answer_text = correct_answer
            # Clean the answer text (strip HTML, highlight syntax, etc.)
            answer_text = clean_markdown(answer_text, source_file)
            _print_with_border(
                f"[red]✗ Incorrect[/red] — [italic]Correct answer:[/italic] {answer_text}", "red"
            )
        else:
            _print_with_border("[red]✗ Incorrect[/red]", "red")

    # Show content/explanation as a separate blockquote below (rendered as markdown)
    if content and content.strip():
        console.print()
        clean_content = clean_markdown(content, source_file).strip()
        # Check if content has admonitions - if so, render directly
        if re.search(r"^(!{3}|\?{3}\+?) \w+", clean_content, re.MULTILINE):
            render_markdown_with_admonitions(clean_content)
        else:
            # Render as blockquote markdown
            blockquote_content = "> " + clean_content.replace("\n", "\n> ")
            console.print(Markdown(blockquote_content))

    # Wait for user to press Enter before continuing
    console.print()
    console.input("[dim]Press Enter to continue, Ctrl+C to exit...[/dim]")

    # Add spacing between questions
    console.print()
    console.print()
    console.print(Rule(style="dim"))
    console.print()
    console.print()


# =============================================================================
# Quiz runner functions
# =============================================================================


def run_multiple_choice_quiz(quiz: Quiz, shuffle: bool = False) -> tuple[bool, list[str]]:
    """Run a multiple-choice quiz interactively.

    Args:
        quiz: The Quiz object to run.
        shuffle: Whether to shuffle the answer order.

    Returns:
        Tuple of (is_correct, correct_answer_texts).
    """
    # Get source file path as string for link expansion
    source_file = str(quiz.source_file) if quiz.source_file else None

    # Display question as markdown with admonition support
    question_text = clean_markdown(quiz.question, source_file)
    console.print()
    render_markdown_with_admonitions(question_text)
    console.print()

    # Prepare choices
    answers = list(quiz.answers)
    if shuffle:
        random.shuffle(answers)

    # Create choice labels (questionary adds its own numbering)
    # Note: questionary can't render markdown, so we clean the text for plain display
    choices = []
    for answer in answers:
        answer_text = clean_markdown(answer.text, source_file)
        choices.append(questionary.Choice(title=answer_text, value=answer))

    # Determine if single or multiple choice
    correct_answers = quiz.correct_answers
    is_multiple = len(correct_answers) > 1

    if is_multiple:
        # Multiple choice - use checkboxes
        selected = questionary.checkbox(
            "Select all correct answers:",
            choices=choices,
            instruction="(Space to select, Enter to submit)",
        ).unsafe_ask()

        # Check if all correct answers are selected and no incorrect ones
        selected_texts = {a.text for a in selected}
        correct_texts = {a.text for a in correct_answers}
        is_correct = selected_texts == correct_texts
    else:
        # Single choice - use select
        selected = questionary.select(
            "Select your answer:",
            choices=choices,
            instruction="(Number/arrows to select, Enter to submit)",
            use_shortcuts=True,
        ).unsafe_ask()

        is_correct = selected.is_correct

    # Get correct answer text for feedback
    correct_answer_texts = [strip_html_tags(a.text) for a in correct_answers]

    return is_correct, correct_answer_texts


def run_fill_in_blank_quiz(quiz: Quiz) -> tuple[bool, list[str]]:
    """Run a fill-in-the-blank quiz interactively.

    Args:
        quiz: The Quiz object to run.

    Returns:
        Tuple of (is_correct, correct_answers).
    """
    from io import StringIO

    from rich.text import Text

    # Get source file path as string for link expansion
    source_file = str(quiz.source_file) if quiz.source_file else None

    # Display question with blanks shown as styled placeholders
    question_text = clean_markdown(quiz.question, source_file)
    num_blanks = len(quiz.blanks)

    # Use unique placeholder that survives markdown rendering
    PLACEHOLDER = "XBLANKPLACEHOLDERX{}X"

    def make_blank_label(index: int) -> str:
        return "[BLANK]" if num_blanks == 1 else f"[BLANK {index + 1}]"

    # Replace [[answer]] and {{BLANK_N}} formats with placeholders
    display_text = question_text
    blank_index = 0
    while re.search(r"\[\[[^\]]+\]\]", display_text):
        display_text = re.sub(
            r"\[\[[^\]]+\]\]", PLACEHOLDER.format(blank_index), display_text, count=1
        )
        blank_index += 1
    for i in range(num_blanks):
        display_text = display_text.replace(f"{{{{BLANK_{i}}}}}", PLACEHOLDER.format(i))

    # Render markdown to capture string (preserves code blocks, formatting)
    string_io = StringIO()
    temp_console = Console(file=string_io, force_terminal=True, width=console.width)
    if re.search(r"^(!{3}|\?{3}\+?) \w+", display_text, re.MULTILINE):
        for item in render_admonitions(display_text):
            temp_console.print(item)
    else:
        temp_console.print(Markdown(display_text))

    # Replace placeholders with styled blank labels
    result = Text.from_ansi(string_io.getvalue())
    for i in range(num_blanks):
        placeholder = PLACEHOLDER.format(i)
        label = f" {make_blank_label(i)} "
        while placeholder in result.plain:
            start = result.plain.find(placeholder)
            styled_blank = Text(label, style="magenta on black")
            before, after = result[:start], result[start + len(placeholder) :]
            result = Text()
            result.append_text(before)
            result.append_text(styled_blank)
            result.append_text(after)

    console.print()
    result.rstrip()  # Modifies in-place
    console.print(result)
    console.print()

    # Prompt for each blank
    user_answers = []
    all_correct = True

    for i, blank in enumerate(quiz.blanks):
        prompt = "Your answer" if num_blanks == 1 else f"Blank {i + 1}"
        answer = questionary.text(f"{prompt}:").unsafe_ask()

        user_answers.append(answer)

        # Normalize for comparison (case-insensitive, trimmed)
        normalized_user = answer.strip().lower()
        normalized_correct = blank.correct_answer.strip().lower()

        if normalized_user != normalized_correct:
            all_correct = False

    # Get correct answers for feedback
    correct_answers = [blank.correct_answer for blank in quiz.blanks]

    return all_correct, correct_answers


def run_single_quiz(quiz: Quiz, shuffle: bool = False) -> bool:
    """Run a single quiz and return whether it was answered correctly.

    Args:
        quiz: The Quiz object to run.
        shuffle: Whether to shuffle answer order (multiple-choice only).

    Returns:
        True if the answer was correct, False otherwise.
    """
    if quiz.is_fill_in_blank:
        is_correct, correct_answers = run_fill_in_blank_quiz(quiz)
    else:
        is_correct, correct_answers = run_multiple_choice_quiz(quiz, shuffle=shuffle)

    # Get source file path as string for link expansion
    source_file = str(quiz.source_file) if quiz.source_file else None

    # Display feedback
    display_feedback(
        is_correct,
        correct_answer=correct_answers if not is_correct else None,
        content=quiz.content,
        source_file=source_file,
    )

    return is_correct


def _print_previous_result(quiz_path: str | None) -> None:
    """Print previous result info if available.

    Args:
        quiz_path: Path to the quiz file for history lookup.
    """
    if not quiz_path:
        return

    from .history import format_time_ago, get_previous_result

    previous = get_previous_result(quiz_path)
    if previous:
        time_ago = format_time_ago(previous.datetime)
        console.print()
        console.print(
            f"You last did this quiz [bold]{time_ago}[/bold] "
            f"and got [bold]{previous.correct}/{previous.total}[/bold] "
            f"([bold]{previous.percentage:.0f}%[/bold])"
        )


def display_quiz_header(quiz_path: str | None = None) -> None:
    """Display the quiz header with branding and previous results.

    Args:
        quiz_path: Optional path to the quiz file for history lookup.
    """
    from rich.text import Text

    # Header with branding
    header = Text()
    header.append("mkdocs-quiz", style="bold blue")
    header.append(" • ", style="dim")
    header.append(
        "https://github.com/ewels/mkdocs-quiz",
        style="dim link https://github.com/ewels/mkdocs-quiz",
    )

    console.print()
    console.print(header)
    _print_previous_result(quiz_path)

    console.print()
    console.print(Rule(style="dim"))
    console.print()


def display_running_quiz(quiz_path: str) -> None:
    """Display the 'Running quiz' message before starting.

    Args:
        quiz_path: Path to the quiz file being run.
    """
    display_path = shorten_path(quiz_path)
    console.print()
    console.print(f"[bold]Running quiz:[/bold] [cyan]{display_path}[/cyan]")
    _print_previous_result(quiz_path)

    console.print()
    console.print(Rule(style="dim"))
    console.print()
    console.print()


def run_quiz_session(
    quizzes: list[Quiz],
    shuffle_questions: bool = False,
    shuffle_answers: bool = False,
    quiz_path: str | None = None,
    show_header: bool = True,
) -> tuple[int, int]:
    """Run an interactive quiz session.

    Args:
        quizzes: List of Quiz objects to run.
        shuffle_questions: Whether to randomize question order.
        shuffle_answers: Whether to randomize answer order.
        quiz_path: Optional path to the quiz file for history tracking.
        show_header: Whether to show the quiz header (set False if already shown).

    Returns:
        Tuple of (correct_count, total_count).
    """
    if not quizzes:
        console.print("[yellow]No quizzes found.[/yellow]")
        return 0, 0

    # Optionally shuffle questions
    if shuffle_questions:
        quizzes = list(quizzes)  # Make a copy
        random.shuffle(quizzes)

    total = len(quizzes)
    correct = 0
    answered = 0

    # Display header with branding and previous results (unless already shown)
    if show_header:
        display_quiz_header(quiz_path)

    # Show which quiz is being run
    if quiz_path:
        display_running_quiz(quiz_path)

    for i, quiz in enumerate(quizzes):
        # Display header
        display_question_header(i + 1, total, correct, answered)

        # Run the quiz
        is_correct = run_single_quiz(quiz, shuffle=shuffle_answers)
        # Track answered separately from enumerate index since we need it for display
        answered += 1  # noqa: SIM113
        if is_correct:
            correct += 1

    return correct, total


def display_final_results(correct: int, total: int, quiz_path: str | None = None) -> None:
    """Display the final quiz results and save to history.

    Args:
        correct: Number of correct answers.
        total: Total number of questions.
        quiz_path: Optional path to the quiz file for history saving.
    """
    if total == 0:
        return

    # Get previous result before saving new one (for comparison display)
    previous_result = None
    if quiz_path:
        from .history import get_previous_result, save_result

        previous_result = get_previous_result(quiz_path)
        save_result(quiz_path, correct, total)

    incorrect = total - correct
    percentage = (correct / total) * 100
    color = get_score_color(percentage)

    # Determine message based on score
    if percentage >= 80:
        message = "Excellent work!"
    elif percentage >= 60:
        message = "Good job!"
    else:
        message = "Keep practicing!"

    # Build the panel content (centered)
    from rich.align import Align
    from rich.console import Group
    from rich.text import Text

    # Score label
    score_label = Text("Score:\n", style="bold")

    # Big score display
    score_digits = Digits(f"{correct}/{total}", style=color)

    # Additional info
    info = Text(justify="center")
    info.append(f"\n{percentage:.0f}%\n\n", style=f"bold {color}")
    info.append(f"✓ Correct:   {correct}\n", style="green")
    info.append(f"✗ Incorrect: {incorrect}\n\n", style="red")
    info.append(message)
    info.append("\n\n")

    # Show comparison with previous result if available
    if previous_result:
        from .history import format_time_ago

        diff = correct - previous_result.correct
        time_ago = format_time_ago(previous_result.datetime)
        if diff > 0:
            info.append(f"↑ +{diff} vs last attempt", style="bold green")
        elif diff < 0:
            info.append(f"↓ {diff} vs last attempt", style="bold red")
        else:
            info.append("Same as last attempt")
        info.append(f" ({previous_result.correct}/{previous_result.total}, {time_ago})")
        info.append("\n")

    info.append("Tip: Run ", style="dim")
    info.append("mkdocs-quiz history", style="dim bold")
    info.append(" to see all your past results", style="dim")
    info.append("\n")

    content = Group(
        Align.center(score_label),
        Align.center(score_digits),
        Align.center(info),
    )

    # Build panel with quiz path in footer if available
    subtitle = f"[cyan]{shorten_path(quiz_path)}[/cyan]" if quiz_path else None

    console.print()
    console.print(
        Panel(
            content,
            title="Quiz Complete!",
            title_align="left",
            subtitle=subtitle,
            subtitle_align="right",
            border_style="blue",
        )
    )
    console.print()
