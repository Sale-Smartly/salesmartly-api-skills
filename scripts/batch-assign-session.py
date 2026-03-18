#!/usr/bin/env python3
"""
批量分配会话 - SaleSmartly API

功能：批量将客户会话分配给指定客服，或结束当前分配
接口：POST /api/v2/batch-assign-contact
文档：https://salesmartly-api.apifox.cn/批量分配会话 -426704813e0.md

使用示例：
    # 分配单个客户给客服
    uv run scripts/batch-assign-session.py --chat-user-id abc123 --assign-sys-user-id 1779 --action start
    
    # 分配多个客户给客服
    uv run scripts/batch-assign-session.py --chat-user-ids abc123,def456,ghi789 --assign-sys-user-id 1779 --action start
    
    # 结束当前分配（释放客户）
    uv run scripts/batch-assign-session.py --chat-user-ids abc123,def456 --assign-sys-user-id 1779 --action end --task-id 574_Sv2sNRlfcn
    
    # 分配全部会话（包括进行中的）
    uv run scripts/batch-assign-session.py --chat-user-ids abc123 --assign-sys-user-id 1779 --action start --assign-type 1

参数说明：
    --chat-user-id: 单个客户 ID
    --chat-user-ids: 多个客户 ID（逗号分隔）
    --chat-user-ids-file: 从文件读取客户 ID 列表（每行一个）
    --assign-sys-user-id: 被分配的客服 ID
    --sys-user-id: 操作者 ID（最高权限的客服 ID）
    --action: start(开始分配) 或 end(结束分配)
    --assign-type: 0=无进行中会话（默认），1=全部
    --task-id: action 为 end 时必需，结束当前分配的任务 ID
    --config: 配置文件路径（默认 api-key.json）
"""

import argparse
import json
import hashlib
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


def batch_assign_session(
    config: dict,
    chat_user_ids: List[str],
    sys_user_id: str,
    assign_sys_user_id: str,
    action: str,
    assign_type: int = 0,
    task_id: Optional[str] = None
) -> dict:
    """
    批量分配会话
    
    Args:
        config: 配置字典（包含 apiKey, projectId）
        chat_user_ids: 客户 ID 列表
        sys_user_id: 操作者 ID（最高权限客服）
        assign_sys_user_id: 被分配的客服 ID
        action: "start"开始分配，"end"结束分配
        assign_type: 0=无进行中会话，1=全部
        task_id: action 为 end 时必需
    
    Returns:
        API 响应结果
    """
    api_key = config.get('apiKey')
    project_id = config.get('projectId')
    
    if not api_key or not project_id:
        raise ValueError("配置文件中缺少 apiKey 或 projectId")
    
    # 准备请求参数
    params = {
        'project_id': project_id,
        'action': action,
        'sys_user_id': sys_user_id,
        'assign_sys_user_id': assign_sys_user_id,
        'assign_type': assign_type,
        'ids': ','.join(chat_user_ids)
    }
    
    # action 为 end 时需要 task_id
    if action == 'end':
        if not task_id:
            raise ValueError("action 为 end 时必须提供 task_id")
        params['task_id'] = task_id
    
    url = "https://developer.salesmartly.com/api/v2/batch-assign-contact"
    result = make_request(url, params, api_key)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='批量分配会话 - 将客户会话批量分配给指定客服或结束分配',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
    # 分配单个客户
    uv run scripts/batch-assign-session.py --chat-user-id abc123 --assign-sys-user-id 1779 --action start
    
    # 分配多个客户
    uv run scripts/batch-assign-session.py --chat-user-ids abc123,def456 --assign-sys-user-id 1779 --action start
    
    # 结束分配（释放客户）
    uv run scripts/batch-assign-session.py --chat-user-ids abc123 --assign-sys-user-id 1779 --action end --task-id 574_Sv2sNRlfcn
    
    # 分配全部会话（包括进行中的）
    uv run scripts/batch-assign-session.py --chat-user-ids abc123 --assign-sys-user-id 1779 --action start --assign-type 1

参数说明：
    action:
        start - 开始分配（将客户分配给客服）
        end   - 结束分配（释放客户，需要 task_id）
    
    assign_type:
        0 - 只分配无进行中会话的客户
        1 - 分配全部客户（默认，包括有进行中会话的，强制分配）
        """
    )
    
    # 客户 ID 参数（三选一）
    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument('--chat-user-id', type=str, help='单个客户 ID')
    id_group.add_argument('--chat-user-ids', type=str, help='多个客户 ID（逗号分隔）')
    id_group.add_argument('--chat-user-ids-file', type=str, help='从文件读取客户 ID 列表（每行一个）')
    
    # 必需参数
    parser.add_argument('--assign-sys-user-id', type=str, required=True,
                       help='被分配的客服 ID（使用 sys_user_id）')
    parser.add_argument('--sys-user-id', type=str, required=True,
                       help='操作者 ID（最高权限的客服 ID）')
    parser.add_argument('--action', type=str, required=True, choices=['start', 'end'],
                       help='start=开始分配，end=结束分配')
    
    # 可选参数
    parser.add_argument('--assign-type', type=int, default=1, choices=[0, 1],
                       help='分配类型：0=无进行中会话，1=全部（默认，强制分配）')
    parser.add_argument('--task-id', type=str,
                       help='action 为 end 时必需，结束当前分配的任务 ID')
    parser.add_argument('--config', type=str, default='api-key.json',
                       help='配置文件路径（默认 api-key.json）')
    parser.add_argument('--quiet', action='store_true',
                       help='安静模式，只输出 JSON 结果')
    
    args = parser.parse_args()
    
    # 验证 task_id
    if args.action == 'end' and not args.task_id:
        print("❌ 错误：action 为 end 时必须提供 --task-id")
        return 1
    
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
    
    # 执行批量分配
    try:
        if not args.quiet:
            action_text = "开始分配" if args.action == 'start' else "结束分配"
            assign_type_text = "无进行中会话" if args.assign_type == 0 else "全部"
            
            print(f"📋 正在批量{action_text}会话...")
            print(f"   操作者 ID: {args.sys_user_id}")
            print(f"   被分配客服：{args.assign_sys_user_id}")
            print(f"   客户数量：{len(chat_user_ids)}")
            print(f"   分配类型：{assign_type_text}")
            if args.task_id:
                print(f"   任务 ID: {args.task_id}")
            print(f"   客户 ID: {','.join(chat_user_ids[:5])}{'...' if len(chat_user_ids) > 5 else ''}")
            print()
        
        result = batch_assign_session(
            config=config,
            chat_user_ids=chat_user_ids,
            sys_user_id=args.sys_user_id,
            assign_sys_user_id=args.assign_sys_user_id,
            action=args.action,
            assign_type=args.assign_type,
            task_id=args.task_id
        )
        
        # 输出结果
        if args.quiet:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            code = result.get('code', -1)
            msg = result.get('msg', 'Unknown')
            data = result.get('data', {})
            
            if code == 0:
                action_text = "分配" if args.action == 'start' else "释放"
                print(f"✅ 批量{action_text}会话成功！")
                print(f"   响应消息：{msg}")
                
                if 'task_id' in data:
                    print(f"   任务 ID: {data['task_id']}")
                    print()
                    print("💡 提示：task_id 可用于后续结束分配操作")
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
