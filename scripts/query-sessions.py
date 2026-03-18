#!/usr/bin/env python3
"""
SaleSmartly Get Session List

获取会话列表 - 支持分页、状态筛选、客服筛选、时间范围筛选

API ID: 429104830e0
Endpoint: /api/v2/get-session-list
Method: GET

功能:
- 获取活跃会话或已结束会话列表
- 支持按客服 ID 筛选
- 支持按会话状态筛选
- 支持时间范围查询
- 支持分页

使用:
uv run scripts/query-sessions.py --page 1 --page-size 20
uv run scripts/query-sessions.py --status 1  # 已结束会话
uv run scripts/query-sessions.py --member 616  # 指定客服
uv run scripts/query-sessions.py --today  # 今天的会话
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

# 配置文件
CONFIG_FILE = "api-key.json"
API_BASE_URL = "https://developer.salesmartly.com"


def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 支持两种格式：
            # 1. 嵌套格式：{"salesmartly": {"apiKey": "...", "projectId": "..."}}
            # 2. 扁平格式：{"apiKey": "...", "projectId": "..."}
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


def query_sessions(page: int = 1, page_size: int = 10, status: int = 0, 
                   sub_status: int = None, member_id: int = None,
                   time_range: str = None, end_time_range: str = None):
    """
    获取会话列表
    
    Args:
        page: 页码（从 1 开始）
        page_size: 每页数量（最大 100）
        status: 会话状态（0=活跃，1=已结束）
        sub_status: 子状态（0=全部，1=未分配，2=机器人接待）
        member_id: 客服 ID（sys_user_id）
        time_range: 开始时间范围（JSON 字符串）
        end_time_range: 结束时间范围（JSON 字符串，仅当 status=1 时有效）
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
        'session_status': status,
    }
    
    # 可选参数
    if sub_status is not None:
        params['sub_status'] = sub_status
    
    if member_id is not None:
        params['sys_user_id'] = member_id
    
    if time_range:
        params['start_time'] = time_range
    
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
        # 注意：如果系统 SSL 证书有问题，使用 CERT_NONE
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            raw_data = response.read().decode('utf-8')
            
            # 调试模式：打印原始响应
            if '--debug' in sys.argv:
                print("🔍 原始响应:")
                print(raw_data[:500])
                print("...")
            
            # API 可能返回多个 JSON（频率限制等），只解析第一个
            # 找到第一个完整的 JSON 对象
            try:
                result = json.loads(raw_data)
            except json.JSONDecodeError:
                # 尝试找到第一个 } 并解析
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
                return result.get('data', {})
            else:
                print(f"❌ API 请求失败：{result.get('msg', '未知错误')}")
                print(f"请求 ID: {result.get('request_id', 'N/A')}")
                sys.exit(1)
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误：{e.code}")
        print(f"响应：{e.read().decode('utf-8')}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络错误：{e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误：{e}")
        sys.exit(1)


def format_sessions(data: dict, verbose: bool = False):
    """格式化输出会话列表"""
    sessions = data.get('list', [])
    total = data.get('total', 0)
    page = data.get('page', 1)
    page_size = data.get('page_size', 10)
    
    if not sessions:
        print("💬 暂无会话数据")
        return
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    
    print(f"💬 会话列表 - 第 {page}/{total_pages} 页（共 {total} 条）")
    print("=" * 100)
    
    # 表头
    print(f"{'会话 ID':<20} {'客户 ID':<26} {'客服 ID':<8} {'状态':<8} {'消息数':<8} {'开始时间':<20}")
    print("-" * 100)
    
    # 会话数据
    for session in sessions:
        session_id = session.get('session_id', 'N/A')[:18]
        chat_user_id = session.get('chat_user_id', 'N/A')[:24]
        sys_user_id = session.get('sys_user_id', '未分配')
        
        # 会话状态
        status = session.get('session_status', 0)
        status_text = "已结束" if status == 1 else "进行中"
        
        # 消息数
        msg_count = session.get('msg_count', 0)
        user_msg = session.get('user_msg_count', 0)
        customer_msg = session.get('customer_msg_count', 0)
        
        # 开始时间
        start_time = session.get('start_time', 0)
        start_str = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S') if start_time else 'N/A'
        
        # 结束时间（仅已结束会话）
        end_time = session.get('end_time', 0)
        end_str = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S') if end_time and status == 1 else ''
        
        print(f"{session_id:<20} {chat_user_id:<26} {str(sys_user_id):<8} {status_text:<8} {msg_count:<8} {start_str:<20}")
        
        if verbose:
            # 详细信息
            title = session.get('title', '')
            tags = session.get('tags', '')
            assign_time = session.get('assign_time', 0)
            assign_str = datetime.fromtimestamp(assign_time).strftime('%Y-%m-%d %H:%M:%S') if assign_time else 'N/A'
            
            print(f"  标题：{title}")
            print(f"  标签：{tags}")
            print(f"  分配时间：{assign_str}")
            if status == 1:
                print(f"  结束时间：{end_str}")
            print("-" * 100)
    
    print("=" * 100)
    print(f"📊 统计：客户消息 {sum(s.get('customer_msg_count', 0) for s in sessions)} | "
          f"客服消息 {sum(s.get('user_msg_count', 0) for s in sessions)}")


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 会话列表查询')
    
    # 分页参数
    parser.add_argument('--page', type=int, default=1, help='页码（从 1 开始，默认 1）')
    parser.add_argument('--page-size', type=int, default=10, help='每页数量（最大 100，默认 10）')
    
    # 筛选参数
    parser.add_argument('--status', type=int, default=0, choices=[0, 1], 
                        help='会话状态（0=活跃，1=已结束，默认 0）')
    parser.add_argument('--sub-status', type=int, choices=[0, 1, 2],
                        help='子状态（0=全部，1=未分配，2=机器人接待）')
    parser.add_argument('--member', type=int, dest='member_id',
                        help='客服 ID（sys_user_id）')
    
    # 时间参数
    parser.add_argument('--today', action='store_true', help='查询今天的会话')
    parser.add_argument('--yesterday', action='store_true', help='查询昨天的会话')
    parser.add_argument('--days', type=int, help='查询最近 N 天的会话')
    parser.add_argument('--start-date', type=str, help='开始日期（YYYY-MM-DD）')
    parser.add_argument('--end-date', type=str, help='结束日期（YYYY-MM-DD）')
    
    # 输出选项
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    parser.add_argument('--debug', action='store_true', help='调试模式（打印原始响应）')
    
    args = parser.parse_args()
    
    # 验证参数
    if args.page_size > 100:
        print("⚠️  page_size 最大为 100，已自动调整为 100")
        args.page_size = 100
    
    # 解析时间范围
    time_range = None
    end_time_range = None
    
    if args.today:
        today = datetime.now().strftime('%Y-%m-%d')
        time_range = parse_time_range(start_date=today, end_date=today)
    elif args.yesterday:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        time_range = parse_time_range(start_date=yesterday, end_date=yesterday)
    elif args.days:
        time_range = parse_time_range(days=args.days)
    elif args.start_date:
        time_range = parse_time_range(start_date=args.start_date, 
                                      end_date=args.end_date)
    
    # 调用 API
    data = query_sessions(
        page=args.page,
        page_size=args.page_size,
        status=args.status,
        sub_status=args.sub_status,
        member_id=args.member_id,
        time_range=time_range,
        end_time_range=end_time_range
    )
    
    # 输出结果
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        format_sessions(data, verbose=args.verbose)


if __name__ == '__main__':
    main()
