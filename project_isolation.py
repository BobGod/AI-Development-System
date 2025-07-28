#!/usr/bin/env python3
"""
AI开发系统 - 项目隔离机制
确保不同项目之间完全隔离，防止相互影响
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

class ProjectStatus(Enum):
    """项目状态枚举"""
    CREATED = "created"
    ANALYZING = "analyzing"
    DESIGNING = "designing"
    DEVELOPING = "developing"
    TESTING = "testing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"

class ProjectType(Enum):
    """项目类型枚举"""
    WEB_APP = "web_app"
    API_SERVICE = "api_service"
    MOBILE_APP = "mobile_app"
    DATA_PLATFORM = "data_platform"
    DESKTOP_APP = "desktop_app"
    MICROSERVICE = "microservice"
    CUSTOM = "custom"

@dataclass
class ProjectConfig:
    """项目配置数据类"""
    project_id: str
    project_name: str
    project_type: ProjectType
    description: str
    owner: str
    created_at: str
    status: ProjectStatus
    version: str = "1.0.0"
    tech_stack: List[str] = None
    requirements: Dict[str, Any] = None
    constraints: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tech_stack is None:
            self.tech_stack = []
        if self.requirements is None:
            self.requirements = {}
        if self.constraints is None:
            self.constraints = {}

class ProjectIsolationManager:
    """项目隔离管理器"""
    
    def __init__(self, system_root: str = None):
        self.system_root = Path(system_root) if system_root else Path.cwd()
        self.projects_root = self.system_root / "projects"
        self.system_core_root = self.system_root / "system-core"
        self.system_config_root = self.system_root / "system-config"
        self.system_memory_root = self.system_root / "system-memory"
        
        # 设置日志
        self.logger = logging.getLogger('ProjectIsolationManager')
        
        # 确保目录结构存在
        self._ensure_directory_structure()
        
        # 当前活跃项目
        self.current_project: Optional[str] = None
        
    def _ensure_directory_structure(self):
        """确保目录结构存在"""
        directories = [
            self.projects_root,
            self.system_core_root,
            self.system_config_root,
            self.system_memory_root,
            self.system_root / "version-control",
            self.system_root / "tools",
            self.system_root / "scripts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        # 创建系统记忆子目录
        memory_subdirs = ["learning", "knowledge", "evolution"]
        for subdir in memory_subdirs:
            (self.system_memory_root / subdir).mkdir(exist_ok=True)
            
    def create_project(self, 
                      project_name: str,
                      project_type: ProjectType,
                      description: str = "",
                      owner: str = "system",
                      tech_stack: List[str] = None,
                      template: str = None) -> str:
        """创建新项目"""
        try:
            # 生成项目ID
            project_id = f"project-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
            
            # 创建项目配置
            project_config = ProjectConfig(
                project_id=project_id,
                project_name=project_name,
                project_type=project_type,
                description=description,
                owner=owner,
                created_at=datetime.now().isoformat(),
                status=ProjectStatus.CREATED,
                tech_stack=tech_stack or []
            )
            
            # 创建项目目录
            project_dir = self.projects_root / project_id
            self._create_project_structure(project_dir, project_config, template)
            
            # 保存项目配置
            self._save_project_config(project_dir, project_config)
            
            # 初始化项目记忆
            self._initialize_project_memory(project_dir)
            
            self.logger.info(f"项目创建成功: {project_name} ({project_id})")
            return project_id
            
        except Exception as e:
            self.logger.error(f"项目创建失败: {e}")
            raise
            
    def _create_project_structure(self, project_dir: Path, config: ProjectConfig, template: str = None):
        """创建项目目录结构"""
        # 基础目录结构
        subdirs = [
            "requirements",      # 需求文档
            "design",           # 设计文件
            "architecture",     # 架构设计
            "code",            # 生成的代码
            "tests",           # 测试文件
            "docs",            # 项目文档
            "deployment",      # 部署配置
            "memory",          # 项目记忆
            "logs",            # 项目日志
            "assets",          # 项目资产
            "config"           # 项目配置
        ]
        
        for subdir in subdirs:
            (project_dir / subdir).mkdir(parents=True, exist_ok=True)
            
        # 如果指定了模板，复制模板文件
        if template:
            self._apply_project_template(project_dir, template, config)
            
        # 创建README文件
        readme_content = f"""# {config.project_name}

