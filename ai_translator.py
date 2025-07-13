#!/usr/bin/env python3
"""
使用SiliconFlow的DeepSeek-V3模型翻译Paul Graham文章
"""

import concurrent.futures
import hashlib
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DeepSeekTranslator:
    def __init__(self, api_key, cache_dir="translation_cache", max_concurrent=8):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model = "deepseek-ai/DeepSeek-V3"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 缓存设置
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 并发控制 - 针对你的API限制优化 (RPM:1000, TPM:10000)
        self.max_concurrent = min(max_concurrent, 8)  # 保守的并发数
        self.request_interval = 0.1  # 请求间隔（秒）
        self.last_request_time = 0
        self.request_lock = Lock()
        
        # 统计
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'failed_requests': 0
        }
        self.stats_lock = Lock()
    
    def get_cache_key(self, text):
        """生成缓存键"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def get_cached_translation(self, text):
        """获取缓存的翻译"""
        cache_key = self.get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    with self.stats_lock:
                        self.stats['cache_hits'] += 1
                    return data['translation']
            except (json.JSONDecodeError, KeyError):
                pass
        return None
    
    def save_translation_cache(self, text, translation):
        """保存翻译到缓存"""
        cache_key = self.get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        cache_data = {
            'original': text[:200] + "..." if len(text) > 200 else text,
            'translation': translation,
            'timestamp': datetime.now().isoformat(),
            'model': self.model
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def translate_text(self, text, context=""):
        """翻译文本（带缓存）"""
        with self.stats_lock:
            self.stats['total_requests'] += 1
        
        # 检查缓存
        cached = self.get_cached_translation(text)
        if cached:
            return cached
        
        prompt = f"""请将以下英文文章翻译成中文，直接输出翻译结果，不要添加任何说明或注释。

{context}

原文：
{text}

中文翻译："""

        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }

        try:
            with self.stats_lock:
                self.stats['api_calls'] += 1
            
            response = requests.post(self.base_url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()

            if 'choices' in result and len(result['choices']) > 0:
                translation = result['choices'][0]['message']['content'].strip()
                # 保存到缓存
                self.save_translation_cache(text, translation)
                return translation
            else:
                print(f"API响应格式错误: {result}")
                with self.stats_lock:
                    self.stats['failed_requests'] += 1
                return None

        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            with self.stats_lock:
                self.stats['failed_requests'] += 1
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            with self.stats_lock:
                self.stats['failed_requests'] += 1
            return None

    def split_article(self, content, max_chunk_size=3000):
        """将文章分割成较小的块进行翻译"""
        # 按段落分割
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            # 如果当前块加上新段落不会超过限制
            if len(current_chunk) + len(paragraph) + 2 < max_chunk_size:
                if current_chunk:
                    current_chunk += '\n\n' + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 保存当前块，开始新块
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph

        # 添加最后一块
        if current_chunk:
            chunks.append(current_chunk)

        return chunks
    
    def print_stats(self):
        """打印统计信息"""
        print(f"\n📊 翻译统计:")
        print(f"  总请求数: {self.stats['total_requests']}")
        print(f"  缓存命中: {self.stats['cache_hits']}")
        print(f"  API调用: {self.stats['api_calls']}")
        print(f"  失败请求: {self.stats['failed_requests']}")
        if self.stats['total_requests'] > 0:
            print(f"  缓存命中率: {self.stats['cache_hits']/self.stats['total_requests']*100:.1f}%")

    def translate_article(self, article_path):
        """翻译整篇文章"""
        print(f"正在翻译: {article_path}")

        # 读取文章
        with open(article_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取标题
        title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1)
        else:
            title = Path(article_path).stem

        print(f"  原标题: {title}")
        
        # 检查是否已经翻译过（断点续传）- 使用原文件名
        output_dir = Path("pg_essays_cn")
        original_filename = Path(article_path).name
        output_file = output_dir / original_filename
        if output_file.exists():
            print(f"  ⏭️  跳过（已存在翻译）: {original_filename}")
            return None

        # 翻译标题
        print("  正在翻译标题...")
        chinese_title = self.translate_text(title)
        if not chinese_title:
            print("  标题翻译失败")
            return None

        print(f"  中文标题: {chinese_title}")

        # 移除原标题行，准备翻译正文
        content_without_title = re.sub(r'^#\s+.+\n+', '', content, count=1)

        # 分割文章
        chunks = self.split_article(content_without_title)
        print(f"  文章分为 {len(chunks)} 个部分")

        # 翻译每个部分
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            print(f"    翻译第 {i + 1}/{len(chunks)} 部分...")

            context = f"这是Paul Graham的文章《{title}》的第{i + 1}部分，共{len(chunks)}部分。"
            translated_chunk = self.translate_text(chunk, context)

            if translated_chunk:
                translated_chunks.append(translated_chunk)
            else:
                print(f"    第 {i + 1} 部分翻译失败")
                translated_chunks.append(chunk)  # 保留原文

            # 智能延迟 - 根据API限制优化 (RPM:1000 ≈ 每秒16.7次)
            # 缓存命中时不需要延迟，API调用时适当延迟
            if translated_chunk and not self.get_cached_translation(chunk):
                time.sleep(0.1)  # 减少延迟，提高效率

        # 组合翻译结果
        translated_content = '\n\n'.join(translated_chunks)

        # 构建最终文档 - 添加metadata头部
        final_content = f"""---
