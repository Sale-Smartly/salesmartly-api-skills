#!/usr/bin/env python3
"""
SaleSmartly 团队客服会话统计 v2
- 按成员统计会话数量
- 直接使用 API 返回的 total 字段
- 支持时间范围筛选
"""

import urllib.request
import urllib.parse
import json
import ssl
import sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import argparse

API_BASE_URL = "https://developer.salesmartly.com"

def load_config():
    """加载配置文件"""
    config_paths = [
        'api-key.json',
        '../api-key.json',
        '/home/admin/.openclaw/workspace/skills/salesmartly-api-skills/api-key.json'
    ]
    
    for path in config_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 支持两种格式
                if 'salesmartly' in config:
                    api_key = config['salesmartly'].get('apiKey')
                    project_id = config['salesmartly'].get('projectId')
                else:
                    api_key = config.get('apiKey')
                    project_id = config.get('projectId')
                
                if api_key and project_id:
                    return api_key, project_id
        except FileNotFoundError:
            continue
        except json.JSONDecodeError:
            print(f"❌ 配置文件格式错误：{path}")
            sys.exit(1)
    
    print("❌ 找不到配置文件 api-key.json")
    sys.exit(1)


def generate_sign(api_key: str, params: dict) -> str:
    """生成 API 签名"""
    sign_parts = [api_key]
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest()


def get_member_list():
    """获取团队成员列表"""
    import hashlib
    api_key, project_id = load_config()
    
    params = {
        'page': 1,
        'page_size': 100,
        'project_id': project_id,
    }
    
    sign_parts = [api_key]
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    query_string = urllib.parse.urlencode(params)
    url = f"{API_BASE_URL}/api/v2/get-member-list?{query_string}"
    
    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json')
    req.add_header('external-sign', sign)
    req.add_header('User-Agent', 'SaleSmartly-Agent/1.0')
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            raw_data = response.read().decode('utf-8')
            try:
                result = json.loads(raw_data)
            except json.JSONDecodeError:
                brace_count = 0
                end_pos = 0
                for i, char in enumerate(raw_data):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
                result = json.loads(raw_data[:end_pos])
            
            if result.get('code') == 0:
                return result.get('data', {}).get('list', [])
            else:
                print(f"❌ 获取成员列表失败：{result.get('msg', '未知错误')}")
                return []
    except Exception as e:
        print(f"❌ 网络错误：{e}")
        return []


def get_session_count(member_id: int = None, status: int = None, time_range: str = None, end_time_range: str = None):
    """
    获取会话数量（直接使用 API 返回的 total 字段）
    
    Returns:
        int: 会话总数
    """
    import hashlib
    api_key, project_id = load_config()
    
    params = {
        'page': 1,
        'page_size': 1,  # 只需要 total，不需要列表数据
        'project_id': project_id,
    }
    
    if member_id is not None:
        params['sys_user_id'] = member_id
    
    if status is not None:
        params['session_status'] = status
    
    if time_range:
        params['start_time'] = time_range
    
    if end_time_range and status == 1:
        params['end_time'] = end_time_range
    
    sign_parts = [api_key]
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    query_string = urllib.parse.urlencode(params)
    url = f"{API_BASE_URL}/api/v2/get-session-list?{query_string}"
    
    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json')
    req.add_header('external-sign', sign)
    req.add_header('User-Agent', 'SaleSmartly-Agent/1.0')
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            raw_data = response.read().decode('utf-8')
            try:
                result = json.loads(raw_data)
            except json.JSONDecodeError:
                brace_count = 0
                end_pos = 0
                for i, char in enumerate(raw_data):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
                result = json.loads(raw_data[:end_pos])
            
            if result.get('code') == 0:
                return result.get('data', {}).get('total', 0)
            else:
                print(f"❌ 获取会话列表失败：{result.get('msg', '未知错误')}")
                return 0
    except Exception as e:
        print(f"❌ 网络错误：{e}")
        return 0


def parse_time_range(days: int = None, start_date: str = None, end_date: str = None):
    """
    解析时间范围（使用北京时间 UTC+8）
    """
    import hashlib
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    
    if days:
        start = now - timedelta(days=days)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
    elif start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=beijing_tz
        )
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, microsecond=0, tzinfo=beijing_tz
        )
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
    elif start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=beijing_tz
        )
        start_ts = int(start.timestamp())
        end_ts = int(now.timestamp())
    else:
        return None
    
    return json.dumps({"start": start_ts, "end": end_ts})


