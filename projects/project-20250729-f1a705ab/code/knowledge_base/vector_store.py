#!/usr/bin/env python3
"""
智能行业知识问答系统 - 向量数据库
使用ChromaDB实现知识的向量化存储和语义检索
"""

import os
import json
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import hashlib
from pathlib import Path

# 向量数据库和嵌入
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# 本地模块
import sys
sys.path.append(str(Path(__file__).parent.parent))
from knowledge_ingestion.document_parser import ExtractedContent, DocumentParseResult

@dataclass
class KnowledgeChunk:
    """知识块数据类"""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    source_document: str = ""
    chunk_index: int = 0
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class SearchResult:
    """搜索结果"""
    chunk: KnowledgeChunk
    similarity_score: float
    rank: int

@dataclass
class SearchQuery:
    """搜索查询"""
    query_text: str
    filters: Dict[str, Any] = None
    top_k: int = 10
    similarity_threshold: float = 0.0
    domain: str = ""
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = {}

class VectorStore:
    """向量数据库管理器"""
    
    def __init__(self, 
                 persist_directory: str = "knowledge_db",
                 collection_name: str = "knowledge_base",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        初始化向量数据库
        
        Args:
            persist_directory: 数据持久化目录
            collection_name: 集合名称
            embedding_model: 嵌入模型名称
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        self.logger = logging.getLogger(__name__)
        
        # 统计信息 - 先初始化，避免引用错误
        self.stats = {
            "total_chunks": 0,
            "total_queries": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        # 初始化嵌入模型
        self.logger.info(f"加载嵌入模型: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # 初始化ChromaDB客户端
        self._init_chromadb()
        
    def _init_chromadb(self):
        """初始化ChromaDB"""
        try:
            # 创建ChromaDB客户端
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 创建或获取集合
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "智能知识问答系统知识库"},
                embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=self.embedding_model_name
                )
            )
            
            # 更新统计信息
            self.stats["total_chunks"] = self.collection.count()
            
            self.logger.info(f"ChromaDB初始化完成，集合: {self.collection_name}, 文档数: {self.stats['total_chunks']}")
            
        except Exception as e:
            self.logger.error(f"ChromaDB初始化失败: {e}")
            raise
            
    async def add_document(self, parse_result: DocumentParseResult) -> int:
        """
        添加文档到向量数据库
        
        Args:
            parse_result: 文档解析结果
            
        Returns:
            int: 添加的知识块数量
        """
        try:
            chunks = await self._create_knowledge_chunks(parse_result)
            
            if not chunks:
                self.logger.warning(f"文档无有效内容: {parse_result.document_id}")
                return 0
                
            # 批量添加到向量数据库
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            
            self.collection.add(
                ids=chunk_ids,
                documents=documents,
                metadatas=metadatas
            )
            
            # 更新统计信息
            self.stats["total_chunks"] += len(chunks)
            self.stats["last_updated"] = datetime.now().isoformat()
            
            self.logger.info(f"成功添加文档: {parse_result.document_id}, 知识块数: {len(chunks)}")
            return len(chunks)
            
        except Exception as e:
            self.logger.error(f"添加文档失败: {parse_result.document_id}, 错误: {e}")
            raise
            
    async def _create_knowledge_chunks(self, parse_result: DocumentParseResult) -> List[KnowledgeChunk]:
        """从解析结果创建知识块"""
        chunks = []
        
        for i, content in enumerate(parse_result.extracted_contents):
            # 过滤太短的内容
            if len(content.content.strip()) < 20:
                continue
                
            # 生成chunk ID
            chunk_id = self._generate_chunk_id(parse_result.document_id, i)
            
            # 准备元数据 - ChromaDB只支持基本数据类型
            metadata = {
                "document_id": parse_result.document_id,
                "source_file": parse_result.metadata.file_name,
                "file_type": parse_result.metadata.file_type,
                "content_type": content.content_type,
                "page_number": content.page_number or 0,
                "chunk_index": i,
                "created_at": datetime.now().isoformat(),
                "document_title": parse_result.metadata.title or "",
                "document_author": parse_result.metadata.author or "",
                # 将列表转换为字符串
                "keywords": ",".join(parse_result.keywords) if parse_result.keywords else "",
                "topics": ",".join(parse_result.topics) if parse_result.topics else ""
            }
            
            # 添加内容特定的元数据
            if content.metadata:
                metadata.update(content.metadata)
                
            chunk = KnowledgeChunk(
                chunk_id=chunk_id,
                content=content.content,
                metadata=metadata,
                source_document=parse_result.document_id,
                chunk_index=i
            )
            
            chunks.append(chunk)
            
        return chunks
        
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        语义搜索
        
        Args:
            query: 搜索查询
            
        Returns:
            List[SearchResult]: 搜索结果列表
        """
        try:
            self.stats["total_queries"] += 1
            
            # 准备查询参数
            where_conditions = {}
            
            # 添加领域过滤 - 修复ChromaDB查询语法
            if query.domain:
                # ChromaDB不支持$contains，改用$eq或直接匹配
                where_conditions["topics"] = query.domain
                
            # 添加自定义过滤条件
            if query.filters:
                where_conditions.update(query.filters)
                
            # 执行向量搜索
            results = self.collection.query(
                query_texts=[query.query_text],
                n_results=query.top_k,
                where=where_conditions if where_conditions else None
            )
            
            # 解析搜索结果
            search_results = []
            
            if results['ids'] and results['ids'][0]:
                for i, (chunk_id, document, metadata, distance) in enumerate(zip(
                    results['ids'][0],
                    results['documents'][0], 
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # 修复相似度计算 - ChromaDB使用的是欧几里得距离
                    # 对于欧几里得距离，我们需要将其转换为相似度分数
                    # 使用倒数关系，距离越小相似度越高
                    if distance == 0:
                        similarity_score = 1.0
                    else:
                        # 使用指数衰减函数，确保相似度在0-1之间
                        similarity_score = 1.0 / (1.0 + distance)
                    
                    # 应用相似度阈值
                    if similarity_score < query.similarity_threshold:
                        continue
                        
                    chunk = KnowledgeChunk(
                        chunk_id=chunk_id,
                        content=document,
                        metadata=metadata
                    )
                    
                    result = SearchResult(
                        chunk=chunk,
                        similarity_score=similarity_score,
                        rank=i + 1
                    )
                    
                    search_results.append(result)
                    
            self.logger.info(f"搜索完成: {query.query_text}, 结果数: {len(search_results)}")
            return search_results
            
        except Exception as e:
            self.logger.error(f"搜索失败: {query.query_text}, 错误: {e}")
            raise
            
    async def get_similar_chunks(self, chunk_id: str, top_k: int = 5) -> List[SearchResult]:
        """
        获取相似的知识块
        
        Args:
            chunk_id: 目标知识块ID
            top_k: 返回结果数量
            
        Returns:
            List[SearchResult]: 相似知识块列表
        """
        try:
            # 获取目标chunk
            target_results = self.collection.get(ids=[chunk_id], include=['documents'])
            
            if not target_results['documents']:
                self.logger.warning(f"找不到知识块: {chunk_id}")
                return []
                
            target_content = target_results['documents'][0]
            
            # 搜索相似内容
            query = SearchQuery(
                query_text=target_content,
                top_k=top_k + 1  # +1 因为会包含自己
            )
            
            results = await self.search(query)
            
            # 过滤掉自己
            filtered_results = [r for r in results if r.chunk.chunk_id != chunk_id]
            
            return filtered_results[:top_k]
            
        except Exception as e:
            self.logger.error(f"获取相似块失败: {chunk_id}, 错误: {e}")
            return []
            
    async def update_chunk(self, chunk_id: str, content: str = None, metadata: Dict[str, Any] = None) -> bool:
        """
        更新知识块
        
        Args:
            chunk_id: 知识块ID
            content: 新内容
            metadata: 新元数据
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 获取现有数据
            existing = self.collection.get(ids=[chunk_id], include=['documents', 'metadatas'])
            
            if not existing['ids']:
                self.logger.warning(f"找不到知识块: {chunk_id}")
                return False
                
            # 准备更新数据
            new_content = content if content is not None else existing['documents'][0]
            new_metadata = existing['metadatas'][0].copy()
            
            if metadata:
                new_metadata.update(metadata)
                
            new_metadata['updated_at'] = datetime.now().isoformat()
            
            # 删除旧数据
            self.collection.delete(ids=[chunk_id])
            
            # 添加新数据
            self.collection.add(
                ids=[chunk_id],
                documents=[new_content],
                metadatas=[new_metadata]
            )
            
            self.logger.info(f"成功更新知识块: {chunk_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新知识块失败: {chunk_id}, 错误: {e}")
            return False
            
    async def delete_document(self, document_id: str) -> int:
        """
        删除文档及其所有知识块
        
        Args:
            document_id: 文档ID
            
        Returns:
            int: 删除的知识块数量
        """
        try:
            # 查找文档的所有知识块
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if not results['ids']:
                self.logger.warning(f"找不到文档: {document_id}")
                return 0
                
            chunk_ids = results['ids']
            
            # 批量删除
            self.collection.delete(ids=chunk_ids)
            
            # 更新统计信息
            self.stats["total_chunks"] -= len(chunk_ids)
            self.stats["last_updated"] = datetime.now().isoformat()
            
            self.logger.info(f"成功删除文档: {document_id}, 知识块数: {len(chunk_ids)}")
            return len(chunk_ids)
            
        except Exception as e:
            self.logger.error(f"删除文档失败: {document_id}, 错误: {e}")
            return 0
            
    async def get_chunk_by_id(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        """
        根据ID获取知识块
        
        Args:
            chunk_id: 知识块ID
            
        Returns:
            Optional[KnowledgeChunk]: 知识块或None
        """
        try:
            results = self.collection.get(
                ids=[chunk_id],
                include=['documents', 'metadatas']
            )
            
            if not results['ids']:
                return None
                
            return KnowledgeChunk(
                chunk_id=chunk_id,
                content=results['documents'][0],
                metadata=results['metadatas'][0]
            )
            
        except Exception as e:
            self.logger.error(f"获取知识块失败: {chunk_id}, 错误: {e}")
            return None
            
    async def get_documents_by_domain(self, domain: str) -> List[str]:
        """
        根据领域获取文档列表
        
        Args:
            domain: 领域名称
            
        Returns:
            List[str]: 文档ID列表
        """
        try:
            results = self.collection.get(
                where={"topics": domain},
                include=['metadatas']
            )
            
            # 提取唯一的文档ID
            document_ids = list(set(
                metadata.get('document_id', '') 
                for metadata in results['metadatas']
                if metadata.get('document_id')
            ))
            
            return document_ids
            
        except Exception as e:
            self.logger.error(f"获取领域文档失败: {domain}, 错误: {e}")
            return []
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            # 更新实时统计
            self.stats["total_chunks"] = self.collection.count()
            
            # 获取领域分布
            all_results = self.collection.get(include=['metadatas'])
            domain_counts = {}
            
            for metadata in all_results['metadatas']:
                topics = metadata.get('topics', [])
                for topic in topics:
                    domain_counts[topic] = domain_counts.get(topic, 0) + 1
                    
            self.stats["domain_distribution"] = domain_counts
            self.stats["unique_documents"] = len(set(
                metadata.get('document_id', '') 
                for metadata in all_results['metadatas']
                if metadata.get('document_id')
            ))
            
            return self.stats.copy()
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return self.stats.copy()
            
    async def backup_database(self, backup_path: str) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份路径
            
        Returns:
            bool: 是否备份成功
        """
        try:
            import shutil
            
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 备份ChromaDB数据
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"knowledge_db_backup_{timestamp}"
            
            shutil.copytree(
                self.persist_directory,
                backup_dir / backup_name
            )
            
            # 保存统计信息
            stats_file = backup_dir / f"stats_{timestamp}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.get_statistics(), f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"数据库备份完成: {backup_dir / backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库备份失败: {e}")
            return False
            
    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """生成知识块ID"""
        content = f"{document_id}_{chunk_index}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()
        
    async def reset_database(self) -> bool:
        """重置数据库（危险操作）"""
        try:
            self.chroma_client.reset()
            self._init_chromadb()
            
            self.stats = {
                "total_chunks": 0,
                "total_queries": 0,
                "last_updated": datetime.now().isoformat()
            }
            
            self.logger.warning("数据库已重置")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库重置失败: {e}")
            return False

# 使用示例
async def main():
    """测试向量数据库"""
    vector_store = VectorStore(persist_directory="test_knowledge_db")
    
    # 模拟文档解析结果进行测试
    from knowledge_ingestion.document_parser import DocumentParseResult, DocumentMetadata, ExtractedContent
    
    metadata = DocumentMetadata(
        file_path="test.txt",
        file_name="test.txt",
        file_type=".txt",
        file_size=1000,
        created_at=datetime.now().isoformat(),
        modified_at=datetime.now().isoformat(),
        title="测试文档"
    )
    
    contents = [
        ExtractedContent(
            content_id="test_1",
            content_type="text",
            content="人工智能是计算机科学的一个分支，它致力于创建能够模拟人类智能的机器。"
        ),
        ExtractedContent(
            content_id="test_2", 
            content_type="text",
            content="机器学习是人工智能的核心技术之一，通过算法让机器从数据中学习。"
        )
    ]
    
    parse_result = DocumentParseResult(
        document_id="test_doc_001",
        metadata=metadata,
        extracted_contents=contents,
        keywords=["人工智能", "机器学习", "算法"],
        topics=["人工智能", "计算机科学"]
    )
    
    try:
        # 添加文档
        chunk_count = await vector_store.add_document(parse_result)
        print(f"添加了 {chunk_count} 个知识块")
        
        # 测试搜索
        query = SearchQuery(
            query_text="什么是人工智能？",
            top_k=5
        )
        
        results = await vector_store.search(query)
        print(f"搜索到 {len(results)} 个结果:")
        
        for result in results:
            print(f"- 相似度: {result.similarity_score:.3f}")
            print(f"  内容: {result.chunk.content[:100]}...")
            
        # 获取统计信息
        stats = vector_store.get_statistics()
        print(f"统计信息: {stats}")
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())