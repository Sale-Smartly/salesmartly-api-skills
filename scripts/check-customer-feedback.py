#!/usr/bin/env python3
"""
严谨查询昨天的客户消息并分析负面情绪反馈

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

from datetime import datetime, timedelta

# 负面情绪关键词（中英文）
NEGATIVE_KEYWORDS = [
    # 中文
    "投诉", "不满", "差", "失望", "退款", "骗", "垃圾", "糟糕", "差劲",
    "问题", "故障", "错误", "不行", "没用", "太慢", "生气", "愤怒",
    "无语", "服了", "呵呵", "垃圾系统", "什么破", "太差了", "受不了",
    "浪费时间", "体验差", "不好用", "很难用", "卡顿", "崩溃",
    # 英文
    "complaint", "bad", "worst", "disappointed", "refund", "scam",
    "terrible", "awful", "problem", "issue", "angry", "hate",
    "useless", "slow", "broken", "bug", "error", "sucks"
]


def analyze_text(text: str) -> list:
    """检查文本包含哪些负面关键词"""
    found = []
    text_lower = text.lower()
    for kw in NEGATIVE_KEYWORDS:
        if kw.lower() in text_lower:
            found.append(kw)
    return found


def main():
    parser = argparse.ArgumentParser(description='昨天客户反馈负面情绪分析')
    add_output_args(parser)
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        client = SaleSmartlyClient(config, timeout=60)
    except ConfigError as e:
        print_result(False, error_msg=str(e), json_mode=args.json)
        sys.exit(1)

    yesterday = datetime.now() - timedelta(days=1)
    start = int(yesterday.replace(hour=0, minute=0, second=0).timestamp())
    end = int(yesterday.replace(hour=23, minute=59, second=59).timestamp())

    if not args.quiet and not args.json:
        print("=" * 70)
        print("📋 昨天客户反馈分析报告")
        print("=" * 70)
        print("日期：%s" % yesterday.strftime('%Y-%m-%d %A'))
        print("时间范围：%s 00:00:00 - 23:59:59" % yesterday.strftime('%Y-%m-%d'))
        print("项目 ID: %s" % config.project_id)
        print("=" * 70)
        print()

    total_messages = 0
    customer_messages = 0
    negative_messages = []
    page = 1

    import json as _json
    updated_time_json = _json.dumps({'start': start, 'end': end})

    while True:
        if not args.quiet and not args.json:
            print("📄 查询第 %d 页..." % page, end=" ")

        try:
            data = client.get('/api/v2/get-all-message-list', {
                'page': str(page),
                'page_size': '100',
                'updated_time': updated_time_json
            })
        except (APIError, NetworkError) as e:
            if not args.quiet and not args.json:
                print("失败")
            print_result(False, error_msg=str(e), json_mode=args.json)
            break

        msgs = data.get('list', [])
        total = data.get('total', 0)

        if not msgs:
            if not args.quiet and not args.json:
                print("无数据")
            break

        if not args.quiet and not args.json:
            print("成功 (共 %d 条)" % total)
        total_messages += len(msgs)

        for msg in msgs:
            sender_type = msg.get('sender_type', 0)

            # 只分析客户消息
            if sender_type != 1:
                continue

            customer_messages += 1
            text = msg.get('text', '')

            # 检查负面情绪
            keywords = analyze_text(text)
            if keywords:
                ts = msg.get('send_time', 0)
                negative_messages.append({
                    'time': format_timestamp(ts),
                    'user': msg.get('chat_user_id', 'N/A'),
                    'session': msg.get('chat_session_id', 'N/A'),
                    'text': text[:300],
                    'keywords': keywords
                })

        # 判断是否还有下一页
        if len(msgs) < 100 or total_messages >= total:
            break
        page += 1

    # 输出报告
    if args.json:
        print_result(True, data={
            'date': yesterday.strftime('%Y-%m-%d'),
            'total_messages': total_messages,
            'customer_messages': customer_messages,
            'negative_count': len(negative_messages),
            'negative_messages': negative_messages,
        }, meta={'query_pages': page}, json_mode=True)
        return

    print()
    print("=" * 70)
    print("📊 统计结果")
    print("=" * 70)
    print("总消息数：%d" % total_messages)
    print("客户消息：%d" % customer_messages)
    print("负面反馈：%d 条" % len(negative_messages))
    print()

    if negative_messages:
        print("⚠️  发现 %d 条潜在不满消息:" % len(negative_messages))
        print("=" * 70)
        for i, msg in enumerate(negative_messages, 1):
            print()
            print("[%d] ⏰ %s" % (i, msg['time']))
            print("    👤 用户：%s" % msg['user'])
            print("    💬 会话：%s" % msg['session'])
            print("    🔍 关键词：%s" % ', '.join(msg['keywords']))
            print("    📝 内容：%s" % msg['text'])
    else:
        print("✅ 昨天没有发现客户不满反馈！")
        print()
        print("🎉 客户反馈良好，继续保持！")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
