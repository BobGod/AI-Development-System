"""
🔥 AI原创爆款文章生成器
基于热点分析和用户心理的原创文章生成，确保10万+阅读量
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import random
import re
from news_spider import NewsItem, collect_realtime_news
from content_processor import AIContentProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ViralPrediction:
    """爆款预测结果"""
    title: str
    content: str
    platform: str
    viral_score: float  # 爆款指数 0-100
    predicted_views: int  # 预测阅读量
    engagement_rate: float  # 预测互动率
    optimization_tips: List[str]  # 优化建议
    risk_factors: List[str]  # 风险提示
    best_publish_time: str  # 最佳发布时间
    target_audience: str  # 目标受众
    trending_keywords: List[str]  # 热门关键词

class ViralArticleGenerator:
    """爆款文章生成器"""
    
    def __init__(self, ai_processor: AIContentProcessor = None):
        self.ai_processor = ai_processor or AIContentProcessor()
        
        # 更自然的爆款文章模板库
        self.viral_templates = {
            "真实体验": {
                "title_patterns": [
                    "{topic}，我用了一周后想说的真心话",
                    "关于{topic}，说点不一样的",
                    "{topic}到底怎么样？我来告诉你真相",
                    "体验{topic}一个月，我发现了这些问题"
                ],
                "hooks": [
                    "先说结论：",
                    "坦白讲，",
                    "用了这么久，不得不说",
                    "可能很多人不同意，但我觉得"
                ],
                "viral_potential": 90
            },
            "实用干货": {
                "title_patterns": [
                    "{topic}避坑指南，看完能省很多钱",
                    "用{topic}三个月，总结了这些经验",
                    "关于{topic}，这些事没人告诉你",
                    "{topic}新手必看，老司机的建议"
                ],
                "hooks": [
                    "废话不多说，直接上干货",
                    "踩过坑才知道",
                    "分享一些实用经验",
                    "新手最容易犯的错误是"
                ],
                "viral_potential": 85
            },
            "观点讨论": {
                "title_patterns": [
                    "说个可能不受欢迎的观点：{topic}",
                    "关于{topic}，我有不同看法",
                    "{topic}真的有那么好吗？",
                    "为什么我不看好{topic}"
                ],
                "hooks": [
                    "可能会被喷，但还是想说",
                    "不同的声音也值得听听",
                    "换个角度看问题",
                    "理性讨论一下"
                ],
                "viral_potential": 95
            },
            "行业内幕": {
                "title_patterns": [
                    "在{topic}行业呆了5年，说点内幕",
                    "从业者视角：{topic}的真实现状",
                    "你不知道的{topic}行业真相",
                    "{topic}从业者不会告诉你的事"
                ],
                "hooks": [
                    "作为行业内的人",
                    "从专业角度来说",
                    "业内人都知道",
                    "有些话不得不说"
                ],
                "viral_potential": 88
            },
            "故事分享": {
                "title_patterns": [
                    "因为{topic}，我的生活发生了这些变化",
                    "{topic}改变了我什么",
                    "从抗拒到接受，我和{topic}的故事",
                    "{topic}让我想明白了一件事"
                ],
                "hooks": [
                    "分享一个真实的故事",
                    "说出来你可能不信",
                    "这件事改变了我的想法",
                    "回想起来还是很感慨"
                ],
                "viral_potential": 82
            }
        }
        
        # 更自然的关键词库
        self.viral_keywords = {
            "真实感词": ["真心话", "坦白讲", "实话实说", "不得不说", "说真的"],
            "经验词": ["踩过坑", "亲测", "用过才知道", "过来人", "老司机"],
            "对比词": ["比较", "差别", "不同", "优缺点", "选择"],
            "疑问词": ["真的吗", "到底", "怎么样", "值得吗", "有用吗"],
            "话题词": ["AI", "ChatGPT", "大模型", "人工智能", "机器人", "自动驾驶"],
            "情感词": ["感慨", "意外", "惊喜", "失望", "后悔", "庆幸"],
            "实用词": ["干货", "技巧", "方法", "经验", "建议", "指南"]
        }
        
        # 平台特性
        self.platform_features = {
            "wechat": {
                "title_length": 64,
                "content_length": (1500, 3000),
                "tone": "专业权威",
                "audience": "商务人群",
                "peak_hours": ["09:00", "12:00", "18:00", "21:00"],
                "engagement_multiplier": 1.2
            },
            "xiaohongshu": {
                "title_length": 50,
                "content_length": (800, 1500),
                "tone": "年轻活泼",
                "audience": "年轻女性",
                "peak_hours": ["11:00", "15:00", "20:00", "22:00"],
                "engagement_multiplier": 1.8
            },
            "weibo": {
                "title_length": 30,
                "content_length": (500, 1000),
                "tone": "简洁有力",
                "audience": "全年龄段",
                "peak_hours": ["12:00", "18:00", "21:00"],
                "engagement_multiplier": 1.5
            }
        }

    def analyze_trending_topics(self, news_items: List[NewsItem]) -> Dict[str, float]:
        """分析热门话题趋势"""
        topic_scores = {}
        
        # 提取话题关键词
        for news in news_items:
            text = (news.title + " " + news.content).lower()
            
            # 统计关键词频率
            for category, keywords in self.viral_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        topic_scores[keyword] = topic_scores.get(keyword, 0) + news.heat_score
        
        # 按热度排序
        sorted_topics = dict(sorted(topic_scores.items(), key=lambda x: x[1], reverse=True))
        return sorted_topics

    def calculate_viral_score(self, title: str, content: str, platform: str) -> float:
        """计算爆款指数"""
        score = 0.0
        
        # 标题分析 (40分)
        title_score = 0
        
        # 情绪激发词
        for word in self.viral_keywords["情绪词"]:
            if word in title:
                title_score += 5
        
        # 数字和数据
        for word in self.viral_keywords["数字词"]:
            if word in title:
                title_score += 4
        
        # 紧迫感
        for word in self.viral_keywords["紧迫词"]:
            if word in title:
                title_score += 6
        
        # 独家性
        for word in self.viral_keywords["独家词"]:
            if word in title:
                title_score += 7
        
        # emoji使用
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', title))
        title_score += min(emoji_count * 2, 8)
        
        score += min(title_score, 40)
        
        # 内容分析 (35分)
        content_score = 0
        
        # 长度适中
        content_len = len(content)
        platform_range = self.platform_features[platform]["content_length"]
        if platform_range[0] <= content_len <= platform_range[1]:
            content_score += 10
        elif content_len < platform_range[0]:
            content_score += 5  # 太短扣分
        
        # 段落结构
        paragraphs = content.split('\n')
        if 3 <= len(paragraphs) <= 8:
            content_score += 8
        
        # 互动元素
        if any(word in content for word in ["你觉得", "大家", "评论", "分享", "转发"]):
            content_score += 7
        
        # 故事性
        if any(word in content for word in ["我", "当时", "突然", "没想到", "结果"]):
            content_score += 10
        
        score += min(content_score, 35)
        
        # 时效性 (15分)
        current_hour = datetime.now().hour
        peak_hours = [int(h.split(':')[0]) for h in self.platform_features[platform]["peak_hours"]]
        if current_hour in peak_hours:
            score += 15
        elif abs(min(peak_hours, key=lambda x: abs(x - current_hour)) - current_hour) <= 1:
            score += 10
        else:
            score += 5
        
        # 话题热度 (10分)
        for keyword in self.viral_keywords["话题词"]:
            if keyword in title or keyword in content:
                score += 10
                break
        
        return min(score, 100)

    def predict_views(self, viral_score: float, platform: str, content_length: int) -> int:
        """预测阅读量"""
        base_views = {
            "wechat": 5000,
            "xiaohongshu": 8000, 
            "weibo": 12000
        }
        
        base = base_views[platform]
        multiplier = self.platform_features[platform]["engagement_multiplier"]
        
        # 爆款指数影响
        score_multiplier = (viral_score / 100) ** 2 * 10 + 1
        
        # 内容长度影响
        length_range = self.platform_features[platform]["content_length"]
        optimal_length = (length_range[0] + length_range[1]) / 2
        length_factor = 1 - abs(content_length - optimal_length) / optimal_length * 0.3
        length_factor = max(length_factor, 0.5)
        
        # 随机因素 (模拟算法推荐的不确定性)
        random_factor = random.uniform(0.7, 1.5)
        
        predicted_views = int(base * multiplier * score_multiplier * length_factor * random_factor)
        
        return max(predicted_views, 1000)  # 最少1000阅读

    def generate_optimization_tips(self, viral_score: float, title: str, content: str, platform: str) -> List[str]:
        """生成优化建议"""
        tips = []
        
        if viral_score < 60:
            tips.append("💡 标题缺乏吸引力，建议添加情绪激发词如'震撼'、'颠覆'等")
            
        if not re.search(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', title):
            tips.append("📱 标题建议添加1-2个相关emoji增加视觉吸引力")
            
        if not any(word in title for word in self.viral_keywords["紧迫词"]):
            tips.append("⏰ 建议在标题中添加紧迫感词汇如'刚刚'、'突发'、'即将'")
            
        content_len = len(content)
        platform_range = self.platform_features[platform]["content_length"]
        if content_len < platform_range[0]:
            tips.append(f"📝 内容过短({content_len}字)，建议扩展到{platform_range[0]}-{platform_range[1]}字")
        elif content_len > platform_range[1]:
            tips.append(f"✂️ 内容过长({content_len}字)，建议压缩到{platform_range[0]}-{platform_range[1]}字")
            
        if not any(word in content for word in ["你觉得", "大家", "评论区", "分享"]):
            tips.append("💬 建议在结尾添加互动引导语，提升评论和分享率")
            
        if platform == "xiaohongshu" and content.count('#') < 3:
            tips.append("🏷️ 小红书建议添加3-5个相关话题标签")
            
        if len(content.split('\n')) < 3:
            tips.append("📄 建议将内容分成3-5个段落，提升阅读体验")
            
        return tips

    async def generate_viral_article(self, topic: str, platform: str = "wechat", template_type: str = None) -> ViralPrediction:
        """生成爆款文章"""
        logger.info(f"🔥 生成爆款文章: {topic} -> {platform}")
        
        # 自动选择最佳模板
        if not template_type:
            # 基于话题选择最适合的模板
            if any(word in topic.lower() for word in ["体验", "使用", "测试", "试用"]):
                template_type = "真实体验"
            elif any(word in topic.lower() for word in ["指南", "教程", "方法", "技巧"]):
                template_type = "实用干货"
            elif any(word in topic.lower() for word in ["争议", "质疑", "反对", "不同看法"]):
                template_type = "观点讨论"
            elif any(word in topic.lower() for word in ["行业", "内幕", "从业", "专业"]):
                template_type = "行业内幕"
            else:
                template_type = "故事分享"
        
        template = self.viral_templates[template_type]
        
        # 生成爆款标题
        title_pattern = random.choice(template["title_patterns"])
        
        # 填充标题模板
        title_vars = {
            "topic": topic,
            "company": self._extract_company(topic),
            "impact": random.choice(["效果", "影响", "震撼", "颠覆"]),
            "action": random.choice(["发布", "更新", "升级", "突破"]),
            "result": random.choice(["全网沸腾", "行业震撼", "用户疯狂", "专家惊叹"]),
            "reaction": random.choice(["反响", "评论", "讨论", "热议"]),
            "revelation": random.choice(["真相大白", "内幕曝光", "秘密揭开", "答案揭晓"]),
            "angle": random.choice(["逻辑", "原理", "机制", "本质"]),
            "aspect": random.choice(["发展", "现状", "趋势", "未来"]),
            "reason": random.choice(["这么火", "备受关注", "引发热议", "成为焦点"]),
            "new_perspective": random.choice(["换个角度看问题", "不一样的思考", "全新的理解", "意想不到的发现"]),
            "claim": random.choice(["有用", "靠谱", "值得", "可信"]),
            "controversy": random.choice(["引发争议", "遭到质疑", "备受争议", "讨论激烈"]),
            "hidden_truth": random.choice(["真相", "内幕", "秘密", "隐情"]),
            "timeframe": random.choice(["一年", "两年", "三年", "五年"]),
            "prediction": random.choice(["大爆发", "大变革", "新突破", "新局面"]),
            "future_impact": random.choice(["巨大影响", "深远意义", "重大变化", "全新时代"]),
            "countdown": random.choice(["倒计时开始", "进入关键期", "迎来转折点", "面临大考"]),
            "consequence": random.choice(["变革", "机遇", "挑战", "转机"]),
            "transformation": random.choice(["改变世界", "重塑行业", "颠覆认知", "创造历史"]),
            "experience": random.choice(["亲密接触", "深度体验", "真实感受", "奇妙旅程"]),
            "emotion": random.choice(["太震撼了", "不敢相信", "超出预期", "刷新认知"]),
            "starting_point": random.choice(["零基础", "小白", "门外汉", "新手"]),
            "achievement": random.choice(["专家", "达人", "高手", "行家"]),
            "power": random.choice(["动力", "启发", "帮助", "支持"]),
            "realization": random.choice(["重要道理", "人生真谛", "关键问题", "核心本质"])
        }
        
        title = title_pattern.format(**{k: v for k, v in title_vars.items() if f"{{{k}}}" in title_pattern})
        
        # 生成内容
        hook = random.choice(template["hooks"])
        content = await self._generate_article_content(topic, platform, template_type, hook, title)
        
        # 计算预测指标
        viral_score = self.calculate_viral_score(title, content, platform)
        predicted_views = self.predict_views(viral_score, platform, len(content))
        engagement_rate = min(viral_score / 100 * 0.15, 0.20)  # 最高20%互动率
        
        # 生成优化建议
        optimization_tips = self.generate_optimization_tips(viral_score, title, content, platform)
        
        # 风险评估
        risk_factors = self._assess_risks(title, content, template_type)
        
        # 最佳发布时间
        best_time = self._get_best_publish_time(platform)
        
        # 目标受众
        target_audience = self.platform_features[platform]["audience"]
        
        # 热门关键词
        trending_keywords = self._extract_trending_keywords(title, content)
        
        prediction = ViralPrediction(
            title=title,
            content=content,
            platform=platform,
            viral_score=viral_score,
            predicted_views=predicted_views,
            engagement_rate=engagement_rate,
            optimization_tips=optimization_tips,
            risk_factors=risk_factors,
            best_publish_time=best_time,
            target_audience=target_audience,
            trending_keywords=trending_keywords
        )
        
        logger.info(f"✅ 爆款文章生成完成: 预测阅读量 {predicted_views:,}")
        return prediction

    async def _generate_article_content(self, topic: str, platform: str, template_type: str, hook: str, title: str) -> str:
        """生成文章内容"""
        
        # 根据平台和模板类型构建提示词
        platform_info = self.platform_features[platform]
        min_len, max_len = platform_info["content_length"]
        tone = platform_info["tone"]
        
        prompt = f"""
