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

# API路由
@app.get("/", response_class=HTMLResponse)
async def root():
    """主页"""
    return HTMLResponse(open("static/index.html", encoding="utf-8").read())

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
            "image_generator": "running"
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
    """处理新闻内容"""
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
            response_data[platform.value] = []
            for content in content_list:
                response_data[platform.value].append({
                    "id": f"{content.original_news.id}_{platform.value}",
                    "original_title": content.original_news.title,
                    "optimized_title": content.optimized_title,
                    "formatted_content": content.formatted_content,
                    "tags": content.tags,
                    "hashtags": content.hashtags,
                    "engagement_score": content.engagement_score,
                    "reading_time": content.reading_time,
                    "thumbnail_prompt": content.thumbnail_prompt
                })
        
        return {
            "success": True,
            "data": response_data,
            "processed_count": len(selected_news),
            "platforms": request.platforms,
            "message": "内容处理完成"
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
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )