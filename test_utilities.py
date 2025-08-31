#!/usr/bin/env python3
"""
Tests for utility functions.
"""
import pytest
from assertpy import assert_that

from generate_blog_posts import (
    BlogPostItem,
    slugify,
    is_valid_to_save,
    clean_html_content,
    format_markdown_content
)


class TestSlugify:
    """Test slugify functionality."""
    
    def test_slugify_basic(self):
        """Test basic slugify functionality."""
        assert_that(slugify("Test Article Title")).is_equal_to("test-article-title")
        assert_that(slugify("Article with Special! Characters@")).is_equal_to("article-with-special-characters")
        assert_that(slugify("   Multiple   Spaces   ")).is_equal_to("multiple-spaces")

    def test_slugify_with_html_tags(self):
        """Test slugify removes HTML tags."""
        assert_that(slugify("<b>Bold Title</b>")).is_equal_to("bold-title")
        assert_that(slugify("Title with <em>emphasis</em>")).is_equal_to("title-with-emphasis")

    def test_slugify_length_limit(self):
        """Test slugify limits length to 75 characters."""
        long_title = "a" * 100
        result = slugify(long_title)
        assert_that(result).is_length(75)

    def test_slugify_edge_cases(self):
        """Test slugify edge cases."""
        assert_that(slugify("")).is_equal_to("")
        assert_that(slugify("   ")).is_equal_to("")
        assert_that(slugify("123-456")).is_equal_to("123-456")
        assert_that(slugify("Title---With---Dashes")).is_equal_to("title-with-dashes")


class TestIsValidToSave:
    """Test validation for saving items."""
    
    def test_valid_item(self, valid_blog_post_data):
        """Test validation of valid item."""
        item = BlogPostItem(**valid_blog_post_data)
        assert_that(is_valid_to_save(item)).is_true()

    def test_invalid_item_empty_ai_category(self, valid_blog_post_data):
        """Test validation fails with empty AI Category."""
        valid_blog_post_data["AI Category"] = ""
        item = BlogPostItem(**valid_blog_post_data)
        assert_that(is_valid_to_save(item)).is_false()

    def test_invalid_item_empty_summary(self, valid_blog_post_data):
        """Test validation fails with empty Summary."""
        valid_blog_post_data["Summary"] = ""
        item = BlogPostItem(**valid_blog_post_data)
        assert_that(is_valid_to_save(item)).is_false()

    def test_invalid_item_whitespace_only(self, valid_blog_post_data):
        """Test validation fails with whitespace-only fields."""
        valid_blog_post_data["AI Category"] = "   "
        valid_blog_post_data["Summary"] = "   "
        item = BlogPostItem(**valid_blog_post_data)
        assert_that(is_valid_to_save(item)).is_false()


class TestCleanHtmlContent:
    """Test HTML content cleaning."""
    
    def test_clean_html_basic(self):
        """Test basic HTML cleaning."""
        assert_that(clean_html_content("<p>Hello World</p>")).is_equal_to("Hello World")
        assert_that(clean_html_content("<b>Bold</b> and <i>italic</i>")).is_equal_to("Bold and italic")

    def test_clean_html_entities(self):
        """Test HTML entity decoding."""
        # Test basic HTML entity decoding
        assert_that(clean_html_content("&amp;")).is_equal_to("&")
        assert_that(clean_html_content("&quot;")).is_equal_to("\"")

    def test_clean_html_whitespace(self):
        """Test whitespace normalization."""
        assert_that(clean_html_content("Multiple    spaces   here")).is_equal_to("Multiple spaces here")

    def test_clean_html_edge_cases(self):
        """Test edge cases for HTML cleaning."""
        assert_that(clean_html_content("")).is_equal_to("")
        assert_that(clean_html_content(None)).is_equal_to("")
        assert_that(clean_html_content("Plain text")).is_equal_to("Plain text")


class TestFormatMarkdownContent:
    """Test Markdown content formatting."""
    
    def test_format_markdown_basic(self, valid_blog_post_data):
        """Test basic Markdown formatting."""
        result = format_markdown_content(valid_blog_post_data)
        
        assert_that(result).contains("Test summary")
        assert_that(result).contains("**Source:**")
        assert_that(result).contains("Test Blog")
        assert_that(result).contains("**Author:**")
        assert_that(result).contains("Test Author")
        assert_that(result).contains("**Category:**")
        assert_that(result).contains("technical_deep_dives")

    def test_format_markdown_missing_author(self, valid_blog_post_data):
        """Test Markdown formatting with missing author."""
        valid_blog_post_data["Author"] = ""
        result = format_markdown_content(valid_blog_post_data)
        
        assert_that(result).contains("**Author:** Unknown")

    def test_format_markdown_with_html_summary(self, valid_blog_post_data):
        """Test Markdown formatting cleans HTML in summary."""
        valid_blog_post_data["Summary"] = "<p>Test <b>summary</b> with HTML</p>"
        result = format_markdown_content(valid_blog_post_data)
        
        assert_that(result).contains("Test summary with HTML")
        assert_that(result).does_not_contain("<p>")
        assert_that(result).does_not_contain("<b>")