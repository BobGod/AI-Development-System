#!/usr/bin/env python3
"""
智能行业知识问答系统 - API服务器
提供RESTful API接口，支持文档上传、知识问答、在线学习等功能
"""

import os
import asyncio
import json
import traceback
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import logging

# FastAPI
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# 本地模块
import sys
sys.path.append(str(Path(__file__).parent.parent))

from knowledge_ingestion.document_parser import DocumentParser, DocumentParseResult
from knowledge_ingestion.web_crawler import WebCrawler, CrawlConfig, CrawlTask
from knowledge_base.vector_store import VectorStore, SearchQuery, KnowledgeChunk
from llm_integration.deepseek_client import DeepSeekClient, GenerationConfig
from qa_engine.answer_generator import AnswerGenerator, QuestionContext, AnswerResult, QAConfig
from domain_adapters.medical_adapter import MedicalAdapter
from session_manager import SessionManager, get_session_manager

# API模型定义
class QuestionRequest(BaseModel):
    """问题请求模型"""
    question: str = Field(..., description="用户问题")
    domain: str = Field("", description="专业领域")
    user_id: str = Field("", description="用户ID")
    session_id: str = Field("", description="会话ID")
    conversation_history: List[Dict[str, str]] = Field(default=[], description="对话历史")
    additional_context: Dict[str, Any] = Field(default={}, description="额外上下文")

class QuestionResponse(BaseModel):
    """问题回答模型"""
    answer: str = Field(..., description="回答内容")
    confidence: float = Field(..., description="置信度")
    sources: List[Dict[str, Any]] = Field(..., description="信息来源")
    reasoning_steps: List[str] = Field(default=[], description="推理步骤")
    related_questions: List[str] = Field(default=[], description="相关问题")
    generated_at: str = Field(..., description="生成时间")
    session_id: str = Field("", description="会话ID")

class DocumentUploadResponse(BaseModel):
    """文档上传响应模型"""
    success: bool = Field(..., description="上传是否成功")
    document_id: str = Field("", description="文档ID")
    message: str = Field(..., description="响应消息")
    chunks_added: int = Field(0, description="添加的知识块数量")

class CrawlTaskRequest(BaseModel):
    """爬取任务请求模型"""
    domain: str = Field(..., description="领域名称")
    urls: List[str] = Field(..., description="种子URL列表")
    schedule: str = Field("daily", description="调度频率")
    config: Dict[str, Any] = Field(default={}, description="爬取配置")

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询")
    domain: str = Field("", description="限定领域")
    top_k: int = Field(10, description="返回结果数量")
    similarity_threshold: float = Field(0.3, description="相似度阈值")

class SystemStatus(BaseModel):
    """系统状态模型"""
    status: str = Field(..., description="系统状态")
    uptime: float = Field(..., description="运行时间(秒)")
    total_documents: int = Field(..., description="文档总数")
    total_chunks: int = Field(..., description="知识块总数")
    total_questions: int = Field(..., description="问题总数")
    supported_domains: List[str] = Field(..., description="支持的领域")

