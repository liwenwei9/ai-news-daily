#!/usr/bin/env python3
"""
AI News Daily - v3.0 DeepSeek版
使用DeepSeek API进行翻译，成本更低，中文能力更强

使用方法：
1. 安装依赖：pip install arxiv feedparser pytz openai
2. 设置环境变量：export DEEPSEEK_API_KEY='your-deepseek-api-key'
3. 运行脚本：python3 ai_news_daily_v3_deepseek.py

DeepSeek API文档：https://platform.deepseek.com/api-docs/
"""

import os
import json
import datetime
import pytz
from typing import List, Dict, Any
import arxiv
import feedparser
import re
import random
import hashlib
import time
import requests

# 尝试导入OpenAI库（DeepSeek兼容OpenAI格式）
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ 警告：未安装openai库，翻译功能将被禁用")
    print("   安装命令：pip install openai")

class AINewsDaily:
    def __init__(self):
        self.github_user = "liwenwei9"
        self.repo_name = "ai-news-daily"
        self.website_url = f"https://{self.github_user}.github.io/{self.repo_name}/"

        # 创建输出目录
        pass # os.makedirs('docs', exist_ok=True)

        # DeepSeek客户端
        self.deepseek_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if api_key:
                # DeepSeek使用OpenAI兼容的接口
                self.deepseek_client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                print("✅ DeepSeek API已配置")
                print("💰 使用DeepSeek翻译，成本约为OpenAI的1/10")
            else:
                print("⚠️ 警告：未设置DEEPSEEK_API_KEY环境变量，翻译功能将被禁用")

        # 翻译缓存
        self.translation_cache = self.load_cache()

        # 新闻源配置
        self.news_sources = {
            # 国际科技媒体
            'techcrunch': {
                'name': 'TechCrunch',
                'url': 'https://techcrunch.com/category/artificial-intelligence/feed/',
                'priority': 1
            },
            'theverge': {
                'name': 'The Verge',
                'url': 'https://www.theverge.com/rss/ai/index.xml',
                'priority': 1
            },
            'wired': {
                'name': 'Wired',
                'url': 'https://www.wired.com/feed/tag/ai/latest/rss',
                'priority': 1
            },
            'venturebeat': {
                'name': 'VentureBeat',
                'url': 'https://venturebeat.com/category/ai/feed/',
                'priority': 1
            },
            # AI垂直媒体/公司博客
            'openai': {
                'name': 'OpenAI Blog',
                'url': 'https://openai.com/blog/rss.xml',
                'priority': 2
            },
            'google_ai': {
                'name': 'Google AI',
                'url': 'https://blog.google/technology/ai/rss/',
                'priority': 2
            },
            'microsoft_ai': {
                'name': 'Microsoft AI',
                'url': 'https://blogs.microsoft.com/ai/feed/',
                'priority': 2
            },
            'meta_ai': {
                'name': 'Meta AI',
                'url': 'https://ai.meta.com/feed/',
                'priority': 2
            },
            'huggingface': {
                'name': 'Hugging Face',
                'url': 'https://huggingface.co/blog/feed.xml',
                'priority': 2
            },
            # 国内科技媒体
            '36kr': {
                'name': '36氪',
                'url': 'https://36kr.com/newsflashes',
                'priority': 3
            },
            'huxiu': {
                'name': '虎嗅',
                'url': 'https://www.huxiu.com/',
                'priority': 3
            },
            'geekpark': {
                'name': '极客公园',
                'url': 'https://www.geekpark.com/news',
                'priority': 3
            }
        }

        # 论文源配置
        self.paper_sources = {
            'arxiv': {
                'name': 'arXiv',
                'count': 5,
                'categories': ['cs.AI', 'cs.LG', 'cs.CV']
            },
            'huggingface': {
                'name': 'Hugging Face',
                'count': 5
            },
            'semantic_scholar': {
                'name': 'Semantic Scholar',
                'count': 5
            }
        }

    def load_cache(self) -> Dict[str, str]:
        """加载翻译缓存"""
        try:
            with open('translation_cache.json', 'r', encoding='utf-8') as f:
                cache = json.load(f)
                print(f"📦 加载翻译缓存：{len(cache)}条")
                return cache
        except:
            return {}

    def save_cache(self):
        """保存翻译缓存"""
        try:
            with open('translation_cache.json', 'w', encoding='utf-8') as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存缓存失败: {e}")

    def translate_to_chinese(self, text: str, is_title: bool = False) -> str:
        """
        使用DeepSeek API翻译成中文
        DeepSeek对中文的理解和翻译质量非常好
        """
        # 如果没有配置DeepSeek，直接返回原文
        if not self.deepseek_client:
            return text

        # 生成缓存键
        cache_key = hashlib.md5(f"deepseek_{text}".encode()).hexdigest()

        # 检查缓存
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        # 调用DeepSeek API翻译
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if is_title:
                    prompt = f"请将以下AI论文标题翻译成中文，保持专业性和准确性：\n\n{text}"
                else:
                    prompt = f"请将以下AI论文摘要翻译成中文，保持专业性和准确性：\n\n{text}"

                response = self.deepseek_client.chat.completions.create(
                    model="deepseek-chat",  # DeepSeek的主要模型
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的AI领域翻译专家。请将内容翻译成中文，保持原意和专业术语的准确性。直接输出翻译结果，不要添加任何解释。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=500 if is_title else 1000
                )

                translated = response.choices[0].message.content.strip()

                # 清理可能的多余内容（DeepSeek有时会添加解释）
                # 如果翻译结果包含"翻译："或"翻译结果："等前缀，去除它们
                prefixes = ["翻译：", "翻译结果：", "中文翻译：", "翻译为："]
                for prefix in prefixes:
                    if translated.startswith(prefix):
                        translated = translated[len(prefix):].strip()

                # 保存到缓存
                self.translation_cache[cache_key] = translated
                self.save_cache()

                print(f"✅ DeepSeek翻译: {text[:40]}... → {translated[:40]}...")

                return translated

            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"⚠️ 翻译失败（已重试{max_retries}次）: {e}")
                    return text  # 返回原文
                print(f"⚠️ 翻译失败，重试中... ({attempt + 1}/{max_retries})")
                time.sleep(2)

        return text

    def generate_one_sentence_summary(self, text: str, max_length: int = 80) -> str:
        """生成一句话概要（引号形式）"""
        text = ' '.join(text.split())
        sentences = re.split(r'[.。!?！？]', text)

        if sentences and len(sentences[0]) > 10:
            first_sentence = sentences[0].strip()
            if len(first_sentence) <= max_length:
                return f'"{first_sentence}"'
            else:
                return f'"{first_sentence[:max_length]}..."'

        if len(text) <= max_length:
            return f'"{text}"'
        return f'"{text[:max_length]}..."'

    def get_arxiv_papers(self) -> List[Dict[str, Any]]:
        """从arXiv获取AI论文"""
        print("📚 获取arXiv论文...")

        papers = []
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query="cat:cs.AI OR cat:cs.LG",
                max_results=5,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            for result in client.results(search):
                # 使用DeepSeek翻译标题
                title_zh = self.translate_to_chinese(result.title, is_title=True)

                # 生成一句话概要
                summary_quote = self.generate_one_sentence_summary(title_zh)

                # 翻译完整摘要（用于详情页，150-300字）
                summary_zh = self.translate_to_chinese(result.summary[:2000])

                paper = {
                    'type': 'paper',
                    'id': result.entry_id.split('/')[-1],
                    'title': result.title,
                    'title_zh': title_zh,
                    'summary_quote': summary_quote,
                    'authors': [author.name for author in result.authors[:3]],
                    'summary': summary_zh,
                    'summary_en': result.summary,
                    'published': result.published.strftime('%Y-%m-%d'),
                    'published_time': result.published,
                    'pdf_url': result.pdf_url,
                    'arxiv_url': f"https://arxiv.org/abs/{result.entry_id.split('/')[-1]}",
                    'category': result.primary_category,
                    'score': random.randint(50, 500)
                }
                papers.append(paper)

            print(f"✅ 获取到 {len(papers)} 篇论文")

        except Exception as e:
            print(f"⚠️ 获取论文失败: {e}")
            import traceback
            traceback.print_exc()

        return papers

    def get_huggingface_papers(self, count: int = 5) -> List[Dict[str, Any]]:
        """从Hugging Face获取AI论文"""
        print("📚 获取Hugging Face论文...")

        papers = []
        try:
            url = "https://huggingface.co/api/papers"
            params = {
                'sort': 'downloads',
                'direction': -1,
                'limit': count
            }

            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()

                for item in data[:count]:
                    title = item.get('title', '')
                    if not title:
                        continue

                    # 尝试通过arXiv ID获取摘要
                    arxiv_id = item.get('arxiv_id', '')
                    summary_en = ''
                    if arxiv_id:
                        try:
                            # 从arXiv获取摘要
                            arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
                            arxiv_response = requests.get(arxiv_url, timeout=10)
                            if arxiv_response.status_code == 200:
                                match = re.search(r'<span class="abstract-full-text"[^>]*>(.*?)</span>', arxiv_response.text, re.DOTALL)
                                if match:
                                    summary_en = re.sub(r'<.*?>', '', match.group(1)).strip()
                        except:
                            pass

                    # 如果没有获取到摘要，使用标题
                    if not summary_en:
                        summary_en = title

                    title_zh = self.translate_to_chinese(title, is_title=True)
                    summary_zh = self.translate_to_chinese(summary_en[:2000]) if summary_en else title_zh

                    paper = {
                        'type': 'paper',
                        'id': item.get('id', item.get('paper_id', '')),
                        'title': title,
                        'title_zh': title_zh,
                        'summary_quote': self.generate_one_sentence_summary(title_zh),
                        'authors': [a.get('author_name', '') for a in item.get('authors', [])[:3]],
                        'summary': summary_zh,
                        'summary_en': summary_en,
                        'published': item.get('published', datetime.datetime.now().strftime('%Y-%m-%d')),
                        'published_time': datetime.datetime.now(),
                        'pdf_url': item.get('pdf_url', ''),
                        'arxiv_url': item.get('arxiv_id', ''),
                        'url': item.get('url', ''),
                        'category': 'Hugging Face',
                        'source': 'Hugging Face',
                        'score': random.randint(50, 500)
                    }
                    papers.append(paper)

                print(f"✅ 获取到 {len(papers)} 篇论文")

        except Exception as e:
            print(f"⚠️ 获取Hugging Face论文失败: {e}")

        return papers


    def get_semantic_scholar_papers(self, count: int = 5) -> List[Dict[str, Any]]:
        """从Semantic Scholar获取AI论文"""
        print("📚 获取Semantic Scholar论文...")

        papers = []
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                'query': 'artificial intelligence machine learning',
                'limit': count,
                'fields': 'title,abstract,authors,year,url,externalIds'
            }

            headers = {'Accept': 'application/json'}
            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                papers_data = data.get('data', [])

                for item in papers_data[:count]:
                    title = item.get('title', '')
                    if not title:
                        continue

                    title_zh = self.translate_to_chinese(title, is_title=True)

                    abstract = item.get('abstract', '')
                    # 翻译完整摘要（用于详情页，150-300字）
                    summary_zh = self.translate_to_chinese(abstract[:2000]) if abstract else title_zh

                    authors = item.get('authors', [])[:3]
                    authors_names = [a.get('name', '') for a in authors]

                    external_ids = item.get('externalIds', {})
                    arxiv_id = external_ids.get('ArXiv', '')

                    paper = {
                        'type': 'paper',
                        'id': arxiv_id or item.get('paperId', ''),
                        'title': title,
                        'title_zh': title_zh,
                        'summary_quote': self.generate_one_sentence_summary(title_zh),
                        'authors': authors_names,
                        'summary': summary_zh,
                        'summary_en': abstract,
                        'published': str(item.get('year', datetime.datetime.now().year)),
                        'published_time': datetime.datetime.now(),
                        'pdf_url': f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else '',
                        'arxiv_url': f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else '',
                        'url': item.get('url', ''),
                        'category': 'AI/ML',
                        'source': 'Semantic Scholar',
                        'score': random.randint(50, 500)
                    }
                    papers.append(paper)

                print(f"✅ 获取到 {len(papers)} 篇论文")

        except requests.exceptions.RequestException as e:
            # 网络错误（DNS解析失败、连接超时等）
            print(f"⚠️ 获取Semantic Scholar论文失败（网络问题）: {e}")
        except Exception as e:
            print(f"⚠️ 获取Semantic Scholar论文失败: {e}")

        return papers

    def get_tech_news(self, target_count: int = 20) -> List[Dict[str, Any]]:
        """获取科技新闻（多源）"""
        print("📰 获取科技新闻...")

        news_items = []

        # 第一步：先获取所有新闻（不翻译）
        for source_key, source_config in self.news_sources.items():
            try:
                print(f"  📡 正在获取: {source_config['name']}")
                feed = feedparser.parse(source_config['url'])

                for entry in feed.entries:
                    text = f"{entry.title} {entry.get('summary', '')}"
                    # AI相关关键词过滤
                    keywords = ['ai', 'artificial intelligence', 'machine learning',
                               'deep learning', 'gpt', 'llm', 'openai', 'google',
                               'anthropic', 'meta', '人工智能', '机器学习', '深度学习']

                    if any(kw in text.lower() for kw in keywords):
                        summary_text = entry.get('summary', '')
                        # 清理HTML标签
                        summary_text = re.sub(r'<[^>]+>', '', summary_text)

                        # 发布时间
                        published_time = datetime.datetime.now()
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            try:
                                published_time = datetime.datetime(*entry.published_parsed[:6])
                            except:
                                pass

                        news = {
                            'type': 'news',
                            'title': entry.title,
                            'title_zh': None,  # 稍后翻译
                            'summary_quote': None,
                            'source': source_config['name'],
                            'source_key': source_key,
                            'link': entry.link,
                            'summary': None,  # 稍后翻译
                            'summary_en': summary_text,
                            'published': entry.get('published', datetime.datetime.now().strftime('%Y-%m-%d')),
                            'published_time': published_time,
                            'priority': source_config['priority'],
                            'score': random.randint(100, 800)
                        }

                        news_items.append(news)

                print(f"    ✅ {source_config['name']}: 获取成功")

            except Exception as e:
                print(f"    ⚠️ {source_config['name']}: 获取失败 - {e}")

        # 按优先级排序，同优先级按时间排序
        news_items.sort(key=lambda x: (x['priority'], x['published_time']), reverse=True)

        # 限制数量（只保留目标数量）
        news_items = news_items[:target_count]

        # 第二步：只对最终选中的新闻进行翻译
        for news in news_items:
            news['title_zh'] = self.translate_to_chinese(news['title'], is_title=True)
            # 翻译完整摘要（用于详情页，150-300字）
            news['summary_zh'] = self.translate_to_chinese(news['summary_en'][:2000]) if news['summary_en'] else news['title_zh']
            news['summary'] = news['summary_zh']
            news['summary_quote'] = self.generate_one_sentence_summary(news['title_zh'])

        print(f"✅ 共获取 {len(news_items)} 条新闻")
        return news_items

    def merge_and_sort_items(self, papers, news):
        """合并论文和新闻，并按时间排序"""
        import pytz
        from datetime import datetime
        import email.utils  # 用于解析RFC 2822格式的时间（如Tue, 03 Mar 2026 13:30:00 +0000）

        # 统一时区为UTC，消除offset-naive/aware差异
        utc = pytz.UTC
        beijing_tz = pytz.timezone('Asia/Shanghai')

        items = []
        
        # 处理论文时间（确保带时区）
        for paper in papers:
            if paper.get('published'):
                pub_dt = None
                # 处理论文的时间格式（通常是ISO格式）
                try:
                    if isinstance(paper['published'], str):
                        # 尝试ISO格式解析
                        pub_dt = datetime.fromisoformat(paper['published'].replace('Z', '+00:00'))
                    else:
                        pub_dt = paper['published']
                except:
                    # 解析失败则用当前时间兜底
                    pub_dt = datetime.now(utc)
                
                # 确保时间带时区
                if pub_dt.tzinfo is None or pub_dt.tzinfo.utcoffset(pub_dt) is None:
                    pub_dt = utc.localize(pub_dt)
                
                paper['published'] = pub_dt
            items.append(paper)
        
        # 处理新闻时间（兼容RFC 2822格式）
        for item in news:
            if item.get('published'):
                pub_dt = None
                try:
                    if isinstance(item['published'], str):
                        # 先尝试解析RFC 2822格式（新闻常用）
                        parsed_date = email.utils.parsedate_tz(item['published'])
                        if parsed_date:
                            pub_dt = datetime.fromtimestamp(email.utils.mktime_tz(parsed_date))
                            # 转为UTC时区的aware时间
                            pub_dt = utc.localize(pub_dt)
                        else:
                            # 备用：尝试ISO格式
                            pub_dt = datetime.fromisoformat(item['published'].replace('Z', '+00:00'))
                    else:
                        pub_dt = item['published']
                except:
                    # 所有解析失败则用当前时间兜底
                    pub_dt = datetime.now(utc)
                
                # 确保时间带时区
                if pub_dt.tzinfo is None or pub_dt.tzinfo.utcoffset(pub_dt) is None:
                    pub_dt = utc.localize(pub_dt)
                
                item['published'] = pub_dt
            items.append(item)
        
        # 按发布时间降序排序（最新的在前）
        items.sort(key=lambda x: x.get('published', datetime.min.replace(tzinfo=utc)), reverse=True)
        
        return items
		
    def generate_html(self, items: List[Dict], date_str: str = None) -> str:
        """生成HTML页面"""
        if date_str is None:
            now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
            date_str = now.strftime('%Y/%m/%d')

        paper_count = sum(1 for item in items if item['type'] == 'paper')
        news_count = sum(1 for item in items if item['type'] == 'news')

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用中文读AI新闻 - {self.github_user}</title>
    <meta name="description" content="每日AI论文和新闻，全中文阅读 ">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --orange: #ff6600;
            --text: #333;
            --text-light: #828282;
            --bg: #f6f6ef;
            --card: #ffffff;
            --border: #e6e6e6;
            --yellow: #ffc107;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            min-height: 100vh;
        }}

        .nav {{
            background: white;
            border-bottom: 1px solid var(--border);
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}

        .nav-container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text);
        }}

        .theme-toggle {{
            padding: 6px 12px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            font-size: 1.2rem;
            transition: all 0.3s;
        }}

        .theme-toggle:hover {{
            background: var(--border);
        }}

        .hero {{
            text-align: center;
            padding: 60px 20px 40px;
            background: white;
        }}

        .hero h1 {{
            font-size: 2.5rem;
            margin-bottom: 15px;
            font-weight: 700;
            color: var(--text);
        }}

        .hero h1 .highlight {{
            color: var(--yellow);
        }}

        .hero .subtitle {{
            font-size: 1.1rem;
            color: var(--text-light);
            margin-bottom: 30px;
        }}

        .tabs {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 30px;
        }}

        .tab {{
            padding: 10px 30px;
            background: var(--bg);
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            color: var(--text);
        }}

        .tab.active {{
            background: var(--yellow);
            color: white;
        }}

        .tab:hover {{
            opacity: 0.8;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 30px 20px;
        }}

        .date-header {{
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 30px;
            color: var(--text);
        }}

        .item {{
            background: white;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.3s;
        }}

        .item:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .item-header {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }}

        .item-score {{
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
            padding-top: 5px;
        }}

        .triangle {{
            width: 0;
            height: 0;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-bottom: 12px solid var(--orange);
            cursor: pointer;
        }}

        .score-number {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-light);
        }}

        .item-content {{
            flex: 1;
            min-width: 0;
        }}

        .item-title {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 8px;
            line-height: 1.4;
            cursor: pointer;
        }}

        .item-title:hover {{
            color: var(--orange);
        }}

        .item-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            font-size: 0.9rem;
            color: var(--text-light);
            margin-bottom: 12px;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .item-quote {{
            font-size: 1rem;
            color: var(--text);
            margin-bottom: 15px;
            font-style: italic;
            padding-left: 15px;
            border-left: 3px solid var(--yellow);
            line-height: 1.6;
        }}

        .item-summary {{
            font-size: 0.95rem;
            color: var(--text);
            line-height: 1.7;
            margin-bottom: 15px;
        }}

        .item-actions {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 14px;
            background: var(--orange);
            color: white !important;
            text-decoration: none;
            border-radius: 5px;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
        }}

        .btn:hover {{
            opacity: 0.9;
            transform: translateY(-1px);
        }}

        .btn-secondary {{
            background: var(--text-light);
        }}

        .type-badge {{
            display: inline-block;
            padding: 3px 8px;
            background: var(--yellow);
            color: white;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 8px;
        }}

        .type-badge.news {{
            background: #4CAF50;
        }}

        footer {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-light);
            background: white;
            border-top: 1px solid var(--border);
            margin-top: 50px;
        }}

        footer p {{
            margin: 8px 0;
            font-size: 0.9rem;
        }}

        footer a {{
            color: var(--orange);
            text-decoration: none;
            font-weight: 600;
        }}

        footer a:hover {{
            text-decoration: underline;
        }}

        @media (max-width: 768px) {{
            .hero h1 {{
                font-size: 1.8rem;
            }}

            .item-header {{
                gap: 10px;
            }}

            .item-title {{
                font-size: 1.1rem;
            }}

            .container {{
                padding: 20px 15px;
            }}
        }}
    </style>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <div class="logo">AI资讯日报</div>
            <button class="theme-toggle" onclick="toggleTheme()">☀️</button>
        </div>
    </nav>

    <div class="hero">
        <h1>用<span class="highlight">中文</span>读AI新闻</h1>
        <div class="subtitle">每日精选AI论文和科技新闻 </div>

        <div class="tabs">
            <button class="tab active" data-type="all">全部 ({len(items)})</button>
            <button class="tab" data-type="paper">论文 ({paper_count})</button>
            <button class="tab" data-type="news">新闻 ({news_count})</button>
        </div>
    </div>

    <div class="container">
        <div class="date-header">{date_str}</div>

        <div class="items-container">
            {self._generate_items_html(items)}
        </div>
    </div>

    <footer>
        <p>🤖 由AI自动生成 | 每日更新 | 使用DeepSeek翻译</p>
        <p>数据来源：arXiv + MIT Technology Review</p>
        <p>🚀 <a href="https://github.com/{self.github_user}/{self.repo_name}" target="_blank">查看GitHub项目</a></p>
        <p style="margin-top: 20px; font-size: 0.85rem;">灵感来源：<a href=" " target="_blank">Zeli</a></p>
    </footer>

    <script>
        document.querySelectorAll('.tab').forEach(tab => {{
            tab.addEventListener('click', function() {{
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                const type = this.dataset.type;
                document.querySelectorAll('.item').forEach(item => {{
                    if (type === 'all') {{
                        item.style.display = 'block';
                    }} else {{
                        item.style.display = item.dataset.type === type ? 'block' : 'none';
                    }}
                }});
            }});
        }});

        function toggleTheme() {{
            const btn = document.querySelector('.theme-toggle');
            const isDark = document.body.style.filter === 'invert(1)';

            if (isDark) {{
                document.body.style.filter = '';
                btn.textContent = '☀️';
            }} else {{
                document.body.style.filter = 'invert(1)';
                btn.textContent = '🌙';
            }}
        }}

        document.querySelectorAll('.triangle').forEach(triangle => {{
            triangle.addEventListener('click', function() {{
                const scoreEl = this.nextElementSibling;
                let score = parseInt(scoreEl.textContent);
                score += 1;
                scoreEl.textContent = score;

                this.style.borderBottomColor = '#ff4500';
                setTimeout(() => {{
                    this.style.borderBottomColor = 'var(--orange)';
                }}, 300);
            }});
        }});
    </script>
