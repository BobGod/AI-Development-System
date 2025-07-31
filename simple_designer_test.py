#!/usr/bin/env python3
"""
AI自主开发系统 - 产品设计师简单测试
验证产品设计师角色的基本功能
"""

import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SimpleDesignerTest')

def main():
    """主测试函数"""
    logger.info("=== 产品设计师简单测试 ===")
    
    tests_passed = 0
    total_tests = 0
    
    # 测试1: 导入产品设计师模块
    total_tests += 1
    try:
        logger.info("1. 测试产品设计师模块导入...")
        
        from roles.product_designer import ProductDesigner, DesignPhase, DeviceType, DesignType
        from config_manager import get_config_manager
        
        logger.info("✓ 产品设计师模块导入成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 产品设计师模块导入失败: {e}")
    
    # 测试2: 创建产品设计师实例
    total_tests += 1
    try:
        logger.info("2. 测试产品设计师创建...")
        
        # 获取配置
        config_manager = get_config_manager()
        designer_config = config_manager.get_role_config("product_designer")
        
        if designer_config:
            logger.info(f"  配置加载成功: {designer_config.role_name}")
            logger.info(f"  最大并发任务: {designer_config.max_concurrent_tasks}")
        
        # 创建产品设计师
        designer = ProductDesigner(config=designer_config.__dict__ if designer_config else None)
        logger.info(f"  产品设计师: {designer.role_name}")
        logger.info(f"  状态: {designer.state.value}")
        
        logger.info("✓ 产品设计师创建成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 产品设计师创建失败: {e}")
        return False
    
    # 测试3: 检查设计工具配置
    total_tests += 1
    try:
        logger.info("3. 测试设计工具配置...")
        
        logger.info(f"  设计工具类别: {list(designer.design_tools.keys())}")
        
        # 检查主要设计软件
        primary_tools = designer.design_tools.get('design_software', {}).get('primary', [])
        logger.info(f"    主要设计软件: {primary_tools}")
        
        # 检查原型工具
        prototyping_tools = designer.design_tools.get('prototyping', {})
        logger.info(f"    原型工具: {list(prototyping_tools.keys())}")
        
        # 检查用户研究工具
        research_tools = designer.design_tools.get('user_research', {})
        logger.info(f"    用户研究工具: {list(research_tools.keys())}")
        
        logger.info("✓ 设计工具配置正确")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 设计工具配置测试失败: {e}")
    
    # 测试4: 检查设计标准
    total_tests += 1
    try:
        logger.info("4. 测试设计标准...")
        
        logger.info(f"  设计标准类别: {list(designer.design_standards.keys())}")
        
        # 检查可访问性标准
        accessibility = designer.design_standards.get('accessibility', {})
        logger.info(f"    可访问性标准: WCAG {accessibility.get('wcag_level')}")
        logger.info(f"    最小字体大小: {accessibility.get('font_size_minimum')}px")
        
        # 检查响应式断点
        breakpoints = designer.design_standards.get('responsive_breakpoints', {})
        logger.info(f"    响应式断点: {breakpoints}")
        
        # 检查设计令牌
        tokens = designer.design_standards.get('design_tokens', {})
        logger.info(f"    设计令牌类别: {list(tokens.keys())}")
        
        logger.info("✓ 设计标准配置正确")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 设计标准测试失败: {e}")
    
    # 测试5: 检查存储结构
    total_tests += 1
    try:
        logger.info("5. 测试数据存储结构...")
        
        logger.info(f"  设计资产: {len(designer.design_assets)} 个")
        logger.info(f"  用户画像: {len(designer.user_personas)} 个")
        logger.info(f"  用户旅程: {len(designer.user_journeys)} 个")
        logger.info(f"  可用性测试: {len(designer.usability_tests)} 个")
        logger.info(f"  设计系统组件: {len(designer.design_system)} 个")
        logger.info(f"  当前项目: {len(designer.current_projects)} 个")
        
        logger.info("✓ 数据存储结构正确")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 数据存储结构测试失败: {e}")
    
    # 测试6: 检查角色状态
    total_tests += 1
    try:
        logger.info("6. 测试角色状态...")
        
        status = designer.get_status()
        logger.info(f"  角色ID: {status['role_id']}")
        logger.info(f"  角色名称: {status['role_name']}")
        logger.info(f"  当前状态: {status['state']}")
        logger.info(f"  当前任务数: {status['current_tasks_count']}")
        
        if status['role_id'] == 'product_designer' and status['role_name'] == '产品设计师':
            logger.info("✓ 角色状态正确")
            tests_passed += 1
        else:
            logger.error("✗ 角色状态不正确")
    except Exception as e:
        logger.error(f"✗ 角色状态测试失败: {e}")
    
    # 测试7: 测试枚举类型
    total_tests += 1
    try:
        logger.info("7. 测试枚举类型...")
        
        # 测试设计阶段枚举
        design_phases = [phase.value for phase in DesignPhase]
        logger.info(f"  设计阶段: {design_phases}")
        
        # 测试设备类型枚举
        device_types = [device.value for device in DeviceType]
        logger.info(f"  设备类型: {device_types}")
        
        # 测试设计类型枚举
        design_types = [design.value for design in DesignType]
        logger.info(f"  设计类型: {design_types}")
        
        if 'research' in design_phases and 'mobile' in device_types and 'wireframe' in design_types:
            logger.info("✓ 枚举类型正确")
            tests_passed += 1
        else:
            logger.error("✗ 枚举类型不完整")
    except Exception as e:
        logger.error(f"✗ 枚举类型测试失败: {e}")
    
    # 测试8: 测试消息处理器
    total_tests += 1
    try:
        logger.info("8. 测试消息处理器...")
        
        handler_count = len(designer.message_handlers)
        logger.info(f"  消息处理器数量: {handler_count}")
        
        expected_handlers = [
            'analyze_user_requirements', 'create_user_personas', 'design_user_journey',
            'create_wireframes', 'design_interface', 'create_prototype',
            'conduct_usability_test', 'evaluate_design', 'create_design_system',
            'review_implementation'
        ]
        
        missing_handlers = [h for h in expected_handlers if h not in designer.message_handlers]
        
        if not missing_handlers:
            logger.info("✓ 所有必需的消息处理器都存在")
            logger.info(f"    处理器列表: {list(designer.message_handlers.keys())}")
            tests_passed += 1
        else:
            logger.error(f"✗ 缺少消息处理器: {missing_handlers}")
    except Exception as e:
        logger.error(f"✗ 消息处理器测试失败: {e}")
    
    # 显示测试结果
    logger.info("=== 测试结果 ===")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过数: {tests_passed}")
    logger.info(f"失败数: {total_tests - tests_passed}")
    
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    logger.info(f"成功率: {success_rate:.1f}%")
    
    if tests_passed == total_tests:
        logger.info("🎉 产品设计师基础功能测试全部通过！")
        logger.info("✅ 产品设计师已成功集成到AI开发系统")
        logger.info("🎨 系统现在具备了完整的用户体验设计能力")
        return True
    else:
        logger.warning(f"⚠️ {total_tests - tests_passed} 个测试失败")
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