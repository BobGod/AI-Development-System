#!/usr/bin/env python3
"""
🚀 快速启动脚本 - AI智能新闻聚合平台
"""

import subprocess
import sys
import os
import time

def check_port(port):
    """检查端口是否可用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except:
            return False

def main():
    print("🚀 启动AI智能新闻聚合平台")
    print("=" * 50)
    
    # 检查端口
    if not check_port(8000):
        print("❌ 端口8000被占用，正在尝试清理...")
        try:
            subprocess.run(["pkill", "-f", "web_app"], check=False)
            time.sleep(2)
        except:
            pass
    
    # 激活虚拟环境并启动
    venv_python = "venv/bin/python"
    if not os.path.exists(venv_python):
        print("❌ 虚拟环境不存在，请先运行: python3 -m venv venv && source venv/bin/activate && pip install fastapi uvicorn requests aiohttp")
        return
    
    print("🔄 启动服务中...")
    
    try:
        # 使用虚拟环境的python启动
        cmd = [venv_python, "web_app.py"]
        process = subprocess.Popen(cmd, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True,
                                 bufsize=1)
        
        print("✅ 服务正在启动...")
        print("🌐 访问地址: http://localhost:8000")
        print("📚 API文档: http://localhost:8000/api/docs")
        print("💡 按 Ctrl+C 停止服务")
        print("-" * 50)
        
        # 实时显示输出
        for line in process.stdout:
            print(line.strip())
            
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        process.terminate()
        print("✅ 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    main()