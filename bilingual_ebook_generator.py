#!/usr/bin/env python3
"""
双语电子书生成器 - 支持EPUB和PDF格式的中英对照版本
"""

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from ebooklib import epub
from urllib.parse import urljoin

# 尝试导入weasyprint，如果失败则禁用PDF功能
try:
    import weasyprint
    PDF_AVAILABLE = True
except ImportError as e:
    print(f"警告：无法导入weasyprint，PDF功能将被禁用: {e}")
    PDF_AVAILABLE = False

from ebook_config import (
    EbookConfig, CSS_STYLES, DATE_PATTERNS, DATE_FORMATS, MARKDOWN_PROCESSING
)


class BilingualEbookGenerator:
    """双语电子书生成器"""
    
    def __init__(self):
        self.config = EbookConfig()
        self.english_dir = Path(self.config.ENGLISH_DIR)
        self.chinese_dir = Path(self.config.CHINESE_DIR)
        self.output_dir = Path(self.config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
        
        # 统计信息
        self.stats = {
            'total_articles': 0,
            'bilingual_articles': 0,
            'english_only': 0,
            'chinese_only': 0,
            'failed_processing': 0,
            'total_paragraphs': 0,
            'aligned_paragraphs': 0
        }
    
    def load_metadata(self) -> Optional[Dict]:
        """加载文章元数据"""
        metadata_file = Path(self.config.METADATA_FILE)
        if not metadata_file.exists():
            print(f"警告：元数据文件 {metadata_file} 不存在")
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'scraped_articles' in data:
                    return data['scraped_articles']
                elif 'articles' in data:
                    return data['articles']
                else:
                    return data
        except Exception as e:
            print(f"读取元数据失败: {e}")
            return None
    
    def find_article_pairs(self) -> List[Dict]:
        """找到英文和中文文章的对应关系"""
        english_files = {f.name: f for f in self.english_dir.glob("*.md")}
        chinese_files = {f.name: f for f in self.chinese_dir.glob("*.md")}
        
        article_pairs = []
        metadata = self.load_metadata()
        
        for filename in english_files.keys():
            if filename in chinese_files:
                pair_info = {
                    'filename': filename,
                    'english_file': english_files[filename],
                    'chinese_file': chinese_files[filename],
                    'metadata': None
                }
                
                # 查找对应的元数据
                if metadata:
                    for article in metadata:
                        if (article.get('filepath', '').endswith(filename) or 
                            filename.replace('.md', '') in article.get('title', '')):
                            pair_info['metadata'] = article
                            break
                
                article_pairs.append(pair_info)
        
        self.stats['total_articles'] = len(english_files)
        self.stats['bilingual_articles'] = len(article_pairs)
        self.stats['english_only'] = len(english_files) - len(article_pairs)
        self.stats['chinese_only'] = len(chinese_files) - len(article_pairs)
        
        print(f"找到 {len(article_pairs)} 篇双语文章（英文 {len(english_files)} 篇，中文 {len(chinese_files)} 篇）")
        
        return article_pairs
    
    def parse_date_from_text(self, text: str) -> Optional[Dict]:
        """从文本中解析日期"""
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                for fmt in DATE_FORMATS:
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
    
    def extract_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """提取frontmatter元数据"""
        frontmatter = {}
        body = content
        
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    fm_text = parts[1].strip()
                    body = parts[2].strip()
                    
                    for line in fm_text.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"')
                            frontmatter[key] = value
            except Exception as e:
                print(f"解析frontmatter失败: {e}")
        
        return frontmatter, body
    
    def clean_markdown_text(self, text: str) -> str:
        """清理Markdown文本"""
        if not text:
            return ""
        
        # 移除HTML标签（如果启用）
        if MARKDOWN_PROCESSING['clean_html']:
            text = re.sub(r'<[^>]+>', '', text)
        
        # 处理特殊标记
        text = re.sub(r'\[翻译失败 - 原文\]', '', text)
        
        # 清理多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def split_into_paragraphs(self, content: str) -> List[str]:
        """将内容分割成段落"""
        # 移除标题行
        content = re.sub(r'^#\s+.+\n+', '', content, count=1)
        
        # 按双换行符分割段落
        paragraphs = content.split('\n\n')
        
        # 清理和过滤段落
        cleaned_paragraphs = []
        for para in paragraphs:
            para = self.clean_markdown_text(para)
            if para and len(para.strip()) > 10:  # 忽略过短的段落
                
                # 如果段落过长，尝试分割
                if (MARKDOWN_PROCESSING['split_long_paragraphs'] and 
                    len(para) > MARKDOWN_PROCESSING['max_paragraph_length']):
                    
                    # 按句号分割长段落
                    sentences = re.split(r'\.(?=\s+[A-Z])', para)
                    current_para = ""
                    
                    for sentence in sentences:
                        if len(current_para) + len(sentence) < MARKDOWN_PROCESSING['max_paragraph_length']:
                            current_para += sentence + "."
                        else:
                            if current_para:
                                cleaned_paragraphs.append(current_para.strip())
                            current_para = sentence + "."
                    
                    if current_para:
                        cleaned_paragraphs.append(current_para.strip())
                else:
                    cleaned_paragraphs.append(para)
        
        return cleaned_paragraphs
    
    def align_paragraphs(self, english_paras: List[str], chinese_paras: List[str]) -> List[Tuple[str, str]]:
        """对齐英文和中文段落"""
        aligned = []
        en_len = len(english_paras)
        cn_len = len(chinese_paras)
        
        if en_len == cn_len:
            # 数量相等，直接配对
            for en, cn in zip(english_paras, chinese_paras):
                aligned.append((en, cn))
        elif en_len > cn_len:
            # 英文段落更多，中文段落可能被合并了
            ratio = en_len / cn_len
            for i, cn in enumerate(chinese_paras):
                start_idx = int(i * ratio)
                end_idx = min(int((i + 1) * ratio), en_len)
                combined_en = '\n\n'.join(english_paras[start_idx:end_idx])
                aligned.append((combined_en, cn))
        else:
            # 中文段落更多，英文段落可能被合并了
            ratio = cn_len / en_len
            for i, en in enumerate(english_paras):
                start_idx = int(i * ratio)
                end_idx = min(int((i + 1) * ratio), cn_len)
                combined_cn = '\n\n'.join(chinese_paras[start_idx:end_idx])
                aligned.append((en, combined_cn))
        
        self.stats['total_paragraphs'] += max(en_len, cn_len)
        self.stats['aligned_paragraphs'] += len(aligned)
        
        return aligned
    
    def process_article_pair(self, pair_info: Dict) -> Optional[Dict]:
        """处理一对英中文章"""
        try:
            # 读取英文文章
            with open(pair_info['english_file'], 'r', encoding='utf-8') as f:
                english_content = f.read()
            
            # 读取中文文章
            with open(pair_info['chinese_file'], 'r', encoding='utf-8') as f:
                chinese_content = f.read()
            
            # 提取元数据
            en_frontmatter, en_body = self.extract_frontmatter(english_content)
            cn_frontmatter, cn_body = self.extract_frontmatter(chinese_content)
            
            # 提取标题
            en_title_match = re.match(r'^#\s+(.+)$', en_body, re.MULTILINE)
            cn_title_match = re.match(r'^#\s+(.+)$', cn_body, re.MULTILINE)
            
            english_title = en_title_match.group(1) if en_title_match else pair_info['filename'].replace('.md', '')
            chinese_title = cn_title_match.group(1) if cn_title_match else cn_frontmatter.get('title', english_title)
            
            # 提取发布日期
            date_info = None
            if pair_info['metadata'] and 'date' in pair_info['metadata']:
                if isinstance(pair_info['metadata']['date'], dict):
                    date_info = pair_info['metadata']['date']
                else:
                    date_info = self.parse_date_from_text(str(pair_info['metadata']['date']))
            
            if not date_info:
                # 从文章内容中提取日期
                date_info = self.parse_date_from_text(en_body)
            
            # 提取URL
            url = ""
            if pair_info['metadata'] and 'url' in pair_info['metadata']:
                url = pair_info['metadata']['url']
            
            # 分割段落
            english_paragraphs = self.split_into_paragraphs(en_body)
            chinese_paragraphs = self.split_into_paragraphs(cn_body)
            
            # 对齐段落
            aligned_paragraphs = self.align_paragraphs(english_paragraphs, chinese_paragraphs)
            
            processed_article = {
                'filename': pair_info['filename'],
                'english_title': english_title,
                'chinese_title': chinese_title,
                'date': date_info,
                'url': url,
                'aligned_paragraphs': aligned_paragraphs,
                'frontmatter': {
                    'english': en_frontmatter,
                    'chinese': cn_frontmatter
                }
            }
            
            return processed_article
            
        except Exception as e:
            print(f"处理文章 {pair_info['filename']} 时出错: {e}")
            self.stats['failed_processing'] += 1
            return None
    
    def convert_markdown_to_html(self, text: str) -> str:
        """将Markdown文本转换为HTML"""
        # 处理基本的Markdown语法
        # 粗体
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        # 斜体
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        # 链接
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        # 代码
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # 处理段落
        paragraphs = text.split('\n\n')
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                if para.startswith('#'):
                    # 标题
                    level = len(para) - len(para.lstrip('#'))
                    para = f'<h{min(level, 6)}>{para.lstrip("#").strip()}</h{min(level, 6)}>'
                else:
                    # 普通段落
                    para = f'<p>{para}</p>'
                html_paragraphs.append(para)
        
        return '\n'.join(html_paragraphs)
    
    def create_article_html(self, article: Dict) -> str:
        """创建文章的HTML内容"""
        html_parts = []
        
        # 文章头部信息
        html_parts.append('<div class="article-header">')
        html_parts.append(f'<div class="article-title">')
        html_parts.append(f'  <div>{article["english_title"]}</div>')
        html_parts.append(f'  <div>{article["chinese_title"]}</div>')
        html_parts.append(f'</div>')
        
        if article.get('date'):
            html_parts.append(f'<div class="article-date">{article["date"]["original"]}</div>')
        
        if article.get('url'):
            html_parts.append(f'<div class="article-url"><a href="{article["url"]}">{article["url"]}</a></div>')
        
        html_parts.append('</div>')
        
        # 双语对照内容
        for en_para, cn_para in article['aligned_paragraphs']:
            html_parts.append('<div class="bilingual-section">')
            
            # 英文段落
            html_parts.append('<div class="english-paragraph">')
            en_html = self.convert_markdown_to_html(en_para)
            html_parts.append(en_html)
            html_parts.append('</div>')
            
            # 中文段落
            is_failed = '[翻译失败 - 原文]' in cn_para
            css_class = 'chinese-paragraph failed-translation' if is_failed else 'chinese-paragraph'
            
            html_parts.append(f'<div class="{css_class}">')
            cn_html = self.convert_markdown_to_html(cn_para)
            html_parts.append(cn_html)
            html_parts.append('</div>')
            
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def create_epub(self, articles: List[Dict], output_path: Path) -> bool:
        """创建EPUB电子书"""
        try:
            book = epub.EpubBook()
            book.set_identifier(str(uuid.uuid4()))
            book.set_title("Paul Graham Essays - Bilingual Collection")
            book.set_language('en')
            book.add_author(self.config.AUTHOR)
            
            # 添加元数据
            book.add_metadata('DC', 'description', 
                f'Bilingual collection of {len(articles)} essays by Paul Graham (English & Chinese)')
            book.add_metadata('DC', 'date', datetime.now().strftime('%Y-%m-%d'))
            book.add_metadata('DC', 'subject', 'Technology, Startups, Programming')
            
            # 创建CSS样式
            nav_css = epub.EpubItem(
                uid="style_nav",
                file_name="style.css",
                media_type="text/css",
                content=CSS_STYLES['epub']
            )
            book.add_item(nav_css)
            
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
            <head>
                <link rel="stylesheet" type="text/css" href="style.css"/>
            </head>
            <body>
                <div class="article-header">
                    <h1>Paul Graham Essays</h1>
                    <h2>Bilingual Collection<br/>双语合集</h2>
                    <p>A collection of {len(articles)} essays in English and Chinese</p>
                    <p>包含 {len(articles)} 篇中英对照文章</p>
                    <p>Date range: {date_range}</p>
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <hr/>
                    <p><small>This ebook was created for personal reading.<br/>
                    All content © Paul Graham. Chinese translations by AI.</small></p>
                </div>
            </body>
            </html>
            '''
            book.add_item(cover_html)
            
            # 按日期排序文章（最新的在前）
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
            
            toc_content = f'''
            <html>
            <head>
                <link rel="stylesheet" type="text/css" href="style.css"/>
            </head>
            <body>
                <div class="toc">
                    <h2>Table of Contents / 目录</h2>
                    <ol>
            '''
            
            for i, article in enumerate(sorted_articles):
                toc_content += f'''
                    <li>
                        <a href="essay_{i+1}.xhtml">
                            {article["english_title"]}<br/>
                            <small>{article["chinese_title"]}</small>
                        </a>
                '''
                if article.get('date'):
                    toc_content += f'<span class="date">({article["date"]["original"]})</span>'
                toc_content += '</li>'
            
            toc_content += '''
                    </ol>
                </div>
            </body>
            </html>
            '''
            
            toc_html.content = toc_content
            book.add_item(toc_html)
            
            # 创建文章章节
            chapters = [cover_html, toc_html]
            
            for i, article in enumerate(sorted_articles):
                chapter = epub.EpubHtml(
                    title=f"{article['english_title']} / {article['chinese_title']}",
                    file_name=f'essay_{i+1}.xhtml',
                    lang='en'
                )
                
                article_html = self.create_article_html(article)
                
                chapter.content = f'''
                <html>
                <head>
                    <link rel="stylesheet" type="text/css" href="style.css"/>
                    <title>{article["english_title"]}</title>
                </head>
                <body>
                    <div class="page-break"></div>
                    {article_html}
                </body>
                </html>
                '''
                
                # 添加样式引用
                chapter.add_item(nav_css)
                book.add_item(chapter)
                chapters.append(chapter)
            
            # 设置目录和书脊
            book.toc = chapters[2:]  # 不包括封面和目录页
            book.spine = chapters
            
            # 添加导航
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # 写入EPUB文件
            epub.write_epub(str(output_path), book)
            print(f"✓ EPUB已创建: {output_path}")
            print(f"  文件大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"创建EPUB失败: {e}")
            return False
    
    def create_pdf(self, articles: List[Dict], output_path: Path) -> bool:
        """创建PDF电子书"""
        if not PDF_AVAILABLE:
            print("❌ PDF功能不可用：weasyprint未正确安装")
            return False
        
        try:
            # 按日期排序文章（最新的在前）
            sorted_articles = sorted(
                articles,
                key=lambda x: x['date']['parsed'] if x.get('date') else datetime(1900, 1, 1),
                reverse=True
            )
            
            # 创建HTML内容
            html_parts = []
            
            # HTML头部
            html_parts.append(f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Paul Graham Essays - Bilingual Collection</title>
                <style>
                {CSS_STYLES['pdf']}
                </style>
            </head>
            <body>
            ''')
            
            # 封面页
            dated_articles = [a for a in articles if a.get('date')]
            if dated_articles:
                dates = [a['date']['parsed'] for a in dated_articles]
                min_date = min(dates).strftime('%B %Y')
                max_date = max(dates).strftime('%B %Y')
                date_range = f"{min_date} - {max_date}"
            else:
                date_range = "Various dates"
            
            html_parts.append(f'''
            <div class="article-header">
                <h1>Paul Graham Essays</h1>
                <h2>Bilingual Collection / 双语合集</h2>
                <p>A collection of {len(articles)} essays in English and Chinese</p>
                <p>包含 {len(articles)} 篇中英对照文章</p>
                <p>Date range: {date_range}</p>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr/>
                <p><small>This book was created for personal reading.<br/>
                All content © Paul Graham. Chinese translations by AI.</small></p>
            </div>
            ''')
            
            # 目录页
            html_parts.append('''
            <div class="page-break"></div>
            <div class="toc">
                <h2>Table of Contents / 目录</h2>
                <ol>
            ''')
            
            for i, article in enumerate(sorted_articles):
                html_parts.append(f'''
                <li>
                    {article["english_title"]}<br/>
                    <small>{article["chinese_title"]}</small>
                ''')
                if article.get('date'):
                    html_parts.append(f'<span class="date">({article["date"]["original"]})</span>')
                html_parts.append('</li>')
            
            html_parts.append('''
                </ol>
            </div>
            ''')
            
            # 文章内容
            for article in sorted_articles:
                html_parts.append('<div class="page-break"></div>')
                article_html = self.create_article_html(article)
                html_parts.append(article_html)
            
            # HTML结尾
            html_parts.append('''
            </body>
            </html>
            ''')
            
            # 合并HTML
            full_html = '\n'.join(html_parts)
            
            # 生成PDF
            print(f"正在生成PDF: {output_path}")
            weasyprint.HTML(string=full_html, base_url=str(self.output_dir)).write_pdf(str(output_path))
            
            print(f"✓ PDF已创建: {output_path}")
            print(f"  文件大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"创建PDF失败: {e}")
            return False
    
    def create_html(self, articles: List[Dict], output_path: Path) -> bool:
        """创建HTML版本"""
        try:
            # 按日期排序文章（最新的在前）
            sorted_articles = sorted(
                articles,
                key=lambda x: x['date']['parsed'] if x.get('date') else datetime(1900, 1, 1),
                reverse=True
            )
            
            # 创建HTML内容
            html_parts = []
            
            # HTML头部
            html_parts.append(f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Paul Graham Essays - Bilingual Collection</title>
                <style>
                {CSS_STYLES['html']}
                </style>
            </head>
            <body>
            ''')
            
            # 封面
            dated_articles = [a for a in articles if a.get('date')]
            if dated_articles:
                dates = [a['date']['parsed'] for a in dated_articles]
                min_date = min(dates).strftime('%B %Y')
                max_date = max(dates).strftime('%B %Y')
                date_range = f"{min_date} - {max_date}"
            else:
                date_range = "Various dates"
            
            html_parts.append(f'''
            <div class="article-header">
                <h1>Paul Graham Essays</h1>
                <h2>Bilingual Collection / 双语合集</h2>
                <p>A collection of {len(articles)} essays in English and Chinese</p>
                <p>包含 {len(articles)} 篇中英对照文章</p>
                <p>Date range: {date_range}</p>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr/>
                <p><small>This webpage was created for personal reading.<br/>
                All content © Paul Graham. Chinese translations by AI.</small></p>
            </div>
            ''')
            
            # 目录
            html_parts.append('''
            <div class="toc">
                <h2>Table of Contents / 目录</h2>
                <ol>
            ''')
            
            for i, article in enumerate(sorted_articles):
                article_id = f"article_{i+1}"
                html_parts.append(f'''
                <li>
                    <a href="#{article_id}">
                        {article["english_title"]}<br/>
                        <small>{article["chinese_title"]}</small>
                    </a>
                ''')
                if article.get('date'):
                    html_parts.append(f'<span class="date">({article["date"]["original"]})</span>')
                html_parts.append('</li>')
            
            html_parts.append('''
                </ol>
            </div>
            ''')
            
            # 文章内容
            for i, article in enumerate(sorted_articles):
                article_id = f"article_{i+1}"
                html_parts.append(f'<div id="{article_id}">')
                article_html = self.create_article_html(article)
                html_parts.append(article_html)
                html_parts.append('</div>')
                html_parts.append('<hr/>')
            
            # HTML结尾
            html_parts.append('''
            </body>
            </html>
            ''')
            
            # 保存HTML文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html_parts))
            
            print(f"✓ HTML已创建: {output_path}")
            print(f"  文件大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"创建HTML失败: {e}")
            return False
    
    def print_stats(self):
        """打印统计信息"""
        print(f"\n📊 生成统计:")
        print(f"  总文章数: {self.stats['total_articles']}")
        print(f"  双语文章: {self.stats['bilingual_articles']}")
        print(f"  仅英文: {self.stats['english_only']}")
        print(f"  仅中文: {self.stats['chinese_only']}")
        print(f"  处理失败: {self.stats['failed_processing']}")
        print(f"  总段落数: {self.stats['total_paragraphs']}")
        print(f"  对齐段落: {self.stats['aligned_paragraphs']}")
        if self.stats['total_paragraphs'] > 0:
            alignment_rate = self.stats['aligned_paragraphs'] / self.stats['total_paragraphs'] * 100
            print(f"  对齐成功率: {alignment_rate:.1f}%")
    
    def generate_ebooks(self, formats: List[str] = None) -> Dict[str, bool]:
        """生成电子书"""
        if formats is None:
            formats = ['epub', 'pdf', 'html']
        
        print("🔍 正在扫描文章...")
        article_pairs = self.find_article_pairs()
        
        if not article_pairs:
            print("❌ 没有找到任何双语文章！")
            return {}
        
        print(f"\n📝 正在处理 {len(article_pairs)} 篇文章...")
        processed_articles = []
        
        for i, pair in enumerate(article_pairs):
            print(f"  处理进度: {i+1}/{len(article_pairs)} - {pair['filename']}")
            article = self.process_article_pair(pair)
            if article:
                processed_articles.append(article)
        
        if not processed_articles:
            print("❌ 没有成功处理任何文章！")
            return {}
        
        print(f"\n✅ 成功处理 {len(processed_articles)} 篇文章")
        
        # 获取输出文件路径
        output_files = self.config.get_output_files()
        results = {}
        
        # 生成各种格式
        print(f"\n📚 正在生成电子书...")
        
        if 'epub' in formats:
            print("\n📖 生成EPUB...")
            results['epub'] = self.create_epub(processed_articles, output_files['epub'])
        
        if 'pdf' in formats:
            print("\n📄 生成PDF...")
            results['pdf'] = self.create_pdf(processed_articles, output_files['pdf'])
        
        if 'html' in formats:
            print("\n🌐 生成HTML...")
            results['html'] = self.create_html(processed_articles, output_files['html'])
        
        # 打印统计信息
        self.print_stats()
        
        return results


def main():
    """主函数"""
    print("🚀 Paul Graham Essays - 双语电子书生成器")
    print("=" * 50)
    
    generator = BilingualEbookGenerator()
    
    # 让用户选择格式
    print("\n选择要生成的格式:")
    print("1. 仅EPUB")
    if PDF_AVAILABLE:
        print("2. 仅PDF")
    else:
        print("2. 仅PDF (不可用)")
    print("3. 仅HTML")
    if PDF_AVAILABLE:
        print("4. EPUB + PDF")
        print("5. 全部格式 (EPUB + PDF + HTML)")
    else:
        print("4. EPUB + HTML")
    
    choice = input(f"\n请选择 (1-{'5' if PDF_AVAILABLE else '4'}): ").strip()
    
    if PDF_AVAILABLE:
        format_map = {
            '1': ['epub'],
            '2': ['pdf'],
            '3': ['html'],
            '4': ['epub', 'pdf'],
            '5': ['epub', 'pdf', 'html']
        }
    else:
        format_map = {
            '1': ['epub'],
            '2': ['html'],  # 如果PDF不可用，选项2变成HTML
            '3': ['html'],
            '4': ['epub', 'html']
        }
    
    formats = format_map.get(choice, ['epub', 'pdf', 'html'])
    
    print(f"\n将生成格式: {', '.join(formats).upper()}")
    
    # 生成电子书
    results = generator.generate_ebooks(formats)
    
    # 显示结果
    print(f"\n{'=' * 50}")
    print("📚 生成完成！")
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"成功生成: {success_count}/{total_count} 种格式")
    
    for format_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {format_name.upper()}")
    
    if success_count > 0:
        print(f"\n文件保存在: {generator.output_dir}")


if __name__ == "__main__":
    main()