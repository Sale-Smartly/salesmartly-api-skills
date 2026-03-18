#!/usr/bin/env python3
"""
批量回聊 - SaleSmartly API

功能：批量对多个客户发起回聊请求（异步处理）
接口：POST /api/v2/batch-talk-back
文档：https://salesmartly-api.apifox.cn/批量回聊 -425955043e0.md

⚠️ 注意：这是一个异步处理接口，不会实时处理完成

使用示例：
    # 对单个客户回聊
    uv run scripts/batch-talk-back.py --chat-user-id abc123 --sys-user-id 1344
    
    # 对多个客户回聊（最多 100 个）
    uv run scripts/batch-talk-back.py --chat-user-ids abc123,def456,ghi789 --sys-user-id 1344
    
    # 从文件读取客户 ID 列表
    uv run scripts/batch-talk-back.py --chat-user-ids-file customers.txt --sys-user-id 1344

参数说明：
    --chat-user-id: 单个访客 ID
    --chat-user-ids: 多个访客 ID（逗号分隔，最多 100 个）
    --chat-user-ids-file: 从文件读取访客 ID 列表（每行一个）
    --sys-user-id: 客服 ID（使用 sys_user_id，不是成员 id）
    --config: 配置文件路径（默认 api-key.json）
"""

import argparse
import json
import hashlib
import time
import ssl
import urllib.request
from pathlib import Path
from typing import List, Optional


def load_config(config_path: str) -> dict:
    """加载配置文件"""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_sign(api_key: str, params: dict) -> str:
    """生成 API 签名"""
    # 参数按字母排序
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    
    # 拼接签名字符串：apiKey + key1=value1&key2=value2...
    sign_parts = [api_key]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()


