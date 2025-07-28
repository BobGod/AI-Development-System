#!/usr/bin/env python3
"""
AI自主开发系统 - 示例项目
验证整个系统的协作能力
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from system_orchestrator import SystemOrchestrator, ProjectConfig
from config_manager import get_config_manager
from communication import MessageBus
from roles.master_controller import MasterController
from roles.memory_manager_simple import MemoryManager


async def run_example_project():
    """运行示例项目"""
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('ExampleProject')
    
    try:
        logger.info("=== 开始AI自主开发系统示例项目 ===")
        
        # 1. 初始化配置管理器
        logger.info("1. 初始化配置管理器...")
        config_manager = get_config_manager()
        system_config = config_manager.get_system_config()
        comm_config = config_manager.get_communication_config()
        
        logger.info(f"系统配置: {system_config.name} v{system_config.version}")
        
        # 2. 创建项目配置
        logger.info("2. 创建项目配置...")
        project_config = ProjectConfig(
            name="用户管理系统",
            description="一个简单的Web用户管理系统，包含用户注册、登录、个人资料管理等功能",
            requirements="""
            功能需求:
            1. 用户注册 - 用户可以使用邮箱和密码注册账户
            2. 用户登录 - 用户可以使用邮箱和密码登录
            3. 个人资料 - 用户可以查看和编辑个人资料
            4. 密码管理 - 用户可以修改密码
            5. 用户列表 - 管理员可以查看所有用户列表
            
            技术需求:
            - 前端: React + TypeScript
            - 后端: Node.js + Express
            - 数据库: PostgreSQL
            - 认证: JWT
            - 部署: Docker
            """,
            constraints=[
                "开发时间: 7天",
                "团队规模: AI开发系统",
                "预算: 无限制",
                "技术栈: Web技术栈"
            ],
            timeline="2024-01-01 到 2024-01-07",
            priority="high"
        )
        
        logger.info(f"项目: {project_config.name}")
        logger.info(f"描述: {project_config.description}")
        
        # 3. 创建消息总线
        logger.info("3. 初始化消息总线...")
        message_bus = MessageBus({
            'queue_size': comm_config.message_queue_size,
            'num_workers': comm_config.num_workers,
            'retention_hours': 12
        })
        
        await message_bus.start()
        logger.info("消息总线启动完成")
        
        # 4. 创建核心角色
        logger.info("4. 创建和初始化核心AI角色...")
        
        # 创建主控制器
        master_controller = MasterController(
            config=config_manager.get_role_config("master_controller").__dict__
        )
        
        # 创建记忆管理器
        memory_manager = MemoryManager(
            config=config_manager.get_role_config("memory_manager").__dict__
        )
        
        # 初始化角色
        await master_controller.initialize(message_bus)
        await memory_manager.initialize(message_bus)
        
        logger.info("核心角色初始化完成")
        
        # 5. 模拟项目初始化流程
        logger.info("5. 开始项目初始化流程...")
        
        # 向主控制器发送项目初始化请求
        init_message = await master_controller.send_message(
            to_role="master_controller",
            action="initialize_project",
            data={'project_config': project_config.__dict__}
        )
        
        logger.info(f"项目初始化请求已发送: {init_message}")
        
        # 等待初始化完成
        await asyncio.sleep(2)
        
        # 6. 模拟用户请求处理
        logger.info("6. 模拟用户请求处理...")
        
        user_requests = [
            "请开始分析项目需求",
            "设计系统架构",
            "开始前端开发",
            "实现用户注册功能",
            "创建数据库设计"
        ]
        
        for i, request in enumerate(user_requests, 1):
            logger.info(f"处理用户请求 {i}: {request}")
            
            response_id = await master_controller.send_message(
                to_role="master_controller",
                action="process_user_request",
                data={'request': request}
            )
            
            logger.info(f"请求已发送，ID: {response_id}")
            
            # 等待处理
            await asyncio.sleep(1)
            
        # 7. 检查系统状态
        logger.info("7. 检查系统状态...")
        
        # 获取主控制器状态
        master_status = master_controller.get_status()
        logger.info(f"主控制器状态: {master_status['state']}")
        logger.info(f"当前任务数: {master_status['current_tasks_count']}")
        logger.info(f"完成任务数: {master_status['stats']['tasks_completed']}")
        
        # 获取记忆管理器状态
        memory_status = memory_manager.get_status()
        logger.info(f"记忆管理器状态: {memory_status['state']}")
        logger.info(f"发送消息数: {memory_status['stats']['messages_sent']}")
        
        # 8. 获取消息总线统计
        logger.info("8. 消息总线统计...")
        bus_stats = message_bus.get_stats()
        logger.info(f"已发送消息: {bus_stats['messages_sent']}")
        logger.info(f"已投递消息: {bus_stats['messages_delivered']}")
        logger.info(f"失败消息: {bus_stats['messages_failed']}")
        logger.info(f"平均投递时间: {bus_stats['average_delivery_time']:.3f}s")
        
        # 9. 模拟系统运行一段时间
        logger.info("9. 系统运行中...")
        await asyncio.sleep(10)
        
        # 10. 验证记忆存储
        logger.info("10. 验证记忆存储功能...")
        
        # 存储一些测试数据
        test_memories = [
            {
                'data_type': 'project_info',
                'data': {'test': 'project_data', 'timestamp': datetime.now().isoformat()},
                'metadata': {'source': 'example_project'},
                'importance': 8,
                'tags': ['test', 'project']
            },
            {
                'data_type': 'decision',
                'data': {'decision': 'use_react_frontend', 'reasoning': 'team_expertise'},
                'metadata': {'decision_maker': 'system_architect'},
                'importance': 9,
                'tags': ['decision', 'frontend', 'react']
            }
        ]
        
        for memory_data in test_memories:
            await memory_manager.send_message(
                to_role="memory_manager",
                action="store_data",
                data=memory_data
            )
            
        logger.info("测试记忆数据已存储")
        
        # 11. 测试记忆检索
        logger.info("11. 测试记忆检索...")
        
        # 检索测试数据
        await memory_manager.send_message(
            to_role="memory_manager",
            action="retrieve_data",
            data={
                'query': {
                    'data_type': 'decision',
                    'importance_min': 5,
                    'limit': 10
                }
            }
        )
        
        logger.info("记忆检索请求已发送")
        
        # 12. 等待所有任务完成
        logger.info("12. 等待系统处理完成...")
        await asyncio.sleep(5)
        
        # 13. 最终状态检查
        logger.info("13. 最终状态检查...")
        
        final_master_status = master_controller.get_status()
        final_memory_status = memory_manager.get_status()
        final_bus_stats = message_bus.get_stats()
        
        logger.info("=== 最终系统状态 ===")
        logger.info(f"主控制器 - 状态: {final_master_status['state']}, "
                   f"完成任务: {final_master_status['stats']['tasks_completed']}, "
                   f"发送消息: {final_master_status['stats']['messages_sent']}")
        
        logger.info(f"记忆管理器 - 状态: {final_memory_status['state']}, "
                   f"完成任务: {final_memory_status['stats']['tasks_completed']}, "
                   f"发送消息: {final_memory_status['stats']['messages_sent']}")
        
        logger.info(f"消息总线 - 发送: {final_bus_stats['messages_sent']}, "
                   f"投递: {final_bus_stats['messages_delivered']}, "
                   f"失败: {final_bus_stats['messages_failed']}")
        
        # 14. 生成项目报告
        logger.info("14. 生成项目运行报告...")
        
        report = {
            'project_name': project_config.name,
            'start_time': datetime.now().isoformat(),
            'duration': '约15秒',
            'system_status': 'running',
            'roles_initialized': ['master_controller', 'memory_manager'],
            'messages_processed': final_bus_stats['messages_sent'],
            'tasks_completed': (final_master_status['stats']['tasks_completed'] + 
                              final_memory_status['stats']['tasks_completed']),
            'success': True
        }
        
        logger.info("=== 项目运行报告 ===")
        for key, value in report.items():
            logger.info(f"{key}: {value}")
            
    except Exception as e:
        logger.error(f"示例项目运行失败: {e}")
        raise
        
    finally:
        # 清理资源
        logger.info("=== 清理系统资源 ===")
        
        try:
            # 关闭角色
            if 'master_controller' in locals():
                await master_controller.shutdown()
                logger.info("主控制器已关闭")
                
            if 'memory_manager' in locals():
                await memory_manager.shutdown()
                logger.info("记忆管理器已关闭")
                
            # 关闭消息总线
            if 'message_bus' in locals():
                await message_bus.stop()
                logger.info("消息总线已关闭")
                
        except Exception as e:
            logger.error(f"清理资源时发生错误: {e}")
            
        logger.info("=== 示例项目完成 ===")


async def quick_system_test():
    """快速系统测试"""
    logger = logging.getLogger('QuickTest')
    
    try:
        logger.info("=== 快速系统测试 ===")
        
        # 1. 测试配置管理器
        logger.info("1. 测试配置管理器...")
        config_manager = get_config_manager()
        
        system_config = config_manager.get_system_config()
        logger.info(f"系统配置加载成功: {system_config.name}")
        
        master_config = config_manager.get_role_config("master_controller")
        logger.info(f"角色配置加载成功: {master_config.role_name}")
        
        # 2. 测试消息总线
        logger.info("2. 测试消息总线...")
        message_bus = MessageBus({'queue_size': 100, 'num_workers': 1})
        await message_bus.start()
        
        # 测试消息发送
        from communication import MessageBuilder, MessageType
        
        test_message = MessageBuilder.create_request(
            from_role="test",
            to_role="test_target",
            action="test_action",
            data={'test': True}
        )
        
        message_id = await message_bus.send_message(test_message)
        logger.info(f"测试消息发送成功: {message_id}")
        
        await asyncio.sleep(1)
        await message_bus.stop()
        
        # 3. 测试角色创建
        logger.info("3. 测试角色创建...")
        
        master_controller = MasterController()
        logger.info(f"主控制器创建成功: {master_controller.role_name}")
        
        memory_manager = MemoryManager()
        logger.info(f"记忆管理器创建成功: {memory_manager.role_name}")
        
        logger.info("=== 快速测试通过 ===")
        return True
        
    except Exception as e:
        logger.error(f"快速测试失败: {e}")
        return False


def create_requirements_file():
    """创建requirements.txt文件"""
    requirements = [
        "aiosqlite>=0.19.0",
        "asyncio",
        "dataclasses",
        "pathlib",
        "enum34",
        "typing",
        "logging",
        "json",
        "datetime",
        "uuid",
        "sqlite3"
    ]
    
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements))
        
    print("requirements.txt 已创建")


def setup_project_structure():
    """设置项目结构"""
    directories = [
        "config",
        "data/memory",
        "logs",
        "backup",
        "roles",
        "communication",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
    print("项目目录结构已创建")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_project_structure()
            create_requirements_file()
            print("项目设置完成")
            
        elif command == "test":
            asyncio.run(quick_system_test())
            
        elif command == "full":
            asyncio.run(run_example_project())
            
        else:
            print("可用命令:")
            print("  setup - 设置项目结构")
            print("  test  - 运行快速测试")
            print("  full  - 运行完整示例项目")
    else:
        # 默认运行完整示例
        asyncio.run(run_example_project())