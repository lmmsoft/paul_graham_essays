#!/usr/bin/env python3
"""
从已有文章重新生成增强版EPUB（支持旧格式）
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from ebooklib import epub
import uuid

def parse_date_from_markdown(markdown_text):
    """从Markdown文本中提取日期"""
    # 尝试多种日期格式
    date_patterns = [
        r'([A-Z][a-z]+ \d{4})',  # "July 2023"
        r'(\d{1,2} [A-Z][a-z]+ \d{4})',  # "1 July 2023"
        r'([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',  # "July 1, 2023"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, markdown_text)
        if match:
            date_str = match.group(1)
            # 尝试解析日期
            for fmt in ['%B %Y', '%d %B %Y', '%B %d, %Y']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return {
                        'original': date_str,
                        'parsed': parsed_date,
                        'sortable': parsed_date.strftime('%Y-%m-%d')
                    }
                except ValueError:
                    continue
    
    return None

def create_enhanced_epub_from_existing(articles, output_dir="output"):
    """从现有文章创建增强版EPUB"""
    
    Path(output_dir).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"paul_graham_essays_enhanced_{timestamp}.epub"
    filepath = Path(output_dir) / filename
    
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title("Paul Graham Essays Collection")
    book.set_language('en')
    book.add_author('Paul Graham')
    
    # 添加元数据
    book.add_metadata('DC', 'description', f'Collection of {len(articles)} essays by Paul Graham')
    book.add_metadata('DC', 'date', datetime.now().strftime('%Y-%m-%d'))
    
    # 处理文章，提取日期
    processed_articles = []
    for article in articles:
        # 如果没有date字段或者date是字符串，从markdown中提取
        if not article.get('date') or isinstance(article.get('date'), str):
            date_info = parse_date_from_markdown(article.get('markdown', ''))
            article['date'] = date_info
        processed_articles.append(article)
    
    # 创建封面
    cover_html = epub.EpubHtml(
        title='Cover',
        file_name='cover.xhtml',
        lang='en'
    )
    
    # 计算日期范围
    dated_articles = [a for a in processed_articles if a.get('date')]
    if dated_articles:
        dates = [a['date']['parsed'] for a in dated_articles]
        min_date = min(dates).strftime('%B %Y')
        max_date = max(dates).strftime('%B %Y')
        date_range = f"{min_date} - {max_date}"
    else:
        date_range = "Various dates"
    
    cover_html.content = f'''
    <html>
    <body>
        <h1>Paul Graham Essays</h1>
        <h2>Complete Collection</h2>
        <p>A collection of {len(articles)} essays</p>
        <p>Date range: {date_range}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr/>
        <p><small>This ebook was created for personal reading. All content © Paul Graham.</small></p>
    </body>
    </html>
    '''
    book.add_item(cover_html)
    
    # 按日期排序文章（新的在前）
    sorted_articles = sorted(
        processed_articles,
        key=lambda x: x['date']['parsed'] if x.get('date') else datetime(1900, 1, 1),
        reverse=True
    )
    
    # 创建目录页
    toc_html = epub.EpubHtml(
        title='Table of Contents',
        file_name='toc.xhtml',
        lang='en'
    )
    
    toc_content = '<html><body><h1>Table of Contents</h1><ol>'
    for article in sorted_articles:
        toc_content += f'<li>{article["title"]}'
        if article.get('date'):
            toc_content += f' <em>({article["date"]["original"]})</em>'
        toc_content += '</li>'
    toc_content += '</ol></body></html>'
    toc_html.content = toc_content
    book.add_item(toc_html)
    
    # 创建章节
    chapters = [cover_html, toc_html]
    
    for i, article in enumerate(sorted_articles):
        chapter = epub.EpubHtml(
            title=article['title'],
            file_name=f'essay_{i+1}.xhtml',
            lang='en'
        )
        
        # 构建HTML内容
        html_content = '<html><body>\n'
        html_content += f'<h1>{article["title"]}</h1>\n'
        
        # 显示日期和原文链接
        if article.get('date'):
            html_content += f'<p><em>{article["date"]["original"]}</em></p>\n'
        html_content += f'<p><small>Original: <a href="{article["url"]}">{article["url"]}</a></small></p>\n'
        html_content += '<hr/>\n'
        
        # 处理正文
        markdown_content = article.get('markdown', '')
        # 移除标题行（避免重复）
        markdown_content = re.sub(r'^#\s+.*\n+', '', markdown_content)
        
        paragraphs = markdown_content.split('\n\n')
        for p in paragraphs:
            p = p.strip()
            if p:
                # 处理Markdown语法
                p = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', p)
                p = re.sub(r'\*(.*?)\*', r'<em>\1</em>', p)
                p = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', p)
                
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
        color: #666;
    }
    strong {
        font-weight: bold;
    }
    small {
        font-size: 0.9em;
        color: #888;
    }
    hr {
        border: none;
        border-top: 1px solid #ddd;
        margin: 1em 0;
    }
    ol li {
        margin: 0.5em 0;
    }
    '''
    
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)
    
    # 写入EPUB
    epub.write_epub(str(filepath), book)
    print(f"✓ EPUB已创建: {filepath}")
    print(f"  文件大小: {os.path.getsize(filepath) / 1024 / 1024:.2f} MB")
    return str(filepath)

def main():
    """主函数"""
    # 查找现有的元数据文件
    metadata_files = [
        'pg_essays_metadata.json',
        'articles_metadata.json'
    ]
    
    articles = []
    
    for filename in metadata_files:
        if os.path.exists(filename):
            print(f"找到元数据文件: {filename}")
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'scraped_articles' in data:
                    articles = data['scraped_articles']
                elif 'articles' in data:
                    articles = data['articles']
                break
    
    if not articles:
        print("没有找到已有的文章数据")
        return
    
    print(f"找到 {len(articles)} 篇文章")
    print("\n正在生成增强版EPUB...")
    
    # 创建增强版EPUB
    epub_file = create_enhanced_epub_from_existing(articles)
    
    print("\n完成！")
    print(f"- 按日期排序（最新在前）")
    print(f"- 每篇文章都包含原文链接")
    print(f"- 生成时间戳已添加")

if __name__ == "__main__":
    main()