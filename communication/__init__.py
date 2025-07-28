"""
AI自主开发系统 - 通信模块
提供角色间的标准化通信协议和消息总线功能
"""

from .message_protocol import (
    Message,
    MessageHeader, 
    MessageBody,
    MessageType,
    Priority,
    MessageStatus,
    MessageBuilder,
    MessageValidator,
    MessageTemplates
)

from .message_bus import (
    MessageBus,
    MessageRouter,
    MessageQueue,
    MessageTracker,
    logging_middleware,
    security_middleware
)

__all__ = [
    # Message Protocol
    'Message',
    'MessageHeader',
    'MessageBody', 
    'MessageType',
    'Priority',
    'MessageStatus',
    'MessageBuilder',
    'MessageValidator',
    'MessageTemplates',
    
    # Message Bus
    'MessageBus',
    'MessageRouter', 
    'MessageQueue',
    'MessageTracker',
    'logging_middleware',
    'security_middleware'
]

__version__ = '1.0.0'