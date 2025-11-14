# GeekNews Mirror

A blog that automatically mirrors content from [news.hada.io](https://news.hada.io/), built with Jekyll and hosted on GitHub Pages.

## 🚀 Quick Start - Create a New Post

### Method 1: Using the Python Script (Recommended)

Simply run:
```bash
python3 new_post.py
```

Or use the shortcut:
```bash
./post.sh
```

Then follow the prompts:
1. Enter your post title
2. Enter categories (optional)
3. Enter tags (optional)
4. Type your content (type 'END' on a new line when finished)
5. Choose whether to publish immediately (y/n)

**Example:**
```
Enter post title: My Amazing Day
Enter categories (comma-separated, or press Enter to skip): life, travel
Enter tags (comma-separated, or press Enter to skip): adventure, fun

📄 Enter your post content (type 'END' on a new line when done):
Today was an amazing day! I went to the beach and had a great time.

The weather was perfect and I met some interesting people.
END

🚀 Do you want to publish this post now? (y/n): y
```

### Method 2: Manual Creation

1. Create a new file in `_posts/` folder with the format: `YYYY-MM-DD-title.md`
2. Add frontmatter at the top:
```yaml
---
layout: post
title: "Your Post Title"
date: 2025-01-28 10:00:00 +0900
categories: blog
tags: [tag1, tag2]
---
```
3. Write your content below the frontmatter
4. Commit and push:
```bash
git add _posts/your-new-post.md
git commit -m "Add new post"
git push origin main
```

## 📝 Writing Tips

- Use markdown syntax for formatting
- Add images to `assets/images/` and reference them with `![Alt text](/assets/images/image.png)`
- Use headings (`##`, `###`) to structure your content
- Add code blocks with triple backticks

## 🎨 Customization

Edit `_config.yml` to customize:
- Site title and description
- Author information
- Social media links
- Theme settings

## 📁 Project Structure

```
.
├── _posts/          # Your blog posts go here
├── _layouts/        # Custom layouts (optional)
├── _includes/       # Reusable components (optional)
├── assets/          # Images, CSS, JS files
│   ├── css/
│   └── images/
├── about.md         # About page
├── archive.md       # Archive page
├── index.md         # Home page
├── _config.yml      # Site configuration
├── Gemfile          # Ruby dependencies
└── new_post.py      # Easy post creation script

```

## 🌐 View Your Blog

Your blog is live at: **https://Sungheyn.github.io**

Changes are automatically deployed when you push to the main branch (usually takes 2-3 minutes).

## 🛠️ Local Development (Optional)

To preview your blog locally before publishing:

```bash
bundle install
bundle exec jekyll serve
```

Then open http://localhost:4000 in your browser.

## 🔄 Automatic Content Mirroring

This blog automatically mirrors articles from [news.hada.io](https://news.hada.io/).

### Manual Mirroring

To manually run the mirror script:

```bash
pip install -r requirements.txt
python3 mirror_hada.py
```

The script will:
- Fetch new articles from news.hada.io
- Create Jekyll posts for each article
- Track already mirrored articles to avoid duplicates
- Save metadata in `.hada_mirror_data.json`

### Automatic Updates

A GitHub Actions workflow runs every 6 hours to automatically fetch and mirror new content. The workflow:
- Runs on a schedule (every 6 hours)
- Can be manually triggered from the Actions tab
- Automatically commits and pushes new posts

### Mirror Script Features

- **Duplicate Prevention**: Tracks mirrored article IDs to avoid duplicates
- **Metadata Extraction**: Extracts title, points, author, time, and external URLs
- **Content Fetching**: Fetches detailed content from article pages
- **Jekyll Integration**: Creates properly formatted Jekyll posts with frontmatter

## 📚 Resources

- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Markdown Guide](https://www.markdownguide.org/)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [news.hada.io](https://news.hada.io/) - Original source
