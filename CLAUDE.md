# CLAUDE.md

此文件为在本代码库中工作的 Claude Code (claude.ai/code) 提供指导。

## 项目概述

这是一个综合性的 Paul Graham 文章爬虫和翻译系统，功能包括：
1. 从 paulgraham.com 爬取文章
2. 将文章转换为 Markdown 格式
3. 生成 EPUB 电子书
4. 使用多种翻译服务提供中文翻译能力

## 核心架构

### 爬虫管道
- **入口点**: `scrape_all_essays.py` (交互式), `pg_scraper_final.py` (快速测试)
- **增强爬虫**: `pg_enhanced_simple.py` 和 `pg_enhanced_scraper.py` 提供缓存和改进的处理
- **输出**: 文章保存到 `articles/` 或 `pg_essays/` 目录，元数据保存为 JSON 文件

### 翻译系统
- **AI 翻译**: `ai_translator.py` 使用 SiliconFlow 的 DeepSeek-V3 模型进行高质量翻译
- **缓存**: 两个系统都在 `translation_cache/` 目录实现智能缓存
- **输出**: 中文文章保存到 `chinese_articles/` 或 `pg_essays_cn/`

### EPUB 生成
- **增强生成器**: `regenerate_epub.py` 从现有文章创建功能丰富的 EPUB
- **多种输出格式**: 支持英文和中文版本
- **元数据保留**: 维护文章日期、标题和结构

## 开发环境

### 设置
```bash
# 安装依赖
pip install -r requirements.txt
```

### 主要依赖
- `requests` + `beautifulsoup4`: 网页爬虫
- `html2text`: HTML 转 Markdown
- `ebooklib`: EPUB 生成
- `weasyprint`: PDF 生成支持

## 常用命令

### 爬取文章
```bash
# 快速测试 (20篇文章)
python pg_scraper_final.py

# 交互式爬取选项
python scrape_all_essays.py

# 带缓存的增强爬取
python pg_enhanced_simple.py
```

### 翻译
```bash
# AI 翻译 (推荐高质量)
python ai_translator.py

# 免费翻译服务
python translate_to_chinese.py
python translate_articles.py
```

### EPUB 生成
```bash
# 从现有文章生成增强 EPUB
python regenerate_epub.py

# 导入现有文章并重新生成
python import_and_regenerate.py
```

## 目录结构

### 输入/输出目录
- `articles/` 或 `pg_essays/`: Markdown 格式的原始英文文章
- `chinese_articles/` 或 `pg_essays_cn/`: 翻译后的中文文章
- `output/`: 生成的 EPUB 文件
- `cache/`: 爬取缓存 (JSON 文件)
- `translation_cache/`: 翻译缓存 (文本文件)

### 元数据文件
- `*_metadata.json`: 文章元数据 (标题、URL、日期、计数)
- `cache_index.json`: 爬取内容的缓存索引

## 翻译工作流

项目支持两种翻译方式：

1. **AI 翻译** (ai_translator.py):
   - 使用 SiliconFlow 的 DeepSeek-V3 模型
   - 提供高质量、上下文感知的翻译
   - 通过智能分块处理长文章
   - 维护专业术语一致性

2. **传统翻译** (translate_*.py):
   - 使用免费 API (Bing, Google, 百度)
   - 实现重试逻辑和速率限制
   - 适合基本翻译需求

## 数据流

```
paulgraham.com → 爬虫 → Markdown文件 → 翻译器 → 中文文件 → EPUB生成器
                     ↓              ↓                        ↓
                  缓存         元数据              翻译缓存
```

## 重要说明

### API 密钥
- AI 翻译器需要在 `ai_translator.py` (第173行) 中配置 SiliconFlow API 密钥
- 免费翻译器不需要 API 密钥但有速率限制

### 速率限制
- 爬虫在请求之间实施 1.5-2 秒延迟
- 翻译服务内置重试逻辑
- 两个系统都尊重服务器资源

### 文件命名
- 所有文件名都经过清理以移除非法字符
- 中文标题可能包含括号中的解释性注释
- EPUB 文件包含时间戳以避免冲突

### 缓存管理
- 爬取缓存防止重复下载文章
- 翻译缓存防止重复翻译片段
- 如需完全刷新，可以安全删除缓存文件