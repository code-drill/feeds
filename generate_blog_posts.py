#!/usr/bin/env python3
"""
Script to generate Nikola blog posts from CSV data.
"""
import contextlib
import csv
import urllib.request
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Optional, Dict, Set
import html

import typer
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BlogPostItem(BaseModel):
    """Pydantic model for blog post CSV data."""
    model_config = ConfigDict(populate_by_name=True)
    
    title: str = Field(..., alias="Title", min_length=1)
    link: str = Field(..., alias="Link", min_length=1)
    published_date: str = Field(..., alias="Published Date", min_length=1)
    summary: str = Field(default="", alias="Summary")
    ai_category: str = Field(default="", alias="AI Category")
    source_name: str = Field(default="", alias="Source Name")
    source_url: str = Field(default="", alias="Source URL")
    author: str = Field(default="", alias="Author")
    
    @field_validator('title', 'link', 'published_date')
    @classmethod
    def required_fields_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Required field cannot be empty')
        return v.strip()
    
    @field_validator('summary', 'ai_category', 'source_name', 'source_url', 'author', mode='before')
    @classmethod
    def optional_fields_cleanup(cls, v):
        return v.strip() if v else ""


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
    
    # Create the main content without original link (title links to original now)
    content = f"""
{summary}

**Source:** [{item['Source Name']}]({item['Source URL']})  
**Author:** {item['Author'] if item['Author'] else 'Unknown'}  
**Category:** {item['AI Category']}
"""
    
    return content.strip()


