#!/usr/bin/env python3
"""
SaleSmartly Assign Session

API ID: 323506414e0
Endpoint: /api/v2/assign-session
Method: POST

@safety: confirm
@retryable: true
@category: session
@operation: update
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="会话分配接口")
    parser.add_argument("--session-id", type=str, required=True, help="会话 ID")
    parser.add_argument("--chat-user-id", type=str, required=True, help="访客 ID")
    parser.add_argument("--sys-user-id", type=str, default="-1", help="当前接待客服 ID")
    parser.add_argument("--assign-sys-user-id", type=str, required=True, help="即将接待客服 ID (sys_user_id)")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        data = client.post(
            "/api/v2/assign-chat-user",
            {
                "session_id": args.session_id,
                "chat_user_id": args.chat_user_id,
                "sys_user_id": args.sys_user_id,
                "assign_sys_user_id": args.assign_sys_user_id,
            },
        )

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ 会话分配成功！")
        print(f"{'='*60}")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}: {format_timestamp(value) if isinstance(value, int) and value > 1_000_000_000 else value}")
        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
