#!/usr/bin/env python3
"""
智能行业知识问答系统 - 会话管理器
管理用户会话、对话历史和上下文连续性
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import uuid

@dataclass
class Message:
    """消息"""
    role: str  # 'user' 或 'assistant'
    content: str
    timestamp: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Session:
    """会话"""
    session_id: str
    user_id: str
    created_at: str
    last_active: str
    messages: List[Message]
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_active:
            self.last_active = self.created_at
        if self.context is None:
            self.context = {}

class SessionManager:
    """会话管理器"""
    
    def __init__(self, max_sessions: int = 1000, session_timeout_hours: int = 24):
        """
        初始化会话管理器
        
        Args:
            max_sessions: 最大会话数量
            session_timeout_hours: 会话超时时间(小时)
        """
        self.max_sessions = max_sessions
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self.sessions: Dict[str, Session] = {}
        self.logger = logging.getLogger(__name__)
        
    def create_session(self, user_id: str, session_id: str = None) -> str:
        """
        创建新会话
        
        Args:
            user_id: 用户ID
            session_id: 可选的会话ID，如果不提供则自动生成
            
        Returns:
            str: 会话ID
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat(),
            messages=[]
        )
        
        self.sessions[session_id] = session
        self.logger.info(f"创建新会话: {session_id} (用户: {user_id})")
        
        # 清理过期会话
        self._cleanup_expired_sessions()
        
        return session_id
        
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Session]: 会话对象，如果不存在则返回None
        """
        session = self.sessions.get(session_id)
        
        if session:
            # 检查是否过期
            last_active = datetime.fromisoformat(session.last_active)
            if datetime.now() - last_active > self.session_timeout:
                self.logger.info(f"会话已过期: {session_id}")
                del self.sessions[session_id]
                return None
                
            # 更新最后活跃时间
            session.last_active = datetime.now().isoformat()
            
        return session
        
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        添加消息到会话
        
        Args:
            session_id: 会话ID
            role: 角色 ('user' 或 'assistant')
            content: 消息内容
            metadata: 消息元数据
            
        Returns:
            bool: 是否成功添加
        """
        session = self.get_session(session_id)
        if not session:
            self.logger.warning(f"会话不存在: {session_id}")
            return False
            
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.last_active = datetime.now().isoformat()
        
        self.logger.debug(f"添加消息到会话 {session_id}: {role}")
        return True
        
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        获取对话历史
        
        Args:
            session_id: 会话ID
            limit: 最大消息数量
            
        Returns:
            List[Dict[str, str]]: 对话历史
        """
        session = self.get_session(session_id)
        if not session:
            return []
            
        # 获取最近的消息
        recent_messages = session.messages[-limit:] if limit > 0 else session.messages
        
        # 转换为对话历史格式
        history = []
        for message in recent_messages:
            history.append({
                message.role: message.content,
                "timestamp": message.timestamp
            })
            
        return history
        
    def get_context_for_question(self, session_id: str, question: str) -> Dict[str, Any]:
        """
        为问题获取上下文
        
        Args:
            session_id: 会话ID
            question: 用户问题
            
        Returns:
            Dict[str, Any]: 上下文信息
        """
        session = self.get_session(session_id)
        if not session:
            return {}
            
        # 获取对话历史
        history = self.get_conversation_history(session_id, limit=6)  # 最近3轮对话
        
        # 构建上下文
        context = {
            "session_id": session_id,
            "user_id": session.user_id,
            "conversation_history": history,
            "session_context": session.context.copy(),
            "message_count": len(session.messages)
        }
        
        # 分析问题中的上下文线索
        context["question_analysis"] = self._analyze_question_context(question, history)
        
        return context
        
    def _analyze_question_context(self, question: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """分析问题的上下文线索"""
        analysis = {
            "has_reference": False,
            "reference_type": None,
            "related_topics": []
        }
        
        # 检查问题中的指代词
        reference_words = ["它", "这个", "那个", "刚才", "上面", "前面", "这", "那", "这些", "那些"]
        if any(word in question for word in reference_words):
            analysis["has_reference"] = True
            analysis["reference_type"] = "pronoun"
            
        # 检查问题中的"继续"、"详细"等词
        continuation_words = ["继续", "详细", "更多", "进一步", "具体", "比如", "例如"]
        if any(word in question for word in continuation_words):
            analysis["has_reference"] = True
            analysis["reference_type"] = "continuation"
            
        # 从历史中提取相关主题
        if history:
            last_messages = history[-2:]  # 最近一轮对话
            for msg in last_messages:
                if 'assistant' in msg:
                    # 简单的主题提取（可以用更复杂的NLP方法）
                    content = msg['assistant']
                    # 提取可能的主题词（这里简化处理）
                    if len(content) > 50:
                        analysis["related_topics"].append(content[:100])
                        
        return analysis
        
    def update_session_context(self, session_id: str, key: str, value: Any) -> bool:
        """
        更新会话上下文
        
        Args:
            session_id: 会话ID
            key: 上下文键
            value: 上下文值
            
        Returns:
            bool: 是否成功更新
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        session.context[key] = value
        session.last_active = datetime.now().isoformat()
        return True
        
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            last_active = datetime.fromisoformat(session.last_active)
            if current_time - last_active > self.session_timeout:
                expired_sessions.append(session_id)
                
        for session_id in expired_sessions:
            del self.sessions[session_id]
            self.logger.info(f"清理过期会话: {session_id}")
            
        # 如果会话数量过多，删除最旧的会话
        if len(self.sessions) > self.max_sessions:
            # 按最后活跃时间排序
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].last_active
            )
            
            # 删除最旧的会话
            sessions_to_remove = len(self.sessions) - self.max_sessions
            for i in range(sessions_to_remove):
                session_id = sorted_sessions[i][0]
                del self.sessions[session_id]
                self.logger.info(f"清理旧会话: {session_id}")
                
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """
        获取用户的所有会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Session]: 用户会话列表
        """
        user_sessions = []
        for session in self.sessions.values():
            if session.user_id == user_id:
                user_sessions.append(session)
                
        # 按最后活跃时间排序
        user_sessions.sort(key=lambda x: x.last_active, reverse=True)
        return user_sessions
        
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功删除
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"删除会话: {session_id}")
            return True
        return False
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        active_sessions = len(self.sessions)
        
        # 统计用户分布
        user_counts = {}
        total_messages = 0
        
        for session in self.sessions.values():
            user_id = session.user_id
            user_counts[user_id] = user_counts.get(user_id, 0) + 1
            total_messages += len(session.messages)
            
        return {
            "active_sessions": active_sessions,
            "total_users": len(user_counts),
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / max(active_sessions, 1)
        }

# 全局会话管理器实例
global_session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """获取全局会话管理器"""
    return global_session_manager