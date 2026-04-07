#!/usr/bin/env python3
"""
客户统计分析 - 深度分析客户数据

功能:
- 客户总量统计
- 客户来源分析
- 客户标签分布
- 活跃客户统计
- 新增客户趋势

使用:
uv run scripts/customer-stats.py
uv run scripts/customer-stats.py --days 30

@safety: safe
@retryable: true
@category: analytics
@operation: query
"""
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError

import json
from datetime import datetime, timedelta
from collections import Counter


def get_all_customers(client, days=30):
    """获取所有客户数据"""
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())

    updated_time_str = json.dumps({"start": start_time, "end": end_time}, separators=(',', ':'))

    all_customers = []
    page = 1
    page_size = 100

    while True:
        params = {
            "page": str(page),
            "page_size": str(page_size),
            "updated_time": updated_time_str
        }

        try:
            data = client.get('/api/v2/get-contact-list', params)
        except (APIError, NetworkError):
            break

        customers = data.get('contact_list', [])
        if not customers:
            break

        all_customers.extend(customers)

        # 检查是否还有更多数据
        total = data.get('total', 0)
        if len(all_customers) >= total:
            break

        page += 1

    return all_customers


def analyze_customers(customers):
    """分析客户数据"""
    if not customers:
        return {}

    # 标签统计
    all_tags = []
    for customer in customers:
        tags = customer.get("tags", [])
        if tags:
            all_tags.extend(tags)

    tag_counts = Counter(all_tags)

    # 来源统计（如果有）
    sources = Counter(c.get("source", "未知") for c in customers)

    # 意向度统计（如果有）
    intentions = Counter(c.get("intention", "未知") for c in customers)

    # 负责人统计
    owners = Counter(c.get("owner_name", "未分配") for c in customers)

    return {
        "total": len(customers),
        "tags": tag_counts,
        "sources": sources,
        "intentions": intentions,
        "owners": owners
    }


def generate_report(client, days=30, json_mode=False, quiet=False):
    """生成客户分析报告"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    if not quiet and not json_mode:
        print("\n" + "=" * 60)
        print("📊 客户统计分析报告")
        print("=" * 60)
        print(f"\n📅 分析周期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        print("-" * 60)

    # 获取客户数据
    if not quiet and not json_mode:
        print("\n⏳ 正在获取客户数据...")
    customers = get_all_customers(client, days)
    if not quiet and not json_mode:
        print(f"✅ 获取到 {len(customers)} 个客户")

    # 分析数据
    if customers:
        stats = analyze_customers(customers)
    else:
        stats = {"total": 0, "tags": Counter(), "sources": Counter(), "intentions": Counter(), "owners": Counter()}

    # JSON 输出
    if json_mode:
        print_result(True, data={
            'total': stats['total'],
            'tags': dict(stats['tags'].most_common(20)),
            'sources': dict(stats['sources'].most_common(10)),
            'intentions': dict(stats['intentions'].most_common(10)),
            'owners': dict(stats['owners'].most_common(10)),
        }, meta={
            'days': days,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
        }, json_mode=True)
        return

    # 总体统计
    print(f"\n📈 总体统计")
    print(f"   客户总数：{stats['total']} 个")
    if days < 30:
        print(f"   平均每天新增：{stats['total'] / days:.1f} 个")

    # 标签分布
    if stats['tags']:
        print(f"\n🏷️  客户标签分布 (Top 10)")
        for tag, count in stats['tags'].most_common(10):
            percentage = (count / stats['total']) * 100
            bar = "█" * int(percentage / 2)
            print(f"   {tag:15} {count:4}个 ({percentage:5.1f}%) {bar}")

    # 意向度分布
    if stats['intentions'] and any(k != "未知" for k in stats['intentions'].keys()):
        print(f"\n🎯 客户意向度分布")
        for intention, count in stats['intentions'].most_common():
            if intention != "未知":
                percentage = (count / stats['total']) * 100
                bar = "█" * int(percentage / 2)
                print(f"   {intention:15} {count:4}个 ({percentage:5.1f}%) {bar}")

    # 负责人分布
    if stats['owners']:
        print(f"\n👔 客户负责人分布 (Top 5)")
        for owner, count in stats['owners'].most_common(5):
            percentage = (count / stats['total']) * 100
            bar = "█" * int(percentage / 2)
            print(f"   {owner:15} {count:4}个 ({percentage:5.1f}%) {bar}")

    # 建议
    print(f"\n💡 优化建议")
    if stats['tags']:
        top_tag = stats['tags'].most_common(1)[0]
        print(f"   - 最多客户标签：{top_tag[0]} ({top_tag[1]}个)")

    if stats['intentions']:
        high_intent = sum(c for i, c in stats['intentions'].items() if i in ["高", "很高", "A", "B"])
        if high_intent:
            print(f"   - 高意向客户：{high_intent}个 (占比 {high_intent/stats['total']*100:.1f}%)")

    print("\n" + "=" * 60)
    print("💡 提示：运行 'uv run scripts/daily-sales-report.py' 查看每日报告")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="客户统计分析")
    parser.add_argument("--days", type=int, default=30, help="分析最近 N 天 (默认 30)")
    add_output_args(parser)

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        client = SaleSmartlyClient(config, timeout=10)
    except ConfigError as e:
        print_result(False, error_msg=str(e), json_mode=args.json)
        sys.exit(1)

    generate_report(client, args.days, json_mode=args.json, quiet=args.quiet)


if __name__ == "__main__":
    main()
