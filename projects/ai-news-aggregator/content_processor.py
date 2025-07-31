"""
🧠 AI智能内容处理和格式化引擎
将原始新闻转换为适合不同平台的精美内容
"""

import asyncio
import aiohttp
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib
from enum import Enum
import os
from news_spider import NewsItem

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Platform(Enum):
    """发布平台枚举"""
    WECHAT = "wechat"
    XIAOHONGSHU = "xiaohongshu"
    WEIBO = "weibo"

@dataclass
class ProcessedContent:
    """处理后的内容"""
    original_news: NewsItem
    platform: Platform
    optimized_title: str
    formatted_content: str
    tags: List[str]
    hashtags: List[str]
    summary: str
    reading_time: int  # 预估阅读时间（秒）
    engagement_score: float  # 预估互动度
    thumbnail_prompt: str  # 配图提示词
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['platform'] = self.platform.value
        result['original_news'] = asdict(self.original_news)
        return result

class AIContentProcessor:
    """AI内容处理引擎"""
    
    def __init__(self, deepseek_api_key: str = None):
        self.api_key = deepseek_api_key or os.getenv("DEEPSEEK_API_KEY")
        self.api_base = "https://api.deepseek.com/v1"
        
        # 平台特色模板
        self.platform_templates = {
            Platform.WECHAT: {
                "title_style": "专业、权威、数据驱动",
                "content_style": "深度分析、结构化、引用来源",
                "max_title_length": 64,
                "emojis": ["📈", "🚀", "💡", "🔥", "⚡", "🎯", "📊"],
                "tone": "professional"
            },
            Platform.XIAOHONGSHU: {
                "title_style": "年轻化、话题性、emoji丰富",
                "content_style": "轻松活泼、互动性强、视觉化",
                "max_title_length": 50,
                "emojis": ["✨", "🤖", "💫", "🎉", "😍", "🔥", "💎", "🌟", "⚡", "🎯"],
                "tone": "casual"
            }
        }
        
        # 热词库
        self.hot_keywords = {
            "技术突破": ["突破", "革命性", "颠覆", "首次", "历史性", "里程碑"],
            "产品发布": ["发布", "推出", "上线", "亮相", "登场", "面世"],  
            "融资投资": ["融资", "投资", "估值", "IPO", "收购", "合并"],
            "行业分析": ["趋势", "预测", "分析", "洞察", "报告", "研究"],
            "技术公司": ["OpenAI", "Google", "百度", "腾讯", "阿里", "字节"],
            "AI模型": ["GPT", "Claude", "Gemini", "文心", "通义", "星火"]
        }

    async def call_deepseek_api(self, messages: List[Dict], model: str = "deepseek-chat") -> str:
        """调用DeepSeek API"""
        if not self.api_key:
            logger.warning("未设置DEEPSEEK_API_KEY，使用模拟响应")
            return self._mock_ai_response(messages)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        logger.error(f"DeepSeek API调用失败: {response.status}")
                        return self._mock_ai_response(messages)
        except Exception as e:
            logger.error(f"DeepSeek API调用异常: {e}")
            return self._mock_ai_response(messages)

    def _mock_ai_response(self, messages: List[Dict]) -> str:
        """模拟AI响应（用于测试）"""
        user_message = messages[-1]["content"] if messages else ""
        
        if "标题" in user_message:
            return """
1. 🚀 GPT-5即将发布！OpenAI内部消息首次曝光
2. 🔥 AI大模型新突破：性能提升300%震撼登场  
3. ⚡ 重磅！下一代AI助手将改变所有行业格局
            """.strip()
        elif "小红书" in user_message:
            return """
🤖✨ AI圈又有大动作啦！

今天刷到一个超级震撼的消息，GPT-5要来了！🔥🔥

据说性能比GPT-4提升了好几倍，简直不敢想象以后的AI会有多强大 😱

✨ 重点来了：
• 推理能力大幅提升
• 支持更多模态交互  
• 响应速度更快
• 创造力爆表 💫

姐妹们，你们觉得AI发展这么快，会不会很快就能帮我们做所有工作了？ 😂

#AI新闻 #GPT5 #人工智能 #科技前沿 #未来已来
            """.strip()
        elif "公众号" in user_message:
            return """
# GPT-5即将发布：AI发展新里程碑

## 📊 核心要点

• OpenAI内部消息确认，GPT-5开发进展顺利
• 预计性能相比GPT-4提升显著，多项指标创新高
• 发布时间窗口初步确定，业界高度关注

## 📰 详细解读

根据可靠消息源透露，OpenAI的下一代大语言模型GPT-5已进入最后测试阶段。相比于GPT-4，新模型在推理能力、创造性输出和多模态理解方面都有显著提升。

技术层面的突破主要体现在：模型参数优化、训练数据质量提升以及计算效率的大幅改进。

## 🔮 行业影响

GPT-5的发布将进一步推动人工智能在各行各业的应用深化，特别是在教育、医疗、金融等领域的智能化转型。

## 💡 总结

AI技术的快速迭代正在重塑我们的工作和生活方式，值得持续关注其发展动态。

---
*本文由AI智能新闻聚合平台自动生成*
            """.strip()
        else:
            return "AI处理完成，已生成优化内容。"

    async def optimize_title(self, news: NewsItem, platform: Platform) -> str:
        """优化标题"""
        template = self.platform_templates[platform]
        
        prompt = f"""
请基于以下AI新闻，为{platform.value}平台生成优化标题：

原标题：{news.title}
新闻内容：{news.content[:300]}
新闻来源：{news.source}

平台要求：
- 风格：{template['title_style']}
- 最大长度：{template['max_title_length']}字
- 适用emoji：{', '.join(template['emojis'])}
- 语调：{template['tone']}

请生成3个候选标题，按推荐度排序，格式：
1. [最推荐标题]
2. [次推荐标题] 
3. [备选标题]

要求标题要有吸引力、准确性和平台适应性。
        """
        
        messages = [
            {"role": "system", "content": "你是专业的新媒体标题优化专家，擅长为不同平台创作吸引人的标题。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.call_deepseek_api(messages)
        
        # 提取第一个标题
        lines = response.strip().split('\n')
        for line in lines:
            if line.strip().startswith('1.'):
                title = re.sub(r'^1\.?\s*', '', line.strip())
                return title[:template['max_title_length']]
        
        # 如果提取失败，返回原标题的优化版本
        return f"{template['emojis'][0]} {news.title[:template['max_title_length']-3]}"

    async def format_content(self, news: NewsItem, platform: Platform, optimized_title: str) -> str:
        """格式化内容"""
        if platform == Platform.WECHAT:
            return await self._format_wechat_content(news, optimized_title)
        elif platform == Platform.XIAOHONGSHU:
            return await self._format_xiaohongshu_content(news, optimized_title)
        else:
            return news.content

    async def _format_wechat_content(self, news: NewsItem, title: str) -> str:
        """格式化微信公众号内容"""
        prompt = f"""
请将以下AI新闻重写为专业的微信公众号文章：

标题：{title}
原始内容：{news.content}
来源：{news.source}
发布时间：{news.published_time.strftime('%Y-%m-%d %H:%M')}

要求：
1. 结构清晰，包含：核心要点、详细解读、行业影响、总结
2. 语言专业但易懂，适合商务读者
3. 适当使用数据和引用增强可信度
4. 长度控制在800-1200字
5. 使用markdown格式，包含合适的标题层级
6. 在文末注明信息来源

请确保内容准确、有价值、易于阅读。
        """
        
        messages = [
            {"role": "system", "content": "你是专业的商业媒体编辑，擅长将新闻信息改写为高质量的公众号文章。"},
            {"role": "user", "content": prompt}
        ]
        
        return await self.call_deepseek_api(messages)

    async def _format_xiaohongshu_content(self, news: NewsItem, title: str) -> str:
        """格式化小红书内容"""
        prompt = f"""
请将以下AI新闻重写为小红书风格的内容：

标题：{title}
原始内容：{news.content}
来源：{news.source}

要求：
1. 年轻化、口语化的表达方式
2. 大量使用emoji，增加视觉效果
3. 分段清晰，每段不超过2行
4. 包含互动元素（提问、征求意见等）
5. 长度300-500字
6. 结尾包含相关话题标签（#标签）
7. 制造话题性和讨论度

风格参考：像朋友分享消息一样自然亲切。
        """
        
        messages = [
            {"role": "system", "content": "你是年轻的小红书博主，擅长用轻松活泼的方式分享科技资讯。"},
            {"role": "user", "content": prompt}
        ]
        
        return await self.call_deepseek_api(messages)

    def extract_tags(self, news: NewsItem, content: str) -> List[str]:
        """提取标签"""
        tags = []
        
        # 基于内容提取关键词
        text = (news.title + " " + content).lower()
        
        # 技术标签
        tech_tags = {
            "gpt": "GPT", "claude": "Claude", "chatgpt": "ChatGPT",
            "openai": "OpenAI", "google": "Google", "百度": "百度",
            "大模型": "大模型", "llm": "LLM", "ai": "人工智能",
            "机器学习": "机器学习", "深度学习": "深度学习",
            "自然语言": "NLP", "计算机视觉": "计算机视觉",
            "自动驾驶": "自动驾驶", "机器人": "机器人"
        }
        
        for keyword, tag in tech_tags.items():
            if keyword in text and tag not in tags:
                tags.append(tag)
        
        # 事件类型标签
        if any(word in text for word in ["发布", "推出", "上线"]):
            tags.append("产品发布")
        if any(word in text for word in ["融资", "投资", "估值"]):
            tags.append("融资投资")
        if any(word in text for word in ["突破", "创新", "首次"]):
            tags.append("技术突破")
        
        return tags[:8]  # 最多8个标签

    def generate_hashtags(self, news: NewsItem, platform: Platform) -> List[str]:
        """生成话题标签"""
        hashtags = []
        
        if platform == Platform.XIAOHONGSHU:
            base_tags = ["AI新闻", "人工智能", "科技前沿", "未来科技"]
            
            # 基于标题内容添加特定标签
            title_lower = news.title.lower()
            if "gpt" in title_lower:
                hashtags.append("GPT")
            if "openai" in title_lower:
                hashtags.append("OpenAI")
            if any(word in title_lower for word in ["发布", "推出"]):
                hashtags.append("新品发布")
            if any(word in title_lower for word in ["突破", "创新"]):
                hashtags.append("科技突破")
                
            hashtags.extend(base_tags)
            
        elif platform == Platform.WECHAT:
            hashtags = ["AI资讯", "科技动态", "行业观察"]
        
        return list(set(hashtags))[:6]  # 去重，最多6个

    def calculate_engagement_score(self, news: NewsItem, processed_content: str) -> float:
        """计算预估互动度"""
        score = 0.0
        
        # 基础热度
        score += news.heat_score * 0.3
        
        # 内容质量因子
        if len(processed_content) > 500:
            score += 20
        elif len(processed_content) > 300:
            score += 10
            
        # 标题吸引力
        title_factors = ["发布", "突破", "首次", "重磅", "震撼", "曝光"]
        for factor in title_factors:
            if factor in news.title:
                score += 8
        
        # 时效性
        hours_ago = (datetime.now() - news.published_time).total_seconds() / 3600
        if hours_ago <= 2:
            score += 15
        elif hours_ago <= 6:
            score += 10
        elif hours_ago <= 12:
            score += 5
            
        return min(score, 100)

    def generate_thumbnail_prompt(self, news: NewsItem) -> str:
        """生成配图提示词"""
        # 基于标题和内容生成图片描述
        title_lower = news.title.lower()
        
        base_style = "professional, high-tech, modern, clean background"
        
        if any(word in title_lower for word in ["gpt", "chatgpt", "ai助手"]):
            return f"AI chatbot interface, digital brain, neural network, {base_style}"
        elif any(word in title_lower for word in ["机器人", "robot"]):
            return f"advanced humanoid robot, futuristic design, white background, {base_style}"
        elif any(word in title_lower for word in ["自动驾驶", "autonomous"]):
            return f"self-driving car with sensors, LiDAR visualization, {base_style}"
        elif any(word in title_lower for word in ["芯片", "chip", "处理器"]):
            return f"computer chip, circuit board, microprocessor, {base_style}"
        elif any(word in title_lower for word in ["数据", "data", "算法"]):
            return f"data visualization, flowing data streams, algorithms, {base_style}"
        else:
            return f"artificial intelligence concept, digital technology, {base_style}"

    async def process_news(self, news: NewsItem, platform: Platform) -> ProcessedContent:
        """处理单条新闻"""
        logger.info(f"🧠 处理新闻: {news.title[:50]}... -> {platform.value}")
        
        # 优化标题
        optimized_title = await self.optimize_title(news, platform)
        
        # 格式化内容
        formatted_content = await self.format_content(news, platform, optimized_title)
        
        # 提取标签
        tags = self.extract_tags(news, formatted_content)
        
        # 生成话题标签
        hashtags = self.generate_hashtags(news, platform)
        
        # 生成摘要
        summary = formatted_content[:150] + "..." if len(formatted_content) > 150 else formatted_content
        
        # 计算预估阅读时间（按每分钟200字计算）
        reading_time = max(30, len(formatted_content) // 200 * 60)
        
        # 计算互动度
        engagement_score = self.calculate_engagement_score(news, formatted_content)
        
        # 生成配图提示
        thumbnail_prompt = self.generate_thumbnail_prompt(news)
        
        processed = ProcessedContent(
            original_news=news,
            platform=platform,
            optimized_title=optimized_title,
            formatted_content=formatted_content,
            tags=tags,
            hashtags=hashtags,
            summary=summary,
            reading_time=reading_time,
            engagement_score=engagement_score,
            thumbnail_prompt=thumbnail_prompt
        )
        
        logger.info(f"✅ 处理完成: {optimized_title[:30]}...")
        return processed

    async def batch_process(self, news_list: List[NewsItem], platforms: List[Platform] = None) -> Dict[Platform, List[ProcessedContent]]:
        """批量处理新闻"""
        if platforms is None:
            platforms = [Platform.WECHAT, Platform.XIAOHONGSHU]
        
        results = {platform: [] for platform in platforms}
        
        # 创建所有任务
        tasks = []
        for news in news_list[:20]:  # 限制处理数量
            for platform in platforms:
                tasks.append(self.process_news(news, platform))
        
        logger.info(f"🚀 开始批量处理: {len(news_list)}条新闻 x {len(platforms)}个平台")
        
        # 并发执行
        processed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        task_index = 0
        for news in news_list[:20]:
            for platform in platforms:
                result = processed_results[task_index]
                if isinstance(result, ProcessedContent):
                    results[platform].append(result)
                else:
                    logger.error(f"处理失败: {result}")
                task_index += 1
        
        # 按互动度排序
        for platform in platforms:
            results[platform].sort(key=lambda x: x.engagement_score, reverse=True)
        
        logger.info(f"✅ 批量处理完成!")
        return results

    def save_processed_content(self, results: Dict[Platform, List[ProcessedContent]], filename: str = None):
        """保存处理结果"""
        if filename is None:
            filename = f"processed_content_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        # 转换为可序列化格式
        data = {
            "processed_time": datetime.now().isoformat(),
            "platforms": {}
        }
        
        for platform, content_list in results.items():
            data["platforms"][platform.value] = {
                "count": len(content_list),
                "content": [item.to_dict() for item in content_list]
            }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"📁 处理结果已保存到: {filename}")
        return filename

# 测试函数
async def test_content_processor():
    """测试内容处理器"""
    from news_spider import collect_realtime_news
    
    # 收集新闻
    news_items = await collect_realtime_news()
    
    # 处理内容
    processor = AIContentProcessor()
    results = await processor.batch_process(news_items[:5])  # 测试前5条
    
    # 保存结果
    processor.save_processed_content(results)
    
    # 展示结果
    print("\n🎨 内容处理结果预览:")
    print("=" * 80)
    
    for platform, content_list in results.items():
        print(f"\n📱 {platform.value.upper()} 平台格式:")
        print("-" * 60)
        
        for i, content in enumerate(content_list[:3], 1):
            print(f"{i}. 标题: {content.optimized_title}")
            print(f"   热度: {content.engagement_score:.1f}分 | 阅读: {content.reading_time}秒")
            print(f"   标签: {', '.join(content.tags)}")
            print(f"   话题: {', '.join(content.hashtags)}")
            print(f"   内容: {content.formatted_content[:100]}...")
            print()

if __name__ == "__main__":
    asyncio.run(test_content_processor())