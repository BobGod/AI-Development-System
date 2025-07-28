# AI自主开发系统 v2.0

🤖 **企业级AI驱动的全栈开发系统**

一个完整的AI开发底座，支持多项目管理、智能代码生成、质量控制和自动化部署。

## ✨ 核心特性

### 🎯 多项目管理
- **完全隔离**: 每个项目拥有独立的工作空间、配置和记忆
- **项目模板**: 支持Web应用、API服务、移动应用等多种项目类型
- **生命周期管理**: 从创建到归档的完整项目生命周期支持
- **版本控制**: 项目和系统的独立版本管理

### 🧠 智能AI角色系统
拥有10个专业AI角色，覆盖完整的软件开发生命周期：

- **项目总控制器** - 统筹项目全局
- **记忆管理器** - 管理项目知识和经验
- **状态监控器** - 监控系统和项目状态
- **需求解析器** - 分析和解析用户需求
- **产品设计师** - UX/UI设计和用户体验
- **系统架构师** - 系统架构和技术选型
- **质量守护者** - 代码质量控制和技术债务管理
- **DevOps工程师** - 部署运维和CI/CD管理
- **开发团队** - 前端、后端、全栈、移动端开发
- **测试工程师** - 测试策略和质量保证

### 🧬 系统记忆与学习
- **多层记忆**: 核心记忆、项目记忆、学习记忆、进化记忆
- **经验积累**: 从成功和失败中自动学习
- **知识沉淀**: 最佳实践和领域专业知识积累
- **智能推荐**: 基于历史经验的智能建议

### 🛡️ 企业级管理
- **项目隔离**: 确保不同项目完全独立，互不干扰
- **权限控制**: 分层的访问控制和安全管理
- **监控告警**: 系统健康监控和异常告警
- **备份恢复**: 完善的数据备份和恢复机制

## 🏗️ 系统架构

```
AI开发系统底座
├── system-core/        # 核心系统（稳定底座）
├── system-config/      # 系统配置
├── system-memory/      # AI记忆系统
├── projects/          # 项目工作区
├── version-control/   # 版本控制
├── tools/            # 管理工具
└── scripts/          # 脚本工具
```

### 项目隔离架构
每个项目拥有完全独立的：
- ✅ 配置空间 - 项目特定配置
- ✅ 工作空间 - 独立的代码和文档
- ✅ 记忆空间 - 项目相关经验
- ✅ 日志空间 - 开发过程记录

## 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   系统编排器    │    │   配置管理器    │    │   消息总线      │
│ SystemOrchestrator│    │ ConfigManager   │    │ MessageBus      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   主控制器      │    │   记忆管理器    │    │   状态监控器    │
│ MasterController│    │ MemoryManager   │    │ StatusMonitor   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   需求解析器    │    │   系统架构师    │    │   开发工程师组  │
│RequirementsParser│    │SystemArchitect  │    │DevelopmentTeam  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │   测试工程师    │
                    │ TestEngineer    │
                    └─────────────────┘
```

## 项目结构

```
claudeCode/
├── ai_dev_roles/           # AI角色规则文档
│   ├── 01_master_controller.md
│   ├── 02_memory_manager.md
│   ├── 03_status_monitor.md
│   ├── 04_requirements_parser.md
│   ├── 05_system_architect.md
│   ├── 06_development_team.md
│   └── 07_test_engineer.md
├── communication/          # 通信模块
│   ├── __init__.py
│   ├── message_protocol.py # 消息协议定义
│   └── message_bus.py     # 消息总线实现
├── roles/                 # AI角色实现
│   ├── base_role.py       # 基础角色类
│   ├── master_controller.py
│   └── memory_manager.py
├── config/               # 配置文件
│   ├── system_config.json
│   └── ...
├── data/                # 数据存储
│   └── memory/
├── logs/                # 日志文件
├── system_orchestrator.py # 系统编排器
├── config_manager.py     # 配置管理器
├── example_project.py    # 示例项目
└── README.md
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd /Users/zhengwei/Desktop/工作/code/claudeCode

