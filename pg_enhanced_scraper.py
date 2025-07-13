#!/usr/bin/env python3
"""
Paul Graham文章爬虫 - 增强版
支持：
1. 缓存机制（避免重复抓取）
2. 文章按日期排序
3. EPUB中显示原文链接
4. 生成PDF
5. 生成时间戳
"""

import os
import re
import json
import time
import hashlib
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import html2text
from urllib.parse import urljoin
from ebooklib import epub
import uuid
import weasyprint
from pathlib import Path

class EnhancedPaulGrahamScraper:
    def __init__(self, cache_dir="cache", output_dir="output"):
        self.base_url = "https://paulgraham.com/"
        self.articles_url = "https://paulgraham.com/articles.html"
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # 加载缓存索引
        self.cache_index_path = self.cache_dir / "cache_index.json"
        self.cache_index = self.load_cache_index()
        
        # HTML转Markdown配置
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.body_width = 0
        self.h2t.ignore_images = True
    
    def load_cache_index(self):
        """加载缓存索引"""
        if self.cache_index_path.exists():
            with open(self.cache_index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_cache_index(self):
        """保存缓存索引"""
        with open(self.cache_index_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
    
    def get_cache_key(self, url):
        """生成缓存键"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get_cached_article(self, url):
        """获取缓存的文章"""
        cache_key = self.get_cache_key(url)
        if cache_key in self.cache_index:
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return None
    
    def save_to_cache(self, url, data):
        """保存文章到缓存"""
        cache_key = self.get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.cache_index[cache_key] = {
            'url': url,
            'title': data['title'],
            'cached_at': datetime.now().isoformat()
        }
        self.save_cache_index()
    
    def extract_date(self, html_content):
        """提取文章日期（改进版）"""
        # 尝试多种日期格式
        date_patterns = [
            r'([A-Z][a-z]+ \d{4})',  # "July 2023"
            r'(\d{1,2} [A-Z][a-z]+ \d{4})',  # "1 July 2023"
            r'([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',  # "July 1, 2023"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, html_content)
            if match:
                date_str = match.group(1)
                # 尝试解析日期
                try:
                    # 尝试不同的日期格式
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
                except:
                    pass
        
        return None
    
    def scrape_article(self, url, title, use_cache=True):
        """抓取单篇文章"""
        # 检查缓存
        if use_cache:
            cached = self.get_cached_article(url)
            if cached:
                print(f"✓ 使用缓存: {title}")
                return cached
        
        print(f"⬇ 正在抓取: {title}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找主要内容
            content = None
            # 优先查找table
            tables = soup.find_all('table')
            for table in tables:
                if len(table.get_text(strip=True)) > 500:
                    content = table
                    break
            
            # 备选方案
            if not content:
                for tag in ['article', 'div', 'main']:
                    elements = soup.find_all(tag)
                    for elem in elements:
                        if len(elem.get_text(strip=True)) > 500:
                            content = elem
                            break
                    if content:
                        break
            
            if not content:
                content = soup.body
            
            # 清理内容
            if content:
                for tag in content(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
            
            # 转换为Markdown
            markdown_text = self.h2t.handle(str(content)) if content else ""
            
            # 提取日期
            date_info = self.extract_date(response.text)
            
            article_data = {
                'title': title,
                'url': url,
                'markdown': f"# {title}\n\n{markdown_text}",
                'date': date_info,
                'scraped_at': datetime.now().isoformat()
            }
            
            # 保存到缓存
            self.save_to_cache(url, article_data)
            
            return article_data
            
        except Exception as e:
            print(f"✗ 抓取失败: {e}")
            return None
    
    def get_article_list(self):
        """获取文章列表"""
        print("正在获取文章列表...")
        response = self.session.get(self.articles_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.html') and href != 'articles.html':
                title = link.get_text(strip=True)
                if title:
                    articles.append({
                        'url': urljoin(self.base_url, href),
                        'title': title
                    })
        
        return articles
    
    def create_enhanced_epub(self, articles, filename=None):
        """创建增强版EPUB（包含原文链接和日期）"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"paul_graham_essays_{timestamp}.epub"
        
        filepath = self.output_dir / filename
        
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title("Paul Graham Essays Collection")
        book.set_language('en')
        book.add_author('Paul Graham')
        
        # 添加元数据
        book.add_metadata('DC', 'description', f'Collection of {len(articles)} essays by Paul Graham')
        book.add_metadata('DC', 'date', datetime.now().strftime('%Y-%m-%d'))
        
        # 创建封面
        cover_html = epub.EpubHtml(
            title='Cover',
            file_name='cover.xhtml',
            lang='en'
        )
        
        # 计算日期范围
        dated_articles = [a for a in articles if a.get('date')]
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
            articles,
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
            paragraphs = article['markdown'].split('\n\n')
            for p in paragraphs[1:]:  # 跳过标题
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
        return str(filepath)
    
    def create_pdf(self, articles, filename=None):
        """生成PDF文件"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"paul_graham_essays_{timestamp}.pdf"
        
        filepath = self.output_dir / filename
        
        # 按日期排序
        sorted_articles = sorted(
            articles,
            key=lambda x: x['date']['parsed'] if x.get('date') else datetime(1900, 1, 1),
            reverse=True
        )
        
        # 生成HTML
        html_content = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Paul Graham Essays</title>
            <style>
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-family: Georgia, 'Times New Roman', serif;
                    line-height: 1.6;
                    color: #333;
                }
                h1 {
                    font-size: 24pt;
                    margin-bottom: 0.5em;
                    page-break-after: avoid;
                }
                h2 {
                    font-size: 18pt;
                    margin-top: 1em;
                    margin-bottom: 0.5em;
                    page-break-after: avoid;
                }
                .article {
                    page-break-before: always;
                }
                .article:first-child {
                    page-break-before: avoid;
                }
                .metadata {
                    font-style: italic;
                    color: #666;
                    margin-bottom: 1em;
                }
                .toc {
                    page-break-after: always;
                }
                .toc li {
                    margin: 0.5em 0;
                }
                a {
                    color: #0066cc;
                    text-decoration: none;
                }
                p {
                    margin: 0.8em 0;
                    text-align: justify;
                }
                .cover {
                    text-align: center;
                    page-break-after: always;
                    padding-top: 10em;
                }
            </style>
        </head>
        <body>
        '''
        
        # 封面
        html_content += f'''
        <div class="cover">
            <h1>Paul Graham Essays</h1>
            <h2>Complete Collection</h2>
            <p>{len(articles)} Essays</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        '''
        
        # 目录
        html_content += '<div class="toc"><h1>Table of Contents</h1><ol>'
        for article in sorted_articles:
            html_content += f'<li>{article["title"]}'
            if article.get('date'):
                html_content += f' <em>({article["date"]["original"]})</em>'
            html_content += '</li>'
        html_content += '</ol></div>'
        
        # 文章内容
        for article in sorted_articles:
            html_content += f'<div class="article">'
            html_content += f'<h1>{article["title"]}</h1>'
            
            html_content += '<div class="metadata">'
            if article.get('date'):
                html_content += f'{article["date"]["original"]}<br/>'
            html_content += f'<a href="{article["url"]}">{article["url"]}</a>'
            html_content += '</div>'
            
            # 处理markdown内容
            content = article['markdown'].replace(f"# {article['title']}", "")
            
            # 简单的Markdown到HTML转换
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
            content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', content)
            
            paragraphs = content.strip().split('\n\n')
            for p in paragraphs:
                if p.strip():
                    if p.startswith('#'):
                        level = len(p) - len(p.lstrip('#'))
                        html_content += f'<h{min(level+1, 6)}>{p.lstrip("#").strip()}</h{min(level+1, 6)}>'
                    else:
                        html_content += f'<p>{p.strip()}</p>'
            
            html_content += '</div>'
        
        html_content += '</body></html>'
        
        # 生成PDF
        print("正在生成PDF...")
        weasyprint.HTML(string=html_content).write_pdf(str(filepath))
        print(f"✓ PDF已创建: {filepath}")
        return str(filepath)
    
    def run(self, max_articles=None, generate_pdf=True):
        """运行爬虫"""
        # 获取文章列表
        articles = self.get_article_list()
        print(f"找到 {len(articles)} 篇文章")
        
        if max_articles:
            articles = articles[:max_articles]
            print(f"将处理前 {len(articles)} 篇文章")
        
        # 抓取文章
        scraped_articles = []
        failed_count = 0
        
        for i, article_info in enumerate(articles):
            print(f"\n进度: {i+1}/{len(articles)}")
            
            article_data = self.scrape_article(
                article_info['url'],
                article_info['title'],
                use_cache=True
            )
            
            if article_data:
                scraped_articles.append(article_data)
            else:
                failed_count += 1
            
            # 如果不是从缓存读取，添加延迟
            if article_data and article_data.get('scraped_at') == datetime.now().isoformat()[:10]:
                time.sleep(1.5)
        
        print(f"\n抓取完成！成功: {len(scraped_articles)}，失败: {failed_count}")
        
        # 保存元数据
        metadata = {
            'total_articles': len(articles),
            'scraped_count': len(scraped_articles),
            'failed_count': failed_count,
            'generated_at': datetime.now().isoformat(),
            'articles': scraped_articles
        }
        
        metadata_path = self.output_dir / f"metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 生成EPUB
        if scraped_articles:
            epub_file = self.create_enhanced_epub(scraped_articles)
            
            # 生成PDF
            if generate_pdf:
                try:
                    pdf_file = self.create_pdf(scraped_articles)
                except Exception as e:
                    print(f"PDF生成失败: {e}")
                    print("可能需要安装weasyprint的系统依赖")
        
        return scraped_articles

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Paul Graham文章爬虫 - 增强版')
    parser.add_argument('--max', type=int, help='最多抓取的文章数量')
    parser.add_argument('--no-pdf', action='store_true', help='不生成PDF')
    parser.add_argument('--force', action='store_true', help='强制重新抓取（忽略缓存）')
    
    args = parser.parse_args()
    
    scraper = EnhancedPaulGrahamScraper()
    
    if args.force:
        # 清空缓存
        print("清空缓存...")
        scraper.cache_index = {}
        scraper.save_cache_index()
    
    scraper.run(
        max_articles=args.max,
        generate_pdf=not args.no_pdf
    )

if __name__ == "__main__":
    main()