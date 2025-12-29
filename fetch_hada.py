#!/usr/bin/env python3
import os
import re
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from xml.etree import ElementTree as ET

RSS_URL = "https://news.hada.io/rss/news"
POSTS_DIR = "_posts"

TECH_KEYWORDS = [
    'ai', 'artificial intelligence', '인공지능', 'llm', 'gpt', 'chatgpt', 'claude', 'gemini',
    'machine learning', '머신러닝', 'deep learning', '딥러닝', 'neural', '신경망',
    'transformer', 'diffusion', 'stable diffusion', 'midjourney', 'dall-e',
    'openai', 'anthropic', 'google ai', 'meta ai', 'deepmind',
    'langchain', 'rag', 'embedding', 'vector', 'fine-tuning', 'fine tuning',
    'prompt', '프롬프트', 'agent', '에이전트', 'copilot', '코파일럿',
    
    'computer', '컴퓨터', 'programming', '프로그래밍', 'coding', '코딩',
    'software', '소프트웨어', 'hardware', '하드웨어', 'developer', '개발자', '개발',
    'algorithm', '알고리즘', 'data structure', '자료구조',
    'python', 'javascript', 'typescript', 'rust', 'go', 'java', 'kotlin', 'swift',
    'c++', 'c#', 'ruby', 'php', 'scala', 'haskell', 'elixir', 'clojure',
    'react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt', 'node.js', 'deno', 'bun',
    'docker', 'kubernetes', 'k8s', 'aws', 'gcp', 'azure', 'cloud', '클라우드',
    'linux', 'unix', 'macos', 'windows', 'ubuntu', 'debian', 'arch',
    'git', 'github', 'gitlab', 'api', 'rest', 'graphql', 'grpc',
    'database', '데이터베이스', 'sql', 'nosql', 'postgresql', 'mysql', 'mongodb', 'redis',
    'frontend', '프론트엔드', 'backend', '백엔드', 'fullstack', '풀스택',
    'devops', 'ci/cd', 'terraform', 'ansible',
    'web', '웹', 'app', '앱', 'mobile', '모바일', 'ios', 'android',
    'security', '보안', 'crypto', '암호화', 'encryption', 'cybersecurity',
    'server', '서버', 'network', '네트워크', 'cpu', 'gpu', 'nvidia', 'amd', 'intel', 'apple silicon',
    'terminal', '터미널', 'cli', 'shell', 'bash', 'zsh',
    'ide', 'vscode', 'vim', 'neovim', 'emacs', 'jetbrains',
    'open source', '오픈소스', 'oss',
    'startup', '스타트업', 'tech', '테크', 'silicon valley',
    'engineer', '엔지니어', 'architecture', '아키텍처',
    
    'game', '게임', 'gaming', '게이밍', 'gamedev', '게임개발',
    'unity', 'unreal', 'godot', 'pygame',
    'steam', 'playstation', 'xbox', 'nintendo', 'switch',
    'esports', 'e스포츠', 'fps', 'mmorpg', 'rpg', 'moba',
    'graphics', '그래픽', 'rendering', '렌더링', '3d', 'opengl', 'vulkan', 'directx',
    'vr', 'ar', 'xr', 'metaverse', '메타버스', 'virtual reality', 'augmented reality',
]

EXCLUDE_KEYWORDS = [
    '부동산', '주식', '투자', '재테크', '금융', '대출', '보험',
    '다이어트', '헬스', '운동', '피트니스',
    '요리', '레시피', '맛집',
    '여행', '관광', '호텔',
    '패션', '뷰티', '화장품',
    '연예', '드라마', '영화', '배우', '아이돌',
    '정치', '선거', '국회',
    '스포츠', '축구', '야구', '농구',
]

def is_tech_related(title: str, content: str) -> bool:
    text = f"{title} {content}".lower()
    
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in text:
            return False
    
    for keyword in TECH_KEYWORDS:
        if keyword in text:
            return True
    
    return False

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

