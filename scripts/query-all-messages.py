#!/usr/bin/env python3
"""
SaleSmartly Get All Messages

API ID: 385681563e0
Endpoint: /api/v2/get-all-message-list
Method: GET

支持自然语言时间参数（--today, --yesterday, --days 等）

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


def parse_date_to_millis(date_str: str) -> int:
    """解析日期字符串为毫秒时间戳"""
    now = datetime.now()

    if date_str.lower() == "now":
        return int(now.timestamp() * 1000)
    elif date_str.lower() == "today":
        return int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    elif date_str.lower() == "yesterday":
        yesterday = now - timedelta(days=1)
        return int(yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)

    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期：{date_str}")


def build_time_range(today=False, yesterday=False, days=None, start_date=None, end_date=None, start_time=None, end_time=None):
    """构建时间范围 JSON 字符串（毫秒级）"""
    now = datetime.now()

    if start_time or end_time:
        s = parse_date_to_millis(start_time) if start_time else int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        e = parse_date_to_millis(end_time) if end_time else int(now.timestamp() * 1000)
        return json.dumps({"start": s, "end": e})

    if start_date or end_date:
        s = parse_date_to_millis(start_date) if start_date else int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        if end_date:
            e = parse_date_to_millis(end_date)
            if " " not in end_date and ":" not in end_date:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
                e = int(end_dt.timestamp() * 1000)
        else:
            e = int(now.timestamp() * 1000)
        return json.dumps({"start": s, "end": e})

    if today:
        s = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        e = int(now.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)
        return json.dumps({"start": s, "end": e})

    if yesterday:
        yd = now - timedelta(days=1)
        s = int(yd.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        e = int(yd.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)
        return json.dumps({"start": s, "end": e})

    if days:
        s = int((now - timedelta(days=days)).timestamp() * 1000)
        e = int(now.timestamp() * 1000)
        return json.dumps({"start": s, "end": e})

    return None


def main():
    parser = argparse.ArgumentParser(
        description="SaleSmartly 消息查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
时间参数示例:
  --today                    查询今天的消息
  --yesterday                查询昨天的消息
  --days 7                   查询最近 7 天
  --start-date 2026-03-17    从指定日期开始
""",
    )

    parser.add_argument("--page", type=int, default=1, help="页码（从 1 开始）")
    parser.add_argument("--page-size", type=int, default=100, help="每页大小（最大 100）")
    parser.add_argument("--all", action="store_true", help="自动获取所有页面数据")
    parser.add_argument("--chat-user-id", type=str, default=None, help="用户 ID")
    parser.add_argument("--session-id", type=str, default=None, help="会话 ID")
    parser.add_argument("--msg-content", type=str, default=None, help="关键词筛选")

    time_group = parser.add_argument_group("时间范围")
    time_group.add_argument("--today", action="store_true", help="查询今天的消息")
    time_group.add_argument("--yesterday", action="store_true", help="查询昨天的消息")
    time_group.add_argument("--days", type=int, default=None, help="查询最近 N 天")
    time_group.add_argument("--start-date", type=str, default=None, help="开始日期 (YYYY-MM-DD)")
    time_group.add_argument("--end-date", type=str, default=None, help="结束日期 (YYYY-MM-DD)")
    time_group.add_argument("--start-time", type=str, default=None, help="开始时间 (YYYY-MM-DD HH:MM:SS)")
    time_group.add_argument("--end-time", type=str, default=None, help="结束时间 (YYYY-MM-DD HH:MM:SS)")
    time_group.add_argument("--send-time", type=str, default=None, help="[兼容] 发送时间范围 JSON")
    time_group.add_argument("--updated-time", type=str, default=None, help="[兼容] 更新时间范围 JSON")

    parser.add_argument("--summary", action="store_true", help="只显示统计摘要")
    parser.add_argument("--format", type=str, default="table", choices=["table", "text"], help="输出格式")
    add_output_args(parser)
    args, _ = parser.parse_known_args()
    json_mode = args.json or args.quiet

    # 构建时间范围
    send_time = args.send_time
    if not send_time:
        send_time = build_time_range(
            today=args.today, yesterday=args.yesterday, days=args.days,
            start_date=args.start_date, end_date=args.end_date,
            start_time=args.start_time, end_time=args.end_time,
        )

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        params = {}
        if args.chat_user_id:
            params["chat_user_id"] = args.chat_user_id
        if args.session_id:
            params["session_id"] = args.session_id
        if args.msg_content:
            params["msg_content"] = args.msg_content
        if send_time:
            params["send_time"] = send_time
        if args.updated_time:
            params["updated_time"] = args.updated_time

        if getattr(args, "all"):
            all_messages, total = client.get_all_pages(
                "/api/v2/get-all-message-list", params, page_size=args.page_size, max_pages=20,
            )
            items = all_messages
        else:
            data = client.get(
                "/api/v2/get-all-message-list",
                {"page": args.page, "page_size": args.page_size, **params},
            )
            items = data.get("list") or []
            total = data.get("total") or 0

        if json_mode:
            print_result(True, data=items, meta={"total": total, "page": args.page, "page_size": args.page_size}, json_mode=True)
            return

        # 摘要模式
        if args.summary:
            print(f"📊 消息统计摘要")
            print(f"{'='*40}")
            print(f"总消息数：{total:,} 条")
            if items:
                customer_msgs = sum(1 for i in items if i.get("sender_type") == 1)
                staff_msgs = sum(1 for i in items if i.get("sender_type") in [2, 3])
                print(f"\n当前数据分布:")
                print(f"  客户消息：{customer_msgs} 条")
                print(f"  系统/客服：{staff_msgs} 条")
                times = [i.get("send_time", 0) for i in items if i.get("send_time")]
                if times:
                    print(f"\n时间范围:")
                    print(f"  最早：{format_timestamp(min(times))}")
                    print(f"  最晚：{format_timestamp(max(times))}")
            return

        # 详细输出
        print(f"\n{'='*60}")
        print(f"✅ 查询成功！总消息数：{total:,} 条，返回 {len(items)} 条")
        print(f"{'='*60}")

        if items and args.format == "table":
            print(f"\n{'#':<4} {'时间':<20} {'类型':<15} {'内容':<50}")
            print(f"{'-'*4} {'-'*20} {'-'*15} {'-'*50}")
            for i, item in enumerate(items, 1):
                send_dt = format_timestamp(item.get("send_time", 0))
                st = item.get("sender_type", 0)
                sender = "客户" if st == 1 else (f"客服({item.get('sender', '')})" if st == 2 else "系统")
                text = (item.get("text", "") or "")[:50]
                print(f"{i:<4} {send_dt:<20} {sender:<15} {text:<50}")
        elif items:
            for i, item in enumerate(items, 1):
                print(f"\n[{i}] ID: {item.get('id', 'N/A')}")
                for k, v in item.items():
                    if k != "id" and v is not None:
                        if isinstance(v, int) and v > 1_000_000_000:
                            print(f"    {k}: {format_timestamp(v)}")
                        else:
                            val = str(v)[:100]
                            print(f"    {k}: {val}")
        else:
            print("\n⚠️  未找到消息")

        print(f"\n{'='*60}")

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
