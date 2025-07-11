#!/usr/bin/env python3
"""
Paul Graham文章爬虫 - 最终版
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

def clean_filename(filename):
    """清理文件名，移除非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def main():
    # 基础设置 - 使用HTTPS
    base_url = "https://paulgraham.com/"
    articles_url = "https://paulgraham.com/articles.html"
    
    # 创建会话
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    # 步骤1: 获取文章列表
    print("正在获取文章列表...")
    try:
        response = session.get(articles_url, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
    except Exception as e:
        print(f"获取文章列表失败: {e}")
        return
    
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
    
    # 限制数量（可根据需要调整）
    max_articles = min(20, len(articles))  # 先抓取前20篇
    articles = articles[:max_articles]
    
    # 创建输出目录
    if not os.path.exists('articles'):
        os.makedirs('articles')
    
    # 步骤2: 配置html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0
    h.ignore_images = True
    
    scraped_articles = []
    failed_count = 0
    
    # 步骤3: 抓取文章
    for i, article in enumerate(articles):
        print(f"\n进度: {i+1}/{max_articles}")
        print(f"正在抓取: {article['title']}")
        
        try:
            # 获取文章内容
            resp = session.get(article['url'], timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            
            # 解析HTML
            article_soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找主要内容
            # Paul Graham的文章通常在table中，但也可能在其他容器中
            content = None
            
            # 尝试多种查找方式
            # 1. 查找包含大量文本的table
            tables = article_soup.find_all('table')
            for table in tables:
                text_length = len(table.get_text(strip=True))
                if text_length > 500:
                    content = table
                    break
            
            # 2. 如果没找到合适的table，查找主要的div或article标签
            if not content:
                for tag in ['article', 'div', 'main']:
                    elements = article_soup.find_all(tag)
                    for elem in elements:
                        text_length = len(elem.get_text(strip=True))
                        if text_length > 500:
                            content = elem
                            break
                    if content:
                        break
            
            # 3. 最后尝试body
            if not content:
                content = article_soup.body
            
            # 转换为Markdown
            if content:
                # 移除脚本和样式
                for tag in content(['script', 'style']):
                    tag.decompose()
                
                markdown_text = h.handle(str(content))
                
                # 添加标题和清理
                markdown_text = f"# {article['title']}\n\n{markdown_text}"
                
                # 清理多余的空行
                markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
                
                # 保存Markdown文件
                filename = clean_filename(article['title']) + '.md'
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
            else:
                print("✗ 未找到文章内容")
                failed_count += 1
            
        except requests.exceptions.RequestException as e:
            print(f"✗ 网络错误: {e}")
            failed_count += 1
        except Exception as e:
            print(f"✗ 抓取失败: {e}")
            failed_count += 1
        
        # 延迟避免过快请求
        time.sleep(2)
    
    # 保存元数据
    metadata = {
        'total_articles': len(articles),
        'scraped_count': len(scraped_articles),
        'failed_count': failed_count,
        'articles': scraped_articles
    }
    
    with open('articles_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # 步骤4: 创建EPUB
    if scraped_articles:
        print("\n正在创建EPUB电子书...")
        
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title("Paul Graham Essays")
        book.set_language('en')
        book.add_author('Paul Graham')
        
        # 添加封面页
        cover_html = epub.EpubHtml(
            title='Cover',
            file_name='cover.xhtml',
            lang='en'
        )
        cover_html.content = f'''
        <html>
        <body>
            <h1>Paul Graham Essays</h1>
            <p>A collection of {len(scraped_articles)} essays by Paul Graham</p>
            <p>Scraped from paulgraham.com</p>
        </body>
        </html>
        '''
        book.add_item(cover_html)
        
        # 创建章节
        chapters = [cover_html]
        
        for i, article in enumerate(scraped_articles):
            chapter = epub.EpubHtml(
                title=article['title'],
                file_name=f'chapter_{i+1}.xhtml',
                lang='en'
            )
            
            # 读取Markdown文件并转换
            with open(article['filepath'], 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 简单的Markdown到HTML转换
            html_content = '<html><body>\n'
            html_content += f'<h1>{article["title"]}</h1>\n'
            
            # 转换段落
            paragraphs = markdown_content.split('\n\n')
            for p in paragraphs[1:]:  # 跳过标题
                p = p.strip()
                if p:
                    # 处理基本的Markdown语法
                    # 粗体
                    p = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', p)
                    # 斜体
                    p = re.sub(r'\*(.*?)\*', r'<em>\1</em>', p)
                    # 链接
                    p = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', p)
                    
                    html_content += f'<p>{p}</p>\n'
            
            html_content += '</body></html>'
            
            chapter.content = html_content
            book.add_item(chapter)
            chapters.append(chapter)
        
        # 设置目录和书脊
        book.toc = chapters[1:]  # 不包括封面页
        book.spine = chapters
        
        # 添加导航
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 添加CSS样式
        style = '''
        body { font-family: Georgia, serif; margin: 1em; }
        h1 { font-size: 1.5em; margin-bottom: 1em; }
        p { margin: 1em 0; line-height: 1.6; }
        a { color: #0066cc; }
        '''
        
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)
        
        # 保存EPUB
        epub_filename = 'paul_graham_essays.epub'
        epub.write_epub(epub_filename, book)
        print(f"✓ EPUB已创建: {epub_filename}")
    
    print(f"\n完成! 共成功抓取 {len(scraped_articles)} 篇文章，失败 {failed_count} 篇")
    print(f"文章保存在 articles/ 目录")
    print(f"EPUB电子书: paul_graham_essays.epub")
    print(f"元数据: articles_metadata.json")

if __name__ == "__main__":
    main()