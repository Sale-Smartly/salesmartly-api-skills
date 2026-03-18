#!/usr/bin/env python3
"""
SaleSmartly Session List Query

Query session list from SaleSmartly API

API ID: 429104830e0
Endpoint: /api/v2/get-session-list
Method: GET

Usage:
    # 基础查询 - 获取活跃会话
    uv run scripts/query-sessions.py --page 1 --page-size 5

    # 获取已结束会话
    uv run scripts/query-sessions.py --session-status ended --page-size 10

    # 按客服 ID 筛选
    uv run scripts/query-sessions.py --sys-user-id 1366 --page-size 10

    # 按时间范围筛选（最近 7 天）
    uv run scripts/query-sessions.py --days 7 --page-size 10

    # 组合筛选 - 已结束会话 + 时间范围
    uv run scripts/query-sessions.py --session-status ended --days 30 --page-size 10
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
# 可通过 --config 参数指定，默认使用 api-key.json
# 测试环境配置：api-key-dev.json
DEFAULT_CONFIG_FILE = "api-key.json"
# API 基础 URL - 默认使用正式环境，可通过环境变量覆盖
# 测试环境：https://developer-dev.salesmartly.com
import os
API_BASE_URL = os.environ.get("SALESMARTLY_API_URL", "https://developer.salesmartly.com")


def load_config(config_file: str = DEFAULT_CONFIG_FILE):
    """加载配置文件"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('apiKey'), config.get('projectId')
    except Exception as e:
        print(f"❌ 读取配置文件失败：{e}")
        sys.exit(1)


def generate_sign(api_key: str, params: dict) -> str:
    """生成 SaleSmartly API 签名（MD5）
    
    规则：
    1. API Token 放最前面
    2. 参数按字母顺序排序
    3. 用 & 连接成字符串
    4. MD5 加密（32 位小写）
    """
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()