title: "{chinese_title}"
original_title: "{title}"
author: "Paul Graham"
translator: "{self.model} (SiliconFlow)"
translate_date: "{datetime.now().strftime('%Y-%m-%d')}"
source_file: "{Path(article_path).name}"
---

# {chinese_title}

{translated_content}"""

        return {
            'title': chinese_title,
            'original_title': title,
            'content': final_content,
            'model': self.model,
            'filename': Path(article_path).name  # 使用原文件名
        }


def clean_filename(filename):
    """清理文件名"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def translate_articles():
    """翻译文章"""
    # API配置
    api_key = os.getenv('SILICONFLOW_API_KEY')
    if not api_key:
        print("错误：未找到API密钥！")
        print("请确保在.env文件中设置了SILICONFLOW_API_KEY")
        return

    translator = DeepSeekTranslator(api_key)

    # 输入和输出目录
    input_dir = Path("pg_essays")
    output_dir = Path("pg_essays_cn")
    output_dir.mkdir(exist_ok=True)

    # 获取所有markdown文件
    md_files = list(input_dir.glob("*.md"))
    existing_files = list(output_dir.glob("*.md"))
    print(f"找到 {len(md_files)} 篇文章")
    print(f"已翻译 {len(existing_files)} 篇文章")

    # 选择要翻译的文章数量
    print("\n选择翻译数量:")
    print("1. 翻译前5篇（测试）")
    print("2. 翻译前20篇")
    print("3. 翻译指定文章")
    print("4. 翻译全部")
    print("5. 继续翻译（跳过已翻译）")

    # 默认选择翻译前5篇（测试）
    choice = '1'
    print(f"\n自动选择: {choice} - 翻译前5篇（测试）")

    if choice == '1':
        files_to_translate = md_files[:5]
    elif choice == '2':
        files_to_translate = md_files[:20]
    elif choice == '3':
        print("\n可用文章:")
        for i, file in enumerate(md_files[:20]):
            print(f"{i + 1}. {file.stem}")

        try:
            indices = input("\n请输入要翻译的文章编号（逗号分隔）: ").split(',')
            files_to_translate = [md_files[int(i.strip()) - 1] for i in indices if i.strip().isdigit()]
        except (ValueError, IndexError):
            print("输入错误，默认翻译前5篇")
            files_to_translate = md_files[:5]
    elif choice == '5':
        # 跳过已翻译的文章
        translated_titles = {f.stem.split('_')[0] for f in existing_files}
        files_to_translate = [f for f in md_files if f.stem not in translated_titles]
        print(f"发现 {len(files_to_translate)} 篇未翻译的文章")
    else:
        files_to_translate = md_files

    print(f"\n将翻译 {len(files_to_translate)} 篇文章")

    if len(files_to_translate) == 0:
        print("没有需要翻译的文章！")
        return

    # 并发翻译文章
    results = []
    
    # 使用线程池进行并发翻译
    max_workers = min(translator.max_concurrent, len(files_to_translate))
    print(f"使用 {max_workers} 个并发线程进行翻译...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有翻译任务
        future_to_file = {
            executor.submit(translator.translate_article, file_path): file_path 
            for file_path in files_to_translate
        }
        
        # 处理完成的任务
        for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
            file_path = future_to_file[future]
            print(f"\n{'=' * 50}")
            print(f"完成进度: {i + 1}/{len(files_to_translate)} - {file_path.name}")
            
            try:
                result = future.result()
                if result:
                    # 保存翻译结果 - 使用原文件名
                    output_path = output_dir / result['filename']

                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(result['content'])

                    print(f"  ✓ 已保存: {result['filename']}")
                    results.append(result)
                else:
                    print(f"  ✗ 翻译失败")

            except Exception as e:
                print(f"  ✗ 处理失败: {e}")

    # 保存翻译记录
    summary = {
        'total_files': len(files_to_translate),
        'successful': len(results),
        'model': translator.model,
        'translated_at': datetime.now().isoformat(),
        'stats': translator.stats,
        'results': results
    }

    with open('translation_log.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 打印统计信息
    translator.print_stats()
    
    print(f"\n{'=' * 50}")
    print(f"翻译完成！")
    print(f"成功翻译: {len(results)} 篇")
    print(f"翻译模型: {translator.model}")
    print(f"文件保存在: {output_dir}")
    print(f"翻译记录: translation_log.json")


if __name__ == "__main__":
    translate_articles()