</body>
</html>'''
        return html

    def generate_root_index(self, latest_date: str) -> str:
        """生成根目录index.html（重定向到当天）"""
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI资讯日报 - 每日AI新闻和论文</title>
    <meta http-equiv="refresh" content="0;url={latest_date}/index.html">
    <style>
        body {{ font-family: -apple-system, sans-serif; text-align: center; padding: 50px; }}
        a {{ color: #ff6600; }}
    </style>
</head>
<body>
    <p>正在跳转到最新内容...</p>
    <p><a href="{latest_date}/index.html">如果未自动跳转，请点击这里</a></p>
</body>
</html>'''
        return html

    def _generate_items_html(self, items: List[Dict]) -> str:
        """生成条目HTML"""
        if not items:
            return '<p style="text-align: center; color: var(--text-light);">暂无数据</p>'

        html_parts = []
        for idx, item in enumerate(items, 1):
            item_type = item['type']
            type_name = '论文' if item_type == 'paper' else '新闻'
            type_class = 'paper' if item_type == 'paper' else 'news'

            # 生成详情页链接
            if item_type == 'paper':
                detail_link = f"paper-{idx}.html"
            else:
                detail_link = f"news-{idx}.html"

            meta_html = ''
            if item_type == 'paper':
                authors_str = ', '.join(item['authors'][:2])
                if len(item['authors']) > 2:
                    authors_str += ' et al.'
                meta_html = f'''
                    <div class="meta-item">👨‍🎓 {authors_str}</div>
                    <div class="meta-item">🏷️ {item['category']}</div>
                    <div class="meta-item">📅 {item['published']}</div>
                '''
            else:
                meta_html = f'''
                    <div class="meta-item">🏢 {item['source']}</div>
                    <div class="meta-item">📅 {item['published']}</div>
                '''

            actions_html = ''
            if item_type == 'paper':
                actions_html = f'''
                    <a href="{detail_link}" class="btn" target="_blank">📖 查看详情</a>
                    <a href="{item['pdf_url']}" class="btn btn-secondary" target="_blank">📄 PDF</a>
                    <a href="{item['arxiv_url']}" class="btn btn-secondary" target="_blank">🔗 arXiv</a>
                '''
            else:
                actions_html = f'''
                    <a href="{detail_link}" class="btn" target="_blank">📖 查看详情</a>
                    <a href="{item['link']}" class="btn btn-secondary" target="_blank">🔗 阅读原文</a>
                '''

            html = f'''
            <div class="item" data-type="{item_type}">
                <div class="item-header">
                    <div class="item-score">
                        <div class="triangle"></div>
                        <div class="score-number">{item['score']}</div>
                    </div>
                    <div class="item-content">
                        <div>
                            <span class="type-badge {type_class}">{type_name}</span>
                            <h3 class="item-title"><a href="{detail_link}" style="color: inherit; text-decoration: none;">{item.get('title_zh', item['title'])}</a></h3>
                        </div>
                        <div class="item-meta">
                            {meta_html}
                        </div>
                    </div>
                </div>
                <div class="item-quote">{item['summary_quote']}</div>
                <div class="item-summary">{item['summary'][:300]}...</div>
                <div class="item-actions">
                    {actions_html}
                </div>
            </div>
            '''
            html_parts.append(html)

        return '\n'.join(html_parts)

    def generate_detail_pages(self, items: List[Dict], output_dir: str, date_str: str):
        """生成所有详情页"""
        print("📄 生成详情页...")

        detail_dir = output_dir
        os.makedirs(detail_dir, exist_ok=True)

        for idx, item in enumerate(items, 1):
            if item['type'] == 'paper':
                filename = f"paper-{idx}.html"
            else:
                filename = f"news-{idx}.html"

            detail_html = self.generate_detail_html(item, filename, date_str)
            detail_path = os.path.join(detail_dir, filename)
            with open(detail_path, 'w', encoding='utf-8') as f:
                f.write(detail_html)

        print(f"✅ 生成 {len(items)} 个详情页")

    def generate_detail_html(self, item: Dict, current_filename: str, date_str: str) -> str:
        """生成单个详情页"""
        item_type = item['type']
        type_name = '论文' if item_type == 'paper' else '新闻'

        # 元信息
        if item_type == 'paper':
            authors_str = ', '.join(item['authors']) if item.get('authors') else '未知'
            meta_html = f"""
            <div class="meta-row"><span class="label">作者:</span> {authors_str}</div>
            <div class="meta-row"><span class="label">分类:</span> {item.get('category', 'AI')}</div>
            """
            actions_html = f"""
            <a href="{item.get('pdf_url', '')}" class="btn" target="_blank">📄 阅读PDF</a>
            <a href="{item.get('arxiv_url', '')}" class="btn btn-secondary" target="_blank">🔗 arXiv</a>
            """
        else:
            meta_html = f"""
            <div class="meta-row"><span class="label">来源:</span> {item.get('source', '未知')}</div>
            """
            actions_html = f"""
            <a href="{item.get('link', '')}" class="btn" target="_blank">🔗 阅读原文</a>
            """

        summary_en_html = f'<div class="summary-en"><h3>英文摘要</h3><p>{item.get("summary_en", "")}</p></div>' if item.get('summary_en') else ''

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{item.get('title_zh', item['title'])} - AI资讯日报</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        :root {{
            --orange: #ff6600;
            --text: #333;
            --text-light: #828282;
            --bg: #f6f6ef;
            --card: #ffffff;
            --border: #e6e6e6;
            --yellow: #ffc107;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
            min-height: 100vh;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 30px;
            color: var(--orange);
            text-decoration: none;
            font-weight: 500;
        }}
        .back-link:hover {{ text-decoration: underline; }}
        .detail-card {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .type-badge {{
            display: inline-block;
            padding: 4px 12px;
            background: var(--yellow);
            color: white;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 20px;
        }}
        .type-badge.news {{ background: #4CAF50; }}
        h1 {{
            font-size: 1.8rem;
            line-height: 1.4;
            margin-bottom: 25px;
            color: var(--text);
        }}
        .meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            padding: 20px 0;
            border-top: 1px solid var(--border);
            border-bottom: 1px solid var(--border);
            margin-bottom: 25px;
        }}
        .meta-row {{
            font-size: 0.95rem;
            color: var(--text-light);
        }}
        .label {{ font-weight: 600; color: var(--text); }}
        .summary {{
            font-size: 1.05rem;
            line-height: 1.8;
            margin-bottom: 30px;
            color: var(--text);
        }}
        .summary h: 10px3 {{ margin-bottom; }}
        .summary-en {{
            font-size: 0.9rem;
            color: var(--text-light);
            padding: 15px;
            background: var(--bg);
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .summary-en h3 {{ margin-bottom: 10px; }}
        .actions {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 20px;
            background: var(--orange);
            color: white !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s;
        }}
        .btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}
        .btn-secondary {{ background: var(--text-light); }}
        .original-title {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px dashed var(--border);
            font-size: 0.9rem;
            color: var(--text-light);
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="index.html" class="back-link">← 返回首页</a>

        <div class="detail-card">
            <span class="type-badge {item_type}">{type_name}</span>

            <h1>{item.get('title_zh', item['title'])}</h1>

            <div class="meta">
                <div class="meta-row"><span class="label">发布时间:</span> {item.get('published', '')}</div>
                {meta_html}
            </div>

            <div class="summary">
                <h3>中文摘要</h3>
                <p>{item.get('summary', '')}</p>
            </div>

            {summary_en_html}

            <div class="actions">
                {actions_html}
            </div>

            <div class="original-title">
                <strong>原文标题:</strong> {item.get('title', '')}
            </div>
        </div>
    </div>
</body>
</html>'''
        return html

    def update_archive_index(self, current_date: str):
        """更新历史归档索引页面"""
        print("📚 更新历史归档...")

        # 读取现有归档（如果存在）
        archive_file = 'archive/index.html'
        dates = []

        if os.path.exists(archive_file):
            try:
                with open(archive_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取已有日期
                    import re
                    dates = re.findall(r'href="(\d{4}/\d{2}/\d{2})/"', content)
            except:
                pass

        # 添加当前日期
        date_dir = current_date.replace('/', '/')
        if date_dir not in dates:
            dates.append(date_dir)

        # 按日期倒序排列
        dates.sort(reverse=True)

        # 生成归档页面
        date_links = []
        for d in dates:
            date_label = d.replace('/', '年').replace('/', '月') + '日'
            date_links.append(f'<li><a href="../{d}/index.html">{date_label}</a></li>')

        archive_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>历史归档 - AI资讯日报</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, sans-serif; background: #f6f6ef; min-height: 100vh; padding: 40px 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        h1 {{ text-align: center; margin-bottom: 30px; color: #333; }}
        ul {{ list-style: none; }}
        li {{ margin-bottom: 10px; }}
        a {{ display: block; padding: 15px 20px; background: white; color: #333; text-decoration: none; border-radius: 8px; transition: all 0.3s; }}
        a:hover {{ background: #ff6600; color: white; }}
        .back {{ display: inline-block; margin-bottom: 20px; color: #ff6600; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="../" class="back">← 返回最新</a>
        <h1>📚 历史归档</h1>
        <ul>
            {''.join(date_links)}
        </ul>
    </div>
</body>
</html>'''

        os.makedirs('archive', exist_ok=True)
        with open(archive_file, 'w', encoding='utf-8') as f:
            f.write(archive_html)

        print(f"✅ 历史归档已更新，共 {len(dates)} 天")

    def run(self):
        """主运行函数"""
        print("🚀 AI News Daily v4.0 (扩展版) 开始运行...")
        print(f"👤 GitHub用户: {self.github_user}")
        print(f"🌐 网站地址: {self.website_url}")

        # 获取当前日期
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        date_str = now.strftime('%Y/%m/%d')

        try:
            # 获取论文（arXiv 5篇 + HF 5篇 + SS 5篇 = 15篇）
            print("\n=== 开始采集论文 ===")
            arxiv_papers = self.get_arxiv_papers()
            hf_papers = self.get_huggingface_papers(count=5)
            ss_papers = self.get_semantic_scholar_papers(count=5)
            papers = arxiv_papers + hf_papers + ss_papers

            # 获取新闻（20条）
            print("\n=== 开始采集新闻 ===")
            news = self.get_tech_news(target_count=20)

            # 合并并排序
            items = self.merge_and_sort_items(papers, news)

            # 生成带日期的目录结构
            output_dir = os.path.join(date_str)
            os.makedirs(output_dir, exist_ok=True)

            # 生成首页
            html = self.generate_html(items, date_str)
            index_path = os.path.join(output_dir, 'index.html')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html)

            # 生成详情页
            self.generate_detail_pages(items, output_dir, date_str)

            # 更新根目录index.html（重定向到当天）
            root_html = self.generate_root_index(date_str)
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(root_html)

            # 更新历史索引
            self.update_archive_index(date_str)

            print("\n✅ 网站生成完成！")
            print(f"📁 文件保存: {date_str}/index.html")
            print(f"📊 内容统计: {len(papers)}篇论文 + {len(news)}条新闻 = {len(items)}条内容")

        except Exception as e:
            print(f"❌ 运行失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    app = AINewsDaily()
    app.run()
