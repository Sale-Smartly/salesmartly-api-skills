#!/usr/bin/env python3
"""
SaleSmartly Get All Messages

Auto-generated from API documentation
API ID: 385681563e0
Endpoint: /api/v2/get-all-message-list
Method: GET

优化版：支持自然语言时间参数（--today, --yesterday, --days 等）
"""


import sys
import json
import hashlib
import argparse
import urllib.request
import urllib.parse
import ssl
from datetime import datetime, timedelta

# 配置文件
CONFIG_FILE = "api-key.json"
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
    """生成 SaleSmartly API 签名（MD5）"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()


def parse_date_to_millis(date_str: str) -> int:
    """
    解析日期字符串为毫秒时间戳
    支持格式：2026-03-17, 2026-03-17 10:30:00, now, today, yesterday
    """
    now = datetime.now()
    
    if date_str.lower() == 'now':
        return int(now.timestamp() * 1000)
    elif date_str.lower() == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(start.timestamp() * 1000)
    elif date_str.lower() == 'yesterday':
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(start.timestamp() * 1000)
    
    # 尝试解析日期格式
    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d']:
        try:
            dt = datetime.strptime(date_str, fmt)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    
    raise ValueError(f"无法解析日期：{date_str}")


def build_time_range(today=False, yesterday=False, days=None, 
                     start_date=None, end_date=None, 
                     start_time=None, end_time=None) -> str:
    """
    构建时间范围 JSON 字符串（毫秒级）
    
    优先级：
    1. start_time/end_time（精确到秒）
    2. start_date/end_date（日期）
    3. today/yesterday/days（快捷选项）
    """
    now = datetime.now()
    
    # 优先级 1：精确时间
    if start_time or end_time:
        if start_time:
            start_ms = parse_date_to_millis(start_time)
        else:
            start_ms = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        
        if end_time:
            end_ms = parse_date_to_millis(end_time)
        else:
            end_ms = int(now.timestamp() * 1000)
        
        return json.dumps({'start': start_ms, 'end': end_ms})
    
    # 优先级 2：日期范围
    if start_date or end_date:
        if start_date:
            start_ms = parse_date_to_millis(start_date)
        else:
            start_ms = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        
        if end_date:
            end_ms = parse_date_to_millis(end_date)
            # 如果是日期格式，设置为当天 23:59:59
            if not ' ' in end_date and ':' not in end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
                end_ms = int(end_dt.timestamp() * 1000)
        else:
            end_ms = int(now.timestamp() * 1000)
        
        return json.dumps({'start': start_ms, 'end': end_ms})
    
    # 优先级 3：快捷选项
    if today:
        start_ms = int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        end_ms = int(now.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)
        return json.dumps({'start': start_ms, 'end': end_ms})
    
    if yesterday:
        yesterday_dt = now - timedelta(days=1)
        start_ms = int(yesterday_dt.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
        end_ms = int(yesterday_dt.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp() * 1000)
        return json.dumps({'start': start_ms, 'end': end_ms})
    
    if days:
        start_dt = now - timedelta(days=days)
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(now.timestamp() * 1000)
        return json.dumps({'start': start_ms, 'end': end_ms})
    
    return None


def format_timestamp(ts, milli=False) -> str:
    """格式化时间戳为可读格式"""
    if ts is None or ts == 0:
        return "N/A"
    try:
        if milli or ts > 1000000000000:
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(ts)


def main_func(page: int = 1, page_size: int = 20, msg_content: str = None,
              send_time: str = None, updated_time: str = None,
              summary: bool = False, quiet: bool = False,
              format_type: str = 'table', **kwargs):
    """
    Query - Get All Messages
    
    参数:
    page: 页码（从 1 开始）
    page_size: 每页大小（最大 100）
    msg_content: 关键词筛选（可选）
    send_time: 消息发送时间范围（毫秒级），JSON 格式：{"start":1744542011000,"end":1744603254000}
    updated_time: 消息更新时间范围（可选），JSON 格式：{"start":1744542011,"end":1744603254}
    summary: 只显示统计摘要
    quiet: 安静模式（只输出 JSON）
    format_type: 输出格式（table/text/json）
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    if not quiet:
        print(f"📊 Query - Get All Messages")
        print(f"API: /api/v2/get-all-message-list")
        print(f"方法：GET")
        print(f"页码：{page}")
        print(f"每页大小：{page_size}")
        if msg_content:
            print(f"关键词：{msg_content}")
        if send_time:
            print(f"发送时间范围：{send_time}")
        if updated_time:
            print(f"更新时间范围：{updated_time}")
        print()
    
    # 构建请求参数
    params = {
        "project_id": project_id,
        "page": str(page),
        "page_size": str(page_size)
    }
    
    # 添加可选参数
    if msg_content:
        params['msg_content'] = msg_content
    if updated_time:
        params['updated_time'] = updated_time
    if send_time:
        params['send_time'] = send_time
    
    for key, value in kwargs.items():
        if value is not None:
            params[key.replace('-', '_')] = value
    
    sign = generate_sign(api_key, params)
    
    # 构建 URL
    query_params = dict(params)
    for k in ['updated_time', 'created_time', 'send_time', 'msg_content']:
        if k in query_params:
            query_params[k] = urllib.parse.quote(query_params[k], safe='')
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{API_BASE_URL}/api/v2/get-all-message-list?{query_string}"
    req = urllib.request.Request(url, headers={
        "Content-Type": "application/json",
        "User-Agent": "SaleSmartly-Agent/1.0",
        "External-Sign": sign
    })
    
    ssl_context = ssl.create_default_context()
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    try:
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            resp_json = json.loads(response.read().decode('utf-8'))
        
        if resp_json.get('code') != 0:
            print(f"❌ 请求失败：{resp_json.get('msg', 'Unknown error')} (code: {resp_json.get('code')})")
            sys.exit(1)
        
        data = resp_json.get('data', {})
        
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        sys.exit(1)
    
    # 安静模式：只输出 JSON
    if quiet:
        print(json.dumps(resp_json, ensure_ascii=False, indent=2))
        return
    
    # 显示结果
    if not summary:
        print(f"\n{'='*60}")
        print(f"✅ 查询成功！")
        print(f"{'='*60}")
    
    # 保存完整 JSON 到文件
    with open('/tmp/salesmartly-full-response.json', 'w', encoding='utf-8') as f:
        json.dump(resp_json, f, indent=2, ensure_ascii=False)
    
    if not summary:
        print(f"📁 完整响应已保存到：/tmp/salesmartly-full-response.json")
        print()
    
    # 显示统计数据
    total = data.get('total', 0)
    page_num = data.get('page', 1)
    page_size_ret = data.get('page_size', page_size)
    
    if summary:
        print(f"📊 消息统计摘要")
        print(f"{'='*40}")
        print(f"总消息数：{total:,} 条")
        print(f"当前页：{page_num} / 每页：{page_size_ret}")
        
        # 分析返回的消息
        items = data.get('list', [])
        if items:
            customer_msgs = sum(1 for i in items if i.get('sender_type') == 1)
            system_msgs = sum(1 for i in items if i.get('sender_type') in [2, 3])
            print(f"\n当前页消息分布:")
            print(f"  客户消息：{customer_msgs} 条")
            print(f"  系统/客服：{system_msgs} 条")
            
            # 时间范围
            times = [i.get('send_time', 0) for i in items if i.get('send_time')]
            if times:
                print(f"\n时间范围:")
                print(f"  最早：{format_timestamp(min(times), milli=True)}")
                print(f"  最晚：{format_timestamp(max(times), milli=True)}")
        return
    
    # 显示详细列表
    items = data.get('list', [])
    if items:
        print(f"\n返回：{len(items)} 条\n")
        
        if format_type == 'table':
            # 表格格式
            print(f"{'#':<4} {'时间':<20} {'类型':<8} {'用户 ID':<12} {'内容':<50}")
            print(f"{'-'*4} {'-'*20} {'-'*8} {'-'*12} {'-'*50}")
            
            for i, item in enumerate(items, 1):
                send_ts = item.get('send_time', 0)
                send_dt = format_timestamp(send_ts, milli=True)
                sender_type = item.get('sender_type', 0)
                sender_id = item.get('sender', 'N/A')
                
                # 根据 sender_type 显示不同的发送人信息
                if sender_type == 1:
                    sender = '客户'
                elif sender_type == 2:
                    sender = f'客服 (ID:{sender_id})'  # sender_id 是客服的 sys_user_id
                else:
                    sender = '系统'
                
                chat_user = (item.get('chat_user_id', 'N/A') or 'N/A')[:10]
                text = (item.get('text', '') or '')[:47]
                if len(text) < 47 and (item.get('text', '') or ''):
                    text = item.get('text', '')
                
                print(f"{i:<4} {send_dt:<20} {sender:<15} {chat_user:<12} {text:<50}")
        else:
            # 详细格式
            for i, item in enumerate(items, 1):
                print(f"\n[{i}] ID: {item.get('id', 'N/A')}")
                for k, v in item.items():
                    if k != 'id' and v is not None:
                        if isinstance(v, int) and v > 1000000000:
                            print(f"    {k}: {format_timestamp(v, milli=v>1000000000000)}")
                        else:
                            val_str = str(v)
                            if len(val_str) > 100:
                                val_str = val_str[:97] + "..."
                            print(f"    {k}: {val_str}")
    
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description='SaleSmartly 消息查询工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
时间参数示例:
  --today                    查询今天的消息
  --yesterday                查询昨天的消息
  --days 7                   查询最近 7 天
  --start-date 2026-03-17    从指定日期开始
  --end-date 2026-03-17      到指定日期结束
  --start-time "2026-03-17 09:00:00"  精确开始时间
  --end-time "2026-03-17 18:00:00"    精确结束时间

