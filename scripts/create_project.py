#!/usr/bin/env python3
"""
AI开发系统 - 创建新项目脚本
快速创建新的AI开发项目
"""

import sys
import os
from pathlib import Path

# 添加系统路径
sys.path.append(str(Path(__file__).parent.parent))

from tools.project_manager import ProjectManager
from project_isolation import ProjectType

def main():
    print("🤖 AI开发系统 - 项目创建向导")
    print("=" * 50)
    
    # 获取系统根目录
    system_root = os.environ.get('AI_DEV_SYSTEM_ROOT', '.')
    pm = ProjectManager(system_root)
    
    try:
        # 收集项目信息
        print("\n📝 请输入项目信息：")
        
        project_name = input("项目名称: ").strip()
        if not project_name:
            print("❌ 项目名称不能为空")
            return
            
        print("\n📋 可用的项目类型：")
        for i, proj_type in enumerate(ProjectType, 1):
            print(f"  {i}. {proj_type.value}")
            
        type_choice = input("\n选择项目类型 (输入数字): ").strip()
        try:
            type_index = int(type_choice) - 1
            project_types = list(ProjectType)
            if 0 <= type_index < len(project_types):
                project_type = project_types[type_index].value
            else:
                raise ValueError("无效选择")
        except (ValueError, IndexError):
            print("❌ 无效的项目类型选择")
            return
            
        description = input("项目描述 (可选): ").strip()
        owner = input("项目负责人 (默认: system): ").strip() or "system"
        
        # 技术栈
        print("\n🔧 技术栈 (用逗号分隔，可选):")
        tech_stack_input = input("技术栈: ").strip()
        tech_stack = [t.strip() for t in tech_stack_input.split(",") if t.strip()] if tech_stack_input else None
        
        # 项目模板
        print("\n📄 可用模板：")
        templates = ["web-app", "api-service", "mobile-app", "data-platform", "无模板"]
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template}")
            
        template_choice = input("选择模板 (输入数字，默认: 5): ").strip() or "5"
        try:
            template_index = int(template_choice) - 1
            if 0 <= template_index < len(templates) - 1:
                template = templates[template_index]
            else:
                template = None
        except ValueError:
            template = None
            
        print("\n🚀 正在创建项目...")
        
        # 创建项目
        result = pm.create_project(
            project_name=project_name,
            project_type=project_type,
            description=description,
            owner=owner,
            tech_stack=tech_stack,
            template=template
        )
        
        if result['success']:
            print(f"\n✅ {result['message']}")
            print(f"📁 项目路径: {result['project_path']}")
            print(f"🆔 项目ID: {result['project_id']}")
            
            # 询问是否切换到新项目
            switch = input("\n是否切换到新项目？ (y/N): ").strip().lower()
            if switch in ['y', 'yes']:
                switch_result = pm.switch_project(result['project_id'])
                if switch_result['success']:
                    print(f"✅ 已切换到项目: {result['project_id']}")
                else:
                    print(f"❌ 切换失败: {switch_result['message']}")
                    
        else:
            print(f"\n❌ 项目创建失败: {result['message']}")
            if 'error' in result:
                print(f"错误详情: {result['error']}")
                
    except KeyboardInterrupt:
        print("\n\n👋 项目创建已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

if __name__ == '__main__':
    main()