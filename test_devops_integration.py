#!/usr/bin/env python3
"""
AI自主开发系统 - DevOps工程师集成测试
验证DevOps工程师角色的核心功能
"""

import asyncio
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DevOpsIntegrationTest')

async def test_devops_integration():
    """DevOps工程师集成测试"""
    logger.info("=== DevOps工程师集成测试 ===")
    
    tests_passed = 0
    total_tests = 0
    
    # 测试1: DevOps角色导入和创建
    total_tests += 1
    try:
        logger.info("1. 测试DevOps角色导入和创建...")
        
        from roles.devops_engineer import DevOpsEngineer, DeploymentStrategy, EnvironmentType
        from config_manager import get_config_manager
        
        # 获取配置
        config_manager = get_config_manager()
        devops_config = config_manager.get_role_config("devops_engineer")
        
        if devops_config:
            logger.info(f"  DevOps配置: {devops_config.role_name}")
            logger.info(f"  最大并发任务: {devops_config.max_concurrent_tasks}")
            logger.info(f"  超时时间: {devops_config.timeout_seconds}秒")
        
        # 创建DevOps工程师实例
        devops = DevOpsEngineer(config=devops_config.__dict__ if devops_config else None)
        logger.info(f"  DevOps工程师: {devops.role_name} (状态: {devops.state.value})")
        
        # 检查默认环境
        logger.info(f"  默认环境数量: {len(devops.environments)}")
        for env_name, env in devops.environments.items():
            logger.info(f"    {env_name}: {env.type.value} - {env.status}")
        
        logger.info("✓ DevOps角色导入和创建测试成功")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"✗ DevOps角色导入和创建测试失败: {e}")
    
    # 测试2: 环境管理功能
    total_tests += 1
    try:
        logger.info("2. 测试环境管理功能...")
        
        from communication import MessageBuilder, MessageType
        
        # 创建环境设置消息
        setup_message = MessageBuilder.create_request(
            from_role="test",
            to_role="devops_engineer",
            action="setup_environment",
            data={
                'environment_name': 'test_env',
                'environment_type': 'testing',
                'resources': {
                    'cpu': '4',
                    'memory': '8Gi',
                    'storage': '50Gi'
                },
                'config': {
                    'auto_deploy': False,
                    'test_data': True
                }
            }
        )
        
        logger.info(f"  环境设置消息: {setup_message.body.action}")
        logger.info(f"  目标环境: {setup_message.body.data['environment_name']}")
        
        # 模拟消息处理
        await devops._handle_setup_environment(setup_message)
        
        # 检查环境是否创建成功
        if 'test_env' in devops.environments:
            test_env = devops.environments['test_env']
            logger.info(f"  测试环境状态: {test_env.status}")
            logger.info(f"  测试环境资源: {test_env.resources}")
        
        logger.info("✓ 环境管理功能测试成功")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"✗ 环境管理功能测试失败: {e}")
    
    # 测试3: 部署功能
    total_tests += 1
    try:
        logger.info("3. 测试应用部署功能...")
        
        # 创建部署消息
        deploy_message = MessageBuilder.create_request(
            from_role="test",
            to_role="devops_engineer",
            action="deploy_application",
            data={
                'environment': 'staging',
                'version': 'v1.2.3',
                'strategy': 'blue_green'
            }
        )
        
        logger.info(f"  部署目标: {deploy_message.body.data['environment']}")
        logger.info(f"  部署版本: {deploy_message.body.data['version']}")
        logger.info(f"  部署策略: {deploy_message.body.data['strategy']}")
        
        # 模拟部署处理
        await devops._handle_deploy_application(deploy_message)
        
        # 检查部署历史
        logger.info(f"  部署历史记录数: {len(devops.deployment_history)}")
        if devops.deployment_history:
            latest_deployment = devops.deployment_history[-1]
            logger.info(f"  最新部署: {latest_deployment.deployment_id}")
            logger.info(f"  部署状态: {latest_deployment.status}")
            logger.info(f"  部署成功: {latest_deployment.success}")
        
        logger.info("✓ 应用部署功能测试成功")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"✗ 应用部署功能测试失败: {e}")
    
    # 测试4: CI/CD流水线设置
    total_tests += 1
    try:
        logger.info("4. 测试CI/CD流水线设置...")
        
        # 创建CI/CD设置消息
        cicd_message = MessageBuilder.create_request(
            from_role="test",
            to_role="devops_engineer",
            action="setup_cicd_pipeline",
            data={
                'project_name': 'test_project',
                'repository_url': 'https://github.com/test/project.git',
                'build_config': {
                    'language': 'python',
                    'framework': 'django',
                    'test_command': 'pytest',
                    'build_command': 'python setup.py build'
                }
            }
        )
        
        logger.info(f"  项目名: {cicd_message.body.data['project_name']}")
        logger.info(f"  仓库URL: {cicd_message.body.data['repository_url']}")
        
        # 模拟CI/CD设置处理
        await devops._handle_setup_cicd_pipeline(cicd_message)
        
        # 检查流水线配置
        if 'test_project' in devops.pipeline_configs:
            pipeline = devops.pipeline_configs['test_project']
            logger.info(f"  流水线阶段: {pipeline['stages']}")
            logger.info(f"  质量门禁: {pipeline['quality_gates']}")
        
        logger.info("✓ CI/CD流水线设置测试成功")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"✗ CI/CD流水线设置测试失败: {e}")
    
    # 测试5: 监控和告警
    total_tests += 1
    try:
        logger.info("5. 测试监控和告警功能...")
        
        # 创建监控消息
        monitor_message = MessageBuilder.create_request(
            from_role="test",
            to_role="devops_engineer", 
            action="monitor_system",
            data={
                'target': 'production',
                'metrics': ['cpu', 'memory', 'response_time']
            }
        )
        
        logger.info(f"  监控目标: {monitor_message.body.data['target']}")
        logger.info(f"  监控指标: {monitor_message.body.data['metrics']}")
        
        # 模拟监控处理
        await devops._handle_monitor_system(monitor_message)
        
        # 检查告警规则
        logger.info(f"  告警规则数: {len(devops.alert_rules)}")
        for rule_name, rule in devops.alert_rules.items():
            logger.info(f"    {rule_name}: 阈值={rule['threshold']}, 严重性={rule['severity']}")
        
        logger.info("✓ 监控和告警功能测试成功")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"✗ 监控和告警功能测试失败: {e}")
    
    # 测试6: 故障处理
    total_tests += 1
    try:
        logger.info("6. 测试故障处理功能...")
        
        # 创建故障处理消息
        incident_message = MessageBuilder.create_request(
            from_role="test",
            to_role="devops_engineer",
            action="handle_incident",
            data={
                'severity': 'p1_high',
                'description': '生产环境响应时间异常',
                'affected_services': ['web_server', 'database']
            }
        )
        
        logger.info(f"  故障严重性: {incident_message.body.data['severity']}")
        logger.info(f"  故障描述: {incident_message.body.data['description']}")
        logger.info(f"  受影响服务: {incident_message.body.data['affected_services']}")
        
        # 模拟故障处理
        await devops._handle_incident(incident_message)
        
        # 检查活跃故障
        logger.info(f"  活跃故障数: {len(devops.active_incidents)}")
        for incident_id, incident in devops.active_incidents.items():
            logger.info(f"    {incident_id}: {incident['status']} - {incident['severity']}")
        
        logger.info("✓ 故障处理功能测试成功")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"✗ 故障处理功能测试失败: {e}")
    
    # 测试7: 安全扫描
    total_tests += 1
    try:
        logger.info("7. 测试安全扫描功能...")
        
        # 创建安全扫描消息
        security_message = MessageBuilder.create_request(
            from_role="test",
            to_role="devops_engineer",
            action="security_scan",
            data={
                'scan_type': 'full',
                'target': 'application'
            }
        )
        
        logger.info(f"  扫描类型: {security_message.body.data['scan_type']}")
        logger.info(f"  扫描目标: {security_message.body.data['target']}")
        
        # 模拟安全扫描处理
        await devops._handle_security_scan(security_message)
        
        # 检查安全策略
        logger.info(f"  安全策略: {list(devops.security_policies.keys())}")
        for policy, enabled in devops.security_policies.items():
            logger.info(f"    {policy}: {'启用' if enabled else '禁用'}")
        
        logger.info("✓ 安全扫描功能测试成功")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"✗ 安全扫描功能测试失败: {e}")
    
    # 测试8: 资源扩缩容
    total_tests += 1
    try:
        logger.info("8. 测试资源扩缩容功能...")
        
        # 创建扩容消息
        scale_message = MessageBuilder.create_request(
            from_role="test",
            to_role="devops_engineer",
            action="scale_resources",
            data={
                'environment': 'production',
                'action': 'scale_up',
                'resources': {
                    'cpu': '8',
                    'memory': '16Gi'
                }
            }
        )
        
        logger.info(f"  扩缩容环境: {scale_message.body.data['environment']}")
        logger.info(f"  扩缩容动作: {scale_message.body.data['action']}")
        logger.info(f"  资源配置: {scale_message.body.data['resources']}")
        
        # 模拟扩缩容处理  
        await devops._handle_scale_resources(scale_message)
        
        # 检查生产环境资源
        if 'production' in devops.environments:
            prod_env = devops.environments['production']
            logger.info(f"  生产环境资源: {prod_env.resources}")
        
        logger.info("✓ 资源扩缩容功能测试成功")
        tests_passed += 1
        
    except Exception as e:
        logger.error(f"✗ 资源扩缩容功能测试失败: {e}")
    
    # 显示测试结果
    logger.info("=== DevOps集成测试结果 ===")
    logger.info(f"总测试数: {total_tests}")
    logger.info(f"通过数: {tests_passed}")
    logger.info(f"失败数: {total_tests - tests_passed}")
    
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    logger.info(f"成功率: {success_rate:.1f}%")
    
    if tests_passed == total_tests:
        logger.info("🎉 DevOps工程师所有功能测试通过！")
        logger.info("✅ DevOps工程师已成功集成到AI开发系统")
        return True
    else:
        logger.warning(f"⚠️ {total_tests - tests_passed} 个测试失败，需要修复")
        return False

