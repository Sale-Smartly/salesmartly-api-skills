#!/usr/bin/env python3
"""
SaleSmartly Create Customer

API ID: 276530997e0
Endpoint: /api/v2/add-contact
Method: POST

@safety: confirm
@retryable: true
@category: customer
@operation: create
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="新增客户")
    parser.add_argument("--channel", type=str, default="12", choices=["7", "12"], help="渠道 (7=Email, 12=WhatsApp App)")
    parser.add_argument("--from-channel-info", type=str, default=None, help="渠道信息")
    parser.add_argument("--phone", type=str, required=True, help="客户手机号（带区号，如 8613800138000）")
    parser.add_argument("--remark-name", type=str, default=None, help="客户备注名")
    parser.add_argument("--remark", type=str, default=None, help="客户备注")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        params = {"channel": args.channel, "phone": args.phone}
        if args.from_channel_info:
            params["from_channel_info"] = args.from_channel_info
        if args.remark_name:
            params["remark_name"] = args.remark_name
        if args.remark:
            params["remark"] = args.remark

        data = client.post("/api/v2/add-contact", params)

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ 客户创建成功！")
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
