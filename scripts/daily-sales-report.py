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
    uv run scripts/daily-sales-report.py --days 7

@safety: safe
@retryable: true
@category: analytics
@operation: query
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, ConfigError, APIError, NetworkError


def generate_report(client: SaleSmartlyClient, days: int = 1, json_mode: bool = False):
    """生成销售报告"""
    # 客户统计
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())
    updated_time_str = json.dumps({"start": start_time, "end": end_time}, separators=(",", ":"))

    customer_data = client.get("/api/v2/get-contact-list", {"page": 1, "page_size": 1, "updated_time": updated_time_str})
    customer_count = customer_data.get("total", 0)

    # 团队成员
    member_data = client.get("/api/v2/get-member-list", {"page": 1, "page_size": 100})
    members = member_data.get("member_list", member_data.get("list", []))

    # WhatsApp 设备
    device_data = client.get("/api/v2/get-individual-whatsapp-list", {"page": 1, "page_size": 100})
    devices = device_data.get("list", [])

    if json_mode:
        report = {
            "period_days": days,
            "customer_count": customer_count,
            "team": {
                "total": len(members),
                "online": sum(1 for m in members if m.get("status") == 1),
            },
            "whatsapp": {
                "total": len(devices),
                "online": sum(1 for d in devices if d.get("status") == 1),
            },
        }
        print_result(True, data=report, json_mode=True)
        return

    # 人类可读输出
    print("\n" + "=" * 60)
    print("📊 SaleSmartly 销售报告")
    print("=" * 60)

    if days == 1:
        print(f"📅 报告日期：{datetime.now().strftime('%Y-%m-%d')}")
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        print(f"📅 报告周期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")

    print("-" * 60)

    print(f"\n👥 客户统计")
    print(f"   新增客户数：{customer_count} 个")

    online_count = sum(1 for m in members if m.get("status") == 1)
    print(f"\n👔 团队成员")
    print(f"   总人数：{len(members)} 人")
    print(f"   在���人数：{online_count} 人")

    if members:
        print(f"\n   成员列表:")
        for member in members[:5]:
            name = member.get("name", "未知")
            email = member.get("email", "")
            status = "🟢 ��线" if member.get("status") == 1 else "🔴 离线"
            print(f"   - {name} ({email}) {status}")
        if len(members) > 5:
            print(f"   ... 还有 {len(members) - 5} 人")

    print(f"\n📱 WhatsApp 设备")
    print(f"   总设备数：{len(devices)} 个")

    if devices:
        online_devices = sum(1 for d in devices if d.get("status") == 1)
        print(f"   在线设备：{online_devices} 个")
        print(f"   离线设备：{len(devices) - online_devices} 个")
        print(f"\n   设备状态:")
        for device in devices[:5]:
            name = device.get("name", "未知")
            phone = device.get("phone", "")
            status = "🟢 在线" if device.get("status") == 1 else "🔴 离线"
            print(f"   - {name} ({phone}) {status}")
        if len(devices) > 5:
            print(f"   ... 还有 {len(devices) - 5} 个设备")

    print("\n" + "=" * 60)
    print("💡 提示：运行 'uv run scripts/customer-stats.py' 查看详细客户分析")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="生成每日销售报告")
    parser.add_argument("--date", type=str, help="指定日期 (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=1, help="最近 N 天")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    days = args.days
    if args.date:
        try:
            report_date = datetime.strptime(args.date, "%Y-%m-%d")
            days = (datetime.now() - report_date).days + 1
        except ValueError:
            print_result(False, error_msg="日期格式错误，应为 YYYY-MM-DD", json_mode=json_mode)
            sys.exit(1)

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)
        generate_report(client, days, json_mode)
    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
