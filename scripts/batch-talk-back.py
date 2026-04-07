#!/usr/bin/env python3
"""
批量回聊 - SaleSmartly API

功能：批量对多个客户发起回聊请求（异步处理）
接口：POST /api/v2/batch-talk-back

注意：这是一个异步处理接口，不会实时处理完成

使用示例：
    uv run scripts/batch-talk-back.py --chat-user-id abc123 --sys-user-id 1344
    uv run scripts/batch-talk-back.py --chat-user-ids abc123,def456 --sys-user-id 1344
    uv run scripts/batch-talk-back.py --chat-user-ids-file customers.txt --sys-user-id 1344

@safety: confirm
@retryable: true
@category: session
@operation: batch
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, ConfigError, APIError, NetworkError


def read_ids_from_file(file_path: str) -> List[str]:
    """从文件读取客户 ID 列表"""
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="批量回聊 - 对多个客户发起回聊请求（异步处理）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 客户 ID 参数（三选一）
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--chat-user-id", type=str, help="单个访客 ID")
    id_group.add_argument("--chat-user-ids", type=str, help="多个访客 ID（逗号分隔，最多 100 个）")
    id_group.add_argument("--chat-user-ids-file", type=str, help="从文件读取访客 ID 列表")

    parser.add_argument("--sys-user-id", type=str, required=True, help="客服 ID (sys_user_id)")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    # 解析客户 ID
    chat_user_ids: List[str] = []
    if args.chat_user_id:
        chat_user_ids = [args.chat_user_id]
    elif args.chat_user_ids:
        chat_user_ids = [i.strip() for i in args.chat_user_ids.split(",") if i.strip()]
    elif args.chat_user_ids_file:
        try:
            chat_user_ids = read_ids_from_file(args.chat_user_ids_file)
        except FileNotFoundError:
            print_result(False, error_msg=f"文件不存在：{args.chat_user_ids_file}", json_mode=json_mode)
            sys.exit(1)

    if not chat_user_ids:
        print_result(False, error_msg="没有提供有效的客户 ID", json_mode=json_mode)
        sys.exit(1)

    if len(chat_user_ids) > 100:
        print_result(False, error_msg=f"最多支持 100 个客户 ID，当前提供 {len(chat_user_ids)} 个", json_mode=json_mode)
        sys.exit(1)

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        if not json_mode:
            print(f"📞 正在发起批量回聊请求...")
            print(f"   客服 ID: {args.sys_user_id}")
            print(f"   客户数量：{len(chat_user_ids)}")
            print()

        data = client.post(
            "/api/v2/batch-talk-back",
            {
                "sys_user_id": args.sys_user_id,
                "chat_user_ids": ",".join(chat_user_ids),
            },
        )

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        print("✅ 批量回聊请求成功！")
        print("\n⚠️  注意：这是一个异步处理接口，系统会在后台逐步处理回聊请求")
        if isinstance(data, dict):
            if "res" in data:
                print(f"   处理结果：{data['res']}")
            if "session_status" in data:
                print(f"   会话状态：{data['session_status']}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main() or 0)