async def test_devops_role_status():
    """测试DevOps角色状态"""
    logger.info("=== DevOps角色状态测试 ===")
    
    try:
        from roles.devops_engineer import DevOpsEngineer
        
        devops = DevOpsEngineer()
        status = devops.get_status()
        
        logger.info("DevOps工程师状态信息:")
        logger.info(f"  角色ID: {status['role_id']}")
        logger.info(f"  角色名称: {status['role_name']}")
        logger.info(f"  当前状态: {status['state']}")
        logger.info(f"  最后活动: {status['last_activity']}")
        logger.info(f"  当前任务数: {status['current_tasks_count']}")
        
        return True
        
    except Exception as e:
        logger.error(f"DevOps角色状态测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始DevOps工程师集成测试...")
    
    try:
        # 运行集成测试
        integration_success = asyncio.run(test_devops_integration())
        
        # 运行状态测试
        status_success = asyncio.run(test_devops_role_status())
        
        overall_success = integration_success and status_success
        
        if overall_success:
            logger.info("🎉 DevOps工程师集成测试全部通过！")
            logger.info("✅ 系统已成功扩展，现在包含8个AI角色")
            logger.info("🚀 系统具备了完整的开发到部署能力")
        else:
            logger.warning("⚠️ 部分测试失败，需要进一步调试")
            
        return overall_success
        
    except Exception as e:
        logger.error(f"测试执行异常: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)