def parse_post_metadata(post_file: Path) -> Dict[str, str]:
    """Parse metadata from a blog post file."""
    metadata = {}
    try:
        with open(post_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract metadata from HTML comment block
        metadata_match = re.search(r'<!--\s*\n(.*?)\n\s*-->', content, re.DOTALL)
        if metadata_match:
            metadata_content = metadata_match.group(1)
            
            # Parse each metadata line
            for line in metadata_content.split('\n'):
                line = line.strip()
                if line.startswith('.. '):
                    line = line[3:]  # Remove '.. ' prefix
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error parsing metadata from {post_file}: {e}")
    
    return metadata


def scan_existing_posts(posts_dir: Path) -> tuple[Set[str], Set[str]]:
    """Scan existing posts to extract unique categories and sources."""
    categories = set()
    sources = set()
    
    # Find all .md files in the posts directory
    post_files = list(posts_dir.glob('**/*.md'))
    
    for post_file in post_files:
        metadata = parse_post_metadata(post_file)
        
        # Extract category
        if 'category' in metadata:
            category = metadata['category'].strip()
            if category:
                categories.add(category)
        
        # Extract source from tags (first tag is typically the source)
        if 'tags' in metadata:
            tags = metadata['tags'].split(',')
            if tags and tags[0].strip():
                source_tag = tags[0].strip()
                sources.add(source_tag)
    
    return categories, sources


def generate_category_buttons(categories: Set[str]) -> str:
    """Generate category filter buttons HTML."""
    # Define category display names and their URL fragments
    category_mapping = {
        'educational': ('Educational & How-To', 'cat_educational'),
        'event': ('Event', 'cat_event'),
        'general': ('General', 'cat_general'),
        'industry_analysis': ('Industry Analysis & Insights', 'cat_industry_analysis'),
        'product_announcements': ('Product Announcements & Updates', 'cat_product_announcements'),
        'security_compliance': ('Security & Compliance Focus', 'cat_security_compliance'),
        'technical_deep_dives': ('Technical Deep Dives', 'cat_technical_deep_dives')
    }
    
    buttons = []
    for category in sorted(categories):
        if category in category_mapping:
            display_name, url_fragment = category_mapping[category]
        else:
            # Handle new categories dynamically
            display_name = category.replace('_', ' ').title()
            url_fragment = f'cat_{category}'
        
        button = f'                <a href="${{abs_link(\'categories/{url_fragment}/\')}}" class="btn btn-outline-primary btn-sm">{display_name}</a>'
        buttons.append(button)
    
    return '\n'.join(buttons)


def generate_source_buttons(sources: Set[str]) -> str:
    """Generate source filter buttons HTML."""
    # Define source display names based on tag names
    source_mapping = {
        '1password-blog': '1Password Blog',
        'airbnb-engineering': 'Airbnb Engineering',
        'amd-developer-blog': 'AMD Developer Blog',
        'apple-developer-news': 'Apple Developer News',
        'atlassian-developer-blog': 'Atlassian Developer Blog',
        'auth0-blog': 'Auth0 Blog',
        'aws-blog': 'AWS Blog',
        'circleci-blog': 'CircleCI Blog',
        'cisco-developer-blog': 'Cisco Developer Blog',
        'cloudflare-blog': 'Cloudflare Blog',
        'code-as-craft': 'Code as Craft',
        'crowdstrike-blog': 'CrowdStrike Blog',
        'databricks-blog': 'Databricks Blog',
        'digitalocean-blog': 'DigitalOcean Blog',
        'docker-blog': 'Docker Blog',
        'doordash-engineering': 'DoorDash Engineering',
        'dropbox-tech-blog': 'Dropbox Tech Blog',
        'elastic-blog': 'Elastic Blog',
        'engineering-at-meta': 'Engineering at Meta',
        'gitlab-blog': 'GitLab Blog',
        'google-developers-blog': 'Google Developers Blog',
        'google-research': 'Google Research',
        'grab-tech': 'Grab Tech',
        'hashicorp-blog': 'HashiCorp Blog',
        'heroku-blog': 'Heroku Blog',
        'hugging-face-blog': 'Hugging Face Blog',
        'jetbrains-blog': 'JetBrains Blog',
        'kubernetes-blog': 'Kubernetes Blog',
        'ly-corporation-tech-blog': 'LY Corporation Tech Blog',
        'lyft-engineering': 'Lyft Engineering',
        'medium-engineering': 'Medium Engineering',
        'mongodb-blog': 'MongoDB Blog',
        'mozilla-hacks': 'Mozilla Hacks',
        'netflix-technology-blog': 'Netflix Technology Blog',
        'nvidia-developer-blog': 'NVIDIA Developer Blog',
        'okta-developer-blog': 'Okta Developer Blog',
        'palantir-blog': 'Palantir Blog',
        'pinterest-engineering': 'Pinterest Engineering',
        'planetscale-blog': 'PlanetScale Blog',
        'railway-blog': 'Railway Blog',
        'red-hat-developer-blog': 'Red Hat Developer Blog',
        'robinhood-engineering': 'Robinhood Engineering',
        'salesforce-engineering': 'Salesforce Engineering',
        'stack-overflow-blog': 'Stack Overflow Blog',
        'stripe-blog': 'Stripe Blog',
        'supabase-blog': 'Supabase Blog',
        'tableau-engineering': 'Tableau Engineering',
        'twilio-engineering': 'Twilio Engineering',
        'uber-engineering': 'Uber Engineering',
        'unity-blog': 'Unity Blog',
        'unreal-engine-blog': 'Unreal Engine Blog',
        'vercel-blog': 'Vercel Blog',
        'webflow-blog': 'Webflow Blog'
    }
    
    buttons = []
    for source in sorted(sources):
        display_name = source_mapping.get(source, source.replace('-', ' ').title())
        button = f'                <a href="${{abs_link(\'sources/{source}/\')}}" class="btn btn-outline-success btn-sm">{display_name}</a>'
        buttons.append(button)
    
    return '\n'.join(buttons)


def update_filters_template(templates_dir: Path, categories: Set[str], sources: Set[str]) -> None:
    """Update the filters template with dynamic content."""
    template_file = templates_dir / 'filters_nav.tmpl'
    
    if not template_file.exists():
        print(f"Template file not found: {template_file}")
        return
    
    # Generate dynamic content
    category_buttons = generate_category_buttons(categories)
    source_buttons = generate_source_buttons(sources)
    
    try:
        # Read template file
        with open(template_file, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Replace placeholders with generated content
        updated_content = template_content.replace('${DYNAMIC_CATEGORIES}', category_buttons)
        updated_content = updated_content.replace('${DYNAMIC_SOURCES}', source_buttons)
        
        # Write updated template
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
            
        print(f"Updated filters template with {len(categories)} categories and {len(sources)} sources")
        
    except Exception as e:
        print(f"Error updating filters template: {e}")


def create_blog_post(item: dict, posts_dir: Path, verbose: bool = False) -> bool:
    """Create a single blog post file."""
    # Parse the published date for directory structure but use current time for publication

    pub_date = datetime.fromisoformat(item['Published Date'].replace('Z', '+00:00')).replace(tzinfo=None)
    if pub_date > datetime.now():
        pub_date = datetime.now()

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
    
    # Prepare tags for sources (tags will be used for source filtering)
    tags_list = []
    
    # Extract source name for tagging
    source_name = item.get('Source Name', '').strip()
    if source_name:
        # Clean up source name for tag
        source_tag = re.sub(r'[^\w\s-]', '', source_name).strip().lower()
        source_tag = re.sub(r'[-\s]+', '-', source_tag)
        if source_tag:
            tags_list.append(source_tag)
    
    # Note: We only use Source Name for tagging/filtering, not Source Category
    
    # Remove duplicates and filter out empty tags
    tags_set = {tag for tag in tags_list if tag.strip()}
    tags_str = ','.join(sorted(tags_set))  # Sort for consistency
    
    # Set category based on AI Category (categories will be used for content type filtering)
    category = item['AI Category'].lower() if item['AI Category'] else 'general'

    is_valid_to_process = item['AI Category'].strip() and item['Summary'].strip()
    if not is_valid_to_process:
        if verbose:
            typer.echo(f"SKIP: {date_str}/{filename} - no `Summary` or `AI Category` present")
        return False

    
    # Create Nikola metadata header using HTML comments
    metadata = f"""<!--
.. title: {title}
.. slug: {slug}
.. date: {pub_date.strftime('%Y-%m-%d %H:%M:%S %z')}
.. tags: {tags_str}
.. category: {category}
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
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode('utf-8')


def parse_csv_to_objects(csv_data: str, verbose: bool = False) -> List[BlogPostItem]:
    """Parse CSV data and return list of BlogPostItem objects."""
    if not csv_data or not csv_data.strip():
        return []
    
    try:
        csv_reader = csv.DictReader(csv_data.splitlines())
        parsed_items = []
        
        for row_num, row_data in enumerate(csv_reader, 1):
            if verbose:
                # Safely handle Unicode characters for console output
                try:
                    typer.echo(f"INFO: processing {row_num} - data: {row_data}")
                except UnicodeEncodeError:
                    typer.echo(f"INFO: processing {row_num} - data: [contains Unicode characters]")
            try:
                item = BlogPostItem(**row_data)
                parsed_items.append(item)
            except Exception as e:
                if verbose:
                    typer.echo(f"WARNING: Skipping row {row_num} - validation error: {e}")
                continue
        
        return parsed_items
    except Exception as e:
        typer.echo(f"ERROR: Error parsing CSV data: {e}", err=True)
        return []


def is_valid_to_save(item: BlogPostItem) -> bool:
    """Validate if a BlogPostItem object is valid to save as a blog post."""
    return bool(item.ai_category.strip() and item.summary.strip())


def save_items_to_files(items: List[BlogPostItem], posts_dir: Path, verbose: bool = False) -> tuple[int, int]:
    """Save list of BlogPostItem objects to files and return counts."""
    created_count = 0
    processed_count = 0
    
    for item in items:
        processed_count += 1
        
        if not is_valid_to_save(item):
            if verbose:
                typer.echo(f"SKIP: {item.title[:50]}... - no `Summary` or `AI Category` present")
            continue
        
        try:
            # Convert BlogPostItem to dict for compatibility with create_blog_post
            item_dict = {
                'Title': item.title,
                'Link': item.link,
                'Published Date': item.published_date,
                'Summary': item.summary,
                'AI Category': item.ai_category,
                'Source Name': item.source_name,
                'Source URL': item.source_url,
                'Author': item.author
            }
            
            if create_blog_post(item_dict, posts_dir, verbose):
                created_count += 1
        except Exception as e:
            typer.echo(f"ERROR: Error creating post for '{item.title}': {e}", err=True)
    
    return created_count, processed_count


def process_csv_for_date(csv_url: str, posts_dir: Path, verbose: bool = False) -> tuple[int, int]:
    """Process CSV data for a specific date using structured approach."""
    if verbose:
        typer.echo(f"Fetching data from {csv_url}")

    # Fetch CSV data
    try:
        csv_data = fetch_csv_data(csv_url)
        if not csv_data or not csv_data.strip():
            typer.echo(f"No data fetched CSV from: {csv_url}")
            return 0, 0
    except Exception as e:
        typer.echo(f"ERROR: Failed to fetch CSV data from: {csv_url}, error: {e}", err=True)
        return 0, 0

    # Parse CSV data to list of objects
    items = parse_csv_to_objects(csv_data, verbose)
    if not items:
        return 0, 0
    
    # Save valid items to files
    return save_items_to_files(items, posts_dir, verbose)


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
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date", "-s",
        help="Start date for date range processing (YYYY-MM-DD format)"
    ),
    offset_days: Optional[int] = typer.Option(
        None,
        "--offset-days", "-o",
        help="Number of days from start date (can be negative for past dates)"
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
      
      # Process date range: 7 days starting from 2025-08-20
      python generate_blog_posts.py --start-date 2025-08-20 --offset-days 7
      
      # Process date range: 3 days before 2025-08-26 (including 2025-08-26)
      python generate_blog_posts.py --start-date 2025-08-26 --offset-days -3
      
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
    
    # Determine templates directory
    templates_dir = script_dir / "feeds.code-drill.eu" / "templates"
    
    # Initialize counters
    total_created = 0
    total_processed = 0
    
    # Handle date range processing
    if offset_days is not None:
        if start_date is None:
            start_dt = datetime.today().date()
        else:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                typer.echo(f"ERROR: Invalid start date format: {start_date}. Use YYYY-MM-DD format.", err=True)
                raise typer.Exit(1)
        
        # Generate date range
        dates_to_process = []
        if offset_days >= 0:
            # Forward range: start_date to start_date + offset_days
            for i in range(offset_days + 1):
                current_date = start_dt + timedelta(days=i)
                dates_to_process.append(current_date.strftime('%Y-%m-%d'))
        else:
            # Backward range: start_date + offset_days to start_date
            for i in range(abs(offset_days) + 1):
                current_date = start_dt - timedelta(days=abs(offset_days) - i)
                dates_to_process.append(current_date.strftime('%Y-%m-%d'))
        
        typer.echo(f"Processing date range: {dates_to_process[0]} to {dates_to_process[-1]} ({len(dates_to_process)} days) from {host}")
        
        for date_str in dates_to_process:
            csv_url = f"http://{host}/daily-items/{date_str}.csv"
            created, processed = process_csv_for_date(csv_url, posts_dir, verbose)
            total_created += created
            total_processed += processed
            
            if not verbose:
                typer.echo(f"{date_str}: {created} created, {processed-created} skipped")
        
        typer.echo(f"\nSummary:")
        typer.echo(f"   Total processed: {total_processed} items")
        typer.echo(f"   Total created: {total_created} new posts")
        typer.echo(f"   Total skipped: {total_processed - total_created} existing posts")
        
    elif start_date is not None or offset_days is not None:
        # Error if only one of start_date or offset_days is provided
        typer.echo("ERROR: Both --start-date and --offset-days must be provided together.", err=True)
        raise typer.Exit(1)
        
    elif dates:
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
        typer.echo(f"   nikola build")
    else:
        typer.echo("\nNo new posts to build.")
    
    # Update filters template with current categories and sources
    typer.echo("\nUpdating filters...")
    categories, sources = scan_existing_posts(posts_dir)
    if categories or sources:
        update_filters_template(templates_dir, categories, sources)
    else:
        typer.echo("No posts found to generate filters from.")


def main():
    """Entry point for the script."""
    app()


if __name__ == "__main__":
    exit(main())