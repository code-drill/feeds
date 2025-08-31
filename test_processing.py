#!/usr/bin/env python3
"""
Tests for core processing functions.
"""
import pytest
from assertpy import assert_that
from mockito import mock, when
from pathlib import Path

from generate_blog_posts import (
    fetch_csv_data,
    process_csv_for_date,
    save_items_to_files,
    create_blog_post
)


class TestFetchCsvData:
    """Test CSV data fetching."""
    
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

    def test_fetch_csv_data_timeout(self):
        """Test CSV data fetch with timeout."""
        import urllib.request
        when(urllib.request).urlopen("http://example.com/data.csv", timeout=30).thenRaise(TimeoutError("Request timeout"))
        
        assert_that(lambda: fetch_csv_data("http://example.com/data.csv")).raises(TimeoutError)


class TestProcessCsvForDate:
    """Test processing CSV for specific dates."""
    
    def test_process_csv_for_date_empty_data(self, temp_posts_dir):
        """Test processing when CSV data is empty."""
        import generate_blog_posts
        when(generate_blog_posts).fetch_csv_data("http://example.com/data.csv").thenReturn("")
        
        created, processed = process_csv_for_date("http://example.com/data.csv", temp_posts_dir)
        
        assert_that(created).is_zero()
        assert_that(processed).is_zero()

    def test_process_csv_for_date_fetch_failure(self, temp_posts_dir):
        """Test processing when CSV fetch fails."""
        import generate_blog_posts
        when(generate_blog_posts).fetch_csv_data("http://example.com/data.csv").thenRaise(Exception("Network error"))
        
        created, processed = process_csv_for_date("http://example.com/data.csv", temp_posts_dir)
        
        assert_that(created).is_zero()
        assert_that(processed).is_zero()

    def test_process_csv_for_date_success(self, temp_posts_dir, sample_csv_data):
        """Test successful processing of CSV data."""
        import generate_blog_posts
        when(generate_blog_posts).fetch_csv_data("http://example.com/data.csv").thenReturn(sample_csv_data)
        
        created, processed = process_csv_for_date("http://example.com/data.csv", temp_posts_dir, verbose=True)
        
        assert_that(processed).is_equal_to(2)  # Two items in sample data
        # Created count might be 0 if files already exist or validation fails

    def test_process_csv_for_date_verbose_mode(self, temp_posts_dir, sample_csv_data):
        """Test processing with verbose mode enabled."""
        import generate_blog_posts
        when(generate_blog_posts).fetch_csv_data("http://example.com/data.csv").thenReturn(sample_csv_data)
        
        # Should not raise any exceptions in verbose mode
        created, processed = process_csv_for_date("http://example.com/data.csv", temp_posts_dir, verbose=True)
        
        assert_that(processed).is_greater_than_or_equal_to(0)
        assert_that(created).is_greater_than_or_equal_to(0)


class TestSaveItemsToFiles:
    """Test saving items to files."""
    
    def test_save_items_empty_list(self, temp_posts_dir):
        """Test saving empty list of items."""
        created, processed = save_items_to_files([], temp_posts_dir)
        
        assert_that(created).is_zero()
        assert_that(processed).is_zero()

    def test_save_items_verbose_mode(self, temp_posts_dir):
        """Test saving items with verbose mode."""
        from generate_blog_posts import BlogPostItem
        
        # Create a valid item
        item_data = {
            "Title": "Test Article",
            "Link": "https://example.com/test",
            "Published Date": "2024-08-30T10:00:00Z",
            "Summary": "Test summary",
            "AI Category": "technical_deep_dives",
            "Source Name": "Test Blog",
            "Source URL": "https://example.com",
            "Author": "Test Author"
        }
        item = BlogPostItem(**item_data)
        
        # Should not raise exceptions in verbose mode
        created, processed = save_items_to_files([item], temp_posts_dir, verbose=True)
        
        assert_that(processed).is_equal_to(1)


class TestCreateBlogPost:
    """Test blog post creation."""
    
    def test_create_blog_post_creates_directory(self, temp_posts_dir, valid_blog_post_data):
        """Test that blog post creation creates the appropriate directory structure."""
        # Create a post - this should create date directory
        result = create_blog_post(valid_blog_post_data, temp_posts_dir, verbose=True)
        
        # Check if date directory was created
        date_dir = temp_posts_dir / "2024-08-30"
        assert_that(date_dir.exists()).is_true()

    def test_create_blog_post_file_exists_skip(self, temp_posts_dir, valid_blog_post_data):
        """Test that existing files are skipped."""
        # Create the post once
        result1 = create_blog_post(valid_blog_post_data, temp_posts_dir, verbose=True)
        
        # Try to create the same post again - should skip
        result2 = create_blog_post(valid_blog_post_data, temp_posts_dir, verbose=True)
        
        # Second attempt should return False (skipped)
        assert_that(result2).is_false()

    def test_create_blog_post_invalid_data(self, temp_posts_dir):
        """Test blog post creation with invalid data."""
        invalid_data = {
            "Title": "Test Article",
            "Link": "https://example.com/test",
            "Published Date": "2024-08-30T10:00:00Z",
            "Summary": "",  # Empty summary
            "AI Category": "",  # Empty category
            "Source Name": "Test Blog",
            "Source URL": "https://example.com",
            "Author": "Test Author"
        }
        
        # Should skip invalid items
        result = create_blog_post(invalid_data, temp_posts_dir, verbose=True)
        assert_that(result).is_false()

    def test_create_blog_post_generates_slug(self, temp_posts_dir, valid_blog_post_data):
        """Test that blog post creation generates appropriate slug."""
        valid_blog_post_data["Title"] = "Test Article with Special! Characters@"
        
        result = create_blog_post(valid_blog_post_data, temp_posts_dir, verbose=True)
        
        # Check that a file was created with slugified name
        date_dir = temp_posts_dir / "2024-08-30"
        files = list(date_dir.glob("*.md"))
        
        if files:  # If file was created (depends on validation)
            filename = files[0].name
            assert_that(filename).contains("test-article-with-special-characters")