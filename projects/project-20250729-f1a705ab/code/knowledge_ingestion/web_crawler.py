#!/usr/bin/env python3
"""
智能行业知识问答系统 - 网络爬虫和在线学习
支持从指定网站自动获取最新知识内容并更新知识库
"""

import os
import asyncio
import aiohttp
import requests
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging
import hashlib
import json
import re
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.robotparser import RobotFileParser

# 网页解析
from bs4 import BeautifulSoup

# Optional dependencies
try:
    import newspaper
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# 内容处理 - Optional dependencies
try:
    from langdetect import detect
    import jieba
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

# 本地模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from knowledge_ingestion.document_parser import ExtractedContent, DocumentParseResult, DocumentMetadata

@dataclass
class WebContent:
    """网页内容数据类"""
    url: str
    title: str
    content: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = None
    category: str = ""
    language: str = ""
    content_type: str = "article"  # article, news, blog, forum, etc.
    extracted_at: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.extracted_at:
            self.extracted_at = datetime.now().isoformat()

@dataclass
class CrawlTask:
    """爬取任务"""
    task_id: str
    urls: List[str]
    domain: str
    crawl_rules: Dict[str, Any]
    schedule: str = "daily"  # daily, weekly, monthly
    last_run: str = ""
    next_run: str = ""
    status: str = "pending"  # pending, running, completed, failed
    results_count: int = 0
    
    def __post_init__(self):
        if not self.last_run:
            self.last_run = datetime.now().isoformat()

@dataclass
class CrawlConfig:
    """爬取配置"""
    max_pages: int = 100
    delay_seconds: float = 1.0
    timeout_seconds: int = 30
    follow_links: bool = False
    max_depth: int = 2
    allowed_domains: List[str] = None
    content_selectors: Dict[str, str] = None
    exclude_patterns: List[str] = None
    user_agent: str = "Knowledge-QA-Bot/1.0"
    
    def __post_init__(self):
        if self.allowed_domains is None:
            self.allowed_domains = []
        if self.content_selectors is None:
            self.content_selectors = {}
        if self.exclude_patterns is None:
            self.exclude_patterns = []

