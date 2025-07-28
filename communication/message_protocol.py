#!/usr/bin/env python3
"""
AI自主开发系统 - 消息通信协议
定义角色间通信的标准化消息格式和协议
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import uuid
import json


class MessageType(Enum):
    """消息类型枚举"""
    # 系统级消息
    SYSTEM_INIT = "system_init"
    SYSTEM_SHUTDOWN = "system_shutdown"
    HEALTH_CHECK = "health_check"
    STATUS_UPDATE = "status_update"
    
    # 任务相关消息
    TASK_ASSIGN = "task_assign"
    TASK_UPDATE = "task_update"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    
    # 请求/响应消息
    REQUEST = "request"
    RESPONSE = "response"
    QUERY = "query"
    NOTIFICATION = "notification"
    
    # 协作消息
    COLLABORATION_REQUEST = "collaboration_request"
    COLLABORATION_RESPONSE = "collaboration_response"
    RESOURCE_REQUEST = "resource_request"
    RESOURCE_RESPONSE = "resource_response"
    
    # 数据同步消息
    DATA_SYNC = "data_sync"
    STATE_SYNC = "state_sync"
    MEMORY_UPDATE = "memory_update"


class Priority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class MessageStatus(Enum):
    """消息状态"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    PROCESSED = "processed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class MessageHeader:
    """消息头部信息"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    priority: Priority = Priority.NORMAL
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    from_role: str = ""
    to_role: str = ""
    correlation_id: Optional[str] = None  # 用于关联请求和响应
    expires_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class MessageBody:
    """消息体"""
    action: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """标准消息结构"""
    header: MessageHeader
    body: MessageBody
    status: MessageStatus = MessageStatus.PENDING
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'header': {
                'message_id': self.header.message_id,
                'message_type': self.header.message_type.value,
                'priority': self.header.priority.value,
                'timestamp': self.header.timestamp,
                'from_role': self.header.from_role,
                'to_role': self.header.to_role,
                'correlation_id': self.header.correlation_id,
                'expires_at': self.header.expires_at,
                'retry_count': self.header.retry_count,
                'max_retries': self.header.max_retries
            },
            'body': {
                'action': self.body.action,
                'data': self.body.data,
                'context': self.body.context,
                'metadata': self.body.metadata
            },
            'status': self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息"""
        header = MessageHeader(
            message_id=data['header']['message_id'],
            message_type=MessageType(data['header']['message_type']),
            priority=Priority(data['header']['priority']),
            timestamp=data['header']['timestamp'],
            from_role=data['header']['from_role'],
            to_role=data['header']['to_role'],
            correlation_id=data['header'].get('correlation_id'),
            expires_at=data['header'].get('expires_at'),
            retry_count=data['header'].get('retry_count', 0),
            max_retries=data['header'].get('max_retries', 3)
        )
        
        body = MessageBody(
            action=data['body']['action'],
            data=data['body'].get('data', {}),
            context=data['body'].get('context', {}),
            metadata=data['body'].get('metadata', {})
        )
        
        return cls(
            header=header,
            body=body,
            status=MessageStatus(data.get('status', 'pending'))
        )
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class MessageBuilder:
    """消息构建器 - 提供便捷的消息创建方法"""
    
    @staticmethod
    def create_request(from_role: str, to_role: str, action: str, 
                      data: Dict[str, Any] = None, priority: Priority = Priority.NORMAL) -> Message:
        """创建请求消息"""
        header = MessageHeader(
            message_type=MessageType.REQUEST,
            priority=priority,
            from_role=from_role,
            to_role=to_role
        )
        
        body = MessageBody(
            action=action,
            data=data or {}
        )
        
        return Message(header=header, body=body)
    
    @staticmethod
    def create_response(request_message: Message, data: Dict[str, Any] = None, 
                       success: bool = True) -> Message:
        """创建响应消息"""
        header = MessageHeader(
            message_type=MessageType.RESPONSE,
            priority=request_message.header.priority,
            from_role=request_message.header.to_role,
            to_role=request_message.header.from_role,
            correlation_id=request_message.header.message_id
        )
        
        response_data = data or {}
        response_data['success'] = success
        
        body = MessageBody(
            action=f"{request_message.body.action}_response",
            data=response_data
        )
        
        return Message(header=header, body=body)
    
    @staticmethod
    def create_task_assignment(from_role: str, to_role: str, task_data: Dict[str, Any],
                             priority: Priority = Priority.NORMAL) -> Message:
        """创建任务分配消息"""
        header = MessageHeader(
            message_type=MessageType.TASK_ASSIGN,
            priority=priority,
            from_role=from_role,
            to_role=to_role
        )
        
        body = MessageBody(
            action="assign_task",
            data=task_data
        )
        
        return Message(header=header, body=body)
    
    @staticmethod
    def create_status_update(from_role: str, status_data: Dict[str, Any]) -> Message:
        """创建状态更新消息"""
        header = MessageHeader(
            message_type=MessageType.STATUS_UPDATE,
            priority=Priority.NORMAL,
            from_role=from_role,
            to_role="status_monitor"
        )
        
        body = MessageBody(
            action="update_status",
            data=status_data
        )
        
        return Message(header=header, body=body)
    
    @staticmethod
    def create_collaboration_request(from_role: str, to_role: str, 
                                   collaboration_type: str, details: Dict[str, Any]) -> Message:
        """创建协作请求消息"""
        header = MessageHeader(
            message_type=MessageType.COLLABORATION_REQUEST,
            priority=Priority.HIGH,
            from_role=from_role,
            to_role=to_role
        )
        
        body = MessageBody(
            action="request_collaboration",
            data={
                'collaboration_type': collaboration_type,
                'details': details
            }
        )
        
        return Message(header=header, body=body)


