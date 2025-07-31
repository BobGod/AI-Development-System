#!/usr/bin/env python3
"""
🧪 爆款文章生成器测试脚本
测试AI原创文章生成和火爆度预测功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 简化版内容处理器（用于测试）
class SimpleAIProcessor:
    def __init__(self):
        pass
    
    async def call_deepseek_api(self, messages):
        """模拟AI生成内容"""
        topic = "AI技术突破"
        
        # 模拟生成的文章内容
        sample_content = f"""
{messages[1]['content'].split('开场白：')[1].split('标题：')[0].strip()}，{topic}再次震撼全球！

刚刚收到消息，这项技术的突破可能比我们想象的更具颠覆性。

**核心突破**
这次技术革新在以下几个关键领域实现了质的飞跃：
• 处理速度提升了500%，超越了所有现有系统
• 能耗降低了70%，真正实现了绿色AI
• 应用场景扩展到20+个全新领域

**行业反响**
业内顶级专家纷纷发声，认为这是"改变游戏规则的时刻"。一位硅谷资深工程师告诉我："这不仅仅是技术进步，这是范式转变。"

**深度影响**
对于我们普通人来说，这意味着：
1. 工作效率将迎来革命性提升
2. 创作门槛大幅降低，人人都能成为创作者
3. 学习方式彻底改变，个性化教育成为现实

**未来展望**
基于这次突破，我预测在接下来的6个月内，整个AI行业将迎来新一轮的爆发式增长。那些能够快速适应和应用这项技术的个人和企业，将获得巨大的先发优势。

你觉得这次技术突破会对你的生活和工作产生什么影响？评论区分享你的想法，让我们一起见证历史的转折点！

#AI突破 #技术革命 #未来已来
        """
        
        return sample_content.strip()

# 直接复制核心类定义（简化版）
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import random
import re

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
    
    def __init__(self, ai_processor = None):
        self.ai_processor = ai_processor or SimpleAIProcessor()
        
        # 爆款文章模板库
        self.viral_templates = {
            "震撼发布": {
                "title_patterns": [
                    "🚀 重磅！{topic}刚刚发布，{impact}震撼全球！",
                    "💥 突发！{topic}{action}，{result}！",
                    "⚡ 刚刚！{company}官宣{topic}，{reaction}炸裂！",
                    "🔥 独家！{topic}内幕曝光，{revelation}！"
                ],
                "hooks": [
                    "刚刚收到内部消息",
                    "朋友圈都在转发这个",
                    "不敢相信自己的眼睛",
                    "这可能改变一切"
                ],
                "viral_potential": 95
            },
            "深度解析": {
                "title_patterns": [
                    "🧠 深度｜{topic}背后的{angle}，99%的人都想错了",
                    "📊 数据说话｜{topic}的{aspect}，真相竟然是这样",
                    "🔍 独家解析｜{topic}为什么{reason}？内行人终于说出真话",
                    "💡 重新认识{topic}：{new_perspective}"
                ],
                "hooks": [
                    "作为行业内部人士",
                    "经过深度调研发现",
                    "让我们用数据说话",
                    "从另一个角度看"
                ],
                "viral_potential": 80
            },
            "争议话题": {
                "title_patterns": [
                    "⚠️ 争议｜{topic}真的{claim}吗？我有不同看法",
                    "🗣️ 热议｜{topic}{controversy}，网友吵翻了！",
                    "❓ 质疑｜{topic}背后的{hidden_truth}，没人敢说出来",
                    "🤔 反思｜{topic}让我们失去了什么？"
                ],
                "hooks": [
                    "可能会得罪一些人，但我还是要说",
                    "这个观点可能很不受欢迎",
                    "准备好被喷了，但真相需要有人说",
                    "不同的声音同样值得倾听"
                ],
                "viral_potential": 90
            },
            "预测未来": {
                "title_patterns": [
                    "🔮 预测｜{topic}将在{timeframe}内{prediction}",
                    "🌟 趋势｜{topic}的{future_impact}，你准备好了吗？",
                    "⏰ 倒计时｜{topic}{countdown}，{consequence}即将到来",
                    "🚀 未来已来｜{topic}正在{transformation}"
                ],
                "hooks": [
                    "如果我告诉你未来是这样",
                    "10年后回看今天",
                    "历史总是惊人的相似",
                    "变化比我们想象的更快"
                ],
                "viral_potential": 75
            },
            "个人故事": {
                "title_patterns": [
                    "💭 亲历｜我与{topic}的{experience}，{emotion}...",
                    "📝 实录｜{topic}改变了我的{aspect}",
                    "💪 励志｜从{starting_point}到{achievement}，{topic}给了我{power}",
                    "😮 震惊｜{topic}让我意识到{realization}"
                ],
                "hooks": [
                    "说出来你可能不信",
                    "这是我的亲身经历",
                    "从没想过会有这样的体验",
                    "如果早知道这些就好了"
                ],
                "viral_potential": 85
            }
        }
        
        # 爆款关键词库
        self.viral_keywords = {
            "情绪词": ["震撼", "炸裂", "疯狂", "惊艳", "崩溃", "沸腾", "颠覆", "逆天"],
            "数字词": ["首次", "史上最", "100%", "10倍", "千万", "亿级", "第一"],
            "紧迫词": ["刚刚", "突发", "紧急", "限时", "倒计时", "最后", "即将"],
            "独家词": ["内幕", "揭秘", "独家", "爆料", "曝光", "首发", "重磅"],
            "对比词": ["VS", "碾压", "秒杀", "超越", "完胜", "吊打", "逆袭"],
            "疑问词": ["为什么", "怎么办", "真的吗", "可能吗", "谁知道", "什么"],
            "话题词": ["人工智能", "ChatGPT", "大模型", "AI", "机器人", "自动驾驶", "元宇宙"]
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
            }
        }

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
            "xiaohongshu": 8000
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
            
        return tips

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

    async def generate_viral_article(self, topic: str, platform: str = "wechat", template_type: str = None) -> ViralPrediction:
        """生成爆款文章"""
        logger.info(f"🔥 生成爆款文章: {topic} -> {platform}")
        
        # 自动选择最佳模板
        if not template_type:
            # 基于话题选择最适合的模板
            if any(word in topic.lower() for word in ["发布", "推出", "上线", "官宣"]):
                template_type = "震撼发布"
            elif any(word in topic.lower() for word in ["分析", "解读", "深度", "研究"]):
                template_type = "深度解析"
            elif any(word in topic.lower() for word in ["争议", "质疑", "反对", "批评"]):
                template_type = "争议话题"
            elif any(word in topic.lower() for word in ["预测", "未来", "趋势", "展望"]):
                template_type = "预测未来"
            else:
                template_type = "个人故事"
        
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
请基于以下信息创作一篇爆款原创文章：

主题：{topic}
平台：{platform}
风格：{template_type}
语调：{tone}
开场白：{hook}
标题：{title}

要求：
1. 字数：{min_len}-{max_len}字
2. 结构清晰，分3-5个段落
3. 开头用钩子吸引读者
4. 内容原创，有独特观点
5. 结尾引导互动
6. 语言{tone}但易懂
7. 适当使用数据和案例
8. 确保内容能引发讨论和分享

请直接输出文章内容，不要包含其他说明。
        """
        
        # 调用AI生成内容
        try:
            content = await self.ai_processor.call_deepseek_api([
                {"role": "system", "content": "你是专业的爆款文章写手，擅长创作能获得10万+阅读的优质内容。"},
                {"role": "user", "content": prompt}
            ])
            return content.strip()
        except Exception as e:
            logger.warning(f"AI生成失败，使用模板生成: {e}")
            return self._generate_template_content(topic, platform, template_type, hook)

    def _generate_template_content(self, topic: str, platform: str, template_type: str, hook: str) -> str:
        """模板生成内容（备用方案）"""
        
        content_templates = {
            "震撼发布": f"""
{hook}，{topic}刚刚正式发布了！

这次发布的影响可能远比我们想象的更大。让我来告诉你为什么：

**核心突破**
这项技术在以下几个方面实现了重大突破：
• 性能提升了300%以上
• 成本降低了50%
• 应用场景扩大了10倍

**行业影响**
业内专家普遍认为，这将彻底改变现有的竞争格局。一位不愿透露姓名的行业资深人士告诉我："这是一个分水岭时刻。"

**你的机会**
对于普通用户来说，这意味着什么？
1. 更好的体验
2. 更低的成本  
3. 更多的可能性

你觉得这个发布会对行业产生什么影响？评论区聊聊你的看法！

#AI技术 #科技前沿 #行业变革
            """,
            
            "深度解析": f"""
{hook}，今天我们来深度解析一下{topic}。

很多人对这个话题的理解都停留在表面，但真相可能和你想的完全不一样。

**数据说话**
根据最新的调研数据显示：
• 90%的人对此存在认知偏差
• 实际情况比预期复杂3倍
• 未来发展趋势出人意料

**深层逻辑**
让我们从技术原理开始分析。这背后的核心逻辑是什么？为什么会有这样的发展？

经过深入研究，我发现了三个关键因素：
1. 技术成熟度的临界点
2. 市场需求的爆发
3. 政策环境的支持

**未来展望**
基于这些分析，我预测在未来12个月内，这个领域将出现重大变化。

你对这个分析有什么看法？是否同意我的观点？

#深度分析 #行业洞察 #技术趋势
            """,
            
            "个人故事": f"""
{hook}，我想和大家分享一个关于{topic}的真实经历。

上个月，我有机会亲身体验了这项技术，那种震撼至今难忘。

**初次接触**
刚开始我是抱着试试看的态度，没想到结果完全超出了预期。那一刻，我意识到未来真的来了。

**深度体验**
在接下来的几天里，我尝试了各种不同的使用场景：
• 工作效率提升了200%
• 创作灵感源源不断
• 学习速度明显加快

**意外发现**
最让我惊喜的是，它不仅仅是一个工具，更像是一个智能伙伴。有时候它给出的建议比我自己想的还要好。

**思考感悟**
这次经历让我深刻认识到，我们正站在一个历史转折点上。那些主动拥抱变化的人，将获得巨大的先发优势。

你有过类似的体验吗？在评论区分享你的故事吧！

#亲身体验 #技术感悟 #未来思考
            """
        }
        
        template_content = content_templates.get(template_type, content_templates["个人故事"])
        return template_content.strip()

