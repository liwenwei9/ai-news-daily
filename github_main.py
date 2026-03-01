#!/usr/bin/env python3

"""

AI News Daily - liwenwei9 专属版本

"""



import os

import json

import datetime

import pytz

from typing import List, Dict, Any

import arxiv

import feedparser



class AINewsDaily:

    def __init__(self):

        self.github_user = "liwenwei9"

        self.repo_name = "ai-news-daily"

        self.website_url = f"https://{self.github_user}.github.io/{self.repo_name}/"

        

        # 创建输出目录

        os.makedirs('docs', exist_ok=True)

    

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

                paper = {

                    'id': result.entry_id.split('/')[-1],

                    'title': result.title,

                    'authors': [author.name for author in result.authors[:3]],

                    'summary': result.summary[:200] + '...',

                    'published': result.published.strftime('%Y-%m-%d'),

                    'pdf_url': result.pdf_url,

                    'arxiv_url': f"https://arxiv.org/abs/{result.entry_id.split('/')[-1]}",

                    'category': result.primary_category

                }

                papers.append(paper)

            

            print(f"✅ 获取到 {len(papers)} 篇论文")

            

        except Exception as e:

            print(f"⚠️ 获取论文失败: {e}")

            # 返回示例数据

            papers = [{

                'id': '2401.12345',

                'title': 'Large Language Models: A Survey',

                'authors': ['AI Researcher'],

                'summary': '大语言模型的最新研究进展和未来方向...',

                'published': datetime.datetime.now().strftime('%Y-%m-%d'),

                'pdf_url': 'https://arxiv.org/pdf/2401.12345.pdf',

                'arxiv_url': 'https://arxiv.org/abs/2401.12345',

                'category': 'cs.AI'

            }]

        

        return papers

    

    def get_tech_news(self) -> List[Dict[str, Any]]:

        """获取科技新闻"""

        print("📰 获取科技新闻...")

        

        news_items = []

        try:

            # 使用MIT Technology Review的RSS

            feed = feedparser.parse('https://www.technologyreview.com/feed/')

            

            for entry in feed.entries[:5]:

                # 过滤AI相关新闻

                text = f"{entry.title} {entry.get('summary', '')}"

                if any(keyword in text.lower() for keyword in ['ai', 'artificial intelligence', 'machine learning']):

                    news = {

                        'title': entry.title,

                        'source': 'MIT Technology Review',

                        'link': entry.link,

                        'summary': entry.get('summary', '')[:150] + '...',

                        'published': entry.get('published', datetime.datetime.now().strftime('%Y-%m-%d')),

                        'content': entry.get('content', [{}])[0].get('value', '')[:100] + '...' if entry.get('content') else ''

                    }

                    news_items.append(news)

            

            print(f"✅ 获取到 {len(news_items)} 条新闻")

            

        except Exception as e:

            print(f"⚠️ 获取新闻失败: {e}")

            # 返回示例数据

            news_items = [{

                'title': 'AI Breakthrough Announced',

                'source': 'Tech News',

                'link': 'https://example.com',

                'summary': '人工智能领域取得重大突破...',

                'published': datetime.datetime.now().strftime('%Y-%m-%d'),

                'content': '详细内容...'

            }]

        

        return news_items

    def generate_html(self, papers: List[Dict], news: List[Dict]) -> str:

        """生成HTML页面"""

        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))

        date_str = now.strftime('%Y年%m月%d日')

        time_str = now.strftime('%H:%M:%S')

        

        # 构建HTML

        html = f'''<!DOCTYPE html>

<html lang="zh-CN">

<head>

    <meta charset="UTF-8">

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>AI News Daily - liwenwei9</title>

    <meta name="description" content="每日AI资讯聚合网站 - liwenwei9的专属版本">

    <style>

        :root {{

            --primary: #667eea;

            --secondary: #764ba2;

            --bg: #f5f7fa;

            --card: #ffffff;

            --text: #333;

        }}

        

        * {{

            margin: 0;

            padding: 0;

            box-sizing: border-box;

        }}

        

        body {{

            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

            line-height: 1.6;

            color: var(--text);

            background: var(--bg);

            min-height: 100vh;

        }}

        

        .container {{

            max-width: 1000px;

            margin: 0 auto;

            padding: 20px;

        }}

        

        header {{

            text-align: center;

            padding: 30px;

            background: linear-gradient(135deg, var(--primary), var(--secondary));

            color: white;

            border-radius: 10px;

            margin-bottom: 30px;

        }}

        

        h1 {{

            font-size: 2.5rem;

            margin-bottom: 10px;

        }}

        

        .subtitle {{

            font-size: 1.1rem;

            opacity: 0.9;

            margin-bottom: 15px;

        }}

        

        .date {{

            background: rgba(255,255,255,0.2);

            padding: 8px 16px;

            border-radius: 20px;

            display: inline-block;

        }}

        

        .stats {{

            display: flex;

            justify-content: center;

            gap: 20px;

            margin: 20px 0;

            flex-wrap: wrap;

        }}

        

        .stat-card {{

            background: rgba(255,255,255,0.9);

            padding: 15px 25px;

            border-radius: 10px;

            text-align: center;

            min-width: 120px;

        }}

        

        .stat-number {{

            font-size: 1.8rem;

            font-weight: bold;

            color: var(--primary);

        }}

        

        .content {{

            background: var(--card);

            border-radius: 15px;

            padding: 30px;

            box-shadow: 0 5px 15px rgba(0,0,0,0.08);

        }}

        

        .section {{

            margin-bottom: 30px;

        }}

        

        .section-title {{

            font-size: 1.5rem;

            color: var(--text);

            margin-bottom: 20px;

            padding-bottom: 10px;

            border-bottom: 2px solid var(--primary);

        }}

        

        .item-card {{

            background: #f8f9fa;

            border-radius: 10px;

            padding: 20px;

            margin-bottom: 15px;

            border-left: 3px solid var(--primary);

        }}

        

        .item-title {{

            font-size: 1.2rem;

            color: #2d3748;

            margin-bottom: 10px;

        }}

        

        .item-meta {{

            display: flex;

            flex-wrap: wrap;

            gap: 15px;

            margin-bottom: 10px;

            font-size: 0.9rem;

            color: #666;

        }}

        

        .item-summary {{

            color: #4a5568;

            line-height: 1.6;

            margin-bottom: 15px;

            padding: 15px;

            background: white;

            border-radius: 8px;

        }}

        

        .btn {{

            display: inline-block;

            padding: 8px 16px;

            background: var(--primary);

            color: white;

            text-decoration: none;

            border-radius: 6px;

            margin-right: 10px;

            transition: background 0.3s;

        }}

        

        .btn:hover {{

            background: #5a67d8;

        }}

        

        footer {{

            text-align: center;

            padding: 30px;

            color: #666;

            margin-top: 30px;

        }}

        

        @media (max-width: 768px) {{

            .container {{ padding: 10px; }}

            h1 {{ font-size: 2rem; }}

            .content {{ padding: 20px; }}

        }}

    </style>

</head>

<body>

    <div class="container">

        <header>

            <h1>🤖 AI News Daily</h1>

            <div class="subtitle">liwenwei9的专属AI资讯站</div>

            <div class="date">📅 {date_str}</div>

            

            <div class="stats">

                <div class="stat-card">

                    <div class="stat-number">{len(papers)}</div>

                    <div>📚 今日论文</div>

                </div>

                <div class="stat-card">

                    <div class="stat-number">{len(news)}</div>

                    <div>📰 今日新闻</div>

                </div>

                <div class="stat-card">

                    <div class="stat-number">{len(papers) + len(news)}</div>

                    <div>✨ 总计内容</div>

                </div>

            </div>

        </header>

        

        <div class="content">

            <section class="section">

                <h2 class="section-title">📚 今日论文精选</h2>

                {self._generate_papers_html(papers)}

            </section>

            

            <section class="section">

                <h2 class="section-title">📰 今日新闻精选</h2>

                {self._generate_news_html(news)}

            </section>

        </div>

        

        <footer>

            <p>🤖 由AI自动生成 | 每日更新 | liwenwei9的专属版本</p>

            <p>📅 最后更新: {date_str} | ⏰ 生成时间: {time_str}</p>

            <p>🚀 <a href="https://github.com/liwenwei9/ai-news-daily" target="_blank" style="color: #667eea;">查看GitHub项目</a></p>

        </footer>

    </div>

    

    <script>

        // 更新时间显示

        function updateTime() {{

            const now = new Date();

            const timeStr = now.toLocaleTimeString('zh-CN');

            const dateStr = now.toLocaleDateString('zh-CN');

            const footer = document.querySelector('footer p:nth-child(2)');

            if (footer) {{

                footer.textContent = `📅 最后更新: ${{dateStr}} | ⏰ 当前时间: ${{timeStr}}`;

            }}

        }}

        

        updateTime();

        setInterval(updateTime, 1000);

    </script>

</body>

</html>'''

        

        return html

    def _generate_papers_html(self, papers: List[Dict]) -> str:

        """生成论文HTML"""

        if not papers:

            return '<p>暂无论文数据</p>'

        

        html_parts = []

        for paper in papers:

            html = f'''

            <div class="item-card">

                <h3 class="item-title">{paper['title']}</h3>

                <div class="item-meta">

                    <span>👨‍🎓 {', '.join(paper['authors'])}</span>

                    <span>🏷️ {paper['category']}</span>

                    <span>📅 {paper['published']}</span>

                </div>

                <div class="item-summary">

                    {paper['summary']}

                </div>

                <div>

                    <a href="{paper['pdf_url']}" class="btn" target="_blank">📄 下载PDF</a>

                    <a href="{paper['arxiv_url']}" class="btn" target="_blank">🔗 arXiv页面</a>

                </div>

            </div>

            '''

            html_parts.append(html)

        

        return '\n'.join(html_parts)

    

    def _generate_news_html(self, news: List[Dict]) -> str:

        """生成新闻HTML"""

        if not news:

            return '<p>暂无新闻数据</p>'

        

        html_parts = []

        for item in news:

            html = f'''

            <div class="item-card">

                <h3 class="item-title">{item['title']}</h3>

                <div class="item-meta">

                    <span>🏢 {item['source']}</span>

                    <span>📅 {item['published']}</span>

                </div>

                <div class="item-summary">

                    {item['summary']}

                </div>

                <div>

                    <a href="{item['link']}" class="btn" target="_blank">🔗 阅读原文</a>

                </div>

            </div>

            '''

            html_parts.append(html)

        

        return '\n'.join(html_parts)

    

    def run(self):

        """主运行函数"""

        print("🚀 AI News Daily 开始运行...")

        print(f"👤 GitHub用户: {self.github_user}")

        print(f"🌐 网站地址: {self.website_url}")

        

        try:

            # 获取数据

            papers = self.get_arxiv_papers()

            news = self.get_tech_news()

            

            # 生成HTML

            html = self.generate_html(papers, news)

            

            # 保存文件

            with open('docs/index.html', 'w', encoding='utf-8') as f:

                f.write(html)

            

            print("✅ 网站生成完成！")

            print(f"📁 文件保存: docs/index.html")

            print(f"🌐 访问地址: {self.website_url}")

            

        except Exception as e:

            print(f"❌ 运行失败: {e}")

            import traceback

            traceback.print_exc()



if __name__ == '__main__':

    app = AINewsDaily()

    app.run()

