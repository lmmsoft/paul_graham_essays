#!/usr/bin/env python3
"""
测试爬虫 - 先抓取几篇文章测试
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 设置基础URL
base_url = "http://www.paulgraham.com/"
articles_url = "http://www.paulgraham.com/articles.html"

# 创建会话
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

print("正在获取文章列表...")
response = session.get(articles_url)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

# 获取前5篇文章链接
links = []
for link in soup.find_all('a', href=True):
    href = link['href']
    if href.endswith('.html') and href != 'articles.html':
        full_url = urljoin(base_url, href)
        title = link.get_text(strip=True)
        if title:
            links.append({
                'url': full_url,
                'title': title,
                'filename': href
            })
            if len(links) >= 5:
                break

print(f"\n找到的前5篇文章:")
for i, link in enumerate(links, 1):
    print(f"{i}. {link['title']} - {link['url']}")