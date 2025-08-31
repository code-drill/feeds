#!/usr/bin/env python3
"""
Tests for CSV parsing functionality.
"""
import pytest
from assertpy import assert_that

from generate_blog_posts import parse_csv_to_objects


class TestParseCsvToObjects:
    """Test CSV parsing functionality."""
    
    def test_parse_valid_csv_data(self, sample_csv_data):
        """Test parsing valid CSV data."""
        items = parse_csv_to_objects(sample_csv_data)
        
        assert_that(items).is_length(2)
        assert_that(items[0].title).is_equal_to("Test Article")
        assert_that(items[0].ai_category).is_equal_to("technical_deep_dives")
        assert_that(items[1].title).is_equal_to("Another Article")
        assert_that(items[1].ai_category).is_equal_to("general")
    
    def test_parse_empty_csv_data(self):
        """Test parsing empty CSV data."""
        items = parse_csv_to_objects("")
        assert_that(items).is_empty()
        
        items = parse_csv_to_objects(None)
        assert_that(items).is_empty()
    
    def test_parse_csv_with_invalid_rows(self):
        """Test parsing CSV with some invalid rows."""
        csv_data = """Title,Link,Published Date,Summary,AI Category,Source Name,Source URL,Author
Test Article,https://example.com/test,2024-08-30T10:00:00Z,Test summary,technical_deep_dives,Test Blog,https://example.com,Test Author
,https://example.com/empty,2024-08-30T10:00:00Z,Empty title,general,Test Blog,https://example.com,Test Author"""
        
        items = parse_csv_to_objects(csv_data)
        
        assert_that(items).is_length(1)  # Only valid row should be parsed
        assert_that(items[0].title).is_equal_to("Test Article")

    def test_parse_csv_with_headers_only(self):
        """Test parsing CSV with only headers."""
        csv_data = "Title,Link,Published Date,Summary,AI Category,Source Name,Source URL,Author"
        
        items = parse_csv_to_objects(csv_data)
        assert_that(items).is_empty()

    def test_parse_csv_with_missing_columns(self):
        """Test parsing CSV with missing required columns."""
        csv_data = """Title,Link
Test Article,https://example.com/test"""
        
        items = parse_csv_to_objects(csv_data)
        assert_that(items).is_empty()  # Should fail validation due to missing Published Date

    def test_parse_csv_verbose_mode(self):
        """Test parsing CSV in verbose mode."""
        csv_data = """Title,Link,Published Date,Summary,AI Category,Source Name,Source URL,Author
Test Article,https://example.com/test,2024-08-30T10:00:00Z,Test summary,technical_deep_dives,Test Blog,https://example.com,Test Author
,https://example.com/empty,2024-08-30T10:00:00Z,Empty title,general,Test Blog,https://example.com,Test Author"""
        
        # Test verbose mode doesn't break functionality
        items = parse_csv_to_objects(csv_data, verbose=True)
        assert_that(items).is_length(1)