"""Playwright tests for fill-in-the-blank input width behavior.

These tests require a local mkdocs server running.

To run locally:
    pip install -e ".[dev,docs]"
    playwright install chromium
    mkdocs serve --dev-addr 127.0.0.1:8765 &
    pytest tests/test_fill_blank_width.py -v
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from playwright.sync_api import Page

BASE_URL = "http://127.0.0.1:8765/mkdocs-quiz"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


class InputData(TypedDict):
    answer: str
    answer_length: int
    size: int


class WidthData(TypedDict):
    answer: str
    answer_length: int
    actual_width: float
    size: int


def test_fill_blank_input_size_varies_by_answer_length(page: Page) -> None:
    """Test that fill-in-the-blank inputs have different size attributes based on answer length.

    The input for "Paris" (5 chars) should have a smaller size than
    the input for "Guido van Rossum" (16 chars).
    """
    page.goto(f"{BASE_URL}/fill-in-blank/")
    page.wait_for_selector(".quiz-blank-input")

    # Get all fill-in-the-blank inputs on the page
    inputs = page.locator(".quiz-blank-input").all()

    # We need at least 2 inputs to compare
    assert len(inputs) >= 2, f"Expected at least 2 fill-blank inputs, found {len(inputs)}"

    # Collect size attributes and answers for analysis
    input_data: list[InputData] = []
    for input_el in inputs:
        size_attr = input_el.get_attribute("size")
        answer = input_el.get_attribute("data-answer") or ""
        input_data.append(
            {
                "answer": answer,
                "answer_length": len(answer),
                "size": int(size_attr) if size_attr else 0,
            }
        )

    print("\nInput sizes by answer length:")
    for data in sorted(input_data, key=lambda x: x["answer_length"]):
        print(
            f"  Answer: '{data['answer']}' ({data['answer_length']} chars) -> size={data['size']}"
        )

    # Find inputs with different answer lengths
    short_inputs = [d for d in input_data if d["answer_length"] <= 5]
    long_inputs = [d for d in input_data if d["answer_length"] >= 10]

    assert short_inputs, "No short answer inputs found (<=5 chars)"
    assert long_inputs, "No long answer inputs found (>=10 chars)"

    # The key assertion: longer answers should have larger size attribute
    shortest = min(short_inputs, key=lambda x: x["answer_length"])
    longest = max(long_inputs, key=lambda x: x["answer_length"])

    print("\nComparing:")
    print(
        f"  Shortest: '{shortest['answer']}' ({shortest['answer_length']} chars) = size {shortest['size']}"
    )
    print(
        f"  Longest: '{longest['answer']}' ({longest['answer_length']} chars) = size {longest['size']}"
    )

    # The longer answer's input should have a larger size
    assert longest["size"] > shortest["size"], (
        f"Expected longer answer '{longest['answer']}' to have larger size than "
        f"shorter answer '{shortest['answer']}', but got "
        f"size={longest['size']} vs size={shortest['size']}"
    )


def test_fill_blank_input_has_size_attribute(page: Page) -> None:
    """Test that fill-in-the-blank inputs have a size attribute based on answer length."""
    page.goto(f"{BASE_URL}/fill-in-blank/")
    page.wait_for_selector(".quiz-blank-input")

    # Get the first fill-blank input
    first_input = page.locator(".quiz-blank-input").first

    # Get size attribute and answer
    size_attr = first_input.get_attribute("size")
    answer = first_input.get_attribute("data-answer") or ""

    print(f"\nFirst input: answer='{answer}' ({len(answer)} chars), size={size_attr}")

    # Verify size attribute exists
    assert size_attr is not None, "Expected input to have size attribute"

    # Size should be answer length + 2 (padding), with minimum of 5
    expected_size = max(5, len(answer) + 2)
    actual_size = int(size_attr)

    print(f"  Expected size: {expected_size}")
    print(f"  Actual size: {actual_size}")

    assert actual_size == expected_size, (
        f"Expected size={expected_size} for answer '{answer}' ({len(answer)} chars), got size={actual_size}"
    )


def test_fill_blank_visual_width_comparison(page: Page) -> None:
    """Visual test comparing actual rendered widths of inputs with different answer lengths."""
    page.goto(f"{BASE_URL}/fill-in-blank/")
    page.wait_for_selector(".quiz-blank-input")

    # Create screenshot directory if needed
    SCREENSHOT_DIR.mkdir(exist_ok=True)

    # Get all inputs and their actual bounding box widths
    inputs = page.locator(".quiz-blank-input").all()

    print("\nActual rendered widths (bounding box):")
    width_data: list[WidthData] = []
    for input_el in inputs:
        answer = input_el.get_attribute("data-answer") or ""
        box = input_el.bounding_box()
        actual_width = box["width"] if box else 0.0
        size_attr = input_el.get_attribute("size") or "0"
        width_data.append(
            {
                "answer": answer,
                "answer_length": len(answer),
                "actual_width": actual_width,
                "size": int(size_attr),
            }
        )
        print(f"  '{answer}' ({len(answer)} chars): size={size_attr}, actual={actual_width:.1f}px")

    # Take a screenshot for visual verification
    page.screenshot(path=SCREENSHOT_DIR / "fill_blank_widths.png", full_page=True)
    print(f"\nScreenshot saved to {SCREENSHOT_DIR / 'fill_blank_widths.png'}")

    # Verify that actual widths differ for different answer lengths
    short_answers = [d for d in width_data if d["answer_length"] <= 5]
    long_answers = [d for d in width_data if d["answer_length"] >= 10]

    if short_answers and long_answers:
        shortest = min(short_answers, key=lambda x: x["answer_length"])
        longest = max(long_answers, key=lambda x: x["answer_length"])

        print("\nActual width comparison:")
        print(f"  Short '{shortest['answer']}': {shortest['actual_width']:.1f}px")
        print(f"  Long '{longest['answer']}': {longest['actual_width']:.1f}px")

        # The actual rendered width of longer answers should be larger
        assert longest["actual_width"] > shortest["actual_width"], (
            f"Expected longer answer to render wider: "
            f"'{longest['answer']}' ({longest['actual_width']:.1f}px) vs "
            f"'{shortest['answer']}' ({shortest['actual_width']:.1f}px)"
        )
