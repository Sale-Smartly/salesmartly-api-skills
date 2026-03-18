#!/usr/bin/env python3
"""
示例脚本 - 演示如何使用 SaleSmartly API 脚本

运行此脚本查看可用功能演示
"""

import json
import os
from pathlib import Path

# 检查 API 配置
def check_setup():
    """检查环境配置"""
    print("🔍 检查环境配置")
    print("=" * 50)
    
    # 检查 api-key.json
    api_key_file = Path("api-key.json")
    if api_key_file.exists():
        print("✅ api-key.json 存在")
        with open(api_key_file, 'r') as f:
            config = json.load(f)
            if config.get("apiKey") and config.get("projectId"):
                print("✅ API Key 和 Project ID 已配置")
            else:
                print("❌ API Key 或 Project ID 缺失")
    else:
        print("❌ api-key.json 不存在")
        print("   请复制 api-key.json.example 并填入你的 API Key")
    
    print()
    
    # 检查脚本文件
    scripts_dir = Path("scripts")
    if scripts_dir.exists():
        script_count = len(list(scripts_dir.glob("*.py")))
        print(f"✅ 发现 {script_count} 个脚本")
    else:
        print("❌ scripts 目录不存在")
    
    print()
    
    # 检查依赖
    try:
        import requests
        print(f"✅ requests 已安装 (v{requests.__version__})")
    except ImportError:
        print("❌ requests 未安装")
        print("   运行：pip install -r requirements.txt")
    
    print()

# 显示快速入门
def show_quickstart():
    """显示快速入门指南"""
    print("🚀 快速入门")
    print("=" * 50)
    print("""
1. 配置 API Key
   cat > api-key.json << 'EOF'
   {
     "apiKey": "your_api_key",
     "projectId": "your_project_id"
   }
   EOF

2. 测试查询客户
   uv run scripts/query-customers.py --page 1 --page-size 5

3. 查看帮助
   uv run scripts/query-customers.py --help

常用命令:
  - 查询客户：uv run scripts/query-customers.py --days 7
  - 查询成员：uv run scripts/query-members.py
  - 查询消息：uv run scripts/query-messages.py --chat-user-id <ID>
  - WhatsApp 设备：uv run scripts/query-whatsapp-apps.py
    """)

# 显示所有可用脚本
def list_scripts():
    """列出所有可用脚本"""
    print("📋 可用脚本")
    print("=" * 50)
    
    scripts_dir = Path("scripts")
    if not scripts_dir.exists():
        print("scripts 目录不存在")
        return
    
    scripts = sorted([f.name for f in scripts_dir.glob("*.py") if not f.name.startswith('_')])
    
    for script in scripts:
        print(f"  - {script}")
    
    print(f"\n共 {len(scripts)} 个脚本")

if __name__ == "__main__":
    print("\n🤖 SaleSmartly AI Skill - 示例脚本\n")
    
    check_setup()
    show_quickstart()
    list_scripts()
    
    print("\n" + "=" * 50)
    print("💡 提示：配置 API Key 后即可开始使用！\n")
