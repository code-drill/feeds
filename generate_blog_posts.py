#!/usr/bin/env python3
"""
Script to generate Nikola blog posts from CSV data.
"""

import csv
import urllib.request
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Optional
import html

import typer


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


def create_blog_post(item: dict, posts_dir: Path, verbose: bool = False) -> bool:
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
        if verbose:
            typer.echo(f"SKIP: {date_str}/{filename} - already exists")
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
    
    if verbose:
        typer.echo(f"CREATED: {date_str}/{filename}")
    return True


def fetch_csv_data(url):
    """Fetch CSV data from the endpoint."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching CSV data: {e}")
        return None


def process_csv_for_date(csv_url: str, posts_dir: Path, verbose: bool = False) -> tuple[int, int]:
    """Process CSV data for a specific date."""
    if verbose:
        typer.echo(f"Fetching data from {csv_url}")
    
    csv_data = fetch_csv_data(csv_url)
    
    if not csv_data:
        typer.echo(f"ERROR: Failed to fetch CSV data from {csv_url}", err=True)
        return 0, 0
    
    # Parse CSV
    try:
        csv_reader = csv.DictReader(csv_data.splitlines())
    except Exception as e:
        typer.echo(f"ERROR: Error parsing CSV data: {e}", err=True)
        return 0, 0
    
    created_count = 0
    processed_count = 0
    
    for item in csv_reader:
        processed_count += 1
        
        # Skip items without required fields
        if not all([item.get('Title'), item.get('Link'), item.get('Published Date')]):
            if verbose:
                typer.echo(f"WARNING: Skipping item {processed_count} - missing required fields")
            continue
            
        try:
            if create_blog_post(item, posts_dir, verbose):
                created_count += 1
        except Exception as e:
            typer.echo(f"ERROR: Error creating post for '{item.get('Title', 'Unknown')}': {e}", err=True)
    
    return created_count, processed_count


app = typer.Typer(
    help="Generate Nikola blog posts from CSV data feeds.",
    add_completion=False,
)


@app.command()
def generate(
    dates: Optional[List[str]] = typer.Argument(
        None,
        help="Specific dates to process (YYYY-MM-DD format). If not provided, processes today's data.",
        metavar="[DATE...]"
    ),
    host: str = typer.Option(
        "host.docker.internal:8000",
        "--host", "-h",
        help="Host for the CSV API endpoint"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Show detailed output including skipped and created files"
    ),
    posts_dir: Optional[Path] = typer.Option(
        None,
        "--posts-dir", "-p",
        help="Custom posts directory (default: feeds.code-drill.eu/posts)"
    )
):
    """
    Generate blog posts from CSV data.
    
    Examples:
    \b
      # Process today's data
      python generate_blog_posts.py
      
      # Process specific date
      python generate_blog_posts.py 2025-08-26
      
      # Process multiple dates
      python generate_blog_posts.py 2025-08-25 2025-08-26 2025-08-27
      
      # Use custom host
      python generate_blog_posts.py --host localhost:3000 2025-08-26
      
      # Verbose output
      python generate_blog_posts.py --verbose 2025-08-26
    """
    
    # Determine paths
    script_dir = Path(__file__).parent
    if posts_dir is None:
        posts_dir = script_dir / "feeds.code-drill.eu" / "posts"
    
    # Ensure posts directory exists
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize counters
    total_created = 0
    total_processed = 0
    
    if dates:
        # Process specific dates provided as arguments
        typer.echo(f"Processing {len(dates)} date(s) from {host}")
        
        for date_str in dates:
            # Validate date format
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                csv_url = f"http://{host}/daily-items/{date_str}.csv"
                created, processed = process_csv_for_date(csv_url, posts_dir, verbose)
                total_created += created
                total_processed += processed
                
                if not verbose:
                    typer.echo(f"{date_str}: {created} created, {processed-created} skipped")
                    
            except ValueError:
                typer.echo(f"ERROR: Invalid date format: {date_str}. Use YYYY-MM-DD format.", err=True)
                continue
        
        typer.echo(f"\nSummary:")
        typer.echo(f"   Total processed: {total_processed} items")
        typer.echo(f"   Total created: {total_created} new posts")
        typer.echo(f"   Total skipped: {total_processed - total_created} existing posts")
        
    else:
        # Default behavior - process today's CSV
        typer.echo(f"Processing today's data from {host}")
        csv_url = f"http://{host}/daily-items.csv"
        created, processed = process_csv_for_date(csv_url, posts_dir, verbose)
        total_created = created
        total_processed = processed
        
        typer.echo(f"\nSummary:")
        typer.echo(f"   Processed: {total_processed} items")
        typer.echo(f"   Created: {total_created} new posts")
        typer.echo(f"   Skipped: {total_processed - total_created} existing posts")
    
    if total_created > 0:
        typer.echo(f"\nTo build the site:")
        typer.echo(f"   cd {posts_dir.parent}")
        typer.echo(f"   uv run --active nikola build")
    else:
        typer.echo("\nNo new posts to build.")


def main():
    """Entry point for the script."""
    app()


if __name__ == "__main__":
    exit(main())