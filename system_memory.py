#!/usr/bin/env python3
"""
AI开发系统 - 系统记忆机制
让AI系统具备学习、记忆和自我优化能力
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
import hashlib

class MemoryType(Enum):
    """记忆类型枚举"""
    CORE = "core"                    # 核心记忆 - 系统基础能力
    PROJECT = "project"              # 项目记忆 - 特定项目经验
    LEARNING = "learning"            # 学习记忆 - 从开发过程学习
    EVOLUTION = "evolution"          # 进化记忆 - 系统自身改进

class LearningCategory(Enum):
    """学习类别枚举"""
    SUCCESS_PATTERN = "success_pattern"      # 成功模式
    FAILURE_LESSON = "failure_lesson"        # 失败教训
    OPTIMIZATION = "optimization"            # 优化经验
    BEST_PRACTICE = "best_practice"          # 最佳实践
    TECHNOLOGY_CHOICE = "technology_choice"   # 技术选择
    USER_FEEDBACK = "user_feedback"          # 用户反馈
    PERFORMANCE_INSIGHT = "performance_insight"  # 性能洞察

@dataclass
class MemoryEntry:
    """记忆条目数据类"""
    entry_id: str
    memory_type: MemoryType
    category: LearningCategory
    title: str
    description: str
    context: Dict[str, Any]
    outcome: str
    confidence: float  # 0.0-1.0, 记忆的可信度
    importance: int    # 1-10, 记忆的重要程度
    created_at: str
    last_accessed: str = ""
    access_count: int = 0
    tags: List[str] = None
    related_entries: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.related_entries is None:
            self.related_entries = []
        if not self.last_accessed:
            self.last_accessed = self.created_at

@dataclass
class SystemCapability:
    """系统能力记录"""
    capability_id: str
    name: str
    description: str
    version: str
    maturity_level: str  # experimental, stable, mature
    usage_count: int
    success_rate: float
    performance_metrics: Dict[str, float]
    improvement_suggestions: List[str]
    created_at: str
    last_updated: str = ""
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = self.created_at

class SystemMemoryManager:
    """系统记忆管理器"""
    
    def __init__(self, memory_root: str = None):
        self.memory_root = Path(memory_root) if memory_root else Path("system-memory")
        self.memory_root.mkdir(parents=True, exist_ok=True)
        
        # 记忆存储路径
        self.learning_dir = self.memory_root / "learning"
        self.knowledge_dir = self.memory_root / "knowledge"
        self.evolution_dir = self.memory_root / "evolution"
        
        # 确保子目录存在
        for directory in [self.learning_dir, self.knowledge_dir, self.evolution_dir]:
            directory.mkdir(exist_ok=True)
            
        # 设置日志
        self.logger = logging.getLogger('SystemMemoryManager')
        
        # 内存缓存
        self.memory_cache: Dict[str, MemoryEntry] = {}
        self.capabilities_cache: Dict[str, SystemCapability] = {}
        
        # 初始化记忆存储
        self._initialize_memory_storage()
        
        # 加载记忆到缓存
        self._load_memory_cache()
        
    def _initialize_memory_storage(self):
        """初始化记忆存储文件"""
        storage_files = {
            self.learning_dir / "successful_patterns.json": [],
            self.learning_dir / "failure_lessons.json": [],
            self.learning_dir / "optimization_records.json": [],
            self.knowledge_dir / "best_practices.json": [],
            self.knowledge_dir / "technology_stack.json": [],
            self.knowledge_dir / "domain_expertise.json": [],
            self.evolution_dir / "capability_growth.json": [],
            self.evolution_dir / "role_improvements.json": [],
            self.evolution_dir / "system_optimizations.json": []
        }
        
        for file_path, initial_data in storage_files.items():
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
                    
    def _load_memory_cache(self):
        """加载记忆到缓存"""
        try:
            # 加载学习记忆
            for memory_file in self.learning_dir.glob("*.json"):
                self._load_memory_file(memory_file, MemoryType.LEARNING)
                
            # 加载知识记忆
            for memory_file in self.knowledge_dir.glob("*.json"):
                self._load_memory_file(memory_file, MemoryType.CORE)
                
            # 加载进化记忆
            for memory_file in self.evolution_dir.glob("*.json"):
                self._load_memory_file(memory_file, MemoryType.EVOLUTION)
                
            self.logger.info(f"记忆缓存加载完成: {len(self.memory_cache)} 条记忆")
            
        except Exception as e:
            self.logger.error(f"记忆缓存加载失败: {e}")
            
    def _load_memory_file(self, file_path: Path, memory_type: MemoryType):
        """加载单个记忆文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
                
            for entry_data in memory_data:
                if isinstance(entry_data, dict) and 'entry_id' in entry_data:
                    # 转换枚举类型
                    entry_data['memory_type'] = MemoryType(entry_data.get('memory_type', memory_type.value))
                    entry_data['category'] = LearningCategory(entry_data.get('category', 'best_practice'))
                    
                    memory_entry = MemoryEntry(**entry_data)
                    self.memory_cache[memory_entry.entry_id] = memory_entry
                    
        except Exception as e:
            self.logger.error(f"加载记忆文件失败 {file_path}: {e}")
            
    def add_memory(self, 
                   memory_type: MemoryType,
                   category: LearningCategory,
                   title: str,
                   description: str,
                   context: Dict[str, Any],
                   outcome: str,
                   confidence: float = 0.8,
                   importance: int = 5,
                   tags: List[str] = None) -> str:
        """添加新的记忆条目"""
        try:
            entry_id = str(uuid.uuid4())
            
            memory_entry = MemoryEntry(
                entry_id=entry_id,
                memory_type=memory_type,
                category=category,
                title=title,
                description=description,
                context=context,
                outcome=outcome,
                confidence=confidence,
                importance=importance,
                created_at=datetime.now().isoformat(),
                tags=tags or []
            )
            
            # 添加到缓存
            self.memory_cache[entry_id] = memory_entry
            
            # 持久化存储
            self._persist_memory(memory_entry)
            
            # 更新相关记忆的关联
            self._update_memory_relationships(memory_entry)
            
            self.logger.info(f"新记忆已添加: {title} ({entry_id})")
            return entry_id
            
        except Exception as e:
            self.logger.error(f"添加记忆失败: {e}")
            raise
            
    def _persist_memory(self, memory_entry: MemoryEntry):
        """持久化记忆到文件"""
        # 根据记忆类型和类别选择存储文件
        storage_file = self._get_storage_file(memory_entry.memory_type, memory_entry.category)
        
        try:
            # 读取现有数据
            if storage_file.exists():
                with open(storage_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
                
            # 添加新记忆
            existing_data.append(asdict(memory_entry))
            
            # 写回文件
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"持久化记忆失败: {e}")
            
    def _get_storage_file(self, memory_type: MemoryType, category: LearningCategory) -> Path:
        """获取存储文件路径"""
        file_mapping = {
            (MemoryType.LEARNING, LearningCategory.SUCCESS_PATTERN): "learning/successful_patterns.json",
            (MemoryType.LEARNING, LearningCategory.FAILURE_LESSON): "learning/failure_lessons.json",
            (MemoryType.LEARNING, LearningCategory.OPTIMIZATION): "learning/optimization_records.json",
            (MemoryType.CORE, LearningCategory.BEST_PRACTICE): "knowledge/best_practices.json",
            (MemoryType.CORE, LearningCategory.TECHNOLOGY_CHOICE): "knowledge/technology_stack.json",
            (MemoryType.EVOLUTION, LearningCategory.OPTIMIZATION): "evolution/system_optimizations.json"
        }
        
        file_path = file_mapping.get((memory_type, category), "knowledge/domain_expertise.json")
        return self.memory_root / file_path
        
    def _update_memory_relationships(self, new_memory: MemoryEntry):
        """更新记忆关联关系"""
        # 基于标签和上下文寻找相关记忆
        related_entries = []
        
        for entry_id, existing_memory in self.memory_cache.items():
            if entry_id == new_memory.entry_id:
                continue
                
            # 检查标签重叠
            tag_overlap = set(new_memory.tags) & set(existing_memory.tags)
            if len(tag_overlap) >= 2:
                related_entries.append(entry_id)
                continue
                
            # 检查上下文相似性
            if self._calculate_context_similarity(new_memory.context, existing_memory.context) > 0.6:
                related_entries.append(entry_id)
                
        new_memory.related_entries = related_entries[:5]  # 最多保留5个相关记忆
        
    def _calculate_context_similarity(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> float:
        """计算上下文相似度"""
        # 简化的相似度计算
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
            
        similarity_score = 0.0
        for key in common_keys:
            if context1[key] == context2[key]:
                similarity_score += 1.0
                
        return similarity_score / len(set(context1.keys()) | set(context2.keys()))
        
    def query_memory(self, 
                     query: str = "",
                     memory_type: MemoryType = None,
                     category: LearningCategory = None,
                     tags: List[str] = None,
                     min_confidence: float = 0.0,
                     min_importance: int = 1,
                     limit: int = 10) -> List[MemoryEntry]:
        """查询记忆"""
        results = []
        
        for memory_entry in self.memory_cache.values():
            # 过滤条件
            if memory_type and memory_entry.memory_type != memory_type:
                continue
            if category and memory_entry.category != category:
                continue
            if memory_entry.confidence < min_confidence:
                continue
            if memory_entry.importance < min_importance:
                continue
                
            # 标签匹配
            if tags:
                if not set(tags) & set(memory_entry.tags):
                    continue
                    
            # 文本匹配
            if query:
                if query.lower() not in memory_entry.title.lower() and \
                   query.lower() not in memory_entry.description.lower():
                    continue
                    
            results.append(memory_entry)
            
            # 更新访问统计
            memory_entry.access_count += 1
            memory_entry.last_accessed = datetime.now().isoformat()
            
        # 按重要性和置信度排序
        results.sort(key=lambda x: (x.importance, x.confidence), reverse=True)
        
        return results[:limit]
        
    def learn_from_experience(self, 
                             project_id: str,
                             experience_type: str,
                             context: Dict[str, Any],
                             outcome: str,
                             success: bool) -> str:
        """从经验中学习"""
        
        # 确定学习类别
        category = LearningCategory.SUCCESS_PATTERN if success else LearningCategory.FAILURE_LESSON
        
        # 生成标题和描述
        title = f"{experience_type}{'成功' if success else '失败'}经验"
        description = f"在项目 {project_id} 中，{experience_type} 的{'成功' if success else '失败'}经验"
        
        # 设置置信度和重要性
        confidence = 0.9 if success else 0.8
        importance = 8 if success else 9  # 失败经验更重要
        
        # 添加标签
        tags = [project_id, experience_type, "automated_learning"]
        if success:
            tags.append("success")
        else:
            tags.append("failure")
            
        return self.add_memory(
            memory_type=MemoryType.LEARNING,
            category=category,
            title=title,
            description=description,
            context=context,
            outcome=outcome,
            confidence=confidence,
            importance=importance,
            tags=tags
        )
        
    def get_recommendations(self, current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """基于当前上下文获取建议"""
        recommendations = []
        
        # 查找相似上下文的成功经验
        for memory_entry in self.memory_cache.values():
            if memory_entry.category == LearningCategory.SUCCESS_PATTERN:
                similarity = self._calculate_context_similarity(current_context, memory_entry.context)
                
                if similarity > 0.5:
                    recommendations.append({
                        'type': 'success_pattern',
                        'title': memory_entry.title,
                        'description': memory_entry.description,
                        'outcome': memory_entry.outcome,
                        'confidence': memory_entry.confidence,
                        'similarity': similarity,
                        'tags': memory_entry.tags
                    })
                    
        # 查找相似上下文的失败教训
        for memory_entry in self.memory_cache.values():
            if memory_entry.category == LearningCategory.FAILURE_LESSON:
                similarity = self._calculate_context_similarity(current_context, memory_entry.context)
                
                if similarity > 0.4:
                    recommendations.append({
                        'type': 'failure_lesson',
                        'title': memory_entry.title,
                        'description': memory_entry.description,
                        'outcome': memory_entry.outcome,
                        'confidence': memory_entry.confidence,
                        'similarity': similarity,
                        'warning': '注意避免类似问题',
                        'tags': memory_entry.tags
                    })
                    
        # 按相似度和置信度排序
        recommendations.sort(key=lambda x: (x['similarity'], x['confidence']), reverse=True)
        
        return recommendations[:10]
        
    def record_system_improvement(self, improvement_type: str, description: str, metrics: Dict[str, float]):
        """记录系统改进"""
        context = {
            'improvement_type': improvement_type,
            'metrics_before': metrics.get('before', {}),
            'metrics_after': metrics.get('after', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        outcome = f"系统在{improvement_type}方面得到改进"
        
        return self.add_memory(
            memory_type=MemoryType.EVOLUTION,
            category=LearningCategory.OPTIMIZATION,
            title=f"系统{improvement_type}改进",
            description=description,
            context=context,
            outcome=outcome,
            confidence=0.9,
            importance=7,
            tags=[improvement_type, "system_improvement", "automated"]
        )
        
    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        stats = {
            'total_memories': len(self.memory_cache),
            'by_type': {},
            'by_category': {},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'importance_distribution': {},
            'most_accessed': [],
            'recent_memories': []
        }
        
        # 按类型统计
        for memory_entry in self.memory_cache.values():
            memory_type = memory_entry.memory_type.value
            stats['by_type'][memory_type] = stats['by_type'].get(memory_type, 0) + 1
            
            # 按类别统计
            category = memory_entry.category.value
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # 置信度分布
            if memory_entry.confidence >= 0.8:
                stats['confidence_distribution']['high'] += 1
            elif memory_entry.confidence >= 0.5:
                stats['confidence_distribution']['medium'] += 1
            else:
                stats['confidence_distribution']['low'] += 1
                
            # 重要性分布
            importance = str(memory_entry.importance)
            stats['importance_distribution'][importance] = stats['importance_distribution'].get(importance, 0) + 1
            
        # 最常访问的记忆
        most_accessed = sorted(self.memory_cache.values(), key=lambda x: x.access_count, reverse=True)
        stats['most_accessed'] = [
            {'title': m.title, 'access_count': m.access_count} 
            for m in most_accessed[:5]
        ]
        
        # 最近的记忆
        recent_memories = sorted(self.memory_cache.values(), key=lambda x: x.created_at, reverse=True)
        stats['recent_memories'] = [
            {'title': m.title, 'created_at': m.created_at} 
            for m in recent_memories[:5]
        ]
        
        return stats
        
    def cleanup_memory(self, max_age_days: int = 365, min_importance: int = 3):
        """清理过期或不重要的记忆"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        to_remove = []
        for entry_id, memory_entry in self.memory_cache.items():
            memory_date = datetime.fromisoformat(memory_entry.created_at.replace('Z', '+00:00'))
            
            # 删除过期且不重要的记忆
            if memory_date < cutoff_date and memory_entry.importance < min_importance:
                to_remove.append(entry_id)
                
        for entry_id in to_remove:
            del self.memory_cache[entry_id]
            
        self.logger.info(f"清理了 {len(to_remove)} 条过期记忆")
        
        # 重新持久化
        self._save_all_memories()
        
    def _save_all_memories(self):
        """保存所有记忆到文件"""
        # 按类型和类别分组
        memory_groups = {}
        
        for memory_entry in self.memory_cache.values():
            storage_file = self._get_storage_file(memory_entry.memory_type, memory_entry.category)
            
            if storage_file not in memory_groups:
                memory_groups[storage_file] = []
                
            memory_groups[storage_file].append(asdict(memory_entry))
            
        # 写入文件
        for storage_file, memories in memory_groups.items():
            try:
                with open(storage_file, 'w', encoding='utf-8') as f:
                    json.dump(memories, f, ensure_ascii=False, indent=2, default=str)
            except Exception as e:
                self.logger.error(f"保存记忆文件失败 {storage_file}: {e}")
                
    def export_memories(self, export_path: str) -> bool:
        """导出记忆到指定路径"""
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # 导出所有记忆
            all_memories = {
                'export_time': datetime.now().isoformat(),
                'total_count': len(self.memory_cache),
                'memories': [asdict(memory) for memory in self.memory_cache.values()],
                'statistics': self.get_memory_statistics()
            }
            
            export_file = export_dir / f"system_memories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(all_memories, f, ensure_ascii=False, indent=2, default=str)
                
            self.logger.info(f"记忆已导出到: {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出记忆失败: {e}")
            return False