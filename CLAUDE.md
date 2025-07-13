# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Paul Graham essay scraper and translation system that:
1. Scrapes essays from paulgraham.com
2. Converts them to Markdown format
3. Generates EPUB ebooks
4. Provides Chinese translation capabilities using multiple translation services

## Core Architecture

### Scraping Pipeline
- **Entry Points**: `scrape_all_essays.py` (interactive), `pg_scraper_final.py` (quick test)
- **Enhanced Scraper**: `pg_enhanced_simple.py` and `pg_enhanced_scraper.py` provide caching and improved processing
- **Output**: Articles saved to `articles/` or `pg_essays/` directories with metadata in JSON files

### Translation System
- **AI Translation**: `ai_translator.py` uses SiliconFlow's DeepSeek-V3 model for high-quality translations
- **Traditional Translation**: `translate_to_chinese.py` and `translate_articles.py` use free translation APIs (Bing, Google, etc.)
- **Caching**: Both systems implement smart caching in `translation_cache/` directory
- **Output**: Chinese articles saved to `chinese_articles/` or `pg_essays_cn/`

### EPUB Generation
- **Enhanced Generator**: `regenerate_epub.py` creates feature-rich EPUBs from existing articles
- **Multiple Output Formats**: Supports both English and Chinese versions
- **Metadata Preservation**: Maintains article dates, titles, and structure

## Development Environment

### Setup
```bash
# Install dependencies
pip install -r requirements.txt
```

### Key Dependencies
- `requests` + `beautifulsoup4`: Web scraping
- `html2text`: HTML to Markdown conversion
- `ebooklib`: EPUB generation
- `translators`: Free translation APIs
- `weasyprint`: PDF generation support

## Common Commands

### Scraping Articles
```bash
# Quick test (20 articles)
python pg_scraper_final.py

# Interactive scraping with options
python scrape_all_essays.py

# Enhanced scraping with caching
python pg_enhanced_simple.py
```

### Translation
```bash
# AI translation (recommended for quality)
python ai_translator.py

# Free translation services
python translate_to_chinese.py
python translate_articles.py
```

### EPUB Generation
```bash
# Generate enhanced EPUB from existing articles
python regenerate_epub.py

# Import existing articles and regenerate
python import_and_regenerate.py
```

## Directory Structure

### Input/Output Directories
- `articles/` or `pg_essays/`: Original English articles in Markdown
- `chinese_articles/` or `pg_essays_cn/`: Translated Chinese articles
- `output/`: Generated EPUB files
- `cache/`: Scraping cache (JSON files)
- `translation_cache/`: Translation cache (text files)

### Metadata Files
- `*_metadata.json`: Article metadata (titles, URLs, dates, counts)
- `cache_index.json`: Cache indexing for scraped content

## Translation Workflow

The project supports two translation approaches:

1. **AI Translation** (ai_translator.py):
   - Uses SiliconFlow's DeepSeek-V3 model
   - Provides high-quality, context-aware translations
   - Handles long articles by intelligent chunking
   - Maintains professional terminology consistency

2. **Traditional Translation** (translate_*.py):
   - Uses free APIs (Bing, Google, Baidu)
   - Implements retry logic and rate limiting
   - Suitable for basic translation needs

## Data Flow

```
paulgraham.com → Scraper → Markdown Files → Translator → Chinese Files → EPUB Generator
                     ↓              ↓                        ↓
                  Cache         Metadata              Translation Cache
```

## Important Notes

### API Keys
- AI translator requires SiliconFlow API key in `ai_translator.py` (line 173)
- Free translators don't require API keys but have rate limits

### Rate Limiting
- Scrapers implement 1.5-2 second delays between requests
- Translation services have built-in retry logic
- Both systems respect server resources

### File Naming
- All filenames are sanitized to remove illegal characters
- Chinese titles may include explanatory notes in parentheses
- EPUB files include timestamps to avoid conflicts

### Cache Management
- Scraping cache prevents re-downloading articles
- Translation cache prevents re-translating segments
- Cache files are safe to delete if full refresh is needed