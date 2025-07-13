#!/usr/bin/env python3
"""
使用SiliconFlow的DeepSeek-V3模型翻译Paul Graham文章
"""

import os
import re
import time
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class DeepSeekTranslator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model = "deepseek-ai/DeepSeek-V3"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def translate_text(self, text, context=""):
        """翻译文本"""
        prompt = f"""请将以下英文文章翻译成中文。要求：
1. 准确翻译原文意思，保持原有的语调和风格
2. 专业术语要准确，保持一致性
3. 保留原文的段落结构
4. 翻译要自然流畅，符合中文表达习惯
5. 对于专业概念，必要时可以在首次出现时保留英文原文在括号中

{context}

原文：
{text}

翻译："""

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
            response = requests.post(self.base_url, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"API响应格式错误: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
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
            print(f"    翻译第 {i+1}/{len(chunks)} 部分...")
            
            context = f"这是Paul Graham的文章《{title}》的第{i+1}部分，共{len(chunks)}部分。"
            translated_chunk = self.translate_text(chunk, context)
            
            if translated_chunk:
                translated_chunks.append(translated_chunk)
            else:
                print(f"    第 {i+1} 部分翻译失败")
                translated_chunks.append(chunk)  # 保留原文
            
            # 添加延迟避免API限制
            time.sleep(2)
        
        # 组合翻译结果
        translated_content = '\n\n'.join(translated_chunks)
        
        # 构建最终文档
        final_content = f"""# {chinese_title}

> 原文：{title}  
> 作者：Paul Graham  
> 翻译模型：{self.model} (SiliconFlow)  
> 翻译时间：{datetime.now().strftime('%Y年%m月%d日')}

{translated_content}"""
        
        return {
            'title': chinese_title,
            'original_title': title,
            'content': final_content,
            'model': self.model
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
    print(f"找到 {len(md_files)} 篇文章")
    
    # 选择要翻译的文章数量
    print("\n选择翻译数量:")
    print("1. 翻译前5篇（测试）")
    print("2. 翻译前20篇")
    print("3. 翻译指定文章")
    print("4. 翻译全部")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == '1':
        files_to_translate = md_files[:5]
    elif choice == '2':
        files_to_translate = md_files[:20]
    elif choice == '3':
        print("\n可用文章:")
        for i, file in enumerate(md_files[:20]):
            print(f"{i+1}. {file.stem}")
        
        try:
            indices = input("\n请输入要翻译的文章编号（逗号分隔）: ").split(',')
            files_to_translate = [md_files[int(i.strip())-1] for i in indices if i.strip().isdigit()]
        except (ValueError, IndexError):
            print("输入错误，默认翻译前5篇")
            files_to_translate = md_files[:5]
    else:
        files_to_translate = md_files
    
    print(f"\n将翻译 {len(files_to_translate)} 篇文章")
    
    # 翻译文章
    results = []
    for i, file_path in enumerate(files_to_translate):
        print(f"\n{'='*50}")
        print(f"进度: {i+1}/{len(files_to_translate)}")
        
        try:
            result = translator.translate_article(file_path)
            if result:
                # 保存翻译结果
                filename = clean_filename(result['title']) + '.md'
                output_path = output_dir / filename
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result['content'])
                
                print(f"  ✓ 已保存: {filename}")
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
        'results': results
    }
    
    with open('translation_log.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"翻译完成！")
    print(f"成功翻译: {len(results)} 篇")
    print(f"翻译模型: {translator.model}")
    print(f"文件保存在: {output_dir}")
    print(f"翻译记录: translation_log.json")

if __name__ == "__main__":
    translate_articles()