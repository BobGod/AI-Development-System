#!/usr/bin/env python3
"""
AI自主开发系统 - 记忆管理器 (简化版)
负责存储、管理和检索整个项目开发过程中的所有历史信息、上下文和知识
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
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
    """记忆管理器 - 系统的记忆中心 (简化版)"""
    
    def __init__(self, role_id: str = "memory_manager", config: Dict[str, Any] = None):
        super().__init__(role_id, "记忆管理器", config)
        
        # 存储配置
        self.storage_path = Path(config.get('storage_path', 'data/memory') if config else 'data/memory')
        
        # 内存存储
        self.memory_store: Dict[str, MemoryEntry] = {}
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
            history = self._get_recent_entries(10)  # 简化版，返回最近10条
            
            response_data = {
                'status': 'retrieved',
                'history': [self._memory_entry_to_dict(entry) for entry in history],
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
            
            # 存储到内存
            self.memory_store[entry_id] = entry
            
            # 更新缓存
            self._update_cache(entry)
            
            # 更新搜索索引
            self._update_search_index(entry)
            
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
            
    def _update_search_index(self, entry: MemoryEntry):
        """更新搜索索引"""
        try:
            # 提取关键词
            keywords = self._extract_keywords(entry)
            
            for keyword in keywords:
                if keyword not in self.search_index:
                    self.search_index[keyword] = []
                self.search_index[keyword].append(entry.id)
                
        except Exception as e:
            self.logger.error(f"更新搜索索引失败: {e}")
            
    def _extract_keywords(self, entry: MemoryEntry) -> List[str]:
        """提取关键词"""
        keywords = set()
        
        # 从内容提取关键词
        content_str = json.dumps(entry.content, ensure_ascii=False)
        # 简化的关键词提取
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
            results = []
            
            # 从内存存储中搜索
            for entry in self.memory_store.values():
                if self._match_query(entry, query):
                    results.append(entry)
                    
            # 按时间排序，最新的在前
            results.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 限制结果数量
            limit = query.get('limit', 100)
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"检索记忆失败: {e}")
            return []
            
    def _match_query(self, entry: MemoryEntry, query: Dict[str, Any]) -> bool:
        """检查条目是否匹配查询条件"""
        # 检查数据类型
        if 'data_type' in query and entry.data_type.value != query['data_type']:
            return False
            
        # 检查源角色
        if 'source_role' in query and entry.source_role != query['source_role']:
            return False
            
        # 检查重要性
        if 'importance_min' in query and entry.importance < query['importance_min']:
            return False
            
        # 检查时间范围
        if 'time_range' in query:
            time_range = query['time_range']
            if 'start' in time_range:
                start_time = datetime.fromisoformat(time_range['start'])
                if entry.timestamp < start_time:
                    return False
            if 'end' in time_range:
                end_time = datetime.fromisoformat(time_range['end'])
                if entry.timestamp > end_time:
                    return False
                    
        return True
        
    def _get_recent_entries(self, limit: int = 10) -> List[MemoryEntry]:
        """获取最近的条目"""
        return self.recent_entries[:limit]
        
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
                'total_memories': len(self.memory_store),
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
            for keyword in keywords:
                if keyword in self.search_index:
                    entry_ids = self.search_index[keyword]
                    for entry_id in entry_ids:
                        if entry_id in self.memory_store:
                            entry = self.memory_store[entry_id]
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
                await asyncio.sleep(300)  # 5分钟备份一次
                await self._create_backup()
                
            except Exception as e:
                self.logger.error(f"定期备份失败: {e}")
                
    async def _create_backup(self):
        """创建备份"""
        try:
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'memory_store': {k: asdict(v) for k, v in self.memory_store.items()},
                'project_timeline': self.project_timeline,
                'current_project': self.current_project
            }
            
            backup_file = self.storage_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"创建备份: {backup_file}")
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            
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
                'active_roles': len(self.role_status) if hasattr(self, 'role_status') else 0,
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
                'total_memories': len(self.memory_store),
                'recent_activities': len([e for e in self.recent_entries if e.timestamp > datetime.now() - timedelta(hours=24)]),
                'key_decisions': len([e for e in self.recent_entries if e.data_type == DataType.DECISION])
            }
            
            return {'status': 'created', 'summary': summary}
            
        except Exception as e:
            raise Exception(f"创建摘要任务失败: {e}")