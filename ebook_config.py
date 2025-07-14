#!/usr/bin/env python3
"""
电子书生成器配置文件
"""

import re
from datetime import datetime
from pathlib import Path

class EbookConfig:
    """电子书生成配置"""
    
    # 基础信息
    AUTHOR = "Paul Graham"
    LANGUAGE_EN = "en"
    LANGUAGE_CN = "zh-CN"
    
    # 目录设置
    ENGLISH_DIR = "pg_essays"
    CHINESE_DIR = "pg_essays_cn"
    OUTPUT_DIR = "output"
    
    # 文件名模板
    EPUB_FILENAME = "paul_graham_essays_bilingual_{timestamp}.epub"
    PDF_FILENAME = "paul_graham_essays_bilingual_{timestamp}.pdf"
    HTML_FILENAME = "paul_graham_essays_bilingual_{timestamp}.html"
    
    # 元数据
    METADATA_FILE = "pg_essays_metadata.json"
    
    @classmethod
    def get_timestamp(cls):
        """获取时间戳"""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    @classmethod
    def get_output_files(cls):
        """获取输出文件路径"""
        timestamp = cls.get_timestamp()
        output_dir = Path(cls.OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)
        
        return {
            'epub': output_dir / cls.EPUB_FILENAME.format(timestamp=timestamp),
            'pdf': output_dir / cls.PDF_FILENAME.format(timestamp=timestamp),
            'html': output_dir / cls.HTML_FILENAME.format(timestamp=timestamp)
        }