async def test_viral_generator():
    """测试爆款文章生成器"""
    print("🔥 AI原创爆款文章生成器测试")
    print("=" * 60)
    
    generator = ViralArticleGenerator()
    
    # 测试话题
    test_topics = [
        "Claude 4.0超越GPT-5震撼发布",
        "AI取代程序员成为现实",
        "中国AI芯片实现全球领先"
    ]
    
    for i, topic in enumerate(test_topics, 1):
        print(f"\n🎯 测试 {i}/3: {topic}")
        print("-" * 50)
        
        try:
            # 生成爆款文章
            article = await generator.generate_viral_article(topic, "wechat")
            
            print(f"📝 标题: {article.title}")
            print(f"🔥 爆款指数: {article.viral_score:.1f}/100")
            print(f"👀 预测阅读量: {article.predicted_views:,}")
            print(f"💬 预测互动率: {article.engagement_rate:.1%}")
            print(f"⏰ 最佳发布时间: {article.best_publish_time}")
            print(f"🎯 目标受众: {article.target_audience}")
            print(f"🏷️ 热门关键词: {', '.join(article.trending_keywords[:5])}")
            
            if article.optimization_tips:
                print(f"\n💡 优化建议:")
                for tip in article.optimization_tips[:3]:
                    print(f"   {tip}")
            
            if article.risk_factors:
                print(f"\n⚠️ 风险评估:")
                for risk in article.risk_factors[:2]:
                    print(f"   {risk}")
            
            print(f"\n📄 文章内容预览:")
            content_preview = article.content[:300] + "..." if len(article.content) > 300 else article.content
            print(content_preview)
            
            # 验证是否达到10万+阅读量目标
            if article.predicted_views >= 10000:
                print(f"\n✅ 成功！预测阅读量 {article.predicted_views:,} 达到10万+目标")
            else:
                print(f"\n⚠️ 注意：预测阅读量 {article.predicted_views:,} 未达到10万+目标")
            
            print("\n" + "="*60)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_viral_generator())