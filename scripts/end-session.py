#!/usr/bin/env python3
"""
SaleSmartly End Session

API ID: 339565482e0
Endpoint: /api/v2/end-session
Method: POST

@safety: destructive
@retryable: false
@category: session
@operation: delete
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="结束会话")
    parser.add_argument("--session-id", type=str, required=True, help="会话 ID")
    parser.add_argument("--chat-user-id", type=str, required=True, help="访客 ID")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        data = client.post(
            "/api/v2/end-session",
            {
                "session_id": args.session_id,
                "chat_user_id": args.chat_user_id,
            },
        )

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ 会话已结束！")
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
