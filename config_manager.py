#!/usr/bin/env python3
"""
AI自主开发系统 - 配置管理器
负责管理系统配置、环境变量和运行时参数
"""

import json
import os
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict
import logging
from enum import Enum


class ConfigType(Enum):
    """配置类型枚举"""
    SYSTEM = "system"
    ROLE = "role"
    COMMUNICATION = "communication"
    STORAGE = "storage"
    SECURITY = "security"
    MONITORING = "monitoring"


@dataclass
class SystemConfig:
    """系统配置"""
    name: str = "AI自主开发系统"
    version: str = "1.0.0"
    environment: str = "development"  # development, staging, production
    log_level: str = "INFO"
    session_timeout: int = 3600
    max_concurrent_tasks: int = 10
    debug_mode: bool = False


@dataclass
class RoleConfig:
    """角色配置"""
    role_id: str
    role_name: str
    enabled: bool = True
    max_concurrent_tasks: int = 3
    timeout_seconds: int = 300
    auto_restart: bool = True
    priority: int = 1
    config_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config_params is None:
            self.config_params = {}


@dataclass
class CommunicationConfig:
    """通信配置"""
    message_queue_size: int = 1000
    message_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 2
    num_workers: int = 3
    enable_compression: bool = False
    enable_encryption: bool = False


@dataclass
class StorageConfig:
    """存储配置"""
    data_path: str = "data"
    backup_path: str = "backup"
    backup_interval: int = 300
    backup_retention_days: int = 7
    enable_compression: bool = True
    max_file_size_mb: int = 100


@dataclass
class SecurityConfig:
    """安全配置"""
    enable_encryption: bool = False
    session_security: bool = True
    audit_logging: bool = True
    max_login_attempts: int = 3
    password_min_length: int = 8
    api_rate_limit: int = 100


