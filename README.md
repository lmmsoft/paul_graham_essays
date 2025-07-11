# Paul Graham 文章爬虫

这是一个用于抓取Paul Graham所有文章并生成EPUB电子书的Python爬虫。

## 功能特点

- 自动抓取Paul Graham网站上的所有文章
- 将HTML内容转换为Markdown格式
- 生成EPUB格式的电子书，方便在各种设备上阅读
- 保存文章元数据（标题、URL、日期等）
- 支持断点续爬和错误处理

## 依赖安装

```bash
pip install -r requirements.txt
```

所需依赖：
- requests: 网络请求
- beautifulsoup4: HTML解析
- html2text: HTML转Markdown
- ebooklib: EPUB生成
- lxml: XML处理

## 使用方法

### 1. 快速测试（抓取20篇文章）
```bash
python pg_scraper_final.py
```

### 2. 完整抓取（交互式选择）
```bash
python scrape_all_essays.py
```

运行后会提供以下选项：
- 抓取前50篇文章（推荐）
- 抓取所有232篇文章
- 自定义数量

## 输出文件

- `articles/` 或 `pg_essays/`: 包含所有Markdown格式的文章
- `articles_metadata.json` 或 `pg_essays_metadata.json`: 文章元数据
- `paul_graham_essays.epub`: 生成的EPUB电子书

## 注意事项

1. 爬虫会在每次请求之间延迟1.5-2秒，以避免对服务器造成压力
2. 完整抓取232篇文章大约需要30-60分钟
3. 生成的EPUB文件可以在Kindle、Apple Books、Google Play Books等阅读器中打开
4. 所有内容版权归Paul Graham所有，仅供个人学习使用

## 故障排除

如果遇到网络错误，可以：
1. 检查网络连接
2. 增加请求超时时间
3. 查看`metadata.json`文件中的失败记录

## 许可

本爬虫工具仅供学习研究使用，请尊重原作者版权。