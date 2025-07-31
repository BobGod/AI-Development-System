#!/usr/bin/env python3
"""
AI自主开发系统 - DevOps工程师简单测试
验证DevOps工程师角色的基本功能
"""

import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SimpleDevOpsTest')

def main():
    """主测试函数"""
    logger.info("=== DevOps工程师简单测试 ===")
    
    tests_passed = 0
    total_tests = 0
    
    # 测试1: 导入DevOps模块
    total_tests += 1
    try:
        logger.info("1. 测试DevOps模块导入...")
        
        from roles.devops_engineer import DevOpsEngineer, DeploymentStrategy, EnvironmentType
        from config_manager import get_config_manager
        
        logger.info("✓ DevOps模块导入成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ DevOps模块导入失败: {e}")
    
    # 测试2: 创建DevOps工程师实例
    total_tests += 1
    try:
        logger.info("2. 测试DevOps工程师创建...")
        
        # 获取配置
        config_manager = get_config_manager()
        devops_config = config_manager.get_role_config("devops_engineer")
        
        if devops_config:
            logger.info(f"  配置加载成功: {devops_config.role_name}")
            logger.info(f"  最大并发任务: {devops_config.max_concurrent_tasks}")
        
        # 创建DevOps工程师
        devops = DevOpsEngineer(config=devops_config.__dict__ if devops_config else None)
        logger.info(f"  DevOps工程师: {devops.role_name}")
        logger.info(f"  状态: {devops.state.value}")
        
        logger.info("✓ DevOps工程师创建成功")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ DevOps工程师创建失败: {e}")
        return False
    
    # 测试3: 检查默认环境
    total_tests += 1
    try:
        logger.info("3. 测试默认环境...")
        
        logger.info(f"  环境数量: {len(devops.environments)}")
        for env_name, env in devops.environments.items():
            logger.info(f"    {env_name}: {env.type.value} - {env.status}")
            logger.info(f"      资源: {env.resources}")
        
        # 检查是否有必需的环境
        required_envs = ['development', 'testing', 'staging', 'production']
        missing_envs = [env for env in required_envs if env not in devops.environments]
        
        if not missing_envs:
            logger.info("✓ 所有必需环境都存在")
            tests_passed += 1
        else:
            logger.error(f"✗ 缺少环境: {missing_envs}")
    except Exception as e:
        logger.error(f"✗ 默认环境测试失败: {e}")
    
    # 测试4: 检查告警规则
    total_tests += 1
    try:
        logger.info("4. 测试告警规则...")
        
        logger.info(f"  告警规则数量: {len(devops.alert_rules)}")
        for rule_name, rule in devops.alert_rules.items():
            logger.info(f"    {rule_name}: 阈值={rule['threshold']}, 严重性={rule['severity']}")
        
        # 检查关键告警规则
        required_rules = ['high_cpu', 'high_memory', 'high_error_rate']
        missing_rules = [rule for rule in required_rules if rule not in devops.alert_rules]
        
        if not missing_rules:
            logger.info("✓ 关键告警规则都存在")
            tests_passed += 1
        else:
            logger.error(f"✗ 缺少告警规则: {missing_rules}")
    except Exception as e:
        logger.error(f"✗ 告警规则测试失败: {e}")
    
    # 测试5: 检查安全策略
    total_tests += 1
    try:
        logger.info("5. 测试安全策略...")
        
        logger.info(f"  安全策略数量: {len(devops.security_policies)}")
        for policy, enabled in devops.security_policies.items():
            logger.info(f"    {policy}: {'启用' if enabled else '禁用'}")
        
        # 检查关键安全策略
        required_policies = ['encryption_in_transit', 'encryption_at_rest', 'container_scanning']
        missing_policies = [policy for policy in required_policies if policy not in devops.security_policies]
        
        if not missing_policies:
            logger.info("✓ 关键安全策略都存在")
            tests_passed += 1
        else:
            logger.error(f"✗ 缺少安全策略: {missing_policies}")
    except Exception as e:
        logger.error(f"✗ 安全策略测试失败: {e}")
    
    # 测试6: 检查角色状态
    total_tests += 1
    try:
        logger.info("6. 测试角色状态...")
        
        status = devops.get_status()
        logger.info(f"  角色ID: {status['role_id']}")
        logger.info(f"  角色名称: {status['role_name']}")
        logger.info(f"  当前状态: {status['state']}")
        logger.info(f"  当前任务数: {status['current_tasks_count']}")
        
        if status['role_id'] == 'devops_engineer' and status['role_name'] == 'DevOps工程师':
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
        
        # 测试部署策略枚举
        strategies = [strategy.value for strategy in DeploymentStrategy]
        logger.info(f"  部署策略: {strategies}")
        
        # 测试环境类型枚举
        env_types = [env_type.value for env_type in EnvironmentType]
        logger.info(f"  环境类型: {env_types}")
        
        if 'blue_green' in strategies and 'production' in env_types:
            logger.info("✓ 枚举类型正确")
            tests_passed += 1
        else:
            logger.error("✗ 枚举类型不完整")
    except Exception as e:
        logger.error(f"✗ 枚举类型测试失败: {e}")
    
    # 显示测试结果
    logger.info("=== 测试结果 ===")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过数: {tests_passed}")
    logger.info(f"失败数: {total_tests - tests_passed}")
    
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    logger.info(f"成功率: {success_rate:.1f}%")
    
    if tests_passed == total_tests:
        logger.info("🎉 DevOps工程师基础功能测试全部通过！")
        logger.info("✅ DevOps工程师已成功集成到AI开发系统")
        logger.info("🚀 系统现在具备了完整的部署运维能力")
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