**项目ID**: {config.project_id}
**项目类型**: {config.project_type.value}
**创建时间**: {config.created_at}
**负责人**: {config.owner}

## 项目描述
{config.description}

## 技术栈
{', '.join(config.tech_stack) if config.tech_stack else '待定'}

## 项目状态
{config.status.value}

## 目录结构
- `requirements/` - 需求文档和分析
- `design/` - 设计文件和原型
- `architecture/` - 系统架构设计
- `code/` - 生成的源代码
- `tests/` - 测试代码和测试计划
- `docs/` - 项目文档
- `deployment/` - 部署脚本和配置
- `memory/` - 项目记忆和学习记录
- `logs/` - 开发过程日志
- `assets/` - 项目资产文件
- `config/` - 项目特定配置
"""
        
        (project_dir / "README.md").write_text(readme_content, encoding='utf-8')
        
    def _apply_project_template(self, project_dir: Path, template: str, config: ProjectConfig):
        """应用项目模板"""
        template_dir = self.system_config_root / "templates" / template
        
        if template_dir.exists():
            # 复制模板文件
            for item in template_dir.rglob("*"):
                if item.is_file():
                    relative_path = item.relative_to(template_dir)
                    target_path = project_dir / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 处理模板变量替换
                    if item.suffix in ['.json', '.md', '.txt', '.py', '.js', '.html']:
                        content = item.read_text(encoding='utf-8')
                        content = self._replace_template_variables(content, config)
                        target_path.write_text(content, encoding='utf-8')
                    else:
                        shutil.copy2(item, target_path)
                        
        else:
            self.logger.warning(f"模板不存在: {template}")
            
    def _replace_template_variables(self, content: str, config: ProjectConfig) -> str:
        """替换模板变量"""
        replacements = {
            '{{PROJECT_ID}}': config.project_id,
            '{{PROJECT_NAME}}': config.project_name,
            '{{PROJECT_TYPE}}': config.project_type.value,
            '{{DESCRIPTION}}': config.description,
            '{{OWNER}}': config.owner,
            '{{CREATED_AT}}': config.created_at,
            '{{TECH_STACK}}': ', '.join(config.tech_stack),
            '{{VERSION}}': config.version
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
            
        return content
        
    def _save_project_config(self, project_dir: Path, config: ProjectConfig):
        """保存项目配置"""
        config_file = project_dir / "project.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(config), f, ensure_ascii=False, indent=2, default=str)
            
    def _initialize_project_memory(self, project_dir: Path):
        """初始化项目记忆"""
        memory_dir = project_dir / "memory"
        
        # 创建记忆文件
        memory_files = {
            "development_log.json": [],
            "decision_records.json": [],
            "lessons_learned.json": [],
            "performance_metrics.json": [],
            "user_feedback.json": [],
            "optimization_history.json": []
        }
        
        for filename, initial_data in memory_files.items():
            memory_file = memory_dir / filename
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
                
    def switch_project(self, project_id: str) -> bool:
        """切换到指定项目"""
        try:
            project_dir = self.projects_root / project_id
            
            if not project_dir.exists():
                self.logger.error(f"项目不存在: {project_id}")
                return False
                
            # 验证项目配置
            config_file = project_dir / "project.json"
            if not config_file.exists():
                self.logger.error(f"项目配置文件不存在: {project_id}")
                return False
                
            # 设置当前项目
            self.current_project = project_id
            
            # 设置环境变量
            os.environ['CURRENT_PROJECT_ID'] = project_id
            os.environ['CURRENT_PROJECT_PATH'] = str(project_dir)
            
            self.logger.info(f"已切换到项目: {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"项目切换失败: {e}")
            return False
            
    def get_project_config(self, project_id: str = None) -> Optional[ProjectConfig]:
        """获取项目配置"""
        if project_id is None:
            project_id = self.current_project
            
        if project_id is None:
            return None
            
        try:
            config_file = self.projects_root / project_id / "project.json"
            
            if not config_file.exists():
                return None
                
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            # 转换枚举类型
            config_data['project_type'] = ProjectType(config_data['project_type'])
            config_data['status'] = ProjectStatus(config_data['status'])
            
            return ProjectConfig(**config_data)
            
        except Exception as e:
            self.logger.error(f"获取项目配置失败: {e}")
            return None
            
    def update_project_status(self, project_id: str, status: ProjectStatus) -> bool:
        """更新项目状态"""
        try:
            config = self.get_project_config(project_id)
            if config is None:
                return False
                
            config.status = status
            
            config_file = self.projects_root / project_id / "project.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, ensure_ascii=False, indent=2, default=str)
                
            self.logger.info(f"项目状态已更新: {project_id} -> {status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新项目状态失败: {e}")
            return False
            
    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目"""
        projects = []
        
        for project_dir in self.projects_root.iterdir():
            if project_dir.is_dir():
                config = self.get_project_config(project_dir.name)
                if config:
                    projects.append({
                        'project_id': config.project_id,
                        'project_name': config.project_name,
                        'project_type': config.project_type.value,
                        'status': config.status.value,
                        'created_at': config.created_at,
                        'owner': config.owner
                    })
                    
        return sorted(projects, key=lambda x: x['created_at'], reverse=True)
        
    def archive_project(self, project_id: str) -> bool:
        """归档项目"""
        try:
            # 更新项目状态
            if not self.update_project_status(project_id, ProjectStatus.ARCHIVED):
                return False
                
            # 创建归档目录
            archive_dir = self.system_root / "version-control" / "archived-projects"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # 移动项目到归档目录
            project_dir = self.projects_root / project_id
            archive_path = archive_dir / f"{project_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            shutil.move(str(project_dir), str(archive_path))
            
            self.logger.info(f"项目已归档: {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"项目归档失败: {e}")
            return False
            
    def get_project_isolation_info(self, project_id: str = None) -> Dict[str, Any]:
        """获取项目隔离信息"""
        if project_id is None:
            project_id = self.current_project
            
        if project_id is None:
            return {"error": "没有当前项目"}
            
        project_dir = self.projects_root / project_id
        
        if not project_dir.exists():
            return {"error": f"项目不存在: {project_id}"}
            
        # 统计项目资源使用情况
        total_size = sum(f.stat().st_size for f in project_dir.rglob('*') if f.is_file())
        file_count = len([f for f in project_dir.rglob('*') if f.is_file()])
        dir_count = len([d for d in project_dir.rglob('*') if d.is_dir()])
        
        return {
            'project_id': project_id,
            'project_path': str(project_dir),
            'isolated_directories': {
                'requirements': str(project_dir / "requirements"),
                'design': str(project_dir / "design"),
                'code': str(project_dir / "code"),
                'tests': str(project_dir / "tests"),
                'docs': str(project_dir / "docs"),
                'memory': str(project_dir / "memory"),
                'logs': str(project_dir / "logs")
            },
            'resource_usage': {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'directory_count': dir_count
            },
            'isolation_status': {
                'config_isolated': (project_dir / "config").exists(),
                'memory_isolated': (project_dir / "memory").exists(),
                'logs_isolated': (project_dir / "logs").exists(),
                'code_isolated': (project_dir / "code").exists()
            }
        }
        
    def validate_isolation(self, project_id: str = None) -> Dict[str, Any]:
        """验证项目隔离状态"""
        if project_id is None:
            project_id = self.current_project
            
        if project_id is None:
            return {"valid": False, "error": "没有当前项目"}
            
        validation_results = {
            "project_id": project_id,
            "valid": True,
            "issues": []
        }
        
        project_dir = self.projects_root / project_id
        
        # 检查项目目录存在
        if not project_dir.exists():
            validation_results["valid"] = False
            validation_results["issues"].append("项目目录不存在")
            return validation_results
            
        # 检查必需的子目录
        required_dirs = ["requirements", "design", "code", "tests", "docs", "memory", "logs", "config"]
        for req_dir in required_dirs:
            if not (project_dir / req_dir).exists():
                validation_results["issues"].append(f"缺少必需目录: {req_dir}")
                
        # 检查项目配置文件
        if not (project_dir / "project.json").exists():
            validation_results["issues"].append("缺少项目配置文件")
            
        # 检查是否有跨项目引用
        try:
            for code_file in (project_dir / "code").rglob("*.py"):
                content = code_file.read_text(encoding='utf-8')
                # 简单检查是否有其他项目的路径引用
                if "projects/" in content and project_id not in content:
                    validation_results["issues"].append(f"发现跨项目引用: {code_file}")
        except Exception:
            pass  # 忽略读取错误
            
        if validation_results["issues"]:
            validation_results["valid"] = False
            
        return validation_results