#!/usr/bin/env python3
"""
SaleSmartly WhatsApp Device Query

API ID: 326572731e0
Endpoint: /api/v2/get-individual-whatsapp-list
Method: GET

Usage:
    uv run scripts/query-whatsapp-apps.py --page 1 --page-size 20
    uv run scripts/query-whatsapp-apps.py --status 1
    uv run scripts/query-whatsapp-apps.py --all --json

@safety: safe
@retryable: true
@category: whatsapp
@operation: query
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


ENDPOINT = "/api/v2/get-individual-whatsapp-list"


def main():
    parser = argparse.ArgumentParser(description="SaleSmartly WhatsApp APP 查询工具")
    parser.add_argument("--page", type=int, default=1, help="页码（从 1 开始）")
    parser.add_argument("--page-size", type=int, default=100, help="每页大小（最大 100）")
    parser.add_argument("--all", action="store_true", help="自动获取所有页面数据（当 total > page_size 时）")

    parser.add_argument("--status", type=int, choices=[0, 1, 2], default=None,
                        help="设备状态：0-未连接 1-有效 2-无效")
    parser.add_argument("--name", type=str, default=None, help="WhatsApp app 名称")
    parser.add_argument("--phone-number", type=str, default=None, help="手机号码")
    parser.add_argument("--remark", type=str, default=None, help="备注")
    parser.add_argument("--id", type=str, default=None, help="云设备 id")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        # 构建请求参数
        params = {
            "page": str(args.page),
            "page_size": str(args.page_size),
        }

        # 可选过滤参数
        if args.status is not None:
            params["status"] = str(args.status)
        if args.name:
            params["name"] = args.name
        if args.phone_number:
            params["phone_number"] = args.phone_number
        if args.remark:
            params["remark"] = args.remark
        if args.id:
            params["id"] = args.id

        if not json_mode:
            print(f"📊 查询 WhatsApp APP 列表")
            if args.status is not None:
                status_map = {0: "未连接", 1: "有效", 2: "无效"}
                print(f"状态过滤：{status_map.get(args.status, str(args.status))}")
            if args.name:
                print(f"名称过滤：{args.name}")
            if args.phone_number:
                print(f"手机号过滤：{args.phone_number}")
            if args.remark:
                print(f"备注过滤：{args.remark}")
            if args.id:
                print(f"设备 ID 过滤：{args.id}")
            print()

        if args.all:
            apps, total = client.get_all_pages(ENDPOINT, params)
        else:
            data = client.get(ENDPOINT, params)
            apps = data.get("list", [])
            total = data.get("total", 0)

        if json_mode:
            print_result(True, data=apps, meta={"total": total, "page": args.page, "page_size": args.page_size}, json_mode=True)
            return

        # 显示结果
        print(f"\n{'='*60}")
        print(f"✅ WhatsApp APP 查询成功！")
        print(f"{'='*60}")
        print(f"总数：{total}")
        print(f"当前页：{args.page}")
        print(f"每页：{args.page_size}")
        print(f"返回：{len(apps)} 条")

        if apps:
            print(f"\n设备列表:")
            for i, app in enumerate(apps, 1):
                print(f"\n[{i}] 设备 ID: {app.get('id', 'N/A')}")

                # 设备名称
                if app.get("name"):
                    print(f"    名称：{app.get('name')}")

                # 手机号码
                if app.get("phone_number"):
                    print(f"    手机号：{app.get('phone_number')}")

                # 备注
                if app.get("remark"):
                    print(f"    备注：{app.get('remark')}")

                # 状态
                app_status = app.get("status")
                status_map = {0: "未连接", 1: "有效", 2: "无效"}
                print(f"    状态：{status_map.get(app_status, str(app_status))}")

                # 创建时间
                created_time = app.get("created_time")
                if created_time:
                    print(f"    创建时间：{format_timestamp(created_time)}")

                # 更新时间
                updated_time = app.get("updated_time")
                if updated_time:
                    print(f"    更新时间：{format_timestamp(updated_time)}")

                # 创建设备的成员 ID
                if app.get("sys_user_id"):
                    print(f"    创建成员 ID: {app.get('sys_user_id')}")
        else:
            print(f"\n⚠️  未找到 WhatsApp 设备")

        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