def make_request(url: str, data: dict, api_key: str) -> dict:
    """发送 API 请求（使用 multipart/form-data）"""
    import uuid
    
    # 生成签名
    sign = generate_sign(api_key, data)
    
    # 生成 multipart/form-data
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
    body_lines = []
    for key, value in data.items():
        body_lines.append(f"--{boundary}")
        body_lines.append(f'Content-Disposition: form-data; name="{key}"')
        body_lines.append("")
        body_lines.append(str(value))
    body_lines.append(f"--{boundary}--")
    body_lines.append("")
    body_data = "\r\n".join(body_lines).encode('utf-8')
    
    # 准备请求
    req = urllib.request.Request(url, data=body_data, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('User-Agent', 'SaleSmartly-Agent/1.0')
    req.add_header('external-sign', sign)
    
    # SSL 验证（安全配置）
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ""
        raise Exception(f"HTTP 错误 {e.code}: {error_body}")
    except urllib.error.URLError as e:
        raise Exception(f"网络错误：{e.reason}")
    except Exception as e:
        raise Exception(f"请求失败：{str(e)}")


def read_chat_user_ids_from_file(file_path: str) -> List[str]:
    """从文件读取客户 ID 列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        ids = [line.strip() for line in f if line.strip()]
    return ids


def batch_talk_back(
    config: dict,
    chat_user_ids: List[str],
    sys_user_id: str
) -> dict:
    """
    批量回聊
    
    Args:
        config: 配置字典（包含 apiKey, projectId）
        chat_user_ids: 访客 ID 列表
        sys_user_id: 客服 ID
    
    Returns:
        API 响应结果
    """
    api_key = config.get('apiKey')
    project_id = config.get('projectId')
    
    if not api_key or not project_id:
        raise ValueError("配置文件中缺少 apiKey 或 projectId")
    
    # 限制最多 100 个
    if len(chat_user_ids) > 100:
        raise ValueError(f"最多支持 100 个客户 ID，当前提供{len(chat_user_ids)}个")
    
    # 准备请求参数
    params = {
        'project_id': project_id,
        'sys_user_id': sys_user_id,
        'chat_user_ids': ','.join(chat_user_ids)
    }
    
    url = "https://developer.salesmartly.com/api/v2/batch-talk-back"
    result = make_request(url, params, api_key)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='批量回聊 - 对多个客户发起回聊请求（异步处理）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
    # 单个客户
    uv run scripts/batch-talk-back.py --chat-user-id abc123 --sys-user-id 1344
    
    # 多个客户（逗号分隔）
    uv run scripts/batch-talk-back.py --chat-user-ids abc123,def456 --sys-user-id 1344
    
    # 从文件读取
    uv run scripts/batch-talk-back.py --chat-user-ids-file customers.txt --sys-user-id 1344
        """
    )
    
    # 客户 ID 参数（三选一）
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument('--chat-user-id', type=str, help='单个访客 ID')
    id_group.add_argument('--chat-user-ids', type=str, help='多个访客 ID（逗号分隔，最多 100 个）')
    id_group.add_argument('--chat-user-ids-file', type=str, help='从文件读取访客 ID 列表（每行一个）')
    
    # 必需参数
    parser.add_argument('--sys-user-id', type=str, required=True, 
                       help='客服 ID（使用 sys_user_id，不是成员 id）')
    
    # 可选参数
    parser.add_argument('--config', type=str, default='api-key.json',
                       help='配置文件路径（默认 api-key.json）')
    parser.add_argument('--quiet', action='store_true',
                       help='安静模式，只输出 JSON 结果')
    
    args = parser.parse_args()
    
    # 加载配置
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"❌ 错误：{e}")
        print("请确保配置文件中包含 apiKey 和 projectId")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误：{e}")
        return 1
    
    # 解析客户 ID 列表
    chat_user_ids = []
    if args.chat_user_id:
        chat_user_ids = [args.chat_user_id]
    elif args.chat_user_ids:
        chat_user_ids = [id.strip() for id in args.chat_user_ids.split(',') if id.strip()]
    elif args.chat_user_ids_file:
        try:
            chat_user_ids = read_chat_user_ids_from_file(args.chat_user_ids_file)
        except FileNotFoundError:
            print(f"❌ 文件不存在：{args.chat_user_ids_file}")
            return 1
    
    if not chat_user_ids:
        print("❌ 错误：没有提供有效的客户 ID")
        return 1
    
    if len(chat_user_ids) > 100:
        print(f"❌ 错误：最多支持 100 个客户 ID，当前提供{len(chat_user_ids)}个")
        return 1
    
    # 执行批量回聊
    try:
        if not args.quiet:
            print(f"📞 正在发起批量回聊请求...")
            print(f"   客服 ID: {args.sys_user_id}")
            print(f"   客户数量：{len(chat_user_ids)}")
            print(f"   客户 ID: {','.join(chat_user_ids[:5])}{'...' if len(chat_user_ids) > 5 else ''}")
            print()
        
        result = batch_talk_back(config, chat_user_ids, args.sys_user_id)
        
        # 输出结果
        if args.quiet:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            code = result.get('code', -1)
            msg = result.get('msg', 'Unknown')
            data = result.get('data', {})
            
            if code == 0:
                print("✅ 批量回聊请求成功！")
                print(f"   响应消息：{msg}")
                print()
                print("⚠️  注意：这是一个异步处理接口，不会实时处理完成")
                print("   系统会在后台逐步处理回聊请求")
                
                if 'res' in data:
                    print(f"   处理结果：{data['res']}")
                if 'session_status' in data:
                    print(f"   会话状态：{data['session_status']}")
            else:
                print(f"❌ 请求失败")
                print(f"   错误码：{code}")
                print(f"   错误信息：{msg}")
            
            print()
            print("完整响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return 0 if result.get('code') == 0 else 1
        
    except Exception as e:
        if not args.quiet:
            print(f"❌ 错误：{e}")
        else:
            print(json.dumps({'code': -1, 'msg': str(e)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    import urllib.parse
    exit(main())