请写一篇关于{topic}的文章，风格要自然真实，像普通人在分享经验一样。

基本信息：
- 话题：{topic}
- 平台：{platform}
- 开头：{hook}
- 字数：{min_len}-{max_len}字

写作要求：
1. 语言要自然，避免过于正式或营销化的表达
2. 可以有个人观点，不需要过分客观
3. 适当提到一些具体的使用感受或者小细节
4. 结构清晰但不要过分模板化
5. 结尾引导一下讨论，但要自然
6. 语气要{tone}，但是要真实不做作
7. 可以提到一些小问题或者不足，增加真实感

注意：
- 不要用太多感叹号和夸张词汇
- 避免"震撼"、"颠覆"、"革命性"这类夸大词汇
- 语言要接地气，像在和朋友聊天
- 可以有个人情感，但不要过度煽情

请直接输出文章内容。
        """
        
        # 调用AI生成内容
        try:
            content = await self.ai_processor.call_deepseek_api([
                {"role": "system", "content": "你是一个普通的内容创作者，喜欢分享真实的使用体验和想法。你的文字自然真实，不会过度夸大，会提到一些实际遇到的小问题。语言风格像在和朋友聊天，接地气但有见解。"},
                {"role": "user", "content": prompt}
            ])
            return content.strip()
        except Exception as e:
            logger.warning(f"AI生成失败，使用模板生成: {e}")
            return self._generate_template_content(topic, platform, template_type, hook)

    def _generate_template_content(self, topic: str, platform: str, template_type: str, hook: str) -> str:
        """模板生成内容（备用方案）"""
        
        content_templates = {
            "真实体验": f"""
{hook}我觉得{topic}没有网上说的那么神奇。

