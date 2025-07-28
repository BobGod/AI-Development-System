#!/usr/bin/env python3
"""
AI自主开发系统 - 消息总线
实现角色间的可靠消息传递、路由和管理
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import weakref

try:
    from .message_protocol import Message, MessageType, Priority, MessageStatus, MessageValidator
except ImportError:
    from message_protocol import Message, MessageType, Priority, MessageStatus, MessageValidator


class MessageRouter:
    """消息路由器 - 负责消息的路由和分发"""
    
    def __init__(self):
        self.routes: Dict[str, Set[str]] = defaultdict(set)  # role -> subscribers
        self.role_handlers: Dict[str, Callable] = {}  # role -> message handler
        self.middleware: List[Callable] = []  # 中间件处理器
        
    def register_role(self, role_id: str, handler: Callable):
        """注册角色消息处理器"""
        self.role_handlers[role_id] = handler
        
    def unregister_role(self, role_id: str):
        """注销角色"""
        if role_id in self.role_handlers:
            del self.role_handlers[role_id]
        
        # 清理路由表
        for subscribers in self.routes.values():
            subscribers.discard(role_id)
            
    def subscribe(self, subscriber_role: str, target_role: str):
        """订阅目标角色的消息"""
        self.routes[target_role].add(subscriber_role)
        
    def unsubscribe(self, subscriber_role: str, target_role: str):
        """取消订阅"""
        self.routes[target_role].discard(subscriber_role)
        
    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self.middleware.append(middleware)
        
    async def route_message(self, message: Message) -> List[str]:
        """路由消息到目标角色"""
        target_roles = []
        
        # 直接发送给目标角色
        if message.header.to_role in self.role_handlers:
            target_roles.append(message.header.to_role)
            
        # 发送给订阅者
        subscribers = self.routes.get(message.header.from_role, set())
        target_roles.extend(subscribers)
        
        return list(set(target_roles))  # 去重
        
    async def apply_middleware(self, message: Message) -> Message:
        """应用中间件处理"""
        for middleware in self.middleware:
            message = await middleware(message)
        return message


class MessageQueue:
    """消息队列 - 实现优先级队列和消息持久化"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues: Dict[Priority, deque] = {
            Priority.CRITICAL: deque(),
            Priority.URGENT: deque(),
            Priority.HIGH: deque(),
            Priority.NORMAL: deque(),
            Priority.LOW: deque()
        }
        self.size = 0
        self.lock = asyncio.Lock()
        
    async def put(self, message: Message) -> bool:
        """添加消息到队列"""
        async with self.lock:
            if self.size >= self.max_size:
                # 队列满时，丢弃最低优先级的消息
                if not await self._make_space():
                    return False
                    
            priority = message.header.priority
            self.queues[priority].append(message)
            self.size += 1
            return True
            
    async def get(self) -> Optional[Message]:
        """从队列获取最高优先级的消息"""
        async with self.lock:
            for priority in [Priority.CRITICAL, Priority.URGENT, Priority.HIGH, 
                           Priority.NORMAL, Priority.LOW]:
                if self.queues[priority]:
                    message = self.queues[priority].popleft()
                    self.size -= 1
                    return message
            return None
            
    async def _make_space(self) -> bool:
        """为新消息腾出空间"""
        # 按优先级从低到高丢弃消息
        for priority in [Priority.LOW, Priority.NORMAL]:
            if self.queues[priority]:
                self.queues[priority].popleft()
                self.size -= 1
                return True
        return False
        
    async def get_size(self) -> int:
        """获取队列大小"""
        return self.size
        
    async def clear(self):
        """清空队列"""
        async with self.lock:
            for queue in self.queues.values():
                queue.clear()
            self.size = 0


