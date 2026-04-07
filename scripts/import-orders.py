#!/usr/bin/env python3
"""
SaleSmartly Import Orders

API ID: 311462851e0
Endpoint: /api/v2/add-contact-order
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
    parser = argparse.ArgumentParser(description="导入订单")
    parser.add_argument("--chat-user-id", type=str, required=True, help="客户 ID")
    parser.add_argument("--order-id", type=str, required=True, help="订单 ID")
    parser.add_argument("--order-name", type=str, default="", help="订单名称")
    parser.add_argument("--money", type=str, default="0", help="金额")
    parser.add_argument("--currency-code", type=str, default="USD", help="货币类型")
    parser.add_argument("--status", type=str, default="1", choices=["1", "2", "3", "4"], help="状态 (1=待处理, 2=处理中, 3=已完成, 4=已取消)")
    parser.add_argument("--platform", type=str, default="other", help="平台")
    parser.add_argument("--remark", type=str, default="", help="备注")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        params = {
            "chat_user_id": args.chat_user_id,
            "order_id": args.order_id,
            "order_name": args.order_name,
            "money": args.money,
            "currency_code": args.currency_code,
            "status": args.status,
            "platform": args.platform,
            "remark": args.remark,
        }

        data = client.post("/api/v2/add-contact-order", params)

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ 订单导入成功！")
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
