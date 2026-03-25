"""Shared test fixtures and helpers."""

from __future__ import annotations

import re

import pytest
from mkdocs.structure.files import Files


def strip_injected_assets(html: str) -> str:
    """Remove inline <script> and <style> tags from HTML for clean attribute counting."""
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    return html


def strip_source_comments(html: str) -> str:
    """Remove <!-- mkdocs-quiz-source ... --> comments from HTML."""
    return re.sub(r"<!-- mkdocs-quiz-source\n.*?\n-->", "", html, flags=re.DOTALL)


@pytest.fixture
def mock_files() -> Files:
    """Create a mock Files object for testing."""
    return Files([])
