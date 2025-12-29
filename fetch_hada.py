#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from xml.etree import ElementTree as ET

RSS_URL = "https://news.hada.io/rss/news"
OUTPUT_DIR = "_data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "hada.json")

def fetch_rss() -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; JekyllBot/1.0; +https://github.com)'
    }
    req = Request(RSS_URL, headers=headers)
    
    try:
        with urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching RSS: {e}", file=sys.stderr)
        sys.exit(1)

def strip_html_tags(html: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', html)
    return re.sub(r'\s+', ' ', text).strip()

def extract_topic_id(url: str) -> str | None:
    match = re.search(r'id=(\d+)', url)
    return match.group(1) if match else None

def parse_atom_feed(xml_content: str) -> dict:
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(xml_content)
    
    feed_title = root.find('atom:title', ns)
    feed_subtitle = root.find('atom:subtitle', ns)
    feed_updated = root.find('atom:updated', ns)
    
    feed_data = {
        'title': feed_title.text if feed_title is not None else 'GeekNews',
        'subtitle': feed_subtitle.text if feed_subtitle is not None else '',
        'updated': feed_updated.text if feed_updated is not None else datetime.now().isoformat(),
        'source_url': 'https://news.hada.io',
        'fetched_at': datetime.now().isoformat(),
        'entries': []
    }
    
    for entry in root.findall('atom:entry', ns):
        title = entry.find('atom:title', ns)
        link = entry.find('atom:link', ns)
        entry_id = entry.find('atom:id', ns)
        updated = entry.find('atom:updated', ns)
        published = entry.find('atom:published', ns)
        author = entry.find('atom:author/atom:name', ns)
        author_uri = entry.find('atom:author/atom:uri', ns)
        content = entry.find('atom:content', ns)
        
        topic_id = extract_topic_id(entry_id.text) if entry_id is not None and entry_id.text else None
        link_href = link.get('href') if link is not None else ''
        content_html = content.text if content is not None and content.text else ''
        content_text = strip_html_tags(content_html)
        
        entry_data = {
            'title': title.text if title is not None else '',
            'link': link_href,
            'topic_id': topic_id,
            'topic_url': f"https://news.hada.io/topic?id={topic_id}" if topic_id else link_href,
            'updated': updated.text if updated is not None else '',
            'published': published.text if published is not None else '',
            'author': author.text if author is not None else '',
            'author_url': author_uri.text if author_uri is not None else '',
            'content_html': content_html,
            'content_text': content_text[:500] + '...' if len(content_text) > 500 else content_text,
        }
        
        feed_data['entries'].append(entry_data)
    
    return feed_data

def save_json(data: dict) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(data['entries'])} entries to {OUTPUT_FILE}")

def main():
    print(f"Fetching RSS from {RSS_URL}...")
    xml_content = fetch_rss()
    
    print("Parsing Atom feed...")
    feed_data = parse_atom_feed(xml_content)
    
    print(f"Found {len(feed_data['entries'])} entries")
    save_json(feed_data)
    
    print("Done!")

if __name__ == '__main__':
    main()
