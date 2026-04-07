#!/usr/bin/env python3
"""
SaleSmartly API 脚本更新检查器

检查 API 文档更新，对比现有脚本，生成更新报告

用法:
    uv run scripts/check-api-updates.py

@safety: safe
@retryable: true
@category: utility
@operation: query
"""
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError

import json
import urllib.request
import urllib.parse
import ssl
import re
from datetime import datetime

# 配置
APIFOX_BASE = "https://salesmartly-api.apifox.cn"
LLMS_URL = f"{APIFOX_BASE}/llms.txt"
SCRIPTS_DIR = Path(__file__).parent

# API ID 到脚本文件的映射
API_TO_SCRIPT = {
    '258167563e0': 'query-customers.py',       # 手写
    '276530997e0': 'create-customer.py',
    '296178103e0': 'batch-tags.py',
    '296183457e0': 'update-customer.py',
    '311462851e0': 'import-orders.py',
    '310397215e0': 'query-members.py',         # 手写
    '317790952e0': 'query-messages.py',        # 手写
    '385681563e0': 'query-all-messages.py',
    '323506414e0': 'assign-session.py',
    '339565482e0': 'end-session.py',
    '326349441e0': 'query-links.py',           # 手写
    '326351442e0': 'query-link-records.py',
    '326572731e0': 'query-whatsapp-apps.py',   # 手写
    '328937730e0': 'get-whatsapp-qrcode.py',
    '334587546e0': 'add-whatsapp-device.py',
    '334594569e0': 'set-whatsapp-proxy.py',
    '334595469e0': 'delete-whatsapp-device.py',
}


def fetch_llms() -> list:
    """获取最新 API 列表"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    try:
        req = urllib.request.Request(LLMS_URL, headers={"User-Agent": "SaleSmartly-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            content = response.read().decode('utf-8')
            return parse_llms(content)
    except Exception as e:
        print(f"❌ 获取 API 列表失败：{e}")
        sys.exit(1)


def parse_llms(content: str) -> list:
    """解析 llms.txt"""
    apis = []
    pattern = r'-\s*([^\[]+)\s*\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, content)

    for match in matches:
        category = match[0].strip()
        name = match[1].strip()
        url = match[2].strip()

        if 'Docs' in category or not url.endswith('.md'):
            continue

        api_id_match = re.search(r'(\w+e\d+)\.md', url)
        if api_id_match:
            api_id = api_id_match.group(1)
            apis.append({
                'category': category,
                'name': name,
                'api_id': api_id,
                'url': url
            })

    return apis


def check_script_exists(api_id: str) -> bool:
    """检查脚本是否存在"""
    if api_id in API_TO_SCRIPT:
        return SCRIPTS_DIR.joinpath(API_TO_SCRIPT[api_id]).exists()
    return False


def get_script_info(script_path: Path) -> dict:
    """获取脚本信息"""
    if not script_path.exists():
        return None

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 API ID
    api_id_match = re.search(r'API ID:\s*(\w+e\d+)', content)
    api_id = api_id_match.group(1) if api_id_match else 'unknown'

    # 提取 API 路径
    path_match = re.search(r'Endpoint:\s*(/[^\s]+)', content)
    path = path_match.group(1) if path_match else 'unknown'

    # 提取方法
    method_match = re.search(r'Method:\s*(GET|POST|PUT|DELETE)', content)
    method = method_match.group(1) if method_match else 'unknown'

    return {
        'api_id': api_id,
        'path': path,
        'method': method,
        'size': script_path.stat().st_size,
        'modified': datetime.fromtimestamp(script_path.stat().st_mtime)
    }


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly API 脚本更新检查器')
    add_output_args(parser)
    args = parser.parse_args()

    if not args.quiet and not args.json:
        print("=" * 70)
        print("📊 SaleSmartly API 脚本更新检查")
        print("=" * 70)
        print()

    # 获取最新 API 列表
    if not args.quiet and not args.json:
        print("📄 获取最新 API 列表...")
    apis = fetch_llms()
    if not args.quiet and not args.json:
        print(f"✅ 找到 {len(apis)} 个 API\n")

    # 分类统计
    implemented = []
    missing = []

    for api in apis:
        api_id = api['api_id']
        script_name = API_TO_SCRIPT.get(api_id)

        if script_name:
            script_path = SCRIPTS_DIR / script_name
            if script_path.exists():
                info = get_script_info(script_path)
                if info and info['api_id'] != 'unknown':
                    implemented.append({
                        'api': api,
                        'script': script_name,
                        'info': info
                    })
                else:
                    missing.append(api)
            else:
                missing.append(api)
        else:
            missing.append(api)

    # JSON 输出
    if args.json:
        print_result(True, data={
            'total_apis': len(apis),
            'implemented': len(implemented),
            'missing': len(missing),
            'implemented_list': [{'name': i['api']['name'], 'script': i['script']} for i in implemented],
            'missing_list': [{'name': m['name'], 'api_id': m['api_id']} for m in missing],
        }, json_mode=True)
        return

    # 显示结果
    print("=" * 70)
    print("📋 检查结果")
    print("=" * 70)
    print()

    # 已实现
    print(f"✅ 已实现：{len(implemented)}/{len(apis)}")
    for item in implemented:
        api = item['api']
        info = item['info']
        print(f"   • {api['category']} - {api['name']}")
        print(f"     脚本：{item['script']} ({info['size']} bytes)")
        print(f"     API: {info['path']} [{info['method']}]")
        print()

    # 缺失的
    if missing:
        print(f"⚠️  未实现：{len(missing)}")
        for api in missing:
            print(f"   • {api['category']} - {api['name']}")
            print(f"     API ID: {api['api_id']}")
            print(f"     命令：uv run scripts/generate-query-script.py --api-id {api['api_id']}")
            print()

    # 总结
    print("=" * 70)
    print("📊 总结")
    print("=" * 70)
    print(f"API 总数：{len(apis)}")
    print(f"已实现：{len(implemented)} ({len(implemented)*100//len(apis) if apis else 0}%)")
    print(f"未实现：{len(missing)}")
    print()

    if missing:
        print("💡 建议操作:")
        print(f"   1. 一键生成所有缺失脚本:")
        print(f"      uv run scripts/batch-generate-scripts.py")
        print()
        print(f"   2. 生成单个脚本:")
        print(f"      uv run scripts/generate-query-script.py --api-id <API_ID>")
        print()
    else:
        print("✅ 所有 API 脚本已实现！")

    print("=" * 70)


if __name__ == "__main__":
    main()
