#!/usr/bin/env python3
"""
导入已有文章并重新生成EPUB
"""

import json
import os
from pathlib import Path
from pg_enhanced_scraper import EnhancedPaulGrahamScraper

def import_existing_articles():
    """导入已有的文章到缓存系统"""
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
                    articles.extend(data['scraped_articles'])
                elif 'articles' in data:
                    articles.extend(data['articles'])
                break
    
    if not articles:
        print("没有找到已有的文章数据")
        return
    
    print(f"找到 {len(articles)} 篇已抓取的文章")
    
    # 创建爬虫实例
    scraper = EnhancedPaulGrahamScraper()
    
    # 导入文章到缓存
    imported_count = 0
    for article in articles:
        if 'url' in article and 'title' in article:
            # 保存到缓存
            scraper.save_to_cache(article['url'], article)
            imported_count += 1
    
    print(f"成功导入 {imported_count} 篇文章到缓存系统")
    
    # 重新生成EPUB
    print("\n正在生成增强版EPUB...")
    scraper.create_enhanced_epub(articles)
    
    print("\n完成！")

if __name__ == "__main__":
    import_existing_articles()