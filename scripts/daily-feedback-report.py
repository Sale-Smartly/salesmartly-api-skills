#!/usr/bin/env python3
"""
SaleSmartly 每日客户反馈报告
自动查询昨天的客户消息，分析负面情绪，推送到钉钉群
"""

import json, hashlib, urllib.request, urllib.parse, ssl
from datetime import datetime, timedelta
import subprocess

CONFIG_FILE = "api-key.json"
API_BASE_URL = "https://developer.salesmartly.com"


def load_config():
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



def generate_sign(api_key: str, params: dict) -> str:
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()

def query_messages(page: int, page_size: int, start_ts: int, end_ts: int):
    api_key, project_id, _ = load_config()
    updated_time_json = json.dumps({'start': start_ts, 'end': end_ts})
    params = {
        'project_id': project_id,
        'page': str(page),
        'page_size': str(page_size),
        'updated_time': updated_time_json
    }
    sign = generate_sign(api_key, params)
    query = 'project_id=%s&page=%s&page_size=%s&updated_time=%s' % (
        project_id, page, page_size, urllib.parse.quote(updated_time_json)
    )
    url = f"{API_BASE_URL}/api/v2/get-all-message-list?{query}"
    
    req = urllib.request.Request(url, headers={
        'External-Sign': sign,
        'Content-Type': 'application/json'
    })
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            data = json.loads(resp.read().decode())
        return data.get('data', {})
    except Exception as e:
        return None

def analyze_text(text: str) -> tuple:
    found = []
    text_lower = text.lower()
    for kw in NEGATIVE_KEYWORDS:
        if kw.lower() in text_lower:
            found.append(kw)
    
    is_high_priority = any(kw in found for kw in HIGH_PRIORITY_KEYWORDS)
    return found, is_high_priority

def timestamp_to_dt(ts):
    if ts > 1000000000000:
        return datetime.fromtimestamp(ts / 1000)
    return datetime.fromtimestamp(ts)

def send_to_dingtalk(title: str, text: str, webhook: str):
    if not webhook:
        print("❌ 钉钉 Webhook 未配置，请在 api-key.json 中添加 dingtalk.webhook")
        return False
    
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text
        }
    }
    
    req = urllib.request.Request(
        webhook,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            return result.get('errcode') == 0
    except Exception as e:
        print(f"发送失败：{e}")
        return False

def main():
    # 加载配置
    api_key, project_id, dingtalk_webhook = load_config()
    
    # 昨天的日期范围
    yesterday = datetime.now() - timedelta(days=1)
    start = int(yesterday.replace(hour=0, minute=0, second=0).timestamp())
    end = int(yesterday.replace(hour=23, minute=59, second=59).timestamp())
    
    print("开始生成 %s 客户反馈报告..." % yesterday.strftime('%Y-%m-%d'))
    
    total_messages = 0
    customer_messages = 0
    negative_messages = []
    high_priority_messages = []
    page = 1
    
    # 查询消息（最多 100 页，避免超时）
    while page <= 100:
        data = query_messages(page, 100, start, end)
        if not data:
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
                dt = timestamp_to_dt(ts)
                msg_data = {
                    'time': dt.strftime('%H:%M'),
                    'user': msg.get('chat_user_id', 'N/A')[:8] + '...',
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
    success = send_to_dingtalk(title, text, dingtalk_webhook)
    
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
