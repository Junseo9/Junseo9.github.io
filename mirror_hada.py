#!/usr/bin/env python3
"""
Automatically mirror and sync content from news.hada.io

This script:
1. Fetches the latest articles from news.hada.io
2. Compares with already mirrored posts (tracked in .hada_mirror_data.json)
3. Creates Jekyll posts for any new articles
4. Automatically syncs when new posts are uploaded to news.hada.io

The script is designed to run automatically via GitHub Actions every 2 hours,
or can be run manually to sync immediately.
"""

import os
import re
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import html2text

# Configuration
HADA_URL = "https://news.hada.io/"
POSTS_DIR = "_posts"
DATA_FILE = ".hada_mirror_data.json"  # Track already mirrored posts
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def load_mirrored_posts():
    """Load list of already mirrored post IDs"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"mirrored_ids": [], "last_update": None}

def save_mirrored_posts(data):
    """Save list of mirrored post IDs"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_filename(title):
    """Create a URL-friendly filename from title"""
    # Remove special characters, keep Korean and alphanumeric
    # Use separate patterns to avoid regex character range issues
    filename = re.sub(r'[^\w\s가-힣-]', '', title)  # Keep word chars, spaces, Korean, hyphens
    filename = re.sub(r'[-\s]+', '-', filename)  # Replace spaces and multiple hyphens with single hyphen
    filename = filename.strip('-')  # Remove leading/trailing hyphens
    return filename[:100]  # Limit length

def parse_time_ago(time_str):
    """Parse Korean time strings like '6시간전', '2일전' to datetime"""
    now = datetime.now()
    
    if '시간전' in time_str or '시간 전' in time_str:
        hours = int(re.search(r'(\d+)', time_str).group(1))
        return now.replace(hour=max(0, now.hour - hours), minute=0, second=0, microsecond=0)
    elif '일전' in time_str or '일 전' in time_str:
        days = int(re.search(r'(\d+)', time_str).group(1))
        return now.replace(day=max(1, now.day - days), hour=0, minute=0, second=0, microsecond=0)
    elif '분전' in time_str or '분 전' in time_str:
        minutes = int(re.search(r'(\d+)', time_str).group(1))
        return now.replace(minute=max(0, now.minute - minutes), second=0, microsecond=0)
    else:
        return now

