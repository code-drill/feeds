#!/usr/bin/env python3
"""
Basic tests for generate_blog_posts.py functionality.
"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
from typer.testing import CliRunner
from assertpy import assert_that
from mockito import mock, when, verify, unstub

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
        
        assert_that(item.title).is_equal_to("Test Article")
        assert_that(item.link).is_equal_to("https://example.com/test")
        assert_that(item.ai_category).is_equal_to("technical_deep_dives")
    
    def test_required_fields_validation(self):
        """Test that required fields cannot be empty."""
        assert_that(lambda: BlogPostItem(
            Title="",  # Empty title should fail
            Link="https://example.com/test",
            **{"Published Date": "2024-08-30T10:00:00Z"}
        )).raises(ValueError)


class TestParseCsvToObjects:
    """Test CSV parsing functionality."""
    
    def test_parse_valid_csv_data(self):
        """Test parsing valid CSV data."""
        csv_data = """Title,Link,Published Date,Summary,AI Category,Source Name,Source URL,Author
Test Article,https://example.com/test,2024-08-30T10:00:00Z,Test summary,technical_deep_dives,Test Blog,https://example.com,Test Author"""
        
        items = parse_csv_to_objects(csv_data)
        
        assert_that(items).is_length(1)
        assert_that(items[0].title).is_equal_to("Test Article")
        assert_that(items[0].ai_category).is_equal_to("technical_deep_dives")
    
    def test_parse_empty_csv_data(self):
        """Test parsing empty CSV data."""
        items = parse_csv_to_objects("")
        assert_that(items).is_empty()
    
    def test_parse_csv_with_invalid_rows(self):
        """Test parsing CSV with some invalid rows."""
        csv_data = """Title,Link,Published Date,Summary,AI Category,Source Name,Source URL,Author
Test Article,https://example.com/test,2024-08-30T10:00:00Z,Test summary,technical_deep_dives,Test Blog,https://example.com,Test Author
,https://example.com/empty,2024-08-30T10:00:00Z,Empty title,general,Test Blog,https://example.com,Test Author"""
        
        items = parse_csv_to_objects(csv_data)
        
        assert_that(items).is_length(1)  # Only valid row should be parsed
        assert_that(items[0].title).is_equal_to("Test Article")


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_slugify_basic(self):
        """Test basic slugify functionality."""
        assert_that(slugify("Test Article Title")).is_equal_to("test-article-title")
        assert_that(slugify("Article with Special! Characters@")).is_equal_to("article-with-special-characters")
        assert_that(slugify("   Multiple   Spaces   ")).is_equal_to("multiple-spaces")
    
    def test_is_valid_to_save(self):
        """Test validation for saving items."""
        valid_item = BlogPostItem(
            Title="Test",
            Link="https://example.com",
            **{"Published Date": "2024-08-30T10:00:00Z"},
            Summary="Test summary",
            **{"AI Category": "technical_deep_dives"}
        )
        assert_that(is_valid_to_save(valid_item)).is_true()
        
        # Invalid item with empty AI Category
        invalid_item = BlogPostItem(
            Title="Test",
            Link="https://example.com",
            **{"Published Date": "2024-08-30T10:00:00Z"},
            Summary="Test summary",
            **{"AI Category": ""}
        )
        assert_that(is_valid_to_save(invalid_item)).is_false()


class TestCLI:
    """Test CLI functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def teardown_method(self):
        """Clean up after each test."""
        unstub()

    def test_cli_help(self):
        """Test CLI help command works."""
        result = self.runner.invoke(app, ["generate", "--help"])
        
        assert_that(result.exit_code).is_zero()
        assert_that(result.stdout).contains("Generate blog posts from CSV data")

    def test_cli_basic_run_no_crash(self):
        """Test CLI runs without crashing on basic invocation."""
        result = self.runner.invoke(app, ["generate", "--verbose"], catch_exceptions=False)
        
        assert_that(result.exit_code).is_zero()
        assert_that(result.stdout).contains("Processing")
        assert_that(result.stdout).contains("from host.docker.internal:8000")

    def test_cli_date_range_missing_params(self):
        """Test CLI generate command with incomplete date range parameters."""
        result = self.runner.invoke(app, ["generate", "--start-date", "2024-08-30"])
        
        assert_that(result.exit_code).is_equal_to(1)

    def test_cli_custom_host_parameter(self):
        """Test CLI accepts custom host parameter."""
        result = self.runner.invoke(app, ["generate", "--host", "localhost:3000", "--verbose"])
        
        assert_that(result.exit_code).is_zero()
        assert_that(result.stdout).contains("localhost:3000")

    def test_cli_handles_fetch_errors(self):
        """Test CLI handles fetch errors gracefully."""
        # Import the module to mock its function properly
        import generate_blog_posts
        when(generate_blog_posts).fetch_csv_data(...).thenRaise(Exception("Network error"))
        
        result = self.runner.invoke(app, ["generate", "2024-08-30", "--verbose"])
        
        assert_that(result.exit_code).is_zero()  # CLI doesn't crash on errors


class TestProcessingFunctions:
    """Test core processing functions."""

    def teardown_method(self):
        """Clean up after each test."""
        unstub()
    
    def test_fetch_csv_data_success(self):
        """Test successful CSV data fetch."""
        import urllib.request
        mock_response = mock()
        when(mock_response).read().thenReturn(b"Title,Link\nTest,http://example.com")
        when(mock_response).__enter__().thenReturn(mock_response)
        when(mock_response).__exit__(...).thenReturn(None)
        when(urllib.request).urlopen("http://example.com/data.csv", timeout=30).thenReturn(mock_response)
        
        result = fetch_csv_data("http://example.com/data.csv")
        
        assert_that(result).is_equal_to("Title,Link\nTest,http://example.com")

    def test_fetch_csv_data_failure(self):
        """Test CSV data fetch failure."""
        import urllib.request
        when(urllib.request).urlopen("http://example.com/data.csv", timeout=30).thenRaise(Exception("Network error"))
        
        assert_that(lambda: fetch_csv_data("http://example.com/data.csv")).raises(Exception)

    def test_process_csv_for_date_empty_data(self):
        """Test processing when CSV data is empty."""
        import generate_blog_posts
        when(generate_blog_posts).fetch_csv_data("http://example.com/data.csv").thenReturn("")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            posts_dir = Path(temp_dir)
            created, processed = process_csv_for_date("http://example.com/data.csv", posts_dir)
            
            assert_that(created).is_zero()
            assert_that(processed).is_zero()

    def test_process_csv_for_date_fetch_failure(self):
        """Test processing when CSV fetch fails."""
        import generate_blog_posts
        when(generate_blog_posts).fetch_csv_data("http://example.com/data.csv").thenRaise(Exception("Network error"))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            posts_dir = Path(temp_dir)
            created, processed = process_csv_for_date("http://example.com/data.csv", posts_dir)
            
            assert_that(created).is_zero()
            assert_that(processed).is_zero()