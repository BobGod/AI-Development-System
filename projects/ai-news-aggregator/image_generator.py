"""
🎨 智能图片生成和匹配系统
为AI新闻自动生成和匹配高质量配图
"""

import asyncio
import aiohttp
import json
import logging
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageStyle(Enum):
    """图片风格枚举"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECH = "tech"
    MODERN = "modern"

@dataclass
class ImageConfig:
    """图片配置"""
    width: int
    height: int
    style: ImageStyle
    format: str = "PNG"
    quality: int = 90

class PlatformImageConfig:
    """不同平台的图片规格"""
    
    CONFIGS = {
        "wechat": ImageConfig(900, 500, ImageStyle.PROFESSIONAL),
        "xiaohongshu": ImageConfig(1080, 1080, ImageStyle.CASUAL),
        "weibo": ImageConfig(800, 450, ImageStyle.MODERN),
        "thumbnail": ImageConfig(400, 300, ImageStyle.TECH)
    }

@dataclass 
class GeneratedImage:
    """生成的图片信息"""
    image_data: bytes
    config: ImageConfig
    prompt: str
    source: str  # "dalle", "stable_diffusion", "unsplash", "generated"
    filename: str
    size_kb: int
    
    def save_to_file(self, directory: str = "generated_images") -> str:
        """保存图片到文件"""
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, self.filename)
        
        with open(filepath, 'wb') as f:
            f.write(self.image_data)
        
        logger.info(f"💾 图片已保存: {filepath} ({self.size_kb}KB)")
        return filepath

class AIImageGenerator:
    """AI图片生成器"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.unsplash_access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        
        # 预定义的AI相关图片模板
        self.ai_image_templates = {
            "gpt": {
                "prompt": "modern AI chatbot interface, clean design, blue and white theme, digital brain network, professional tech illustration",
                "style": "digital art, high quality, 8k"
            },
            "robot": {
                "prompt": "futuristic humanoid robot, sleek white design, advanced technology, studio lighting, clean background",
                "style": "product photography, professional"
            },
            "brain": {
                "prompt": "artificial neural network, digital brain, glowing connections, blue purple gradient, sci-fi aesthetic",
                "style": "digital art, cyberpunk, high tech"
            },
            "data": {
                "prompt": "data visualization, flowing data streams, charts and graphs, technology background, modern interface",
                "style": "infographic style, clean, professional"
            },
            "chip": {
                "prompt": "computer microchip, circuit board, electronic components, macro photography, high tech details",
                "style": "product photography, macro lens"
            },
            "autonomous": {
                "prompt": "self-driving car with sensor visualization, LiDAR points, urban environment, future transportation",
                "style": "concept art, realistic, high detail"
            },
            "startup": {
                "prompt": "modern office space, team collaboration, startup environment, innovation, bright lighting",
                "style": "corporate photography, professional"
            },
            "investment": {
                "prompt": "financial growth chart, upward trend, money and technology, success visualization, gold and green colors",
                "style": "business illustration, clean design"
            }
        }

    def get_image_keywords(self, title: str, content: str) -> List[str]:
        """从内容中提取图片关键词"""
        text = (title + " " + content).lower()
        keywords = []
        
        # 技术关键词映射
        keyword_map = {
            "gpt": ["gpt", "chatgpt", "语言模型"],
            "robot": ["机器人", "robot", "humanoid"],
            "brain": ["大脑", "神经", "brain", "neural"],
            "data": ["数据", "data", "分析", "analytics"],
            "chip": ["芯片", "chip", "处理器", "processor"],
            "autonomous": ["自动驾驶", "autonomous", "self-driving"],
            "startup": ["创业", "startup", "公司", "团队"],
            "investment": ["投资", "融资", "investment", "funding"]
        }
        
        for category, terms in keyword_map.items():
            if any(term in text for term in terms):
                keywords.append(category)
        
        return keywords[:3]  # 最多3个关键词

    async def generate_with_dalle(self, prompt: str, config: ImageConfig) -> Optional[GeneratedImage]:
        """使用DALL-E生成图片"""
        if not self.openai_api_key:
            logger.warning("未设置OpenAI API密钥，跳过DALL-E生成")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": f"{config.width}x{config.height}",
                "quality": "hd",
                "response_format": "b64_json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/images/generations",
                    headers=headers,
                    json=payload,
                    timeout=60
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        image_b64 = result["data"][0]["b64_json"]
                        image_data = base64.b64decode(image_b64)
                        
                        filename = f"dalle_{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png"
                        
                        return GeneratedImage(
                            image_data=image_data,
                            config=config,
                            prompt=prompt,
                            source="dalle",
                            filename=filename,
                            size_kb=len(image_data) // 1024
                        )
                    else:
                        logger.error(f"DALL-E API调用失败: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"DALL-E生成失败: {e}")
            return None

    async def search_unsplash(self, query: str, config: ImageConfig) -> Optional[GeneratedImage]:
        """从Unsplash搜索图片"""
        if not self.unsplash_access_key:
            logger.warning("未设置Unsplash API密钥，跳过图片搜索")
            return None
        
        try:
            headers = {
                "Authorization": f"Client-ID {self.unsplash_access_key}"
            }
            
            params = {
                "query": query,
                "per_page": 5,
                "orientation": "landscape" if config.width > config.height else "portrait"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.unsplash.com/search/photos",
                    headers=headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        if result["results"]:
                            photo = result["results"][0]
                            image_url = photo["urls"]["regular"]
                            
                            # 下载图片
                            async with session.get(image_url) as img_response:
                                if img_response.status == 200:
                                    image_data = await img_response.read()
                                    
                                    # 调整图片尺寸
                                    image_data = self.resize_image(image_data, config)
                                    
                                    filename = f"unsplash_{photo['id']}.jpg"
                                    
                                    return GeneratedImage(
                                        image_data=image_data,
                                        config=config,
                                        prompt=query,
                                        source="unsplash",
                                        filename=filename,
                                        size_kb=len(image_data) // 1024
                                    )
        except Exception as e:
            logger.error(f"Unsplash搜索失败: {e}")
            return None

    def resize_image(self, image_data: bytes, config: ImageConfig) -> bytes:
        """调整图片尺寸"""
        try:
            with Image.open(BytesIO(image_data)) as img:
                # 调整尺寸保持比例
                img.thumbnail((config.width, config.height), Image.Resampling.LANCZOS)
                
                # 创建指定尺寸的背景
                background = Image.new('RGB', (config.width, config.height), (255, 255, 255))
                
                # 居中放置图片
                x = (config.width - img.width) // 2
                y = (config.height - img.height) // 2
                background.paste(img, (x, y))
                
                # 转换为bytes
                output = BytesIO()
                background.save(output, format=config.format, quality=config.quality)
                return output.getvalue()
                
        except Exception as e:
            logger.error(f"图片尺寸调整失败: {e}")
            return image_data

    def extract_english_keywords(self, text: str) -> str:
        """从中文新闻标题中提取英文关键词"""
        # 常见AI中英文对照词典
        keyword_mapping = {
            "GPT": "GPT",
            "ChatGPT": "ChatGPT", 
            "OpenAI": "OpenAI",
            "AI": "AI",
            "人工智能": "Artificial Intelligence",
            "机器学习": "Machine Learning",
            "深度学习": "Deep Learning",
            "神经网络": "Neural Network",
            "大模型": "Large Language Model",
            "LLM": "LLM",
            "模型": "Model",
            "算法": "Algorithm",
            "数据": "Data",
            "训练": "Training",
            "推理": "Inference",
            "生成": "Generation",
            "对话": "Conversation",
            "聊天": "Chat",
            "机器人": "Robot",
            "自动驾驶": "Autonomous Driving",
            "计算机视觉": "Computer Vision",
            "自然语言": "Natural Language",
            "语音": "Speech",
            "图像": "Image",
            "视频": "Video",
            "文本": "Text",
            "代码": "Code",
            "编程": "Programming",
            "软件": "Software",
            "技术": "Technology",
            "科技": "Tech",
            "创新": "Innovation",
            "发布": "Release",
            "更新": "Update",
            "升级": "Upgrade",
            "突破": "Breakthrough",
            "革命": "Revolution",
            "未来": "Future",
            "智能": "Intelligence",
            "系统": "System",
            "平台": "Platform",
            "应用": "Application",
            "工具": "Tool",
            "服务": "Service",
            "云": "Cloud",
            "边缘": "Edge",
            "物联网": "IoT",
            "区块链": "Blockchain",
            "元宇宙": "Metaverse",
            "VR": "VR",
            "AR": "AR",
            "芯片": "Chip",
            "处理器": "Processor",
            "GPU": "GPU",
            "CPU": "CPU",
            "量子": "Quantum",
            "5G": "5G",
            "6G": "6G"
        }
        
        # 提取已有的英文词汇
        import re
        english_words = re.findall(r'[A-Za-z0-9]+', text)
        result_words = []
        
        # 添加英文词汇
        for word in english_words:
            if len(word) > 1:  # 排除单个字母
                result_words.append(word)
        
        # 根据中文内容添加对应英文词汇
        for chinese, english in keyword_mapping.items():
            if chinese in text and english not in result_words:
                result_words.append(english)
        
        # 如果没有找到关键词，使用默认的
        if not result_words:
            result_words = ["AI", "Technology", "Innovation"]
        
        return " • ".join(result_words[:3])  # 最多3个关键词，用点分隔

    def generate_text_image(self, text: str, config: ImageConfig) -> GeneratedImage:
        """生成文字图片（备用方案）- 使用英文避免中文乱码"""
        try:
            # 创建图片
            img = Image.new('RGB', (config.width, config.height), (45, 55, 72))  # 深蓝灰色背景
            draw = ImageDraw.Draw(img)
            
            # 尝试加载字体
            try:
                # 根据系统选择字体
                if os.name == 'nt':  # Windows
                    font_large = ImageFont.truetype("arial.ttf", 48)
                    font_small = ImageFont.truetype("arial.ttf", 24)
                else:  # macOS/Linux
                    try:
                        font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 48)
                        font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
                    except:
                        font_large = ImageFont.load_default()
                        font_small = ImageFont.load_default()
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # 绘制主标题 - 使用英文
            main_text = "AI News"
            try:
                bbox = draw.textbbox((0, 0), main_text, font=font_large)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                text_width = len(main_text) * 20
                text_height = 48
            
            x = (config.width - text_width) // 2
            y = config.height // 2 - 50
            
            draw.text((x, y), main_text, fill=(255, 255, 255), font=font_large)
            
            # 绘制副标题 - 使用提取的英文关键词
            sub_text = self.extract_english_keywords(text)
            try:
                bbox = draw.textbbox((0, 0), sub_text, font=font_small)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(sub_text) * 12
            
            x = (config.width - text_width) // 2
            y = config.height // 2 + 20
            
            draw.text((x, y), sub_text, fill=(156, 163, 175), font=font_small)
            
            # 添加装饰元素
            draw.rectangle([(50, config.height - 80), (config.width - 50, config.height - 75)], 
                         fill=(59, 130, 246))  # 蓝色装饰条
            
            # 转换为bytes
            output = BytesIO()
            img.save(output, format=config.format, quality=config.quality)
            image_data = output.getvalue()
            
            filename = f"text_{hashlib.md5(text.encode()).hexdigest()[:8]}.png"
            
            return GeneratedImage(
                image_data=image_data,
                config=config,
                prompt=f"Text image: {sub_text}",
                source="generated",
                filename=filename,
                size_kb=len(image_data) // 1024
            )
            
        except Exception as e:
            logger.error(f"文字图片生成失败: {e}")
            # 返回最简单的图片
            try:
                img = Image.new('RGB', (config.width, config.height), (45, 55, 72))
                output = BytesIO()
                img.save(output, format='PNG')
                return GeneratedImage(
                    image_data=output.getvalue(),
                    config=config,
                    prompt="Simple image",
                    source="generated",
                    filename="simple.png",
                    size_kb=len(output.getvalue()) // 1024
                )
            except:
                # 最后的兜底方案
                empty_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x17IDAT\x08\x1dc```bPPP\x00\x02\xac\xac\xac\x00\x05\x06\x06\x06\x00\x00\x00\x00\x00\x01?\x1e\x99\x85\x00\x00\x00\x00IEND\xaeB`\x82'
                return GeneratedImage(
                    image_data=empty_data,
                    config=config,
                    prompt="Empty image",
                    source="generated",
                    filename="empty.png",
                    size_kb=1
                )

    async def generate_image_for_news(self, title: str, content: str, platform: str = "wechat") -> GeneratedImage:
        """为新闻生成配图"""
        config = PlatformImageConfig.CONFIGS[platform]
        keywords = self.get_image_keywords(title, content)
        
        logger.info(f"🎨 为新闻生成配图: {title[:30]}... -> {platform}")
        logger.info(f"   关键词: {keywords}")
        
        # 选择最佳模板
        if keywords:
            template_key = keywords[0]
            template = self.ai_image_templates.get(template_key, self.ai_image_templates["brain"])
        else:
            template = self.ai_image_templates["brain"]
        
        # 构建完整提示词
        full_prompt = f"{template['prompt']}, {template['style']}"
        
        # 尝试多种生成方式
        image = None
        
        # 1. 尝试DALL-E生成
        if not image:
            image = await self.generate_with_dalle(full_prompt, config)
        
        # 2. 尝试Unsplash搜索
        if not image:
            search_query = " ".join(keywords) if keywords else "artificial intelligence technology"
            image = await self.search_unsplash(search_query, config)
        
        # 3. 生成文字图片作为备用
        if not image:
            logger.warning("所有图片生成方式失败，使用文字图片")
            image = self.generate_text_image(title, config)
        
        logger.info(f"✅ 配图生成完成: {image.source} - {image.size_kb}KB")
        return image

    async def batch_generate_images(self, news_data: List[Dict], platforms: List[str] = None) -> Dict[str, List[GeneratedImage]]:
        """批量生成图片"""
        if platforms is None:
            platforms = ["wechat", "xiaohongshu"]
        
        results = {platform: [] for platform in platforms}
        tasks = []
        
        # 创建任务
        for news in news_data[:10]:  # 限制处理数量
            for platform in platforms:
                task = self.generate_image_for_news(news["title"], news["content"], platform)
                tasks.append((task, news, platform))
        
        logger.info(f"🚀 开始批量生成图片: {len(news_data)}条新闻 x {len(platforms)}个平台")
        
        # 执行任务
        for task, news, platform in tasks:
            try:
                image = await task
                results[platform].append({
                    "news_title": news["title"],
                    "image": image
                })
            except Exception as e:
                logger.error(f"图片生成失败: {e}")
        
        logger.info(f"✅ 批量图片生成完成!")
        return results

    def save_generated_images(self, results: Dict[str, List[GeneratedImage]], base_dir: str = "generated_images"):
        """保存生成的图片"""
        saved_files = {}
        
        for platform, images in results.items():
            platform_dir = os.path.join(base_dir, platform)
            os.makedirs(platform_dir, exist_ok=True)
            
            saved_files[platform] = []
            
            for item in images:
                if isinstance(item, dict) and "image" in item:
                    image = item["image"]
                    filepath = image.save_to_file(platform_dir)
                    saved_files[platform].append({
                        "news_title": item["news_title"],
                        "filepath": filepath,
                        "filename": image.filename,
                        "source": image.source,
                        "size_kb": image.size_kb
                    })
        
        # 保存索引文件
        index_file = os.path.join(base_dir, "image_index.json")
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump({
                "generated_time": datetime.now().isoformat(),
                "platforms": saved_files
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📋 图片索引已保存: {index_file}")
        return saved_files

# 测试函数
async def test_image_generator():
    """测试图片生成器"""
    generator = AIImageGenerator()
    
    # 测试新闻数据
    test_news = [
        {
            "title": "GPT-5即将发布！OpenAI内部消息曝光性能提升300%",
            "content": "据可靠消息源透露，OpenAI的下一代大语言模型GPT-5已进入最后测试阶段，性能相比GPT-4有显著提升..."
        },
        {
            "title": "谷歌发布新款AI机器人，自主学习能力震撼业界", 
            "content": "谷歌最新发布的人形机器人具备强大的自主学习能力，能够在复杂环境中执行各种任务..."
        },
        {
            "title": "字节跳动AI芯片项目获50亿融资，估值达千亿",
            "content": "字节跳动旗下AI芯片项目获得新一轮融资，投资方包括多家知名投资机构..."
        }
    ]
    
    # 生成图片
    results = await generator.batch_generate_images(test_news)
    
    # 保存图片
    saved_files = generator.save_generated_images(results)
    
    # 展示结果
    print("\n🎨 图片生成结果:")
    print("=" * 80)
    
    for platform, images in saved_files.items():
        print(f"\n📱 {platform.upper()} 平台图片:")
        print("-" * 60)
        
        for item in images:
            print(f"新闻: {item['news_title'][:50]}...")
            print(f"文件: {item['filename']} ({item['size_kb']}KB)")
            print(f"来源: {item['source']}")
            print(f"路径: {item['filepath']}")
            print()

if __name__ == "__main__":
    asyncio.run(test_image_generator())