def fetch_hada_articles():
    """Fetch articles from news.hada.io homepage"""
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        print(f"Fetching articles from {HADA_URL}...")
        response = requests.get(HADA_URL, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # news.hada.io structure: articles are in table rows or list items
        # Look for all links that point to topic?id= (with or without leading slash)
        topic_links = soup.find_all('a', href=re.compile(r'topic\?id=\d+'))
        
        seen_ids = set()
        
        for link in topic_links:
            try:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Extract topic ID
                id_match = re.search(r'id=(\d+)', href)
                if not id_match:
                    continue
                
                topic_id = id_match.group(1)
                # Skip comment links (they have &go=comments)
                if '&go=comments' in href or topic_id in seen_ids:
                    continue
                seen_ids.add(topic_id)
                
                # Get title - could be in the link text or a child element
                title = link.get_text(separator=' ', strip=True)  # Use space as separator for multi-line
                if not title:
                    # Try finding title in child elements
                    title_elem = link.find(['span', 'div', 'strong', 'b'])
                    if title_elem:
                        title = title_elem.get_text(separator=' ', strip=True)
                
                # Clean up title - remove extra whitespace and newlines
                title = ' '.join(title.split())
                
                if not title or len(title) < 3:
                    continue
                
                # Find the parent row/container for metadata
                container = link.find_parent(['tr', 'li', 'div'])
                if not container:
                    container = link.parent
                
                # Get all text in container to parse metadata
                container_text = container.get_text(' ', strip=True)
                
                # Extract points (format: "X points" or "X points by")
                points = 0
                points_match = re.search(r'(\d+)\s*points?', container_text, re.I)
                if points_match:
                    points = int(points_match.group(1))
                
                # Extract author (format: "by username" or "X points by username")
                author = "GeekNews"
                author_match = re.search(r'by\s+([a-zA-Z0-9가-힣_]+)', container_text, re.I)
                if author_match:
                    author = author_match.group(1)
                
                # Extract time (format: "X시간전", "X일전", "X분전")
                time_str = ""
                time_match = re.search(r'(\d+[시간일분]전)', container_text)
                if time_match:
                    time_str = time_match.group(1)
                
                # Get external URL - the title link might point to external URL
                # Check parent container for external link
                external_url = None
                container_links = container.find_all('a', href=True) if container else []
                for clink in container_links:
                    clink_href = clink.get('href', '')
                    # External URLs start with http or are absolute paths
                    if clink_href.startswith('http') and 'hada.io' not in clink_href:
                        external_url = clink_href
                        break
                    # Also check for data-url attribute
                    if clink.get('data-url'):
                        external_url = clink.get('data-url')
                        break
                
                # Try to find description in nearby elements
                description = ""
                # Look for description in next sibling or parent's next sibling
                next_elem = container.find_next(['p', 'div', 'span'], class_=re.compile(r'desc|summary|content|text', re.I))
                if next_elem:
                    description = next_elem.get_text(strip=True)[:500]
                
                articles.append({
                    'id': topic_id,
                    'title': title,
                    'points': points,
                    'author': author,
                    'time_str': time_str,
                    'external_url': external_url,
                    'description': description,
                    'hada_url': urljoin(HADA_URL, href)
                })
                
            except Exception as e:
                print(f"Error parsing article: {e}")
                continue
        
        # Remove duplicates based on ID
        unique_articles = {}
        for article in articles:
            if article['id'] not in unique_articles:
                unique_articles[article['id']] = article
        
        articles = list(unique_articles.values())
        print(f"Found {len(articles)} unique articles")
        return articles
        
    except Exception as e:
        print(f"Error fetching articles: {e}")
        import traceback
        traceback.print_exc()
        return []

def fetch_article_details(article):
    """Fetch detailed content from article page and convert to markdown"""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(article['hada_url'], headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize html2text converter
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # Don't wrap lines
        h.unicode_snob = True  # Use unicode
        h.mark_code = True  # Mark code blocks
        
        # Try to find article content - look for markdown content area
        # news.hada.io uses markdown-it, so content might be in a specific div
        content_elem = None
        
        # Try multiple selectors
        selectors = [
            ('div', {'class': re.compile(r'markdown|content|article|post', re.I)}),
            ('article', {}),
            ('main', {}),
            ('div', {'id': re.compile(r'content|article|post', re.I)}),
        ]
        
        for tag, attrs in selectors:
            content_elem = soup.find(tag, attrs)
            if content_elem:
                break
        
        # If still not found, look for the main content area
        if not content_elem:
            # Look for divs with markdown content
            all_divs = soup.find_all('div')
            for div in all_divs:
                div_text = div.get_text(strip=True)
                if len(div_text) > 200:  # Likely the main content
                    content_elem = div
                    break
        
        if content_elem:
            # Remove navigation, headers, footers, etc.
            for elem in content_elem.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                elem.decompose()
            
            # Remove upvote buttons and metadata that might be in the content
            for elem in content_elem.find_all(['a', 'span'], string=re.compile(r'▲|points|by|시간전|일전|댓글', re.I)):
                if elem.parent and elem.parent.name in ['div', 'span']:
                    # Check if it's metadata (small text, likely in header)
                    parent_text = elem.parent.get_text()
                    if any(x in parent_text for x in ['points', 'by', '시간전', '일전', '댓글']):
                        elem.parent.decompose()
            
            # Convert HTML to markdown
            html_content = str(content_elem)
            markdown_content = h.handle(html_content)
            
            # Clean up the markdown
            # Remove excessive blank lines
            markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
            # Remove leading/trailing whitespace
            markdown_content = markdown_content.strip()
            
            article['content'] = markdown_content[:10000]  # Limit content length
        else:
            # Fallback: use description or try to extract from body
            body = soup.find('body')
            if body:
                # Remove scripts, styles, nav, etc.
                for elem in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    elem.decompose()
                html_content = str(body)
                markdown_content = h.handle(html_content)
                # Try to extract just the main content (skip navigation)
                lines = markdown_content.split('\n')
                # Find the start of actual content (skip headers, navigation)
                start_idx = 0
                for i, line in enumerate(lines):
                    if len(line.strip()) > 50 and not any(x in line for x in ['▲', 'points', 'by', '로그인', '검색']):
                        start_idx = i
                        break
                article['content'] = '\n'.join(lines[start_idx:])[:10000]
            else:
                article['content'] = article.get('description', '')
        
        return article
        
    except Exception as e:
        print(f"    Warning: Error fetching article details for {article['id']}: {e}")
        article['content'] = article.get('description', '')
        return article

def create_jekyll_post(article):
    """Create a Jekyll post from article data"""
    # Parse date
    if article.get('time_str'):
        post_date = parse_time_ago(article['time_str'])
    else:
        post_date = datetime.now()
    
    date_str = post_date.strftime("%Y-%m-%d")
    time_str = post_date.strftime("%H:%M:%S +0900")
    
    # Create filename
    filename_title = clean_filename(article['title'])
    filename = f"{date_str}-{filename_title}.md"
    filepath = os.path.join(POSTS_DIR, filename)
    
    # Avoid duplicates
    if os.path.exists(filepath):
        print(f"  Post already exists: {filename}")
        return False
    
    # Prepare content
    content = article.get('content', article.get('description', ''))
    external_url = article.get('external_url')
    if external_url and external_url != 'None':
        content = f"원문: [{external_url}]({external_url})\n\n" + content
    
    # Escape title for YAML (handle quotes and special chars)
    title_escaped = article['title'].replace('"', '\\"').replace('\n', ' ').replace('\r', '')
    title_escaped = ' '.join(title_escaped.split())  # Normalize whitespace
    
    # Handle external_url - don't include if None or empty
    external_url = article.get('external_url') or ''
    external_url_line = f"external_url: {external_url}" if external_url and external_url != 'None' else ""
    
    # Create frontmatter
    post_content = f"""---
layout: post
title: "{title_escaped}"
date: {date_str} {time_str}
categories: news
tags: [hada, mirror]
points: {article.get('points', 0)}
author: {article.get('author', 'GeekNews')}
{external_url_line}
hada_id: {article.get('id', '')}
---

{content}
"""
    
    # Write file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(post_content)
        print(f"  ✓ Created: {filename}")
        return True
    except Exception as e:
        print(f"  ✗ Error creating {filename}: {e}")
        return False

def check_existing_posts():
    """Check existing posts and extract hada_ids to sync with mirror data"""
    existing_ids = set()
    if os.path.exists(POSTS_DIR):
        for filename in os.listdir(POSTS_DIR):
            if filename.endswith('.md'):
                filepath = os.path.join(POSTS_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract hada_id from frontmatter
                        id_match = re.search(r'hada_id:\s*(\d+)', content)
                        if id_match:
                            existing_ids.add(id_match.group(1))
                except Exception as e:
                    print(f"  Warning: Could not read {filename}: {e}")
    return existing_ids

def sync_mirror_data():
    """Sync mirror data with existing posts to ensure consistency"""
    print("📋 Syncing mirror data with existing posts...")
    existing_ids = check_existing_posts()
    mirror_data = load_mirrored_posts()
    mirrored_ids = set(mirror_data.get('mirrored_ids', []))
    
    # Add any existing post IDs that aren't in mirror data
    missing_ids = existing_ids - mirrored_ids
    if missing_ids:
        print(f"  Found {len(missing_ids)} existing posts not in mirror data, adding them...")
        mirror_data['mirrored_ids'].extend(list(missing_ids))
        save_mirrored_posts(mirror_data)
    
    # Remove IDs from mirror data if posts don't exist (optional cleanup)
    # This is commented out to preserve history, but can be enabled if needed
    # missing_posts = mirrored_ids - existing_ids
    # if missing_posts:
    #     print(f"  Found {len(missing_posts)} IDs in mirror data without posts")
    
    return mirror_data

def main():
    """Main function to mirror hada.io content"""
    print("=" * 60)
    print("🔄 Mirroring content from news.hada.io")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Sync mirror data with existing posts first
    mirror_data = sync_mirror_data()
    mirrored_ids = set(mirror_data.get('mirrored_ids', []))
    
    print(f"📊 Currently tracking {len(mirrored_ids)} mirrored articles")
    if mirror_data.get('last_update'):
        print(f"📅 Last update: {mirror_data['last_update']}\n")
    
    # Ensure posts directory exists
    os.makedirs(POSTS_DIR, exist_ok=True)
    
    # Fetch articles from news.hada.io
    print("🌐 Fetching latest articles from news.hada.io...")
    articles = fetch_hada_articles()
    
    if not articles:
        print("❌ No articles found. Exiting.")
        return
    
    print(f"✅ Found {len(articles)} articles on news.hada.io\n")
    
    # Filter out already mirrored articles
    new_articles = [a for a in articles if a['id'] not in mirrored_ids]
    
    if not new_articles:
        print("✨ All articles are already mirrored. No new posts to sync.")
        print(f"   Total articles on site: {len(articles)}")
        print(f"   Total mirrored: {len(mirrored_ids)}")
        return
    
    # Sort by ID (newer articles typically have higher IDs)
    new_articles.sort(key=lambda x: int(x['id']), reverse=True)
    
    print(f"🆕 Found {len(new_articles)} new articles to mirror")
    print(f"   Processing articles...\n")
    
    created_count = 0
    failed_count = 0
    new_mirrored_ids = []
    
    for i, article in enumerate(new_articles, 1):
        title_preview = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
        print(f"[{i}/{len(new_articles)}] {title_preview}")
        print(f"    ID: {article['id']} | Points: {article.get('points', 0)}")
        
        try:
            # Fetch detailed content
            article = fetch_article_details(article)
            
            # Create Jekyll post
            if create_jekyll_post(article):
                created_count += 1
                new_mirrored_ids.append(article['id'])
                print(f"    ✓ Successfully created post\n")
            else:
                failed_count += 1
                print(f"    ✗ Failed to create post\n")
        except Exception as e:
            failed_count += 1
            print(f"    ✗ Error: {e}\n")
        
        # Be polite - don't hammer the server
        if i < len(new_articles):
            time.sleep(1)
    
    # Update mirrored IDs
    if new_mirrored_ids:
        mirror_data['mirrored_ids'].extend(new_mirrored_ids)
        mirror_data['last_update'] = datetime.now().isoformat()
        save_mirrored_posts(mirror_data)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Sync complete!")
    print(f"   📝 Created: {created_count} new posts")
    if failed_count > 0:
        print(f"   ⚠️  Failed: {failed_count} posts")
    print(f"   📊 Total tracked: {len(mirror_data['mirrored_ids'])} articles")
    print(f"   🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Exit with error code if all failed
    if created_count == 0 and failed_count > 0:
        exit(1)

if __name__ == "__main__":
    main()

