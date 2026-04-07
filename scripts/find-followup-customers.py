#!/usr/bin/env python3
"""
SaleSmartly 客户跟进查找

找出 N 天未联系的客户，生成待跟进列表

Usage:
    uv run scripts/find-followup-customers.py --days 7 --limit 20
    uv run scripts/find-followup-customers.py --days 3 --dingtalk  # 推送到钉钉

@safety: safe
@retryable: true
@category: customer
@operation: query
"""
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lib import load_config, SaleSmartlyClient, add_output_args, print_result, format_timestamp, ConfigError, APIError, NetworkError

import json
from datetime import datetime, timedelta


def get_all_customers(client, days=365):
    """获取所有客户数据"""
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())

    print(f"📥 正在获取客户数据（最近 {days} 天）...")

    updated_time_str = json.dumps({"start": start_time, "end": end_time})
    all_customers = []

    for page in range(1, 20):  # 最多查 20 页
        params = {
            "updated_time": updated_time_str,
            "page": str(page),
            "page_size": "100"
        }

        try:
            data = client.get('/api/v2/get-contact-list', params)
        except (APIError, NetworkError) as e:
            print(f"❌ 请求失败：{e}")
            break

        customers = data.get('list', [])
        if not customers:
            break

        print(f"  第 {page} 页：{len(customers)} 条")
        all_customers.extend(customers)

        if len(customers) < 100:
            break

    # 去重
    seen = set()
    unique_customers = []
    for c in all_customers:
        uid = c.get('chat_user_id')
        if uid not in seen:
            seen.add(uid)
            unique_customers.append(c)

    print(f"✅ 获取到 {len(unique_customers)} 个唯一客户\n")
    return unique_customers


def get_last_message_time(client, chat_user_id, days=60):
    """获取与某个客户的最后联系时间"""
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())

    params = {
        "chat_user_id": chat_user_id,
        "page_size": "1",  # 只查最新 1 条
        "updated_time": json.dumps({"start": start_time, "end": end_time})
    }

    try:
        data = client.get('/api/v2/get-message-list', params)
        messages = data.get('list', [])
        if messages:
            last_msg = messages[0]
            send_time = last_msg.get('send_time', 0)
            # 13 位毫秒转秒
            if send_time > 1000000000000:
                send_time = send_time // 1000
            return send_time
        return 0
    except (APIError, NetworkError):
        return 0


def send_dingtalk_notification(client, followup_list, days, webhook):
    """发送钉钉通知"""
    if not followup_list:
        return

    if not webhook:
        print("⚠️ 钉钉 Webhook 未配置，请在 api-key.json 中添加 dingtalk.webhook")
        return

    # 构建消息
    title = f"📋 待跟进客户提醒（{days} 天未联系）"
    content = [title, ""]

    for i, customer in enumerate(followup_list[:10], 1):  # 最多显示 10 个
        days_ago = customer['days_since_contact']
        name = customer.get('name', '未知')
        phone = customer.get('phone', '')

        content.append(f"{i}. {name} - {days_ago}天未联系")
        if phone:
            content[-1] += f" ({phone})"

    if len(followup_list) > 10:
        content.append(f"\n... 还有 {len(followup_list) - 10} 个客户")

    content.append(f"\n总计：**{len(followup_list)}** 个客户需要跟进")

    message = "\n".join(content)

    payload = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }

    try:
        result = client.post_webhook(webhook, payload)
        if result.get('errcode') == 0:
            print(f"✅ 钉钉通知已发送")
        else:
            print(f"⚠️ 钉钉发送失败：{result.get('errmsg')}")
    except NetworkError as e:
        print(f"⚠️ 钉钉发送失败：{e}")


