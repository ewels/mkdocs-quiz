"""Shared test fixtures."""

from __future__ import annotations

import pytest
from mkdocs.structure.files import Files


@pytest.fixture
def mock_files() -> Files:
    """Create a mock Files object for testing."""
    return Files([])