def main():
    import hashlib
    parser = argparse.ArgumentParser(description='SaleSmartly 团队客服会话统计 v2')
    
    parser.add_argument('--today', action='store_true', help='统计今天的会话')
    parser.add_argument('--yesterday', action='store_true', help='统计昨天的会话')
    parser.add_argument('--days', type=int, help='统计最近 N 天的会话')
    parser.add_argument('--start-date', type=str, help='开始日期（YYYY-MM-DD）')
    parser.add_argument('--end-date', type=str, help='结束日期（YYYY-MM-DD）')
    parser.add_argument('--status', type=int, choices=[0, 1], help='会话状态（0=活跃，1=已结束）')
    parser.add_argument('--member', type=int, dest='member_id', help='指定客服 ID')
    
    args = parser.parse_args()
    
    # 解析时间范围
    time_range = None
    end_time_range = None
    time_desc = ""
    
    if args.today:
        today = datetime.now().strftime('%Y-%m-%d')
        time_range = parse_time_range(start_date=today, end_date=today)
        end_time_range = time_range
        time_desc = "今天"
    elif args.yesterday:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        time_range = parse_time_range(start_date=yesterday, end_date=yesterday)
        end_time_range = time_range
        time_desc = "昨天"
    elif args.days:
        time_range = parse_time_range(days=args.days)
        end_time_range = time_range
        time_desc = f"最近 {args.days} 天"
    elif args.start_date:
        time_range = parse_time_range(start_date=args.start_date, end_date=args.end_date)
        end_time_range = time_range
        time_desc = f"{args.start_date} 至 {args.end_date or '今天'}"
    else:
        time_desc = "全部时间"
    
    # 获取成员列表
    print(f"⏳ 正在获取团队成员列表...")
    members = get_member_list()
    print(f"✅ 共 {len(members)} 个成员\n")
    
    # 按成员统计
    stats = []
    
    # 先统计所有成员的会话
    for member in members:
        mid = member.get('sys_user_id') or member.get('id')
        name = member.get('name') or f"客服{mid}"
        role = member.get('role') or '普通成员'
        email = member.get('email', '')
        
        if args.member_id and mid != args.member_id:
            continue
        
        # 查询活跃会话
        active_count = get_session_count(
            member_id=mid,
            status=0,
            time_range=time_range
        )
        
        # 查询已结束会话
        ended_count = get_session_count(
            member_id=mid,
            status=1,
            time_range=time_range,
            end_time_range=end_time_range
        )
        
        total_count = active_count + ended_count
        
        stats.append({
            'member_id': mid,
            'name': name,
            'role': role,
            'email': email,
            'active': active_count,
            'ended': ended_count,
            'total': total_count,
        })
    
    # 查询未分配的会话（sys_user_id=0）
    # 注意：API 对活跃会话的 sys_user_id=0 筛选有 Bug，只查询已结束会话的未分配
    if not args.member_id:
        print("  → 查询未分配会话...")
        unassigned_active = 0  # API Bug：sys_user_id=0 的活跃会话查询返回所有会话
        unassigned_ended = get_session_count(
            member_id=0,
            status=1,
            time_range=time_range,
            end_time_range=end_time_range
        )
        unassigned_total = unassigned_active + unassigned_ended
        
        if unassigned_total > 0:
            stats.append({
                'member_id': 0,
                'name': '未分配',
                'role': '-',
                'email': '',
                'active': unassigned_active,
                'ended': unassigned_ended,
                'total': unassigned_total,
            })
    
    # 输出统计表格
    print(f"📅 时间范围：{time_desc}")
    if args.status == 0:
        print(f"📊 会话类型：活跃会话")
    elif args.status == 1:
        print(f"📊 会话类型：已结束会话")
    else:
        print(f"📊 会话类型：活跃 + 已结束（全部）")
    print()
    
    print("📊 团队客服会话统计")
    print("=" * 100)
    print(f"{'客服':<15} {'角色':<12} {'总会话':<10} {'活跃':<8} {'已结束':<10}")
    print("-" * 100)
    
    grand_total = 0
    grand_active = 0
    grand_ended = 0
    
    for s in sorted(stats, key=lambda x: x['total'], reverse=True):
        print(f"{s['name']:<15} {s['role']:<12} {s['total']:<10} {s['active']:<8} {s['ended']:<10}")
        grand_total += s['total']
        grand_active += s['active']
        grand_ended += s['ended']
    
    print("-" * 100)
    print(f"{'总计':<15} {'':<12} {grand_total:<10} {grand_active:<8} {grand_ended:<10}")
    print("=" * 100)


if __name__ == '__main__':
    main()