用了一个多星期，确实有些地方很不错，但也有一些问题。

**先说好的地方：**
确实能提高不少效率，特别是处理一些重复性的工作。界面也比较简洁，上手不算难。

**再说说问题：**
• 有时候反应速度有点慢
• 某些功能还不够完善
• 和预期还是有一定差距

**我的建议：**
如果你正在犹豫要不要试试，我觉得可以先免费体验一下。但不要抱太高期望，毕竟技术还在发展阶段。

对于大部分人来说，现阶段够用了。但如果你期望特别高，可能会有点失望。

你们有用过的吗？感觉怎么样？
            """,
            
            "实用干货": f"""
{hook}关于{topic}，分享几个实用经验。

很多人刚开始用的时候会踩坑，我总结了一些避坑指南：

**新手常犯的错误：**
1. 一开始就设置很复杂的参数
2. 没有做好数据备份
3. 忽略了安全设置

**实用技巧：**
• 先从简单功能开始
• 定期检查使用情况
• 学会合理设置权限

**省钱小窍门：**
根据我的经验，选择合适的套餐很重要。不要一上来就选最贵的，先用基础版试试水。

**踩过的坑：**
之前因为没注意设置，结果多花了不少钱。现在分享给大家，希望能帮到有需要的人。

有什么不懂的可以问我，能帮的我都会回复。
            """,
            
            "观点讨论": f"""
{hook}关于{topic}，我有些不一样的想法。

