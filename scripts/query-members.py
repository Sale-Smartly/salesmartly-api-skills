#!/usr/bin/env python3
"""
SalesSmartly Member Query

API ID: 310397215e0
Endpoint: /api/v2/get-member-list
Method: GET
"""

import sys
import json
import hashlib
import argparse
import urllib.request
import urllib.parse
import ssl
from datetime import datetime

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
    """生成 SalesSmartly API 签名（MD5）"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()


def query_members(page: int = 1, page_size: int = 20, status: str = None):
    """
    查询团队成员列表
    
    Args:
        page: 页码（从 1 开始）
        page_size: 每页大小（最大 100）
        status: 状态过滤 (active=活跃，inactive=非活跃，all=全部)
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    print(f"📊 查询团队成员")
    if status:
        print(f"状态过滤：{status}")
    print()
    
    # 构建请求
    params = {
        "project_id": project_id,
        "page": str(page),
        "page_size": str(page_size)
    }
    
    # 如果指定了状态，添加过滤
    if status and status != 'all':
        params['status'] = '1' if status == 'active' else '0'
    
    sign = generate_sign(api_key, params)
    
    query_params = dict(params)
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{API_BASE_URL}/api/v2/get-member-list?{query_string}"
    
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
        
        if resp_json.get('code') != 0:
            print(f"❌ 查询失败：{resp_json.get('msg', 'Unknown error')} (code: {resp_json.get('code')})")
            sys.exit(1)
        
        data = resp_json.get('data', {})
        members = data.get('list', [])
        total = data.get('total', 0)
        
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        sys.exit(1)
    
    # 显示结果
    print(f"\n{'='*60}")
    print(f"✅ 团队成员查询成功！")
    print(f"{'='*60}")
    print(f"总数：{total}")
    print(f"当前页：{page}")
    print(f"每页：{page_size}")
    print(f"返回：{len(members)} 条")
    
    if members:
        print(f"\n成员列表:")
        for i, m in enumerate(members, 1):
            print(f"\n[{i}] {m.get('nickname', m.get('member_name', m.get('name', 'N/A')))}")
            print(f"    成员 ID: {m.get('id', m.get('member_id', 'N/A'))}")
            
            # 邮箱
            if m.get('email'):
                print(f"    邮箱：{m.get('email')}")
            
            # 手机号
            if m.get('mobile') or m.get('phone'):
                print(f"    手机：{m.get('mobile', m.get('phone'))}")
            
            # 状态
            member_status = m.get('status')
            status_text = '活跃' if str(member_status) == '1' else '非活跃'
            print(f"    状态：{status_text}")
            
            # 角色
            role = m.get('role') or m.get('role_id')
            if role:
                role_map = {
                    '1': '管理员',
                    '2': '普通成员',
                    '3': '访客'
                }
                print(f"    角色：{role_map.get(str(role), str(role))}")
            
            # 最后登录时间
            last_login = m.get('last_login_time')
            if last_login:
                last_login_dt = datetime.fromtimestamp(last_login)
                print(f"    最后登录：{last_login_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 创建时间
            created_time = m.get('created_time') or m.get('add_time')
            if created_time:
                created_dt = datetime.fromtimestamp(created_time)
                print(f"    加入时间：{created_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\n⚠️  未找到成员")
    
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='SalesSmartly 团队成员查询工具')
    parser.add_argument('--page', type=int, default=1, help='页码（从 1 开始）')
    parser.add_argument('--page-size', type=int, default=20, help='每页大小（最大 100）')
    parser.add_argument('--status', type=str, choices=['active', 'inactive', 'all'], 
                        default=None, help='状态过滤：active=活跃，inactive=非活跃，all=全部')
    
    args = parser.parse_args()
    
    query_members(
        page=args.page,
        page_size=args.page_size,
        status=args.status
    )


if __name__ == "__main__":
    main()
