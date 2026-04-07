#!/usr/bin/env python3
"""
SaleSmartly 团队客服会话统计 v2
- 按成员统计会话数量
- 直接使用 API 返回的 total 字段
- 支持时间范围筛选

@safety: safe
@retryable: true
@category: team
@operation: query
"""
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError

import json
from datetime import datetime, timezone, timedelta


def parse_time_range(days=None, start_date=None, end_date=None):
    """
    解析时间范围（使用北京时间 UTC+8）
    """
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)

    if days:
        start = now - timedelta(days=days)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
    elif start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=beijing_tz
        )
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, microsecond=0, tzinfo=beijing_tz
        )
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
    elif start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=beijing_tz
        )
        start_ts = int(start.timestamp())
        end_ts = int(now.timestamp())
    else:
        return None

    return json.dumps({"start": start_ts, "end": end_ts})


def get_session_count(client, member_id=None, status=None, time_range=None, end_time_range=None):
    """
    获取会话数量（直接使用 API 返回的 total 字段）
    """
    params = {
        'page': 1,
        'page_size': 1,  # 只需要 total，不需要列表数据
    }

    if member_id is not None:
        params['sys_user_id'] = member_id

    if status is not None:
        params['session_status'] = status

    if time_range:
        params['start_time'] = time_range

    if end_time_range and status == 1:
        params['end_time'] = end_time_range

    try:
        data = client.get('/api/v2/get-session-list', params)
        return data.get('total', 0)
    except (APIError, NetworkError) as e:
        print(f"❌ 获取会话列表失败：{e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 团队客服会话统计 v2')

    parser.add_argument('--today', action='store_true', help='统计今天的会话')
    parser.add_argument('--yesterday', action='store_true', help='统计昨天的会话')
    parser.add_argument('--days', type=int, help='统计最近 N 天的会话')
    parser.add_argument('--start-date', type=str, help='开始日期（YYYY-MM-DD）')
    parser.add_argument('--end-date', type=str, help='结束日期（YYYY-MM-DD）')
    parser.add_argument('--status', type=int, choices=[0, 1], help='会话状态（0=活跃，1=已结束）')
    parser.add_argument('--member', type=int, dest='member_id', help='指定客服 ID')
    add_output_args(parser)

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        client = SaleSmartlyClient(config, timeout=30)
    except ConfigError as e:
        print_result(False, error_msg=str(e), json_mode=args.json)
        sys.exit(1)

    # 解析时间范围
    time_range = None
    end_time_range = None
    time_desc = ""

    if args.today:
        today = datetime.now().strftime('%Y-%m-%d')
        time_range = parse_time_range(start_date=today, end_date=today)
        end_time_range = time_range
        time_desc = "今天"
    elif args.yesterday:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        time_range = parse_time_range(start_date=yesterday, end_date=yesterday)
        end_time_range = time_range
        time_desc = "昨天"
    elif args.days:
        time_range = parse_time_range(days=args.days)
        end_time_range = time_range
        time_desc = f"最近 {args.days} 天"
    elif args.start_date:
        time_range = parse_time_range(start_date=args.start_date, end_date=args.end_date)
        end_time_range = time_range
        time_desc = f"{args.start_date} 至 {args.end_date or '今天'}"
    else:
        time_desc = "全部时间"

    # 获取成员列表
    if not args.quiet and not args.json:
        print(f"⏳ 正在获取团队成员列表...")

    try:
        member_data = client.get('/api/v2/get-member-list', {
            'page': 1,
            'page_size': 100,
        })
        members = member_data.get('list', [])
    except (APIError, NetworkError) as e:
        print_result(False, error_msg=f"获取成员列表失败：{e}", json_mode=args.json)
        sys.exit(1)

    if not args.quiet and not args.json:
        print(f"✅ 共 {len(members)} 个成员\n")

    # 按成员统计
    stats = []

    for member in members:
        mid = member.get('sys_user_id') or member.get('id')
        name = member.get('name') or f"客服{mid}"
        role = member.get('role') or '普通成员'
        email = member.get('email', '')

        if args.member_id and mid != args.member_id:
            continue

        # 查询活跃会话
        active_count = get_session_count(
            client,
            member_id=mid,
            status=0,
            time_range=time_range
        )

        # 查询已结束会话
        ended_count = get_session_count(
            client,
            member_id=mid,
            status=1,
            time_range=time_range,
            end_time_range=end_time_range
        )

        total_count = active_count + ended_count

        stats.append({
            'member_id': mid,
            'name': name,
            'role': role,
            'email': email,
            'active': active_count,
            'ended': ended_count,
            'total': total_count,
        })

    # 查询未分配的会话（sys_user_id=0）
    # 注意：API 对活跃会话的 sys_user_id=0 筛选有 Bug，只查询已结束会话的未分配
    if not args.member_id:
        if not args.quiet and not args.json:
            print("  → 查询未分配会话...")
        unassigned_active = 0  # API Bug：sys_user_id=0 的活跃会话查询返回所有会话
        unassigned_ended = get_session_count(
            client,
            member_id=0,
            status=1,
            time_range=time_range,
            end_time_range=end_time_range
        )
        unassigned_total = unassigned_active + unassigned_ended

        if unassigned_total > 0:
            stats.append({
                'member_id': 0,
                'name': '未分配',
                'role': '-',
                'email': '',
                'active': unassigned_active,
                'ended': unassigned_ended,
                'total': unassigned_total,
            })

    # JSON 输出
    if args.json:
        print_result(True, data=stats, meta={'time_range': time_desc}, json_mode=True)
        return

    # 输出统计表格
    print(f"📅 时间范围：{time_desc}")
    if args.status == 0:
        print(f"📊 会话类型：活跃会话")
    elif args.status == 1:
        print(f"📊 会话类型：已结束会话")
    else:
        print(f"📊 会话类型：活跃 + 已结束（全部）")
    print()

    print("📊 团队客服会话统计")
    print("=" * 100)
    print(f"{'客服':<15} {'角色':<12} {'总会话':<10} {'活跃':<8} {'已结束':<10}")
    print("-" * 100)

    grand_total = 0
    grand_active = 0
    grand_ended = 0

    for s in sorted(stats, key=lambda x: x['total'], reverse=True):
        print(f"{s['name']:<15} {s['role']:<12} {s['total']:<10} {s['active']:<8} {s['ended']:<10}")
        grand_total += s['total']
        grand_active += s['active']
        grand_ended += s['ended']

    print("-" * 100)
    print(f"{'总计':<15} {'':<12} {grand_total:<10} {grand_active:<8} {grand_ended:<10}")
    print("=" * 100)


if __name__ == '__main__':
    main()
