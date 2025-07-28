#!/usr/bin/env python3
"""
AI开发系统 - 项目管理器
提供完整的项目生命周期管理功能
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加系统路径
sys.path.append(str(Path(__file__).parent.parent))

from project_isolation import ProjectIsolationManager, ProjectConfig, ProjectStatus, ProjectType
from system_memory import SystemMemoryManager, MemoryType, LearningCategory

class ProjectManager:
    """项目管理器 - 统一管理所有AI开发项目"""
    
    def __init__(self, system_root: str = None):
        self.system_root = Path(system_root) if system_root else Path.cwd()
        
        # 初始化组件
        self.isolation_manager = ProjectIsolationManager(str(self.system_root))
        self.memory_manager = SystemMemoryManager(str(self.system_root / "system-memory"))
        
        # 设置日志
        self._setup_logging()
        
        # 项目活动历史
        self.activity_log: List[Dict[str, Any]] = []
        
    def _setup_logging(self):
        """设置日志系统"""
        log_dir = self.system_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'project_manager.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ProjectManager')
        
    def create_project(self, 
                      project_name: str,
                      project_type: str,
                      description: str = "",
                      owner: str = "system",
                      tech_stack: List[str] = None,
                      template: str = None) -> Dict[str, Any]:
        """创建新项目"""
        try:
            self.logger.info(f"开始创建项目: {project_name}")
            
            # 验证项目类型
            try:
                proj_type = ProjectType(project_type)
            except ValueError:
                raise ValueError(f"不支持的项目类型: {project_type}")
                
            # 创建项目
            project_id = self.isolation_manager.create_project(
                project_name=project_name,
                project_type=proj_type,
                description=description,
                owner=owner,
                tech_stack=tech_stack,
                template=template
            )
            
            # 记录创建活动
            self._log_activity("project_created", {
                'project_id': project_id,
                'project_name': project_name,
                'project_type': project_type,
                'owner': owner
            })
            
            # 添加到系统记忆
            self.memory_manager.add_memory(
                memory_type=MemoryType.PROJECT,
                category=LearningCategory.BEST_PRACTICE,
                title=f"项目创建: {project_name}",
                description=f"成功创建{project_type}类型的项目",
                context={
                    'project_id': project_id,
                    'project_type': project_type,
                    'tech_stack': tech_stack or [],
                    'template': template
                },
                outcome="项目创建成功",
                tags=[project_type, "project_creation", "success"]
            )
            
            return {
                'success': True,
                'project_id': project_id,
                'message': f'项目 "{project_name}" 创建成功',
                'project_path': str(self.system_root / "projects" / project_id)
            }
            
        except Exception as e:
            self.logger.error(f"项目创建失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'项目 "{project_name}" 创建失败'
            }
            
    def list_projects(self, status_filter: str = None) -> List[Dict[str, Any]]:
        """列出所有项目"""
        try:
            projects = self.isolation_manager.list_projects()
            
            # 状态过滤
            if status_filter:
                projects = [p for p in projects if p['status'] == status_filter]
                
            # 添加额外信息
            for project in projects:
                project_id = project['project_id']
                
                # 获取项目隔离信息
                isolation_info = self.isolation_manager.get_project_isolation_info(project_id)
                if 'resource_usage' in isolation_info:
                    project['size_mb'] = isolation_info['resource_usage']['total_size_mb']
                    project['file_count'] = isolation_info['resource_usage']['file_count']
                    
                # 获取最近活动
                recent_activities = [
                    activity for activity in self.activity_log 
                    if activity.get('context', {}).get('project_id') == project_id
                ]
                project['recent_activity_count'] = len(recent_activities[-10:])  # 最近10个活动
                
            self._log_activity("projects_listed", {'count': len(projects), 'filter': status_filter})
            
            return projects
            
        except Exception as e:
            self.logger.error(f"列出项目失败: {e}")
            return []
            
    def switch_project(self, project_id: str) -> Dict[str, Any]:
        """切换到指定项目"""
        try:
            success = self.isolation_manager.switch_project(project_id)
            
            if success:
                # 获取项目配置
                config = self.isolation_manager.get_project_config(project_id)
                
                # 记录切换活动
                self._log_activity("project_switched", {
                    'project_id': project_id,
                    'project_name': config.project_name if config else 'Unknown'
                })
                
                return {
                    'success': True,
                    'project_id': project_id,
                    'message': f'已切换到项目: {project_id}',
                    'project_config': config.__dict__ if config else None
                }
            else:
                return {
                    'success': False,
                    'error': 'Project not found or invalid',
                    'message': f'无法切换到项目: {project_id}'
                }
                
        except Exception as e:
            self.logger.error(f"项目切换失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'项目切换失败: {project_id}'
            }
            
    def get_project_status(self, project_id: str = None) -> Dict[str, Any]:
        """获取项目状态详情"""
        try:
            if project_id is None:
                project_id = self.isolation_manager.current_project
                
            if not project_id:
                return {'error': '没有指定项目或当前项目'}
                
            # 获取项目配置
            config = self.isolation_manager.get_project_config(project_id)
            if not config:
                return {'error': f'项目不存在: {project_id}'}
                
            # 获取隔离信息
            isolation_info = self.isolation_manager.get_project_isolation_info(project_id)
            
            # 验证隔离状态
            validation_result = self.isolation_manager.validate_isolation(project_id)
            
            # 获取项目活动历史
            project_activities = [
                activity for activity in self.activity_log
                if activity.get('context', {}).get('project_id') == project_id
            ]
            
            # 获取相关记忆
            project_memories = self.memory_manager.query_memory(
                tags=[project_id],
                limit=5
            )
            
            return {
                'project_id': project_id,
                'config': config.__dict__,
                'isolation_info': isolation_info,
                'validation': validation_result,
                'recent_activities': project_activities[-10:],
                'memory_count': len(project_memories),
                'is_current': project_id == self.isolation_manager.current_project
            }
            
        except Exception as e:
            self.logger.error(f"获取项目状态失败: {e}")
            return {'error': str(e)}
            
    def update_project_status(self, project_id: str, new_status: str) -> Dict[str, Any]:
        """更新项目状态"""
        try:
            # 验证状态
            try:
                status = ProjectStatus(new_status)
            except ValueError:
                return {
                    'success': False,
                    'error': f'无效的项目状态: {new_status}'
                }
                
            # 更新状态
            success = self.isolation_manager.update_project_status(project_id, status)
            
            if success:
                # 记录状态变更
                self._log_activity("project_status_updated", {
                    'project_id': project_id,
                    'new_status': new_status
                })
                
                # 添加到记忆
                self.memory_manager.add_memory(
                    memory_type=MemoryType.PROJECT,
                    category=LearningCategory.BEST_PRACTICE,
                    title=f"项目状态更新: {project_id}",
                    description=f"项目状态更新为: {new_status}",
                    context={
                        'project_id': project_id,
                        'status': new_status,
                        'timestamp': datetime.now().isoformat()
                    },
                    outcome="状态更新成功",
                    tags=[project_id, "status_update", new_status]
                )
                
                return {
                    'success': True,
                    'message': f'项目状态已更新为: {new_status}'
                }
            else:
                return {
                    'success': False,
                    'error': '状态更新失败'
                }
                
        except Exception as e:
            self.logger.error(f"更新项目状态失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def archive_project(self, project_id: str) -> Dict[str, Any]:
        """归档项目"""
        try:
            success = self.isolation_manager.archive_project(project_id)
            
            if success:
                # 记录归档活动
                self._log_activity("project_archived", {
                    'project_id': project_id
                })
                
                # 添加到记忆
                self.memory_manager.add_memory(
                    memory_type=MemoryType.PROJECT,
                    category=LearningCategory.BEST_PRACTICE,
                    title=f"项目归档: {project_id}",
                    description=f"项目 {project_id} 已成功归档",
                    context={
                        'project_id': project_id,
                        'archived_at': datetime.now().isoformat()
                    },
                    outcome="项目归档成功",
                    tags=[project_id, "archived", "completed"]
                )
                
                return {
                    'success': True,
                    'message': f'项目 {project_id} 已归档'
                }
            else:
                return {
                    'success': False,
                    'error': '项目归档失败'
                }
                
        except Exception as e:
            self.logger.error(f"项目归档失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def get_system_overview(self) -> Dict[str, Any]:
        """获取系统总览"""
        try:
            projects = self.list_projects()
            
            # 统计信息
            stats = {
                'total_projects': len(projects),
                'by_status': {},
                'by_type': {},
                'total_size_mb': 0,
                'total_files': 0
            }
            
            for project in projects:
                # 按状态统计
                status = project['status']
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # 按类型统计
                proj_type = project['project_type']
                stats['by_type'][proj_type] = stats['by_type'].get(proj_type, 0) + 1
                
                # 资源统计
                stats['total_size_mb'] += project.get('size_mb', 0)
                stats['total_files'] += project.get('file_count', 0)
                
            # 系统记忆统计
            memory_stats = self.memory_manager.get_memory_statistics()
            
            # 最近活动
            recent_activities = self.activity_log[-20:]  # 最近20个活动
            
            return {
                'system_root': str(self.system_root),
                'current_project': self.isolation_manager.current_project,
                'project_statistics': stats,
                'memory_statistics': memory_stats,
                'recent_activities': recent_activities,
                'system_health': self._check_system_health()
            }
            
        except Exception as e:
            self.logger.error(f"获取系统总览失败: {e}")
            return {'error': str(e)}
            
    def _check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        health_status = {
            'overall': 'healthy',
            'issues': [],
            'warnings': []
        }
        
        try:
            # 检查关键目录
            required_dirs = ['system-core', 'system-config', 'system-memory', 'projects']
            for dir_name in required_dirs:
                dir_path = self.system_root / dir_name
                if not dir_path.exists():
                    health_status['issues'].append(f'缺少关键目录: {dir_name}')
                    
            # 检查项目隔离状态
            projects = self.isolation_manager.list_projects()
            for project in projects:
                project_id = project['project_id']
                validation = self.isolation_manager.validate_isolation(project_id)
                if not validation['valid']:
                    health_status['warnings'].append(f'项目隔离问题: {project_id}')
                    
            # 检查系统记忆
            memory_stats = self.memory_manager.get_memory_statistics()
            if memory_stats['total_memories'] == 0:
                health_status['warnings'].append('系统记忆为空，建议初始化基础知识')
                
            # 确定总体健康状态
            if health_status['issues']:
                health_status['overall'] = 'unhealthy'
            elif health_status['warnings']:
                health_status['overall'] = 'warning'
                
        except Exception as e:
            health_status['overall'] = 'error'
            health_status['issues'].append(f'健康检查失败: {e}')
            
        return health_status
        
    def _log_activity(self, activity_type: str, context: Dict[str, Any]):
        """记录活动日志"""
        activity = {
            'activity_id': len(self.activity_log) + 1,
            'activity_type': activity_type,
            'timestamp': datetime.now().isoformat(),
            'context': context
        }
        
        self.activity_log.append(activity)
        
        # 保持最近1000个活动
        if len(self.activity_log) > 1000:
            self.activity_log = self.activity_log[-1000:]
            
    def learn_from_project_experience(self, 
                                    project_id: str,
                                    experience_type: str,
                                    description: str,
                                    success: bool,
                                    context: Dict[str, Any] = None) -> str:
        """从项目经验中学习"""
        try:
            context = context or {}
            context['project_id'] = project_id
            
            outcome = description + (" - 成功" if success else " - 失败")
            
            memory_id = self.memory_manager.learn_from_experience(
                project_id=project_id,
                experience_type=experience_type,
                context=context,
                outcome=outcome,
                success=success
            )
            
            self._log_activity("learning_recorded", {
                'project_id': project_id,
                'experience_type': experience_type,
                'success': success,
                'memory_id': memory_id
            })
            
            return memory_id
            
        except Exception as e:
            self.logger.error(f"记录学习经验失败: {e}")
            raise

def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description='AI开发系统项目管理器')
    parser.add_argument('--system-root', default='.', help='系统根目录')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 创建项目命令
    create_parser = subparsers.add_parser('create', help='创建新项目')
    create_parser.add_argument('name', help='项目名称')
    create_parser.add_argument('type', help='项目类型')
    create_parser.add_argument('--description', default='', help='项目描述')
    create_parser.add_argument('--owner', default='system', help='项目负责人')
    create_parser.add_argument('--tech-stack', nargs='+', help='技术栈')
    create_parser.add_argument('--template', help='项目模板')
    
    # 列出项目命令
    list_parser = subparsers.add_parser('list', help='列出所有项目')
    list_parser.add_argument('--status', help='按状态过滤')
    
    # 切换项目命令
    switch_parser = subparsers.add_parser('switch', help='切换项目')
    switch_parser.add_argument('project_id', help='项目ID')
    
    # 项目状态命令
    status_parser = subparsers.add_parser('status', help='查看项目状态')
    status_parser.add_argument('project_id', nargs='?', help='项目ID（可选）')
    
    # 更新状态命令
    update_parser = subparsers.add_parser('update-status', help='更新项目状态')
    update_parser.add_argument('project_id', help='项目ID')
    update_parser.add_argument('status', help='新状态')
    
    # 归档项目命令
    archive_parser = subparsers.add_parser('archive', help='归档项目')
    archive_parser.add_argument('project_id', help='项目ID')
    
    # 系统总览命令
    overview_parser = subparsers.add_parser('overview', help='系统总览')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    # 创建项目管理器
    pm = ProjectManager(args.system_root)
    
    # 执行命令
    if args.command == 'create':
        result = pm.create_project(
            project_name=args.name,
            project_type=args.type,
            description=args.description,
            owner=args.owner,
            tech_stack=args.tech_stack,
            template=args.template
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.command == 'list':
        projects = pm.list_projects(args.status)
        print(json.dumps(projects, indent=2, ensure_ascii=False))
        
    elif args.command == 'switch':
        result = pm.switch_project(args.project_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.command == 'status':
        result = pm.get_project_status(args.project_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.command == 'update-status':
        result = pm.update_project_status(args.project_id, args.status)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.command == 'archive':
        result = pm.archive_project(args.project_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif args.command == 'overview':
        result = pm.get_system_overview()
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()