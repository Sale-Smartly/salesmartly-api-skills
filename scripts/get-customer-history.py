#!/usr/bin/env python3
"""
SaleSmartly 客户历史查询

查看客户完整画像：基本信息 + 订单 + 聊天记录 + 跟进建议

Usage:
    uv run scripts/get-customer-history.py --phone 8613800138000
    uv run scripts/get-customer-history.py --chat-user-id 12345 --days 30
    uv run scripts/get-customer-history.py --phone 8613800138000 --dingtalk
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
API_BASE_URL = "https://developer.salesmartly.com"


def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 支持新旧两种配置格式
            if 'salesmartly' in config:
                api_key = config['salesmartly'].get('apiKey')
                project_id = config['salesmartly'].get('projectId')
                dingtalk_webhook = config.get('dingtalk', {}).get('webhook')
            else:
                api_key = config.get('apiKey')
                project_id = config.get('projectId')
                dingtalk_webhook = config.get('dingtalk', {}).get('webhook')
            return api_key, project_id, dingtalk_webhook
    except Exception as e:
        print(f"❌ 读取配置文件失败：{e}")
        sys.exit(1)


def generate_sign(api_key: str, params: dict) -> str:
    """生成 SaleSmartly API 签名（MD5）"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()


def get_customer_by_phone(api_key, project_id, phone):
    """根据手机号查找客户"""
    # 先获取所有客户，然后匹配手机号
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=365)).timestamp())
    
    print(f"🔍 正在查找手机号：{phone} ...")
    
    for page in range(1, 20):
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
            "User-Agent": "SaleSmartly-Agent/1.0",
            "External-Sign": sign
        }
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                resp_json = json.loads(response.read().decode('utf-8'))
            
            customers = resp_json.get('data', {}).get('list', [])
            
            # 匹配手机号
            for c in customers:
                if c.get('phone') == phone or c.get('phone') == phone[1:]:
                    return c
            
            if len(customers) < 100:
                break
                
        except Exception as e:
            print(f"❌ 请求失败：{e}")
            break
    
    return None


def get_customer_messages(api_key, project_id, chat_user_id, days=30, limit=10):
    """获取客户聊天记录"""
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())
    
    params = {
        "project_id": project_id,
        "chat_user_id": chat_user_id,
        "page_size": str(limit),
        "updated_time": json.dumps({"start": start_time, "end": end_time})
    }
    
    sign = generate_sign(api_key, params)
    
    query_params = {
        "project_id": project_id,
        "chat_user_id": chat_user_id,
        "page_size": str(limit),
        "updated_time": urllib.parse.quote(params['updated_time'])
    }
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{API_BASE_URL}/api/v2/get-message-list?{query_string}"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SaleSmartly-Agent/1.0",
        "External-Sign": sign
    }
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            resp_json = json.loads(response.read().decode('utf-8'))
        
        messages = resp_json.get('data', {}).get('list', [])
        return messages if messages else []
        
    except Exception as e:
        print(f"⚠️  获取消息失败：{e}")
        return []


def analyze_customer(customer, messages):
    """分析客户并生成跟进建议"""
    suggestions = []
    
    # 分析聊天频率
    if messages:
        msg_count = len(messages)
        if msg_count == 0:
            suggestions.append("⚠️  客户从未联系过，建议主动破冰")
        elif msg_count < 3:
            suggestions.append("💬 联系较少，建议增加互动频率")
        else:
            suggestions.append("✅ 联系频繁，保持良好沟通")
    
    # 分析最后联系时间
    if messages:
        last_msg = messages[0]
        send_time = last_msg.get('send_time', 0)
        if send_time > 1000000000000:
            send_time = send_time // 1000
        
        days_since = (datetime.now().timestamp() - send_time) / 86400
        
        if days_since > 30:
            suggestions.append(f"⏰ 已 {int(days_since)} 天未联系，建议尽快跟进")
        elif days_since > 7:
            suggestions.append(f"📅 {int(days_since)} 天未联系，可以主动问候")
    
    # 分析客户信息完整度
    missing_info = []
    if not customer.get('phone'):
        missing_info.append("电话")
    if not customer.get('email'):
        missing_info.append("邮箱")
    if not customer.get('name') or customer.get('name') == 'Guest_':
        missing_info.append("昵称")
    
    if missing_info:
        suggestions.append(f"📝 客户信息不完整：缺少{','.join(missing_info)}，建议补充")
    
    # 分析订单状态（如果有）
    # TODO: 后续可以集成订单查询
    
    return suggestions


def send_dingtalk_notification(customer, messages, suggestions, webhook):
    """发送钉钉通知"""
    if not webhook:
        print("⚠️ 钉钉 Webhook 未配置，请在 api-key.json 中添加 dingtalk.webhook")
        return
    
    name = customer.get('name', '未知')
    phone = customer.get('phone', '')
    
    content = [f"📋 客户画像：{name}"]
    
    if phone:
        content.append(f"📱 电话：{phone}")
    
    content.append(f"\n💡 跟进建议：")
    for i, s in enumerate(suggestions[:3], 1):
        content.append(f"{i}. {s}")
    
    if messages:
        last_msg = messages[0]
        text = last_msg.get('text', '')
        if text:
            content.append(f"\n💬 最近消息：{text[:50]}...")
    
    message = "\n".join(content)
    
    data = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }
    
    try:
        resp = requests.post(webhook, json=data, timeout=10)
        result = resp.json()
        if result.get('errcode') == 0:
            print(f"\n✅ 钉钉通知已发送")
        else:
            print(f"\n⚠️  钉钉发送失败：{result.get('errmsg')}")
    except Exception as e:
        print(f"\n⚠️  钉钉发送失败：{e}")