# CSS样式定义
CSS_STYLES = {
    'epub': """
/* EPUB样式 - 适用于电子阅读器 */
body {
    font-family: Georgia, "Times New Roman", "Songti SC", "SimSun", serif;
    margin: 1em 2em;
    line-height: 1.6;
    color: #333;
}

h1 {
    font-size: 1.8em;
    margin: 1.5em 0 1em 0;
    color: #1a1a1a;
    text-align: center;
    border-bottom: 2px solid #ddd;
    padding-bottom: 0.5em;
}

h2 {
    font-size: 1.4em;
    margin: 1.2em 0 0.8em 0;
    color: #2c2c2c;
}

h3 {
    font-size: 1.2em;
    margin: 1em 0 0.6em 0;
    color: #404040;
}

/* 文章头部信息 */
.article-header {
    text-align: center;
    margin: 2em 0;
    padding: 1em;
    background-color: #f9f9f9;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
}

.article-title {
    font-size: 1.5em;
    font-weight: bold;
    margin-bottom: 0.5em;
    color: #1a1a1a;
}

.article-date {
    font-style: italic;
    color: #666;
    margin: 0.3em 0;
}

.article-url {
    font-size: 0.9em;
    color: #0066cc;
    word-break: break-all;
    margin-top: 0.5em;
}

/* 双语对照容器 */
.bilingual-section {
    margin: 1.5em 0;
}

.english-paragraph {
    margin-bottom: 1em;
    padding: 0.8em;
    background-color: #f8f9fa;
    border-radius: 6px;
}

.english-paragraph p {
    margin: 0;
    color: #2c3e50;
    font-style: italic;
}

.chinese-paragraph {
    margin-bottom: 1.5em;
    padding: 0.8em;
    background-color: #fff8f0;
    border-radius: 6px;
}

.chinese-paragraph p {
    margin: 0;
    color: #1a1a1a;
    font-weight: 500;
}

/* 特殊段落标记 */
.failed-translation {
    background-color: #fff2f2;
    border-left-color: #dc3545;
    font-style: italic;
    color: #721c24;
}

.failed-translation::before {
    content: "⚠️ 翻译失败：";
    font-weight: bold;
    display: block;
    margin-bottom: 0.5em;
}

/* 链接样式 */
a {
    color: #0066cc;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* 强调样式 */
strong {
    font-weight: bold;
    color: #1a1a1a;
}

em {
    font-style: italic;
    color: #555;
}

/* 代码样式 */
code {
    font-family: "Monaco", "Consolas", "Courier New", monospace;
    background-color: #f4f4f4;
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 0.9em;
}

/* 分隔线 */
hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}

/* 目录样式 */
.toc {
    margin: 2em 0;
}

.toc h2 {
    color: #1a1a1a;
    border-bottom: 2px solid #ddd;
    padding-bottom: 0.5em;
}

.toc ol {
    list-style-type: decimal;
    padding-left: 2em;
}

.toc li {
    margin: 0.8em 0;
    line-height: 1.4;
}

.toc a {
    text-decoration: none;
    color: #333;
}

.toc a:hover {
    color: #0066cc;
    text-decoration: underline;
}

.toc .date {
    font-style: italic;
    color: #666;
    font-size: 0.9em;
    margin-left: 0.5em;
}

/* 页面分隔 */
.page-break {
    page-break-before: always;
}
""",

    'pdf': """
/* PDF样式 - 适用于打印和PDF生成 */
@page {
    size: A4;
    margin: 2cm 2.5cm;
}

body {
    font-family: Georgia, "Times New Roman", "Songti SC", "SimSun", serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
    max-width: none;
}

h1 {
    font-size: 18pt;
    margin: 2em 0 1em 0;
    color: #1a1a1a;
    text-align: center;
    border-bottom: 2pt solid #333;
    padding-bottom: 0.5em;
    page-break-after: avoid;
}

h2 {
    font-size: 14pt;
    margin: 1.5em 0 0.8em 0;
    color: #2c2c2c;
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    margin: 1.2em 0 0.6em 0;
    color: #404040;
    page-break-after: avoid;
}

/* 文章头部信息 */
.article-header {
    text-align: center;
    margin: 2em 0;
    padding: 1em;
    border: 2pt solid #ccc;
    background-color: #f9f9f9;
    page-break-inside: avoid;
}

.article-title {
    font-size: 14pt;
    font-weight: bold;
    margin-bottom: 0.5em;
    color: #1a1a1a;
}

.article-date {
    font-style: italic;
    color: #666;
    margin: 0.3em 0;
    font-size: 10pt;
}

.article-url {
    font-size: 9pt;
    color: #333;
    word-break: break-all;
    margin-top: 0.5em;
}

/* 双语对照容器 */
.bilingual-section {
    margin: 1em 0;
    page-break-inside: avoid;
}

.english-paragraph {
    margin-bottom: 0.5em;
    padding: 0.5em 0.8em;
    background-color: #f8f9fa;
    border: 1pt solid #e0e0e0;
}

.english-paragraph p {
    margin: 0;
    color: #2c3e50;
    font-style: italic;
    font-size: 10pt;
}

.chinese-paragraph {
    margin-bottom: 1em;
    padding: 0.5em 0.8em;
    background-color: #fff8f0;
    border: 1pt solid #e0e0e0;
}

.chinese-paragraph p {
    margin: 0;
    color: #1a1a1a;
    font-weight: 500;
    font-size: 11pt;
}

/* 特殊段落标记 */
.failed-translation {
    background-color: #fff2f2;
    border-left-color: #dc3545;
    font-style: italic;
    color: #721c24;
}

.failed-translation::before {
    content: "⚠️ 翻译失败：";
    font-weight: bold;
    display: block;
    margin-bottom: 0.3em;
    font-size: 9pt;
}

/* 链接样式 */
a {
    color: #333;
    text-decoration: none;
}

/* 强调样式 */
strong {
    font-weight: bold;
    color: #1a1a1a;
}

em {
    font-style: italic;
    color: #555;
}

/* 代码样式 */
code {
    font-family: "Monaco", "Consolas", "Courier New", monospace;
    background-color: #f4f4f4;
    padding: 0.1em 0.3em;
    border: 1pt solid #ddd;
    font-size: 9pt;
}

/* 分隔线 */
hr {
    border: none;
    border-top: 1pt solid #999;
    margin: 1.5em 0;
}

/* 目录样式 */
.toc {
    margin: 2em 0;
    page-break-after: always;
}

.toc h2 {
    color: #1a1a1a;
    border-bottom: 2pt solid #333;
    padding-bottom: 0.5em;
    page-break-after: avoid;
}

.toc ol {
    list-style-type: decimal;
    padding-left: 1.5em;
}

.toc li {
    margin: 0.5em 0;
    line-height: 1.3;
    page-break-inside: avoid;
}

.toc a {
    text-decoration: none;
    color: #333;
}

.toc .date {
    font-style: italic;
    color: #666;
    font-size: 9pt;
    margin-left: 0.5em;
}

/* 页面分隔 */
.page-break {
    page-break-before: always;
}

/* 避免孤立行 */
p {
    orphans: 2;
    widows: 2;
}
""",

    'html': """
/* HTML样式 - 适用于网页浏览 */
body {
    font-family: Georgia, "Times New Roman", "Songti SC", "SimSun", serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 2em;
    line-height: 1.6;
    color: #333;
    background-color: #fafafa;
}

h1 {
    font-size: 2.2em;
    margin: 2em 0 1em 0;
    color: #1a1a1a;
    text-align: center;
    border-bottom: 3px solid #ddd;
    padding-bottom: 0.5em;
}

h2 {
    font-size: 1.6em;
    margin: 1.5em 0 0.8em 0;
    color: #2c2c2c;
}

h3 {
    font-size: 1.3em;
    margin: 1.2em 0 0.6em 0;
    color: #404040;
}

/* 文章头部信息 */
.article-header {
    text-align: center;
    margin: 3em 0;
    padding: 2em;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.article-title {
    font-size: 1.8em;
    font-weight: bold;
    margin-bottom: 0.5em;
    color: #1a1a1a;
}

.article-date {
    font-style: italic;
    color: #666;
    margin: 0.5em 0;
    font-size: 1.1em;
}

.article-url {
    font-size: 1em;
    color: #0066cc;
    word-break: break-all;
    margin-top: 1em;
}

.article-url a {
    color: #0066cc;
    text-decoration: none;
}

.article-url a:hover {
    text-decoration: underline;
}

/* 双语对照容器 */
.bilingual-section {
    margin: 2em 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.english-paragraph {
    margin: 0;
    padding: 1.5em;
    background-color: #f8f9fa;
    border-left: 5px solid #007bff;
}

.english-paragraph p {
    margin: 0;
    color: #2c3e50;
    font-style: italic;
    font-size: 1.05em;
}

.chinese-paragraph {
    margin: 0;
    padding: 1.5em;
    background-color: #fff8f0;
    border-left: 5px solid #ff6b35;
}

.chinese-paragraph p {
    margin: 0;
    color: #1a1a1a;
    font-weight: 500;
    font-size: 1.1em;
}

/* 特殊段落标记 */
.failed-translation {
    background-color: #fff2f2;
    border-left-color: #dc3545;
    font-style: italic;
    color: #721c24;
}

.failed-translation::before {
    content: "⚠️ 翻译失败：";
    font-weight: bold;
    display: block;
    margin-bottom: 0.5em;
    color: #dc3545;
}

/* 链接样式 */
a {
    color: #0066cc;
    text-decoration: none;
    transition: color 0.3s ease;
}

a:hover {
    color: #0056b3;
    text-decoration: underline;
}

/* 强调样式 */
strong {
    font-weight: bold;
    color: #1a1a1a;
}

em {
    font-style: italic;
    color: #555;
}

/* 代码样式 */
code {
    font-family: "Monaco", "Consolas", "Courier New", monospace;
    background-color: #f4f4f4;
    padding: 0.3em 0.5em;
    border-radius: 4px;
    font-size: 0.9em;
    border: 1px solid #e0e0e0;
}

/* 分隔线 */
hr {
    border: none;
    border-top: 2px solid #ddd;
    margin: 3em 0;
}

/* 目录样式 */
.toc {
    margin: 3em 0;
    background-color: white;
    padding: 2em;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.toc h2 {
    color: #1a1a1a;
    border-bottom: 3px solid #ddd;
    padding-bottom: 0.5em;
    margin-bottom: 1.5em;
}

.toc ol {
    list-style-type: decimal;
    padding-left: 2em;
}

.toc li {
    margin: 1em 0;
    line-height: 1.4;
}

.toc a {
    text-decoration: none;
    color: #333;
    font-size: 1.1em;
}

.toc a:hover {
    color: #0066cc;
    text-decoration: underline;
}

.toc .date {
    font-style: italic;
    color: #666;
    font-size: 0.95em;
    margin-left: 0.5em;
}

/* 响应式设计 */
@media (max-width: 768px) {
    body {
        padding: 1em;
    }
    
    .article-header {
        padding: 1.5em;
    }
    
    .english-paragraph,
    .chinese-paragraph {
        padding: 1em;
    }
    
    .toc {
        padding: 1.5em;
    }
}

/* 打印样式 */
@media print {
    body {
        background-color: white;
        max-width: none;
        padding: 0;
    }
    
    .article-header {
        background: white;
        box-shadow: none;
        border: 2px solid #ccc;
    }
    
    .bilingual-section {
        box-shadow: none;
        border: 1px solid #ccc;
        margin: 1em 0;
    }
    
    .toc {
        background-color: white;
        box-shadow: none;
        border: 2px solid #ccc;
    }
}
"""
}

# 日期解析配置
DATE_PATTERNS = [
    r'([A-Z][a-z]+ \d{4})',  # "July 2023"
    r'(\d{1,2} [A-Z][a-z]+ \d{4})',  # "1 July 2023"
    r'([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',  # "July 1, 2023"
    r'(\d{4}-\d{2}-\d{2})',  # "2023-07-01"
]

DATE_FORMATS = ['%B %Y', '%d %B %Y', '%B %d, %Y', '%Y-%m-%d']

# Markdown处理配置
MARKDOWN_PROCESSING = {
    'max_paragraph_length': 2000,  # 最大段落长度
    'split_long_paragraphs': True,  # 是否分割长段落
    'preserve_code_blocks': True,   # 是否保留代码块
    'clean_html': True,            # 是否清理HTML标签
}