#!/usr/bin/env python3
"""
SaleSmartly 每日客户反馈报告
自动查询昨天的客户消息，分析负面情绪，推送到钉钉群

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


# 负面情绪关键词
NEGATIVE_KEYWORDS = [
    "投诉", "不满", "差", "失望", "退款", "骗", "垃圾", "糟糕", "差劲",
    "问题", "故障", "错误", "不行", "没用", "太慢", "生气", "愤怒",
    "无语", "服了", "呵呵", "垃圾系统", "什么破", "太差了", "受不了",
    "complaint", "bad", "worst", "disappointed", "refund", "scam",
    "terrible", "awful", "problem", "issue", "angry", "hate", "bug"
]

# 高优先级关键词（需要立即关注）
HIGH_PRIORITY_KEYWORDS = ["投诉", "退款", "骗", "垃圾", "生气", "愤怒", "refund", "scam", "angry"]


def analyze_text(text: str) -> tuple:
    found = []
    text_lower = text.lower()
    for kw in NEGATIVE_KEYWORDS:
        if kw.lower() in text_lower:
            found.append(kw)

    is_high_priority = any(kw in found for kw in HIGH_PRIORITY_KEYWORDS)
    return found, is_high_priority


def send_to_dingtalk(client, title: str, text: str, webhook: str):
    if not webhook:
        print("❌ 钉钉 Webhook 未配置，请在 api-key.json 中添加 dingtalk.webhook")
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text
        }
    }

    try:
        result = client.post_webhook(webhook, payload)
        return result.get('errcode') == 0
    except NetworkError as e:
        print(f"发送失败：{e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 每日客户反馈报告')
    add_output_args(parser)
    args = parser.parse_args()

    # 加载配置
    try:
        config = load_config(args.config)
        client = SaleSmartlyClient(config, timeout=60)
    except ConfigError as e:
        print_result(False, error_msg=str(e), json_mode=args.json)
        sys.exit(1)

    # 昨天的日期范围
    yesterday = datetime.now() - timedelta(days=1)
    start = int(yesterday.replace(hour=0, minute=0, second=0).timestamp())
    end = int(yesterday.replace(hour=23, minute=59, second=59).timestamp())

    if not args.quiet and not args.json:
        print("开始生成 %s 客户反馈报告..." % yesterday.strftime('%Y-%m-%d'))

    total_messages = 0
    customer_messages = 0
    negative_messages = []
    high_priority_messages = []
    page = 1

    updated_time_json = json.dumps({'start': start, 'end': end})

    # 查询消息（最多 100 页，避免超时）
    while page <= 100:
        try:
            data = client.get('/api/v2/get-all-message-list', {
                'page': str(page),
                'page_size': '100',
                'updated_time': updated_time_json
            })
        except (APIError, NetworkError):
            break

        msgs = data.get('list', [])
        total = data.get('total', 0)

        if not msgs:
            break

        total_messages += len(msgs)

        for msg in msgs:
            sender_type = msg.get('sender_type', 0)
            if sender_type != 1:  # 只分析客户消息
                continue

            customer_messages += 1
            text = msg.get('text', '')
            keywords, is_high_priority = analyze_text(text)

            if keywords:
                ts = msg.get('send_time', 0)
                dt_str = format_timestamp(ts)
                # Extract time portion for display
                time_str = dt_str.split(' ')[-1] if ' ' in dt_str else dt_str
                msg_data = {
                    'time': time_str,
                    'user': str(msg.get('chat_user_id', 'N/A'))[:8] + '...',
                    'text': text[:150],
                    'keywords': keywords,
                    'is_high_priority': is_high_priority
                }
                negative_messages.append(msg_data)
                if is_high_priority:
                    high_priority_messages.append(msg_data)

        if len(msgs) < 100 or total_messages >= total:
            break
        page += 1

    # JSON 输出
    if args.json:
        log_entry = {
            'date': yesterday.strftime('%Y-%m-%d'),
            'total_messages': total_messages,
            'customer_messages': customer_messages,
            'negative_messages': len(negative_messages),
            'high_priority': len(high_priority_messages),
        }
        print_result(True, data=log_entry, json_mode=True)
        return

    # 生成报告
    date_str = yesterday.strftime('%Y-%m-%d %A')

    # 构建钉钉消息
    text = "## 📊 客户反馈日报 (%s)\n\n" % date_str
    text += "### 📈 数据统计\n"
    text += "- **总消息数**: %d 条\n" % total_messages
    text += "- **客户消息**: %d 条\n" % customer_messages
    text += "- **负面反馈**: %d 条\n" % len(negative_messages)

    if high_priority_messages:
        text += "- **🔴 高优先级**: %d 条\n" % len(high_priority_messages)

    text += "\n---\n\n"

    if negative_messages:
        # 高优先级问题
        if high_priority_messages:
            text += "### 🔴 高优先级问题\n"
            for i, msg in enumerate(high_priority_messages[:5], 1):
                text += "%d. [%s] %s\n" % (i, msg['time'], msg['text'])
                text += "   关键词：%s\n\n" % ', '.join(msg['keywords'])
            text += "\n"

        # 问题分类统计
        keyword_count = {}
        for msg in negative_messages:
            for kw in msg['keywords']:
                keyword_count[kw] = keyword_count.get(kw, 0) + 1

        top_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:10]

        text += "### 📋 热门问题关键词\n"
        for kw, count in top_keywords:
            text += "- **%s**: %d 次\n" % (kw, count)

        text += "\n---\n"
        text += "_详细分析请登录系统查看_"
    else:
        text += "### ✅ 昨天没有发现客户不满反馈\n"
        text += "🎉 客户反馈良好，继续保持！"

    # 发送钉钉
    title = "客户反馈日报 - %s" % yesterday.strftime('%Y-%m-%d')
    success = send_to_dingtalk(client, title, text, config.dingtalk_webhook)

    if success:
        print("✅ 报告已发送到钉钉群")
    else:
        print("❌ 发送失败")

    # 保存日志
    log_entry = {
        'date': yesterday.strftime('%Y-%m-%d'),
        'total_messages': total_messages,
        'customer_messages': customer_messages,
        'negative_messages': len(negative_messages),
        'high_priority': len(high_priority_messages),
        'sent': success
    }

    print("报告生成完成：%s" % json.dumps(log_entry, ensure_ascii=False))


if __name__ == "__main__":
    main()