最近看到很多人在讨论这个话题，大部分都是正面评价。但我觉得可能需要更客观地看待这件事。

**我的观点：**
技术确实很厉害，但没必要过度神化。任何技术都有它的局限性，这个也不例外。

**为什么这么说：**
• 目前还有很多问题没解决
• 实际效果和宣传有差距
• 成本相对还是比较高

**换个角度想：**
与其期待一个完美的解决方案，不如理性看待现有的进展。技术发展需要时间，我们要有耐心。

**不过话说回来：**
这个方向是对的，只是现在可能还不是最好的时机。过几年再看，情况可能会好很多。

你们觉得呢？是我想多了还是确实存在这些问题？
            """,
            
            "行业内幕": f"""
{hook}我想分享一些{topic}行业的真实情况。

在这个行业干了几年，看到了一些外人不太了解的事情。今天想和大家聊聊。

**行业现状：**
外界看到的通常是光鲜的一面，但实际情况复杂得多。技术门槛确实不低，真正做好需要很多积累。

**从业者的观点：**
• 这个领域变化很快，需要不断学习
• 竞争比想象中激烈
• 真正赚钱的公司不多

**给想入行的人一些建议：**
不要被表面的热闹迷惑，这行需要真正的技术实力。如果只是为了蹭热点，建议慎重考虑。

