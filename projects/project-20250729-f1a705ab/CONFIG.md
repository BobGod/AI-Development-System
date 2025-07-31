# 配置管理说明

## 📋 概述

本项目使用分层配置管理机制，将敏感信息与普通配置分离：

- **`.env`** - 存储敏感配置信息（API密钥、数据库密码等）
- **`config/config.yaml`** - 存储普通系统配置
- **`.env.template`** - 环境配置模板文件

## 🔐 敏感信息管理

### 环境配置文件 (.env)

所有敏感信息都存储在项目根目录的 `.env` 文件中：

```bash
# DeepSeek API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# JWT密钥
JWT_SECRET=your_jwt_secret_key_here

# 数据库连接信息
DB_PASSWORD=your_db_password

# 其他API密钥
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
```

### Git忽略设置

`.env` 文件已添加到 `.gitignore` 中，确保不会被提交到版本控制：

```gitignore
# 敏感配置文件
.env
.env.*
*.env
config/secrets.yaml
config/secrets.json
```

## 🛠️ 配置使用方法

### 1. 首次设置

```bash
# 复制模板文件
cp .env.template .env

# 编辑配置文件，填入真实的API密钥
vim .env
```

### 2. 配置读取

系统启动时会自动：

1. 加载 `.env` 文件中的环境变量
2. 读取 `config/config.yaml` 配置文件
3. 使用环境变量替换配置文件中的占位符

### 3. 配置文件中的环境变量引用

在 `config.yaml` 中使用 `${变量名}` 格式引用环境变量：

```yaml
deepseek:
  api_key: "${DEEPSEEK_API_KEY}"
  
security:
  jwt_secret: "${JWT_SECRET}"
```

## 📦 支持的配置类型

### API服务配置
- DeepSeek API密钥
- OpenAI API密钥  
- Google API密钥
- 百度/阿里云API密钥

### 数据库配置
- PostgreSQL连接信息
- Redis缓存配置
- 数据库密码

### 安全配置
- JWT密钥
- 加密密钥
- 会话密钥

### 第三方服务
- 邮件服务配置
- 云存储配置
- 监控服务配置

## 🚀 部署建议

### 开发环境
- 使用 `.env` 文件存储配置
- 定期轮换API密钥
- 不要在代码中硬编码敏感信息

### 生产环境
- 使用环境变量或密钥管理服务
- 启用HTTPS和其他安全措施
- 定期审计和轮换密钥

### Docker部署
```bash
# 使用环境变量
docker run -e DEEPSEEK_API_KEY=your_key your_image

# 或使用env文件
docker run --env-file .env your_image
```

### Kubernetes部署
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
data:
  deepseek-api-key: <base64-encoded-key>
```

## ⚠️ 安全注意事项

1. **永远不要提交 `.env` 文件到Git**
2. **定期轮换API密钥**
3. **使用强密码和随机密钥**
4. **限制API密钥的权限范围**
5. **监控API密钥的使用情况**
6. **在生产环境中使用专业的密钥管理服务**

## 🔧 故障排除

### 环境变量未加载
1. 确认 `.env` 文件位于项目根目录
2. 检查文件权限是否正确
3. 验证环境变量名称拼写

### API密钥无效
1. 检查密钥是否过期
2. 确认密钥权限是否足够
3. 验证API服务是否可用

### 配置文件格式错误
1. 检查YAML语法是否正确
2. 确认环境变量引用格式
3. 验证配置值类型是否匹配