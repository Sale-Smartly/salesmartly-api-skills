#!/usr/bin/env python3
"""
SaleSmartly Batch Tags

API ID: 296178103e0
Endpoint: /api/v2/batch-update-label
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

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="批量标签操作")
    parser.add_argument("--ids", type=str, required=True, help="客户 chat_user_id 列表（逗号分隔，最多 10 个）")
    parser.add_argument("--update-label-names", type=str, required=True, help="标签名列表（逗号分隔，最多 10 个）")
    parser.add_argument("--update-type", type=str, default="append", choices=["append", "remove", "update"], help="操作类型：append=追加, remove=移除, update=覆盖")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        data = client.post(
            "/api/v2/batch-update-label",
            {
                "ids": args.ids,
                "update_label_names": args.update_label_names,
                "update_type": args.update_type,
            },
        )

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ 批量标签操作成功！")
        print(f"{'='*60}")
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"{k}: {v}")
        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
