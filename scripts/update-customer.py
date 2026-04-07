#!/usr/bin/env python3
"""
SaleSmartly Update Customer

API ID: 296183457e0
Endpoint: /api/v2/update-user-info
Method: POST

@safety: confirm
@retryable: true
@category: customer
@operation: update
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="更新客户信息")
    parser.add_argument("--chat-user-id", type=str, required=True, help="客户 ID")
    parser.add_argument("--remark", type=str, default=None, help="客户备注")
    parser.add_argument("--remark-name", type=str, default=None, help="客户备注名")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        params = {"chat_user_id": args.chat_user_id}
        if args.remark is not None:
            params["remark"] = args.remark
        if args.remark_name is not None:
            params["remark_name"] = args.remark_name

        data = client.post("/api/v2/update-user-info", params)

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ 客户信息更新成功！")
        print(f"{'='*60}")
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"{k}: {format_timestamp(v) if isinstance(v, int) and v > 1_000_000_000 else v}")
        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