# 安装依赖
pip install aiosqlite asyncio

# 创建项目结构
python example_project.py setup
```

### 2. 运行快速测试

```bash
# 运行快速系统测试
python example_project.py test
```

### 3. 运行完整示例

```bash
# 运行完整示例项目
python example_project.py full
```

## 使用示例

### 基本使用

```python
import asyncio
from system_orchestrator import SystemOrchestrator, ProjectConfig

async def main():
    # 创建项目配置
    project_config = ProjectConfig(
        name="我的项目",
        description="项目描述",
        requirements="功能需求...",
        constraints=["时间限制", "技术栈限制"],
        timeline="开发时间线"
    )
    
    # 创建系统编排器
    orchestrator = SystemOrchestrator()
    
    # 初始化系统
    await orchestrator.initialize_system(project_config)
    
    # 处理用户请求
    response = await orchestrator.process_user_request("开始开发项目")
    
    # 关闭系统
    await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### 配置管理

```python
from config_manager import get_config_manager

# 获取配置管理器
config_manager = get_config_manager()

# 获取系统配置
system_config = config_manager.get_system_config()
print(f"系统名称: {system_config.name}")

# 获取角色配置
master_config = config_manager.get_role_config("master_controller")
print(f"主控制器最大任务数: {master_config.max_concurrent_tasks}")
```

### 消息通信

```python
from communication import MessageBuilder, MessageBus

# 创建消息
message = MessageBuilder.create_request(
    from_role="sender",
    to_role="receiver",
    action="test_action",
    data={"key": "value"}
)

# 发送消息
message_bus = MessageBus()
await message_bus.start()
message_id = await message_bus.send_message(message)
```

## 配置说明

### 系统配置 (config/system_config.json)

```json
{
  "system": {
    "name": "AI自主开发系统",
    "version": "1.0.0",
    "session_timeout": 3600,
    "max_concurrent_tasks": 10,
    "log_level": "INFO"
  }
}
```

### 角色配置

每个AI角色都有独立的配置参数：

- `enabled`: 是否启用该角色
- `max_concurrent_tasks`: 最大并发任务数
- `timeout_seconds`: 任务超时时间
- `auto_restart`: 是否自动重启
- `priority`: 角色优先级

## 开发指南

### 添加新角色

1. 在 `ai_dev_roles/` 中创建角色规则文档
2. 在 `roles/` 中实现角色类，继承 `BaseRole`
3. 在配置文件中添加角色配置
4. 在系统编排器中注册角色

### 扩展消息类型

1. 在 `communication/message_protocol.py` 中添加新的消息类型
2. 在相关角色中添加消息处理器
3. 更新消息模板

### 自定义配置

1. 在 `config_manager.py` 中定义新的配置类
2. 添加配置验证逻辑
3. 在角色中使用配置

## 日志和监控

系统提供完整的日志记录和监控功能：

- **系统日志**: 记录在 `logs/` 目录
- **消息跟踪**: 跟踪所有角色间的消息传递
- **性能监控**: 监控任务执行时间和成功率
- **状态报告**: 定期生成系统状态报告

## 故障排除

### 常见问题

1. **角色启动失败**
   - 检查配置文件是否正确
   - 确认数据目录权限
   - 查看日志文件获取详细错误信息

2. **消息传递异常**
   - 检查消息总线状态
   - 验证角色注册情况
   - 确认消息格式正确

3. **数据库连接问题**
   - 检查SQLite文件权限
   - 确认存储路径存在
   - 重新初始化数据库

### 调试模式

在配置中启用调试模式：

```python
config_manager.update_system_config(debug_mode=True, log_level="DEBUG")
```

## 性能优化

- **消息队列大小**: 根据系统负载调整队列大小
- **工作者数量**: 增加消息处理工作者数量
- **缓存大小**: 调整记忆管理器缓存大小
- **备份频率**: 根据需要调整备份间隔

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请创建 Issue 或发送邮件。

---

**注意**: 这是一个实验性项目，用于探索AI自主开发的可能性。系统仍在持续改进中。