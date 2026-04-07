#!/usr/bin/env python3
"""
SaleSmartly Customer Query

API ID: 258167563e0
Endpoint: /api/v2/get-contact-list
Method: GET

Usage:
    uv run scripts/query-customers.py --page 1 --page-size 5
    uv run scripts/query-customers.py --filter-by created --days 60

@safety: safe
@retryable: true
@category: customer
@operation: query
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


def query_customer_by_id(client: "SaleSmartlyClient", chat_user_id: str):
    """通过遍历客户列表查找单个客户"""
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=365)).timestamp())
    updated_time_str = json.dumps({"start": start_time, "end": end_time})

    items, _ = client.get_all_pages(
        "/api/v2/get-contact-list",
        {"updated_time": updated_time_str},
        max_pages=20,
    )
    for c in items:
        if str(c.get("chat_user_id")) == str(chat_user_id):
            return c
    return None


def main():
    parser = argparse.ArgumentParser(description="SaleSmartly ��户查询工具")
    parser.add_argument("--page", type=int, default=1, help="页码（从 1 开���）")
    parser.add_argument("--page-size", type=int, default=100, help="每页大小（最大 100）")
    parser.add_argument("--days", type=int, default=30, help="查询最近 N 天的数据")
    parser.add_argument(
        "--filter-by",
        type=str,
        choices=["updated", "created"],
        default="updated",
        help="过滤方式：updated=按更新时间，created=按创建时���",
    )
    parser.add_argument("--all", action="store_true", help="自动获取所有页面数据")
    parser.add_argument("--chat-user-id", type=str, help="客户 ID（指定时查询单个客户）")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        # 单个客户查询
        if args.chat_user_id:
            customer = query_customer_by_id(client, args.chat_user_id)
            if not customer:
                print_result(False, error_msg=f"未找到客户：{args.chat_user_id}", json_mode=json_mode)
                sys.exit(1)
            if json_mode:
                print_result(True, data=customer, json_mode=True)
                return
            print(f"\n{'='*60}")
            print(f"✅ 找到客户！")
            print(f"{'='*60}\n")
            print(f"姓名：{customer.get('name', 'N/A')}")
            print(f"客户 ID: {customer.get('chat_user_id', 'N/A')}")
            for field, label in [("email", "邮箱"), ("phone", "电话"), ("country", "国家"), ("city", "城市")]:
                if customer.get(field):
                    print(f"{label}：{customer[field]}")
            if customer.get("created_time"):
                print(f"创建时间：{format_timestamp(customer['created_time'])}")
            print(f"\n{'='*60}")
            return

        # 列表查询
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=args.days)).timestamp())
        updated_time_str = json.dumps({"start": start_time, "end": end_time})

        if not json_mode:
            print(f"\n📊 查询范围：{datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')} 至 {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')}")
            print(f"过滤方式：{'创建时间' if args.filter_by == 'created' else '更新时间'}\n")

        if args.filter_by == "created" or getattr(args, "all"):
            # 需要获取所有页再客户端过滤
            if not json_mode:
                print("正在获取所有客户数据...")
            all_customers, _ = client.get_all_pages(
                "/api/v2/get-contact-list",
                {"updated_time": updated_time_str},
            )

            # 去重
            seen = set()
            unique = []
            for c in all_customers:
                uid = c.get("chat_user_id")
                if uid not in seen:
                    seen.add(uid)
                    unique.append(c)

            if args.filter_by == "created":
                customers = [c for c in unique if c.get("created_time", 0) >= start_time]
                customers.sort(key=lambda x: x.get("created_time", 0))
            else:
                customers = unique

            total = len(customers)
            # 客户端分页
            start_idx = (args.page - 1) * args.page_size
            display = customers[start_idx : start_idx + args.page_size]
        else:
            # 单页查询
            data = client.get(
                "/api/v2/get-contact-list",
                {
                    "updated_time": updated_time_str,
                    "page": args.page,
                    "page_size": args.page_size,
                },
            )
            display = data.get("list", [])
            total = data.get("total", 0)

        if json_mode:
            print_result(True, data=display, meta={"total": total, "page": args.page, "page_size": args.page_size}, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"��� 客户查询��功！")
        print(f"{'='*60}")
        print(f"总��：{total}")
        print(f"当前页��{args.page}")
        print(f"每页：{args.page_size}")
        print(f"返回��{len(display)} 条")

        if display:
            print(f"\n客户列表:")
            for i, c in enumerate(display, 1):
                print(f"\n[{i}] {c.get('name', 'N/A')}")
                print(f"    ID: {c.get('chat_user_id', 'N/A')}")
                for field, label in [("email", "邮箱"), ("phone", "电话"), ("country", "国家"), ("city", "城市")]:
                    if c.get(field):
                        print(f"    {label}：{c[field]}")
                if c.get("created_time"):
                    print(f"    创建：{format_timestamp(c['created_time'])}")
        else:
            print(f"\n⚠️  未找到客户")

        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