def html_to_markdown(html: str) -> str:
    text = html
    text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'## \1\n', text)
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)
    text = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text)
    text = re.sub(r'<li>(.*?)</li>', r'- \1\n', text)
    text = re.sub(r'<ul[^>]*>|</ul>', '', text)
    text = re.sub(r'<ol[^>]*>|</ol>', '', text)
    text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_topic_id(url: str) -> str | None:
    match = re.search(r'id=(\d+)', url)
    return match.group(1) if match else None

def slugify(text: str) -> str:
    text = re.sub(r'[^\w\s가-힣-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text[:50].strip('-')

def parse_datetime(dt_str: str) -> datetime:
    try:
        return datetime.fromisoformat(dt_str.replace('+09:00', '+0900').replace(':', ''))
    except:
        try:
            return datetime.strptime(dt_str[:19], '%Y-%m-%dT%H:%M:%S')
        except:
            return datetime.now()

def create_post(entry: dict) -> tuple[str, str]:
    published = parse_datetime(entry['published'])
    date_str = published.strftime('%Y-%m-%d')
    slug = slugify(entry['title'])
    filename = f"{date_str}-{slug}.md"
    
    content_md = html_to_markdown(entry['content_html'])
    
    frontmatter = f"""---
layout: post
title: "{entry['title'].replace('"', '\\"')}"
date: {published.strftime('%Y-%m-%d %H:%M:%S')} +0900
categories: geeknews
tags: [geeknews, hada]
author: {entry['author']}
original_url: {entry['topic_url']}
---

"""
    
    body = f"""> 이 글은 [GeekNews]({entry['topic_url']})에서 미러된 글입니다.
> 원문 작성자: [{entry['author']}]({entry['author_url']})

{content_md}

---

[GeekNews에서 원문 보기]({entry['topic_url']})
"""
    
    return filename, frontmatter + body

def parse_and_save(xml_content: str) -> tuple[int, int]:
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    root = ET.fromstring(xml_content)
    
    os.makedirs(POSTS_DIR, exist_ok=True)
    
    total = 0
    saved = 0
    
    for entry in root.findall('atom:entry', ns):
        total += 1
        title_el = entry.find('atom:title', ns)
        link_el = entry.find('atom:link', ns)
        entry_id = entry.find('atom:id', ns)
        published_el = entry.find('atom:published', ns)
        author_el = entry.find('atom:author/atom:name', ns)
        author_uri_el = entry.find('atom:author/atom:uri', ns)
        content_el = entry.find('atom:content', ns)
        
        title = title_el.text if title_el is not None and title_el.text else ''
        content_html = content_el.text if content_el is not None and content_el.text else ''
        content_text = strip_html_tags(content_html)
        
        if not is_tech_related(title, content_text):
            print(f"Skipped (not tech): {title[:50] if title else 'Untitled'}...")
            continue
        
        topic_id = extract_topic_id(entry_id.text) if entry_id is not None and entry_id.text else None
        
        entry_data = {
            'title': title,
            'topic_id': topic_id,
            'topic_url': f"https://news.hada.io/topic?id={topic_id}" if topic_id else '',
            'published': published_el.text if published_el is not None else '',
            'author': author_el.text if author_el is not None else 'unknown',
            'author_url': author_uri_el.text if author_uri_el is not None else '',
            'content_html': content_html,
        }
        
        filename, content = create_post(entry_data)
        filepath = os.path.join(POSTS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created: {filename}")
        saved += 1
    
    return saved, total

def main():
    print(f"Fetching RSS from {RSS_URL}...")
    xml_content = fetch_rss()
    
    print("Parsing and filtering posts (AI/Computer/Game only)...")
    saved, total = parse_and_save(xml_content)
    
    print(f"Done! Created {saved}/{total} posts (filtered for tech content).")

if __name__ == '__main__':
    main()
