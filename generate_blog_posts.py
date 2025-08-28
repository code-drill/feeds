#!/usr/bin/env python3
"""
Script to generate Nikola blog posts from CSV data.

Usage:
    python generate_blog_posts.py # Process today's CSV (default)
    python generate_blog_posts.py 2025-08-26 # Process specific date
    python generate_blog_posts.py 2025-08-25 2025-08-26 # Process multiple dates

CSV endpoints:
    - Current: http://host.docker.internal:8000/daily-items.csv
    - Historical: http://host.docker.internal:8000/daily-items/<YYYY-MM-DD>.csv
"""

import csv
import urllib.request
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import html


def slugify(text):
    """Convert text to a URL-friendly slug."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Convert to lowercase and replace spaces/special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text[:75]  # Limit length


def clean_html_content(content):
    """Clean HTML content and convert to readable text."""
    if not content:
        return ""
    
    # Decode HTML entities
    content = html.unescape(content)
    
    # Remove HTML tags but keep the content
    content = re.sub(r'<[^>]+>', '', content)
    
    # Clean up extra whitespace
    content = re.sub(r'\s+', ' ', content).strip()
    
    return content


def format_markdown_content(item):
    """Format the blog post content in Markdown."""
    summary = clean_html_content(item['Summary'])
    
    # Create the main content
    content = f"""
{summary}

**Source:** [{item['Source Name']}]({item['Source URL']})  
**Author:** {item['Author'] if item['Author'] else 'Unknown'}  
**Category:** {item['AI Category']}  
**Original Link:** [{item['Title']}]({item['Link']})
"""
    
    return content.strip()


def create_blog_post(item, posts_dir):
    """Create a single blog post file."""
    # Parse the published date
    pub_date = datetime.fromisoformat(item['Published Date'].replace('Z', '+00:00'))
    date_str = pub_date.strftime('%Y-%m-%d')
    
    # Create date directory
    date_dir = posts_dir / date_str
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # Create slug from title
    slug = slugify(item['Title'])
    
    # Create filename (without date prefix since it's in the directory name)
    filename = f"{slug}.md"
    filepath = date_dir / filename
    
    # Skip if file already exists
    if filepath.exists():
        print(f"Skipping {date_str}/{filename} - already exists")
        return False
    
    # Clean and prepare metadata fields
    title = item['Title'].replace('"', '\\"')  # Escape quotes
    description = clean_html_content(item['Summary'])[:150] + "..."
    description = description.replace('"', '\\"')  # Escape quotes
    
    # Prepare tags (clean up categories and AI category)
    tags_list = []
    if item['AI Category']:
        tags_list.append(item['AI Category'].lower())
    if item['Source Category']:
        # Split source category by comma and clean up
        source_tags = [tag.strip().lower() for tag in item['Source Category'].split(',')]
        tags_list.extend(source_tags)
    tags_list.append('tech')  # Add default tag
    # Remove duplicates and filter out empty tags
    tags_set = {tag for tag in tags_list if tag.strip()}
    tags_str = ','.join(sorted(tags_set))  # Sort for consistency
    
    # Create Nikola metadata header using HTML comments
    metadata = f"""<!--
.. title: {title}
.. slug: {slug}
.. date: {pub_date.strftime('%Y-%m-%d %H:%M:%S %z')}
.. tags: {tags_str}
.. category: {item['AI Category'].lower() if item['AI Category'] else 'tech'}
.. link: {item['Link']}
.. description: {description}
.. type: text
-->

"""
    
    # Format content
    content = format_markdown_content(item)
    
    # Write the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(metadata + content)
    
    print(f"Created: {date_str}/{filename}")
    return True


def fetch_csv_data(url):
    """Fetch CSV data from the endpoint."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching CSV data: {e}")
        return None


def process_csv_for_date(csv_url, posts_dir):
    """Process CSV data for a specific date."""
    print(f"Fetching data from {csv_url}...")
    csv_data = fetch_csv_data(csv_url)
    
    if not csv_data:
        print(f"Failed to fetch CSV data from {csv_url}")
        return 0, 0
    
    # Parse CSV
    try:
        csv_reader = csv.DictReader(csv_data.splitlines())
    except Exception as e:
        print(f"Error parsing CSV data: {e}")
        return 0, 0
    
    created_count = 0
    processed_count = 0
    
    for item in csv_reader:
        processed_count += 1
        
        # Skip items without required fields
        if not all([item.get('Title'), item.get('Link'), item.get('Published Date')]):
            print(f"Skipping item {processed_count} - missing required fields")
            continue
            
        try:
            if create_blog_post(item, posts_dir):
                created_count += 1
        except Exception as e:
            print(f"Error creating post for '{item.get('Title', 'Unknown')}': {e}")
    
    return created_count, processed_count


def main():
    """Main function to process CSV and generate blog posts."""
    import sys
    
    # Determine paths
    script_dir = Path(__file__).parent
    posts_dir = script_dir / "feeds.code-drill.eu" / "posts"
    
    # Ensure posts directory exists
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize counters
    total_created = 0
    total_processed = 0
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Process specific dates provided as arguments
        for date_arg in sys.argv[1:]:
            # Validate date format
            try:
                datetime.strptime(date_arg, '%Y-%m-%d')
                csv_url = f"http://host.docker.internal:8000/daily-items/{date_arg}.csv"
                created, processed = process_csv_for_date(csv_url, posts_dir)
                total_created += created
                total_processed += processed
            except ValueError:
                print(f"Invalid date format: {date_arg}. Use YYYY-MM-DD format.")
                continue
        
        print(f"\nTotal processed {total_processed} items across all dates")
        print(f"Total created {total_created} new blog posts")
        
    else:
        # Default behavior - process today's CSV
        csv_url = "http://host.docker.internal:8000/daily-items.csv"
        created, processed = process_csv_for_date(csv_url, posts_dir)
        total_created = created
        total_processed = processed
        
        print(f"\nProcessed {total_processed} items")
        print(f"Created {total_created} new blog posts")
        print(f"Skipped {total_processed - total_created} items")
    
    if total_created > 0:
        print(f"\nTo build the site, run:")
        print(f"cd {posts_dir.parent}")
        print(f"uv run --active nikola build")
    
    return 0


if __name__ == "__main__":
    exit(main())