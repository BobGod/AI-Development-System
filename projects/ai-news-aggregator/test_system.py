#!/usr/bin/env python3
"""
🧪 AI智能新闻聚合平台 - 快速测试脚本
验证所有核心功能是否正常工作
"""

import asyncio
import sys
import json
from datetime import datetime

async def test_news_spider():
    """测试新闻爬虫"""
    print("🕷️  测试新闻爬虫...")
    try:
        from news_spider import collect_realtime_news
        news = await collect_realtime_news()
        print(f"   ✅ 成功收集 {len(news)} 条AI新闻")
        
        if news:
            top_news = news[0]
            print(f"   📰 热门新闻: {top_news.title[:50]}...")
            print(f"   🔥 热度评分: {top_news.heat_score:.1f}")
        
        return True, len(news)
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False, 0

async def test_content_processor():
    """测试内容处理"""
    print("🧠 测试AI内容处理...")
    try:
        from news_spider import collect_realtime_news
        from content_processor import AIContentProcessor, Platform
        
        # 获取测试新闻
        news = await collect_realtime_news()
        if not news:
            print("   ⚠️  跳过：没有新闻数据")
            return True
        
        processor = AIContentProcessor()
        result = await processor.process_news(news[0], Platform.WECHAT)
        
        print(f"   ✅ 内容处理成功")
        print(f"   📝 优化标题: {result.optimized_title[:50]}...")
        print(f"   🎯 互动评分: {result.engagement_score:.1f}")
        print(f"   🏷️  标签数量: {len(result.tags)}")
        
        return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False

async def test_image_generator():
    """测试图片生成"""
    print("🎨 测试图片生成...")
    try:
        from image_generator import AIImageGenerator
        
        generator = AIImageGenerator()
        
        # 测试文字图片生成（保底方案）
        test_title = "GPT-5即将发布！性能提升300%震撼登场"
        image = generator.generate_text_image(test_title, generator.ai_image_templates["gpt"])
        
        print(f"   ✅ 图片生成成功")
        print(f"   📊 图片大小: {image.size_kb}KB")
        print(f"   📁 文件名: {image.filename}")
        
        return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False

def test_web_interface():
    """测试Web界面文件"""
    print("🌐 测试Web界面...")
    try:
        import os
        
        # 检查关键文件
        files_to_check = [
            "web_app.py",
            "static/index.html",
            "requirements.txt",
            ".env.template"
        ]
        
        missing_files = []
        for file in files_to_check:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"   ❌ 缺少文件: {', '.join(missing_files)}")
            return False
        
        print("   ✅ Web界面文件检查通过")
        return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False

async def run_full_test():
    """运行完整测试"""
    print("🤖 AI智能新闻聚合平台 - 系统测试")
    print("=" * 50)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # 测试新闻爬虫
    spider_success, news_count = await test_news_spider()
    test_results.append(("新闻爬虫", spider_success))
    
    # 测试内容处理（仅在有新闻时测试）
    if spider_success and news_count > 0:
        processor_success = await test_content_processor()
        test_results.append(("内容处理", processor_success))
    else:
        print("🧠 跳过内容处理测试（无新闻数据）")
        test_results.append(("内容处理", None))
    
    # 测试图片生成
    image_success = await test_image_generator()
    test_results.append(("图片生成", image_success))
    
    # 测试Web界面
    web_success = test_web_interface()
    test_results.append(("Web界面", web_success))
    
    # 输出测试结果
    print()
    print("📊 测试结果汇总:")
    print("-" * 30)
    
    passed = 0
    total = 0
    
    for test_name, result in test_results:
        if result is True:
            status = "✅ 通过"
            passed += 1
            total += 1
        elif result is False:
            status = "❌ 失败"
            total += 1
        else:
            status = "⏭️  跳过"
        
        print(f"{test_name:12} {status}")
    
    print("-" * 30)
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"通过率: {passed}/{total} ({success_rate:.1f}%)")
    
    # 系统建议
    print()
    print("💡 系统建议:")
    if success_rate >= 75:
        print("🎉 系统运行良好！可以启动服务了")
        print("   运行命令: ./start.sh")
    elif success_rate >= 50:
        print("⚠️  系统基本可用，但建议修复失败的测试")
    else:
        print("🚨 系统存在较多问题，建议检查配置和依赖")
    
    print()
    print("🔗 启动后访问:")
    print("   Web界面: http://localhost:8000")
    print("   API文档: http://localhost:8000/api/docs")
    
    return success_rate >= 50

def main():
    """主函数"""
    try:
        success = asyncio.run(run_full_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⛔ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试过程中发生意外错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()