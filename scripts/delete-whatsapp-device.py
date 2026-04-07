#!/usr/bin/env python3
"""
SaleSmartly Delete WhatsApp Device

API ID: 334595469e0
Endpoint: /api/v2/remove-individual-whatsapp-app
Method: POST

@safety: destructive
@retryable: false
@category: whatsapp
@operation: delete
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="删除 WhatsApp 设备")
    parser.add_argument("--id", type=int, required=True, help="WhatsApp 设备 ID")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        data = client.post("/api/v2/remove-individual-whatsapp-app", {"id": args.id})

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ WhatsApp 设备已删除！")
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
