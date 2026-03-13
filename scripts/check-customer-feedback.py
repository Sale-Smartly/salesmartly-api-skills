#!/usr/bin/env python3
"""
严谨查询昨天的客户消息并分析负面情绪反馈
"""

import json, hashlib, urllib.request, urllib.parse, ssl
from datetime import datetime, timedelta

CONFIG_FILE = "api-key.json"
API_BASE_URL = "https://developer.salesmartly.com"

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

def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
        return config.get('apiKey'), config.get('projectId')

def generate_sign(api_key: str, params: dict) -> str:
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()

def query_messages(page: int, page_size: int, start_ts: int, end_ts: int):
    api_key, project_id = load_config()
    
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
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            data = json.loads(resp.read().decode())
        return data.get('data', {})
    except Exception as e:
        print(f"  ❌ 请求失败：{e}")
        return None

def analyze_text(text: str) -> list:
    """检查文本包含哪些负面关键词"""
    found = []
    text_lower = text.lower()
    for kw in NEGATIVE_KEYWORDS:
        if kw.lower() in text_lower:
            found.append(kw)
    return found

def timestamp_to_dt(ts):
    if ts > 1000000000000:
        return datetime.fromtimestamp(ts / 1000)
    return datetime.fromtimestamp(ts)

def main():
    yesterday = datetime.now() - timedelta(days=1)
    start = int(yesterday.replace(hour=0, minute=0, second=0).timestamp())
    end = int(yesterday.replace(hour=23, minute=59, second=59).timestamp())
    
    print("="*70)
    print("📋 昨天客户反馈分析报告")
    print("="*70)
    print("日期：%s" % yesterday.strftime('%Y-%m-%d %A'))
    print("时间范围：%s 00:00:00 - 23:59:59" % yesterday.strftime('%Y-%m-%d'))
    print("项目 ID: %s" % load_config()[1])
    print("="*70)
    print()
    
    total_messages = 0
    customer_messages = 0
    negative_messages = []
    page = 1
    
    while True:
        print("📄 查询第 %d 页..." % page, end=" ")
        data = query_messages(page, 100, start, end)
        
        if not data:
            print("失败")
            break
        
        msgs = data.get('list', [])
        total = data.get('total', 0)
        
        if not msgs:
            print("无数据")
            break
        
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
                dt = timestamp_to_dt(ts)
                negative_messages.append({
                    'time': dt.strftime('%Y-%m-%d %H:%M:%S'),
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
    print()
    print("="*70)
    print("📊 统计结果")
    print("="*70)
    print("总消息数：%d" % total_messages)
    print("客户消息：%d" % customer_messages)
    print("负面反馈：%d 条" % len(negative_messages))
    print()
    
    if negative_messages:
        print("⚠️  发现 %d 条潜在不满消息:" % len(negative_messages))
        print("="*70)
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
    print("="*70)

if __name__ == "__main__":
    main()
