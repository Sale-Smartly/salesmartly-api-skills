#!/usr/bin/env python3
"""
SaleSmartly Batch Script Generator

Auto-generate scripts from llms.txt
"""

import sys
import json
import hashlib
import urllib.request
import urllib.parse
import ssl
import re
from pathlib import Path

# 配置
APIFOX_BASE = "https://salesmartly-api.apifox.cn"
LLMS_URL = f"{APIFOX_BASE}/llms.txt"
OUTPUT_DIR = Path("scripts")

# 已存在的脚本，跳过
EXISTING_SCRIPTS = {
    'get-contact-list': 'query-customers.py',
    'get-member-list': 'query-members.py',
    'get-message-list': 'query-messages.py',
    'get-link-list': 'query-links.py',
    'get-individual-whatsapp-list': 'query-whatsapp-apps.py',
}


def fetch_llms() -> list:
    """获取 llms.txt 内容"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    try:
        req = urllib.request.Request(LLMS_URL, headers={"User-Agent": "SaleSmartly-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            content = response.read().decode('utf-8')
            return parse_llms(content)
    except Exception as e:
        print(f"❌ 获取 llms.txt 失败：{e}")
        sys.exit(1)


def parse_llms(content: str) -> list:
    """解析 llms.txt 提取 API 列表"""
    apis = []
    
    # 匹配 API 文档链接（支持中文 URL）
    pattern = r'-\s*([^\[]+)\s*\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, content)
    
    for match in matches:
        category = match[0].strip()
        name = match[1].strip()
        url = match[2].strip()
        
        # 跳过非 API 文档
        if 'Docs' in category or not url.endswith('.md'):
            continue
        
        # 从 URL 提取 API ID
        api_id_match = re.search(r'(\w+e\d+)\.md', url)
        if api_id_match:
            api_id = api_id_match.group(1)
            apis.append({
                'category': category,
                'name': name,
                'api_id': api_id
            })
    
    return apis


def fetch_api_doc(api_id: str) -> dict:
    """获取 API 文档内容"""
    url = f"{APIFOX_BASE}/{api_id}.md"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SaleSmartly-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            content = response.read().decode('utf-8')
            return parse_api_doc(content, api_id)
    except Exception as e:
        print(f"  ⚠️  获取失败：{e}")
        return None


def parse_api_doc(content: str, api_id: str) -> dict:
    """解析 API 文档 Markdown"""
    api_info = {
        'api_id': api_id,
        'name': '',
        'path': '',
        'method': 'GET',
        'params': [],
        'category': ''
    }
    
    # 提取 API 名称（第一行）
    lines = content.strip().split('
')
    if lines:
        api_info['name'] = lines[0].strip()
    
    # 提取 API 路径（OpenAPI 格式）
    path_match = re.search(r'^\s*(/api/v2/[^\s:]+):', content, re.MULTILINE)
    if path_match:
        api_info['path'] = path_match.group(1).strip()
    
    # 提取请求方法
    method_match = re.search(r'(get|post|put|delete):\s*$', content, re.IGNORECASE | re.MULTILINE)
    if method_match:
        api_info['method'] = method_match.group(1).upper()
    
    # 提取参数（body 参数）
    body_params = re.findall(r'^\s*(\w+):\s*
\s*description:\s*(.+?)(?=
\s*\w+:|
\s*required:|
\s*examples:|\Z)', content, re.MULTILINE | re.DOTALL)
    for param in body_params:
        if param[0] not in ['project_id', 'external-sign']:
            api_info['params'].append({
                'name': param[0],
                'in': 'body',
                'description': param[1].strip()
            })
    
    return api_info


def name_to_filename(name: str, method: str) -> str:
    """将 API 名称转换为文件名"""
    # 移除特殊字符
    name_clean = re.sub(r'[^\w]', '_', name)
    
    # 根据方法添加前缀
    prefix_map = {
        'GET': 'query',
        'POST': 'create',
        'PUT': 'update',
        'DELETE': 'delete'
    }
    prefix = prefix_map.get(method, 'api')
    
    return f"{prefix}-{name_clean.lower()}.py"


def generate_script(api_info: dict) -> str:
    """生成查询脚本"""
    method = api_info['method']
    prefix_map = {
        'GET': '查询',
        'POST': '创建',
        'PUT': '更新',
        'DELETE': '删除'
    }
    action = prefix_map.get(method, '操作')
    
    # 生成参数解析代码
    param_args = ""
    param_doc = ""
    required_params = []
    
    for param in api_info['params']:
        if param['in'] == 'body':
            param_name = param['name'].replace('_', '-')
            param_args += f"    parser.add_argument('--{param_name}', type=str, default=None, help='{param['description']}')
"
            param_doc += f"    {param['name']}: {param['description']}
"
            
            # 检查是否必填
            if f"{param['name']}\
" in str(api_info):
                required_params.append(param_name)
    
    script = f'''#!/usr/bin/env python3
"""
SaleSmartly {action}{api_info['name'].replace("（", "(").replace("）", ")")} 脚本

自动生成 - 根据 API 文档
API ID: {api_info['api_id']}
API 路径：{api_info['path']}
方法：{method}
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
        print(f"❌ 读取配置文件失败：{{e}}")
        sys.exit(1)


