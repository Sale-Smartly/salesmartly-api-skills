#!/usr/bin/env python3
"""
批量分配会话 - SaleSmartly API

功能：批量将客户会话分配给指定客服，或结束当前分配
接口：POST /api/v2/batch-assign-contact

使用示例：
    uv run scripts/batch-assign-session.py --chat-user-id abc123 --assign-sys-user-id 1779 --action start
    uv run scripts/batch-assign-session.py --chat-user-ids abc123,def456 --assign-sys-user-id 1779 --action start
    uv run scripts/batch-assign-session.py --chat-user-ids abc123 --assign-sys-user-id 1779 --action end --task-id 574_xxx

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
        description="批量分配会话 - 将客户会话批量分配给指定客服或结束分配",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 客户 ID 参数（三选一）
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument("--chat-user-id", type=str, help="单个客户 ID")
    id_group.add_argument("--chat-user-ids", type=str, help="多个客��� ID（逗号分隔）")
    id_group.add_argument("--chat-user-ids-file", type=str, help="从文件读取客户 ID 列表")

    # 必需参数
    parser.add_argument("--assign-sys-user-id", type=str, required=True, help="被分配的���服 ID (sys_user_id)")
    parser.add_argument("--sys-user-id", type=str, required=True, help="操作者 ID（最高权限客服 ID）")
    parser.add_argument("--action", type=str, required=True, choices=["start", "end"], help="start=开始分配，end=结束分配")

    # 可选参数
    parser.add_argument("--assign-type", type=int, default=1, choices=[0, 1], help="0=无进行中会话，1=全部（默认）")
    parser.add_argument("--task-id", type=str, help="action 为 end 时必需")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    # 验证
    if args.action == "end" and not args.task_id:
        print_result(False, error_msg="action 为 end 时必须提供 --task-id", json_mode=json_mode)
        sys.exit(1)

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

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        params = {
            "action": args.action,
            "sys_user_id": args.sys_user_id,
            "assign_sys_user_id": args.assign_sys_user_id,
            "assign_type": args.assign_type,
            "ids": ",".join(chat_user_ids),
        }
        if args.action == "end" and args.task_id:
            params["task_id"] = args.task_id

        if not json_mode:
            action_text = "开始分��" if args.action == "start" else "结束分配"
            print(f"📋 正在批量{action_text}会话...")
            print(f"   客服：{args.assign_sys_user_id}")
            print(f"   客户数量：{len(chat_user_ids)}")
            print()

        data = client.post("/api/v2/batch-assign-contact", params)

        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        action_text = "分配" if args.action == "start" else "释放"
        print(f"✅ 批量{action_text}会话成功！")
        if isinstance(data, dict) and "task_id" in data:
            print(f"   任务 ID: {data['task_id']}")
            print("\n💡 提示：task_id 可用于后续结束分配操作")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main() or 0)
