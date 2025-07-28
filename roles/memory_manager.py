#!/usr/bin/env python3
"""
AI自主开发系统 - 记忆管理器
负责存储、管理和检索整个项目开发过程中的所有历史信息、上下文和知识
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
# import sqlite3
# import aiosqlite
from dataclasses import dataclass
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roles.base_role import BaseRole, Task, TaskStatus
from communication import Message, MessageBuilder, MessageType, Priority


class DataType(Enum):
    """数据类型枚举"""
    PROJECT_INFO = "project_info"
    COMMUNICATION = "communication"
    DECISION = "decision"
    CODE_CHANGE = "code_change"
    ISSUE_SOLUTION = "issue_solution"
    MILESTONE = "milestone"
    KNOWLEDGE = "knowledge"
    CONTEXT = "context"


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    data_type: DataType
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
    source_role: str
    importance: int = 5  # 1-10, 10最重要
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class MemoryManager(BaseRole):
    """记忆管理器 - 系统的记忆中心"""
    
    def __init__(self, role_id: str = "memory_manager", config: Dict[str, Any] = None):
        super().__init__(role_id, "记忆管理器", config)
        
        # 存储配置
        self.storage_path = Path(config.get('storage_path', 'data/memory') if config else 'data/memory')
        self.db_path = self.storage_path / 'memory.db'
        self.backup_interval = config.get('backup_interval', 300) if config else 300  # 5分钟
        
        # 内存缓存
        self.memory_cache: Dict[str, MemoryEntry] = {}
        self.recent_entries: List[MemoryEntry] = []
        self.max_cache_size = 1000
        
        # 项目上下文
        self.current_project: Optional[Dict[str, Any]] = None
        self.project_timeline: List[Dict[str, Any]] = []
        
        # 知识库
        self.knowledge_base: Dict[str, Dict[str, Any]] = {
            'best_practices': {},
            'solutions': {},
            'patterns': {},
            'decisions': {}
        }
        
        # 搜索索引
        self.search_index: Dict[str, List[str]] = {}  # keyword -> entry_ids
        
        # 注册专用消息处理器
        self.message_handlers.update({
            'initialize_project_context': self._handle_initialize_project,
            'store_data': self._handle_store_data,
            'retrieve_data': self._handle_retrieve_data,
            'query_history': self._handle_query_history,
            'update_context': self._handle_update_context,
            'create_snapshot': self._handle_create_snapshot,
            'search_knowledge': self._handle_search_knowledge
        })
        
    async def _initialize_role(self):
        """初始化记忆管理器"""
        self.logger.info("初始化记忆管理器")
        
        # 创建存储目录
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化数据库
        await self._init_database()
        
        # 加载缓存
        await self._load_cache()
        
        # 启动定期备份任务
        asyncio.create_task(self._periodic_backup())
        
        # 启动缓存清理任务
        asyncio.create_task(self._periodic_cache_cleanup())
        
    async def _cleanup_role(self):
        """清理记忆管理器"""
        self.logger.info("清理记忆管理器")
        
        # 执行最后一次备份
        await self._create_backup()
        
    async def _handle_custom_message(self, message: Message):
        """处理自定义消息"""
        self.logger.warning(f"收到未知消息类型: {message.body.action}")
        
    async def _process_task(self, task: Task) -> Dict[str, Any]:
        """处理任务"""
        task_type = task.task_type
        
        if task_type == "store_memory":
            return await self._store_memory_task(task)
        elif task_type == "retrieve_memory":
            return await self._retrieve_memory_task(task)
        elif task_type == "analyze_context":
            return await self._analyze_context_task(task)
        elif task_type == "create_summary":
            return await self._create_summary_task(task)
        else:
            raise ValueError(f"未知任务类型: {task_type}")
            
    async def _init_database(self):
        """初始化数据库 - 使用内存存储"""
        # 简化实现，使用内存存储而不是SQLite
        self.memory_entries_db = {}
        self.search_index_db = {}
        self.project_context_db = {}
        self.logger.info("使用内存数据库初始化完成")
            
    async def _load_cache(self):
        """加载缓存 - 内存版本"""
        try:
            # 从内存数据库加载到缓存
            for entry_id, entry_data in self.memory_entries_db.items():
                entry = MemoryEntry(**entry_data)
                self.memory_cache[entry.id] = entry
                self.recent_entries.append(entry)
                
            self.logger.info(f"加载了 {len(self.memory_entries_db)} 个记忆条目到缓存")
                
        except Exception as e:
            self.logger.error(f"加载缓存失败: {e}")
            
    def _row_to_memory_entry(self, row) -> MemoryEntry:
        """将数据库行转换为记忆条目"""
        return MemoryEntry(
            id=row[0],
            data_type=DataType(row[1]),
            content=json.loads(row[2]),
            metadata=json.loads(row[3]),
            timestamp=datetime.fromisoformat(row[4]),
            source_role=row[5],
            importance=row[6],
            tags=json.loads(row[7])
        )
        
    async def _handle_initialize_project(self, message: Message):
        """处理项目初始化"""
        try:
            project_data = message.body.data
            self.current_project = project_data.get('project_config', {})
            
            # 存储项目信息
            await self._store_memory(
                data_type=DataType.PROJECT_INFO,
                content=self.current_project,
                metadata={
                    'initialization_time': datetime.now().isoformat(),
                    'session_id': project_data.get('session_id', 'unknown')
                },
                source_role=message.header.from_role,
                importance=10,
                tags=['project', 'initialization']
            )
            
            # 创建项目时间线的第一个条目
            timeline_entry = {
                'event': 'project_initialized',
                'timestamp': datetime.now().isoformat(),
                'description': f"项目 '{self.current_project.get('name', 'Unknown')}' 初始化",
                'metadata': project_data
            }
            self.project_timeline.append(timeline_entry)
            
            response_data = {
                'status': 'initialized',
                'project_name': self.current_project.get('name', 'Unknown'),
                'memory_entry_id': f"project_init_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"项目初始化失败: {e}")
            
    async def _handle_store_data(self, message: Message):
        """处理数据存储请求"""
        try:
            data = message.body.data
            data_type = DataType(data.get('data_type', DataType.CONTEXT.value))
            content = data.get('data', {})
            metadata = data.get('metadata', {})
            importance = data.get('importance', 5)
            tags = data.get('tags', [])
            
            entry_id = await self._store_memory(
                data_type=data_type,
                content=content,
                metadata=metadata,
                source_role=message.header.from_role,
                importance=importance,
                tags=tags
            )
            
            response_data = {
                'status': 'stored',
                'entry_id': entry_id,
                'data_type': data_type.value
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"数据存储失败: {e}")
            
    async def _handle_retrieve_data(self, message: Message):
        """处理数据检索请求"""
        try:
            query = message.body.data.get('query', {})
            results = await self._retrieve_memories(query)
            
            response_data = {
                'status': 'retrieved',
                'results': [self._memory_entry_to_dict(entry) for entry in results],
                'count': len(results)
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"数据检索失败: {e}")
            
    async def _handle_query_history(self, message: Message):
        """处理历史查询请求"""
        try:
            query_params = message.body.data
            time_range = query_params.get('time_range', {})
            role_filter = query_params.get('role_filter')
            data_type_filter = query_params.get('data_type_filter')
            
            history = await self._query_history(time_range, role_filter, data_type_filter)
            
            response_data = {
                'status': 'retrieved',
                'history': history,
                'count': len(history)
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"历史查询失败: {e}")
            
    async def _handle_update_context(self, message: Message):
        """处理上下文更新请求"""
        try:
            context_data = message.body.data
            
            # 更新项目上下文
            if 'project_context' in context_data:
                if self.current_project:
                    self.current_project.update(context_data['project_context'])
                else:
                    self.current_project = context_data['project_context']
                    
            # 添加到时间线
            if 'timeline_event' in context_data:
                self.project_timeline.append(context_data['timeline_event'])
                
            # 存储上下文更新
            await self._store_memory(
                data_type=DataType.CONTEXT,
                content=context_data,
                metadata={'update_type': 'context_update'},
                source_role=message.header.from_role,
                importance=7
            )
            
            response_data = {
                'status': 'updated',
                'timestamp': datetime.now().isoformat()
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"上下文更新失败: {e}")
            
    async def _handle_create_snapshot(self, message: Message):
        """处理创建快照请求"""
        try:
            snapshot_data = await self._create_project_snapshot()
            
            # 存储快照
            await self._store_memory(
                data_type=DataType.MILESTONE,
                content=snapshot_data,
                metadata={'snapshot_type': 'project_state'},
                source_role=message.header.from_role,
                importance=9,
                tags=['snapshot', 'milestone']
            )
            
            response_data = {
                'status': 'created',
                'snapshot_id': snapshot_data['snapshot_id'],
                'timestamp': snapshot_data['timestamp']
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"创建快照失败: {e}")
            
    async def _handle_search_knowledge(self, message: Message):
        """处理知识搜索请求"""
        try:
            search_query = message.body.data.get('query', '')
            search_type = message.body.data.get('type', 'general')
            
            results = await self._search_knowledge_base(search_query, search_type)
            
            response_data = {
                'status': 'searched',
                'results': results,
                'query': search_query,
                'count': len(results)
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"知识搜索失败: {e}")
            
    async def _store_memory(self, data_type: DataType, content: Dict[str, Any],
                           metadata: Dict[str, Any], source_role: str,
                           importance: int = 5, tags: List[str] = None) -> str:
        """存储记忆条目"""
        try:
            # 创建记忆条目
            entry_id = f"{data_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
            entry = MemoryEntry(
                id=entry_id,
                data_type=data_type,
                content=content,
                metadata=metadata,
                timestamp=datetime.now(),
                source_role=source_role,
                importance=importance,
                tags=tags or []
            )
            
            # 存储到数据库
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO memory_entries 
                    (id, data_type, content, metadata, timestamp, source_role, importance, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.id,
                    entry.data_type.value,
                    json.dumps(entry.content, ensure_ascii=False),
                    json.dumps(entry.metadata, ensure_ascii=False),
                    entry.timestamp.isoformat(),
                    entry.source_role,
                    entry.importance,
                    json.dumps(entry.tags, ensure_ascii=False)
                ))
                
                await db.commit()
                
            # 更新缓存
            self._update_cache(entry)
            
            # 更新搜索索引
            await self._update_search_index(entry)
            
            self.logger.debug(f"存储记忆条目: {entry_id}")
            return entry_id
            
        except Exception as e:
            self.logger.error(f"存储记忆失败: {e}")
            raise
            
    def _update_cache(self, entry: MemoryEntry):
        """更新缓存"""
        # 添加到缓存
        self.memory_cache[entry.id] = entry
        self.recent_entries.insert(0, entry)
        
        # 限制缓存大小
        if len(self.recent_entries) > self.max_cache_size:
            removed_entry = self.recent_entries.pop()
            self.memory_cache.pop(removed_entry.id, None)
            
    async def _update_search_index(self, entry: MemoryEntry):
        """更新搜索索引"""
        try:
            # 提取关键词
            keywords = self._extract_keywords(entry)
            
            async with aiosqlite.connect(self.db_path) as db:
                for keyword in keywords:
                    await db.execute('''
                        INSERT OR REPLACE INTO search_index (keyword, entry_id, relevance)
                        VALUES (?, ?, ?)
                    ''', (keyword.lower(), entry.id, 1.0))
                    
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"更新搜索索引失败: {e}")
            
    def _extract_keywords(self, entry: MemoryEntry) -> List[str]:
        """提取关键词"""
        keywords = set()
        
        # 从内容提取关键词
        content_str = json.dumps(entry.content, ensure_ascii=False)
        # 简化的关键词提取（实际应用中可以使用更复杂的NLP技术）
        words = content_str.lower().split()
        keywords.update([word for word in words if len(word) > 2])
        
        # 添加标签
        keywords.update([tag.lower() for tag in entry.tags])
        
        # 添加数据类型
        keywords.add(entry.data_type.value)
        
        return list(keywords)
        
    async def _retrieve_memories(self, query: Dict[str, Any]) -> List[MemoryEntry]:
        """检索记忆"""
        try:
            conditions = []
            params = []
            
            # 构建查询条件
            if 'data_type' in query:
                conditions.append('data_type = ?')
                params.append(query['data_type'])
                
            if 'source_role' in query:
                conditions.append('source_role = ?')
                params.append(query['source_role'])
                
            if 'importance_min' in query:
                conditions.append('importance >= ?')
                params.append(query['importance_min'])
                
            if 'time_range' in query:
                time_range = query['time_range']
                if 'start' in time_range:
                    conditions.append('timestamp >= ?')
                    params.append(time_range['start'])
                if 'end' in time_range:
                    conditions.append('timestamp <= ?')
                    params.append(time_range['end'])
                    
            # 构建SQL查询
            where_clause = ' AND '.join(conditions) if conditions else '1=1'
            limit = query.get('limit', 100)
            
            sql = f'''
                SELECT * FROM memory_entries 
                WHERE {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ?
            '''
            params.append(limit)
            
            # 执行查询
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(sql, params)
                rows = await cursor.fetchall()
                
            return [self._row_to_memory_entry(row) for row in rows]
            
        except Exception as e:
            self.logger.error(f"检索记忆失败: {e}")
            return []
            
    async def _query_history(self, time_range: Dict[str, str], 
                           role_filter: Optional[str] = None,
                           data_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """查询历史记录"""
        query = {}
        
        if time_range:
            query['time_range'] = time_range
        if role_filter:
            query['source_role'] = role_filter
        if data_type_filter:
            query['data_type'] = data_type_filter
            
        entries = await self._retrieve_memories(query)
        return [self._memory_entry_to_dict(entry) for entry in entries]
        
    def _memory_entry_to_dict(self, entry: MemoryEntry) -> Dict[str, Any]:
        """将记忆条目转换为字典"""
        return {
            'id': entry.id,
            'data_type': entry.data_type.value,
            'content': entry.content,
            'metadata': entry.metadata,
            'timestamp': entry.timestamp.isoformat(),
            'source_role': entry.source_role,
            'importance': entry.importance,
            'tags': entry.tags
        }
        
    async def _create_project_snapshot(self) -> Dict[str, Any]:
        """创建项目快照"""
        snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snapshot = {
            'snapshot_id': snapshot_id,
            'timestamp': datetime.now().isoformat(),
            'project_info': self.current_project,
            'timeline': self.project_timeline[-10:],  # 最近10个事件
            'statistics': {
                'total_memories': len(self.memory_cache),
                'timeline_events': len(self.project_timeline),
                'active_since': self.stats['uptime_start'].isoformat()
            }
        }
        
        return snapshot
        
    async def _search_knowledge_base(self, query: str, search_type: str) -> List[Dict[str, Any]]:
        """搜索知识库"""
        try:
            keywords = query.lower().split()
            results = []
            
            # 搜索记忆条目
            async with aiosqlite.connect(self.db_path) as db:
                for keyword in keywords:
                    cursor = await db.execute('''
                        SELECT me.* FROM memory_entries me
                        JOIN search_index si ON me.id = si.entry_id
                        WHERE si.keyword LIKE ?
                        ORDER BY si.relevance DESC, me.importance DESC
                        LIMIT 20
                    ''', (f'%{keyword}%',))
                    
                    rows = await cursor.fetchall()
                    for row in rows:
                        entry = self._row_to_memory_entry(row)
                        if entry.id not in [r['id'] for r in results]:
                            results.append(self._memory_entry_to_dict(entry))
                            
            return results[:50]  # 限制返回结果数量
            
        except Exception as e:
            self.logger.error(f"搜索知识库失败: {e}")
            return []
            
    async def _periodic_backup(self):
        """定期备份"""
        while self.running:
            try:
                await asyncio.sleep(self.backup_interval)
                await self._create_backup()
                
            except Exception as e:
                self.logger.error(f"定期备份失败: {e}")
                
    async def _create_backup(self):
        """创建备份"""
        try:
            backup_path = self.storage_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            # 复制数据库文件
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            self.logger.info(f"创建备份: {backup_path}")
            
            # 清理旧备份（保留最近7天）
            await self._cleanup_old_backups()
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            
    async def _cleanup_old_backups(self):
        """清理旧备份"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for backup_file in self.storage_path.glob("backup_*.db"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    self.logger.debug(f"删除旧备份: {backup_file}")
                    
        except Exception as e:
            self.logger.error(f"清理旧备份失败: {e}")
            
    async def _periodic_cache_cleanup(self):
        """定期缓存清理"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次
                
                # 移除重要性较低的旧条目
                cutoff_time = datetime.now() - timedelta(hours=24)
                to_remove = []
                
                for entry_id, entry in self.memory_cache.items():
                    if entry.timestamp < cutoff_time and entry.importance < 7:
                        to_remove.append(entry_id)
                        
                for entry_id in to_remove:
                    self.memory_cache.pop(entry_id, None)
                    
                # 重建recent_entries列表
                self.recent_entries = [
                    entry for entry in self.recent_entries 
                    if entry.id in self.memory_cache
                ]
                
                if to_remove:
                    self.logger.info(f"清理了 {len(to_remove)} 个缓存条目")
                    
            except Exception as e:
                self.logger.error(f"缓存清理失败: {e}")
                
    # 任务处理方法
    async def _store_memory_task(self, task: Task) -> Dict[str, Any]:
        """存储记忆任务"""
        try:
            data = task.data
            entry_id = await self._store_memory(
                data_type=DataType(data['data_type']),
                content=data['content'],
                metadata=data.get('metadata', {}),
                source_role=data['source_role'],
                importance=data.get('importance', 5),
                tags=data.get('tags', [])
            )
            
            return {'status': 'stored', 'entry_id': entry_id}
            
        except Exception as e:
            raise Exception(f"存储记忆任务失败: {e}")
            
    async def _retrieve_memory_task(self, task: Task) -> Dict[str, Any]:
        """检索记忆任务"""
        try:
            query = task.data.get('query', {})
            results = await self._retrieve_memories(query)
            
            return {
                'status': 'retrieved',
                'results': [self._memory_entry_to_dict(entry) for entry in results],
                'count': len(results)
            }
            
        except Exception as e:
            raise Exception(f"检索记忆任务失败: {e}")
            
    async def _analyze_context_task(self, task: Task) -> Dict[str, Any]:
        """分析上下文任务"""
        try:
            # 简化的上下文分析
            analysis = {
                'project_phase': 'development',
                'active_roles': len(self.role_status),
                'recent_activities': len(self.recent_entries),
                'context_completeness': 0.8
            }
            
            return {'status': 'analyzed', 'analysis': analysis}
            
        except Exception as e:
            raise Exception(f"分析上下文任务失败: {e}")
            
    async def _create_summary_task(self, task: Task) -> Dict[str, Any]:
        """创建摘要任务"""
        try:
            # 简化的摘要创建
            summary = {
                'project_name': self.current_project.get('name', 'Unknown') if self.current_project else 'Unknown',
                'total_memories': len(self.memory_cache),
                'recent_activities': len([e for e in self.recent_entries if e.timestamp > datetime.now() - timedelta(hours=24)]),
                'key_decisions': len([e for e in self.recent_entries if e.data_type == DataType.DECISION])
            }
            
            return {'status': 'created', 'summary': summary}
            
        except Exception as e:
            raise Exception(f"创建摘要任务失败: {e}")