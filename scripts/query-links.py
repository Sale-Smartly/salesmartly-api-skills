#!/usr/bin/env python3
"""
SaleSmartly Link Query

API ID: 326349441e0
Endpoint: /api/v2/get-link-list
Method: GET

Usage:
    uv run scripts/query-links.py --page 1 --page-size 20
    uv run scripts/query-links.py --days 7
    uv run scripts/query-links.py --all --json

@safety: safe
@retryable: true
@category: marketing
@operation: query
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


ENDPOINT = "/api/v2/get-link-list"


def main():
    parser = argparse.ArgumentParser(description="SaleSmartly 分流链接查询工具")
    parser.add_argument("--page", type=int, default=1, help="页码（从 1 开始）")
    parser.add_argument("--page-size", type=int, default=100, help="每页大小（最大 100）")
    parser.add_argument("--all", action="store_true", help="自动获取所有页面数据（当 total > page_size 时）")
    parser.add_argument("--days", type=int, default=None, help="查询最近 N 天创建的链接")
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

        # 时间范围过滤
        if args.days:
            end_time = int(datetime.now().timestamp())
            start_time = int((datetime.now() - timedelta(days=args.days)).timestamp())
            params["created_time"] = json.dumps({"start": start_time, "end": end_time})

        if not json_mode:
            print(f"📊 查询分流链接列表")
            if args.days:
                print(f"时间范围：最近 {args.days} 天")
            print()

        if args.all:
            links, total = client.get_all_pages(ENDPOINT, params)
        else:
            data = client.get(ENDPOINT, params)
            links = data.get("list", [])
            total = data.get("total", 0)

        if json_mode:
            print_result(True, data=links, meta={"total": total, "page": args.page, "page_size": args.page_size}, json_mode=True)
            return

        # 显示结果
        print(f"\n{'='*60}")
        print(f"✅ 分流链接查询成功！")
        print(f"{'='*60}")
        print(f"总数：{total}")
        print(f"当前页：{args.page}")
        print(f"每页：{args.page_size}")
        print(f"返回：{len(links)} 条")

        if links:
            print(f"\n链接列表:")
            for i, link in enumerate(links, 1):
                print(f"\n[{i}] 链接 ID: {link.get('id', 'N/A')}")

                # 链接名称
                if link.get("name"):
                    print(f"    名称：{link.get('name')}")

                # 链接 URL
                if link.get("link"):
                    print(f"    URL: {link.get('link')}")

                # 创建时间
                created_time = link.get("created_time")
                if created_time:
                    print(f"    创建时间：{format_timestamp(created_time)}")

                # 更新时间
                updated_time = link.get("updated_time")
                if updated_time:
                    print(f"    更新时间：{format_timestamp(updated_time)}")

                # 使用次数
                if link.get("use_count") is not None:
                    print(f"    使用次数：{link.get('use_count')}")

                # 状态
                if link.get("status") is not None:
                    status_map = {
                        0: "未激活",
                        1: "启用",
                        2: "禁用",
                    }
                    print(f"    状态：{status_map.get(link.get('status'), str(link.get('status')))}")
        else:
            print(f"\n⚠️  未找到分流链接")

        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
