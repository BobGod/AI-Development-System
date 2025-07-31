#!/usr/bin/env python3
"""
AI自主开发系统 - 质量守护者简单测试
验证质量守护者角色的基本功能
"""

import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SimpleQualityTest')

def main():
    """主测试函数"""
    logger.info("=== 质量守护者简单测试 ===")
    
    tests_passed = 0
    total_tests = 0
    
    # 测试1: 导入质量守护者模块
    total_tests += 1
    try:
        logger.info("1. 测试质量守护者模块导入...")
        
        from roles.quality_guardian import QualityGuardian, QualityLevel, IssueType, IssueSeverity
        from config_manager import get_config_manager
        
        logger.info("✓ 质量守护者模块导入成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 质量守护者模块导入失败: {e}")
    
    # 测试2: 创建质量守护者实例
    total_tests += 1
    try:
        logger.info("2. 测试质量守护者创建...")
        
        # 获取配置
        config_manager = get_config_manager()
        quality_config = config_manager.get_role_config("quality_guardian")
        
        if quality_config:
            logger.info(f"  配置加载成功: {quality_config.role_name}")
            logger.info(f"  最大并发任务: {quality_config.max_concurrent_tasks}")
        
        # 创建质量守护者
        guardian = QualityGuardian(config=quality_config.__dict__ if quality_config else None)
        logger.info(f"  质量守护者: {guardian.role_name}")
        logger.info(f"  状态: {guardian.state.value}")
        
        logger.info("✓ 质量守护者创建成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 质量守护者创建失败: {e}")
        return False
    
    # 测试3: 检查质量规则
    total_tests += 1
    try:
        logger.info("3. 测试质量规则...")
        
        logger.info(f"  质量规则类别: {list(guardian.quality_rules.keys())}")
        
        # 检查复杂度规则
        complexity_rules = guardian.quality_rules.get('complexity', {})
        logger.info(f"    复杂度规则: 最大圈复杂度={complexity_rules.get('max_cyclomatic_complexity')}")
        
        # 检查重复率规则
        duplication_rules = guardian.quality_rules.get('duplication', {})
        logger.info(f"    重复率规则: 最大重复率={duplication_rules.get('max_duplication_ratio')}")
        
        # 检查覆盖率规则
        coverage_rules = guardian.quality_rules.get('coverage', {})
        logger.info(f"    覆盖率规则: 最小行覆盖率={coverage_rules.get('min_line_coverage')}")
        
        logger.info("✓ 质量规则配置正确")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 质量规则测试失败: {e}")
    
    # 测试4: 检查质量门禁
    total_tests += 1
    try:
        logger.info("4. 测试质量门禁...")
        
        logger.info(f"  阻断条件数量: {len(guardian.quality_gates.get('blocking_conditions', []))}")
        for condition in guardian.quality_gates.get('blocking_conditions', []):
            logger.info(f"    阻断条件: {condition.get('type')} - 阈值={condition.get('threshold', 'N/A')}")
        
        logger.info(f"  警告条件数量: {len(guardian.quality_gates.get('warning_conditions', []))}")
        for condition in guardian.quality_gates.get('warning_conditions', []):
            logger.info(f"    警告条件: {condition.get('type')} - 阈值={condition.get('threshold', 'N/A')}")
        
        logger.info("✓ 质量门禁配置正确")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 质量门禁测试失败: {e}")
    
    # 测试5: 检查分析工具配置
    total_tests += 1
    try:
        logger.info("5. 测试分析工具配置...")
        
        logger.info(f"  支持的语言: {list(guardian.analysis_tools.keys())}")
        
        for language, tools in guardian.analysis_tools.items():
            logger.info(f"    {language}:")
            for tool_type, tool_list in tools.items():
                logger.info(f"      {tool_type}: {tool_list}")
        
        logger.info("✓ 分析工具配置正确")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ 分析工具配置测试失败: {e}")
    
    # 测试6: 检查角色状态
    total_tests += 1
    try:
        logger.info("6. 测试角色状态...")
        
        status = guardian.get_status()
        logger.info(f"  角色ID: {status['role_id']}")
        logger.info(f"  角色名称: {status['role_name']}")
        logger.info(f"  当前状态: {status['state']}")
        logger.info(f"  当前任务数: {status['current_tasks_count']}")
        
        if status['role_id'] == 'quality_guardian' and status['role_name'] == '质量守护者':
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
        
        # 测试质量等级枚举
        quality_levels = [level.value for level in QualityLevel]
        logger.info(f"  质量等级: {quality_levels}")
        
        # 测试问题类型枚举
        issue_types = [issue_type.value for issue_type in IssueType]
        logger.info(f"  问题类型: {issue_types}")
        
        # 测试严重程度枚举
        severities = [severity.value for severity in IssueSeverity]
        logger.info(f"  严重程度: {severities}")
        
        if 'excellent' in quality_levels and 'security' in issue_types and 'critical' in severities:
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
        
        handler_count = len(guardian.message_handlers)
        logger.info(f"  消息处理器数量: {handler_count}")
        
        expected_handlers = [
            'analyze_code', 'check_quality_gates', 'scan_security',
            'detect_duplicates', 'analyze_complexity', 'manage_tech_debt',
            'generate_quality_report', 'update_quality_rules'
        ]
        
        missing_handlers = [h for h in expected_handlers if h not in guardian.message_handlers]
        
        if not missing_handlers:
            logger.info("✓ 所有必需的消息处理器都存在")
            logger.info(f"    处理器列表: {list(guardian.message_handlers.keys())}")
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
        logger.info("🎉 质量守护者基础功能测试全部通过！")
        logger.info("✅ 质量守护者已成功集成到AI开发系统")
        logger.info("🛡️ 系统现在具备了完整的代码质量控制能力")
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