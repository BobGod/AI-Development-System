#!/usr/bin/env python3
"""
AI自主开发系统 - 基础角色类
定义所有AI角色的共同接口和基础功能
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from communication import Message, MessageBuilder, MessageType, Priority


class RoleState(Enum):
    """角色状态枚举"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """任务类"""
    
    def __init__(self, task_id: str, task_type: str, data: Dict[str, Any], 
                 priority: Priority = Priority.NORMAL):
        self.task_id = task_id
        self.task_type = task_type
        self.data = data
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.progress = 0.0  # 0.0 - 1.0
        
    def start(self):
        """开始任务"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()
        
    def complete(self, result: Dict[str, Any] = None):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result or {}
        self.progress = 1.0
        
    def fail(self, error_message: str):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message
        
    def update_progress(self, progress: float):
        """更新进度"""
        self.progress = max(0.0, min(1.0, progress))
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'data': self.data,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error_message': self.error_message,
            'progress': self.progress
        }


class BaseRole(ABC):
    """基础角色抽象类"""
    
    def __init__(self, role_id: str, role_name: str, config: Dict[str, Any] = None):
        self.role_id = role_id
        self.role_name = role_name
        self.config = config or {}
        self.state = RoleState.INITIALIZING
        
        # 任务管理
        self.current_tasks: Dict[str, Task] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.max_concurrent_tasks = self.config.get('max_concurrent_tasks', 3)
        
        # 通信相关
        self.message_bus: Optional[Any] = None
        self.message_handlers: Dict[str, Callable] = {}
        
        # 日志和统计
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.stats = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'uptime_start': datetime.now()
        }
        
        # 内部状态
        self.last_activity = datetime.now()
        self.worker_tasks: List[asyncio.Task] = []
        self.running = False
        
        # 注册基础消息处理器
        self._register_base_handlers()
        
    def _register_base_handlers(self):
        """注册基础消息处理器"""
        self.message_handlers.update({
            'health_check': self._handle_health_check,
            'status_query': self._handle_status_query,
            'task_assign': self._handle_task_assignment,
            'task_cancel': self._handle_task_cancellation,
            'shutdown': self._handle_shutdown
        })
        
    async def initialize(self, message_bus: Any):
        """初始化角色"""
        try:
            self.logger.info(f"初始化角色 {self.role_name}")
            self.message_bus = message_bus
            
            # 执行具体角色的初始化
            await self._initialize_role()
            
            # 启动任务处理器
            await self._start_task_workers()
            
            self.state = RoleState.ACTIVE
            self.running = True
            
            # 发送初始化完成消息
            await self._send_status_update("initialized")
            
            self.logger.info(f"角色 {self.role_name} 初始化完成")
            
        except Exception as e:
            self.logger.error(f"角色初始化失败: {e}")
            self.state = RoleState.ERROR
            raise
            
    async def shutdown(self):
        """关闭角色"""
        try:
            self.logger.info(f"关闭角色 {self.role_name}")
            self.running = False
            self.state = RoleState.SHUTDOWN
            
            # 停止任务处理器
            for task in self.worker_tasks:
                task.cancel()
                
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            self.worker_tasks.clear()
            
            # 取消所有进行中的任务
            for task in self.current_tasks.values():
                if task.status == TaskStatus.IN_PROGRESS:
                    task.status = TaskStatus.CANCELLED
                    
            # 执行具体角色的清理
            await self._cleanup_role()
            
            self.logger.info(f"角色 {self.role_name} 已关闭")
            
        except Exception as e:
            self.logger.error(f"角色关闭时发生错误: {e}")
            
    async def handle_message(self, message: Message):
        """处理接收到的消息"""
        try:
            self.stats['messages_received'] += 1
            self.last_activity = datetime.now()
            
            action = message.body.action
            
            # 查找处理器
            handler = self.message_handlers.get(action)
            if handler:
                await handler(message)
            else:
                # 交给具体角色处理
                await self._handle_custom_message(message)
                
        except Exception as e:
            self.logger.error(f"处理消息时发生错误: {e}")
            
            # 发送错误响应
            if message.header.message_type == MessageType.REQUEST:
                await self._send_error_response(message, str(e))
                
    async def send_message(self, to_role: str, action: str, data: Dict[str, Any] = None,
                          message_type: MessageType = MessageType.REQUEST,
                          priority: Priority = Priority.NORMAL) -> str:
        """发送消息"""
        try:
            message = MessageBuilder.create_request(
                from_role=self.role_id,
                to_role=to_role,
                action=action,
                data=data or {},
                priority=priority
            )
            message.header.message_type = message_type
            
            message_id = await self.message_bus.send_message(message)
            self.stats['messages_sent'] += 1
            
            return message_id
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            raise
            
    async def add_task(self, task_type: str, data: Dict[str, Any], 
                      priority: Priority = Priority.NORMAL) -> str:
        """添加任务到队列"""
        task_id = str(uuid.uuid4())
        task = Task(task_id, task_type, data, priority)
        
        # 使用负优先级值，因为PriorityQueue是最小堆
        priority_value = -priority.value
        await self.task_queue.put((priority_value, task))
        
        self.logger.info(f"添加任务 {task_id}: {task_type}")
        return task_id
        
    def get_status(self) -> Dict[str, Any]:
        """获取角色状态"""
        return {
            'role_id': self.role_id,
            'role_name': self.role_name,
            'state': self.state.value,
            'last_activity': self.last_activity.isoformat(),
            'current_tasks_count': len(self.current_tasks),
            'task_queue_size': self.task_queue.qsize(),
            'stats': self.stats.copy()
        }
        
    # 基础消息处理器
    async def _handle_health_check(self, message: Message):
        """处理健康检查"""
        response_data = {
            'status': 'healthy',
            'state': self.state.value,
            'last_activity': self.last_activity.isoformat(),
            'uptime': (datetime.now() - self.stats['uptime_start']).total_seconds()
        }
        
        await self._send_response(message, response_data)
        
    async def _handle_status_query(self, message: Message):
        """处理状态查询"""
        status = self.get_status()
        await self._send_response(message, status)
        
    async def _handle_task_assignment(self, message: Message):
        """处理任务分配"""
        try:
            task_data = message.body.data
            task_type = task_data.get('task_type', 'unknown')
            task_details = task_data.get('task_details', {})
            priority = Priority(task_data.get('priority', Priority.NORMAL.value))
            
            task_id = await self.add_task(task_type, task_details, priority)
            
            response_data = {
                'task_id': task_id,
                'status': 'accepted'
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"任务分配失败: {e}")
            
    async def _handle_task_cancellation(self, message: Message):
        """处理任务取消"""
        try:
            task_id = message.body.data.get('task_id')
            
            if task_id in self.current_tasks:
                task = self.current_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                del self.current_tasks[task_id]
                
                response_data = {'status': 'cancelled'}
            else:
                response_data = {'status': 'not_found'}
                
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"任务取消失败: {e}")
            
    async def _handle_shutdown(self, message: Message):
        """处理关闭消息"""
        await self._send_response(message, {'status': 'shutting_down'})
        await self.shutdown()
        
    async def _send_response(self, request_message: Message, data: Dict[str, Any]):
        """发送响应消息"""
        response = MessageBuilder.create_response(request_message, data, success=True)
        await self.message_bus.send_message(response)
        
    async def _send_error_response(self, request_message: Message, error_message: str):
        """发送错误响应"""
        response = MessageBuilder.create_response(
            request_message, 
            {'error': error_message}, 
            success=False
        )
        await self.message_bus.send_message(response)
        
    async def _send_status_update(self, event: str, data: Dict[str, Any] = None):
        """发送状态更新"""
        update_data = {
            'event': event,
            'role_id': self.role_id,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        
        await self.send_message(
            to_role="status_monitor",
            action="status_update",
            data=update_data,
            message_type=MessageType.NOTIFICATION
        )
        
    async def _start_task_workers(self):
        """启动任务处理工作者"""
        for i in range(self.max_concurrent_tasks):
            task = asyncio.create_task(self._task_worker(f"worker-{i}"))
            self.worker_tasks.append(task)
            
    async def _task_worker(self, worker_name: str):
        """任务处理工作者"""
        self.logger.debug(f"任务工作者 {worker_name} 启动")
        
        while self.running:
            try:
                # 从队列获取任务
                priority_value, task = await asyncio.wait_for(
                    self.task_queue.get(), timeout=1.0
                )
                
                # 检查并发任务数量限制
                if len(self.current_tasks) >= self.max_concurrent_tasks:
                    # 重新放回队列
                    await self.task_queue.put((priority_value, task))
                    await asyncio.sleep(0.1)
                    continue
                    
                # 执行任务
                self.current_tasks[task.task_id] = task
                await self._execute_task(task)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"工作者 {worker_name} 处理任务时发生错误: {e}")
                
        self.logger.debug(f"任务工作者 {worker_name} 停止")
        
    async def _execute_task(self, task: Task):
        """执行单个任务"""
        try:
            self.logger.info(f"开始执行任务 {task.task_id}: {task.task_type}")
            task.start()
            
            # 调用具体角色的任务处理方法
            result = await self._process_task(task)
            
            # 任务完成
            task.complete(result)
            self.stats['tasks_completed'] += 1
            
            self.logger.info(f"任务 {task.task_id} 完成")
            
        except Exception as e:
            # 任务失败
            task.fail(str(e))
            self.stats['tasks_failed'] += 1
            
            self.logger.error(f"任务 {task.task_id} 失败: {e}")
            
        finally:
            # 从当前任务列表中移除
            self.current_tasks.pop(task.task_id, None)
            
            # 发送任务状态更新
            await self._send_task_status_update(task)
            
    async def _send_task_status_update(self, task: Task):
        """发送任务状态更新"""
        await self._send_status_update("task_update", task.to_dict())
        
    # 抽象方法 - 需要具体角色实现
    @abstractmethod
    async def _initialize_role(self):
        """角色特定的初始化逻辑"""
        pass
        
    @abstractmethod
    async def _cleanup_role(self):
        """角色特定的清理逻辑"""
        pass
        
    @abstractmethod
    async def _handle_custom_message(self, message: Message):
        """处理角色特定的消息"""
        pass
        
    @abstractmethod
    async def _process_task(self, task: Task) -> Dict[str, Any]:
        """处理角色特定的任务"""
        pass