def find_followup_customers(client, config, days=7, limit=20, dingtalk=False, json_mode=False, quiet=False):
    """
    找出需要跟进的客户

    Args:
        client: SaleSmartlyClient instance
        config: Config instance
        days: N 天未联系
        limit: 最多返回多少个
        dingtalk: 是否发送到钉钉
        json_mode: JSON 输出模式
        quiet: 安静模式
    """
    if not quiet and not json_mode:
        print(f"\n🔍 查找 {days} 天未联系的客户...\n")

    # 1. 获取所有客户
    customers = get_all_customers(client, days=365)

    # 2. 检查每个客户的最后联系时间
    followup_list = []
    now = datetime.now().timestamp()

    if not quiet and not json_mode:
        print(f"📊 正在分析客户联系情况...\n")

    for i, customer in enumerate(customers, 1):
        chat_user_id = customer.get('chat_user_id')

        # 获取最后联系时间
        last_contact = get_last_message_time(client, chat_user_id, days=60)

        # 计算多少天未联系
        if last_contact > 0:
            days_since = (now - last_contact) / 86400  # 转换为天数
        else:
            # 没有聊天记录，用客户创建时间
            created_time = customer.get('created_time', 0)
            if created_time > 0:
                days_since = (now - created_time) / 86400
            else:
                days_since = 999  # 未知时间，视为很久未联系

        # 如果超过 N 天未联系，加入待跟进列表
        if days_since >= days:
            followup_list.append({
                **customer,
                'days_since_contact': int(days_since),
                'last_contact_time': last_contact
            })

        # 进度显示
        if not quiet and not json_mode and i % 10 == 0:
            print(f"  已检查 {i}/{len(customers)} 个客户，待跟进：{len(followup_list)}")

    # 3. 排序（按未联系天数降序）
    followup_list.sort(key=lambda x: x['days_since_contact'], reverse=True)

    # 4. 限制数量
    followup_list = followup_list[:limit]

    # 5. JSON 输出
    if json_mode:
        print_result(True, data=[{
            'chat_user_id': c.get('chat_user_id'),
            'name': c.get('name', '未知'),
            'phone': c.get('phone', ''),
            'email': c.get('email', ''),
            'days_since_contact': c['days_since_contact'],
        } for c in followup_list], meta={
            'days_threshold': days,
            'total_found': len(followup_list),
        }, json_mode=True)
        return followup_list

    # 5. 输出结果
    print(f"\n{'='*70}")
    print(f"✅ 找到 {len(followup_list)} 个需要跟进的客户")
    print(f"{'='*70}\n")

    if followup_list:
        for i, c in enumerate(followup_list, 1):
            days_ago = c['days_since_contact']
            name = c.get('name', '未知')
            phone = c.get('phone', '')
            email = c.get('email', '')

            print(f"[{i}] {name}")
            print(f"    ⏰ {days_ago} 天未联系")
            if phone:
                print(f"    📱 电话：{phone}")
            if email:
                print(f"    📧 邮箱：{email}")
            if c.get('country'):
                print(f"    🌍 地区：{c.get('country')} {c.get('city', '')}")
            print()
    else:
        print("🎉 太棒了！所有客户都在近期联系过！\n")

    # 6. 发送到钉钉（只有用户明确要求才发送）
    if dingtalk and followup_list:
        print(f"\n📤 正在发送钉钉通知...")
        send_dingtalk_notification(client, followup_list, days, config.dingtalk_webhook)
    elif dingtalk and not followup_list:
        print(f"\n⚠️  没有待跟进客户，跳过钉钉通知")

    print(f"{'='*70}")

    return followup_list


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 客户跟进查找工具')
    parser.add_argument('--days', type=int, default=7, help='N 天未联系（默认 7 天）')
    parser.add_argument('--limit', type=int, default=20, help='最多返回多少个（默认 20）')
    parser.add_argument('--dingtalk', action='store_true', help='发送到钉钉群')
    add_output_args(parser)

    args = parser.parse_args()

    try:
        config = load_config(args.config)
        client = SaleSmartlyClient(config, timeout=30)
    except ConfigError as e:
        print_result(False, error_msg=str(e), json_mode=args.json)
        sys.exit(1)

    find_followup_customers(
        client=client,
        config=config,
        days=args.days,
        limit=args.limit,
        dingtalk=args.dingtalk,
        json_mode=args.json,
        quiet=args.quiet,
    )


if __name__ == "__main__":
    main()
