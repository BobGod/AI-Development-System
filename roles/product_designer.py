#!/usr/bin/env python3
"""
AI自主开发系统 - 产品设计师
负责用户体验设计、界面设计、交互设计、可用性评估
"""

import asyncio
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roles.base_role import BaseRole, Task, TaskStatus, RoleState

class DesignPhase(Enum):
    """设计阶段枚举"""
    RESEARCH = "research"           # 用户研究阶段
    IDEATION = "ideation"          # 构思阶段
    WIREFRAMING = "wireframing"    # 线框图阶段
    PROTOTYPING = "prototyping"    # 原型制作阶段
    TESTING = "testing"            # 用户测试阶段
    REFINEMENT = "refinement"      # 优化完善阶段
    HANDOFF = "handoff"           # 设计交付阶段

class DeviceType(Enum):
    """设备类型枚举"""
    DESKTOP = "desktop"           # 桌面端
    TABLET = "tablet"            # 平板端
    MOBILE = "mobile"            # 移动端
    WEARABLE = "wearable"        # 可穿戴设备
    TV = "tv"                    # 电视端

class DesignType(Enum):
    """设计类型枚举"""
    WIREFRAME = "wireframe"       # 线框图
    MOCKUP = "mockup"            # 视觉稿
    PROTOTYPE = "prototype"       # 原型
    DESIGN_SYSTEM = "design_system"  # 设计系统
    USER_FLOW = "user_flow"      # 用户流程
    PERSONA = "persona"          # 用户画像

class UsabilityLevel(Enum):
    """可用性等级枚举"""
    EXCELLENT = "excellent"      # 优秀 (90-100分)
    GOOD = "good"               # 良好 (80-89分)
    ACCEPTABLE = "acceptable"    # 可接受 (70-79分)
    POOR = "poor"               # 较差 (60-69分)
    CRITICAL = "critical"       # 严重 (0-59分)

