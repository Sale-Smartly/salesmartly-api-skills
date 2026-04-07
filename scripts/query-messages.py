#!/usr/bin/env python3
"""
SaleSmartly Message Query

API ID: 317790952e0
Endpoint: /api/v2/get-message-list
Method: GET

Usage:
    uv run scripts/query-messages.py --chat-user-id USER123
    uv run scripts/query-messages.py --session-id SESS456 --days 7
    uv run scripts/query-messages.py --chat-user-id USER123 --all --json

⚠️ 重要：发送人 ID 说明
-----------------------------------------
消息中的 `sender` 字段含义取决于 `sender_type`：

- sender_type = 1 (用户): sender = 客户 chat_user_id
- sender_type = 2 (团队成员): sender = 客服 sys_user_id ← 真正的客服 ID
- sender_type = 3 (系统): sender = 系统

✅ 正确用法：当 sender_type=2 时，sender 是客服的 sys_user_id
❌ 错误用法：不要将 sender 与成员 id 字段混淆

@safety: safe
@retryable: true
@category: session
@operation: query
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError


ENDPOINT = "/api/v2/get-message-list"


def main():
    parser = argparse.ArgumentParser(description="SaleSmartly 聊天记录查询工具")

    # 查询条件（二选一）
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--chat-user-id", type=str, help="用户 ID（与 --session-id 二选一）")
    group.add_argument("--session-id", type=str, help="会话 ID（与 --chat-user-id 二选一）")

    parser.add_argument("--page-size", type=int, default=100, help="每页大小（最大 100）")
    parser.add_argument("--all", action="store_true", help="自动获取所有页面数据（当 total > page_size 时）")

    parser.add_argument("--days", type=int, default=None, help="查询最近 N 天的消息")
    parser.add_argument("--start-sequence-id", type=str, default=None, help="开始的消息 ID")
    parser.add_argument("--end-sequence-id", type=str, default=None, help="结束的消息 ID")
    parser.add_argument("--msg-content", type=str, default=None, help="关键词筛选（可选）")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        # 构建请求参数
        params = {
            "page_size": str(args.page_size),
        }

        # chat_user_id 和 session_id 二选一
        if args.chat_user_id:
            params["chat_user_id"] = args.chat_user_id
        if args.session_id:
            params["session_id"] = args.session_id

        # 可选参数
        if args.start_sequence_id:
            params["start_sequence_id"] = args.start_sequence_id
        if args.end_sequence_id:
            params["end_sequence_id"] = args.end_sequence_id
        if args.msg_content:
            params["msg_content"] = args.msg_content

        # 时间范围过滤
        if args.days:
            end_time = int(datetime.now().timestamp())
            start_time = int((datetime.now() - timedelta(days=args.days)).timestamp())
            params["updated_time"] = json.dumps({"start": start_time, "end": end_time})

        if not json_mode:
            print(f"📊 查询聊天记录")
            if args.chat_user_id:
                print(f"用户 ID: {args.chat_user_id}")
            if args.session_id:
                print(f"会话 ID: {args.session_id}")
            if args.days:
                print(f"时间范围：最近 {args.days} 天")
            if args.msg_content:
                print(f"关键词：{args.msg_content}")
            print()

        if args.all:
            messages, total = client.get_all_pages(ENDPOINT, params, page_size=args.page_size)
        else:
            data = client.get(ENDPOINT, params)
            messages = data.get("list") if data else None
            total = data.get("total", 0) if data else 0

        # 处理 messages 为 None 的情况
        if messages is None:
            messages = []

        if json_mode:
            print_result(True, data=messages, meta={"total": total, "count": len(messages)}, json_mode=True)
            return

        # 显示结果
        print(f"\n{'='*60}")
        print(f"✅ 聊天记录查询成功！")
        print(f"{'='*60}")
        print(f"返回：{len(messages)} 条")

        if messages:
            print(f"\n消息列表:")
            for i, msg in enumerate(messages, 1):
                print(f"\n[{i}] 消息 ID: {msg.get('sequence_id', 'N/A')}")

                # 消息类型
                msg_type = msg.get("msg_type")
                type_map = {
                    0: "未定义",
                    1: "文本",
                    2: "图片",
                    3: "模板",
                    4: "文件",
                    5: "回传",
                    6: "视频",
                    7: "邮件",
                    8: "系统消息",
                }
                print(f"    类型：{type_map.get(msg_type, str(msg_type))}")

                # 发送人类型
                sender_type = msg.get("sender_type")
                sender = msg.get("sender", "N/A")
                sender_type_map = {
                    1: "用户",
                    2: "团队成员",
                    3: "系统",
                }
                sender_text = sender_type_map.get(sender_type, str(sender_type))
                # 当发送人是团队成员时，sender 是客服的 sys_user_id
                if sender_type == 2:
                    print(f"    发送人：{sender_text} (客服 ID: {sender})")
                else:
                    print(f"    发送人：{sender_text} ({sender})")

                # 消息内容
                text = msg.get("text", "")
                if text:
                    # 截断长消息
                    if len(text) > 100:
                        text = text[:100] + "..."
                    print(f"    内容：{text}")

                # 发送时间
                send_time = msg.get("send_time")
                if send_time:
                    print(f"    发送时间：{format_timestamp(send_time)}")

                # 已读时间
                read_time = msg.get("read_time")
                if read_time:
                    print(f"    已读时间：{format_timestamp(read_time)}")

                # 是否撤回
                is_withdraw = msg.get("is_withdraw")
                if is_withdraw:
                    print(f"    状态：已撤回")

                # 是否回复
                is_reply = msg.get("is_reply")
                if is_reply:
                    print(f"    状态：已回复")
        else:
            print(f"\n⚠️  未找到消息")

        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
