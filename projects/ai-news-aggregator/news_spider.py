"""
🤖 AI智能新闻聚合平台 - 新闻收集爬虫引擎
超越量子位、机器之心的全自动化新闻收集系统
"""

import asyncio
import aiohttp
import feedparser
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import hashlib
import re
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    """新闻条目数据结构"""
    title: str
    content: str
    url: str
    source: str
    published_time: datetime
    author: str = ""
    tags: List[str] = None
    heat_score: float = 0.0
    content_type: str = "article"  # article, paper, tool, product
    language: str = "zh"
    summary: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        # 生成唯一ID
        self.id = hashlib.md5(f"{self.url}{self.title}".encode()).hexdigest()[:16]

class NewsSpider:
    """高性能新闻爬虫引擎"""
    
    def __init__(self):
        self.session = None
        self.collected_urls = set()  # 防重复
        self.ai_keywords = [
            "人工智能", "AI", "GPT", "ChatGPT", "Claude", "大模型", "LLM",
            "机器学习", "深度学习", "神经网络", "自然语言处理", "NLP",
            "计算机视觉", "OpenAI", "Google AI", "百度AI", "腾讯AI",
            "自动驾驶", "机器人", "智能助手", "AIGC", "Stable Diffusion",
            "Midjourney", "文心一言", "通义千问", "星火", "混元"
        ]
        
        # 多语言数据源配置
        self.data_sources = {
            "chinese_media": [
                {
                    "name": "量子位",
                    "rss": "https://www.qbitai.com/feed",
                    "website": "https://www.qbitai.com",
                    "encoding": "utf-8",
                    "language": "zh"
                },
                {
                    "name": "机器之心", 
                    "rss": "https://www.jiqizhixin.com/rss",
                    "website": "https://www.jiqizhixin.com",
                    "encoding": "utf-8",
                    "language": "zh"
                },
                {
                    "name": "雷锋网AI",
                    "rss": "https://www.leiphone.com/category/ai/feed",
                    "website": "https://www.leiphone.com",
                    "encoding": "utf-8", 
                    "language": "zh"
                },
                {
                    "name": "36氪AI",
                    "rss": "https://36kr.com/motif/327686782977.rss",
                    "website": "https://36kr.com",
                    "encoding": "utf-8",
                    "language": "zh"
                },
                {
                    "name": "新智元",
                    "website": "https://www.ai-techreview.com",
                    "selectors": {
                        "article_list": ".article-item",
                        "title": ".title",
                        "url": "a",
                        "time": ".time"
                    },
                    "language": "zh"
                }
            ],
            "international_media": [
                {
                    "name": "TechCrunch AI",
                    "rss": "https://techcrunch.com/category/artificial-intelligence/feed/",
                    "website": "https://techcrunch.com",
                    "language": "en"
                },
                {
                    "name": "VentureBeat AI",
                    "rss": "https://venturebeat.com/ai/feed/",
                    "website": "https://venturebeat.com",
                    "language": "en"
                },
                {
                    "name": "The Verge AI",
                    "rss": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
                    "website": "https://www.theverge.com",
                    "language": "en"
                }
            ],
            "research_sources": [
                {
                    "name": "arXiv AI",
                    "rss": "https://rss.arxiv.org/rss/cs.AI",
                    "website": "https://arxiv.org",
                    "content_type": "paper",
                    "language": "en"
                },
                {
                    "name": "HuggingFace Blog",
                    "rss": "https://huggingface.co/blog/feed.xml",
                    "website": "https://huggingface.co",
                    "language": "en"
                },
                {
                    "name": "OpenAI Blog",
                    "rss": "https://openai.com/blog/rss.xml",
                    "website": "https://openai.com",
                    "language": "en"
                }
            ]
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; AI-News-Aggregator/1.0; +https://ai-news-aggregator.com/bot)'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    def is_ai_related(self, title: str, content: str = "") -> bool:
        """判断是否为AI相关内容"""
        text = (title + " " + content).lower()
        return any(keyword.lower() in text for keyword in self.ai_keywords)

    def calculate_heat_score(self, item: NewsItem) -> float:
        """计算新闻热度分数"""
        score = 0.0
        
        # 时间因子 (越新越热)
        hours_ago = (datetime.now() - item.published_time).total_seconds() / 3600
        if hours_ago <= 1:
            score += 50
        elif hours_ago <= 6:
            score += 30
        elif hours_ago <= 24:
            score += 20
        elif hours_ago <= 72:
            score += 10
        
        # 关键词热度
        hot_keywords = {
            "GPT-5": 30, "Claude-4": 25, "GPT-4": 20, "ChatGPT": 15,
            "OpenAI": 15, "谷歌": 10, "百度": 8, "腾讯": 8,
            "发布": 15, "突破": 20, "首次": 18, "超越": 22,
            "融资": 12, "收购": 15, "IPO": 20, "估值": 10
        }
        
        title_lower = item.title.lower()
        for keyword, points in hot_keywords.items():
            if keyword.lower() in title_lower:
                score += points
        
        # 内容长度和质量
        if len(item.content) > 1000:
            score += 10
        elif len(item.content) > 500:
            score += 5
            
        # 来源权威性
        source_weights = {
            "量子位": 20, "机器之心": 20, "OpenAI": 25, "Google": 20,
            "TechCrunch": 18, "The Verge": 15, "arXiv": 22
        }
        score += source_weights.get(item.source, 5)
        
        return min(score, 100)  # 最高100分

    async def fetch_rss_feed(self, source: Dict) -> List[NewsItem]:
        """获取RSS订阅源"""
        news_items = []
        
        try:
            async with self.session.get(source["rss"]) as response:
                if response.status != 200:
                    logger.warning(f"RSS获取失败: {source['name']} - {response.status}")
                    return news_items
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                logger.info(f"📡 获取RSS: {source['name']} - {len(feed.entries)}条")
                
                for entry in feed.entries[:20]:  # 限制每个源最多20条
                    try:
                        # 解析发布时间
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_time = datetime(*entry.published_parsed[:6])
                        else:
                            pub_time = datetime.now() - timedelta(hours=1)
                        
                        # 只处理24小时内的新闻
                        if (datetime.now() - pub_time).days > 1:
                            continue
                            
                        # 提取内容
                        content = ""
                        if hasattr(entry, 'summary'):
                            content = BeautifulSoup(entry.summary, 'html.parser').get_text()
                        elif hasattr(entry, 'content'):
                            content = BeautifulSoup(entry.content[0].value, 'html.parser').get_text()
                        
                        # 检查是否AI相关
                        if not self.is_ai_related(entry.title, content):
                            continue
                        
                        # 防重复
                        if entry.link in self.collected_urls:
                            continue
                        self.collected_urls.add(entry.link)
                        
                        news_item = NewsItem(
                            title=entry.title.strip(),
                            content=content[:2000],  # 限制长度
                            url=entry.link,
                            source=source["name"],
                            published_time=pub_time,
                            author=getattr(entry, 'author', ''),
                            language=source.get("language", "zh"),
                            content_type=source.get("content_type", "article")
                        )
                        
                        # 计算热度
                        news_item.heat_score = self.calculate_heat_score(news_item)
                        
                        news_items.append(news_item)
                        
                    except Exception as e:
                        logger.error(f"处理RSS条目失败: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"获取RSS失败 {source['name']}: {e}")
        
        return news_items

    async def scrape_website(self, source: Dict) -> List[NewsItem]:
        """爬取网站内容"""
        news_items = []
        
        try:
            async with self.session.get(source["website"]) as response:
                if response.status != 200:
                    return news_items
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 这里需要根据不同网站的结构来解析
                # 简化版本，实际需要为每个网站定制选择器
                articles = soup.find_all(['article', 'div'], class_=re.compile(r'(article|post|news|item)', re.I))
                
                for article in articles[:10]:  # 限制数量
                    try:
                        title_elem = article.find(['h1', 'h2', 'h3', 'h4', 'a'])
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        if not title or not self.is_ai_related(title):
                            continue
                            
                        url = title_elem.get('href') or article.find('a')['href']
                        if url and not url.startswith('http'):
                            url = urljoin(source["website"], url)
                        
                        if url in self.collected_urls:
                            continue
                        self.collected_urls.add(url)
                        
                        # 获取内容摘要
                        content_elem = article.find(['p', 'div'])
                        content = content_elem.get_text()[:500] if content_elem else ""
                        
                        news_item = NewsItem(
                            title=title,
                            content=content,
                            url=url,
                            source=source["name"],
                            published_time=datetime.now() - timedelta(minutes=30),
                            language=source.get("language", "zh")
                        )
                        
                        news_item.heat_score = self.calculate_heat_score(news_item)
                        news_items.append(news_item)
                        
                    except Exception as e:
                        logger.error(f"处理网站条目失败: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"爬取网站失败 {source['name']}: {e}")
        
        return news_items

    async def collect_all_news(self) -> List[NewsItem]:
        """收集所有新闻源"""
        all_news = []
        tasks = []
        
        # 收集所有RSS任务
        for category, sources in self.data_sources.items():
            for source in sources:
                if "rss" in source:
                    tasks.append(self.fetch_rss_feed(source))
                else:
                    tasks.append(self.scrape_website(source))
        
        logger.info(f"🚀 开始收集新闻，总共{len(tasks)}个数据源...")
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 汇总结果
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"任务执行失败: {result}")
            elif isinstance(result, list):
                all_news.extend(result)
        
        # 去重和排序
        seen_titles = set()
        unique_news = []
        
        for news in all_news:
            title_key = news.title.lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        # 按热度排序
        unique_news.sort(key=lambda x: x.heat_score, reverse=True)
        
        logger.info(f"✅ 收集完成！共获得{len(unique_news)}条AI相关新闻")
        
        return unique_news[:50]  # 返回热度最高的50条

    def save_to_json(self, news_items: List[NewsItem], filename: str = None):
        """保存到JSON文件"""
        if filename is None:
            filename = f"ai_news_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        data = {
            "collected_time": datetime.now().isoformat(),
            "total_count": len(news_items),
            "news_items": [asdict(item) for item in news_items]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"📁 新闻数据已保存到: {filename}")
        return filename

# 实时新闻收集任务
async def collect_realtime_news():
    """实时新闻收集主函数"""
    async with NewsSpider() as spider:
        news_items = await spider.collect_all_news()
        
        # 保存数据
        filename = spider.save_to_json(news_items)
        
        # 打印热门新闻
        print("\n🔥 今日AI热门新闻 Top 10:")
        print("=" * 80)
        
        for i, news in enumerate(news_items[:10], 1):
            print(f"{i:2d}. [{news.heat_score:4.1f}分] {news.title}")
            print(f"    📍 {news.source} | ⏰ {news.published_time.strftime('%H:%M')} | 🌐 {news.language}")
            print(f"    📝 {news.content[:100]}...")
            print("-" * 80)
        
        return news_items

if __name__ == "__main__":
    # 测试运行
    asyncio.run(collect_realtime_news())