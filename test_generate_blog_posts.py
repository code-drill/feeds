#!/usr/bin/env python3
"""
Basic tests for generate_blog_posts.py functionality.
"""
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import shutil
from typer.testing import CliRunner

from generate_blog_posts import (
    BlogPostItem,
    parse_csv_to_objects,
    slugify,
    is_valid_to_save,
    app,
    process_csv_for_date,
    fetch_csv_data
)


class TestBlogPostItem:
    """Test BlogPostItem validation."""
    
    def test_valid_blog_post_item(self):
        """Test creating a valid BlogPostItem."""
        data = {
            "Title": "Test Article",
            "Link": "https://example.com/test",
            "Published Date": "2024-08-30T10:00:00Z",
            "Summary": "Test summary",
            "AI Category": "technical_deep_dives",
            "Source Name": "Test Blog",
            "Source URL": "https://example.com",
            "Author": "Test Author"
        }
        item = BlogPostItem(**data)
        assert item.title == "Test Article"
        assert item.link == "https://example.com/test"
        assert item.ai_category == "technical_deep_dives"
    
    def test_required_fields_validation(self):
        """Test that required fields cannot be empty."""
        with pytest.raises(ValueError):
            BlogPostItem(
                Title="",  # Empty title should fail
                Link="https://example.com/test",
                **{"Published Date": "2024-08-30T10:00:00Z"}
            )


class TestParseCsvToObjects:
    """Test CSV parsing functionality."""
    
    def test_parse_valid_csv_data(self):
        """Test parsing valid CSV data."""
        csv_data = """Title,Link,Published Date,Summary,AI Category,Source Name,Source URL,Author
Test Article,https://example.com/test,2024-08-30T10:00:00Z,Test summary,technical_deep_dives,Test Blog,https://example.com,Test Author"""
        
        items = parse_csv_to_objects(csv_data)
        assert len(items) == 1
        assert items[0].title == "Test Article"
        assert items[0].ai_category == "technical_deep_dives"
    
    def test_parse_empty_csv_data(self):
        """Test parsing empty CSV data."""
        items = parse_csv_to_objects("")
        assert len(items) == 0
    
    def test_parse_csv_with_invalid_rows(self):
        """Test parsing CSV with some invalid rows."""
        csv_data = """Title,Link,Published Date,Summary,AI Category,Source Name,Source URL,Author
Test Article,https://example.com/test,2024-08-30T10:00:00Z,Test summary,technical_deep_dives,Test Blog,https://example.com,Test Author
,https://example.com/empty,2024-08-30T10:00:00Z,Empty title,general,Test Blog,https://example.com,Test Author"""
        
        items = parse_csv_to_objects(csv_data)
        assert len(items) == 1  # Only valid row should be parsed
        assert items[0].title == "Test Article"


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_slugify_basic(self):
        """Test basic slugify functionality."""
        assert slugify("Test Article Title") == "test-article-title"
        assert slugify("Article with Special! Characters@") == "article-with-special-characters"
        assert slugify("   Multiple   Spaces   ") == "multiple-spaces"
    
    def test_is_valid_to_save(self):
        """Test validation for saving items."""
        valid_item = BlogPostItem(
            Title="Test",
            Link="https://example.com",
            **{"Published Date": "2024-08-30T10:00:00Z"},
            Summary="Test summary",
            **{"AI Category": "technical_deep_dives"}
        )
        assert is_valid_to_save(valid_item) is True
        
        # Invalid item with empty AI Category
        invalid_item = BlogPostItem(
            Title="Test",
            Link="https://example.com",
            **{"Published Date": "2024-08-30T10:00:00Z"},
            Summary="Test summary",
            **{"AI Category": ""}
        )
        assert is_valid_to_save(invalid_item) is False


class TestCLI:
    """Test CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command works."""
        result = self.runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Generate blog posts from CSV data" in result.stdout

    def test_cli_basic_run_no_crash(self):
        """Test CLI runs without crashing on basic invocation."""
        result = self.runner.invoke(app, ["generate", "--verbose"], catch_exceptions=False)
        assert result.exit_code == 0
        # CLI shows different messages based on whether args are provided
        assert "Processing" in result.stdout and "from host.docker.internal:8000" in result.stdout

    def test_cli_date_range_missing_params(self):
        """Test CLI generate command with incomplete date range parameters."""
        result = self.runner.invoke(app, ["generate", "--start-date", "2024-08-30"])
        assert result.exit_code == 1

    def test_cli_custom_host_parameter(self):
        """Test CLI accepts custom host parameter."""
        result = self.runner.invoke(app, ["generate", "--host", "localhost:3000", "--verbose"])
        assert result.exit_code == 0
        assert "localhost:3000" in result.stdout

    @patch('generate_blog_posts.fetch_csv_data')
    def test_cli_handles_fetch_errors(self, mock_fetch):
        """Test CLI handles fetch errors gracefully."""
        mock_fetch.side_effect = Exception("Network error")
        result = self.runner.invoke(app, ["generate", "2024-08-30", "--verbose"])
        assert result.exit_code == 0  # CLI doesn't crash on errors


class TestProcessingFunctions:
    """Test core processing functions."""
    
    @patch('urllib.request.urlopen')
    def test_fetch_csv_data_success(self, mock_urlopen):
        """Test successful CSV data fetch."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"Title,Link\nTest,http://example.com"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        result = fetch_csv_data("http://example.com/data.csv")
        assert result == "Title,Link\nTest,http://example.com"

    @patch('urllib.request.urlopen')
    def test_fetch_csv_data_failure(self, mock_urlopen):
        """Test CSV data fetch failure."""
        mock_urlopen.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            fetch_csv_data("http://example.com/data.csv")

    @patch('generate_blog_posts.fetch_csv_data')
    def test_process_csv_for_date_empty_data(self, mock_fetch):
        """Test processing when CSV data is empty."""
        mock_fetch.return_value = ""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            posts_dir = Path(temp_dir)
            created, processed = process_csv_for_date("http://example.com/data.csv", posts_dir)
            
            assert created == 0
            assert processed == 0

    @patch('generate_blog_posts.fetch_csv_data')
    def test_process_csv_for_date_fetch_failure(self, mock_fetch):
        """Test processing when CSV fetch fails."""
        mock_fetch.side_effect = Exception("Network error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            posts_dir = Path(temp_dir)
            created, processed = process_csv_for_date("http://example.com/data.csv", posts_dir)
            
            assert created == 0
            assert processed == 0