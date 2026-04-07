#!/usr/bin/env python3
"""
SaleSmartly Set WhatsApp Proxy

API ID: 334594569e0
Endpoint: /api/v2/set-individual-whatsapp-app-proxy
Method: POST

@safety: confirm
@retryable: true
@category: whatsapp
@operation: update
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, ConfigError, APIError, NetworkError


def main():
    parser = argparse.ArgumentParser(description="设置 WhatsApp 代理")
    parser.add_argument("--id", type=int, required=True, help="WhatsApp 设备 ID")
    parser.add_argument("--is-proxy", type=int, required=True, choices=[0, 1], help="0=禁用代理, 1=启用代理")
    parser.add_argument("--host", type=str, default=None, help="代理主机")
    parser.add_argument("--port", type=int, default=None, help="代理端口")
    parser.add_argument("--type", type=str, default="socks5", help="代理类型")
    parser.add_argument("--protocol", type=str, default="ipv4", help="协议")
    parser.add_argument("--account", type=str, default=None, help="账号")
    parser.add_argument("--password", type=str, default=None, help="密码")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        params = {"id": args.id, "is_proxy": args.is_proxy}
        for field in ["host", "port", "type", "protocol", "account", "password"]:
            val = getattr(args, field, None)
            if val is not None:
                params[field] = val

        data = client.post("/api/v2/set-individual-whatsapp-app-proxy", params)

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print(f"\n{'='*60}")
        print(f"✅ WhatsApp 代理设置成功！")
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
