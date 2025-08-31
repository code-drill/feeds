#!/usr/bin/env python3
"""
Tests for CLI functionality.
"""
import pytest
from assertpy import assert_that
from mockito import when

from generate_blog_posts import app, fetch_csv_data


class TestCLI:
    """Test CLI functionality."""

    def test_cli_help(self, cli_runner):
        """Test CLI help command works."""
        result = cli_runner.invoke(app, ["generate", "--help"])
        
        assert_that(result.exit_code).is_zero()
        assert_that(result.stdout).contains("Generate blog posts from CSV data")

    def test_cli_basic_run_no_crash(self, cli_runner):
        """Test CLI runs without crashing on basic invocation."""
        result = cli_runner.invoke(app, ["generate", "--verbose"], catch_exceptions=False)
        
        assert_that(result.exit_code).is_zero()
        assert_that(result.stdout).contains("Processing")
        assert_that(result.stdout).contains("from host.docker.internal:8000")

    def test_cli_date_range_missing_params(self, cli_runner):
        """Test CLI generate command with incomplete date range parameters."""
        result = cli_runner.invoke(app, ["generate", "--start-date", "2024-08-30"])
        
        assert_that(result.exit_code).is_equal_to(1)

    def test_cli_custom_host_parameter(self, cli_runner):
        """Test CLI accepts custom host parameter."""
        result = cli_runner.invoke(app, ["generate", "--host", "localhost:3000", "--verbose"])
        
        assert_that(result.exit_code).is_zero()
        assert_that(result.stdout).contains("localhost:3000")

    def test_cli_handles_fetch_errors(self, cli_runner):
        """Test CLI handles fetch errors gracefully."""
        # Import the module to mock its function properly
        import generate_blog_posts
        when(generate_blog_posts).fetch_csv_data(...).thenRaise(Exception("Network error"))
        
        result = cli_runner.invoke(app, ["generate", "2024-08-30", "--verbose"])
        
        assert_that(result.exit_code).is_zero()  # CLI doesn't crash on errors

    def test_cli_verbose_flag(self, cli_runner):
        """Test CLI verbose flag provides detailed output."""
        result = cli_runner.invoke(app, ["generate", "--verbose"])
        
        assert_that(result.exit_code).is_zero()
        # Verbose mode should show detailed processing information
        assert_that(result.stdout).contains("Processing")

    def test_cli_specific_date_format(self, cli_runner):
        """Test CLI with specific date format."""
        result = cli_runner.invoke(app, ["generate", "2024-08-30", "--verbose"])
        
        assert_that(result.exit_code).is_zero()
        # Should process the specific date
        assert_that(result.stdout).contains("Processing")

    def test_cli_multiple_dates(self, cli_runner):
        """Test CLI with multiple dates."""
        result = cli_runner.invoke(app, ["generate", "2024-08-30", "2024-08-31", "--verbose"])
        
        assert_that(result.exit_code).is_zero()
        # Should process multiple dates
        assert_that(result.stdout).contains("Processing")

    def test_cli_date_range_positive_offset(self, cli_runner):
        """Test CLI with positive date range offset."""
        result = cli_runner.invoke(app, ["generate", "--start-date", "2024-08-30", "--offset-days", "2", "--verbose"])
        
        assert_that(result.exit_code).is_zero()
        assert_that(result.stdout).contains("Processing date range")
        assert_that(result.stdout).contains("3 days")  # 2 offset + start date

    def test_cli_date_range_negative_offset(self, cli_runner):
        """Test CLI with negative date range offset."""
        result = cli_runner.invoke(app, ["generate", "--start-date", "2024-08-30", "--offset-days", "-2", "--verbose"])
        
        assert_that(result.exit_code).is_zero()
        assert_that(result.stdout).contains("Processing date range")
        assert_that(result.stdout).contains("3 days")  # 2 offset + start date

    def test_cli_custom_posts_dir(self, cli_runner, temp_posts_dir):
        """Test CLI with custom posts directory."""
        result = cli_runner.invoke(app, ["generate", "--posts-dir", str(temp_posts_dir), "--verbose"])
        
        assert_that(result.exit_code).is_zero()
        # Should complete without error even with custom posts directory
        assert_that(result.stdout).contains("Processing")