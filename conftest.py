#!/usr/bin/env python3
"""
Shared test fixtures and configuration for the test suite.
"""
import pytest
from pathlib import Path
import tempfile
from typer.testing import CliRunner
from assertpy import assert_that
from mockito import mock, when, verify, unstub

# Common test data
SAMPLE_CSV_DATA = """Title,Link,Published Date,Summary,AI Category,Source Name,Source URL,Author
Test Article,https://example.com/test,2024-08-30T10:00:00Z,Test summary content,technical_deep_dives,Test Blog,https://example.com,Test Author
Another Article,https://example.com/test2,2024-08-30T11:00:00Z,Another summary,general,Test Blog,https://example.com,Test Author"""

VALID_BLOG_POST_DATA = {
    "Title": "Test Article",
    "Link": "https://example.com/test",
    "Published Date": "2024-08-30T10:00:00Z",
    "Summary": "Test summary",
    "AI Category": "technical_deep_dives",
    "Source Name": "Test Blog",
    "Source URL": "https://example.com",
    "Author": "Test Author"
}


@pytest.fixture
def cli_runner():
    """Fixture providing a CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_csv_data():
    """Fixture providing sample CSV data."""
    return SAMPLE_CSV_DATA


@pytest.fixture
def valid_blog_post_data():
    """Fixture providing valid blog post data."""
    return VALID_BLOG_POST_DATA.copy()


@pytest.fixture
def temp_posts_dir():
    """Fixture providing a temporary posts directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(autouse=True)
def cleanup_mocks():
    """Automatically clean up mocks after each test."""
    yield
    unstub()