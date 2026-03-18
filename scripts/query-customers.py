#!/usr/bin/env python3
"""
SaleSmartly Customer Query

Query customer list from SaleSmartly API

API ID: 258167563e0
Endpoint: /api/v2/get-contact-list
Method: GET

Usage:
    uv run scripts/query-customers.py --page 1 --page-size 5
    uv run scripts/query-customers.py --filter-by created --days 60
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


def fetch_all_pages(api_key, project_id, start_time, end_time, page_size=100):
    """获取所有页的数据"""
    all_customers = []
    
    for page in range(1, 10):  # 最多查 10 页
        updated_time_str = json.dumps({"start": start_time, "end": end_time})
        params = {
            "project_id": project_id,
            "updated_time": updated_time_str,
            "page": str(page),
            "page_size": str(page_size)
        }
        
        sign = generate_sign(api_key, params)
        
        query_params = {
            "project_id": project_id,
            "updated_time": urllib.parse.quote(updated_time_str),
            "page": str(page),
            "page_size": str(page_size)
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
            if not customers:
                break
            
            print(f"  第 {page} 页：{len(customers)} 条")
            all_customers.extend(customers)
            
            # 如果返回少于 page_size，说明是最后一页
            if len(customers) < page_size:
                break
                
        except Exception as e:
            print(f"❌ 请求失败：{e}")
            break
    
    return all_customers


def query_customers(page: int = 1, page_size: int = 20, days: int = 30, filter_by: str = 'updated', fetch_all: bool = False):
    """
    查询客户列表
    
    Args:
        page: 页码（从 1 开始）
        page_size: 每页大小（最大 100）
        days: 查询最近 N 天的数据
        filter_by: 过滤方式 ('updated'=按更新时间，'created'=按创建时间)
        fetch_all: 是否自动获取所有页面数据
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    # 计算时间范围
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())
    
    print(f"\n📊 查询范围：{datetime.fromtimestamp(start_time).strftime('%Y-%m-%d')} 至 {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d')}")
    print(f"过滤方式：{'创建时间' if filter_by == 'created' else '更新时间'}")
    print()
    
    # 如果按创建时间过滤，需要获取所有页
    if filter_by == 'created':
        print("正在获取所有客户数据...")
        all_customers = fetch_all_pages(api_key, project_id, start_time, end_time)
        
        # 去重
        seen = set()
        unique_customers = []
        for c in all_customers:
            uid = c.get('chat_user_id')
            if uid not in seen:
                seen.add(uid)
                unique_customers.append(c)
        
        print(f"去重后总计：{len(unique_customers)} 条唯一客户\n")
        
        # 按创建时间过滤
        customers = [
            c for c in unique_customers 
            if c.get('created_time', 0) >= start_time
        ]
        customers.sort(key=lambda x: x.get('created_time', 0))
        
        total = len(customers)
        # 分页显示
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_customers = customers[start_idx:end_idx]
        
    else:
        # 按更新时间过滤（API 原生支持）
        updated_time_str = json.dumps({"start": start_time, "end": end_time})
        
        # 如果 fetch_all 为 True，获取所有页面
        if fetch_all:
            print("正在获取所有客户数据...")
            all_customers = fetch_all_pages(api_key, project_id, start_time, end_time, page_size)
            customers = all_customers
            total = len(customers)
            page = 1
            page_customers = customers
        else:
            # 只获取单页
            params = {
                "project_id": project_id,
                "updated_time": updated_time_str,
                "page": str(page),
                "page_size": str(page_size)
            }
            
            sign = generate_sign(api_key, params)
            
            query_params = {
                "project_id": project_id,
                "updated_time": urllib.parse.quote(updated_time_str),
                "page": str(page),
                "page_size": str(page_size)
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
                
                if resp_json.get('code') != 0:
                    print(f"❌ 查询失败：{resp_json.get('msg', 'Unknown error')} (code: {resp_json.get('code')})")
                    sys.exit(1)
                
                data = resp_json.get('data', {})
                customers = data.get('list', [])
                total = data.get('total', 0)
                
            except Exception as e:
                print(f"❌ 请求失败：{e}")
                sys.exit(1)
            
            page_customers = customers
    
    # 显示结果
    print(f"\n{'='*60}")
    print(f"✅ 客户查询成功！")
    print(f"{'='*60}")
    print(f"总数：{total}")
    print(f"当前页：{page}")
    print(f"每页：{page_size}")
    print(f"返回：{len(page_customers if filter_by == 'created' else customers)} 条")
    
    display_customers = page_customers if filter_by == 'created' else customers
    
    if display_customers:
        print(f"\n客户列表:")
        for i, c in enumerate(display_customers, 1):
            print(f"\n[{i}] {c.get('name', 'N/A')}")
            print(f"    ID: {c.get('chat_user_id', 'N/A')}")
            if c.get('email'):
                print(f"    邮箱：{c.get('email')}")
            if c.get('phone'):
                print(f"    电话：{c.get('phone')}")
            if c.get('country'):
                print(f"    国家：{c.get('country')}")
            if c.get('city'):
                print(f"    城市：{c.get('city')}")
            
            created = c.get('created_time')
            if created:
                created_dt = datetime.fromtimestamp(created)
                print(f"    创建：{created_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\n⚠️  未找到客户")
    
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 客户查询工具')
    parser.add_argument('--page', type=int, default=1, help='页码（从 1 开始）')
    parser.add_argument('--page-size', type=int, default=100, help='每页大小（最大 100）')
    parser.add_argument('--days', type=int, default=30, help='查询最近 N 天的数据')
    parser.add_argument('--filter-by', type=str, choices=['updated', 'created'], default='updated',
                        help='过滤方式：updated=按更新时间，created=按创建时间')
    parser.add_argument('--all', action='store_true', help='自动获取所有页面数据（当 total > page_size 时）')
    
    args = parser.parse_args()
    
    query_customers(
        page=args.page,
        page_size=args.page_size,
        days=args.days,
        filter_by=args.filter_by,
        fetch_all=args.all
    )


if __name__ == "__main__":
    main()
