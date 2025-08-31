#!/usr/bin/env python3
"""
Tests for BlogPostItem model validation.
"""
import pytest
from assertpy import assert_that

from generate_blog_posts import BlogPostItem


class TestBlogPostItem:
    """Test BlogPostItem validation."""
    
    def test_valid_blog_post_item(self, valid_blog_post_data):
        """Test creating a valid BlogPostItem."""
        item = BlogPostItem(**valid_blog_post_data)
        
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

    def test_field_aliases(self, valid_blog_post_data):
        """Test that field aliases work correctly."""
        item = BlogPostItem(**valid_blog_post_data)
        
        # Test that we can access fields by their Python names
        assert_that(item.published_date).is_equal_to("2024-08-30T10:00:00Z")
        assert_that(item.ai_category).is_equal_to("technical_deep_dives")
        assert_that(item.source_name).is_equal_to("Test Blog")
        assert_that(item.source_url).is_equal_to("https://example.com")

    def test_optional_fields_default_values(self):
        """Test that optional fields have correct default values."""
        minimal_data = {
            "Title": "Test Title",
            "Link": "https://example.com",
            "Published Date": "2024-08-30T10:00:00Z"
        }
        item = BlogPostItem(**minimal_data)
        
        assert_that(item.summary).is_equal_to("")
        assert_that(item.ai_category).is_equal_to("")
        assert_that(item.source_name).is_equal_to("")
        assert_that(item.source_url).is_equal_to("")
        assert_that(item.author).is_equal_to("")

    def test_field_cleanup(self):
        """Test that fields are properly cleaned up (whitespace stripped)."""
        data = {
            "Title": "  Test Title  ",
            "Link": "  https://example.com  ",
            "Published Date": "  2024-08-30T10:00:00Z  ",
            "Summary": "  Test summary  ",
            "AI Category": "  technical_deep_dives  "
        }
        item = BlogPostItem(**data)
        
        assert_that(item.title).is_equal_to("Test Title")
        assert_that(item.link).is_equal_to("https://example.com")
        assert_that(item.published_date).is_equal_to("2024-08-30T10:00:00Z")
        assert_that(item.summary).is_equal_to("Test summary")
        assert_that(item.ai_category).is_equal_to("technical_deep_dives")