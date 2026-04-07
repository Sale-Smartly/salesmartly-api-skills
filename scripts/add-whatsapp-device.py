#!/usr/bin/env python3
"""
SaleSmartly Add WhatsApp Device

API ID: 334587546e0
Endpoint: /api/v2/purchase-individual-whatsapp-app
Method: POST

@safety: confirm
@retryable: true
@category: whatsapp
@operation: create
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="添加 WhatsApp 设备")
    parser.add_argument("--country", type=str, default="us", help="国家代码")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        data = client.post("/api/v2/purchase-individual-whatsapp-app", {"country": args.country})

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ WhatsApp 设备添加成功！")
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
