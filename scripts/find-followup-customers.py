#!/usr/bin/env python3
"""
SalesSmartly 客户跟进查找

找出 N 天未联系的客户，生成待跟进列表

Usage:
    uv run scripts/find-followup-customers.py --days 7 --limit 20
    uv run scripts/find-followup-customers.py --days 3 --dingtalk  # 推送到钉钉
"""

import sys
import json
import hashlib
import argparse
import urllib.request
import urllib.parse
import ssl
from datetime import datetime, timedelta
import requests

# 配置文件
CONFIG_FILE = "api-key.json"
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=c5e9abb0ab576f6f64ab450694e13a0fe75ceaee114873ce8f59b76b4bcc719e"
API_BASE_URL = "https://developer.salesmartly.com"


def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('apiKey'), config.get('projectId')
    except Exception as e:
        print(f"❌ 读取配置文件失败：{e}")
        sys.exit(1)


def generate_sign(api_key: str, params: dict) -> str:
    """生成 SalesSmartly API 签名（MD5）"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()


def get_all_customers(api_key, project_id, days=365):
    """获取所有客户数据"""
    all_customers = []
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())
    
    print(f"📥 正在获取客户数据（最近 {days} 天）...")
    
    for page in range(1, 20):  # 最多查 20 页
        updated_time_str = json.dumps({"start": start_time, "end": end_time})
        params = {
            "project_id": project_id,
            "updated_time": updated_time_str,
            "page": str(page),
            "page_size": "100"
        }
        
        sign = generate_sign(api_key, params)
        
        query_params = {
            "project_id": project_id,
            "updated_time": urllib.parse.quote(updated_time_str),
            "page": str(page),
            "page_size": "100"
        }
        query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
        url = f"{API_BASE_URL}/api/v2/get-contact-list?{query_string}"
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SalesSmartly-Agent/1.0",
            "External-Sign": sign
        }
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                resp_json = json.loads(response.read().decode('utf-8'))
            
            customers = resp_json.get('data', {}).get('list', [])
            if not customers:
                break
            
            print(f"  第 {page} 页：{len(customers)} 条")
            all_customers.extend(customers)
            
            if len(customers) < 100:
                break
                
        except Exception as e:
            print(f"❌ 请求失败：{e}")
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


def get_last_message_time(api_key, project_id, chat_user_id, days=60):
    """获取与某个客户的最后联系时间"""
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())
    
    params = {
        "project_id": project_id,
        "chat_user_id": chat_user_id,
        "page_size": "1",  # 只查最新 1 条
        "updated_time": json.dumps({"start": start_time, "end": end_time})
    }
    
    sign = generate_sign(api_key, params)
    
    query_params = {
        "project_id": project_id,
        "chat_user_id": chat_user_id,
        "page_size": "1",
        "updated_time": urllib.parse.quote(params['updated_time'])
    }
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{API_BASE_URL}/api/v2/get-message-list?{query_string}"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SalesSmartly-Agent/1.0",
        "External-Sign": sign
    }
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            resp_json = json.loads(response.read().decode('utf-8'))
        
        messages = resp_json.get('data', {}).get('list', [])
        if messages:
            # 返回最新的消息时间
            last_msg = messages[0]
            send_time = last_msg.get('send_time', 0)
            # 13 位毫秒转秒
            if send_time > 1000000000000:
                send_time = send_time // 1000
            return send_time
        return 0
        
    except Exception as e:
        return 0


def send_dingtalk_notification(followup_list, days):
    """发送钉钉通知"""
    if not followup_list:
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
    
    data = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }
    
    try:
        resp = requests.post(DINGTALK_WEBHOOK, json=data, timeout=10)
        result = resp.json()
        if result.get('errcode') == 0:
            print(f"✅ 钉钉通知已发送")
        else:
            print(f"⚠️ 钉钉发送失败：{result.get('errmsg')}")
    except Exception as e:
        print(f"⚠️ 钉钉发送失败：{e}")


def find_followup_customers(days: int = 7, limit: int = 20, dingtalk: bool = False):
    """
    找出需要跟进的客户
    
    Args:
        days: N 天未联系
        limit: 最多返回多少个
        dingtalk: 是否发送到钉钉
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    print(f"\n🔍 查找 {days} 天未联系的客户...\n")
    
    # 1. 获取所有客户
    customers = get_all_customers(api_key, project_id, days=365)
    
    # 2. 检查每个客户的最后联系时间
    followup_list = []
    now = datetime.now().timestamp()
    
    print(f"📊 正在分析客户联系情况...\n")
    
    for i, customer in enumerate(customers, 1):
        chat_user_id = customer.get('chat_user_id')
        name = customer.get('name', '未知')
        
        # 获取最后联系时间
        last_contact = get_last_message_time(api_key, project_id, chat_user_id, days=60)
        
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
        if i % 10 == 0:
            print(f"  已检查 {i}/{len(customers)} 个客户，待跟进：{len(followup_list)}")
    
    # 3. 排序（按未联系天数降序）
    followup_list.sort(key=lambda x: x['days_since_contact'], reverse=True)
    
    # 4. 限制数量
    followup_list = followup_list[:limit]
    
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
        send_dingtalk_notification(followup_list, days)
    elif dingtalk and not followup_list:
        print(f"\n⚠️  没有待跟进客户，跳过钉钉通知")
    
    print(f"{'='*70}")
    
    return followup_list


def main():
    parser = argparse.ArgumentParser(description='SalesSmartly 客户跟进查找工具')
    parser.add_argument('--days', type=int, default=7, help='N 天未联系（默认 7 天）')
    parser.add_argument('--limit', type=int, default=20, help='最多返回多少个（默认 20）')
    parser.add_argument('--dingtalk', action='store_true', help='发送到钉钉群')
    
    args = parser.parse_args()
    
    find_followup_customers(
        days=args.days,
        limit=args.limit,
        dingtalk=args.dingtalk
    )


if __name__ == "__main__":
    main()
