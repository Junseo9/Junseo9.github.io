---
layout: default
title: Categories
---

<div class="categories">
  <h1>Categories</h1>
  <ul>
    {% for category in site.categories %}
      <li>
        <h2>{{ category[0] }}</h2>
        <ul>
          {% for post in category[1] %}
            <li><a href="{{ post.url | relative_url }}">{{ post.title }}</a></li>
          {% endfor %}
        </ul>
      </li>
    {% endfor %}
  </ul>
</div>