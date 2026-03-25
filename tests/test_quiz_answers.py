"""Playwright tests for quiz answer validation.

These tests verify that selecting correct answers marks the quiz as correct,
and selecting incorrect answers marks it as incorrect. This catches regressions
like the mouseup auto-submit bug where all answers were marked wrong.

To run locally:
    pip install -e ".[dev,docs]"
    playwright install chromium
    mkdocs serve --dev-addr 127.0.0.1:8765 &
    pytest tests/test_quiz_answers.py -v
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from playwright.sync_api import Page

BASE_URL = "http://127.0.0.1:8765/mkdocs-quiz"


@pytest.fixture(autouse=True)
def clear_local_storage(page: Page) -> None:
    """Clear localStorage before each test to avoid persisted quiz state."""
    page.goto(BASE_URL)
    page.evaluate("window.localStorage.clear()")


class TestSingleChoiceAutoSubmit:
    """Tests for single-choice (radio button) quizzes with auto-submit enabled."""

    def test_correct_answer_marked_correct(self, page: Page) -> None:
        """Selecting the correct radio button should mark the quiz as correct."""
        page.goto(f"{BASE_URL}/multiple-choice/")
        page.wait_for_selector(".quiz")

        # First quiz: "What is the answer to the following sum? 2+2" -> correct answer is "4"
        quiz = page.locator(".quiz").first
        fieldset = quiz.locator("fieldset")

        # Find the correct answer input (has data-correct attribute)
        correct_input = fieldset.locator('input[data-correct="true"]')
        correct_input.click()

        # Wait for auto-submit feedback to appear
        feedback = quiz.locator(".quiz-feedback")
        feedback.wait_for(state="visible", timeout=3000)

        # Should show correct feedback
        assert quiz.locator(".quiz-feedback .correct").count() > 0, (
            "Expected correct feedback after selecting the right answer"
        )

    def test_wrong_answer_marked_incorrect(self, page: Page) -> None:
        """Selecting a wrong radio button should mark the quiz as incorrect."""
        page.goto(f"{BASE_URL}/multiple-choice/")
        page.wait_for_selector(".quiz")

        quiz = page.locator(".quiz").first
        fieldset = quiz.locator("fieldset")

        # Find an incorrect answer input (no data-correct attribute)
        wrong_input = fieldset.locator('input[name="answer"]:not([data-correct])').first
        wrong_input.click()

        # Wait for auto-submit feedback
        feedback = quiz.locator(".quiz-feedback")
        feedback.wait_for(state="visible", timeout=3000)

        # Should show incorrect feedback
        assert quiz.locator(".quiz-feedback .incorrect").count() > 0, (
            "Expected incorrect feedback after selecting the wrong answer"
        )


class TestMultipleChoiceSubmit:
    """Tests for multiple-choice (checkbox) quizzes with explicit submit."""

    def test_all_correct_answers_marked_correct(self, page: Page) -> None:
        """Selecting all correct checkboxes and submitting should be correct."""
        page.goto(f"{BASE_URL}/multiple-choice/")
        page.wait_for_selector(".quiz")

        # Find a checkbox quiz (second quiz: "Which of these are even numbers?")
        quizzes = page.locator(".quiz").all()
        checkbox_quiz = None
        for q in quizzes:
            if q.locator('input[type="checkbox"]').count() > 0:
                checkbox_quiz = q
                break

        assert checkbox_quiz is not None, "No checkbox quiz found on the page"

        fieldset = checkbox_quiz.locator("fieldset")

        # Check all correct answers
        correct_inputs = fieldset.locator('input[data-correct="true"]').all()
        assert len(correct_inputs) > 0, "No correct answers found"
        for inp in correct_inputs:
            inp.check()

        # Submit the form
        submit_btn = checkbox_quiz.locator('button[type="submit"]')
        submit_btn.click()

        # Should show correct feedback
        feedback = checkbox_quiz.locator(".quiz-feedback")
        feedback.wait_for(state="visible", timeout=3000)
        assert checkbox_quiz.locator(".quiz-feedback .correct").count() > 0, (
            "Expected correct feedback when all correct checkboxes selected"
        )

    def test_partial_correct_answers_marked_incorrect(self, page: Page) -> None:
        """Selecting only some correct checkboxes should be incorrect."""
        page.goto(f"{BASE_URL}/multiple-choice/")
        page.wait_for_selector(".quiz")

        quizzes = page.locator(".quiz").all()
        checkbox_quiz = None
        for q in quizzes:
            if q.locator('input[type="checkbox"]').count() > 0:
                checkbox_quiz = q
                break

        assert checkbox_quiz is not None, "No checkbox quiz found"

        fieldset = checkbox_quiz.locator("fieldset")

        # Check only the first correct answer (not all)
        correct_inputs = fieldset.locator('input[data-correct="true"]').all()
        assert len(correct_inputs) > 1, "Need multiple correct answers for this test"
        correct_inputs[0].check()

        # Submit
        submit_btn = checkbox_quiz.locator('button[type="submit"]')
        submit_btn.click()

        feedback = checkbox_quiz.locator(".quiz-feedback")
        feedback.wait_for(state="visible", timeout=3000)
        assert checkbox_quiz.locator(".quiz-feedback .incorrect").count() > 0, (
            "Expected incorrect feedback when only some correct answers selected"
        )


class TestFillInTheBlank:
    """Tests for fill-in-the-blank quizzes."""

    def test_correct_fill_in_blank(self, page: Page) -> None:
        """Typing the correct answer should mark fill-in-blank as correct."""
        page.goto(f"{BASE_URL}/fill-in-blank/")
        page.wait_for_selector(".quiz")

        quiz = page.locator(".quiz").first
        blank_input = quiz.locator(".quiz-blank-input").first

        # Get the correct answer from data-answer attribute
        correct_answer = blank_input.get_attribute("data-answer")
        assert correct_answer, "Expected data-answer attribute on blank input"

        # Type the correct answer
        blank_input.fill(correct_answer)

        # Submit
        submit_btn = quiz.locator('button[type="submit"]')
        submit_btn.click()

        feedback = quiz.locator(".quiz-feedback")
        feedback.wait_for(state="visible", timeout=3000)
        assert quiz.locator(".quiz-feedback .correct").count() > 0, (
            f"Expected correct feedback after typing '{correct_answer}'"
        )

    def test_wrong_fill_in_blank(self, page: Page) -> None:
        """Typing a wrong answer should mark fill-in-blank as incorrect."""
        page.goto(f"{BASE_URL}/fill-in-blank/")
        page.wait_for_selector(".quiz")

        quiz = page.locator(".quiz").first
        blank_input = quiz.locator(".quiz-blank-input").first

        # Type a clearly wrong answer
        blank_input.fill("definitely_wrong_answer_xyz")

        # Submit
        submit_btn = quiz.locator('button[type="submit"]')
        submit_btn.click()

        feedback = quiz.locator(".quiz-feedback")
        feedback.wait_for(state="visible", timeout=3000)
        assert quiz.locator(".quiz-feedback .incorrect").count() > 0, (
            "Expected incorrect feedback after typing wrong answer"
        )

    def test_case_insensitive_fill_in_blank(self, page: Page) -> None:
        """Fill-in-blank answers should be case insensitive."""
        page.goto(f"{BASE_URL}/fill-in-blank/")
        page.wait_for_selector(".quiz")

        quiz = page.locator(".quiz").first
        blank_input = quiz.locator(".quiz-blank-input").first

        correct_answer = blank_input.get_attribute("data-answer")
        assert correct_answer, "Expected data-answer attribute"

        # Type the answer in different case
        blank_input.fill(correct_answer.upper())

        submit_btn = quiz.locator('button[type="submit"]')
        submit_btn.click()

        feedback = quiz.locator(".quiz-feedback")
        feedback.wait_for(state="visible", timeout=3000)
        assert quiz.locator(".quiz-feedback .correct").count() > 0, (
            f"Expected correct feedback for case-insensitive match of '{correct_answer}'"
        )
