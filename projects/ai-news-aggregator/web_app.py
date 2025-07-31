"""
🌐 AI智能新闻聚合平台 - Web API服务
提供RESTful API和Web界面
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import os
import logging
from datetime import datetime
import uvicorn

# 导入自定义模块
from news_spider import NewsSpider, collect_realtime_news
from content_processor import AIContentProcessor, Platform
from image_generator import AIImageGenerator
from viral_article_generator import ViralArticleGenerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI智能新闻聚合平台",
    description="超越量子位、机器之心的全自动化AI新闻收集和内容生成系统",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
cached_news = []
cached_processed_content = {}
last_update_time = None

# 初始化服务组件
content_processor = AIContentProcessor()
image_generator = AIImageGenerator()
viral_generator = ViralArticleGenerator(content_processor)

# 请求模型
class NewsRequest(BaseModel):
    """新闻请求模型"""
    limit: int = 20
    platform: str = "wechat"
    refresh: bool = False

class ContentRequest(BaseModel):
    """内容处理请求模型"""
    news_ids: List[str]
    platforms: List[str] = ["wechat", "xiaohongshu"]

class ExportRequest(BaseModel):
    """导出请求模型"""
    content_id: str
    platform: str
    format: str = "markdown"

class ViralArticleRequest(BaseModel):
    """爆款文章生成请求模型"""
    topic: str
    platform: str = "wechat"
    template_type: Optional[str] = None

class BatchViralRequest(BaseModel):
    """批量爆款文章生成请求模型"""
    topics: List[str]
    count: int = 3
    platforms: List[str] = ["wechat", "xiaohongshu"]

# API路由
@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
        <head><title>AI新闻聚合平台</title></head>
        <body>
            <h1>🤖 AI智能新闻聚合平台</h1>
            <p>系统正在启动中...</p>
            <p>API文档: <a href="/api/docs">/api/docs</a></p>
            <p>系统状态: <a href="/api/health">/api/health</a></p>
            <p>最新新闻: <a href="/api/news/latest">/api/news/latest</a></p>
        </body>
        </html>
        """)

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "news_spider": "running",
            "content_processor": "running", 
            "image_generator": "running",
            "viral_generator": "running"
        }
    }

@app.get("/api/news/latest")
async def get_latest_news(limit: int = 20, refresh: bool = False):
    """获取最新AI新闻"""
    global cached_news, last_update_time
    
    try:
        # 检查是否需要刷新
        if refresh or not cached_news or not last_update_time or \
           (datetime.now() - last_update_time).seconds > 1800:  # 30分钟更新一次
            
            logger.info("🔄 刷新新闻数据...")
            cached_news = await collect_realtime_news()
            last_update_time = datetime.now()
        
        # 返回限制数量的新闻
        news_data = []
        for news in cached_news[:limit]:
            news_dict = {
                "id": news.id,
                "title": news.title,
                "content": news.content,
                "url": news.url,
                "source": news.source,
                "published_time": news.published_time.isoformat(),
                "author": news.author,
                "tags": news.tags,
                "heat_score": news.heat_score,
                "language": news.language,
                "content_type": news.content_type
            }
            news_data.append(news_dict)
        
        return {
            "success": True,
            "data": news_data,
            "total": len(cached_news),
            "last_update": last_update_time.isoformat() if last_update_time else None,
            "message": f"获取到 {len(news_data)} 条AI新闻"
        }
        
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")

