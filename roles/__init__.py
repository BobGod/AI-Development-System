"""
AI自主开发系统 - 角色模块
包含所有AI角色的实现
"""

from .base_role import BaseRole, Task, TaskStatus, RoleState
from .master_controller import MasterController, ProjectPhase, DecisionType
from .memory_manager_simple import MemoryManager, DataType, MemoryEntry
from .devops_engineer import DevOpsEngineer, DeploymentStrategy, EnvironmentType
from .quality_guardian import QualityGuardian, QualityLevel, IssueType, IssueSeverity
from .product_designer import ProductDesigner, DesignPhase, DeviceType, DesignType

__all__ = [
    'BaseRole',
    'Task', 
    'TaskStatus',
    'RoleState',
    'MasterController',
    'ProjectPhase',
    'DecisionType', 
    'MemoryManager',
    'DataType',
    'MemoryEntry',
    'DevOpsEngineer',
    'DeploymentStrategy',
    'EnvironmentType',
    'QualityGuardian',
    'QualityLevel',
    'IssueType',
    'IssueSeverity',
    'ProductDesigner',
    'DesignPhase',
    'DeviceType',
    'DesignType'
]

__version__ = '1.0.0'