class WebCrawler:
    """网络爬虫和在线学习管理器"""
    
    def __init__(self, 
                 config: CrawlConfig = None,
                 storage_path: str = "crawl_data"):
        """
        初始化网络爬虫
        
        Args:
            config: 爬取配置
            storage_path: 数据存储路径
        """
        self.config = config or CrawlConfig()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # 初始化newspaper - 如果可用
        if NEWSPAPER_AVAILABLE:
            self.newspaper_config = newspaper.Config()
            self.newspaper_config.browser_user_agent = self.config.user_agent
            self.newspaper_config.request_timeout = self.config.timeout_seconds
        else:
            self.newspaper_config = None
        
        # 爬取历史和缓存
        self.crawl_history: Dict[str, datetime] = {}
        self.visited_urls: Set[str] = set()
        
        # Selenium配置（用于动态网站） - 如果可用
        if SELENIUM_AVAILABLE:
            self.chrome_options = Options()
            self.chrome_options.add_argument("--headless")
            self.chrome_options.add_argument("--no-sandbox")
            self.chrome_options.add_argument("--disable-dev-shm-usage")
            self.chrome_options.add_argument(f"--user-agent={self.config.user_agent}")
        else:
            self.chrome_options = None
        
        # 加载已保存的爬取历史
        self._load_crawl_history()
        
    async def crawl_url(self, url: str, use_selenium: bool = False) -> Optional[WebContent]:
        """
        爬取单个URL
        
        Args:
            url: 目标URL
            use_selenium: 是否使用Selenium（用于动态网站）
            
        Returns:
            Optional[WebContent]: 提取的网页内容
        """
        try:
            # 检查robots.txt
            if not await self._check_robots_permission(url):
                self.logger.warning(f"Robots.txt禁止爬取: {url}")
                return None
                
            # 检查是否最近已爬取
            if self._is_recently_crawled(url):
                self.logger.info(f"最近已爬取，跳过: {url}")
                return None
                
            self.logger.info(f"开始爬取: {url}")
            
            if use_selenium:
                content = await self._crawl_with_selenium(url)
            else:
                content = await self._crawl_with_newspaper(url)
                
            if content:
                # 记录爬取历史
                self.crawl_history[url] = datetime.now()
                self.visited_urls.add(url)
                
                # 保存内容
                await self._save_web_content(content)
                
                self.logger.info(f"成功爬取: {url}")
                
            return content
            
        except Exception as e:
            self.logger.error(f"爬取失败: {url}, 错误: {e}")
            return None
            
    async def _crawl_with_newspaper(self, url: str) -> Optional[WebContent]:
        """使用newspaper3k爬取内容"""
        if not NEWSPAPER_AVAILABLE or not self.newspaper_config:
            return None
            
        try:
            article = Article(url, config=self.newspaper_config)
            article.download()
            article.parse()
            article.nlp()
            
            # 检查内容质量
            if len(article.text.strip()) < 100:
                self.logger.warning(f"内容太短，跳过: {url}")
                return None
                
            # 检测语言
            try:
                language = detect(article.text[:1000])
            except:
                language = "unknown"
                
            # 提取标签和分类
            tags = list(article.keywords) if article.keywords else []
            
            content = WebContent(
                url=url,
                title=article.title or "无标题",
                content=article.text,
                published_date=article.publish_date.isoformat() if article.publish_date else None,
                author=", ".join(article.authors) if article.authors else None,
                tags=tags,
                language=language,
                content_type="article"
            )
            
            return content
            
        except Exception as e:
            self.logger.error(f"Newspaper爬取失败: {url}, 错误: {e}")
            return None
            
    async def _crawl_with_selenium(self, url: str) -> Optional[WebContent]:
        """使用Selenium爬取动态内容"""
        driver = None
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)
            
            # 等待页面加载
            WebDriverWait(driver, self.config.timeout_seconds).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 提取标题
            try:
                title = driver.find_element(By.TAG_NAME, "title").get_attribute("text")
            except:
                title = "无标题"
                
            # 提取主要内容
            content_text = ""
            
            # 尝试使用配置的选择器
            if self.config.content_selectors:
                for selector_type, selector in self.config.content_selectors.items():
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            content_text += element.text + "\n"
                    except:
                        continue
                        
            # 如果没有找到内容，使用默认策略
            if not content_text.strip():
                content_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "article, .content, .post-content, .entry-content, main, .main")
                
                for element in content_elements:
                    content_text += element.text + "\n"
                    
            # 如果还是没有内容，获取body文本
            if not content_text.strip():
                body = driver.find_element(By.TAG_NAME, "body")
                content_text = body.text
                
            # 清理内容
            content_text = self._clean_web_content(content_text)
            
            if len(content_text.strip()) < 100:
                self.logger.warning(f"Selenium提取内容太短: {url}")
                return None
                
            # 检测语言
            try:
                language = detect(content_text[:1000])
            except:
                language = "unknown"
                
            content = WebContent(
                url=url,
                title=title,
                content=content_text,
                language=language,
                content_type="dynamic_page"
            )
            
            return content
            
        except Exception as e:
            self.logger.error(f"Selenium爬取失败: {url}, 错误: {e}")
            return None
            
        finally:
            if driver:
                driver.quit()
                
    async def crawl_multiple_urls(self, urls: List[str], 
                                 max_concurrent: int = 5) -> List[WebContent]:
        """
        批量爬取多个URL
        
        Args:
            urls: URL列表
            max_concurrent: 最大并发数
            
        Returns:
            List[WebContent]: 爬取结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def crawl_with_semaphore(url: str) -> Optional[WebContent]:
            async with semaphore:
                # 添加延迟避免对服务器造成压力
                await asyncio.sleep(self.config.delay_seconds)
                return await self.crawl_url(url)
                
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤有效结果
        valid_results = []
        for result in results:
            if isinstance(result, WebContent):
                valid_results.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"批量爬取异常: {result}")
                
        self.logger.info(f"批量爬取完成，成功: {len(valid_results)}/{len(urls)}")
        return valid_results
        
    async def discover_urls(self, base_url: str, 
                          max_depth: int = 2) -> List[str]:
        """
        从基础URL发现相关链接
        
        Args:
            base_url: 基础URL
            max_depth: 最大搜索深度
            
        Returns:
            List[str]: 发现的URL列表
        """
        discovered_urls = set()
        to_visit = [(base_url, 0)]  # (url, depth)
        visited = set()
        
        while to_visit and len(discovered_urls) < self.config.max_pages:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited or depth > max_depth:
                continue
                
            visited.add(current_url)
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(current_url, 
                                         timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # 提取所有链接
                            for link in soup.find_all('a', href=True):
                                href = link['href']
                                absolute_url = urljoin(current_url, href)
                                
                                # 检查是否符合条件
                                if self._should_follow_link(absolute_url, base_url):
                                    discovered_urls.add(absolute_url)
                                    
                                    if depth < max_depth:
                                        to_visit.append((absolute_url, depth + 1))
                                        
            except Exception as e:
                self.logger.error(f"URL发现失败: {current_url}, 错误: {e}")
                
            # 添加延迟
            await asyncio.sleep(self.config.delay_seconds)
            
        return list(discovered_urls)
        
    async def create_crawl_task(self, 
                              domain: str,
                              seed_urls: List[str],
                              schedule: str = "daily") -> CrawlTask:
        """
        创建爬取任务
        
        Args:
            domain: 领域名称
            seed_urls: 种子URL列表
            schedule: 调度频率
            
        Returns:
            CrawlTask: 爬取任务
        """
        task_id = hashlib.md5(f"{domain}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        # 扩展URL列表
        if self.config.follow_links:
            all_urls = set(seed_urls)
            for seed_url in seed_urls:
                discovered = await self.discover_urls(seed_url, self.config.max_depth)
                all_urls.update(discovered)
            final_urls = list(all_urls)
        else:
            final_urls = seed_urls
            
        task = CrawlTask(
            task_id=task_id,
            urls=final_urls,
            domain=domain,
            crawl_rules=asdict(self.config),
            schedule=schedule
        )
        
        # 保存任务
        await self._save_crawl_task(task)
        
        self.logger.info(f"创建爬取任务: {task_id}, 域名: {domain}, URL数: {len(final_urls)}")
        return task
        
    async def execute_crawl_task(self, task: CrawlTask) -> List[WebContent]:
        """
        执行爬取任务
        
        Args:
            task: 爬取任务
            
        Returns:
            List[WebContent]: 爬取结果
        """
        try:
            task.status = "running"
            task.last_run = datetime.now().isoformat()
            
            self.logger.info(f"开始执行爬取任务: {task.task_id}")
            
            # 执行爬取
            results = await self.crawl_multiple_urls(task.urls)
            
            # 过滤和处理结果
            processed_results = []
            for content in results:
                if content and self._is_relevant_content(content, task.domain):
                    # 添加领域标签
                    content.tags.append(task.domain)
                    content.category = task.domain
                    processed_results.append(content)
                    
            task.results_count = len(processed_results)
            task.status = "completed"
            
            # 计算下次运行时间
            task.next_run = self._calculate_next_run(task.schedule).isoformat()
            
            # 更新任务状态
            await self._save_crawl_task(task)
            
            self.logger.info(f"爬取任务完成: {task.task_id}, 结果数: {len(processed_results)}")
            return processed_results
            
        except Exception as e:
            task.status = "failed"
            await self._save_crawl_task(task)
            self.logger.error(f"爬取任务失败: {task.task_id}, 错误: {e}")
            return []
            
    async def convert_to_document_results(self, 
                                        web_contents: List[WebContent]) -> List[DocumentParseResult]:
        """
        将网页内容转换为文档解析结果
        
        Args:
            web_contents: 网页内容列表
            
        Returns:
            List[DocumentParseResult]: 文档解析结果列表
        """
        results = []
        
        for content in web_contents:
            try:
                # 创建文档元数据
                metadata = DocumentMetadata(
                    file_path=content.url,
                    file_name=self._url_to_filename(content.url),
                    file_type=".html",
                    file_size=len(content.content.encode('utf-8')),
                    created_at=content.extracted_at,
                    modified_at=content.published_date or content.extracted_at,
                    title=content.title,
                    author=content.author or "",
                    language=content.language
                )
                
                # 创建提取内容
                extracted_content = ExtractedContent(
                    content_id=hashlib.md5(content.url.encode()).hexdigest(),
                    content_type="web_article",
                    content=content.content,
                    confidence=0.8,
                    metadata={
                        "url": content.url,
                        "published_date": content.published_date,
                        "content_type": content.content_type,
                        "extraction_method": "web_crawl"
                    }
                )
                
                # 生成文档ID
                document_id = hashlib.md5(content.url.encode()).hexdigest()
                
                # 创建解析结果
                parse_result = DocumentParseResult(
                    document_id=document_id,
                    metadata=metadata,
                    extracted_contents=[extracted_content],
                    summary=self._generate_summary(content.content),
                    keywords=content.tags,
                    topics=[content.category] if content.category else []
                )
                
                results.append(parse_result)
                
            except Exception as e:
                self.logger.error(f"转换网页内容失败: {content.url}, 错误: {e}")
                
        return results
        
    def _should_follow_link(self, url: str, base_url: str) -> bool:
        """检查是否应该跟踪链接"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # 检查域名限制
            if self.config.allowed_domains and parsed_url.netloc not in self.config.allowed_domains:
                if parsed_url.netloc != parsed_base.netloc:
                    return False
                    
            # 检查排除模式
            for pattern in self.config.exclude_patterns:
                if re.search(pattern, url):
                    return False
                    
            # 排除常见的非内容链接
            excluded_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.rar'}
            if any(url.lower().endswith(ext) for ext in excluded_extensions):
                return False
                
            return True
            
        except Exception:
            return False
            
    def _is_relevant_content(self, content: WebContent, domain: str) -> bool:
        """检查内容是否与领域相关"""
        # 简单的相关性检查，可以用更复杂的算法替换
        domain_keywords = domain.lower().split()
        content_lower = (content.title + " " + content.content).lower()
        
        # 检查是否包含领域关键词
        matches = sum(1 for keyword in domain_keywords if keyword in content_lower)
        return matches > 0
        
    def _clean_web_content(self, content: str) -> str:
        """清理网页内容"""
        # 去除多余空白
        content = re.sub(r'\s+', ' ', content)
        
        # 去除常见的网页噪音
        noise_patterns = [
            r'Cookie',
            r'广告',
            r'Advertisement',
            r'点击.*查看',
            r'更多.*内容'
        ]
        
        for pattern in noise_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            
        return content.strip()
        
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成内容摘要"""
        if len(content) <= max_length:
            return content
            
        # 取前几句话作为摘要
        sentences = re.split(r'[。！？\n]', content)
        summary = ""
        
        for sentence in sentences:
            if len(summary + sentence) <= max_length:
                summary += sentence.strip() + "。"
            else:
                break
                
        return summary if summary else content[:max_length]
        
    def _url_to_filename(self, url: str) -> str:
        """将URL转换为文件名"""
        parsed = urlparse(url)
        filename = parsed.path.replace('/', '_').replace('\\', '_')
        if not filename or filename == '_':
            filename = parsed.netloc.replace('.', '_')
        return f"{filename}.html"
        
    def _is_recently_crawled(self, url: str, hours: int = 24) -> bool:
        """检查URL是否最近已被爬取"""
        if url not in self.crawl_history:
            return False
            
        last_crawled = self.crawl_history[url]
        time_diff = datetime.now() - last_crawled
        return time_diff.total_seconds() < hours * 3600
        
    def _calculate_next_run(self, schedule: str) -> datetime:
        """计算下次运行时间"""
        now = datetime.now()
        
        if schedule == "daily":
            return now + timedelta(days=1)
        elif schedule == "weekly":
            return now + timedelta(weeks=1)
        elif schedule == "monthly":
            return now + timedelta(days=30)
        else:
            return now + timedelta(days=1)
            
    async def _check_robots_permission(self, url: str) -> bool:
        """检查robots.txt权限"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch(self.config.user_agent, url)
            
        except Exception:
            # 如果无法获取robots.txt，默认允许
            return True
            
    async def _save_web_content(self, content: WebContent):
        """保存网页内容"""
        try:
            content_file = self.storage_path / "web_contents" / f"{hashlib.md5(content.url.encode()).hexdigest()}.json"
            content_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(content), f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"保存网页内容失败: {e}")
            
    async def _save_crawl_task(self, task: CrawlTask):
        """保存爬取任务"""
        try:
            task_file = self.storage_path / "tasks" / f"{task.task_id}.json"
            task_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(task), f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"保存爬取任务失败: {e}")
            
    def _load_crawl_history(self):
        """加载爬取历史"""
        try:
            history_file = self.storage_path / "crawl_history.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    
                for url, timestamp_str in history_data.items():
                    self.crawl_history[url] = datetime.fromisoformat(timestamp_str)
                    
        except Exception as e:
            self.logger.error(f"加载爬取历史失败: {e}")
            
    async def save_crawl_history(self):
        """保存爬取历史"""
        try:
            history_file = self.storage_path / "crawl_history.json"
            history_data = {
                url: timestamp.isoformat() 
                for url, timestamp in self.crawl_history.items()
            }
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存爬取历史失败: {e}")

# 使用示例
async def main():
    """测试网络爬虫"""
    config = CrawlConfig(
        max_pages=10,
        delay_seconds=1.0,
        follow_links=True,
        max_depth=1
    )
    
    crawler = WebCrawler(config)
    
    # 测试单个URL爬取
    test_url = "https://example.com"  # 替换为实际URL
    content = await crawler.crawl_url(test_url)
    
    if content:
        print(f"标题: {content.title}")
        print(f"内容长度: {len(content.content)} 字符")
        print(f"语言: {content.language}")
        print(f"标签: {content.tags}")
        
        # 转换为文档解析结果
        doc_results = await crawler.convert_to_document_results([content])
        print(f"转换后的文档数: {len(doc_results)}")

if __name__ == "__main__":
    asyncio.run(main())