# 全局变量
app = FastAPI(
    title="智能行业知识问答系统",
    description="基于DeepSeek大模型的多领域智能知识问答API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 安全配置
security = HTTPBearer(auto_error=False)

# 全局组件
document_parser: Optional[DocumentParser] = None
vector_store: Optional[VectorStore] = None
llm_client: Optional[DeepSeekClient] = None
answer_generator: Optional[AnswerGenerator] = None
web_crawler: Optional[WebCrawler] = None
session_manager: SessionManager = get_session_manager()

# 系统状态
system_start_time = datetime.now()
logger = logging.getLogger(__name__)

# 初始化函数
async def initialize_system():
    """初始化系统组件"""
    global document_parser, vector_store, llm_client, answer_generator, web_crawler
    
    try:
        logger.info("开始初始化系统组件...")
        
        # 1. 初始化文档解析器
        document_parser = DocumentParser()
        logger.info("文档解析器初始化完成")
        
        # 2. 初始化向量数据库
        vector_store = VectorStore(
            persist_directory="knowledge_db",
            collection_name="knowledge_base"
        )
        logger.info("向量数据库初始化完成")
        
        # 3. 初始化LLM客户端
        llm_client = DeepSeekClient()
        logger.info("DeepSeek客户端初始化完成")
        
        # 4. 初始化答案生成器
        qa_config = QAConfig(
            max_context_length=4000,
            top_k_results=5,
            similarity_threshold=0.3,
            temperature=0.3,
            enable_reasoning=True,
            enable_source_citation=True
        )
        
        answer_generator = AnswerGenerator(llm_client, vector_store, qa_config)
        
        # 注册领域适配器
        medical_adapter = MedicalAdapter()
        answer_generator.register_domain_adapter("医疗健康", medical_adapter)
        
        logger.info("答案生成器初始化完成")
        
        # 5. 初始化网络爬虫
        crawl_config = CrawlConfig(
            max_pages=50,
            delay_seconds=1.0,
            follow_links=True,
            max_depth=2
        )
        web_crawler = WebCrawler(crawl_config)
        logger.info("网络爬虫初始化完成")
        
        logger.info("系统组件初始化完成！")
        
    except Exception as e:
        logger.error(f"系统初始化失败: {e}")
        raise

# 依赖注入
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """获取当前用户（简化实现）"""
    # 开发环境跳过认证
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    if debug_mode or os.getenv("ENVIRONMENT", "development") == "development":
        return {"user_id": "dev_user", "permissions": ["read", "write"]}
    
    # 生产环境需要验证token
    if not credentials:
        raise HTTPException(status_code=401, detail="需要认证")
    
    # 在实际部署中，这里应该验证JWT token等
    return {"user_id": "default_user", "permissions": ["read", "write"]}

def require_write_permission(user: dict = Depends(get_current_user)):
    """需要写权限"""
    if "write" not in user.get("permissions", []):
        raise HTTPException(status_code=403, detail="需要写权限")
    return user

# API路由

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    await initialize_system()

@app.get("/")
async def root():
    """根路径 - 返回Web界面"""
    # 首先尝试简化版本
    simple_file = static_dir / "simple.html"
    if simple_file.exists():
        return FileResponse(str(simple_file))
    
    # 备选原版本
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {
            "name": "智能行业知识问答系统",
            "version": "1.0.0",
            "status": "运行中",
            "description": "基于DeepSeek大模型的多领域智能知识问答API",
            "note": "Web界面文件不存在，请检查 static/simple.html"
        }

@app.get("/api")
async def api_info():
    """API信息"""
    return {
        "name": "智能行业知识问答系统",
        "version": "1.0.0",
        "status": "运行中",
        "description": "基于DeepSeek大模型的多领域智能知识问答API"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查各组件状态
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "document_parser": document_parser is not None,
                "vector_store": vector_store is not None,
                "llm_client": llm_client is not None,
                "answer_generator": answer_generator is not None,
                "web_crawler": web_crawler is not None
            }
        }
        
        # 检查LLM连接
        if llm_client:
            llm_health = await llm_client.health_check()
            health_status["components"]["llm_connection"] = llm_health
            
        # 如果有组件未初始化，标记为不健康
        if not all(health_status["components"].values()):
            health_status["status"] = "unhealthy"
            
        return health_status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态"""
    try:
        uptime = (datetime.now() - system_start_time).total_seconds()
        
        # 获取统计信息
        vector_stats = vector_store.get_statistics() if vector_store else {}
        qa_stats = answer_generator.get_statistics() if answer_generator else {}
        
        return SystemStatus(
            status="运行中",
            uptime=uptime,
            total_documents=vector_stats.get("unique_documents", 0),
            total_chunks=vector_stats.get("total_chunks", 0),
            total_questions=qa_stats.get("total_questions", 0),
            supported_domains=qa_stats.get("registered_domains", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """问答接口 - 支持会话记忆"""
    try:
        if not answer_generator:
            raise HTTPException(status_code=503, detail="答案生成器未初始化")
            
        # 处理会话
        user_id = request.user_id or "anonymous"
        session_id = request.session_id
        
        # 如果没有提供session_id，创建新会话
        if not session_id:
            session_id = session_manager.create_session(user_id)
        elif not session_manager.get_session(session_id):
            # 会话不存在，创建新会话
            session_id = session_manager.create_session(user_id, session_id)
            
        # 添加用户问题到会话
        session_manager.add_message(session_id, "user", request.question)
        
        # 获取会话上下文
        session_context = session_manager.get_context_for_question(session_id, request.question)
        
        # 构建问题上下文，优先使用会话历史
        conversation_history = session_context.get("conversation_history", [])
        if not conversation_history:
            conversation_history = request.conversation_history
            
        context = QuestionContext(
            question=request.question,
            domain=request.domain,
            user_id=user_id,
            session_id=session_id,
            conversation_history=conversation_history,
            additional_context={
                **request.additional_context,
                **session_context
            }
        )
        
        # 生成答案
        result = await answer_generator.generate_answer(context)
        
        # 添加AI回答到会话
        session_manager.add_message(session_id, "assistant", result.answer, {
            "confidence": result.confidence,
            "sources_count": len(result.sources)
        })
        
        # 获取相关问题建议
        related_questions = []
        if request.domain and request.domain in answer_generator.domain_adapters:
            adapter = answer_generator.domain_adapters[request.domain]
            related_questions = await adapter.suggest_related_questions(request.question)
            
        return QuestionResponse(
            answer=result.answer,
            confidence=result.confidence,
            sources=result.sources,
            reasoning_steps=result.reasoning_steps,
            related_questions=related_questions,
            generated_at=result.generated_at,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"问答处理失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")

@app.post("/ask/stream")
async def ask_question_stream(request: QuestionRequest):
    """流式问答接口"""
    try:
        if not llm_client:
            raise HTTPException(status_code=503, detail="LLM客户端未初始化")
            
        # 构建消息
        from llm_integration.deepseek_client import ChatMessage, MessageRole
        
        messages = [
            ChatMessage(MessageRole.SYSTEM, "你是一个专业的知识问答助手"),
            ChatMessage(MessageRole.USER, request.question)
        ]
        
        # 流式生成
        async def generate_stream():
            try:
                async for chunk in llm_client.chat_completion_stream(messages):
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"流式问答失败: {str(e)}")

@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form(""),
    user: dict = Depends(require_write_permission)
):
    """上传文档接口"""
    try:
        if not document_parser or not vector_store:
            raise HTTPException(status_code=503, detail="文档处理组件未初始化")
            
        # 保存上传的文件
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / file.filename
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        # 解析文档
        parse_result = await document_parser.parse_document(str(file_path))
        
        if parse_result.parse_status != "success":
            raise HTTPException(
                status_code=400, 
                detail=f"文档解析失败: {parse_result.error_message}"
            )
            
        # 如果指定了领域，添加到主题中
        if domain and domain not in parse_result.topics:
            parse_result.topics.append(domain)
            
        # 添加到向量数据库
        chunks_added = await vector_store.add_document(parse_result)
        
        # 保留原始文件以供下载和预览
        # file_path.unlink(missing_ok=True)  # 不删除文件
        
        return DocumentUploadResponse(
            success=True,
            document_id=parse_result.document_id,
            message=f"文档上传成功，添加了 {chunks_added} 个知识块",
            chunks_added=chunks_added
        )
        
    except Exception as e:
        logger.error(f"文档上传失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")

@app.post("/search")
async def search_knowledge(request: SearchRequest):
    """知识搜索接口"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="向量数据库未初始化")
            
        # 构建搜索查询
        search_query = SearchQuery(
            query_text=request.query,
            domain=request.domain,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        # 执行搜索
        results = await vector_store.search(search_query)
        
        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.chunk.content,
                "similarity_score": result.similarity_score,
                "source_file": result.chunk.metadata.get("source_file", "Unknown"),
                "page_number": result.chunk.metadata.get("page_number", 0),
                "chunk_id": result.chunk.chunk_id,
                "metadata": result.chunk.metadata
            })
            
        return {
            "query": request.query,
            "results_count": len(formatted_results),
            "results": formatted_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.post("/crawl/task")
async def create_crawl_task(
    request: CrawlTaskRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_write_permission)
):
    """创建爬取任务"""
    try:
        if not web_crawler:
            raise HTTPException(status_code=503, detail="网络爬虫未初始化")
            
        # 创建爬取任务
        task = await web_crawler.create_crawl_task(
            domain=request.domain,
            seed_urls=request.urls,
            schedule=request.schedule
        )
        
        # 在后台执行任务
        background_tasks.add_task(execute_crawl_task_background, task.task_id)
        
        return {
            "success": True,
            "task_id": task.task_id,
            "message": f"爬取任务已创建，包含 {len(task.urls)} 个URL",
            "status": task.status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建爬取任务失败: {str(e)}")

async def execute_crawl_task_background(task_id: str):
    """后台执行爬取任务"""
    try:
        # 这里需要从存储中加载任务
        # 简化实现，实际应该有任务存储机制
        logger.info(f"开始执行后台爬取任务: {task_id}")
        
        # 执行爬取逻辑...
        # 将结果添加到知识库...
        
        logger.info(f"后台爬取任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"后台爬取任务失败: {task_id}, 错误: {e}")

@app.get("/domains")
async def get_supported_domains():
    """获取支持的领域列表"""
    try:
        domains = []
        
        if answer_generator:
            stats = answer_generator.get_statistics()
            domains = stats.get("registered_domains", [])
            
        # 添加默认领域
        default_domains = ["通用", "人工智能", "计算机科学", "医疗健康", "法律", "教育", "金融"]
        
        all_domains = list(set(domains + default_domains))
        
        return {
            "supported_domains": all_domains,
            "registered_adapters": domains,
            "total_count": len(all_domains)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取领域列表失败: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user: dict = Depends(require_write_permission)
):
    """删除文档"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="向量数据库未初始化")
            
        deleted_count = await vector_store.delete_document(document_id)
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="文档不存在")
            
        return {
            "success": True,
            "message": f"成功删除文档，共删除 {deleted_count} 个知识块",
            "deleted_chunks": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")

@app.get("/statistics")
async def get_statistics():
    """获取系统统计信息"""
    try:
        stats = {}
        
        # 向量数据库统计
        if vector_store:
            stats["vector_store"] = vector_store.get_statistics()
            
        # 问答统计
        if answer_generator:
            stats["qa_engine"] = answer_generator.get_statistics()
            
        # LLM统计
        if llm_client:
            stats["llm_client"] = llm_client.get_request_statistics()
            
        # 系统统计
        stats["system"] = {
            "uptime_seconds": (datetime.now() - system_start_time).total_seconds(),
            "start_time": system_start_time.isoformat()
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

# 错误处理
@app.get("/documents")
async def list_documents():
    """获取已上传的文档列表"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="向量数据库未初始化")
            
        # 从向量数据库获取所有文档的元数据
        all_chunks = vector_store.collection.get()
        
        # 按文档ID分组，提取文档信息
        documents = {}
        for i, chunk_id in enumerate(all_chunks['ids']):
            metadata = all_chunks['metadatas'][i]
            doc_id = metadata.get('document_id')
            
            if doc_id and doc_id not in documents:
                documents[doc_id] = {
                    'document_id': doc_id,
                    'source_file': metadata.get('source_file', 'Unknown'),
                    'file_type': metadata.get('file_type', 'Unknown'),
                    'document_title': metadata.get('document_title', ''),
                    'created_at': metadata.get('created_at', ''),
                    'keywords': metadata.get('keywords', ''),
                    'topics': metadata.get('topics', ''),
                    'chunk_count': 0
                }
            
            if doc_id in documents:
                documents[doc_id]['chunk_count'] += 1
        
        return {
            "total_documents": len(documents),
            "documents": list(documents.values())
        }
        
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")

@app.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    """下载文档"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="向量数据库未初始化")
            
        # 从数据库获取文档信息
        results = vector_store.collection.get(
            where={"document_id": document_id},
            limit=1
        )
        
        if not results['ids']:
            raise HTTPException(status_code=404, detail="文档不存在")
            
        metadata = results['metadatas'][0]
        source_file = metadata.get('source_file', 'unknown.txt')
        
        # 查找文件
        upload_dir = Path("uploads")
        file_path = upload_dir / source_file
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
            
        return FileResponse(
            path=str(file_path),
            filename=source_file,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载文档失败: {str(e)}")

@app.get("/documents/{document_id}")
async def get_document_info(document_id: str):
    """获取文档详细信息"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="向量数据库未初始化")
            
        # 从数据库获取所有相关的知识块
        results = vector_store.collection.get(
            where={"document_id": document_id}
        )
        
        if not results['ids']:
            raise HTTPException(status_code=404, detail="文档不存在")
            
        # 构建文档信息
        metadata = results['metadatas'][0]
        chunks = []
        
        for i, chunk_id in enumerate(results['ids']):
            chunks.append({
                'chunk_id': chunk_id,
                'content': results['documents'][i],
                'metadata': results['metadatas'][i]
            })
        
        return {
            'document_id': document_id,
            'source_file': metadata.get('source_file', 'Unknown'),
            'file_type': metadata.get('file_type', 'Unknown'),
            'document_title': metadata.get('document_title', ''),
            'created_at': metadata.get('created_at', ''),
            'keywords': metadata.get('keywords', '').split(',') if metadata.get('keywords') else [],
            'topics': metadata.get('topics', '').split(',') if metadata.get('topics') else [],
            'chunk_count': len(chunks),
            'chunks': chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档信息失败: {str(e)}")

# 会话管理API
@app.post("/sessions")
async def create_session(user_id: str = "anonymous"):
    """创建新会话"""
    try:
        session_id = session_manager.create_session(user_id)
        return {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
            
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "created_at": session.created_at,
            "last_active": session.last_active,
            "message_count": len(session.messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")

@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 20):
    """获取会话历史"""
    try:
        history = session_manager.get_conversation_history(session_id, limit)
        return {
            "session_id": session_id,
            "history": history,
            "total_messages": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        success = session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        return {"message": "会话删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(e)}")

@app.get("/sessions/stats")
async def get_session_stats():
    """获取会话统计"""
    try:
        stats = session_manager.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# 主函数
def main():
    """启动API服务器"""
    import argparse
    
    parser = argparse.ArgumentParser(description="智能知识问答系统API服务器")
    parser.add_argument("--host", default="0.0.0.0", help="服务器地址")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="启用自动重载")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 启动服务器
    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )

if __name__ == "__main__":
    main()