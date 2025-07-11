#!/usr/bin/env python3
"""
Paul Graham文章爬虫 - 完整版
抓取所有文章并生成完整的EPUB电子书
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
import sys

def clean_filename(filename):
    """清理文件名，移除非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def main():
    # 询问用户是否要抓取所有文章
    print("Paul Graham文章爬虫")
    print("-" * 40)
    print("已成功测试，可以抓取文章。")
    print("网站上共有232篇文章。")
    print("\n选项：")
    print("1. 抓取前50篇文章（推荐，约需5-10分钟）")
    print("2. 抓取所有232篇文章（约需30-60分钟）")
    print("3. 自定义数量")
    print("4. 退出")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == '1':
        max_articles = 50
    elif choice == '2':
        max_articles = None  # 抓取所有
    elif choice == '3':
        try:
            max_articles = int(input("请输入要抓取的文章数量: "))
        except ValueError:
            print("无效输入，使用默认50篇")
            max_articles = 50
    else:
        print("退出程序")
        return
    
    # 基础设置
    base_url = "https://paulgraham.com/"
    articles_url = "https://paulgraham.com/articles.html"
    
    # 创建会话
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    # 获取文章列表
    print("\n正在获取文章列表...")
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
    
    # 限制数量
    if max_articles:
        articles = articles[:max_articles]
        print(f"将抓取前 {len(articles)} 篇文章")
    
    # 创建输出目录
    if not os.path.exists('pg_essays'):
        os.makedirs('pg_essays')
    
    # 配置html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0
    h.ignore_images = True
    
    scraped_articles = []
    failed_articles = []
    
    # 抓取文章
    print("\n开始抓取文章...")
    for i, article in enumerate(articles):
        print(f"\r进度: {i+1}/{len(articles)} - {article['title'][:50]}...", end='', flush=True)
        
        try:
            # 获取文章内容
            resp = session.get(article['url'], timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            
            # 解析HTML
            article_soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找主要内容
            content = None
            
            # 查找包含大量文本的table
            tables = article_soup.find_all('table')
            for table in tables:
                text_length = len(table.get_text(strip=True))
                if text_length > 500:
                    content = table
                    break
            
            # 如果没找到，尝试其他容器
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
            
            # 最后尝试body
            if not content:
                content = article_soup.body
            
            # 转换为Markdown
            if content:
                # 移除脚本和样式
                for tag in content(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                markdown_text = h.handle(str(content))
                
                # 添加标题
                markdown_text = f"# {article['title']}\n\n{markdown_text}"
                
                # 清理多余的空行
                markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
                
                # 保存Markdown文件
                filename = clean_filename(article['title']) + '.md'
                filepath = os.path.join('pg_essays', filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_text)
                
                # 尝试提取日期
                date_match = re.search(r'([A-Z][a-z]+ \d{4})', resp.text)
                date = date_match.group(1) if date_match else None
                
                scraped_articles.append({
                    'title': article['title'],
                    'url': article['url'],
                    'markdown': markdown_text,
                    'filepath': filepath,
                    'date': date
                })
            else:
                failed_articles.append(article)
            
        except Exception as e:
            failed_articles.append({**article, 'error': str(e)})
        
        # 延迟避免过快请求
        time.sleep(1.5)
    
    print("\n\n抓取完成！")
    print(f"成功: {len(scraped_articles)} 篇")
    print(f"失败: {len(failed_articles)} 篇")
    
    # 保存元数据
    metadata = {
        'total_found': len(articles),
        'scraped_count': len(scraped_articles),
        'failed_count': len(failed_articles),
        'scraped_articles': scraped_articles,
        'failed_articles': failed_articles
    }
    
    with open('pg_essays_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # 创建EPUB
    if scraped_articles:
        print("\n正在创建EPUB电子书...")
        
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title("Paul Graham Essays Collection")
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
            <h2>Complete Collection</h2>
            <p>A collection of {len(scraped_articles)} essays by Paul Graham</p>
            <p>Source: paulgraham.com</p>
            <hr/>
            <p><small>This ebook was created for personal reading. All content belongs to Paul Graham.</small></p>
        </body>
        </html>
        '''
        book.add_item(cover_html)
        
        # 添加目录页
        toc_html = epub.EpubHtml(
            title='Table of Contents',
            file_name='toc.xhtml',
            lang='en'
        )
        toc_content = '<html><body><h1>Table of Contents</h1><ol>'
        for article in scraped_articles:
            toc_content += f'<li>{article["title"]}'
            if article.get('date'):
                toc_content += f' ({article["date"]})'
            toc_content += '</li>'
        toc_content += '</ol></body></html>'
        toc_html.content = toc_content
        book.add_item(toc_html)
        
        # 创建章节
        chapters = [cover_html, toc_html]
        
        for i, article in enumerate(scraped_articles):
            chapter = epub.EpubHtml(
                title=article['title'],
                file_name=f'essay_{i+1}.xhtml',
                lang='en'
            )
            
            # 读取Markdown文件
            with open(article['filepath'], 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 转换为HTML
            html_content = '<html><body>\n'
            html_content += f'<h1>{article["title"]}</h1>\n'
            if article.get('date'):
                html_content += f'<p><em>{article["date"]}</em></p>\n'
            
            # 处理段落
            paragraphs = markdown_content.split('\n\n')
            for p in paragraphs[1:]:
                p = p.strip()
                if p:
                    # 处理Markdown语法
                    p = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', p)
                    p = re.sub(r'\*(.*?)\*', r'<em>\1</em>', p)
                    p = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', p)
                    
                    # 处理标题
                    if p.startswith('#'):
                        level = len(p) - len(p.lstrip('#'))
                        p = f'<h{min(level, 6)}>{p.lstrip("#").strip()}</h{min(level, 6)}>'
                    else:
                        p = f'<p>{p}</p>'
                    
                    html_content += p + '\n'
            
            html_content += '</body></html>'
            
            chapter.content = html_content
            book.add_item(chapter)
            chapters.append(chapter)
        
        # 设置目录和书脊
        book.toc = chapters[2:]  # 不包括封面和目录页
        book.spine = chapters
        
        # 添加导航
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 添加CSS样式
        style = '''
        body { 
            font-family: Georgia, 'Times New Roman', serif; 
            margin: 1em 2em;
            line-height: 1.6;
        }
        h1 { 
            font-size: 1.8em; 
            margin: 1em 0 0.5em 0;
            color: #333;
        }
        h2 {
            font-size: 1.4em;
            margin: 1em 0 0.5em 0;
            color: #555;
        }
        p { 
            margin: 0.8em 0; 
            text-align: justify;
        }
        a { 
            color: #0066cc; 
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        em {
            font-style: italic;
        }
        strong {
            font-weight: bold;
        }
        '''
        
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)
        
        # 为所有章节添加CSS
        for chapter in chapters:
            if hasattr(chapter, 'add_item'):
                chapter.add_item(nav_css)
        
        # 保存EPUB
        epub_filename = f'paul_graham_essays_{len(scraped_articles)}_articles.epub'
        epub.write_epub(epub_filename, book)
        print(f"✓ EPUB已创建: {epub_filename}")
        print(f"  文件大小: {os.path.getsize(epub_filename) / 1024 / 1024:.2f} MB")
    
    print(f"\n所有文件已保存：")
    print(f"- Markdown文章: pg_essays/ 目录")
    print(f"- 元数据: pg_essays_metadata.json")
    if scraped_articles:
        print(f"- EPUB电子书: {epub_filename}")

if __name__ == "__main__":
    main()