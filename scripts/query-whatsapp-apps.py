#!/usr/bin/env python3
"""
SaleSmartly WhatsApp Device Query

API ID: 326572731e0
Endpoint: /api/v2/get-individual-whatsapp-list
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
    """生成 SaleSmartly API 签名（MD5）"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()


def query_whatsapp_apps(page: int = 1, page_size: int = 20, status: int = None,
                        name: str = None, phone_number: str = None, 
                        remark: str = None, id: str = None):
    """
    查询 WhatsApp APP 列表
    
    Args:
        page: 页码（从 1 开始）
        page_size: 每页大小（最大 100）
        status: 设备状态 0-未连接 1-有效 2-无效
        name: WhatsApp app 名称
        phone_number: 手机号码
        remark: 备注
        id: 云设备 id
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    print(f"📊 查询 WhatsApp APP 列表")
    if status is not None:
        status_map = {0: '未连接', 1: '有效', 2: '无效'}
        print(f"状态过滤：{status_map.get(status, str(status))}")
    if name:
        print(f"名称过滤：{name}")
    if phone_number:
        print(f"手机号过滤：{phone_number}")
    if remark:
        print(f"备注过滤：{remark}")
    if id:
        print(f"设备 ID 过滤：{id}")
    print()
    
    # 构建请求参数
    params = {
        "project_id": project_id,
        "page": str(page),
        "page_size": str(page_size)
    }
    
    # 可选过滤参数
    if status is not None:
        params['status'] = str(status)
    if name:
        params['name'] = name
    if phone_number:
        params['phone_number'] = phone_number
    if remark:
        params['remark'] = remark
    if id:
        params['id'] = id
    
    sign = generate_sign(api_key, params)
    
    # 构建查询字符串
    query_params = dict(params)
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{API_BASE_URL}/api/v2/get-individual-whatsapp-list?{query_string}"
    
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
        apps = data.get('list', [])
        total = data.get('total', 0)
        
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        sys.exit(1)
    
    # 显示结果
    print(f"\n{'='*60}")
    print(f"✅ WhatsApp APP 查询成功！")
    print(f"{'='*60}")
    print(f"总数：{total}")
    print(f"当前页：{page}")
    print(f"每页：{page_size}")
    print(f"返回：{len(apps)} 条")
    
    if apps:
        print(f"\n设备列表:")
        for i, app in enumerate(apps, 1):
            print(f"\n[{i}] 设备 ID: {app.get('id', 'N/A')}")
            
            # 设备名称
            if app.get('name'):
                print(f"    名称：{app.get('name')}")
            
            # 手机号码
            if app.get('phone_number'):
                print(f"    手机号：{app.get('phone_number')}")
            
            # 备注
            if app.get('remark'):
                print(f"    备注：{app.get('remark')}")
            
            # 状态
            app_status = app.get('status')
            status_map = {0: '未连接', 1: '有效', 2: '无效'}
            print(f"    状态：{status_map.get(app_status, str(app_status))}")
            
            # 创建时间
            created_time = app.get('created_time')
            if created_time:
                created_dt = datetime.fromtimestamp(created_time)
                print(f"    创建时间：{created_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 更新时间
            updated_time = app.get('updated_time')
            if updated_time:
                updated_dt = datetime.fromtimestamp(updated_time)
                print(f"    更新时间：{updated_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 创建设备的成员 ID
            if app.get('sys_user_id'):
                print(f"    创建成员 ID: {app.get('sys_user_id')}")
    else:
        print(f"\n⚠️  未找到 WhatsApp 设备")
    
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly WhatsApp APP 查询工具')
    parser.add_argument('--page', type=int, default=1, help='页码（从 1 开始）')
    parser.add_argument('--page-size', type=int, default=20, help='每页大小（最大 100）')
    parser.add_argument('--status', type=int, choices=[0, 1, 2], default=None, 
                        help='设备状态：0-未连接 1-有效 2-无效')
    parser.add_argument('--name', type=str, default=None, help='WhatsApp app 名称')
    parser.add_argument('--phone-number', type=str, default=None, help='手机号码')
    parser.add_argument('--remark', type=str, default=None, help='备注')
    parser.add_argument('--id', type=str, default=None, help='云设备 id')
    
    args = parser.parse_args()
    
    query_whatsapp_apps(
        page=args.page,
        page_size=args.page_size,
        status=args.status,
        name=args.name,
        phone_number=args.phone_number,
        remark=args.remark,
        id=args.id
    )


if __name__ == "__main__":
    main()