class MessageValidator:
    """消息验证器"""
    
    @staticmethod
    def validate_message(message: Message) -> tuple[bool, str]:
        """验证消息格式"""
        try:
            # 检查必填字段
            if not message.header.from_role:
                return False, "from_role不能为空"
            
            if not message.header.to_role:
                return False, "to_role不能为空"
            
            if not message.body.action:
                return False, "action不能为空"
            
            # 检查消息类型
            if not isinstance(message.header.message_type, MessageType):
                return False, "无效的消息类型"
            
            # 检查优先级
            if not isinstance(message.header.priority, Priority):
                return False, "无效的优先级"
            
            # 检查时间戳格式
            try:
                datetime.fromisoformat(message.header.timestamp.replace('Z', '+00:00'))
            except ValueError:
                return False, "无效的时间戳格式"
            
            return True, "消息格式有效"
            
        except Exception as e:
            return False, f"验证消息时发生错误: {e}"


# 预定义的常用消息模板
class MessageTemplates:
    """常用消息模板"""
    
    @staticmethod
    def system_initialization(from_role: str, project_config: Dict[str, Any]) -> Message:
        """系统初始化消息"""
        return MessageBuilder.create_request(
            from_role=from_role,
            to_role="master_controller",
            action="initialize_system",
            data={'project_config': project_config},
            priority=Priority.CRITICAL
        )
    
    @staticmethod
    def requirement_analysis(from_role: str, requirements: str) -> Message:
        """需求分析消息"""
        return MessageBuilder.create_request(
            from_role=from_role,
            to_role="requirements_parser",
            action="analyze_requirements",
            data={'requirements': requirements},
            priority=Priority.HIGH
        )
    
    @staticmethod
    def architecture_design(from_role: str, parsed_requirements: Dict[str, Any]) -> Message:
        """架构设计消息"""
        return MessageBuilder.create_request(
            from_role=from_role,
            to_role="system_architect",
            action="design_architecture",
            data={'requirements': parsed_requirements},
            priority=Priority.HIGH
        )
    
    @staticmethod
    def code_development(from_role: str, to_role: str, development_task: Dict[str, Any]) -> Message:
        """代码开发消息"""
        return MessageBuilder.create_task_assignment(
            from_role=from_role,
            to_role=to_role,
            task_data={
                'task_type': 'development',
                'specifications': development_task
            },
            priority=Priority.NORMAL
        )
    
    @staticmethod
    def testing_request(from_role: str, test_requirements: Dict[str, Any]) -> Message:
        """测试请求消息"""
        return MessageBuilder.create_request(
            from_role=from_role,
            to_role="test_engineer",
            action="create_test_plan",
            data={'test_requirements': test_requirements},
            priority=Priority.NORMAL
        )
    
    @staticmethod
    def memory_store(from_role: str, data_type: str, data: Dict[str, Any]) -> Message:
        """记忆存储消息"""
        return MessageBuilder.create_request(
            from_role=from_role,
            to_role="memory_manager",
            action="store_data",
            data={
                'data_type': data_type,
                'data': data
            },
            priority=Priority.NORMAL
        )
    
    @staticmethod
    def memory_retrieve(from_role: str, query: Dict[str, Any]) -> Message:
        """记忆检索消息"""  
        return MessageBuilder.create_request(
            from_role=from_role,
            to_role="memory_manager",
            action="retrieve_data",
            data={'query': query},
            priority=Priority.NORMAL
        )


# 使用示例
if __name__ == "__main__":
    # 创建一个请求消息
    message = MessageBuilder.create_request(
        from_role="master_controller",
        to_role="requirements_parser",
        action="parse_requirements",
        data={'requirements': '创建一个用户管理系统'},
        priority=Priority.HIGH
    )
    
    # 验证消息
    is_valid, validation_message = MessageValidator.validate_message(message)
    print(f"消息验证结果: {is_valid}, {validation_message}")
    
    # 输出消息JSON
    print("消息JSON:")
    print(message.to_json())
    
    # 创建响应消息
    response = MessageBuilder.create_response(
        request_message=message,
        data={'parsed_requirements': {'功能': '用户管理', '技术栈': 'Python'}},
        success=True
    )
    
    print("\n响应消息JSON:")
    print(response.to_json())