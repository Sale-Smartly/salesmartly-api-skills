#!/usr/bin/env python3
"""
每日销售报告 - 生成当日销售活动总结

功能:
- 新增客户统计
- 客户总量统计
- 团队成员活跃度
- WhatsApp 设备状态

使用:
uv run scripts/daily-sales-report.py --date 2026-03-11
uv run scripts/daily-sales-report.py --days 7  # 最近 7 天
"""

import json
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path

# 加载 API 配置
SCRIPT_DIR = Path(__file__).parent
API_CONFIG = SCRIPT_DIR / "api-key.json"

if not API_CONFIG.exists():
    print("❌ 错误：api-key.json 不存在")
    print("请先配置 API Key")
    sys.exit(1)

with open(API_CONFIG, 'r') as f:
    config = json.load(f)

API_KEY = config.get("apiKey")
PROJECT_ID = config.get("projectId")
BASE_URL = "https://developer.salesmartly.com"

def get_sign(params):
    """生成 API 签名"""
    import hashlib
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [API_KEY]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()

def api_request(endpoint, params=None):
    """发送 API 请求"""
    if params is None:
        params = {}
    
    params["project_id"] = PROJECT_ID
    params["sign"] = get_sign(params)
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API 请求失败：{e}")
        return None

def get_customer_count(days=1):
    """获取客户数量统计"""
    # 计算时间范围
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    params = {
        "page": "1",
        "page_size": "1",
        "updated_time": str(int(start_time.timestamp()))
    }
    
    result = api_request("/api/v2/get-contact-list", params)
    if result and result.get("code") == 0:
        return result.get("data", {}).get("total", 0)
    return 0

def get_member_list():
    """获取团队成员列表"""
    params = {
        "page": "1",
        "page_size": "100"
    }
    
    result = api_request("/api/v2/get-member-list", params)
    if result and result.get("code") == 0:
        return result.get("data", {}).get("member_list", [])
    return []

def get_whatsapp_devices():
    """获取 WhatsApp 设备列表"""
    params = {
        "page": "1",
        "page_size": "100"
    }
    
    result = api_request("/api/v2/get-individual-whatsapp-list", params)
    if result and result.get("code") == 0:
        return result.get("data", {}).get("list", [])
    return []

def generate_report(days=1):
    """生成销售报告"""
    print("\n" + "=" * 60)
    print("📊 SalesSmartly 销售报告")
    print("=" * 60)
    
    if days == 1:
        print(f"📅 报告日期：{datetime.now().strftime('%Y-%m-%d')}")
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        print(f"📅 报告周期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    print("-" * 60)
    
    # 客户统计
    customer_count = get_customer_count(days)
    print(f"\n👥 客户统计")
    print(f"   新增客户数：{customer_count} 个")
    
    # 团队成员
    members = get_member_list()
    print(f"\n👔 团队成员")
    print(f"   总人数：{len(members)} 人")
    
    online_count = sum(1 for m in members if m.get("status") == 1)
    print(f"   在线人数：{online_count} 人")
    
    if members:
        print(f"\n   成员列表:")
        for member in members[:5]:  # 显示前 5 个
            name = member.get("name", "未知")
            email = member.get("email", "")
            status = "🟢 在线" if member.get("status") == 1 else "🔴 离线"
            print(f"   - {name} ({email}) {status}")
        if len(members) > 5:
            print(f"   ... 还有 {len(members) - 5} 人")
    
    # WhatsApp 设备
    devices = get_whatsapp_devices()
    print(f"\n📱 WhatsApp 设备")
    print(f"   总设备数：{len(devices)} 个")
    
    if devices:
        online_devices = sum(1 for d in devices if d.get("status") == 1)
        print(f"   在线设备：{online_devices} 个")
        print(f"   离线设备：{len(devices) - online_devices} 个")
        
        print(f"\n   设备状态:")
        for device in devices[:5]:  # 显示前 5 个
            name = device.get("name", "未知")
            phone = device.get("phone", "")
            status = "🟢 在线" if device.get("status") == 1 else "🔴 离线"
            print(f"   - {name} ({phone}) {status}")
        if len(devices) > 5:
            print(f"   ... 还有 {len(devices) - 5} 个设备")
    
    print("\n" + "=" * 60)
    print("💡 提示：运行 'uv run scripts/customer-stats.py' 查看详细客户分析")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成每日销售报告")
    parser.add_argument("--date", type=str, help="指定日期 (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=1, help="最近 N 天")
    
    args = parser.parse_args()
    
    days = args.days
    if args.date:
        try:
            report_date = datetime.strptime(args.date, "%Y-%m-%d")
            days = (datetime.now() - report_date).days + 1
        except ValueError:
            print("❌ 日期格式错误，应为 YYYY-MM-DD")
            sys.exit(1)
    
    generate_report(days)