@dataclass
class UserPersona:
    """用户画像数据类"""
    persona_id: str
    name: str
    age_range: str
    occupation: str
    goals: List[str]
    pain_points: List[str]
    behaviors: List[str]
    tech_proficiency: str
    preferred_devices: List[str]
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class UserJourney:
    """用户旅程数据类"""
    journey_id: str
    persona_id: str
    scenario: str
    stages: List[Dict[str, Any]]
    touchpoints: List[str]
    pain_points: List[str]
    opportunities: List[str]
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class DesignAsset:
    """设计资产数据类"""
    asset_id: str
    asset_type: DesignType
    title: str
    description: str
    device_type: DeviceType
    file_path: str
    version: str
    status: str = "draft"
    tags: List[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

@dataclass
class UsabilityTest:
    """可用性测试数据类"""
    test_id: str
    test_name: str
    test_type: str
    participants: int
    tasks: List[Dict[str, Any]]
    metrics: Dict[str, float]
    findings: List[str]
    recommendations: List[str]
    conducted_at: str = ""
    
    def __post_init__(self):
        if not self.conducted_at:
            self.conducted_at = datetime.now().isoformat()

@dataclass
class DesignSystemComponent:
    """设计系统组件数据类"""
    component_id: str
    component_name: str
    component_type: str
    description: str
    usage_guidelines: str
    variations: List[Dict[str, Any]]
    properties: Dict[str, Any]
    code_snippets: Dict[str, str]
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

class ProductDesigner(BaseRole):
    """产品设计师 - 负责用户体验设计和界面设计"""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            role_id="product_designer",
            role_name="产品设计师",
            config=config
        )
        
        # 设计工具配置
        self.design_tools = self._init_design_tools()
        
        # 设计资产存储
        self.design_assets: Dict[str, DesignAsset] = {}
        self.user_personas: Dict[str, UserPersona] = {}
        self.user_journeys: Dict[str, UserJourney] = {}
        self.usability_tests: Dict[str, UsabilityTest] = {}
        
        # 设计系统
        self.design_system: Dict[str, DesignSystemComponent] = {}
        
        # 设计标准配置
        self.design_standards = self._init_design_standards()
        
        # 当前设计项目
        self.current_projects: Dict[str, Dict[str, Any]] = {}
        
        # 消息处理器映射
        self.message_handlers.update({
            'analyze_user_requirements': self._handle_analyze_user_requirements,
            'create_user_personas': self._handle_create_user_personas,
            'design_user_journey': self._handle_design_user_journey,
            'create_wireframes': self._handle_create_wireframes,
            'design_interface': self._handle_design_interface,
            'create_prototype': self._handle_create_prototype,
            'conduct_usability_test': self._handle_conduct_usability_test,
            'evaluate_design': self._handle_evaluate_design,
            'create_design_system': self._handle_create_design_system,
            'review_implementation': self._handle_review_implementation
        })
        
        self.logger.info(f"{self.role_name} 初始化完成")
        
    def _init_design_tools(self) -> Dict[str, Any]:
        """初始化设计工具配置"""
        return {
            'design_software': {
                'primary': ['Figma', 'Sketch', 'Adobe XD'],
                'specialized': ['Principle', 'Framer', 'ProtoPie'],
                'handoff': ['Zeplin', 'Avocode', 'Figma Dev Mode']
            },
            'prototyping': {
                'low_fidelity': ['Balsamiq', 'Wireframe.cc', 'Draw.io'],
                'high_fidelity': ['InVision', 'Marvel', 'Principle'],
                'code_based': ['Framer X', 'React Storybook']
            },
            'user_research': {
                'surveys': ['Typeform', 'Google Forms', 'SurveyMonkey'],
                'interviews': ['Zoom', 'Loom', 'UserInterviews'],
                'testing': ['UserTesting', 'Maze', 'Hotjar'],
                'analytics': ['Google Analytics', 'Mixpanel', 'Amplitude']
            },
            'collaboration': {
                'documentation': ['Notion', 'Confluence', 'GitBook'],
                'whiteboarding': ['Miro', 'FigJam', 'Whimsical'],
                'feedback': ['InVision Comments', 'Figma Comments', 'ReviewBoard']
            }
        }
        
    def _init_design_standards(self) -> Dict[str, Any]:
        """初始化设计标准"""
        return {
            'accessibility': {
                'wcag_level': 'AA',
                'color_contrast_ratio': 4.5,
                'font_size_minimum': 16,
                'touch_target_minimum': 44
            },
            'responsive_breakpoints': {
                'mobile': 320,
                'tablet': 768,
                'desktop': 1024,
                'large_desktop': 1440
            },
            'design_tokens': {
                'colors': {
                    'primary': '#007bff',
                    'secondary': '#6c757d',
                    'success': '#28a745',
                    'warning': '#ffc107',
                    'danger': '#dc3545',
                    'info': '#17a2b8'
                },
                'typography': {
                    'font_family_primary': 'Inter, system-ui, sans-serif',
                    'font_family_monospace': 'Menlo, Monaco, monospace',
                    'font_sizes': [12, 14, 16, 18, 20, 24, 32, 48, 64],
                    'line_heights': [1.2, 1.4, 1.6, 1.8]
                },
                'spacing': [4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96],
                'shadows': {
                    'small': '0 1px 3px rgba(0,0,0,0.12)',
                    'medium': '0 4px 6px rgba(0,0,0,0.16)',
                    'large': '0 10px 25px rgba(0,0,0,0.19)'
                }
            },
            'animation': {
                'duration_fast': '150ms',
                'duration_normal': '300ms',
                'duration_slow': '500ms',
                'easing_standard': 'cubic-bezier(0.4, 0.0, 0.2, 1)',
                'easing_decelerate': 'cubic-bezier(0.0, 0.0, 0.2, 1)',
                'easing_accelerate': 'cubic-bezier(0.4, 0.0, 1, 1)'
            }
        }
        
    async def _handle_analyze_user_requirements(self, message):
        """处理用户需求分析请求"""
        try:
            data = message.body.data
            requirements = data.get('requirements', '')
            target_users = data.get('target_users', [])
            business_goals = data.get('business_goals', [])
            
            self.logger.info("开始分析用户需求")
            
            # 执行需求分析
            analysis_result = await self._analyze_requirements(requirements, target_users, business_goals)
            
            response_data = {
                'analysis_completed': True,
                'user_insights': analysis_result['user_insights'],
                'design_opportunities': analysis_result['design_opportunities'],
                'constraints': analysis_result['constraints'],
                'recommendations': analysis_result['recommendations']
            }
            
            await self._send_response(message, 'user_research_result', response_data)
            self.logger.info("用户需求分析完成")
            
        except Exception as e:
            self.logger.error(f"用户需求分析失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _analyze_requirements(self, requirements: str, target_users: List[str], business_goals: List[str]) -> Dict[str, Any]:
        """分析用户需求"""
        
        # 提取用户洞察
        user_insights = []
        if target_users:
            for user_type in target_users:
                user_insights.append({
                    'user_type': user_type,
                    'primary_needs': self._extract_user_needs(requirements, user_type),
                    'usage_context': self._analyze_usage_context(requirements, user_type),
                    'pain_points': self._identify_pain_points(requirements, user_type)
                })
        
        # 识别设计机会
        design_opportunities = [
            "简化用户操作流程，减少认知负担",
            "优化信息架构，提升内容可发现性",
            "增强视觉层次，改善界面可读性",
            "设计响应式布局，支持多设备使用"
        ]
        
        # 识别约束条件
        constraints = [
            "技术实现限制",
            "时间和资源约束",
            "兼容性要求",
            "可访问性标准"
        ]
        
        # 生成设计建议
        recommendations = [
            "进行用户访谈，深入了解用户需求",
            "创建用户画像，明确目标用户特征",
            "设计用户旅程地图，优化体验流程",
            "制作原型进行早期验证"
        ]
        
        return {
            'user_insights': user_insights,
            'design_opportunities': design_opportunities,
            'constraints': constraints,
            'recommendations': recommendations
        }
        
    def _extract_user_needs(self, requirements: str, user_type: str) -> List[str]:
        """提取用户需求"""
        # 简化的需求提取逻辑
        needs = []
        if '管理' in requirements:
            needs.append('需要高效的管理工具')
        if '查看' in requirements or '浏览' in requirements:
            needs.append('需要清晰的信息展示')
        if '操作' in requirements:
            needs.append('需要简单直观的操作界面')
        if '数据' in requirements:
            needs.append('需要准确的数据展示和分析')
            
        return needs or ['需要明确的功能定义']
        
    def _analyze_usage_context(self, requirements: str, user_type: str) -> Dict[str, Any]:
        """分析使用场景"""
        return {
            'primary_devices': ['desktop', 'mobile'],
            'usage_frequency': 'daily',
            'usage_duration': 'medium',
            'environment': 'office'
        }
        
    def _identify_pain_points(self, requirements: str, user_type: str) -> List[str]:
        """识别痛点"""
        return [
            '操作流程复杂',
            '信息获取困难',
            '响应速度慢',
            '界面不够直观'
        ]
        
    async def _handle_create_user_personas(self, message):
        """处理创建用户画像请求"""
        try:
            data = message.body.data
            user_research_data = data.get('user_research_data', {})
            target_segments = data.get('target_segments', [])
            
            self.logger.info("开始创建用户画像")
            
            # 创建用户画像
            personas = await self._create_personas(user_research_data, target_segments)
            
            # 存储用户画像
            for persona in personas:
                self.user_personas[persona.persona_id] = persona
                
            response_data = {
                'personas_created': len(personas),
                'personas': [asdict(persona) for persona in personas]
            }
            
            await self._send_response(message, 'user_personas', response_data)
            self.logger.info(f"用户画像创建完成，共创建 {len(personas)} 个画像")
            
        except Exception as e:
            self.logger.error(f"用户画像创建失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _create_personas(self, research_data: Dict, segments: List[str]) -> List[UserPersona]:
        """创建用户画像"""
        personas = []
        
        # 根据用户细分创建画像
        if not segments:
            segments = ['primary_user', 'secondary_user']
            
        for i, segment in enumerate(segments):
            persona = UserPersona(
                persona_id=str(uuid.uuid4()),
                name=f"用户{chr(65+i)}",  # 用户A, 用户B, etc.
                age_range="25-35",
                occupation="知识工作者",
                goals=[
                    "高效完成工作任务",
                    "获取准确的信息",
                    "简化操作流程"
                ],
                pain_points=[
                    "界面操作复杂",
                    "信息查找困难",
                    "响应速度慢"
                ],
                behaviors=[
                    "经常使用移动设备",
                    "偏好简洁的界面",
                    "重视操作效率"
                ],
                tech_proficiency="中等",
                preferred_devices=["desktop", "mobile"]
            )
            personas.append(persona)
            
        return personas
        
    async def _handle_design_user_journey(self, message):
        """处理用户旅程设计请求"""
        try:
            data = message.body.data
            persona_id = data.get('persona_id')
            scenario = data.get('scenario', '')
            key_tasks = data.get('key_tasks', [])
            
            self.logger.info(f"开始设计用户旅程: {scenario}")
            
            # 设计用户旅程
            journey = await self._design_journey(persona_id, scenario, key_tasks)
            
            # 存储用户旅程
            self.user_journeys[journey.journey_id] = journey
            
            response_data = {
                'journey_created': True,
                'journey': asdict(journey)
            }
            
            await self._send_response(message, 'user_journey_map', response_data)
            self.logger.info("用户旅程设计完成")
            
        except Exception as e:
            self.logger.error(f"用户旅程设计失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _design_journey(self, persona_id: str, scenario: str, tasks: List[str]) -> UserJourney:
        """设计用户旅程"""
        
        # 定义旅程阶段
        stages = [
            {
                'stage': 'awareness',
                'name': '认知阶段',
                'user_actions': ['发现问题', '寻找解决方案'],
                'emotions': ['好奇', '期待'],
                'touchpoints': ['搜索引擎', '社交媒体']
            },
            {
                'stage': 'consideration',
                'name': '考虑阶段', 
                'user_actions': ['比较选项', '评估特性'],
                'emotions': ['谨慎', '比较'],
                'touchpoints': ['产品页面', '功能介绍']
            },
            {
                'stage': 'usage',
                'name': '使用阶段',
                'user_actions': ['注册账号', '学习使用', '执行任务'],
                'emotions': ['学习', '专注', '成就感'],
                'touchpoints': ['登录页面', '主界面', '功能页面']
            },
            {
                'stage': 'advocacy',
                'name': '推荐阶段',
                'user_actions': ['分享体验', '推荐他人'],
                'emotions': ['满意', '自豪'],
                'touchpoints': ['分享功能', '推荐页面']
            }
        ]
        
        journey = UserJourney(
            journey_id=str(uuid.uuid4()),
            persona_id=persona_id or 'default',
            scenario=scenario,
            stages=stages,
            touchpoints=['网站首页', '产品界面', '帮助中心', '客服系统'],
            pain_points=['学习成本高', '操作复杂', '反馈不及时'],
            opportunities=['简化操作流程', '提供引导教程', '优化反馈机制']
        )
        
        return journey
        
    async def _handle_create_wireframes(self, message):
        """处理线框图创建请求"""
        try:
            data = message.body.data
            page_type = data.get('page_type', 'general')
            device_type = data.get('device_type', 'desktop')
            content_requirements = data.get('content_requirements', {})
            
            self.logger.info(f"开始创建线框图: {page_type} - {device_type}")
            
            # 创建线框图
            wireframe = await self._create_wireframe(page_type, device_type, content_requirements)
            
            # 存储设计资产
            self.design_assets[wireframe.asset_id] = wireframe
            
            response_data = {
                'wireframe_created': True,
                'wireframe': asdict(wireframe),
                'design_notes': self._generate_wireframe_notes(page_type, device_type)
            }
            
            await self._send_response(message, 'wireframes', response_data)
            self.logger.info("线框图创建完成")
            
        except Exception as e:
            self.logger.error(f"线框图创建失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _create_wireframe(self, page_type: str, device_type: str, requirements: Dict) -> DesignAsset:
        """创建线框图"""
        
        wireframe_id = str(uuid.uuid4())
        
        wireframe = DesignAsset(
            asset_id=wireframe_id,
            asset_type=DesignType.WIREFRAME,
            title=f"{page_type.title()} 页面线框图",
            description=f"用于 {device_type} 设备的 {page_type} 页面线框图",
            device_type=DeviceType(device_type),
            file_path=f"wireframes/{wireframe_id}.fig",
            version="1.0",
            status="draft",
            tags=[page_type, device_type, "wireframe"]
        )
        
        return wireframe
        
    def _generate_wireframe_notes(self, page_type: str, device_type: str) -> List[str]:
        """生成线框图设计说明"""
        notes = [
            f"基于 {device_type} 设备特性进行布局设计",
            "重点关注信息层次和内容组织",
            "确保核心功能在首屏可见",
            "预留响应式适配空间"
        ]
        
        if page_type == 'dashboard':
            notes.extend([
                "仪表板布局采用卡片式设计",
                "重要指标突出显示",
                "支持自定义和个性化配置"
            ])
        elif page_type == 'form':
            notes.extend([
                "表单字段逻辑分组",
                "必填字段明确标识",
                "提供清晰的错误提示"
            ])
            
        return notes
        
    async def _handle_create_prototype(self, message):
        """处理原型创建请求"""
        try:
            data = message.body.data
            wireframe_ids = data.get('wireframe_ids', [])
            interaction_flows = data.get('interaction_flows', [])
            fidelity_level = data.get('fidelity_level', 'high')
            
            self.logger.info(f"开始创建原型: 保真度={fidelity_level}")
            
            # 创建原型
            prototype = await self._create_prototype_asset(wireframe_ids, interaction_flows, fidelity_level)
            
            # 存储原型
            self.design_assets[prototype.asset_id] = prototype
            
            response_data = {
                'prototype_created': True,
                'prototype': asdict(prototype),
                'interaction_notes': self._generate_interaction_notes(interaction_flows)
            }
            
            await self._send_response(message, 'prototype_ready', response_data)
            self.logger.info("原型创建完成")
            
        except Exception as e:
            self.logger.error(f"原型创建失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _create_prototype_asset(self, wireframe_ids: List[str], flows: List[Dict], fidelity: str) -> DesignAsset:
        """创建原型资产"""
        
        prototype_id = str(uuid.uuid4())
        
        prototype = DesignAsset(
            asset_id=prototype_id,
            asset_type=DesignType.PROTOTYPE,
            title=f"{fidelity.title()} 保真度原型",
            description="可交互的产品原型，用于用户测试和开发参考",
            device_type=DeviceType.DESKTOP,  # 默认桌面端
            file_path=f"prototypes/{prototype_id}.fig",
            version="1.0",
            status="ready_for_testing",
            tags=[fidelity, "prototype", "interactive"]
        )
        
        return prototype
        
    def _generate_interaction_notes(self, flows: List[Dict]) -> List[str]:
        """生成交互说明"""
        notes = [
            "原型包含主要用户流程的交互",
            "点击热区已标记，支持用户测试",
            "动画效果遵循设计系统规范",
            "状态变化提供适当的视觉反馈"
        ]
        
        if flows:
            notes.append(f"实现了 {len(flows)} 个关键交互流程")
            
        return notes
        
    async def _handle_conduct_usability_test(self, message):
        """处理可用性测试请求"""
        try:
            data = message.body.data
            prototype_id = data.get('prototype_id')
            test_scenarios = data.get('test_scenarios', [])
            participant_count = data.get('participant_count', 5)
            
            self.logger.info(f"开始可用性测试: 参与者={participant_count}人")
            
            # 执行可用性测试
            test_result = await self._conduct_usability_testing(prototype_id, test_scenarios, participant_count)
            
            # 存储测试结果
            self.usability_tests[test_result.test_id] = test_result
            
            response_data = {
                'test_completed': True,
                'test_result': asdict(test_result),
                'usability_score': self._calculate_usability_score(test_result),
                'priority_issues': self._identify_priority_issues(test_result)
            }
            
            await self._send_response(message, 'usability_test_report', response_data)
            self.logger.info("可用性测试完成")
            
        except Exception as e:
            self.logger.error(f"可用性测试失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _conduct_usability_testing(self, prototype_id: str, scenarios: List[Dict], participants: int) -> UsabilityTest:
        """执行可用性测试"""
        
        # 模拟测试任务
        test_tasks = [
            {
                'task_id': 'task_1',
                'description': '完成用户注册流程',
                'success_rate': 0.8,
                'average_time': 120,
                'error_count': 1
            },
            {
                'task_id': 'task_2', 
                'description': '查找并使用核心功能',
                'success_rate': 0.9,
                'average_time': 90,
                'error_count': 0
            },
            {
                'task_id': 'task_3',
                'description': '完成设置配置',
                'success_rate': 0.7,
                'average_time': 180,
                'error_count': 2
            }
        ]
        
        # 计算综合指标
        metrics = {
            'overall_success_rate': sum(task['success_rate'] for task in test_tasks) / len(test_tasks),
            'average_completion_time': sum(task['average_time'] for task in test_tasks) / len(test_tasks),
            'total_errors': sum(task['error_count'] for task in test_tasks),
            'satisfaction_score': 4.2  # 5分制
        }
        
        # 主要发现
        findings = [
            "用户对整体界面布局反馈积极",
            "注册流程中的验证步骤造成困扰",
            "核心功能易于发现和使用",
            "设置页面信息层次需要优化"
        ]
        
        # 改进建议
        recommendations = [
            "简化注册验证流程",
            "优化设置页面的信息组织",
            "增加操作反馈的及时性",
            "改善错误提示的友好性"
        ]
        
        test = UsabilityTest(
            test_id=str(uuid.uuid4()),
            test_name=f"原型可用性测试 - {datetime.now().strftime('%Y%m%d')}",
            test_type="moderated_remote",
            participants=participants,
            tasks=test_tasks,
            metrics=metrics,
            findings=findings,
            recommendations=recommendations
        )
        
        return test
        
    def _calculate_usability_score(self, test: UsabilityTest) -> float:
        """计算可用性分数"""
        success_weight = 0.4
        time_weight = 0.3
        error_weight = 0.2
        satisfaction_weight = 0.1
        
        # 标准化各项指标 (0-100分)
        success_score = test.metrics['overall_success_rate'] * 100
        time_score = max(0, 100 - (test.metrics['average_completion_time'] - 60) / 2)  # 60秒为基准
        error_score = max(0, 100 - test.metrics['total_errors'] * 10)
        satisfaction_score = test.metrics['satisfaction_score'] * 20  # 5分制转100分制
        
        overall_score = (
            success_score * success_weight +
            time_score * time_weight +
            error_score * error_weight +
            satisfaction_score * satisfaction_weight
        )
        
        return round(overall_score, 1)
        
    def _identify_priority_issues(self, test: UsabilityTest) -> List[Dict[str, Any]]:
        """识别优先级问题"""
        issues = []
        
        # 基于成功率识别问题
        for task in test.tasks:
            if task['success_rate'] < 0.8:
                issues.append({
                    'type': 'task_success',
                    'severity': 'high' if task['success_rate'] < 0.6 else 'medium',
                    'description': f"任务「{task['description']}」成功率偏低",
                    'impact': 'user_completion'
                })
                
        # 基于错误数量识别问题
        if test.metrics['total_errors'] > 3:
            issues.append({
                'type': 'user_errors',
                'severity': 'high',
                'description': '用户操作错误频发',
                'impact': 'user_experience'
            })
            
        return issues
        
    async def _handle_evaluate_design(self, message):
        """处理设计评估请求"""
        try:
            data = message.body.data
            design_id = data.get('design_id')
            evaluation_criteria = data.get('criteria', [])
            
            self.logger.info(f"开始设计评估: {design_id}")
            
            # 执行设计评估
            evaluation = await self._evaluate_design_quality(design_id, evaluation_criteria)
            
            response_data = {
                'evaluation_completed': True,
                'design_id': design_id,
                'overall_score': evaluation['overall_score'],
                'criteria_scores': evaluation['criteria_scores'],
                'strengths': evaluation['strengths'],
                'improvements': evaluation['improvements'],
                'recommendations': evaluation['recommendations']
            }
            
            await self._send_response(message, 'design_evaluation', response_data)
            self.logger.info("设计评估完成")
            
        except Exception as e:
            self.logger.error(f"设计评估失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _evaluate_design_quality(self, design_id: str, criteria: List[str]) -> Dict[str, Any]:
        """评估设计质量"""
        
        # 默认评估标准
        default_criteria = [
            'usability', 'visual_design', 'consistency', 
            'accessibility', 'responsiveness'
        ]
        
        eval_criteria = criteria or default_criteria
        
        # 模拟评估分数
        criteria_scores = {}
        for criterion in eval_criteria:
            if criterion == 'usability':
                criteria_scores[criterion] = 85
            elif criterion == 'visual_design':
                criteria_scores[criterion] = 90
            elif criterion == 'consistency':
                criteria_scores[criterion] = 88
            elif criterion == 'accessibility':
                criteria_scores[criterion] = 75
            elif criterion == 'responsiveness':
                criteria_scores[criterion] = 82
            else:
                criteria_scores[criterion] = 80
                
        # 计算总分
        overall_score = sum(criteria_scores.values()) / len(criteria_scores)
        
        # 识别优势
        strengths = [
            "视觉设计现代简洁",
            "界面布局清晰合理",
            "交互流程符合用户习惯"
        ]
        
        # 识别改进点
        improvements = [
            "可访问性标准需要加强",
            "移动端适配可以优化",
            "加载状态反馈需要完善"
        ]
        
        # 改进建议
        recommendations = [
            "增加键盘导航支持",
            "优化移动端触控体验",
            "完善异常状态的设计",
            "建立更完整的设计系统"
        ]
        
        return {
            'overall_score': round(overall_score, 1),
            'criteria_scores': criteria_scores,
            'strengths': strengths,
            'improvements': improvements,
            'recommendations': recommendations
        }
        
    async def _handle_create_design_system(self, message):
        """处理设计系统创建请求"""
        try:
            data = message.body.data
            system_scope = data.get('scope', 'basic')
            brand_guidelines = data.get('brand_guidelines', {})
            
            self.logger.info(f"开始创建设计系统: 范围={system_scope}")
            
            # 创建设计系统
            components = await self._create_design_system_components(system_scope, brand_guidelines)
            
            # 存储设计系统组件
            for component in components:
                self.design_system[component.component_id] = component
                
            response_data = {
                'design_system_created': True,
                'components_count': len(components),
                'components': [asdict(comp) for comp in components],
                'system_documentation': self._generate_system_documentation()
            }
            
            await self._send_response(message, 'design_system_spec', response_data)
            self.logger.info(f"设计系统创建完成，包含 {len(components)} 个组件")
            
        except Exception as e:
            self.logger.error(f"设计系统创建失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _create_design_system_components(self, scope: str, guidelines: Dict) -> List[DesignSystemComponent]:
        """创建设计系统组件"""
        components = []
        
        # 基础组件
        basic_components = [
            {
                'name': 'Button',
                'type': 'interaction',
                'description': '通用按钮组件，支持多种样式和状态',
                'variations': [
                    {'name': 'Primary', 'usage': '主要操作'},
                    {'name': 'Secondary', 'usage': '次要操作'},
                    {'name': 'Text', 'usage': '文本链接式操作'}
                ]
            },
            {
                'name': 'Input',
                'type': 'form',
                'description': '文本输入框组件，支持验证和错误状态',
                'variations': [
                    {'name': 'Text', 'usage': '单行文本输入'},
                    {'name': 'Textarea', 'usage': '多行文本输入'},
                    {'name': 'Password', 'usage': '密码输入'}
                ]
            },
            {
                'name': 'Card',
                'type': 'layout',
                'description': '卡片容器组件，用于内容分组',
                'variations': [
                    {'name': 'Basic', 'usage': '基础内容卡片'},
                    {'name': 'Media', 'usage': '包含媒体的卡片'},
                    {'name': 'Action', 'usage': '包含操作的卡片'}
                ]
            }
        ]
        
        # 如果是完整范围，添加更多组件
        if scope == 'comprehensive':
            basic_components.extend([
                {
                    'name': 'Navigation',
                    'type': 'navigation',
                    'description': '导航组件，支持多级菜单',
                    'variations': [
                        {'name': 'Horizontal', 'usage': '顶部横向导航'},
                        {'name': 'Vertical', 'usage': '侧边垂直导航'},
                        {'name': 'Breadcrumb', 'usage': '面包屑导航'}
                    ]
                },
                {
                    'name': 'Modal',
                    'type': 'overlay',
                    'description': '模态对话框组件',
                    'variations': [
                        {'name': 'Confirmation', 'usage': '确认对话框'},
                        {'name': 'Form', 'usage': '表单对话框'},
                        {'name': 'Info', 'usage': '信息展示对话框'}
                    ]
                }
            ])
            
        # 创建组件对象
        for comp_data in basic_components:
            component = DesignSystemComponent(
                component_id=str(uuid.uuid4()),
                component_name=comp_data['name'],
                component_type=comp_data['type'],
                description=comp_data['description'],
                usage_guidelines=f"{comp_data['name']} 组件的使用指南和最佳实践",
                variations=comp_data['variations'],
                properties={
                    'colors': ['primary', 'secondary', 'success', 'warning', 'danger'],
                    'sizes': ['small', 'medium', 'large'],
                    'states': ['default', 'hover', 'active', 'disabled']
                },
                code_snippets={
                    'react': f"<{comp_data['name']} />",
                    'vue': f"<{comp_data['name'].lower()} />",
                    'html': f"<div class=\"{comp_data['name'].lower()}\"></div>"
                }
            )
            components.append(component)
            
        return components
        
    def _generate_system_documentation(self) -> Dict[str, Any]:
        """生成设计系统文档"""
        return {
            'overview': '完整的设计系统规范，包含组件库、设计标准和使用指南',
            'principles': [
                '一致性：统一的视觉语言和交互模式',
                '可访问性：符合WCAG标准的设计实践',
                '可扩展性：支持组件变体和主题定制',
                '开发友好：提供完整的实现规范'
            ],
            'structure': {
                'foundations': '基础元素（颜色、字体、间距等）',
                'components': '可复用的UI组件',
                'patterns': '常见的交互模式和布局',
                'guidelines': '设计和使用指南'
            },
            'maintenance': {
                'versioning': '版本管理策略',
                'updates': '组件更新流程',
                'contribution': '贡献指南和评审流程'
            }
        }
        
    async def _initialize_role(self):
        """初始化角色特定资源"""
        self.logger.info(f"{self.role_name} 角色初始化完成")
        
    async def _cleanup_role(self):
        """清理角色特定资源"""
        self.logger.info(f"{self.role_name} 角色清理完成")
        
    async def _process_task(self, task: Task):
        """处理任务"""
        self.logger.info(f"处理任务: {task.task_id}")
        # 简化处理
        task.status = TaskStatus.COMPLETED
        
    async def _handle_custom_message(self, message):
        """处理自定义消息"""
        self.logger.info(f"收到自定义消息: {message}")
        return "处理完成"
        
    async def _handle_review_implementation(self, message):
        """处理实现审查请求"""
        try:
            data = message.body.data
            implementation_url = data.get('implementation_url', '')
            design_id = data.get('design_id', '')
            
            self.logger.info("开始审查开发实现")
            
            # 审查实现与设计的一致性
            review_result = await self._review_implementation_consistency(implementation_url, design_id)
            
            response_data = {
                'review_completed': True,
                'consistency_score': review_result['consistency_score'],
                'issues_found': review_result['issues'],
                'recommendations': review_result['recommendations'],
                'approved': review_result['consistency_score'] >= 80
            }
            
            await self._send_response(message, 'implementation_feedback', response_data)
            self.logger.info("实现审查完成")
            
        except Exception as e:
            self.logger.error(f"实现审查失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _review_implementation_consistency(self, url: str, design_id: str) -> Dict[str, Any]:
        """审查实现一致性"""
        
        # 模拟审查结果
        issues = [
            {
                'type': 'spacing',
                'severity': 'minor',
                'description': '页面边距与设计稿存在2px差异',
                'location': 'header section'
            },
            {
                'type': 'color',
                'severity': 'medium',
                'description': '按钮颜色不符合设计系统规范',
                'location': 'primary button'
            }
        ]
        
        recommendations = [
            "使用CSS变量确保颜色一致性",
            "建立设计标记(Design Tokens)系统",
            "增加视觉回归测试",
            "定期进行设计与开发对比检查"
        ]
        
        # 计算一致性分数
        consistency_score = 85  # 模拟分数
        
        return {
            'consistency_score': consistency_score,
            'issues': issues,
            'recommendations': recommendations
        }
        
    async def _handle_design_interface(self, message):
        """处理界面设计请求"""
        try:
            data = message.body.data
            wireframe_id = data.get('wireframe_id', '')
            design_requirements = data.get('design_requirements', {})
            
            self.logger.info("开始界面视觉设计")
            
            # 创建界面设计
            interface_design = await self._create_interface_design(wireframe_id, design_requirements)
            
            # 存储设计资产
            self.design_assets[interface_design.asset_id] = interface_design
            
            response_data = {
                'design_created': True,
                'design': asdict(interface_design),
                'design_specifications': self._generate_design_specifications(design_requirements)
            }
            
            await self._send_response(message, 'interface_design', response_data)
            self.logger.info("界面设计创建完成")
            
        except Exception as e:
            self.logger.error(f"界面设计失败: {e}")
            await self._send_error_response(message, str(e))
            
    async def _create_interface_design(self, wireframe_id: str, requirements: Dict) -> DesignAsset:
        """创建界面设计"""
        design_id = str(uuid.uuid4())
        
        design = DesignAsset(
            asset_id=design_id,
            asset_type=DesignType.MOCKUP,
            title="界面视觉设计稿",
            description="高保真界面设计，包含完整的视觉样式",
            device_type=DeviceType.DESKTOP,
            file_path=f"designs/{design_id}.fig",
            version="1.0",
            status="ready_for_development",
            tags=["interface", "visual", "mockup"]
        )
        
        return design
        
    def _generate_design_specifications(self, requirements: Dict) -> Dict[str, Any]:
        """生成设计规范"""
        return {
            'colors': {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'success': '#28a745',
                'warning': '#ffc107',
                'danger': '#dc3545'
            },
            'typography': {
                'headings': 'Inter Bold',
                'body': 'Inter Regular',
                'sizes': ['14px', '16px', '18px', '24px', '32px']
            },
            'spacing': {
                'base_unit': '8px',
                'margins': ['8px', '16px', '24px', '32px'],
                'paddings': ['8px', '16px', '24px', '32px']
            },
            'components': {
                'buttons': 'rounded corners, 8px padding',
                'cards': '4px border radius, subtle shadow',
                'forms': 'clear labels, validation states'
            }
        }