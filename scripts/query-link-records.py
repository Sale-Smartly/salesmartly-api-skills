#!/usr/bin/env python3
"""
SaleSmartly Get Link Records

API ID: 326351442e0
Endpoint: /api/v2/get-link-record-list
Method: GET

@safety: safe
@retryable: true
@category: marketing
@operation: query
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="查询分流链接记录")
    parser.add_argument("--page", type=int, default=1, help="页码（从 1 开始）")
    parser.add_argument("--page-size", type=int, default=100, help="每页大小（最大 100）")
    parser.add_argument("--all", action="store_true", help="自动获取所有页面数据")
    parser.add_argument("--link-url", type=str, default=None, help="链接 URL 过滤")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        params = {}
        if args.link_url:
            params["link_url"] = args.link_url

        if getattr(args, "all"):
            items, total = client.get_all_pages("/api/v2/get-link-record-list", params, page_size=args.page_size)
        else:
            data = client.get("/api/v2/get-link-record-list", {"page": args.page, "page_size": args.page_size, **params})
            items = data.get("list", [])
            total = data.get("total", 0)

        if json_mode:
            print_result(True, data=items, meta={"total": total}, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ 链接记录查询成功！")
        print(f"{'='*60}")
        print(f"总数：{total}")
        print(f"返回：{len(items)} 条")

        if items:
            for i, r in enumerate(items, 1):
                print(f"\n[{i}]")
                for k, v in r.items():
                    if isinstance(v, int) and v > 1_000_000_000:
                        print(f"    {k}: {format_timestamp(v)}")
                    else:
                        print(f"    {k}: {v}")
        else:
            print(f"\n⚠️  未找到记录")

        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