@dataclass
class MonitoringConfig:
    """监控配置"""
    health_check_interval: int = 30
    performance_monitoring: bool = True
    log_retention_days: int = 30
    metrics_collection: bool = True
    alert_thresholds: Dict[str, Union[int, float]] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'cpu_usage': 80,
                'memory_usage': 85,
                'response_time': 5000,
                'error_rate': 0.05
            }


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.system_config_path = self.config_dir / "system_config.json"
        self.roles_config_path = self.config_dir / "roles_config.json"
        self.communication_config_path = self.config_dir / "communication_config.json"
        self.storage_config_path = self.config_dir / "storage_config.json"
        self.security_config_path = self.config_dir / "security_config.json"
        self.monitoring_config_path = self.config_dir / "monitoring_config.json"
        
        # 配置缓存
        self._config_cache: Dict[str, Any] = {}
        self._watchers: List[callable] = []
        
        # 日志
        self.logger = logging.getLogger('ConfigManager')
        
        # 初始化配置
        self._initialize_configs()
        
    def _initialize_configs(self):
        """初始化配置文件"""
        try:
            # 如果配置文件不存在，创建默认配置
            if not self.system_config_path.exists():
                self._create_default_system_config()
                
            if not self.roles_config_path.exists():
                self._create_default_roles_config()
                
            if not self.communication_config_path.exists():
                self._create_default_communication_config()
                
            if not self.storage_config_path.exists():
                self._create_default_storage_config()
                
            if not self.security_config_path.exists():
                self._create_default_security_config()
                
            if not self.monitoring_config_path.exists():
                self._create_default_monitoring_config()
                
            # 加载所有配置到缓存
            self._load_all_configs()
            
        except Exception as e:
            self.logger.error(f"初始化配置失败: {e}")
            raise
            
    def _create_default_system_config(self):
        """创建默认系统配置"""
        default_config = SystemConfig()
        self._save_config(self.system_config_path, asdict(default_config))
        
    def _create_default_roles_config(self):
        """创建默认角色配置"""
        default_roles = {
            "master_controller": RoleConfig(
                role_id="master_controller",
                role_name="项目总控制器",
                max_concurrent_tasks=5,
                timeout_seconds=300,
                priority=1
            ),
            "memory_manager": RoleConfig(
                role_id="memory_manager",
                role_name="记忆管理器",
                max_concurrent_tasks=3,
                timeout_seconds=180,
                priority=1,
                config_params={
                    "storage_path": "data/memory",
                    "backup_interval": 300
                }
            ),
            "status_monitor": RoleConfig(
                role_id="status_monitor",
                role_name="状态监控器",
                max_concurrent_tasks=2,
                timeout_seconds=60,
                priority=1,
                config_params={
                    "check_interval": 30
                }
            ),
            "requirements_parser": RoleConfig(
                role_id="requirements_parser",
                role_name="需求解析器",
                max_concurrent_tasks=3,
                timeout_seconds=240,
                priority=2
            ),
            "system_architect": RoleConfig(
                role_id="system_architect",
                role_name="系统架构师",
                max_concurrent_tasks=2,
                timeout_seconds=600,
                priority=2
            ),
            "frontend_dev": RoleConfig(
                role_id="frontend_dev",
                role_name="前端开发工程师",
                max_concurrent_tasks=4,
                timeout_seconds=900,
                priority=3,
                config_params={
                    "tech_stack": ["React", "Vue", "TypeScript"]
                }
            ),
            "backend_dev": RoleConfig(
                role_id="backend_dev",
                role_name="后端开发工程师",
                max_concurrent_tasks=4,
                timeout_seconds=900,
                priority=3,
                config_params={
                    "tech_stack": ["Node.js", "Python", "Java"]
                }
            ),
            "fullstack_dev": RoleConfig(
                role_id="fullstack_dev",
                role_name="全栈开发工程师",
                max_concurrent_tasks=3,
                timeout_seconds=1200,
                priority=3,
                config_params={
                    "tech_stack": ["MEAN", "MERN", "Django"]
                }
            ),
            "mobile_dev": RoleConfig(
                role_id="mobile_dev",
                role_name="移动端开发工程师",
                enabled=False,
                max_concurrent_tasks=2,
                timeout_seconds=1200,
                priority=4,
                config_params={
                    "tech_stack": ["React Native", "Flutter", "Swift"]
                }
            ),
            "test_engineer": RoleConfig(
                role_id="test_engineer",
                role_name="测试工程师",
                max_concurrent_tasks=3,
                timeout_seconds=600,
                priority=3,
                config_params={
                    "coverage_threshold": 80
                }
            ),
            "devops_engineer": RoleConfig(
                role_id="devops_engineer",
                role_name="DevOps工程师",
                max_concurrent_tasks=4,
                timeout_seconds=1800,
                priority=2,
                config_params={
                    "deployment_strategies": ["blue_green", "canary", "rolling"],
                    "environments": ["development", "testing", "staging", "production"],
                    "monitoring_interval": 60,
                    "health_check_interval": 300,
                    "security_scan_interval": 3600,
                    "alert_thresholds": {
                        "cpu_usage": 80,
                        "memory_usage": 85,
                        "response_time": 10000,
                        "error_rate": 5
                    }
                }
            ),
            "quality_guardian": RoleConfig(
                role_id="quality_guardian",
                role_name="质量守护者",
                max_concurrent_tasks=3,
                timeout_seconds=1200,
                priority=2,
                config_params={
                    "quality_rules": {
                        "max_complexity": 10,
                        "min_coverage": 80,
                        "max_duplication": 5,
                        "min_maintainability": 80
                    },
                    "analysis_tools": {
                        "python": ["pylint", "flake8", "bandit", "mypy"],
                        "javascript": ["eslint", "jshint"],
                        "typescript": ["tslint", "eslint"]
                    },
                    "quality_gates": {
                        "block_critical_issues": True,
                        "block_security_issues": True,
                        "warning_threshold": 5
                    },
                    "tech_debt_thresholds": {
                        "max_debt_ratio": 5,
                        "review_interval": 604800
                    }
                }
            ),
            "product_designer": RoleConfig(
                role_id="product_designer",
                role_name="产品设计师",
                max_concurrent_tasks=3,
                timeout_seconds=1800,
                priority=2,
                config_params={
                    "design_tools": {
                        "primary": ["Figma", "Sketch", "Adobe XD"],
                        "prototyping": ["InVision", "Marvel", "Principle"],
                        "research": ["Miro", "UserTesting", "Hotjar"]
                    },
                    "design_standards": {
                        "accessibility_level": "AA",
                        "color_contrast_ratio": 4.5,
                        "min_font_size": 16,
                        "min_touch_target": 44
                    },
                    "supported_devices": ["desktop", "tablet", "mobile"],
                    "design_phases": ["research", "wireframing", "prototyping", "testing"],
                    "usability_thresholds": {
                        "min_success_rate": 80,
                        "max_completion_time": 300,
                        "max_error_rate": 5,
                        "min_satisfaction": 4.0
                    }
                }
            )
        }
        
        # 转换为字典格式
        roles_dict = {role_id: asdict(config) for role_id, config in default_roles.items()}
        self._save_config(self.roles_config_path, roles_dict)
        
    def _create_default_communication_config(self):
        """创建默认通信配置"""
        default_config = CommunicationConfig()
        self._save_config(self.communication_config_path, asdict(default_config))
        
    def _create_default_storage_config(self):
        """创建默认存储配置"""
        default_config = StorageConfig()
        self._save_config(self.storage_config_path, asdict(default_config))
        
    def _create_default_security_config(self):
        """创建默认安全配置"""
        default_config = SecurityConfig()
        self._save_config(self.security_config_path, asdict(default_config))
        
    def _create_default_monitoring_config(self):
        """创建默认监控配置"""
        default_config = MonitoringConfig()
        self._save_config(self.monitoring_config_path, asdict(default_config))
        
    def _save_config(self, file_path: Path, config_data: Dict[str, Any]):
        """保存配置到文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存配置文件失败 {file_path}: {e}")
            raise
            
    def _load_config(self, file_path: Path) -> Dict[str, Any]:
        """从文件加载配置"""
        try:
            if not file_path.exists():
                return {}
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"加载配置文件失败 {file_path}: {e}")
            return {}
            
    def _load_all_configs(self):
        """加载所有配置到缓存"""
        self._config_cache = {
            ConfigType.SYSTEM.value: self._load_config(self.system_config_path),
            ConfigType.ROLE.value: self._load_config(self.roles_config_path),
            ConfigType.COMMUNICATION.value: self._load_config(self.communication_config_path),
            ConfigType.STORAGE.value: self._load_config(self.storage_config_path),
            ConfigType.SECURITY.value: self._load_config(self.security_config_path),
            ConfigType.MONITORING.value: self._load_config(self.monitoring_config_path)
        }
        
    def get_system_config(self) -> SystemConfig:
        """获取系统配置"""
        config_dict = self._config_cache.get(ConfigType.SYSTEM.value, {})
        # 处理嵌套的system配置
        if 'system' in config_dict:
            config_dict = config_dict['system']
        return SystemConfig(**config_dict)
        
    def get_role_config(self, role_id: str) -> Optional[RoleConfig]:
        """获取角色配置"""
        roles_config = self._config_cache.get(ConfigType.ROLE.value, {})
        role_dict = roles_config.get(role_id)
        
        if role_dict:
            return RoleConfig(**role_dict)
        return None
        
    def get_all_role_configs(self) -> Dict[str, RoleConfig]:
        """获取所有角色配置"""
        roles_config = self._config_cache.get(ConfigType.ROLE.value, {})
        return {
            role_id: RoleConfig(**config_dict) 
            for role_id, config_dict in roles_config.items()
        }
        
    def get_communication_config(self) -> CommunicationConfig:
        """获取通信配置"""
        config_dict = self._config_cache.get(ConfigType.COMMUNICATION.value, {})
        # 处理嵌套的communication配置
        if 'communication' in config_dict:
            config_dict = config_dict['communication']
        return CommunicationConfig(**config_dict)
        
    def get_storage_config(self) -> StorageConfig:
        """获取存储配置"""
        config_dict = self._config_cache.get(ConfigType.STORAGE.value, {})
        return StorageConfig(**config_dict)
        
    def get_security_config(self) -> SecurityConfig:
        """获取安全配置"""
        config_dict = self._config_cache.get(ConfigType.SECURITY.value, {})
        return SecurityConfig(**config_dict)
        
    def get_monitoring_config(self) -> MonitoringConfig:
        """获取监控配置"""
        config_dict = self._config_cache.get(ConfigType.MONITORING.value, {})
        return MonitoringConfig(**config_dict)
        
    def update_system_config(self, **kwargs):
        """更新系统配置"""
        config = self.get_system_config()
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
                
        self._config_cache[ConfigType.SYSTEM.value] = asdict(config)
        self._save_config(self.system_config_path, asdict(config))
        self._notify_watchers(ConfigType.SYSTEM, config)
        
    def update_role_config(self, role_id: str, **kwargs):
        """更新角色配置"""
        config = self.get_role_config(role_id)
        if not config:
            return False
            
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
                
        roles_config = self._config_cache[ConfigType.ROLE.value]
        roles_config[role_id] = asdict(config)
        
        self._save_config(self.roles_config_path, roles_config)
        self._notify_watchers(ConfigType.ROLE, {role_id: config})
        return True
        
    def get_config_value(self, config_type: ConfigType, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config_dict = self._config_cache.get(config_type.value, {})
        return config_dict.get(key, default)
        
    def set_config_value(self, config_type: ConfigType, key: str, value: Any):
        """设置配置值"""
        if config_type.value not in self._config_cache:
            self._config_cache[config_type.value] = {}
            
        self._config_cache[config_type.value][key] = value
        
        # 保存到文件
        file_path_map = {
            ConfigType.SYSTEM: self.system_config_path,
            ConfigType.ROLE: self.roles_config_path,
            ConfigType.COMMUNICATION: self.communication_config_path,
            ConfigType.STORAGE: self.storage_config_path,
            ConfigType.SECURITY: self.security_config_path,
            ConfigType.MONITORING: self.monitoring_config_path
        }
        
        file_path = file_path_map.get(config_type)
        if file_path:
            self._save_config(file_path, self._config_cache[config_type.value])
            self._notify_watchers(config_type, {key: value})
            
    def reload_configs(self):
        """重新加载所有配置"""
        self._load_all_configs()
        self.logger.info("配置已重新加载")
        
    def validate_configs(self) -> Dict[str, List[str]]:
        """验证配置有效性"""
        errors = {
            'system': [],
            'roles': [],
            'communication': [],
            'storage': [],
            'security': [],
            'monitoring': []
        }
        
        try:
            # 验证系统配置
            system_config = self.get_system_config()
            if system_config.max_concurrent_tasks <= 0:
                errors['system'].append("max_concurrent_tasks 必须大于0")
                
            if system_config.session_timeout <= 0:
                errors['system'].append("session_timeout 必须大于0")
                
            # 验证角色配置
            role_configs = self.get_all_role_configs()
            for role_id, config in role_configs.items():
                if config.max_concurrent_tasks <= 0:
                    errors['roles'].append(f"{role_id}: max_concurrent_tasks 必须大于0")
                    
                if config.timeout_seconds <= 0:
                    errors['roles'].append(f"{role_id}: timeout_seconds 必须大于0")
                    
            # 验证通信配置
            comm_config = self.get_communication_config()
            if comm_config.message_queue_size <= 0:
                errors['communication'].append("message_queue_size 必须大于0")
                
            if comm_config.num_workers <= 0:
                errors['communication'].append("num_workers 必须大于0")
                
            # 验证存储配置
            storage_config = self.get_storage_config()
            if storage_config.backup_interval <= 0:
                errors['storage'].append("backup_interval 必须大于0")
                
            # 验证安全配置
            security_config = self.get_security_config()
            if security_config.max_login_attempts <= 0:
                errors['security'].append("max_login_attempts 必须大于0")
                
            # 验证监控配置
            monitoring_config = self.get_monitoring_config()
            if monitoring_config.health_check_interval <= 0:
                errors['monitoring'].append("health_check_interval 必须大于0")
                
        except Exception as e:
            errors['system'].append(f"配置验证时发生错误: {e}")
            
        return errors
        
    def add_config_watcher(self, callback: callable):
        """添加配置变更监听器"""
        self._watchers.append(callback)
        
    def remove_config_watcher(self, callback: callable):
        """移除配置变更监听器"""
        if callback in self._watchers:
            self._watchers.remove(callback)
            
    def _notify_watchers(self, config_type: ConfigType, updated_config: Any):
        """通知配置变更监听器"""
        for watcher in self._watchers:
            try:
                watcher(config_type, updated_config)
            except Exception as e:
                self.logger.error(f"通知配置监听器失败: {e}")
                
    def export_configs(self, export_path: str):
        """导出所有配置"""
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # 导出所有配置文件
            import shutil
            
            config_files = [
                self.system_config_path,
                self.roles_config_path,
                self.communication_config_path,
                self.storage_config_path,
                self.security_config_path,
                self.monitoring_config_path
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    shutil.copy2(config_file, export_dir / config_file.name)
                    
            self.logger.info(f"配置已导出到: {export_path}")
            
        except Exception as e:
            self.logger.error(f"导出配置失败: {e}")
            raise
            
    def import_configs(self, import_path: str):
        """导入配置"""
        try:
            import_dir = Path(import_path)
            if not import_dir.exists():
                raise FileNotFoundError(f"导入路径不存在: {import_path}")
                
            # 导入所有配置文件
            import shutil
            
            config_files = [
                ("system_config.json", self.system_config_path),
                ("roles_config.json", self.roles_config_path),
                ("communication_config.json", self.communication_config_path),
                ("storage_config.json", self.storage_config_path),
                ("security_config.json", self.security_config_path),
                ("monitoring_config.json", self.monitoring_config_path)
            ]
            
            for filename, target_path in config_files:
                source_path = import_dir / filename
                if source_path.exists():
                    shutil.copy2(source_path, target_path)
                    
            # 重新加载配置
            self.reload_configs()
            
            self.logger.info(f"配置已从 {import_path} 导入")
            
        except Exception as e:
            self.logger.error(f"导入配置失败: {e}")
            raise
            
    def get_environment_variables(self) -> Dict[str, str]:
        """获取环境变量配置"""
        env_vars = {}
        
        # 系统环境变量
        system_config = self.get_system_config()
        env_vars.update({
            'AI_DEV_SYSTEM_NAME': system_config.name,
            'AI_DEV_SYSTEM_VERSION': system_config.version,
            'AI_DEV_ENVIRONMENT': system_config.environment,
            'AI_DEV_LOG_LEVEL': system_config.log_level,
            'AI_DEV_DEBUG_MODE': str(system_config.debug_mode).lower()
        })
        
        # 存储环境变量
        storage_config = self.get_storage_config()
        env_vars.update({
            'AI_DEV_DATA_PATH': storage_config.data_path,
            'AI_DEV_BACKUP_PATH': storage_config.backup_path
        })
        
        return env_vars
        
    def apply_environment_variables(self):
        """应用环境变量到系统"""
        env_vars = self.get_environment_variables()
        
        for key, value in env_vars.items():
            os.environ[key] = value
            
        self.logger.info(f"应用了 {len(env_vars)} 个环境变量")


# 单例模式的全局配置管理器
_config_manager_instance: Optional[ConfigManager] = None


def get_config_manager(config_dir: str = "config") -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager_instance
    
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager(config_dir)
        
    return _config_manager_instance


# 便捷函数
def get_system_config() -> SystemConfig:
    """获取系统配置"""
    return get_config_manager().get_system_config()


def get_role_config(role_id: str) -> Optional[RoleConfig]:
    """获取角色配置"""
    return get_config_manager().get_role_config(role_id)


def get_communication_config() -> CommunicationConfig:
    """获取通信配置"""
    return get_config_manager().get_communication_config()


# 使用示例
if __name__ == "__main__":
    # 创建配置管理器
    config_manager = ConfigManager()
    
    # 获取系统配置
    sys_config = config_manager.get_system_config()
    print(f"系统名称: {sys_config.name}")
    print(f"版本: {sys_config.version}")
    
    # 获取角色配置
    master_config = config_manager.get_role_config("master_controller")
    if master_config:
        print(f"主控制器最大并发任务数: {master_config.max_concurrent_tasks}")
        
    # 验证配置
    validation_errors = config_manager.validate_configs()
    for category, errors in validation_errors.items():
        if errors:
            print(f"{category} 配置错误: {errors}")
            
    # 应用环境变量
    config_manager.apply_environment_variables()
    print(f"AI系统环境: {os.environ.get('AI_DEV_ENVIRONMENT', 'unknown')}")