def get_customer_history(chat_user_id: str = None, phone: str = None, 
                         days: int = 30, message_limit: int = 10,
                         dingtalk: bool = False):
    """
    获取客户完整历史
    
    Args:
        chat_user_id: 客户 ID
        phone: 手机号（二选一）
        days: 查询最近 N 天的消息
        message_limit: 返回多少条消息
        dingtalk: 是否发送到钉钉
    """
    api_key, project_id, dingtalk_webhook = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    # 1. 获取客户信息
    customer = None
    
    if chat_user_id:
        # 直接通过 ID 查询（需要调用查询接口）
        print(f"🔍 正在查询客户 ID: {chat_user_id} ...")
        # TODO: 实现通过 ID 查询单个客户
        # 暂时先通过遍历查找
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=365)).timestamp())
        
        for page in range(1, 20):
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
                "User-Agent": "SaleSmartly-Agent/1.0",
                "External-Sign": sign
            }
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                    resp_json = json.loads(response.read().decode('utf-8'))
                
                customers = resp_json.get('data', {}).get('list', [])
                
                for c in customers:
                    if str(c.get('chat_user_id')) == str(chat_user_id):
                        customer = c
                        break
                
                if customer or len(customers) < 100:
                    break
                    
            except Exception as e:
                print(f"❌ 请求失败：{e}")
                break
    
    elif phone:
        customer = get_customer_by_phone(api_key, project_id, phone)
    
    if not customer:
        print(f"❌ 未找到客户")
        sys.exit(1)
    
    chat_user_id = customer.get('chat_user_id')
    print(f"✅ 找到客户：{customer.get('name', '未知')}")
    
    # 2. 获取聊天记录
    print(f"\n📊 正在获取最近 {days} 天的聊天记录...")
    messages = get_customer_messages(api_key, project_id, chat_user_id, days, message_limit)
    print(f"✅ 获取到 {len(messages)} 条消息")
    
    # 3. 分析客户
    print(f"\n🔍 正在分析客户...")
    suggestions = analyze_customer(customer, messages)
    
    # 4. 输出结果
    print(f"\n{'='*70}")
    print(f"📋 客户完整画像")
    print(f"{'='*70}\n")
    
    # 基本信息
    print(f"【基本信息】")
    print(f"  姓名：{customer.get('name', '未知')}")
    print(f"  客户 ID: {chat_user_id}")
    if customer.get('phone'):
        print(f"  电话：{customer.get('phone')}")
    if customer.get('email'):
        print(f"  邮箱：{customer.get('email')}")
    if customer.get('country'):
        print(f"  地区：{customer.get('country')} {customer.get('city', '')}")
    
    # 统计信息
    created_time = customer.get('created_time', 0)
    if created_time:
        if created_time > 1000000000000:
            created_time = created_time // 1000
        created_dt = datetime.fromtimestamp(created_time)
        print(f"  创建时间：{created_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n【聊天统计】")
    print(f"  最近 {days} 天消息数：{len(messages)}")
    
    # 最近消息
    if messages:
        print(f"\n【最近消息】")
        for i, msg in enumerate(messages[:5], 1):
            text = msg.get('text', '')
            if text:
                if len(text) > 80:
                    text = text[:80] + "..."
                
                sender_type = msg.get('sender_type')
                sender = "客户" if sender_type == 1 else "客服"
                
                send_time = msg.get('send_time', 0)
                if send_time > 1000000000000:
                    send_time = send_time // 1000
                send_dt = datetime.fromtimestamp(send_time)
                
                print(f"  {i}. [{sender}] {send_dt.strftime('%m-%d %H:%M')} - {text}")
    
    # 跟进建议
    print(f"\n【跟进建议】")
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. {s}")
    
    if not suggestions:
        print(f"  ✅ 暂无特别建议，保持正常跟进即可")
    
    print(f"\n{'='*70}")
    
    # 5. 发送到钉钉（只有用户明确要求才发送）
    if dingtalk:
        print(f"\n📤 正在发送钉钉通知...")
        send_dingtalk_notification(customer, messages, suggestions, dingtalk_webhook)
    else:
        print(f"\n💡 提示：添加 --dingtalk 参数可推送到钉钉群")
    
    return {
        'customer': customer,
        'messages': messages,
        'suggestions': suggestions
    }


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 客户历史查询工具')
    parser.add_argument('--chat-user-id', type=str, help='客户 ID（必需，与 --phone 二选一）')
    parser.add_argument('--phone', type=str, help='手机号（与 chat-user-id 二选一）')
    parser.add_argument('--days', type=int, default=30, help='查询最近 N 天的消息（默认 30 天）')
    parser.add_argument('--message-limit', type=int, default=10, help='返回多少条消息（默认 10 条）')
    parser.add_argument('--dingtalk', action='store_true', help='发送到钉钉群')
    
    args = parser.parse_args()
    
    if not args.chat_user_id and not args.phone:
        print("❌ 错误：必须指定 --chat-user-id 或 --phone")
        sys.exit(1)
    
    get_customer_history(
        chat_user_id=args.chat_user_id,
        phone=args.phone,
        days=args.days,
        message_limit=args.message_limit,
        dingtalk=args.dingtalk
    )


if __name__ == "__main__":
    main()
