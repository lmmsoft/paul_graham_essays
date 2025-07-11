#!/usr/bin/env python3
"""
Paul Graham文章爬虫
抓取所有文章并转换为Markdown格式
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urljoin
import json
from datetime import datetime
from ebooklib import epub
import uuid

class PaulGrahamScraper:
    def __init__(self):
        self.base_url = "http://www.paulgraham.com/"
        self.articles_url = "http://www.paulgraham.com/articles.html"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.articles = []
        
    def get_article_links(self):
        """获取所有文章链接"""
        print("正在获取文章列表...")
        response = self.session.get(self.articles_url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        # 查找所有以.html结尾的链接
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.html') and href != 'articles.html':
                full_url = urljoin(self.base_url, href)
                title = link.get_text(strip=True)
                if title:  # 确保有标题
                    links.append({
                        'url': full_url,
                        'title': title,
                        'filename': href
                    })
        
        print(f"找到 {len(links)} 篇文章")
        return links
    
    def extract_article_content(self, html_content):
        """从HTML中提取文章内容"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除script和style标签
        for script in soup(["script", "style"]):
            script.decompose()
            
        # 查找主要内容区域
        # Paul Graham的文章通常在table中
        content = None
        tables = soup.find_all('table')
        for table in tables:
            # 查找包含大量文本的table
            text_length = len(table.get_text(strip=True))
            if text_length > 1000:  # 假设文章至少1000字符
                content = table
                break
        
        if not content:
            # 如果没找到table，尝试获取body内容
            content = soup.body
            
        return str(content) if content else ""
    
    def html_to_markdown(self, html_content, title):
        """将HTML转换为Markdown"""
        # 配置html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # 不自动换行
        
        markdown = h.handle(html_content)
        
        # 添加标题
        markdown = f"# {title}\n\n{markdown}"
        
        return markdown
    
    def scrape_article(self, article_info):
        """抓取单篇文章"""
        url = article_info['url']
        title = article_info['title']
        
        print(f"正在抓取: {title}")
        
        try:
            response = self.session.get(url)
            response.encoding = 'utf-8'
            
            # 提取内容
            content_html = self.extract_article_content(response.text)
            
            # 转换为Markdown
            markdown_content = self.html_to_markdown(content_html, title)
            
            # 尝试从页面中提取日期
            date_match = re.search(r'(\w+ \d{4})', response.text)
            date = date_match.group(1) if date_match else None
            
            article_data = {
                'title': title,
                'url': url,
                'markdown': markdown_content,
                'date': date,
                'filename': article_info['filename']
            }
            
            return article_data
            
        except Exception as e:
            print(f"抓取失败 {title}: {e}")
            return None
    
    def save_markdown(self, article, output_dir="articles"):
        """保存Markdown文件"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 清理文件名
        filename = re.sub(r'[<>:"/\\|?*]', '_', article['title'])
        filename = f"{filename}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(article['markdown'])
            
        return filepath
    
    def create_epub(self, articles, output_file="paul_graham_essays.epub"):
        """创建EPUB电子书"""
        print("\n正在创建EPUB电子书...")
        
        book = epub.EpubBook()
        
        # 设置元数据
        book.set_identifier(str(uuid.uuid4()))
        book.set_title("Paul Graham Essays")
        book.set_language('en')
        book.add_author('Paul Graham')
        
        # 创建封面页
        cover_content = """
        <h1>Paul Graham Essays</h1>
        <p>A collection of essays by Paul Graham</p>
        <p>Total essays: {}</p>
        """.format(len(articles))
        
        # 目录
        toc = []
        spine = ['nav']
        
        # 添加每篇文章
        for i, article in enumerate(articles):
            # 创建章节
            chapter = epub.EpubHtml(
                title=article['title'],
                file_name=f"article_{i}.xhtml",
                lang='en'
            )
            
            # 将Markdown转换为HTML
            # 简单处理，实际可能需要更复杂的转换
            html_content = f"""
            <h1>{article['title']}</h1>
            {'<p><em>' + article['date'] + '</em></p>' if article['date'] else ''}
            {article['markdown'].replace('\n\n', '</p><p>').replace('\n', '<br/>')}
            """
            
            chapter.content = html_content
            
            # 添加到书籍
            book.add_item(chapter)
            toc.append(chapter)
            spine.append(chapter)
        
        # 添加目录
        book.toc = toc
        book.spine = spine
        
        # 添加导航文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 写入文件
        epub.write_epub(output_file, book, {})
        print(f"EPUB电子书已创建: {output_file}")
    
    def run(self):
        """运行爬虫"""
        # 获取文章列表
        article_links = self.get_article_links()
        
        # 抓取每篇文章
        for i, link in enumerate(article_links):
            print(f"\n进度: {i+1}/{len(article_links)}")
            article = self.scrape_article(link)
            
            if article:
                self.articles.append(article)
                # 保存Markdown
                self.save_markdown(article)
                
            # 延迟避免过快请求
            time.sleep(1)
        
        # 保存元数据
        with open('articles_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, ensure_ascii=False, indent=2)
        
        # 创建EPUB
        if self.articles:
            self.create_epub(self.articles)
        
        print(f"\n完成！共抓取 {len(self.articles)} 篇文章")

if __name__ == "__main__":
    scraper = PaulGrahamScraper()
    scraper.run()