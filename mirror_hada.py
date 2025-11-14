import feedparser
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

def main():
    # Load existing data
    if os.path.exists('.hada_mirror_data.json'):
        with open('.hada_mirror_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {'mirrored_ids': [], 'last_update': datetime.now().isoformat()}

    mirrored = set(data['mirrored_ids'])

    # Fetch RSS feed
    feed = feedparser.parse('https://news.hada.io/rss/news')

    new_posts = []

    for entry in feed.entries:
        # Extract ID from link
        link_parts = entry.link.split('=')
        if len(link_parts) > 1:
            post_id = link_parts[-1]
        else:
            continue

        if post_id in mirrored:
            continue

        # Fetch the topic page
        try:
            resp = requests.get(entry.link, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch {entry.link}: {e}")
            continue

        soup = BeautifulSoup(resp.content, 'lxml')

        # Extract title
        title_elem = soup.find('h1')
        title = title_elem.text.strip() if title_elem else entry.title

        # Extract content: find paragraphs after the main external link
        main_link = soup.find('a', href=lambda h: h and isinstance(h, str) and h.startswith('http') and 'hada.io' not in h)
        content = ''
        if main_link and main_link.parent:
            content_parts = []
            for sibling in main_link.parent.find_next_siblings(['p', 'ul', 'ol', 'blockquote']):
                content_parts.append(sibling.get_text())
            content = '\n\n'.join(content_parts)
        if not content and hasattr(entry, 'content'):
            # Parse HTML content from RSS
            rss_content = BeautifulSoup(entry.content[0].value, 'lxml').get_text()
            content = rss_content
        elif not content:
            content = entry.summary if hasattr(entry, 'summary') else ''

        # Parse date
        try:
            # RSS has published as 2025-11-14T20:02:12+09:00
            pub_date = datetime.fromisoformat(entry.published.replace('Z', '+00:00').replace('+09:00', ''))
        except:
            pub_date = datetime.now()

        # Create filename
        safe_title = ''.join(c for c in title if c.isalnum() or c in ' -').rstrip()
        filename = f"{pub_date.strftime('%Y-%m-%d')}-{safe_title.replace(' ', '-').lower()}.md"

        # Jekyll front matter
        front_matter = f"""---
title: "{title.replace('"', '\\"')}"
date: {pub_date.isoformat()}
categories: news
tags: mirror
original_url: {entry.link}
source: news.hada.io
---

{content}
"""

        # Ensure _posts directory exists
        os.makedirs('_posts', exist_ok=True)

        # Write the post
        with open(f'_posts/{filename}', 'w', encoding='utf-8') as f:
            f.write(front_matter)

        new_posts.append(post_id)
        print(f"Mirrored post: {title}")

    # Update data
    data['mirrored_ids'].extend(new_posts)
    data['last_update'] = datetime.now().isoformat()

    with open('.hada_mirror_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Mirrored {len(new_posts)} new posts.")

if __name__ == '__main__':
    main()