#!/usr/bin/env python3
"""
Paul Graham文章爬虫 - 简化版
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urljoin
import json
from ebooklib import epub
import uuid

def main():
    # 基础设置
    base_url = "http://www.paulgraham.com/"
    articles_url = "http://www.paulgraham.com/articles.html"
    
    # 创建会话
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    # 步骤1: 获取文章列表
    print("正在获取文章列表...")
    response = session.get(articles_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    articles = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.html') and href != 'articles.html':
            title = link.get_text(strip=True)
            if title:
                articles.append({
                    'url': urljoin(base_url, href),
                    'title': title,
                    'filename': href
                })
    
    print(f"找到 {len(articles)} 篇文章")
    
    # 创建输出目录
    if not os.path.exists('articles'):
        os.makedirs('articles')
    
    # 步骤2: 抓取文章
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0
    
    scraped_articles = []
    
    for i, article in enumerate(articles[:10]):  # 先只抓取前10篇测试
        print(f"\n进度: {i+1}/10")
        print(f"正在抓取: {article['title']}")
        
        try:
            # 获取文章内容
            resp = session.get(article['url'])
            resp.encoding = 'utf-8'
            
            # 解析HTML
            article_soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找主要内容 (Paul Graham的文章通常在table中)
            content = None
            tables = article_soup.find_all('table')
            for table in tables:
                text_length = len(table.get_text(strip=True))
                if text_length > 500:  # 假设文章至少500字符
                    content = table
                    break
            
            if not content:
                content = article_soup.body
            
            # 转换为Markdown
            if content:
                markdown_text = h.handle(str(content))
                markdown_text = f"# {article['title']}\n\n{markdown_text}"
                
                # 保存Markdown文件
                filename = re.sub(r'[<>:"/\\|?*]', '_', article['title']) + '.md'
                filepath = os.path.join('articles', filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_text)
                
                scraped_articles.append({
                    'title': article['title'],
                    'url': article['url'],
                    'markdown': markdown_text,
                    'filepath': filepath
                })
                
                print(f"✓ 成功保存: {filename}")
            
        except Exception as e:
            print(f"✗ 抓取失败: {e}")
        
        # 延迟避免过快请求
        time.sleep(1)
    
    # 步骤3: 创建EPUB
    if scraped_articles:
        print("\n正在创建EPUB电子书...")
        
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title("Paul Graham Essays (Sample)")
        book.set_language('en')
        book.add_author('Paul Graham')
        
        # 创建章节
        chapters = []
        for i, article in enumerate(scraped_articles):
            chapter = epub.EpubHtml(
                title=article['title'],
                file_name=f'chapter_{i}.xhtml',
                lang='en'
            )
            
            # 简单的Markdown到HTML转换
            html_content = f"<h1>{article['title']}</h1>\n"
            paragraphs = article['markdown'].split('\n\n')
            for p in paragraphs[1:]:  # 跳过标题
                if p.strip():
                    html_content += f"<p>{p.strip()}</p>\n"
            
            chapter.content = html_content
            book.add_item(chapter)
            chapters.append(chapter)
        
        # 设置目录和书脊
        book.toc = chapters
        book.spine = ['nav'] + chapters
        
        # 添加导航
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 保存EPUB
        epub_filename = 'paul_graham_essays_sample.epub'
        epub.write_epub(epub_filename, book)
        print(f"✓ EPUB已创建: {epub_filename}")
    
    print(f"\n完成! 共成功抓取 {len(scraped_articles)} 篇文章")

if __name__ == "__main__":
    main()