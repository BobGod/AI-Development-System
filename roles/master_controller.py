#!/usr/bin/env python3
"""
AI自主开发系统 - 项目总控制器
负责整个软件开发生命周期的协调、决策和推进
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roles.base_role import BaseRole, Task, TaskStatus, RoleState
from communication import Message, MessageBuilder, MessageType, Priority


class ProjectPhase(Enum):
    """项目阶段枚举"""
    INITIALIZATION = "initialization"
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


class DecisionType(Enum):
    """决策类型枚举"""
    TECHNICAL_CHOICE = "technical_choice"
    RESOURCE_ALLOCATION = "resource_allocation"
    PRIORITY_ADJUSTMENT = "priority_adjustment"
    QUALITY_STANDARD = "quality_standard"
    RISK_MITIGATION = "risk_mitigation"


class ProjectContext:
    """项目上下文"""
    
    def __init__(self, project_config: Dict[str, Any]):
        self.project_name = project_config.get('name', 'Unknown Project')
        self.description = project_config.get('description', '')
        self.requirements = project_config.get('requirements', '')
        self.constraints = project_config.get('constraints', [])
        self.timeline = project_config.get('timeline', '')
        
        self.current_phase = ProjectPhase.INITIALIZATION
        self.milestones: List[Dict[str, Any]] = []
        self.decisions: List[Dict[str, Any]] = []
        self.active_roles: Dict[str, str] = {}  # role_id -> status
        self.project_metrics = {
            'progress_percentage': 0.0,
            'quality_score': 0.0,
            'risk_level': 'low'
        }


class MasterController(BaseRole):
    """项目总控制器 - 系统的核心决策和协调角色"""
    
    def __init__(self, role_id: str = "master_controller", config: Dict[str, Any] = None):
        super().__init__(role_id, "项目总控制器", config)
        
        self.project_context: Optional[ProjectContext] = None
        self.development_plan: List[Dict[str, Any]] = []
        self.coordination_tasks: Dict[str, Any] = {}
        
        # 决策历史和规则
        self.decision_history: List[Dict[str, Any]] = []
        self.decision_rules = self._init_decision_rules()
        
        # 角色协调状态
        self.role_status: Dict[str, Dict[str, Any]] = {}
        self.pending_responses: Dict[str, Dict[str, Any]] = {}
        
        # 注册专用消息处理器
        self.message_handlers.update({
            'initialize_project': self._handle_project_initialization,
            'process_user_request': self._handle_user_request,
            'role_status_update': self._handle_role_status_update,
            'request_decision': self._handle_decision_request,
            'phase_completion': self._handle_phase_completion,
            'emergency_escalation': self._handle_emergency_escalation
        })
        
    def _init_decision_rules(self) -> Dict[str, Any]:
        """初始化决策规则"""
        return {
            'technical_selection': {
                'criteria': ['business_fit', 'technical_maturity', 'team_expertise', 'performance', 'cost'],
                'weights': [0.3, 0.25, 0.2, 0.15, 0.1]
            },
            'priority_rules': {
                'core_functionality': 1,
                'user_experience': 2,
                'performance_optimization': 3,
                'advanced_features': 4
            },
            'quality_gates': {
                'code_coverage': 0.8,
                'critical_bugs': 0,
                'security_issues': 0,
                'performance_degradation': 0.05
            }
        }
        
    async def _initialize_role(self):
        """初始化总控制器"""
        self.logger.info("初始化项目总控制器")
        
        # 启动定期检查任务
        asyncio.create_task(self._periodic_health_check())
        asyncio.create_task(self._periodic_progress_review())
        
    async def _cleanup_role(self):
        """清理总控制器"""
        self.logger.info("清理项目总控制器")
        
    async def _handle_custom_message(self, message: Message):
        """处理自定义消息"""
        self.logger.warning(f"收到未知消息类型: {message.body.action}")
        
    async def _process_task(self, task: Task) -> Dict[str, Any]:
        """处理任务"""
        task_type = task.task_type
        
        if task_type == "coordinate_development":
            return await self._coordinate_development(task)
        elif task_type == "make_decision":
            return await self._make_decision(task)
        elif task_type == "monitor_progress":
            return await self._monitor_progress(task)
        elif task_type == "resolve_conflict":
            return await self._resolve_conflict(task)
        else:
            raise ValueError(f"未知任务类型: {task_type}")
            
    async def _handle_project_initialization(self, message: Message):
        """处理项目初始化"""
        try:
            project_config = message.body.data.get('project_config', {})
            self.project_context = ProjectContext(project_config)
            
            self.logger.info(f"初始化项目: {self.project_context.project_name}")
            
            # 创建开发计划
            await self._create_development_plan()
            
            # 激活记忆管理器
            await self._initialize_memory_manager()
            
            # 开始需求分析阶段
            await self._start_requirements_analysis()
            
            # 发送成功响应
            response_data = {
                'project_name': self.project_context.project_name,
                'status': 'initialized',
                'current_phase': self.project_context.current_phase.value
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"项目初始化失败: {e}")
            
    async def _handle_user_request(self, message: Message):
        """处理用户请求"""
        try:
            user_request = message.body.data.get('request', '')
            
            self.logger.info(f"处理用户请求: {user_request}")
            
            # 分析请求类型和优先级
            request_analysis = await self._analyze_user_request(user_request)
            
            # 根据分析结果采取行动
            action_result = await self._execute_user_request(request_analysis)
            
            response_data = {
                'request_id': message.header.message_id,
                'analysis': request_analysis,
                'action_taken': action_result,
                'status': 'processed'
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"处理用户请求失败: {e}")
            
    async def _handle_role_status_update(self, message: Message):
        """处理角色状态更新"""
        try:
            status_data = message.body.data
            role_id = status_data.get('role_id')
            
            if role_id:
                self.role_status[role_id] = {
                    'last_update': datetime.now(),
                    'status': status_data,
                    'message_id': message.header.message_id
                }
                
                # 检查是否需要采取行动
                await self._check_role_status_action(role_id, status_data)
                
        except Exception as e:
            self.logger.error(f"处理角色状态更新失败: {e}")
            
    async def _handle_decision_request(self, message: Message):
        """处理决策请求"""
        try:
            decision_data = message.body.data
            decision_type = decision_data.get('decision_type')
            options = decision_data.get('options', [])
            context = decision_data.get('context', {})
            
            # 做出决策
            decision = await self._make_strategic_decision(decision_type, options, context)
            
            # 记录决策
            self._record_decision(decision_type, decision, context)
            
            response_data = {
                'decision': decision,
                'reasoning': decision.get('reasoning', ''),
                'confidence': decision.get('confidence', 0.5)
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"决策失败: {e}")
            
    async def _handle_phase_completion(self, message: Message):
        """处理阶段完成通知"""
        try:
            phase_data = message.body.data
            completed_phase = phase_data.get('phase')
            results = phase_data.get('results', {})
            
            self.logger.info(f"阶段完成: {completed_phase}")
            
            # 验证阶段完成质量
            quality_check = await self._validate_phase_completion(completed_phase, results)
            
            if quality_check['passed']:
                # 进入下一阶段
                await self._advance_to_next_phase(completed_phase)
            else:
                # 要求重做或修复
                await self._request_phase_rework(completed_phase, quality_check['issues'])
                
            response_data = {
                'phase': completed_phase,
                'validation': quality_check,
                'next_action': 'advance' if quality_check['passed'] else 'rework'
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"处理阶段完成失败: {e}")
            
    async def _handle_emergency_escalation(self, message: Message):
        """处理紧急情况上报"""
        try:
            emergency_data = message.body.data
            severity = emergency_data.get('severity', 'medium')
            description = emergency_data.get('description', '')
            
            self.logger.warning(f"紧急情况: {description} (严重性: {severity})")
            
            # 根据严重性采取不同措施
            if severity == 'critical':
                await self._handle_critical_emergency(emergency_data)
            elif severity == 'high':
                await self._handle_high_priority_issue(emergency_data)
            else:
                await self._handle_standard_issue(emergency_data)
                
            response_data = {
                'emergency_id': message.header.message_id,
                'status': 'acknowledged',
                'action_taken': True
            }
            
            await self._send_response(message, response_data)
            
        except Exception as e:
            await self._send_error_response(message, f"处理紧急情况失败: {e}")
            
    async def _create_development_plan(self):
        """创建开发计划"""
        if not self.project_context:
            return
            
        # 基础开发阶段
        self.development_plan = [
            {
                'phase': ProjectPhase.REQUIREMENTS_ANALYSIS,
                'description': '需求分析和规格制定',
                'estimated_duration': '2-3天',
                'key_deliverables': ['需求文档', '用户故事', '验收标准'],
                'responsible_roles': ['requirements_parser']
            },
            {
                'phase': ProjectPhase.ARCHITECTURE_DESIGN,
                'description': '系统架构设计',
                'estimated_duration': '3-4天',
                'key_deliverables': ['架构文档', '技术方案', '接口设计'],
                'responsible_roles': ['system_architect']
            },
            {
                'phase': ProjectPhase.DEVELOPMENT,
                'description': '代码开发实现',
                'estimated_duration': '10-15天',
                'key_deliverables': ['功能模块', '代码文档', '单元测试'],
                'responsible_roles': ['frontend_dev', 'backend_dev', 'fullstack_dev']
            },
            {
                'phase': ProjectPhase.TESTING,
                'description': '系统测试验证',
                'estimated_duration': '3-5天',
                'key_deliverables': ['测试报告', '质量评估', '问题修复'],
                'responsible_roles': ['test_engineer']
            }
        ]
        
        self.logger.info(f"创建了包含 {len(self.development_plan)} 个阶段的开发计划")
        
    async def _initialize_memory_manager(self):
        """初始化记忆管理器"""
        project_data = {
            'project_config': {
                'name': self.project_context.project_name,
                'description': self.project_context.description,
                'requirements': self.project_context.requirements,
                'constraints': self.project_context.constraints
            },
            'development_plan': self.development_plan,
            'session_id': datetime.now().strftime('%Y%m%d_%H%M%S')
        }
        
        await self.send_message(
            to_role="memory_manager",
            action="initialize_project_context",
            data=project_data,
            priority=Priority.HIGH
        )
        
    async def _start_requirements_analysis(self):
        """开始需求分析阶段"""
        self.project_context.current_phase = ProjectPhase.REQUIREMENTS_ANALYSIS
        
        # 向需求解析器发送任务
        await self.send_message(
            to_role="requirements_parser",
            action="analyze_requirements",
            data={
                'requirements': self.project_context.requirements,
                'project_context': {
                    'name': self.project_context.project_name,
                    'description': self.project_context.description,
                    'constraints': self.project_context.constraints
                }
            },
            priority=Priority.HIGH
        )
        
        self.logger.info("已启动需求分析阶段")
        
    async def _analyze_user_request(self, request: str) -> Dict[str, Any]:
        """分析用户请求"""
        # 简化的请求分析逻辑
        analysis = {
            'request_type': 'general',
            'priority': 'medium',
            'estimated_complexity': 'medium',
            'required_roles': ['requirements_parser'],
            'estimated_time': '1-2小时'
        }
        
        # 关键词检测
        if any(keyword in request.lower() for keyword in ['紧急', 'urgent', '立即']):
            analysis['priority'] = 'high'
            
        if any(keyword in request.lower() for keyword in ['新功能', '开发', '实现']):
            analysis['request_type'] = 'development'
            analysis['required_roles'].extend(['system_architect', 'frontend_dev', 'backend_dev'])
            
        if any(keyword in request.lower() for keyword in ['测试', 'bug', '问题']):
            analysis['request_type'] = 'testing'
            analysis['required_roles'].append('test_engineer')
            
        return analysis
        
    async def _execute_user_request(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """执行用户请求"""
        request_type = analysis['request_type']
        
        if request_type == 'development':
            return await self._handle_development_request(analysis)
        elif request_type == 'testing':
            return await self._handle_testing_request(analysis)
        else:
            return await self._handle_general_request(analysis)
            
    async def _handle_development_request(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """处理开发请求"""
        # 创建开发协调任务
        task_id = await self.add_task(
            task_type="coordinate_development",
            data=analysis,
            priority=Priority.HIGH if analysis['priority'] == 'high' else Priority.NORMAL
        )
        
        return {
            'action': 'development_coordination_started',
            'task_id': task_id,
            'status': 'in_progress'
        }
        
    async def _handle_testing_request(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """处理测试请求"""
        # 通知测试工程师
        await self.send_message(
            to_role="test_engineer",
            action="handle_test_request",
            data=analysis,
            priority=Priority.HIGH if analysis['priority'] == 'high' else Priority.NORMAL
        )
        
        return {
            'action': 'test_request_forwarded',
            'status': 'forwarded_to_test_engineer'
        }
        
    async def _handle_general_request(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """处理一般请求"""
        return {
            'action': 'general_acknowledgment',
            'status': 'acknowledged'
        }
        
    async def _make_strategic_decision(self, decision_type: str, options: List[Dict], 
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """做出战略决策"""
        if decision_type == DecisionType.TECHNICAL_CHOICE.value:
            return await self._make_technical_decision(options, context)
        elif decision_type == DecisionType.RESOURCE_ALLOCATION.value:
            return await self._make_resource_decision(options, context)
        else:
            # 默认决策逻辑
            return {
                'chosen_option': options[0] if options else None,
                'reasoning': '基于默认规则选择',
                'confidence': 0.5
            }
            
    async def _make_technical_decision(self, options: List[Dict], context: Dict) -> Dict[str, Any]:
        """做出技术决策"""
        if not options:
            return {'chosen_option': None, 'reasoning': '无可选项', 'confidence': 0}
            
        # 简化的评分逻辑
        best_option = None
        best_score = -1
        
        for option in options:
            score = 0
            # 根据决策规则计算分数
            criteria = self.decision_rules['technical_selection']['criteria']
            weights = self.decision_rules['technical_selection']['weights']
            
            for i, criterion in enumerate(criteria):
                if criterion in option:
                    score += option[criterion] * weights[i]
                    
            if score > best_score:
                best_score = score
                best_option = option
                
        return {
            'chosen_option': best_option,
            'reasoning': f'基于技术评估选择，得分: {best_score:.2f}',
            'confidence': min(best_score, 1.0)
        }
        
    async def _make_resource_decision(self, options: List[Dict], context: Dict) -> Dict[str, Any]:
        """做出资源分配决策"""
        # 简化的资源分配逻辑
        return {
            'chosen_option': options[0] if options else None,
            'reasoning': '基于当前项目阶段和优先级分配',
            'confidence': 0.7
        }
        
    def _record_decision(self, decision_type: str, decision: Dict[str, Any], context: Dict):
        """记录决策"""
        decision_record = {
            'id': len(self.decision_history) + 1,
            'timestamp': datetime.now().isoformat(),
            'type': decision_type,
            'decision': decision,
            'context': context,
            'decision_maker': self.role_id
        }
        
        self.decision_history.append(decision_record)
        
    async def _check_role_status_action(self, role_id: str, status_data: Dict[str, Any]):
        """检查角色状态并采取必要行动"""
        event = status_data.get('event', '')
        
        if event == 'task_failed':
            await self._handle_task_failure(role_id, status_data)
        elif event == 'role_error':
            await self._handle_role_error(role_id, status_data)
        elif event == 'task_completed':
            await self._handle_task_completion(role_id, status_data)
            
    async def _handle_task_failure(self, role_id: str, status_data: Dict[str, Any]):
        """处理任务失败"""
        self.logger.warning(f"角色 {role_id} 的任务失败")
        
        # 可以实现重试逻辑或重新分配任务
        
    async def _handle_role_error(self, role_id: str, status_data: Dict[str, Any]):
        """处理角色错误"""
        self.logger.error(f"角色 {role_id} 发生错误")
        
        # 可以实现角色重启或任务重新分配
        
    async def _handle_task_completion(self, role_id: str, status_data: Dict[str, Any]):
        """处理任务完成"""
        self.logger.info(f"角色 {role_id} 完成任务")
        
        # 可以触发下一步行动
        
    async def _periodic_health_check(self):
        """定期健康检查"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 每5分钟检查一次
                
                # 检查各角色状态
                for role_id in ['memory_manager', 'status_monitor', 'requirements_parser']:
                    await self.send_message(
                        to_role=role_id,
                        action="health_check",
                        message_type=MessageType.QUERY
                    )
                    
            except Exception as e:
                self.logger.error(f"定期健康检查失败: {e}")
                
    async def _periodic_progress_review(self):
        """定期进度回顾"""
        while self.running:
            try:
                await asyncio.sleep(1800)  # 每30分钟检查一次
                
                if self.project_context:
                    progress = await self._calculate_project_progress()
                    self.logger.info(f"项目进度: {progress:.1f}%")
                    
            except Exception as e:
                self.logger.error(f"定期进度回顾失败: {e}")
                
    async def _calculate_project_progress(self) -> float:
        """计算项目进度"""
        # 简化的进度计算逻辑
        phase_weights = {
            ProjectPhase.REQUIREMENTS_ANALYSIS: 0.2,
            ProjectPhase.ARCHITECTURE_DESIGN: 0.2,
            ProjectPhase.DEVELOPMENT: 0.5,
            ProjectPhase.TESTING: 0.1
        }
        
        current_phase = self.project_context.current_phase
        completed_weight = 0
        
        for phase, weight in phase_weights.items():
            if phase.value < current_phase.value:
                completed_weight += weight
                
        return completed_weight * 100
        
    # 其他协调和决策方法的占位符实现
    async def _coordinate_development(self, task: Task) -> Dict[str, Any]:
        """协调开发工作"""
        await asyncio.sleep(1)  # 模拟处理时间
        return {'status': 'coordinated', 'result': 'development_coordinated'}
        
    async def _make_decision(self, task: Task) -> Dict[str, Any]:
        """做出决策"""
        await asyncio.sleep(1)  # 模拟处理时间
        return {'status': 'decided', 'decision': 'default_decision'}
        
    async def _monitor_progress(self, task: Task) -> Dict[str, Any]:
        """监控进度"""
        await asyncio.sleep(1)  # 模拟处理时间
        return {'status': 'monitored', 'progress': '50%'}
        
    async def _resolve_conflict(self, task: Task) -> Dict[str, Any]:
        """解决冲突"""
        await asyncio.sleep(1)  # 模拟处理时间
        return {'status': 'resolved', 'resolution': 'conflict_resolved'}
        
    async def _validate_phase_completion(self, phase: str, results: Dict) -> Dict[str, Any]:
        """验证阶段完成"""
        return {'passed': True, 'issues': []}
        
    async def _advance_to_next_phase(self, completed_phase: str):
        """进入下一阶段"""
        self.logger.info(f"从 {completed_phase} 进入下一阶段")
        
    async def _request_phase_rework(self, phase: str, issues: List[str]):
        """请求阶段重做"""
        self.logger.warning(f"请求 {phase} 阶段重做，问题: {issues}")
        
    async def _handle_critical_emergency(self, emergency_data: Dict):
        """处理严重紧急情况"""
        self.logger.critical("处理严重紧急情况")
        
    async def _handle_high_priority_issue(self, emergency_data: Dict):
        """处理高优先级问题"""
        self.logger.warning("处理高优先级问题")
        
    async def _handle_standard_issue(self, emergency_data: Dict):
        """处理标准问题"""
        self.logger.info("处理标准问题")