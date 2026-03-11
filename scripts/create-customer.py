#!/usr/bin/env python3
"""
SalesSmartly Create Customer

Auto-generated from API documentation
API ID: 276530997e0
Endpoint: /api/v2/add-contact
Method: POST
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


def main_func(channel: str = '12', from_channel_info: str = None, phone: str = None, remark_name: str = None, remark: str = None, **kwargs):
    """
    Create - Create Customer
    
    参数:
    channel: 目前仅支持WhatsApp api-7和WhatsApp App-12
    from_channel_info: 归属渠道的渠道信息 如归属的手机号
    phone: 客户手机号需要加区号（不支持86的手机号）
    remark_name: 添加客户备注名（限制长度50个字）
    remark: 客户备注（限制长度2000个字）
    page: 页码（从 1 开始，仅 GET 请求）
        page_size: 每页大小（最大 100，仅 GET 请求）
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    print(f"📊 Create - Create Customer")
    print(f"API: /api/v2/add-contact")
    print(f"方法：POST")
    print()
    
    # 构建请求参数
    params = {}
    
    # GET 请求添加分页参数
    if 'POST' == 'GET':
        params = {
            "project_id": project_id,
            "page": str(page),
            "page_size": str(page_size)
        }
    else:
        # POST/PUT 请求
        params = {
            "project_id": project_id
        }
    
    # 添加可选参数
    for key, value in kwargs.items():
        if value is not None:
            params[key.replace('-', '_')] = value
    
    sign = generate_sign(api_key, params)
    
    # 构建 URL
    if 'POST' == 'GET':
        query_params = dict(params)
        for k in ['updated_time', 'created_time']:
            if k in query_params and query_params[k].startswith('{'):
                query_params[k] = urllib.parse.quote(query_params[k])
        query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
        url = f"{API_BASE_URL}/api/v2/add-contact?{query_string}"
        req = urllib.request.Request(url, headers={
            "Content-Type": "application/json",
            "User-Agent": "SalesSmartly-Agent/1.0",
            "External-Sign": sign
        })
    else:
        # POST/PUT 请求
        url = f"{API_BASE_URL}/api/v2/add-contact"
        # 所有参数参与签名
        sign = generate_sign(api_key, params)
        
        # 生成 multipart/form-data
        import uuid
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
        body_lines = []
        for key, value in params.items():
            body_lines.append(f"--{boundary}")
            body_lines.append(f'Content-Disposition: form-data; name="{key}"')
            body_lines.append("")
            body_lines.append(str(value))
        body_lines.append(f"--{boundary}--")
        body_lines.append("")
        data = "\r\n".join(body_lines).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='POST', headers={
            "Content-Type": "multipart/form-data; boundary=" + boundary,
            "User-Agent": "SalesSmartly-Agent/1.0",
            "External-Sign": sign
        })
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
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
    
    # 显示结果
    print(f"\n{'='*60}")
    print(f"✅ 创建成功！")
    print(f"{'='*60}")
    
    # 显示返回数据
    if isinstance(data, dict):
        for key, value in data.items():
            if key != 'list':
                if isinstance(value, int) and value > 1000000000:
                    try:
                        ts = value // 1000 if value > 1000000000000 else value
                        dt = datetime.fromtimestamp(ts)
                        print(f"{key}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        print(f"{key}: {value}")
                else:
                    print(f"{key}: {value}")
        
        # 如果有 list 字段
        items = data.get('list', [])
        if items:
            print(f"\n返回：{len(items)} 条")
            for i, item in enumerate(items, 1):
                print(f"\n[{i}] ID: {item.get('id', 'N/A')}")
                for k, v in item.items():
                    if k != 'id' and v is not None:
                        if isinstance(v, int) and v > 1000000000:
                            try:
                                ts = v // 1000 if v > 1000000000000 else v
                                dt = datetime.fromtimestamp(ts)
                                print(f"    {k}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                            except:
                                print(f"    {k}: {v}")
                        else:
                            print(f"    {k}: {v}")
    elif isinstance(data, list):
        print(f"返回：{len(data)} 条")
        for i, item in enumerate(data, 1):
            print(f"\n[{i}] {item}")
    
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='新增客户')
    parser.add_argument('--channel', type=str, default='12', help='渠道 ID（WhatsApp App=12）')
    parser.add_argument('--from-channel-info', type=str, default=None, help='归属渠道信息')
    parser.add_argument('--phone', type=str, required=True, help='客户手机号（加区号，不支持 86）')
    parser.add_argument('--remark-name', type=str, default=None, help='客户备注名')
    parser.add_argument('--remark', type=str, default=None, help='客户备注')
    args = parser.parse_args()
    main_func(
        channel=args.channel,
        from_channel_info=args.from_channel_info,
        phone=args.phone,
        remark_name=args.remark_name,
        remark=args.remark
    )


if __name__ == "__main__":
    main()
