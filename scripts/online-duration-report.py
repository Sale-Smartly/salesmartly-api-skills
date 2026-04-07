#!/usr/bin/env python3
"""
在线时长报表查询脚本

功能：查询客服在指定日期范围内的在线时长统计数据
API：GET /api/v2/get-online-duration-report

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
from datetime import datetime, timedelta


# ============================================================================
# 工具函数
# ============================================================================

def format_duration(seconds):
    """格式化时长（秒 -> 小时：分钟：秒）"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours}小时{minutes}分钟{secs}秒"
    elif minutes > 0:
        return f"{minutes}分钟{secs}秒"
    else:
        return f"{secs}秒"


def format_duration_hours(seconds):
    """格式化时长（秒 -> *时*分*秒）"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    return f"{hours}时{minutes}分{secs}秒"


# ============================================================================
# 输出函数
# ============================================================================

def print_report(report_list, start_date, end_date, sys_user_id=None):
    """打印报表数据"""
    if not report_list:
        print(f"\n📊 在线时长报表")
        print(f"   日期范围：{start_date} 至 {end_date}")
        print(f"   没有找到数据")
        return

    # 打印表头
    print(f"\n📊 在线时长报表")
    print(f"   日期范围：{start_date} 至 {end_date}")
    if sys_user_id:
        print(f"   客服 ID：{sys_user_id}")
    print(f"   共 {len(report_list)} 个客服")
    print()

    # 打印表格
    print("=" * 140)
    print(f"{'客服昵称':<30} {'ID':<10} {'登录时长':<20} {'在线时长':<20} {'忙碌时长':<20} {'离线时长':<20}")
    print("-" * 140)

    # 统计总计
    total_login = 0
    total_online = 0
    total_busy = 0
    total_offline = 0

    for item in report_list:
        nickname = item.get('nickname', 'N/A')
        uid = item.get('sys_user_id', 0)
        login_duration = item.get('login_duration', 0)
        online_duration = item.get('online_duration', 0)
        busy_duration = item.get('busy_duration', 0)
        offline_duration = item.get('offline_duration', 0)

        print(f"{nickname:<30} {uid:<10} {format_duration_hours(login_duration):<20} "
              f"{format_duration_hours(online_duration):<20} {format_duration_hours(busy_duration):<20} "
              f"{format_duration_hours(offline_duration):<20}")

        total_login += login_duration
        total_online += online_duration
        total_busy += busy_duration
        total_offline += offline_duration

    # 打印总计
    print("-" * 140)
    print(f"{'总计':<30} {'':<10} {format_duration_hours(total_login):<20} "
          f"{format_duration_hours(total_online):<20} {format_duration_hours(total_busy):<20} "
          f"{format_duration_hours(total_offline):<20}")
    print("=" * 140)

    # 打印详细时长（秒）
    print(f"\n📝 详细数据（秒）:")
    print(f"   总登录时长：{format_duration(total_login)}")
    print(f"   总在线时长：{format_duration(total_online)}")
    print(f"   总忙碌时长：{format_duration(total_busy)}")
    print(f"   总离线时长：{format_duration(total_offline)}")

    # 计算比例
    if total_login > 0:
        online_ratio = (total_online / total_login) * 100
        busy_ratio = (total_busy / total_login) * 100
        offline_ratio = (total_offline / total_login) * 100

        print(f"\n📈 状态比例（占登录时长）:")
        print(f"   在线：{online_ratio:.1f}%")
        print(f"   忙碌：{busy_ratio:.1f}%")
        print(f"   离线：{offline_ratio:.1f}%")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='在线时长报表查询脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询今天的在线时长
  python online-duration-report.py --today

  # 查询昨天的在线时长
  python online-duration-report.py --yesterday

  # 查询指定日期范围
  python online-duration-report.py --start 2026-03-01 --end 2026-03-31

  # 查询指定客服的在线时长
  python online-duration-report.py --today --user-id 36294

  # 输出 JSON 格式
  python online-duration-report.py --today --json
        """
    )

    # 日期参数（互斥组）
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--today', action='store_true',
                           help='查询今天')
    date_group.add_argument('--yesterday', action='store_true',
                           help='查询昨天')
    date_group.add_argument('--start', type=str, metavar='DATE',
                           help='开始日期（YYYY-MM-DD）')
    date_group.add_argument('--days', type=int, metavar='N',
                           help='查询最近 N 天')

    # 结束日期
    parser.add_argument('--end', type=str, metavar='DATE',
                       help='结束日期（YYYY-MM-DD），与 --start 配合使用')

    # 客服筛选
    parser.add_argument('--user-id', type=int, metavar='ID',
                       help='客服 ID，筛选指定客服')

    # 输出格式
    add_output_args(parser)

    args = parser.parse_args()

    # 加载配置
    try:
        config = load_config(args.config)
        client = SaleSmartlyClient(config, timeout=30)
    except ConfigError as e:
        print_result(False, error_msg=str(e), json_mode=args.json)
        sys.exit(1)

    # 计算日期范围
    today = datetime.now().date()

    if args.today:
        start_date = today
        end_date = today
    elif args.yesterday:
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif args.start:
        start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
        if args.end:
            end_date = datetime.strptime(args.end, '%Y-%m-%d').date()
        else:
            end_date = start_date
    elif args.days:
        end_date = today
        start_date = today - timedelta(days=args.days - 1)
    else:
        print_result(False, error_msg="请指定日期范围", json_mode=args.json)
        sys.exit(1)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # 构建请求参数
    params = {
        'start_date': start_date_str,
        'end_date': end_date_str,
    }

    if args.user_id is not None:
        params['sys_user_id'] = args.user_id

    # 调用 API
    try:
        data = client.get('/api/v2/get-online-duration-report', params)
    except (APIError, NetworkError) as e:
        print_result(False, error_msg=str(e), json_mode=args.json)
        sys.exit(1)

    report_list = data.get('list', [])

    # 输出结果
    if args.json:
        print_result(True, data=report_list, meta={
            'start_date': start_date_str,
            'end_date': end_date_str,
            'count': len(report_list),
        }, json_mode=True)
    else:
        print_report(report_list, start_date_str, end_date_str, args.user_id)


if __name__ == '__main__':
    main()