@app.post("/api/content/process")
async def process_content(request: ContentRequest):
    """处理新闻内容并生成配图"""
    global cached_news, cached_processed_content
    
    try:
        # 根据ID筛选新闻
        selected_news = []
        for news in cached_news:
            if news.id in request.news_ids:
                selected_news.append(news)
        
        if not selected_news:
            raise HTTPException(status_code=404, detail="未找到指定的新闻")
        
        # 处理内容
        processor = AIContentProcessor()
        platforms = [Platform(p) for p in request.platforms]
        results = await processor.batch_process(selected_news, platforms)
        
        # 生成配图
        generated_images = {}
        for platform_str in request.platforms:
            generated_images[platform_str] = []
            
            # 为每个新闻生成配图
            for news in selected_news:
                try:
                    image = await image_generator.generate_image_for_news(
                        news.title, 
                        news.content[:200],  # 使用前200字符
                        platform_str
                    )
                    
                    # 确保目录存在
                    import os
                    os.makedirs(f"static/images/{platform_str}", exist_ok=True)
                    
                    # 保存图片
                    image_path = image.save_to_file(f"static/images/{platform_str}")
                    
                    generated_images[platform_str].append({
                        "news_id": news.id,
                        "image_path": image_path,
                        "image_url": f"/static/images/{platform_str}/{image.filename}",
                        "image_source": image.source,
                        "size_kb": image.size_kb,
                        "prompt": image.prompt
                    })
                    
                except Exception as e:
                    logger.error(f"为新闻 {news.id} 生成配图失败: {e}")
                    # 添加占位符
                    generated_images[platform_str].append({
                        "news_id": news.id,
                        "image_path": None,
                        "image_url": None,
                        "image_source": "failed",
                        "size_kb": 0,
                        "error": str(e)
                    })
        
        # 缓存结果
        for platform, content_list in results.items():
            platform_key = platform.value
            if platform_key not in cached_processed_content:
                cached_processed_content[platform_key] = []
            
            for content in content_list:
                content_dict = content.to_dict()
                content_dict["processed_time"] = datetime.now().isoformat()
                cached_processed_content[platform_key].append(content_dict)
        
        # 格式化返回数据
        response_data = {}
        for platform, content_list in results.items():
            platform_key = platform.value
            response_data[platform_key] = []
            
            for content in content_list:
                # 查找对应的配图
                image_info = None
                for img in generated_images.get(platform_key, []):
                    if img["news_id"] == content.original_news.id:
                        image_info = img
                        break
                
                response_data[platform_key].append({
                    "id": f"{content.original_news.id}_{platform_key}",
                    "original_title": content.original_news.title,
                    "optimized_title": content.optimized_title,
                    "formatted_content": content.formatted_content,
                    "tags": content.tags,
                    "hashtags": content.hashtags,
                    "engagement_score": content.engagement_score,
                    "reading_time": content.reading_time,
                    "thumbnail_prompt": content.thumbnail_prompt,
                    "generated_image": image_info,  # 新增：配图信息
                    "processed_time": datetime.now().isoformat()
                })
        
        return {
            "success": True,
            "data": response_data,
            "processed_count": len(selected_news),
            "platforms": request.platforms,
            "images_generated": sum(len(imgs) for imgs in generated_images.values()),
            "message": "内容处理和配图生成完成"
        }
        
    except Exception as e:
        logger.error(f"内容处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"内容处理失败: {str(e)}")

@app.post("/api/images/generate")
async def generate_images(background_tasks: BackgroundTasks, news_ids: List[str], platforms: List[str] = ["wechat"]):
    """生成配图"""
    global cached_news
    
    try:
        # 筛选新闻
        selected_news = []
        for news in cached_news:
            if news.id in news_ids:
                selected_news.append({
                    "title": news.title,
                    "content": news.content,
                    "id": news.id
                })
        
        if not selected_news:
            raise HTTPException(status_code=404, detail="未找到指定的新闻")
        
        # 生成图片
        generator = AIImageGenerator()
        results = await generator.batch_generate_images(selected_news, platforms)
        
        # 保存图片
        saved_files = generator.save_generated_images(results)
        
        return {
            "success": True,
            "data": saved_files,
            "generated_count": len(selected_news),
            "platforms": platforms,
            "message": "配图生成完成"
        }
        
    except Exception as e:
        logger.error(f"配图生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"配图生成失败: {str(e)}")

@app.get("/api/content/export/{content_id}/{platform}")
async def export_content(content_id: str, platform: str, format: str = "markdown"):
    """导出内容"""
    global cached_processed_content
    
    try:
        if platform not in cached_processed_content:
            raise HTTPException(status_code=404, detail="未找到指定平台的内容")
        
        # 查找内容
        content_item = None
        for item in cached_processed_content[platform]:
            if f"{item['original_news']['id']}_{platform}" == content_id:
                content_item = item
                break
        
        if not content_item:
            raise HTTPException(status_code=404, detail="未找到指定内容")
        
        # 格式化导出内容
        if format == "markdown":
            export_content = content_item["formatted_content"]
        elif format == "html":
            # 简单的HTML格式化
            export_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{content_item['optimized_title']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .meta {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
        .tags {{ margin-top: 20px; }}
        .tag {{ background: #e3f2fd; padding: 4px 8px; margin: 2px; border-radius: 4px; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>{content_item['optimized_title']}</h1>
    <div class="meta">
        <p>互动评分: {content_item['engagement_score']:.1f}分 | 阅读时间: {content_item['reading_time']}秒</p>
        <p>标签: {', '.join(content_item['tags'])}</p>
    </div>
    <div class="content">
        {content_item['formatted_content'].replace(chr(10), '<br>')}
    </div>
    <div class="tags">
        话题: {' '.join(['#' + tag for tag in content_item['hashtags']])}
    </div>
</body>
</html>
            """.strip()
        else:
            export_content = content_item["formatted_content"]
        
        return {
            "success": True,
            "data": {
                "content": export_content,
                "title": content_item["optimized_title"],
                "format": format,
                "platform": platform,
                "export_time": datetime.now().isoformat()
            },
            "message": "内容导出成功"
        }
        
    except Exception as e:
        logger.error(f"内容导出失败: {e}")
        raise HTTPException(status_code=500, detail=f"内容导出失败: {str(e)}")

@app.get("/api/images/{platform}/{filename}")
async def get_image(platform: str, filename: str):
    """获取生成的图片"""
    image_path = f"generated_images/{platform}/{filename}"
    
    if os.path.exists(image_path):
        return FileResponse(image_path)
    else:
        raise HTTPException(status_code=404, detail="图片不存在")

@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    global cached_news, cached_processed_content, last_update_time
    
    try:
        # 统计数据
        total_news = len(cached_news)
        processed_count = sum(len(items) for items in cached_processed_content.values())
        
        # 热度分布
        heat_distribution = {"high": 0, "medium": 0, "low": 0}
        for news in cached_news:
            if news.heat_score >= 70:
                heat_distribution["high"] += 1
            elif news.heat_score >= 40:
                heat_distribution["medium"] += 1
            else:
                heat_distribution["low"] += 1
        
        # 来源分布
        source_distribution = {}
        for news in cached_news:
            source_distribution[news.source] = source_distribution.get(news.source, 0) + 1
        
        return {
            "success": True,
            "data": {
                "total_news": total_news,
                "processed_content": processed_count,
                "last_update": last_update_time.isoformat() if last_update_time else None,
                "heat_distribution": heat_distribution,
                "source_distribution": source_distribution,
                "platforms": list(cached_processed_content.keys()),
                "uptime_hours": 24  # 简化统计
            },
            "message": "统计信息获取成功"
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🔥 新增：爆款文章生成API
@app.post("/api/viral/generate")
async def generate_viral_article(request: ViralArticleRequest):
    """生成单篇爆款文章"""
    try:
        logger.info(f"🔥 生成爆款文章请求: {request.topic}")
        
        article = await viral_generator.generate_viral_article(
            topic=request.topic,
            platform=request.platform,
            template_type=request.template_type
        )
        
        return {
            "status": "success",
            "data": {
                "title": article.title,
                "content": article.content,
                "platform": article.platform,
                "viral_score": article.viral_score,
                "predicted_views": article.predicted_views,
                "engagement_rate": article.engagement_rate,
                "optimization_tips": article.optimization_tips,
                "risk_factors": article.risk_factors,
                "best_publish_time": article.best_publish_time,
                "target_audience": article.target_audience,
                "trending_keywords": article.trending_keywords,
                "generated_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"爆款文章生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@app.post("/api/viral/auto-generate")
async def auto_generate_viral_articles(count: int = 5, platform: str = "wechat"):
    """根据当前热门新闻自动生成爆款文章"""
    global cached_news
    
    try:
        logger.info(f"🚀 自动生成爆款文章: 基于热门新闻，数量 {count}")
        
        if not cached_news:
            raise HTTPException(status_code=404, detail="暂无新闻数据，请先刷新新闻")
        
        # 选择热度最高的新闻
        hot_news = sorted(cached_news, key=lambda x: x.heat_score, reverse=True)[:count]
        
        generated_articles = []
        
        for news in hot_news:
            try:
                # 基于新闻标题生成爆款文章
                article = await viral_generator.generate_viral_article(
                    topic=news.title,
                    platform=platform,
                    template_type=None  # 自动选择最佳模板
                )
                
                # 为文章生成配图
                try:
                    image = await image_generator.generate_image_for_news(
                        news.title, 
                        news.content[:200],
                        platform
                    )
                    
                    # 保存图片
                    os.makedirs(f"static/images/{platform}", exist_ok=True)
                    image_path = image.save_to_file(f"static/images/{platform}")
                    
                    image_info = {
                        "image_url": f"/static/images/{platform}/{image.filename}",
                        "image_source": image.source,
                        "size_kb": image.size_kb,
                        "prompt": image.prompt
                    }
                except Exception as img_e:
                    logger.warning(f"为文章生成配图失败: {img_e}")
                    image_info = None
                
                generated_articles.append({
                    "original_news_id": news.id,
                    "original_title": news.title,
                    "original_source": news.source,
                    "original_heat_score": news.heat_score,
                    "viral_title": article.title,
                    "viral_content": article.content,
                    "platform": article.platform,
                    "viral_score": article.viral_score,
                    "predicted_views": article.predicted_views,
                    "engagement_rate": article.engagement_rate,
                    "best_publish_time": article.best_publish_time,
                    "target_audience": article.target_audience,
                    "trending_keywords": article.trending_keywords,
                    "generated_image": image_info,
                    "generated_time": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"为新闻 {news.title[:30]}... 生成爆款文章失败: {e}")
                continue
        
        # 按预测阅读量排序
        generated_articles.sort(key=lambda x: x["predicted_views"], reverse=True)
        
        return {
            "status": "success",
            "data": {
                "total_generated": len(generated_articles),
                "articles": generated_articles,
                "summary": {
                    "avg_viral_score": sum(a["viral_score"] for a in generated_articles) / len(generated_articles) if generated_articles else 0,
                    "total_predicted_views": sum(a["predicted_views"] for a in generated_articles),
                    "best_article": generated_articles[0] if generated_articles else None,
                    "articles_with_10k_plus": len([a for a in generated_articles if a["predicted_views"] >= 10000])
                },
                "generated_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"自动生成爆款文章失败: {e}")
        raise HTTPException(status_code=500, detail=f"自动生成失败: {str(e)}")

@app.post("/api/viral/batch")
async def generate_batch_viral_articles(request: BatchViralRequest):
    """批量生成爆款文章"""
    try:
        logger.info(f"🚀 批量生成爆款文章: {len(request.topics)} 个话题")
        
        results = []
        
        for topic in request.topics:
            for platform in request.platforms:
                try:
                    article = await viral_generator.generate_viral_article(topic, platform)
                    
                    results.append({
                        "topic": topic,
                        "title": article.title,
                        "content": article.content,
                        "platform": article.platform,
                        "viral_score": article.viral_score,
                        "predicted_views": article.predicted_views,
                        "engagement_rate": article.engagement_rate,
                        "optimization_tips": article.optimization_tips[:3],  # 只返回前3个建议
                        "risk_factors": article.risk_factors[:2],  # 只返回前2个风险
                        "best_publish_time": article.best_publish_time,
                        "target_audience": article.target_audience,
                        "trending_keywords": article.trending_keywords[:5]  # 只返回前5个关键词
                    })
                    
                except Exception as e:
                    logger.error(f"话题 {topic} 在 {platform} 平台生成失败: {e}")
                    continue
        
        # 按预测阅读量排序
        results.sort(key=lambda x: x["predicted_views"], reverse=True)
        
        return {
            "status": "success",
            "data": {
                "total_generated": len(results),
                "articles": results,
                "summary": {
                    "avg_viral_score": sum(r["viral_score"] for r in results) / len(results) if results else 0,
                    "total_predicted_views": sum(r["predicted_views"] for r in results),
                    "best_article": results[0] if results else None
                },
                "generated_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"批量生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量生成失败: {str(e)}")

@app.get("/api/viral/templates")
async def get_viral_templates():
    """获取爆款文章模板类型"""
    return {
        "status": "success",
        "data": {
            "templates": list(viral_generator.viral_templates.keys()),
            "platforms": list(viral_generator.platform_features.keys()),
            "template_details": {
                name: {
                    "viral_potential": info["viral_potential"],
                    "sample_patterns": info["title_patterns"][:2],  # 前2个示例
                    "sample_hooks": info["hooks"][:2]  # 前2个钩子
                }
                for name, info in viral_generator.viral_templates.items()
            }
        }
    }

@app.post("/api/viral/optimize")
async def optimize_article(title: str, content: str, platform: str = "wechat"):
    """优化文章以提升爆款潜力"""
    try:
        # 计算当前爆款指数
        current_score = viral_generator.calculate_viral_score(title, content, platform)
        
        # 生成优化建议
        optimization_tips = viral_generator.generate_optimization_tips(current_score, title, content, platform)
        
        # 预测阅读量
        predicted_views = viral_generator.predict_views(current_score, platform, len(content))
        
        # 风险评估
        risk_factors = viral_generator._assess_risks(title, content, "深度解析")
        
        return {
            "status": "success",
            "data": {
                "current_viral_score": current_score,
                "predicted_views": predicted_views,
                "optimization_tips": optimization_tips,
                "risk_factors": risk_factors,
                "trending_keywords": viral_generator._extract_trending_keywords(title, content),
                "best_publish_time": viral_generator._get_best_publish_time(platform),
                "platform_features": viral_generator.platform_features[platform],
                "analysis_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"文章优化分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

# 后台任务：定期更新新闻
async def periodic_news_update():
    """定期更新新闻"""
    global cached_news, last_update_time
    
    while True:
        try:
            await asyncio.sleep(1800)  # 30分钟更新一次
            logger.info("🔄 定期更新新闻...")
            cached_news = await collect_realtime_news()
            last_update_time = datetime.now()
            logger.info(f"✅ 新闻更新完成，共 {len(cached_news)} 条")
        except Exception as e:
            logger.error(f"定期更新失败: {e}")

# 启动时初始化
@app.on_event("startup")
async def startup_event():
    """启动事件"""
    global cached_news, last_update_time
    
    logger.info("🚀 AI智能新闻聚合平台启动中...")
    
    # 创建必要的目录
    os.makedirs("generated_images", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    # 初始化新闻数据
    try:
        cached_news = await collect_realtime_news()
        last_update_time = datetime.now()
        logger.info(f"✅ 初始化完成，获取到 {len(cached_news)} 条新闻")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        cached_news = []
    
    # 启动定期更新任务
    asyncio.create_task(periodic_news_update())
    
    logger.info("🎉 系统启动完成！访问 http://localhost:8000")

if __name__ == "__main__":
    uvicorn.run(
        "web_app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )