#!/usr/bin/env python3
"""
SaleSmartly Member Session Stats

团队客服会话统计 - 统计指定时间范围内每个成员的接待会话数

API: 
- /api/v2/get-member-list (310397215e0)
- /api/v2/get-session-list (429104830e0)

功能:
- 统计每个客服的会话总数
- 支持按时间范围筛选
- 支持分别统计活跃/已结束会话
- 支持显示详细数据（消息数、评分等）

使用:
uv run scripts/member-session-stats.py --days 7
uv run scripts/member-session-stats.py --today
uv run scripts/member-session-stats.py --status 0  # 只看活跃
uv run scripts/member-session-stats.py --status 1  # 只看已结束
uv run scripts/member-session-stats.py --days 30 --verbose
"""


import sys
import json
import hashlib
import argparse
import urllib.request
import urllib.parse
import ssl
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# 配置文件
CONFIG_FILE = "api-key.json"
API_BASE_URL = "https://developer.salesmartly.com"


def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 支持两种格式：嵌套格式和扁平格式
            if 'salesmartly' in config:
                return config['salesmartly'].get('apiKey'), config['salesmartly'].get('projectId')
            else:
                return config.get('apiKey'), config.get('projectId')
    except Exception as e:
        print(f"❌ 加载配置文件失败：{e}")
        print(f"提示：请确保 {CONFIG_FILE} 文件存在且格式正确")
        sys.exit(1)


def generate_sign(api_key: str, params: dict) -> str:
    """
    生成接口签名
    
    签名规则：
    1. 将所有参数按 key 的 ASCII 码从小到大排序
    2. 以 api_key 开头，拼接 key=value 格式
    3. 用 & 连接所有参数
    4. 对拼接后的字符串进行 MD5 加密
    """
    # 过滤空值参数
    filtered_params = {k: v for k, v in params.items() if v is not None and v != ''}
    
    # 按 key 排序
    sorted_params = sorted(filtered_params.items(), key=lambda x: x[0])
    
    # 生成签名（api_key 开头）
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    
    # 拼接并生成 MD5
    sign_str = "&".join(sign_parts)
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    return sign


def parse_time_range(days: int = None, start_date: str = None, end_date: str = None):
    """
    解析时间范围
    
    返回：{"start": timestamp, "end": timestamp} 格式的 JSON 字符串
    """
    now = datetime.now()
    
    if days:
        # 最近 N 天
        start = now - timedelta(days=days)
        start_ts = int(start.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        end_ts = int(now.timestamp())
    elif start_date and end_date:
        # 指定日期范围
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
    elif start_date:
        # 只指定开始日期
        start = datetime.strptime(start_date, "%Y-%m-%d")
        start_ts = int(start.timestamp())
        end_ts = int(now.timestamp())
    else:
        return None
    
    return json.dumps({"start": start_ts, "end": end_ts})


def get_member_list(page: int = 1, page_size: int = 100):
    """
    获取团队成员列表
    
    API: /api/v2/get-member-list
    """
    api_key, project_id = load_config()
    
    if not project_id:
        print("❌ 配置文件中缺少 projectId")
        sys.exit(1)
    
    # 构建请求参数
    params = {
        'page': page,
        'page_size': page_size,
        'project_id': project_id,
    }
    
    # 生成签名
    sign = generate_sign(api_key, params)
    
    # 构建 URL
    query_string = urllib.parse.urlencode(params)
    url = f"{API_BASE_URL}/api/v2/get-member-list?{query_string}"
    
    # 创建请求
    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json')
    req.add_header('external-sign', sign)
    req.add_header('User-Agent', 'SaleSmartly-Agent/1.0')
    
    try:
        # 发送请求
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            raw_data = response.read().decode('utf-8')
            
            # API 可能返回多个 JSON，只解析第一个
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
                
                if end_pos > 0:
                    result = json.loads(raw_data[:end_pos])
                else:
                    raise
            
            if result.get('code') == 0:
                return result.get('data', {}).get('list', [])
            else:
                print(f"❌ 获取成员列表失败：{result.get('msg', '未知错误')}")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ 网络错误：{e}")
        sys.exit(1)


def get_session_stats(member_id: int = None, status: int = None, time_range: str = None, end_time_range: str = None):
    """
    获取会话统计（支持分页获取所有数据）
    
    API: /api/v2/get-session-list
    
    Args:
        member_id: 客服 ID（可选，不传则获取所有）
        status: 会话状态（0=活跃，1=已结束，None=全部）
        time_range: 开始时间范围（JSON 字符串）
        end_time_range: 结束时间范围（JSON 字符串，仅当查询已结束会话时需要）
    
    Returns:
        dict: {member_id: {'total': 总数， 'active': 活跃数， 'ended': 已结束数， 'sessions': [...]}}
    """
    api_key, project_id = load_config()
    
    if not project_id:
        print("❌ 配置文件中缺少 projectId")
        sys.exit(1)
    
    all_sessions = []
    page = 1
    page_size = 100  # 最大页数，减少请求次数
    
    while True:
        # 构建请求参数
        params = {
            'page': page,
            'page_size': page_size,
            'project_id': project_id,
        }
        
        # 可选参数
        if member_id is not None:
            params['sys_user_id'] = member_id
        
        if status is not None:
            params['session_status'] = status
        
        if time_range:
            params['start_time'] = time_range
        
        # 已结束会话需要 end_time 参数
        if end_time_range and status == 1:
            params['end_time'] = end_time_range
        
        # 生成签名
        sign = generate_sign(api_key, params)
        
        # 构建 URL
        query_string = urllib.parse.urlencode(params)
        url = f"{API_BASE_URL}/api/v2/get-session-list?{query_string}"
        
        # 创建请求
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json')
        req.add_header('external-sign', sign)
        req.add_header('User-Agent', 'SaleSmartly-Agent/1.0')
        
        try:
            # 发送请求
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                raw_data = response.read().decode('utf-8')
                
                # API 可能返回多个 JSON，只解析第一个
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
                    
                    if end_pos > 0:
                        result = json.loads(raw_data[:end_pos])
                    else:
                        raise
                
                if result.get('code') == 0:
                    data = result.get('data', {})
                    sessions = data.get('list', [])
                    total = data.get('total', 0)
                    
                    if not sessions:
                        break
                    
                    all_sessions.extend(sessions)
                    
                    # 如果返回少于 page_size，说明是最后一页
                    if len(sessions) < page_size:
                        break
                    
                    # 如果已获取的数据达到总数，停止
                    if len(all_sessions) >= total:
                        break
                    
                    page += 1
                else:
                    print(f"❌ 获取会话列表失败：{result.get('msg', '未知错误')}")
                    break
                    
        except Exception as e:
            print(f"❌ 网络错误：{e}")
            break
    
    return all_sessions


def format_stats(members: list, sessions: list, status_filter: int = None, verbose: bool = False):
    """格式化输出统计结果"""
    
    # 构建成员映射
    member_map = {}
    for member in members:
        mid = member.get('id') or member.get('sys_user_id')
        if mid:
            member_map[mid] = {
                'name': member.get('name', '未知'),
                'role': member.get('role', '普通成员'),
                'email': member.get('email', ''),
            }
    
    # 统计每个成员的会话
    stats = defaultdict(lambda: {
        'total': 0,
        'active': 0,
        'ended': 0,
        'msg_count': 0,
        'user_msg_count': 0,
        'customer_msg_count': 0,
        'sessions': []
    })
    
    for session in sessions:
        sys_user_id = session.get('sys_user_id')
        if not sys_user_id:
            continue
        
        # 判断会话状态：有 end_time 且不为 0 表示已结束
        end_time = session.get('end_time', 0)
        session_status = 1 if (end_time and end_time > 0) else 0
        
        msg_count = session.get('msg_count', 0)
        
        stats[sys_user_id]['total'] += 1
        if session_status == 0:
            stats[sys_user_id]['active'] += 1
        else:
            stats[sys_user_id]['ended'] += 1
        
        stats[sys_user_id]['msg_count'] += msg_count
        stats[sys_user_id]['user_msg_count'] += session.get('user_msg_count', 0)
        stats[sys_user_id]['customer_msg_count'] += session.get('customer_msg_count', 0)
        
        if verbose:
            stats[sys_user_id]['sessions'].append({
                'session_id': session.get('session_id'),
                'status': '活跃' if session_status == 0 else '已结束',
                'msg_count': msg_count,
                'start_time': session.get('start_time'),
            })
    
    # 输出统计
    print("\n📊 团队客服会话统计")
    print("=" * 120)
    
    # 表头
    if status_filter is None:
        print(f"{'客服':<15} {'角色':<12} {'总会话':<10} {'活跃':<8} {'已结束':<10} {'消息总数':<10} {'客户消息':<10} {'客服消息':<10}")
    else:
        status_text = "活跃" if status_filter == 0 else "已结束"
        print(f"{'客服':<15} {'角色':<12} {'会话数':<10} {'消息总数':<10} {'客户消息':<10} {'客服消息':<10}")
    
    print("-" * 120)
    
    # 按会话数排序
    sorted_members = sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True)
    
    total_sessions = 0
    total_active = 0
    total_ended = 0
    total_msgs = 0
    
    for member_id, data in sorted_members:
        member_info = member_map.get(member_id, {'name': f'客服{member_id}', 'role': '未知'})
        name = member_info['name']
        role = member_info['role']
        
        if status_filter is None:
            print(f"{name:<15} {role:<12} {data['total']:<10} {data['active']:<8} {data['ended']:<10} {data['msg_count']:<10} {data['customer_msg_count']:<10} {data['user_msg_count']:<10}")
        else:
            print(f"{name:<15} {role:<12} {data['total']:<10} {data['msg_count']:<10} {data['customer_msg_count']:<10} {data['user_msg_count']:<10}")
        
        total_sessions += data['total']
        total_active += data['active']
        total_ended += data['ended']
        total_msgs += data['msg_count']
    
    print("-" * 120)
    
    # 总计
    if status_filter is None:
        print(f"{'总计':<15} {'':<12} {total_sessions:<10} {total_active:<8} {total_ended:<10} {total_msgs:<10}")
    else:
        status_text = "活跃" if status_filter == 0 else "已结束"
        print(f"{'总计':<15} {'':<12} {total_sessions:<10} {total_msgs:<10}")
    
    print("=" * 120)
    
    # 详细信息
    if verbose:
        print("\n📋 详细会话列表")
        print("=" * 120)
        
        for member_id, data in sorted_members:
            member_info = member_map.get(member_id, {'name': f'客服{member_id}'})
            name = member_info['name']
            
            print(f"\n{name}（共 {data['total']} 个会话）:")
            for session in data['sessions'][:10]:  # 只显示前 10 个
                session_id = session.get('session_id', 'N/A')
                status = session.get('status', 'N/A')
                msg_count = session.get('msg_count', 0)
                start_time = session.get('start_time', 0)
                start_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S') if start_time else 'N/A'
                
                print(f"  - {session_id} [{status}] {msg_count}条消息 {start_str}")
            
            if len(data['sessions']) > 10:
                print(f"  ... 还有 {len(data['sessions']) - 10} 个会话")
        
        print("=" * 120)


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 团队客服会话统计')
    
    # 时间参数
    parser.add_argument('--today', action='store_true', help='统计今天的会话')
    parser.add_argument('--yesterday', action='store_true', help='统计昨天的会话')
    parser.add_argument('--days', type=int, help='统计最近 N 天的会话')
    parser.add_argument('--start-date', type=str, help='开始日期（YYYY-MM-DD）')
    parser.add_argument('--end-date', type=str, help='结束日期（YYYY-MM-DD）')
    
    # 状态筛选
    parser.add_argument('--status', type=int, choices=[0, 1], 
                        help='会话状态（0=活跃，1=已结束，不传则统计全部）')
    
    # 成员筛选
    parser.add_argument('--member', type=int, dest='member_id',
                        help='指定客服 ID（不传则统计所有成员）')
    
    # 输出选项
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细会话列表')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    
    args = parser.parse_args()
    
    # 解析时间范围
    time_range = None
    end_time_range = None
    time_desc = ""
    
    if args.today:
        today = datetime.now().strftime('%Y-%m-%d')
        time_range = parse_time_range(start_date=today, end_date=today)
        end_time_range = time_range  # 已结束会话也用相同的时间范围
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
        time_range = parse_time_range(start_date=args.start_date, 
                                      end_date=args.end_date)
        end_time_range = time_range
        time_desc = f"{args.start_date} 至 {args.end_date or '今天'}"
    else:
        time_desc = "全部时间"
    
    # 获取成员列表
    print(f"⏳ 正在获取团队成员列表...")
    members = get_member_list()
    print(f"✅ 共 {len(members)} 个成员")
    
    # 获取会话数据
    all_sessions = []
    
    if args.status is not None:
        # 查询单一状态（活跃或已结束）
        if args.member_id:
            print(f"⏳ 正在获取客服 {args.member_id} 的会话数据...")
        else:
            print(f"⏳ 正在获取所有成员的会话数据...")
        
        if time_desc:
            print(f"📅 时间范围：{time_desc}")
        
        status_text = "活跃" if args.status == 0 else "已结束"
        print(f"📊 会话类型：{status_text}")
        
        all_sessions = get_session_stats(
            member_id=args.member_id,
            status=args.status,
            time_range=time_range,
            end_time_range=end_time_range
        )
    else:
        # 查询全部状态（活跃 + 已结束）- 分两次查询
        print(f"⏳ 正在获取所有成员的会话数据...")
        if time_desc:
            print(f"📅 时间范围：{time_desc}")
        print(f"📊 会话类型：活跃 + 已结束（全部）")
        
        # 查询活跃会话
        print("  → 查询活跃会话...")
        active_sessions = get_session_stats(
            member_id=args.member_id,
            status=0,
            time_range=time_range
        )
        print(f"    ✅ 活跃会话：{len(active_sessions)} 个")
        
        # 查询已结束会话
        print("  → 查询已结束会话...")
        ended_sessions = get_session_stats(
            member_id=args.member_id,
            status=1,
            time_range=time_range,
            end_time_range=end_time_range
        )
        print(f"    ✅ 已结束会话：{len(ended_sessions)} 个")
        
        # 合并
        all_sessions = active_sessions + ended_sessions
    
    print(f"✅ 共获取 {len(all_sessions)} 个会话")
    
    # 输出结果
    if args.json:
        # JSON 输出
        result = {
            'time_range': time_desc,
            'status_filter': args.status,
            'total_sessions': len(all_sessions),
            'members': [],
        }
        
        # 构建成员映射
        member_map = {m.get('id') or m.get('sys_user_id'): m for m in members}
        
        # 统计
        stats = defaultdict(lambda: {'total': 0, 'active': 0, 'ended': 0})
        for session in all_sessions:
            sys_user_id = session.get('sys_user_id')
            if not sys_user_id:
                continue
            
            stats[sys_user_id]['total'] += 1
            if session.get('session_status', 0) == 0:
                stats[sys_user_id]['active'] += 1
            else:
                stats[sys_user_id]['ended'] += 1
        
        for member_id, data in stats.items():
            member_info = member_map.get(member_id, {})
            result['members'].append({
                'member_id': member_id,
                'name': member_info.get('name', '未知'),
                'role': member_info.get('role', '普通成员'),
                'total': data['total'],
                'active': data['active'],
                'ended': data['ended'],
            })
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 表格输出
        format_stats(members, all_sessions, status_filter=args.status, verbose=args.verbose)


if __name__ == '__main__':
    main()