class MessageTracker:
    """消息跟踪器 - 跟踪消息的生命周期"""
    
    def __init__(self, retention_hours: int = 24):
        self.messages: Dict[str, Message] = {}  # message_id -> message
        self.message_states: Dict[str, Dict] = {}  # message_id -> state info
        self.retention_hours = retention_hours
        self.cleanup_task: Optional[asyncio.Task] = None
        
    def start_cleanup_task(self):
        """启动清理任务"""
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
        
    def stop_cleanup_task(self):
        """停止清理任务"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            
    def track_message(self, message: Message):
        """开始跟踪消息"""
        self.messages[message.header.message_id] = message
        self.message_states[message.header.message_id] = {
            'created_at': datetime.now(),
            'status': MessageStatus.PENDING,
            'delivery_attempts': 0,
            'last_attempt': None,
            'error_message': None
        }
        
    def update_message_status(self, message_id: str, status: MessageStatus, 
                            error_message: str = None):
        """更新消息状态"""
        if message_id in self.message_states:
            self.message_states[message_id]['status'] = status
            self.message_states[message_id]['last_attempt'] = datetime.now()
            
            if error_message:
                self.message_states[message_id]['error_message'] = error_message
                
            if status in [MessageStatus.SENT, MessageStatus.FAILED]:
                self.message_states[message_id]['delivery_attempts'] += 1
                
    def get_message_status(self, message_id: str) -> Optional[Dict]:
        """获取消息状态"""
        return self.message_states.get(message_id)
        
    def get_pending_messages(self) -> List[Message]:
        """获取待处理的消息"""
        pending_messages = []
        for message_id, state in self.message_states.items():
            if state['status'] == MessageStatus.PENDING:
                pending_messages.append(self.messages[message_id])
        return pending_messages
        
    async def _cleanup_expired_messages(self):
        """清理过期消息"""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
                expired_ids = []
                
                for message_id, state in self.message_states.items():
                    if state['created_at'] < cutoff_time:
                        expired_ids.append(message_id)
                        
                for message_id in expired_ids:
                    self.messages.pop(message_id, None)
                    self.message_states.pop(message_id, None)
                    
                # 每小时清理一次
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"清理过期消息时发生错误: {e}")
                await asyncio.sleep(300)  # 5分钟后重试


class MessageBus:
    """消息总线 - 核心通信组件"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.router = MessageRouter()
        self.message_queue = MessageQueue(
            max_size=self.config.get('queue_size', 10000)
        )
        self.tracker = MessageTracker(
            retention_hours=self.config.get('retention_hours', 24)
        )
        
        self.running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.logger = logging.getLogger('MessageBus')
        
        # 性能统计
        self.stats = {
            'messages_sent': 0,
            'messages_delivered': 0,
            'messages_failed': 0,
            'average_delivery_time': 0
        }
        
    async def start(self):
        """启动消息总线"""
        if self.running:
            return
            
        self.logger.info("启动消息总线...")
        self.running = True
        
        # 启动消息处理工作者
        num_workers = self.config.get('num_workers', 3)
        for i in range(num_workers):
            task = asyncio.create_task(self._message_worker(f"worker-{i}"))
            self.worker_tasks.append(task)
            
        # 启动消息跟踪清理任务
        self.tracker.start_cleanup_task()
        
        # 启动统计报告任务
        asyncio.create_task(self._stats_reporter())
        
        self.logger.info("消息总线启动完成")
        
    async def stop(self):
        """停止消息总线"""
        if not self.running:
            return
            
        self.logger.info("停止消息总线...")
        self.running = False
        
        # 停止工作者任务
        for task in self.worker_tasks:
            task.cancel()
            
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
        
        # 停止跟踪清理任务
        self.tracker.stop_cleanup_task()
        
        self.logger.info("消息总线已停止")
        
    def register_role(self, role_id: str, handler: Callable):
        """注册角色"""
        self.router.register_role(role_id, handler)
        self.logger.info(f"角色 {role_id} 已注册")
        
    def unregister_role(self, role_id: str):
        """注销角色"""
        self.router.unregister_role(role_id)
        self.logger.info(f"角色 {role_id} 已注销")
        
    async def send_message(self, message: Message) -> str:
        """发送消息"""
        try:
            # 验证消息
            is_valid, error_msg = MessageValidator.validate_message(message)
            if not is_valid:
                raise ValueError(f"消息验证失败: {error_msg}")
                
            # 应用中间件
            message = await self.router.apply_middleware(message)
            
            # 跟踪消息
            self.tracker.track_message(message)
            
            # 加入队列
            success = await self.message_queue.put(message)
            if not success:
                self.tracker.update_message_status(
                    message.header.message_id, 
                    MessageStatus.FAILED,
                    "消息队列已满"
                )
                raise Exception("消息队列已满")
                
            self.stats['messages_sent'] += 1
            return message.header.message_id
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            raise
            
    async def _message_worker(self, worker_name: str):
        """消息处理工作者"""
        self.logger.info(f"消息工作者 {worker_name} 启动")
        
        while self.running:
            try:
                # 从队列获取消息
                message = await asyncio.wait_for(
                    self.message_queue.get(), timeout=1.0
                )
                
                if message:
                    await self._process_message(message)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"工作者 {worker_name} 处理消息时发生错误: {e}")
                
        self.logger.info(f"消息工作者 {worker_name} 停止")
        
    async def _process_message(self, message: Message):
        """处理单个消息"""
        start_time = datetime.now()
        
        try:
            # 路由消息
            target_roles = await self.router.route_message(message)
            
            if not target_roles:
                self.tracker.update_message_status(
                    message.header.message_id,
                    MessageStatus.FAILED,
                    "找不到目标角色"
                )
                return
                
            # 发送给目标角色
            for role_id in target_roles:
                await self._deliver_to_role(message, role_id)
                
            # 更新状态
            self.tracker.update_message_status(
                message.header.message_id,
                MessageStatus.DELIVERED
            )
            
            # 更新统计
            self.stats['messages_delivered'] += 1
            delivery_time = (datetime.now() - start_time).total_seconds()
            self._update_average_delivery_time(delivery_time)
            
        except Exception as e:
            self.logger.error(f"处理消息 {message.header.message_id} 失败: {e}")
            self.tracker.update_message_status(
                message.header.message_id,
                MessageStatus.FAILED,
                str(e)
            )
            self.stats['messages_failed'] += 1
            
    async def _deliver_to_role(self, message: Message, role_id: str):
        """将消息投递给特定角色"""
        try:
            handler = self.router.role_handlers.get(role_id)
            if handler:
                # 调用角色的消息处理器
                await handler(message)
            else:
                raise Exception(f"角色 {role_id} 的处理器未找到")
                
        except Exception as e:
            self.logger.error(f"投递消息给角色 {role_id} 失败: {e}")
            raise
            
    def _update_average_delivery_time(self, delivery_time: float):
        """更新平均投递时间"""
        current_avg = self.stats['average_delivery_time']
        delivered_count = self.stats['messages_delivered']
        
        if delivered_count == 1:
            self.stats['average_delivery_time'] = delivery_time
        else:
            # 计算移动平均
            self.stats['average_delivery_time'] = (
                (current_avg * (delivered_count - 1) + delivery_time) / delivered_count
            )
            
    async def _stats_reporter(self):
        """统计报告器"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 每5分钟报告一次
                
                self.logger.info(f"消息总线统计: "
                               f"已发送={self.stats['messages_sent']}, "
                               f"已投递={self.stats['messages_delivered']}, "
                               f"失败={self.stats['messages_failed']}, "
                               f"平均投递时间={self.stats['average_delivery_time']:.3f}s")
                               
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"统计报告时发生错误: {e}")
                
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
        
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            'queue_size': self.message_queue.size,
            'max_size': self.message_queue.max_size,
            'utilization': self.message_queue.size / self.message_queue.max_size
        }


# 中间件示例
async def logging_middleware(message: Message) -> Message:
    """日志中间件"""
    logger = logging.getLogger('MessageMiddleware')
    logger.info(f"消息 {message.header.message_id}: "
                f"{message.header.from_role} -> {message.header.to_role}, "
                f"动作: {message.body.action}")
    return message


async def security_middleware(message: Message) -> Message:
    """安全中间件"""
    # 这里可以添加消息加密、签名验证等安全处理
    return message


# 使用示例
async def example_usage():
    """使用示例"""
    # 创建消息总线
    bus = MessageBus({
        'queue_size': 1000,
        'num_workers': 2,
        'retention_hours': 12
    })
    
    # 添加中间件
    bus.router.add_middleware(logging_middleware)
    bus.router.add_middleware(security_middleware)
    
    # 启动消息总线
    await bus.start()
    
    # 模拟角色处理器
    async def role_handler(message: Message):
        print(f"角色处理消息: {message.header.message_id}")
        
    # 注册角色
    bus.register_role("test_role", role_handler)
    
    # 发送消息
    from .message_protocol import MessageBuilder
    
    message = MessageBuilder.create_request(
        from_role="sender",
        to_role="test_role", 
        action="test_action",
        data={'test': 'data'}
    )
    
    message_id = await bus.send_message(message)
    print(f"消息已发送: {message_id}")
    
    # 等待处理
    await asyncio.sleep(2)
    
    # 获取统计
    stats = bus.get_stats()
    print(f"统计信息: {stats}")
    
    # 停止消息总线
    await bus.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())