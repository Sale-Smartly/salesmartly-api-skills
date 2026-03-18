#!/usr/bin/env python3
"""
SaleSmartly Link Query

API ID: 326349441e0
Endpoint: /api/v2/get-link-list
Method: GET
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


def query_links(page: int = 1, page_size: int = 20, days: int = None):
    """
    查询分流链接列表
    
    Args:
        page: 页码（从 1 开始）
        page_size: 每页大小（最大 100）
        days: 查询最近 N 天创建的链接
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    print(f"📊 查询分流链接列表")
    if days:
        print(f"时间范围：最近 {days} 天")
    print()
    
    # 构建请求参数
    params = {
        "project_id": project_id,
        "page": str(page),
        "page_size": str(page_size)
    }
    
    # 时间范围过滤
    if days:
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=days)).timestamp())
        params['created_time'] = json.dumps({"start": start_time, "end": end_time})
    
    sign = generate_sign(api_key, params)
    
    # 构建查询字符串
    query_params = dict(params)
    if 'created_time' in query_params:
        query_params['created_time'] = urllib.parse.quote(query_params['created_time'])
    
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{API_BASE_URL}/api/v2/get-link-list?{query_string}"
    
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
        
        if resp_json.get('code') != 0:
            print(f"❌ 查询失败：{resp_json.get('msg', 'Unknown error')} (code: {resp_json.get('code')})")
            sys.exit(1)
        
        data = resp_json.get('data', {})
        links = data.get('list', [])
        total = data.get('total', 0)
        
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        sys.exit(1)
    
    # 显示结果
    print(f"\n{'='*60}")
    print(f"✅ 分流链接查询成功！")
    print(f"{'='*60}")
    print(f"总数：{total}")
    print(f"当前页：{page}")
    print(f"每页：{page_size}")
    print(f"返回：{len(links)} 条")
    
    if links:
        print(f"\n链接列表:")
        for i, link in enumerate(links, 1):
            print(f"\n[{i}] 链接 ID: {link.get('id', 'N/A')}")
            
            # 链接名称
            if link.get('name'):
                print(f"    名称：{link.get('name')}")
            
            # 链接 URL
            if link.get('link'):
                print(f"    URL: {link.get('link')}")
            
            # 创建时间
            created_time = link.get('created_time')
            if created_time:
                created_dt = datetime.fromtimestamp(created_time)
                print(f"    创建时间：{created_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 更新时间
            updated_time = link.get('updated_time')
            if updated_time:
                updated_dt = datetime.fromtimestamp(updated_time)
                print(f"    更新时间：{updated_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 使用次数
            if link.get('use_count') is not None:
                print(f"    使用次数：{link.get('use_count')}")
            
            # 状态
            if link.get('status') is not None:
                status_map = {
                    0: '未激活',
                    1: '启用',
                    2: '禁用'
                }
                print(f"    状态：{status_map.get(link.get('status'), str(link.get('status')))}")
    else:
        print(f"\n⚠️  未找到分流链接")
    
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 分流链接查询工具')
    parser.add_argument('--page', type=int, default=1, help='页码（从 1 开始）')
    parser.add_argument('--page-size', type=int, default=100, help='每页大小（最大 100）')
    parser.add_argument('--all', action='store_true', help='自动获取所有页面数据（当 total > page_size 时）')
    
    parser.add_argument('--days', type=int, default=None, help='查询最近 N 天创建的链接')
    
    args = parser.parse_args()
    
    query_links(
        page=args.page,
        page_size=args.page_size,
        days=args.days
    )


if __name__ == "__main__":
    main()
