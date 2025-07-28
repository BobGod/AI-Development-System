#!/usr/bin/env python3
"""
AI自主开发系统 - 基础测试
验证核心组件的基本功能
"""

import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('BasicTest')

def main():
    """主测试函数"""
    logger.info("=== AI自主开发系统 - 基础测试 ===")
    
    tests_passed = 0
    total_tests = 0
    
    # 测试1: 导入模块
    total_tests += 1
    try:
        logger.info("1. 测试模块导入...")
        
        from config_manager import get_config_manager, SystemConfig, RoleConfig
        from communication import MessageBuilder, MessageType, Priority, Message
        from roles.base_role import BaseRole, Task, TaskStatus, RoleState
        from roles.master_controller import MasterController, ProjectPhase
        from roles.memory_manager_simple import MemoryManager, DataType
        
        logger.info("✓ 所有模块导入成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 模块导入失败: {e}")
    
    # 测试2: 配置管理
    total_tests += 1
    try:
        logger.info("2. 测试配置管理...")
        
        config_manager = get_config_manager()
        system_config = config_manager.get_system_config()
        
        logger.info(f"  系统名称: {system_config.name}")
        logger.info(f"  版本: {system_config.version}")
        logger.info(f"  环境: {system_config.environment}")
        
        # 测试角色配置
        master_config = config_manager.get_role_config("master_controller")
        if master_config:
            logger.info(f"  主控制器配置: {master_config.role_name}")
        
        logger.info("✓ 配置管理测试成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 配置管理测试失败: {e}")
    
    # 测试3: 消息协议
    total_tests += 1
    try:
        logger.info("3. 测试消息协议...")
        
        # 创建消息
        message = MessageBuilder.create_request(
            from_role="test_sender",
            to_role="test_receiver",
            action="test_action",
            data={"message": "Hello World", "timestamp": datetime.now().isoformat()},
            priority=Priority.HIGH
        )
        
        logger.info(f"  消息ID: {message.header.message_id}")
        logger.info(f"  消息类型: {message.header.message_type.value}")
        logger.info(f"  优先级: {message.header.priority.value}")
        logger.info(f"  动作: {message.body.action}")
        
        # 验证消息
        from communication import MessageValidator
        is_valid, msg = MessageValidator.validate_message(message)
        
        if is_valid:
            logger.info("✓ 消息协议测试成功")
            tests_passed += 1
        else:
            logger.error(f"✗ 消息验证失败: {msg}")
    except Exception as e:
        logger.error(f"✗ 消息协议测试失败: {e}")
    
    # 测试4: AI角色创建
    total_tests += 1
    try:
        logger.info("4. 测试AI角色创建...")
        
        # 创建主控制器
        master = MasterController()
        logger.info(f"  主控制器: {master.role_name} (状态: {master.state.value})")
        
        # 创建记忆管理器
        memory = MemoryManager()
        logger.info(f"  记忆管理器: {memory.role_name} (状态: {memory.state.value})")
        
        # 测试角色状态
        master_status = master.get_status()
        logger.info(f"  主控制器状态: {master_status['state']}")
        
        memory_status = memory.get_status()
        logger.info(f"  记忆管理器状态: {memory_status['state']}")
        
        logger.info("✓ AI角色创建测试成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ AI角色创建测试失败: {e}")
    
    # 测试5: 项目配置
    total_tests += 1
    try:
        logger.info("5. 测试项目配置...")
        
        from system_orchestrator import ProjectConfig
        
        project_config = ProjectConfig(
            name="测试项目",
            description="这是一个测试项目",
            requirements="基本功能测试",
            constraints=["时间限制", "资源限制"],
            timeline="2024-01-01 到 2024-01-07"
        )
        
        logger.info(f"  项目名称: {project_config.name}")
        logger.info(f"  项目描述: {project_config.description}")
        logger.info(f"  约束条件: {len(project_config.constraints)} 个")
        
        logger.info("✓ 项目配置测试成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 项目配置测试失败: {e}")
    
    # 显示测试结果
    logger.info("=== 测试结果 ===")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过数: {tests_passed}")
    logger.info(f"失败数: {total_tests - tests_passed}")
    
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    logger.info(f"成功率: {success_rate:.1f}%")
    
    if tests_passed == total_tests:
        logger.info("🎉 所有测试通过！系统基础功能正常")
        logger.info("系统已准备好运行更复杂的场景")
        return True
    else:
        logger.warning(f"⚠️ {total_tests - tests_passed} 个测试失败，需要修复")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        exit(1)
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        exit(1)