def query_sessions(page: int = 1, page_size: int = 10, session_status: str = 'active',
                   sys_user_id: int = None, days: int = None,
                   start_time: int = None, end_time: int = None,
                   config_file: str = DEFAULT_CONFIG_FILE):
    """
    查询会话列表
    
    Args:
        page: 页码（从 1 开始）
        page_size: 每页大小（最大 100）
        session_status: 会话状态 ('active'=活跃，'ended'=已结束)
        sys_user_id: 客服 ID（可选）
        days: 查询最近 N 天的数据（可选）
        start_time: 开始时间戳（可选，与 days 互斥）
        end_time: 结束时间戳（可选，与 days 互斥）
        config_file: 配置文件路径
    """
    api_key, project_id = load_config(config_file)
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    # 构建基础参数
    params = {
        "page": str(page),
        "page_size": str(page_size),
        "project_id": project_id
    }
    
    # 会话状态转换
    # 文档说明：0=活跃会话（默认），1=已结束会话
    if session_status == 'ended':
        params["session_status"] = "1"
    else:
        params["session_status"] = "0"
    
    # 客服 ID 筛选
    if sys_user_id:
        params["sys_user_id"] = str(sys_user_id)
    
    # 时间范围处理
    # 文档说明：时间参数必须是 JSON 格式的时间戳字符串
    # 格式：{"start":1626256341,"end":1626256341}
    if days:
        # 计算时间范围
        end_ts = int(datetime.now().timestamp())
        start_ts = int((datetime.now() - timedelta(days=days)).timestamp())
    elif start_time and end_time:
        start_ts = start_time
        end_ts = end_time
    else:
        start_ts = None
        end_ts = None
    
    # 添加时间参数（仅当 session_status=1 时 end_time 才有效）
    if start_ts:
        time_json = json.dumps({"start": start_ts, "end": end_ts})
        params["start_time"] = time_json
        if session_status == 'ended':
            params["end_time"] = time_json
    
    # 生成签名
    sign = generate_sign(api_key, params)
    
    # 构建 URL（需要对 JSON 格式的参数进行 URL 编码）
    query_params = {}
    for k, v in params.items():
        if k in ['start_time', 'end_time']:
            # JSON 格式的参数需要 URL 编码
            query_params[k] = urllib.parse.quote(v)
        else:
            query_params[k] = v
    
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{API_BASE_URL}/api/v2/get-session-list?{query_string}"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SaleSmartly-Agent/1.0",
        "external-sign": sign
    }
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    # 打印请求信息
    print("\n" + "="*80)
    print("📊 SaleSmartly 会话列表查询")
    print("="*80)
    print(f"\n📍 请求 URL:")
    print(f"   {url}")
    print(f"\n📤 请求参数:")
    print(f"   页码：{page}")
    print(f"   每页：{page_size}")
    print(f"   会话状态：{'已结束' if session_status == 'ended' else '活跃'}")
    if sys_user_id:
        print(f"   客服 ID: {sys_user_id}")
    if start_ts:
        print(f"   时间范围：{datetime.fromtimestamp(start_ts).strftime('%Y-%m-%d %H:%M:%S')} 至 {datetime.fromtimestamp(end_ts).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n🔐 签名：{sign}")
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            raw_data = response.read().decode('utf-8')
            # 可能返回多个 JSON（频率限制警告），只取第一个完整对象
            if '}{' in raw_data:
                # 找到第一个完整的 JSON 对象
                brace_count = 0
                end_idx = 0
                for i, c in enumerate(raw_data):
                    if c == '{':
                        brace_count += 1
                    elif c == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                raw_data = raw_data[:end_idx]
            resp_json = json.loads(raw_data)
        
        if resp_json.get('code') != 0:
            print(f"\n❌ 查询失败：{resp_json.get('msg', 'Unknown error')} (code: {resp_json.get('code')})")
            sys.exit(1)
        
        data = resp_json.get('data', {})
        sessions = data.get('list', [])
        total = data.get('total', 0)
        page = data.get('page', 1)
        page_size = data.get('page_size', 10)
        
        # 显示结果
        print("\n" + "="*80)
        print("✅ 会话查询成功！")
        print("="*80)
        print(f"总数：{total}")
        print(f"当前页：{page}")
        print(f"每页：{page_size}")
        print(f"返回：{len(sessions)} 条")
        
        if sessions:
            print(f"\n会话列表:")
            for i, s in enumerate(sessions, 1):
                print(f"\n[{i}] {s.get('title', 'N/A') or '无标题'}")
                print(f"    用户 ID: {s.get('chat_user_id', 'N/A')}")
                print(f"    会话 ID: {s.get('session_id', 'N/A')}")
                
                # 渠道信息
                channel = s.get('channel', 0)
                channel_map = {1: '网页', 2: 'WhatsApp', 7: 'Facebook', 15: 'Instagram'}
                print(f"    渠道：{channel_map.get(channel, f'Channel {channel}')}")
                
                # 客服 ID
                sys_uid = s.get('sys_user_id', 0)
                if sys_uid:
                    print(f"    客服 ID: {sys_uid}")
                
                # 时间信息
                start_time = s.get('start_time')
                if start_time:
                    start_dt = datetime.fromtimestamp(start_time)
                    print(f"    开始：{start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                
                end_time = s.get('end_time')
                if end_time and end_time > 0:
                    end_dt = datetime.fromtimestamp(end_time)
                    print(f"    结束：{end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                elif end_time == 0:
                    print(f"    状态：🟢 进行中")
                
                # 消息统计
                msg_count = s.get('msg_count', 0)
                user_msg = s.get('user_msg_count', 0)
                customer_msg = s.get('customer_msg_count', 0)
                if msg_count > 0:
                    print(f"    消息：{msg_count} (客服：{user_msg}, 客户：{customer_msg})")
                
                # 标签
                tags = s.get('tags')
                if tags and tags != '<nil>':
                    print(f"    标签：{tags}")
        else:
            print(f"\n⚠️  未找到会话")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"\n❌ 请求失败：{e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 会话列表查询工具')
    parser.add_argument('--page', type=int, default=1, help='页码（从 1 开始）')
    parser.add_argument('--page-size', type=int, default=10, help='每页大小（最大 100）')
    parser.add_argument('--all', action='store_true', help='自动获取所有页面数据（当 total > page_size 时）')
    
    parser.add_argument('--session-status', type=str, choices=['active', 'ended'], default='active',
                        help='会话状态：active=活跃会话，ended=已结束会话')
    parser.add_argument('--sys-user-id', type=int, help='客服 ID（筛选指定客服的会话）')
    parser.add_argument('--days', type=int, help='查询最近 N 天的数据')
    parser.add_argument('--start-time', type=int, help='开始时间戳（Unix 时间戳，秒级）')
    parser.add_argument('--end-time', type=int, help='结束时间戳（Unix 时间戳，秒级）')
    parser.add_argument('--config', type=str, default=DEFAULT_CONFIG_FILE, help='配置文件路径（默认：api-key.json）')
    
    args = parser.parse_args()
    
    query_sessions(
        page=args.page,
        page_size=args.page_size,
        session_status=args.session_status,
        sys_user_id=args.sys_user_id,
        days=args.days,
        start_time=args.start_time,
        end_time=args.end_time,
        config_file=args.config
    )


if __name__ == "__main__":
    main()
