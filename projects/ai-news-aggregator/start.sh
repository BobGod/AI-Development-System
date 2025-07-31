#!/bin/bash

# AI智能新闻聚合平台启动脚本
# 🚀 一键启动超越量子位、机器之心的全自动化AI新闻平台

echo "🤖 AI智能新闻聚合平台启动脚本"
echo "=================================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✅ Python版本: $python_version"
else
    echo "❌ 错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查是否存在.env文件
if [ ! -f ".env" ]; then
    echo "📝 首次运行，创建配置文件..."
    cp .env.template .env
    echo "⚠️  请编辑 .env 文件，填入你的API密钥："
    echo "   - DEEPSEEK_API_KEY (必需)"
    echo "   - OPENAI_API_KEY (可选，用于图片生成)"
    echo "   - UNSPLASH_ACCESS_KEY (可选，用于图片搜索)"
    echo ""
    echo "配置完成后，再次运行此脚本启动系统。"
    exit 0
fi

# 检查DeepSeek API密钥
if ! grep -q "DEEPSEEK_API_KEY=sk-" .env; then
    echo "⚠️  警告: 未检测到有效的DeepSeek API密钥"
    echo "   系统将在模拟模式下运行，部分功能可能受限"
    read -p "继续启动吗? (y/N): " confirm
    if [[ $confirm != [yY] ]]; then
        echo "启动取消"
        exit 0
    fi
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📚 安装依赖包..."
pip install -r requirements.txt

# 创建必要目录
echo "📁 创建目录结构..."
mkdir -p static generated_images uploads logs

# 运行预检查
echo "🔍 运行系统预检查..."
python3 -c "
import asyncio
from news_spider import collect_realtime_news

async def test():
    try:
        news = await collect_realtime_news()
        print(f'✅ 新闻爬虫测试成功，获取到 {len(news)} 条新闻')
        return True
    except Exception as e:
        print(f'⚠️  新闻爬虫测试失败: {e}')
        return False

result = asyncio.run(test())
exit(0 if result else 1)
"

if [[ $? -eq 0 ]]; then
    echo "✅ 系统预检查通过"
else
    echo "⚠️  系统预检查未完全通过，但仍可启动"
fi

# 启动服务
echo ""
echo "🚀 启动AI智能新闻聚合平台..."
echo "=================================="
echo "📱 Web界面: http://localhost:8000"
echo "📖 API文档: http://localhost:8000/api/docs"
echo "📊 系统状态: http://localhost:8000/api/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动FastAPI应用
python3 -m uvicorn web_app:app --host 0.0.0.0 --port 8000 --reload