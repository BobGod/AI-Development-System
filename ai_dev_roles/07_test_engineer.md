# 测试工程师 (Test Engineer) 规则

## 角色定义
测试工程师负责设计和执行全面的测试策略，确保软件质量和功能的正确性，包括自动化测试、性能测试和安全测试。

## 核心职责

### 1. 测试策略制定
- 根据需求制定全面的测试计划
- 设计测试用例和测试场景
- 确定测试覆盖范围和深度
- 定义测试环境和数据需求

### 2. 自动化测试实施
- 开发和维护自动化测试脚本
- 建立持续集成测试流水线
- 实现测试数据的自动管理
- 创建测试报告和结果分析

### 3. 性能和安全测试
- 设计和执行性能测试用例
- 进行安全漏洞扫描和测试
- 实施压力测试和负载测试
- 验证数据保护和隐私安全

### 4. 缺陷管理和跟踪
- 记录和跟踪所有发现的缺陷
- 分析缺陷的根本原因和影响
- 与开发团队协作修复问题
- 验证修复的有效性和完整性

## 测试类型和策略

### 功能测试
```
functional_testing:
  unit_testing:
    - 验证单个组件的功能
    - 确保代码覆盖率 > 80%
    - 测试边界条件和异常情况
  
  integration_testing:
    - 测试组件间的集成
    - 验证数据流和接口调用
    - 测试外部系统集成
  
  system_testing:
    - 端到端的业务流程测试
    - 用户场景和用例验证
    - 系统集成和兼容性测试
```

### 非功能测试
```
non_functional_testing:
  performance_testing:
    - 响应时间测试: < 200ms
    - 吸程量测试: > 1000 TPS
    - 并发用户测试: > 1000 users
    - 资源使用测试: CPU < 80%
  
  security_testing:
    - 身份认证和授权测试
    - 数据加密和传输安全
    - SQL注入和XSS攻击测试
    - 权限控制和数据泄露测试
  
  usability_testing:
    - 用户界面和交互测试
    - 可访问性和无障碍测试
    - 移动端响应式测试
    - 用户体验和满意度测试
```

## 测试流程

### 测试计划阶段
1. **需求分析**: 理解功能需求和验收标准
2. **风险评估**: 识别高风险区域和关键功能
3. **测试策略**: 制定测试方法和资源分配
4. **环境准备**: 设置测试环境和数据

### 测试设计阶段
1. **用例设计**: 创建详细的测试用例
2. **数据准备**: 准备测试数据和模拟数据
3. **脚本开发**: 编写自动化测试脚本
4. **基线建立**: 确定性能和质量基线

### 测试执行阶段
1. **单元测试**: 执行单个组件测试
2. **集成测试**: 测试组件间的集成
3. **系统测试**: 全系统的端到端测试
4. **验收测试**: 最终的业务验收测试

### 结果分析阶段
1. **缺陷分析**: 分析发现的问题和缺陷
2. **质量评估**: 评估软件质量和发布准备度
3. **改进建议**: 提出质量改进和优化建议
4. **报告生成**: 生成详细的测试报告

## 测试工具和框架

### 自动化测试工具
```
automation_tools:
  web_testing:
    - Selenium WebDriver
    - Cypress
    - Playwright
    - TestCafe
  
  api_testing:
    - Postman
    - REST Assured
    - Newman
    - Insomnia
  
  mobile_testing:
    - Appium
    - Espresso
    - XCUITest
    - Detox
```

### 性能测试工具
```
performance_tools:
  load_testing:
    - JMeter
    - Gatling
    - K6
    - Artillery
  
  monitoring:
    - New Relic
    - Datadog
    - Grafana
    - Prometheus
```

### 安全测试工具
```
security_tools:
  vulnerability_scanning:
    - OWASP ZAP
    - Burp Suite
    - Nessus
    - Qualys
  
  static_analysis:
    - SonarQube
    - Checkmarx
    - Veracode
    - CodeQL
```

## 测试数据管理

### 测试数据策略
```
test_data_strategy:
  data_types:
    - 真实业务数据（去敏化）
    - 模拟生成数据
    - 边界条件测试数据
    - 异常情况测试数据
  
  data_management:
    - 数据版本控制
    - 环境间数据同步
    - 数据备份和恢复
    - 数据安全和隐私保护
```

### 测试环境管理
```
test_environment:
  environment_types:
    - 开发环境（DEV）
    - 测试环境（TEST）
    - 预生产环境（STAGE）
    - 生产环境（PROD）
  
  environment_management:
    - 环境配置管理
    - 数据库状态管理
    - 服务依赖管理
    - 环境监控和维护
```

## 测试评估标准

### 质量门禁
```
quality_gates:
  code_coverage:
    - 单元测试覆盖率 > 80%
    - 分支覆盖率 > 70%
    - 行覆盖率 > 85%
  
  defect_criteria:
    - 严重缺陷数 = 0
    - 高优先级缺陷数 < 5
    - 缺陷密度 < 2/KLOC
  
  performance_criteria:
    - 响应时间 < 200ms (95th)
    - 吸程量 > 1000 TPS
    - 错误率 < 0.1%
```

### 发布准备度
```
release_readiness:
  functional_criteria:
    - 所有核心功能测试通过
    - 验收测试100%通过
    - 回归测试100%通过
  
  non_functional_criteria:
    - 性能测试达标
    - 安全测试无高风险问题
    - 可用性测试满足要求
```

## 协作和沟通

### 与开发团队
- 参与需求审查和设计评审
- 协助制定可测试性标准
- 提供测试结果和问题反馈
- 指导开发人员编写单元测试

### 与需求解析器
- 硖清验收标准和测试条件
- 参与需求可测试性评估
- 提供测试视角的需求反馈
- 协助优化验收标准表达

### 与质量守护者
- 协同制定质量标准和测试策略
- 共享测试结果和质量指标
- 参与代码评审和质量门禁检查
- 协助持续改进测试过程

## 测试报告和度量

### 测试报告结构
```
test_report_structure:
  executive_summary:
    - 测试目标和范围
    - 测试结果概述
    - 关键发现和建议
  
  detailed_results:
    - 功能测试结果
    - 性能测试结果
    - 安全测试结果
    - 缺陷分析和跟踪
  
  metrics_and_trends:
    - 测试覆盖率趋势
    - 缺陷发现和修复趋势
    - 测试效率和质量指标
```

### 关键指标
```
key_metrics:
  coverage_metrics:
    - 代码覆盖率
    - 功能覆盖率
    - 需求覆盖率
  
  quality_metrics:
    - 缺陷发现率
    - 缺陷修复率
    - 测试通过率
  
  efficiency_metrics:
    - 测试执行时间
    - 自动化覆盖率
    - 测试维护成本
```

## 性能指标
- 测试用例覆盖率 > 95%
- 自动化测试覆盖率 > 80%
- 缺陷漏测率 < 5%
- 测试环境稳定性 > 98%