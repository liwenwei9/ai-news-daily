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

                # 翻译摘要（只翻译前500字符以节省成本）
                summary_zh = self.translate_to_chinese(result.summary[:500])

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

    def get_tech_news(self) -> List[Dict[str, Any]]:
        """获取科技新闻"""
        print("📰 获取科技新闻...")

        news_items = []
        try:
            feed = feedparser.parse('https://www.technologyreview.com/feed/')

            count = 0
            for entry in feed.entries:
                if count >= 5:
                    break

                text = f"{entry.title} {entry.get('summary', '')}"
                if any(keyword in text.lower() for keyword in ['ai', 'artificial intelligence', 'machine learning']):
                    # 使用DeepSeek翻译标题
                    title_zh = self.translate_to_chinese(entry.title, is_title=True)

                    # 翻译摘要
                    summary_text = entry.get('summary', '')
                    summary_zh = self.translate_to_chinese(summary_text[:500]) if summary_text else title_zh

                    summary_quote = self.generate_one_sentence_summary(title_zh, max_length=80)

                    published_time = datetime.datetime.now()
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        try:
                            published_time = datetime.datetime(*entry.published_parsed[:6])
                        except:
                            pass

                    news = {
                        'type': 'news',
                        'title': entry.title,
                        'title_zh': title_zh,
                        'summary_quote': summary_quote,
                        'source': 'MIT Technology Review',
                        'link': entry.link,
                        'summary': summary_zh,
                        'summary_en': summary_text,
                        'published': entry.get('published', datetime.datetime.now().strftime('%Y-%m-%d')),
                        'published_time': published_time,
                        'score': random.randint(100, 800)
                    }
                    news_items.append(news)
                    count += 1

            print(f"✅ 获取到 {len(news_items)} 条新闻")

        except Exception as e:
            print(f"⚠️ 获取新闻失败: {e}")
            import traceback
            traceback.print_exc()

        return news_items

        def merge_and_sort_items(self, papers, news):
        """合并论文和新闻，并按时间排序"""
        import pytz
        from datetime import datetime

        # 统一时区为UTC（或北京时间），消除offset-naive/aware差异
        utc = pytz.UTC
        beijing_tz = pytz.timezone('Asia/Shanghai')

        items = []
        
        # 处理论文时间（确保带时区）
        for paper in papers:
            # 将论文的published时间转为带时区的datetime
            if paper.get('published'):
                # 如果是字符串，先解析；如果是datetime，确保带时区
                if isinstance(paper['published'], str):
                    pub_dt = datetime.fromisoformat(paper['published'].replace('Z', '+00:00'))
                else:
                    pub_dt = paper['published']
                
                # 确保时间带时区（如果没有，强制设为UTC）
                if pub_dt.tzinfo is None or pub_dt.tzinfo.utcoffset(pub_dt) is None:
                    pub_dt = utc.localize(pub_dt)
                
                paper['published'] = pub_dt
            items.append(paper)
        
        # 处理新闻时间（确保带时区）
        for item in news:
            if item.get('published'):
                if isinstance(item['published'], str):
                    pub_dt = datetime.fromisoformat(item['published'].replace('Z', '+00:00'))
                else:
                    pub_dt = item['published']
                
                if pub_dt.tzinfo is None or pub_dt.tzinfo.utcoffset(pub_dt) is None:
                    pub_dt = utc.localize(pub_dt)
                
                item['published'] = pub_dt
            items.append(item)
        
        # 按发布时间降序排序（最新的在前）
        items.sort(key=lambda x: x.get('published', datetime.min.replace(tzinfo=utc)), reverse=True)
        
        return items
		
    def generate_html(self, items: List[Dict]) -> str:
        """生成HTML页面"""
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
    <meta name="description" content="每日AI论文和新闻，全中文阅读 - DeepSeek翻译">
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
        <div class="subtitle">每日精选AI论文和科技新闻 · DeepSeek翻译</div>

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
        <p style="margin-top: 20px; font-size: 0.85rem;">灵感来源：<a href="https://zeli.app" target="_blank">Zeli</a></p>
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

    def _generate_items_html(self, items: List[Dict]) -> str:
        """生成条目HTML"""
        if not items:
            return '<p style="text-align: center; color: var(--text-light);">暂无数据</p>'

        html_parts = []
        for item in items:
            item_type = item['type']
            type_name = '论文' if item_type == 'paper' else '新闻'
            type_class = 'paper' if item_type == 'paper' else 'news'

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
                    <a href="{item['pdf_url']}" class="btn" target="_blank">📄 PDF</a>
                    <a href="{item['arxiv_url']}" class="btn btn-secondary" target="_blank">🔗 arXiv</a>
                '''
            else:
                actions_html = f'''
                    <a href="{item['link']}" class="btn" target="_blank">🔗 阅读原文</a>
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
                            <h3 class="item-title">{item.get('title_zh', item['title'])}</h3>
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

    def run(self):
        """主运行函数"""
        print("🚀 AI News Daily v3.0 (DeepSeek版) 开始运行...")
        print(f"👤 GitHub用户: {self.github_user}")
        print(f"🌐 网站地址: {self.website_url}")

        try:
            papers = self.get_arxiv_papers()
            news = self.get_tech_news()
            items = self.merge_and_sort_items(papers, news)
            html = self.generate_html(items)

            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(html)

            print("✅ 网站生成完成！")
            print(f"📁 文件保存: index.html")
            print(f"📊 内容统计: {len(papers)}篇论文 + {len(news)}条新闻 = {len(items)}条内容")
            print("💰 使用DeepSeek翻译，成本低廉，中文质量优秀")

        except Exception as e:
            print(f"❌ 运行失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    app = AINewsDaily()
    app.run()