输出格式:
  --summary                  只显示统计摘要
  --quiet                    安静模式（只输出 JSON）
  --format table|text        表格或详细格式

示例:
  python3 query-all-messages.py --today --summary
  python3 query-all-messages.py --days 7 --page-size 50
  python3 query-all-messages.py --msg-content "认证" --today
  python3 query-all-messages.py --quiet | jq '.data.total'
'''
    )
    
    # 分页参数
    parser.add_argument('--page', type=int, default=1, help='页码（从 1 开始）')
    parser.add_argument('--page-size', type=int, default=20, help='每页大小（最大 100）')
    
    # 筛选参数
    parser.add_argument('--msg-content', type=str, default=None, help='关键词筛选（可选）')
    
    # 时间参数 - 快捷选项
    time_group = parser.add_argument_group('时间范围（快捷选项）')
    time_group.add_argument('--today', action='store_true', help='查询今天的消息')
    time_group.add_argument('--yesterday', action='store_true', help='查询昨天的消息')
    time_group.add_argument('--days', type=int, default=None, help='查询最近 N 天')
    
    # 时间参数 - 自定义
    time_group.add_argument('--start-date', type=str, default=None, help='开始日期（YYYY-MM-DD）')
    time_group.add_argument('--end-date', type=str, default=None, help='结束日期（YYYY-MM-DD）')
    time_group.add_argument('--start-time', type=str, default=None, help='开始时间（YYYY-MM-DD HH:MM:SS）')
    time_group.add_argument('--end-time', type=str, default=None, help='结束时间（YYYY-MM-DD HH:MM:SS）')
    
    # 兼容旧参数
    time_group.add_argument('--send-time', type=str, default=None, help='[兼容] 消息发送时间范围，JSON 格式')
    time_group.add_argument('--updated-time', type=str, default=None, help='[兼容] 消息更新时间范围，JSON 格式')
    
    # 输出格式
    output_group = parser.add_argument_group('输出格式')
    output_group.add_argument('--summary', action='store_true', help='只显示统计摘要')
    output_group.add_argument('--quiet', action='store_true', help='安静模式（只输出 JSON）')
    output_group.add_argument('--format', type=str, default='table', choices=['table', 'text'], help='输出格式（table/text）')
    
    args, unknown = parser.parse_known_args()
    
    # 构建时间范围
    send_time = args.send_time
    if not send_time:
        send_time = build_time_range(
            today=args.today,
            yesterday=args.yesterday,
            days=args.days,
            start_date=args.start_date,
            end_date=args.end_date,
            start_time=args.start_time,
            end_time=args.end_time
        )
    
    main_func(
        page=args.page, 
        page_size=args.page_size, 
        msg_content=args.msg_content,
        send_time=send_time,
        updated_time=args.updated_time,
        summary=args.summary,
        quiet=args.quiet,
        format_type=args.format
    )


if __name__ == "__main__":
    main()
