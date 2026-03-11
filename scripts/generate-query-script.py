#!/usr/bin/env python3
"""
SalesSmartly Script Generator

Auto-generate script from API documentation
"""

import sys
import json
import hashlib
import argparse
import urllib.request
import urllib.parse
import ssl
import re
from pathlib import Path

# 配置文件
CONFIG_FILE = "api-key.json"
API_BASE_URL = "https://developer.salesmartly.com"
APIFOX_BASE = "https://salesmartly-api.apifox.cn"


def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('apiKey'), config.get('projectId')
    except Exception as e:
        print(f"❌ 读取配置文件失败：{e}")
        sys.exit(1)


def fetch_api_doc(api_id: str) -> dict:
    """获取 API 文档内容"""
    url = f"{APIFOX_BASE}/{api_id}.md"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SalesSmartly-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            content = response.read().decode('utf-8')
            return parse_api_doc(content)
    except Exception as e:
        print(f"❌ 获取 API 文档失败：{e}")
        sys.exit(1)


def parse_api_doc(content: str) -> dict:
    """解析 API 文档 Markdown"""
    api_info = {
        'name': '',
        'path': '',
        'method': 'GET',
        'params': [],
        'description': ''
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
    
    # 提取参数（OpenAPI 格式）
    param_matches = re.findall(r'name:\s*(\w+)\s+in:\s*(query|body|header).*?description:\s*(.+?)(?=
\s*name:|
\s*required:|
\s*examples:|\Z)', content, re.DOTALL)
    for param in param_matches:
        api_info['params'].append({
            'name': param[0],
            'in': param[1],
            'description': param[2].strip()
        })
    
    # 如果是 body 参数，提取 requestBody 中的字段
    body_params = re.findall(r'^\s*(\w+):\s*
\s*description:\s*(.+?)(?=
\s*\w+:|
\s*required:|
\s*examples:|\Z)', content, re.MULTILINE | re.DOTALL)
    for param in body_params:
        if param[0] not in ['project_id', 'external-sign']:
            # 检查是否已存在
            exists = any(p['name'] == param[0] for p in api_info['params'])
            if not exists:
                api_info['params'].append({
                    'name': param[0],
                    'in': 'body',
                    'description': param[1].strip()
                })
    
    return api_info


def generate_script(api_info: dict) -> str:
    """生成查询脚本"""
    name = api_info['name'].replace('（', '(').replace('）', ')')
    name_clean = re.sub(r'[^\w]', '_', name)
    filename = f"query-{name_clean.lower()}.py"
    
    # 生成参数解析代码
    param_args = ""
    param_doc = ""
    for param in api_info['params']:
        if param['in'] == 'query' and param['name'] not in ['project_id', 'page', 'page_size', 'external-sign']:
            param_args += f"    parser.add_argument('--{param['name'].replace('_', '-')}', type=str, default=None, help='{param['description']}')
"
            param_doc += f"    {param['name']}: {param['description']}
"
    
    script = f'''#!/usr/bin/env python3
"""
SalesSmartly {name} 脚本

自动生成 - 根据 API 文档
API 路径：{api_info['path']}
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
    """生成 SalesSmartly API 签名（MD5）"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{{k}}={{v}}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()


def {name_clean.lower()}(page: int = 1, page_size: int = 20, **kwargs):
    """
    {name}
    
    参数:
{param_doc}    page: 页码（从 1 开始）
        page_size: 每页大小（最大 100）
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    print(f"📊 {name}")
    print()
    
    # 构建请求参数
    params = {{
        "project_id": project_id,
        "page": str(page),
        "page_size": str(page_size)
    }}
    
    # 添加可选参数
    for key, value in kwargs.items():
        if value is not None:
            params[key.replace('-', '_')] = value
    
    sign = generate_sign(api_key, params)
    
    # 构建查询字符串
    query_params = dict(params)
    for key in ['updated_time', 'created_time']:
        if key in query_params and isinstance(query_params[key], str) and query_params[key].startswith('{{'):
            query_params[key] = urllib.parse.quote(query_params[key])
    
    query_string = "&".join([f"{{k}}={{v}}" for k, v in query_params.items()])
    url = f"{{API_BASE_URL}}{api_info['path']}?{{query_string}}"
    
    headers = {{
        "Content-Type": "application/json",
        "User-Agent": "SalesSmartly-Agent/1.0",
        "External-Sign": sign
    }}
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            resp_json = json.loads(response.read().decode('utf-8'))
        
        if resp_json.get('code') != 0:
            print(f"❌ 请求失败：{{resp_json.get('msg', 'Unknown error')}} (code: {{resp_json.get('code')}})")
            sys.exit(1)
        
        data = resp_json.get('data', {{}})
        items = data.get('list', [])
        total = data.get('total', 0)
        
    except Exception as e:
        print(f"❌ 请求失败：{{e}}")
        sys.exit(1)
    
    # 显示结果
    print(f"\
{{'='*60}}")
    print(f"✅ {name}成功！")
    print(f"{{'='*60}}")
    print(f"总数：{{total}}")
    print(f"当前页：{{page}}")
    print(f"每页：{{page_size}}")
    print(f"返回：{{len(items)}} 条")
    
    if items:
        print(f"\
列表:")
        for i, item in enumerate(items, 1):
            print(f"\
[{{i}}] ID: {{item.get('id', 'N/A')}}")
            # 显示所有字段
            for key, value in item.items():
                if key != 'id' and value is not None:
                    if isinstance(value, int) and value > 1000000000:  # 时间戳
                        try:
                            if value > 1000000000000:
                                value = value // 1000
                            dt = datetime.fromtimestamp(value)
                            print(f"    {{key}}: {{dt.strftime('%Y-%m-%d %H:%M:%S')}}")
                        except:
                            print(f"    {{key}}: {{value}}")
                    else:
                        print(f"    {{key}}: {{value}}")
    else:
        print(f"\
⚠️  未找到数据")
    
    print(f"\
{{'='*60}}")


def main():
    parser = argparse.ArgumentParser(description='{name}工具')
    parser.add_argument('--page', type=int, default=1, help='页码（从 1 开始）')
    parser.add_argument('--page-size', type=int, default=20, help='每页大小（最大 100）')
{param_args}
    args = parser.parse_args()
    
    {name_clean.lower()}(
        page=args.page,
        page_size=args.page_size,
        **vars(args)
    )


if __name__ == "__main__":
    main()
'''
    
    return filename, script


def main():
    parser = argparse.ArgumentParser(description='SalesSmartly API 脚本生成器')
    parser.add_argument('--api-url', type=str, help='API 文档完整 URL')
    parser.add_argument('--api-id', type=str, help='API 文档 ID（从 llms.txt 获取）')
    parser.add_argument('--output', type=str, default='scripts/', help='输出目录')
    
    args = parser.parse_args()
    
    if args.api_url:
        # 从完整 URL 提取 API ID
        match = re.search(r'/(\w+e\d+)\.md', args.api_url)
        if match:
            api_id = match.group(1)
        else:
            print("❌ 无法从 URL 提取 API ID")
            sys.exit(1)
    elif args.api_id:
        api_id = args.api_id
    else:
        print("❌ 请提供 --api-url 或 --api-id")
        sys.exit(1)
    
    print(f"📄 获取 API 文档：{api_id}")
    api_info = fetch_api_doc(api_id)
    
    if not api_info['path']:
        print("❌ 无法解析 API 路径")
        sys.exit(1)
    
    print(f"✅ 解析成功:")
    print(f"   名称：{api_info['name']}")
    print(f"   路径：{api_info['path']}")
    print(f"   方法：{api_info['method']}")
    print(f"   参数：{len(api_info['params'])} 个")
    
    filename, script = generate_script(api_info)
    output_path = Path(args.output) / filename
    
    output_path.write_text(script, encoding='utf-8')
    print(f"
✅ 脚本已生成：{output_path}")
    print(f"   大小：{len(script)} bytes")
    
    # 设置执行权限
    import os
    os.chmod(output_path, 0o755)


if __name__ == "__main__":
    main()