def generate_sign(api_key: str, params: dict) -> str:
    """生成 SaleSmartly API 签名（MD5）"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{{k}}={{v}}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()


def main_func(page: int = 1, page_size: int = 20, **kwargs):
    """
    {action}{api_info['name']}
    
    参数:
{param_doc}    page: 页码（从 1 开始，仅 GET 请求）
        page_size: 每页大小（最大 100，仅 GET 请求）
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    print(f"📊 {action}{api_info['name']}")
    print(f"API: {api_info['path']}")
    print(f"方法：{method}")
    print()
    
    # 构建请求参数
    params = {{}}
    
    # GET 请求添加分页参数
    if {method!r} == 'GET':
        params = {{
            "project_id": project_id,
            "page": str(page),
            "page_size": str(page_size)
        }}
    else:
        # POST/PUT 请求
        params = {{
            "project_id": project_id
        }}
    
    # 添加可选参数
    for key, value in kwargs.items():
        if value is not None:
            params[key.replace('-', '_')] = value
    
    sign = generate_sign(api_key, params)
    
    # 构建 URL
    if {method!r} == 'GET':
        query_params = dict(params)
        for k in ['updated_time', 'created_time']:
            if k in query_params and query_params[k].startswith('{{'):
                query_params[k] = urllib.parse.quote(query_params[k])
        query_string = "&".join([f"{{k}}={{v}}" for k, v in query_params.items()])
        url = f"{{API_BASE_URL}}{api_info['path']}?{{query_string}}"
        req = urllib.request.Request(url, headers={{
            "Content-Type": "application/json",
            "User-Agent": "SaleSmartly-Agent/1.0",
            "External-Sign": sign
        }})
    else:
        # POST/PUT 请求
        url = f"{{API_BASE_URL}}{api_info['path']}"
        # 签名参数不包含 project_id（在 body 中）
        sign_params = {{k: v for k, v in params.items() if k != 'project_id'}}
        sign = generate_sign(api_key, sign_params)
        data = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(url, data=data, method={method!r}, headers={{
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "SaleSmartly-Agent/1.0",
            "External-Sign": sign
        }})
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    try:
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            resp_json = json.loads(response.read().decode('utf-8'))
        
        if resp_json.get('code') != 0:
            print(f"❌ 请求失败：{{resp_json.get('msg', 'Unknown error')}} (code: {{resp_json.get('code')}})")
            sys.exit(1)
        
        data = resp_json.get('data', {{}})
        
    except Exception as e:
        print(f"❌ 请求失败：{{e}}")
        sys.exit(1)
    
    # 显示结果
    print(f"\
{{'='*60}}")
    print(f"✅ {action}成功！")
    print(f"{{'='*60}}")
    
    # 显示返回数据
    if isinstance(data, dict):
        for key, value in data.items():
            if key != 'list':
                if isinstance(value, int) and value > 1000000000:
                    try:
                        ts = value // 1000 if value > 1000000000000 else value
                        dt = datetime.fromtimestamp(ts)
                        print(f"{{key}}: {{dt.strftime('%Y-%m-%d %H:%M:%S')}}")
                    except:
                        print(f"{{key}}: {{value}}")
                else:
                    print(f"{{key}}: {{value}}")
        
        # 如果有 list 字段
        items = data.get('list', [])
        if items:
            print(f"\
返回：{{len(items)}} 条")
            for i, item in enumerate(items, 1):
                print(f"\
[{{i}}] ID: {{item.get('id', 'N/A')}}")
                for k, v in item.items():
                    if k != 'id' and v is not None:
                        if isinstance(v, int) and v > 1000000000:
                            try:
                                ts = v // 1000 if v > 1000000000000 else v
                                dt = datetime.fromtimestamp(ts)
                                print(f"    {{k}}: {{dt.strftime('%Y-%m-%d %H:%M:%S')}}")
                            except:
                                print(f"    {{k}}: {{v}}")
                        else:
                            print(f"    {{k}}: {{v}}")
    elif isinstance(data, list):
        print(f"返回：{{len(data)}} 条")
        for i, item in enumerate(data, 1):
            print(f"\
[{{i}}] {{item}}")
    
    print(f"\
{{'='*60}}")


def main():
    parser = argparse.ArgumentParser(description='{action}{api_info['name']}工具')
{"" if method == 'GET' else "    # 非 GET 请求不需要分页参数
"}
    parser.add_argument('--page', type=int, default=1, help='页码（从 1 开始）')
    parser.add_argument('--page-size', type=int, default=20, help='每页大小（最大 100）')
{param_args}
    args = parser.parse_args()
    
    main_func(
        page=args.page,
        page_size=args.page_size,
        **vars(args)
    )


if __name__ == "__main__":
    main()
'''
    
    return script


def main():
    print("📄 获取 API 列表...")
    apis = fetch_llms()
    print(f"✅ 找到 {len(apis)} 个 API
")
    
    generated = 0
    skipped = 0
    
    for api in apis:
        print(f"📝 处理：{api['category']} - {api['name']}")
        
        # 检查是否已存在
        api_info = fetch_api_doc(api['api_id'])
        if not api_info or not api_info['path']:
            print(f"  ⚠️  跳过（无法解析）")
            skipped += 1
            continue
        
        # 检查是否已有对应脚本
        path_key = api_info['path'].split('/')[-1]
        if path_key in EXISTING_SCRIPTS:
            print(f"  ✓ 已存在：{EXISTING_SCRIPTS[path_key]}")
            skipped += 1
            continue
        
        # 生成文件名
        filename = name_to_filename(api_info['name'], api_info['method'])
        output_path = OUTPUT_DIR / filename
        
        # 生成脚本
        script = generate_script(api_info)
        output_path.write_text(script, encoding='utf-8')
        
        print(f"  ✅ 生成：{filename} ({len(script)} bytes)")
        generated += 1
    
    print(f"
{'='*60}")
    print(f"✅ 完成！生成 {generated} 个脚本，跳过 {skipped} 个")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
