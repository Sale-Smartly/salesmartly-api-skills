#!/usr/bin/env python3
"""
SaleSmartly Member Query

API ID: 310397215e0
Endpoint: /api/v2/get-member-list
Method: GET

@safety: safe
@retryable: true
@category: team
@operation: query
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="SaleSmartly 团队成员查询工具")
    parser.add_argument("--page", type=int, default=1, help="页码（从 1 开始）")
    parser.add_argument("--page-size", type=int, default=100, help="每页大小（最大 100）")
    parser.add_argument("--all", action="store_true", help="自动获取所有页面数据")
    parser.add_argument(
        "--status",
        type=str,
        choices=["active", "inactive", "all"],
        default=None,
        help="状态过滤：active=活跃，inactive=非活跃，all=全部",
    )
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        params = {}
        if args.status and args.status != "all":
            params["status"] = "1" if args.status == "active" else "0"

        data = client.get(
            "/api/v2/get-member-list",
            {"page": args.page, "page_size": args.page_size, **params},
        )
        members = data.get("list", [])
        total = data.get("total", 0)

        if json_mode:
            print_result(True, data=members, meta={"total": total, "page": args.page, "page_size": args.page_size}, json_mode=True)
            return

        # 人类可读输出
        print(f"\n{'='*60}")
        print(f"✅ 团队成员查询成功！")
        print(f"{'='*60}")
        print(f"总数：{total}")
        print(f"当前页：{args.page}")
        print(f"返回：{len(members)} 条")

        if members:
            print(f"\n成员列表:")
            for i, m in enumerate(members, 1):
                name = m.get("nickname", m.get("member_name", m.get("name", "N/A")))
                print(f"\n[{i}] {name}")
                print(f"    客服 ID (sys_user_id): {m.get('sys_user_id', 'N/A')}")
                print(f"    成员 ID (id): {m.get('id', 'N/A')}")
                if m.get("email"):
                    print(f"    邮箱：{m['email']}")
                if m.get("mobile") or m.get("phone"):
                    print(f"    手机：{m.get('mobile', m.get('phone'))}")
                status_val = m.get("status")
                print(f"    状态：{'活跃' if str(status_val) == '1' else '非活跃'}")
                role = m.get("role") or m.get("role_id")
                if role:
                    role_map = {"1": "管理员", "2": "普通成员", "3": "访客"}
                    print(f"    角色：{role_map.get(str(role), str(role))}")
                if m.get("last_login_time"):
                    print(f"    最后登录：{format_timestamp(m['last_login_time'])}")
                created = m.get("created_time") or m.get("add_time")
                if created:
                    print(f"    加入时间：{format_timestamp(created)}")
        else:
            print(f"\n⚠️  未找到成员")

        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
