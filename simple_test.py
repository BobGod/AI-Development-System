#!/usr/bin/env python3
"""
AI自主开发系统 - 简单测试
快速验证核心组件是否正常工作
"""

import asyncio
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SimpleTest')

def test_imports():
    """测试导入"""
    try:
        logger.info("1. 测试基础导入...")
        
        # 测试配置管理器
        from config_manager import get_config_manager
        config_manager = get_config_manager()
        logger.info("✓ 配置管理器导入成功")
        
        # 测试通信模块
        from communication import MessageBuilder, MessageType, Priority
        logger.info("✓ 通信模块导入成功")
        
        # 测试角色
        from roles.base_role import BaseRole
        from roles.master_controller import MasterController
        from roles.memory_manager_simple import MemoryManager
        logger.info("✓ 角色模块导入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"导入测试失败: {e}")
        return False

def test_config():
    """测试配置"""
    try:
        logger.info("2. 测试配置系统...")
        
        from config_manager import get_config_manager
        config_manager = get_config_manager()
        
        # 测试系统配置
        system_config = config_manager.get_system_config()
        logger.info(f"✓ 系统配置: {system_config.name} v{system_config.version}")
        
        # 测试角色配置
        master_config = config_manager.get_role_config("master_controller")
        if master_config:
            logger.info(f"✓ 角色配置: {master_config.role_name}")
        else:
            logger.warning("! 角色配置未找到")
            
        return True
        
    except Exception as e:
        logger.error(f"配置测试失败: {e}")
        return False

def test_message_creation():
    """测试消息创建"""
    try:
        logger.info("3. 测试消息创建...")
        
        from communication import MessageBuilder, MessageType, Priority
        
        # 创建测试消息
        message = MessageBuilder.create_request(
            from_role="test_sender",
            to_role="test_receiver", 
            action="test_action",
            data={"test": True, "timestamp": datetime.now().isoformat()},
            priority=Priority.NORMAL
        )
        
        logger.info(f"✓ 消息创建成功: {message.header.message_id}")
        logger.info(f"  从: {message.header.from_role} -> 到: {message.header.to_role}")
        logger.info(f"  动作: {message.body.action}")
        
        return True
        
    except Exception as e:
        logger.error(f"消息创建测试失败: {e}")
        return False

async def test_role_creation():
    """测试角色创建"""
    try:
        logger.info("4. 测试AI角色创建...")
        
        from roles.master_controller import MasterController
        from roles.memory_manager_simple import MemoryManager
        
        # 创建主控制器
        master = MasterController()
        logger.info(f"✓ 主控制器创建成功: {master.role_name}")
        logger.info(f"  状态: {master.state.value}")
        
        # 创建记忆管理器
        memory = MemoryManager()
        logger.info(f"✓ 记忆管理器创建成功: {memory.role_name}")
        logger.info(f"  状态: {memory.state.value}")
        
        return True
        
    except Exception as e:
        logger.error(f"角色创建测试失败: {e}")
        return False

async def test_basic_message_bus():
    """测试基础消息总线"""
    try:
        logger.info("5. 测试消息总线...")
        
        from communication import MessageBus, MessageBuilder
        
        # 创建消息总线
        bus = MessageBus({'queue_size': 10, 'num_workers': 1})
        
        # 启动消息总线
        await bus.start()
        logger.info("✓ 消息总线启动成功")
        
        # 创建测试消息
        test_message = MessageBuilder.create_request(
            from_role="test",
            to_role="test_target",
            action="ping",
            data={"message": "Hello World"}
        )
        
        # 发送消息
        message_id = await bus.send_message(test_message)
        logger.info(f"✓ 消息发送成功: {message_id}")
        
        # 等待处理
        await asyncio.sleep(0.1)
        
        # 获取统计
        stats = bus.get_stats()
        logger.info(f"✓ 消息统计: 发送={stats['messages_sent']}, 投递={stats['messages_delivered']}")
        
        # 停止消息总线
        await bus.stop()
        logger.info("✓ 消息总线已停止")
        
        return True
        
    except Exception as e:
        logger.error(f"消息总线测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    try:
        logger.info("=== AI自主开发系统 - 简单测试 ===")
        start_time = datetime.now()
        
        results = []
        
        # 同步测试
        results.append(test_imports())
        results.append(test_config())
        results.append(test_message_creation())
        
        # 异步测试
        results.append(await test_role_creation())
        results.append(await test_basic_message_bus())
        
        # 统计结果
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=== 测试结果 ===")
        logger.info(f"总测试数: {total}")
        logger.info(f"通过数: {passed}")
        logger.info(f"失败数: {total - passed}")
        logger.info(f"成功率: {success_rate:.1f}%")
        logger.info(f"耗时: {duration:.2f}秒")
        
        if passed == total:
            logger.info("🎉 所有测试通过！系统基础功能正常")
            return True
        else:
            logger.warning(f"⚠️ {total - passed} 个测试失败")
            return False
            
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        return False

def main():
    """主函数"""
    try:
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        exit(1)
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        exit(1)

if __name__ == "__main__":
    main()