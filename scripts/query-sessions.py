#!/usr/bin/env python3
"""
SaleSmartly Get Session List

获取会话列表 - 支持分页、状态筛选、客服筛选、时间范围筛选

API ID: 429104830e0
Endpoint: /api/v2/get-session-list
Method: GET

Usage:
    uv run scripts/query-sessions.py --page 1 --page-size 20
    uv run scripts/query-sessions.py --status 1
    uv run scripts/query-sessions.py --member 616
    uv run scripts/query-sessions.py --today
    uv run scripts/query-sessions.py --days 7 --json

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


ENDPOINT = "/api/v2/get-session-list"


def parse_time_range(days: int = None, start_date: str = None, end_date: str = None):
    """
    解析时间范围

    返回：{"start": timestamp, "end": timestamp} 格式的 JSON 字符串
    """
    now = datetime.now()

    if days:
        start = now - timedelta(days=days)
        start_ts = int(start.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        end_ts = int(now.timestamp())
    elif start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
    elif start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        start_ts = int(start.timestamp())
        end_ts = int(now.timestamp())
    else:
        return None

    return json.dumps({"start": start_ts, "end": end_ts})


def format_sessions(data: dict, verbose: bool = False):
    """格式化输出会话列表"""
    sessions = data.get("list", [])
    total = data.get("total", 0)
    page = data.get("page", 1)
    page_size = data.get("page_size", 10)

    if not sessions:
        print("💬 暂无会话数据")
        return

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size

    print(f"💬 会话列表 - 第 {page}/{total_pages} 页（共 {total} 条）")
    print("=" * 100)

    # 表头
    print(f"{'会话 ID':<20} {'客户 ID':<26} {'客服 ID':<8} {'状态':<8} {'消息数':<8} {'开始时间':<20}")
    print("-" * 100)

    # 会话数据
    for session in sessions:
        session_id = session.get("session_id", "N/A")[:18]
        chat_user_id = session.get("chat_user_id", "N/A")[:24]
        sys_user_id = session.get("sys_user_id", "未分配")

        # 会话状态
        status = session.get("session_status", 0)
        status_text = "已结束" if status == 1 else "进行中"

        # 消息数
        msg_count = session.get("msg_count", 0)

        # 开始时间
        start_time = session.get("start_time", 0)
        start_str = format_timestamp(start_time) if start_time else "N/A"

        # 结束时间（仅已结束会话）
        end_time = session.get("end_time", 0)
        end_str = format_timestamp(end_time) if end_time and status == 1 else ""

        print(f"{session_id:<20} {chat_user_id:<26} {str(sys_user_id):<8} {status_text:<8} {msg_count:<8} {start_str:<20}")

        if verbose:
            # 详细信息
            title = session.get("title", "")
            tags = session.get("tags", "")
            assign_time = session.get("assign_time", 0)
            assign_str = format_timestamp(assign_time) if assign_time else "N/A"

            print(f"  标题：{title}")
            print(f"  标签：{tags}")
            print(f"  分配时间：{assign_str}")
            if status == 1:
                print(f"  结束时间：{end_str}")
            print("-" * 100)

    print("=" * 100)
    print(f"📊 统计：客户消息 {sum(s.get('customer_msg_count', 0) for s in sessions)} | "
          f"客服消息 {sum(s.get('user_msg_count', 0) for s in sessions)}")


def main():
    parser = argparse.ArgumentParser(description="SaleSmartly 会话列表查询")

    # 分页参数
    parser.add_argument("--page", type=int, default=1, help="页码（从 1 开始，默认 1）")
    parser.add_argument("--page-size", type=int, default=10, help="每页数量（最大 100，默认 10）")

    # 筛选参数
    parser.add_argument("--status", type=int, default=0, choices=[0, 1],
                        help="会话状态（0=活跃，1=已结束，默认 0）")
    parser.add_argument("--sub-status", type=int, choices=[0, 1, 2],
                        help="子状态（0=全部，1=未分配，2=机器人接待）")
    parser.add_argument("--member", type=int, dest="member_id",
                        help="客服 ID（sys_user_id）")
    parser.add_argument("--session-id", type=str, dest="session_id",
                        help="会话 ID（精确查询单个会话）")

    # 时间参数
    parser.add_argument("--today", action="store_true", help="查询今天的会话")
    parser.add_argument("--yesterday", action="store_true", help="查询昨天的会话")
    parser.add_argument("--days", type=int, help="查询最近 N 天的会话")
    parser.add_argument("--start-date", type=str, help="开始日期（YYYY-MM-DD）")
    parser.add_argument("--end-date", type=str, help="结束日期（YYYY-MM-DD）")

    # 输出选项
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--debug", action="store_true", help="调试模式（打印原始响应）")
    add_output_args(parser)
    args = parser.parse_args()
    json_mode = args.json or args.quiet

    # 验证参数
    if args.page_size > 100:
        if not json_mode:
            print("⚠️  page_size 最大为 100，已自动调整为 100")
        args.page_size = 100

    try:
        config = load_config(config_path=args.config)
        client = SaleSmartlyClient(config)

        # 解析时间范围
        time_range = None

        if args.today:
            today = datetime.now().strftime("%Y-%m-%d")
            time_range = parse_time_range(start_date=today, end_date=today)
        elif args.yesterday:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            time_range = parse_time_range(start_date=yesterday, end_date=yesterday)
        elif args.days:
            time_range = parse_time_range(days=args.days)
        elif args.start_date:
            time_range = parse_time_range(start_date=args.start_date, end_date=args.end_date)

        # 构建请求参数
        params = {
            "page": args.page,
            "page_size": args.page_size,
            "session_status": args.status,
        }

        if args.sub_status is not None:
            params["sub_status"] = args.sub_status
        if args.member_id is not None:
            params["sys_user_id"] = args.member_id
        if args.session_id:
            params["session_id"] = args.session_id
        if time_range:
            params["start_time"] = time_range
        # end_time only valid for ended sessions
        # (end_time_range is not exposed as CLI arg in original, kept as-is)

        # 调用 API
        data = client.get(ENDPOINT, params)

        # 输出结果
        if json_mode:
            print_result(True, data=data, json_mode=True)
            return

        format_sessions(data, verbose=args.verbose)

    except (ConfigError, APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=json_mode)
        sys.exit(1)


if __name__ == "__main__":
    main()