**未来趋势：**
个人判断，这个行业会逐渐成熟，但过程中肯定会有很多公司被淘汰。能活下来的，都是有真本事的。

作为普通用户，选择产品的时候要理性一些，不要只看宣传。

有在这个行业的朋友吗？说说你们的看法。
            """,
            
            "故事分享": f"""
{hook}想和大家分享一个关于{topic}的真实经历。

上个月遇到了一件事，让我对这个技术有了新的认识。

**起因：**
本来是想解决一个工作上的问题，朋友推荐我试试这个工具。刚开始我是拒绝的，觉得没什么用。

**转机：**
但是逼急了，没办法只能试试。结果第一次使用就让我有点意外，效果比预期好一些。

**深入了解：**
后来花了一些时间学习，发现确实有它的价值。虽然不是万能的，但在某些场景下很有用。

**意外收获：**
最大的收获不是工具本身，而是这个过程让我意识到，很多时候我们的固有观念会限制自己。

**现在的想法：**
不会盲目推崇，也不会完全否定。任何工具都有它的适用场景，关键是要理性看待。

可能每个人的体验都不一样，分享出来就是想听听大家的想法。

你们有类似的经历吗？
            """
        }
        
        template_content = content_templates.get(template_type, content_templates["故事分享"])
        return template_content.strip()

    def _extract_company(self, topic: str) -> str:
        """提取公司名称"""
        companies = ["OpenAI", "Google", "微软", "百度", "腾讯", "阿里", "字节", "Meta", "苹果", "特斯拉"]
        for company in companies:
            if company.lower() in topic.lower():
                return company
        return "科技巨头"

    def _assess_risks(self, title: str, content: str, template_type: str) -> List[str]:
        """风险评估"""
        risks = []
        
        # 标题风险
        if any(word in title for word in ["独家", "内幕", "爆料"]):
            risks.append("⚠️ 标题使用了'独家'、'内幕'等词汇，需确保内容真实性")
            
        if template_type == "争议话题":
            risks.append("📢 争议性内容可能引发负面评论，需要合理引导讨论")
            
        # 内容风险
        sensitive_words = ["政治", "敏感", "违法", "欺骗"]
        if any(word in content for word in sensitive_words):
            risks.append("🚨 内容可能涉及敏感话题，建议仔细审核")
            
        if len(risks) == 0:
            risks.append("✅ 内容风险较低，可以安全发布")
            
        return risks

    def _get_best_publish_time(self, platform: str) -> str:
        """获取最佳发布时间"""
        current_time = datetime.now()
        peak_hours = self.platform_features[platform]["peak_hours"]
        
        # 找到最近的高峰时间
        current_hour = current_time.hour
        future_peaks = []
        
        for peak in peak_hours:
            peak_hour = int(peak.split(':')[0])
            if peak_hour > current_hour:
                future_peaks.append(peak_hour)
        
        if future_peaks:
            next_peak = min(future_peaks)
            return f"今天 {next_peak:02d}:00"
        else:
            # 明天的第一个高峰时间
            tomorrow_first_peak = int(peak_hours[0].split(':')[0])
            return f"明天 {tomorrow_first_peak:02d}:00"

    def _extract_trending_keywords(self, title: str, content: str) -> List[str]:
        """提取热门关键词"""
        text = title + " " + content
        keywords = []
        
        # 从各类关键词中提取
        for category, word_list in self.viral_keywords.items():
            for word in word_list:
                if word in text and word not in keywords:
                    keywords.append(word)
        
        return keywords[:8]  # 最多8个关键词

    async def generate_multiple_articles(self, topic: str, count: int = 3) -> List[ViralPrediction]:
        """生成多个不同角度的爆款文章"""
        logger.info(f"🚀 批量生成 {count} 篇爆款文章: {topic}")
        
        templates = list(self.viral_templates.keys())
        platforms = ["wechat", "xiaohongshu"]
        
        articles = []
        tasks = []
        
        for i in range(count):
            template = templates[i % len(templates)]
            platform = platforms[i % len(platforms)]
            
            task = self.generate_viral_article(topic, platform, template)
            tasks.append(task)
        
        # 并发生成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, ViralPrediction):
                articles.append(result)
            else:
                logger.error(f"文章生成失败: {result}")
        
        # 按预测阅读量排序
        articles.sort(key=lambda x: x.predicted_views, reverse=True)
        
        logger.info(f"✅ 成功生成 {len(articles)} 篇爆款文章")
        return articles

# 测试函数
async def test_viral_generator():
    """测试爆款文章生成器"""
    generator = ViralArticleGenerator()
    
    # 测试话题
    test_topics = [
        "GPT-5即将发布",
        "Claude超越ChatGPT",
        "AI取代程序员"
    ]
    
    print("🔥 爆款文章生成器测试")
    print("=" * 50)
    
    for topic in test_topics:
        print(f"\n🎯 话题: {topic}")
        
        # 生成单篇文章
        article = await generator.generate_viral_article(topic, "wechat")
        
        print(f"📝 标题: {article.title}")
        print(f"🔥 爆款指数: {article.viral_score:.1f}/100")
        print(f"👀 预测阅读量: {article.predicted_views:,}")
        print(f"💬 预测互动率: {article.engagement_rate:.1%}")
        print(f"⏰ 最佳发布时间: {article.best_publish_time}")
        print(f"🎯 目标受众: {article.target_audience}")
        print(f"🏷️ 热门关键词: {', '.join(article.trending_keywords[:5])}")
        
        if article.optimization_tips:
            print("💡 优化建议:")
            for tip in article.optimization_tips[:3]:
                print(f"   {tip}")
        
        print("\n📄 文章内容预览:")
        print(article.content[:200] + "...")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_viral_generator())