#!/usr/bin/env python3
"""
🧪 图片生成器测试脚本
测试文字图片生成功能（无需外部依赖）
"""

import os
import hashlib
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from enum import Enum

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
        
        print(f"💾 图片已保存: {filepath} ({self.size_kb}KB)")
        return filepath

class PlatformImageConfig:
    """不同平台的图片规格"""
    
    CONFIGS = {
        "wechat": ImageConfig(900, 500, ImageStyle.PROFESSIONAL),
        "xiaohongshu": ImageConfig(1080, 1080, ImageStyle.CASUAL),
        "weibo": ImageConfig(800, 450, ImageStyle.MODERN),
        "thumbnail": ImageConfig(400, 300, ImageStyle.TECH)
    }

def generate_text_image(text: str, config: ImageConfig) -> GeneratedImage:
    """生成文字图片（备用方案）"""
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
        
        # 绘制主标题
        main_text = "AI 新闻"
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
        
        # 绘制副标题
        sub_text = text[:30] + "..." if len(text) > 30 else text
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
            prompt=f"Text image: {text}",
            source="generated",
            filename=filename,
            size_kb=len(image_data) // 1024
        )
        
    except Exception as e:
        print(f"❌ 文字图片生成失败: {e}")
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

def test_image_generator():
    """测试图片生成器"""
    print("🎨 图片生成器测试")
    print("=" * 60)
    
    # 测试新闻标题
    test_titles = [
        "Claude 4.0超越GPT-5震撼发布",
        "AI取代程序员成为现实",
        "中国AI芯片实现全球领先"
    ]
    
    platforms = ["wechat", "xiaohongshu"]
    
    for i, title in enumerate(test_titles, 1):
        print(f"\n🎯 测试 {i}/{len(test_titles)}: {title}")
        print("-" * 50)
        
        for platform in platforms:
            try:
                config = PlatformImageConfig.CONFIGS[platform]
                image = generate_text_image(title, config)
                
                # 保存图片
                directory = f"test_images/{platform}"
                filepath = image.save_to_file(directory)
                
                print(f"📱 {platform.upper()} 平台:")
                print(f"   尺寸: {config.width}x{config.height}")
                print(f"   文件: {image.filename}")
                print(f"   大小: {image.size_kb}KB")
                print(f"   路径: {filepath}")
                
            except Exception as e:
                print(f"❌ {platform} 平台图片生成失败: {e}")
    
    print("\n✅ 图片生成测试完成!")
    print("🔍 请检查 test_images/ 目录查看生成的图片")

if __name__ == "__main__":
    test_image_generator()