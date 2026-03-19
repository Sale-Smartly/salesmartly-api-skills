#!/usr/bin/env python3
"""
SaleSmartly Message Query

API ID: 317790952e0
Endpoint: /api/v2/get-message-list
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
    global API_BASE_URL
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            api_key = config.get('apiKey')
            project_id = config.get('projectId')
            # 支持自定义域名
            if config.get('baseUrl'):
                API_BASE_URL = config.get('baseUrl')
            return api_key, project_id
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


def query_messages(chat_user_id: str = None, session_id: str = None, page_size: int = 20, 
                   days: int = None, start_sequence_id: str = None, end_sequence_id: str = None,
                   msg_content: str = None, all_pages: bool = False):
    """
    查询指定用户的聊天记录列表
    
    Args:
        chat_user_id: 用户 ID（与 session_id 二选一）
        session_id: 会话 ID（与 chat_user_id 二选一）
        page_size: 每页大小（最大 100）
        days: 查询最近 N 天的消息
        start_sequence_id: 开始的消息 ID
        end_sequence_id: 结束的消息 ID
        msg_content: 关键词筛选（可选）
    
    ⚠️ 重要：发送人 ID 说明
    -----------------------------------------
    消息中的 `sender` 字段含义取决于 `sender_type`：
    
    - sender_type = 1 (用户): sender = 客户 chat_user_id
    - sender_type = 2 (团队成员): sender = 客服 sys_user_id ← 真正的客服 ID
    - sender_type = 3 (系统): sender = 系统
    
    ✅ 正确用法：当 sender_type=2 时，sender 是客服的 sys_user_id
    ❌ 错误用法：不要将 sender 与成员 id 字段混淆
    """
    api_key, project_id = load_config()
    
    if not api_key or not project_id:
        print("❌ 配置错误：缺少 API Key 或 Project ID")
        sys.exit(1)
    
    if not chat_user_id and not session_id:
        print("❌ 错误：--chat-user-id 或 --session-id 必须填写一个")
        sys.exit(1)
    
    print(f"📊 查询聊天记录")
    if chat_user_id:
        print(f"用户 ID: {chat_user_id}")
    if session_id:
        print(f"会话 ID: {session_id}")
    if days:
        print(f"时间范围：最近 {days} 天")
    if msg_content:
        print(f"关键词：{msg_content}")
    print()
    
    # 构建请求参数
    params = {
        "project_id": project_id,
        "page_size": str(page_size)
    }
    
    # chat_user_id 和 session_id 二选一
    if chat_user_id:
        params["chat_user_id"] = chat_user_id
    if session_id:
        params["session_id"] = session_id
    
    # 可选参数
    if start_sequence_id:
        params['start_sequence_id'] = start_sequence_id
    if end_sequence_id:
        params['end_sequence_id'] = end_sequence_id
    if msg_content:
        params['msg_content'] = msg_content
    
    # 时间范围过滤
    if days:
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=days)).timestamp())
        params['updated_time'] = json.dumps({"start": start_time, "end": end_time})
    
    sign = generate_sign(api_key, params)
    
    # 构建查询字符串
    query_params = dict(params)
    if 'updated_time' in query_params:
        query_params['updated_time'] = urllib.parse.quote(query_params['updated_time'])
    
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{API_BASE_URL}/api/v2/get-message-list?{query_string}"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "SaleSmartly-Agent/1.0",
        "External-Sign": sign
    }
    
    ssl_context = ssl.create_default_context()
    # 支持禁用 SSL 验证（用于 dev 环境或证书问题）
    import os
    if os.environ.get('DISABLE_SSL_VERIFY') == 'true':
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    else:
        # 正式环境也可能遇到证书链问题，使用较宽松的验证
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
        messages = data.get('list') if data else None
        total = data.get('total', 0) if data else 0
        
        # 如果需要获取所有页面
        if all_pages and messages and total > len(messages):
            print(f"  正在获取所有页面数据... (共 {total} 条)")
            all_messages = list(messages)
            page = 2
            while len(all_messages) < total:
                params['page'] = str(page)
                sign = generate_sign(api_key, params)
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                url = f"{API_BASE_URL}/api/v2/get-message-list?{query_string}"
                headers['External-Sign'] = sign
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
                    resp_json = json.loads(resp.read().decode('utf-8'))
                data = resp_json.get('data', {})
                page_messages = data.get('list', [])
                if not page_messages:
                    break
                all_messages.extend(page_messages)
                if page % 5 == 0:
                    print(f"  已获取第 {page} 页 ({len(page_messages)} 条)，共 {len(all_messages)}/{total} 条...")
                page += 1
            messages = all_messages
        
        # 调试：打印原始响应
        # print(f"DEBUG: resp_json = {json.dumps(resp_json, indent=2)}")
        # print(f"DEBUG: data = {data}")
        # print(f"DEBUG: messages = {messages}")
        
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        sys.exit(1)
    
    # 显示结果
    print(f"\n{'='*60}")
    print(f"✅ 聊天记录查询成功！")
    print(f"{'='*60}")
    
    # 处理 messages 为 None 的情况
    if messages is None:
        messages = []
        print(f"返回：0 条（API 返回空列表）")
    else:
        print(f"返回：{len(messages)} 条")
    
    if messages:
        print(f"\n消息列表:")
        for i, msg in enumerate(messages, 1):
            print(f"\n[{i}] 消息 ID: {msg.get('sequence_id', 'N/A')}")
            
            # 消息类型
            msg_type = msg.get('msg_type')
            type_map = {
                0: '未定义',
                1: '文本',
                2: '图片',
                3: '模板',
                4: '文件',
                5: '回传',
                6: '视频',
                7: '邮件',
                8: '系统消息'
            }
            print(f"    类型：{type_map.get(msg_type, str(msg_type))}")
            
            # 发送人类型
            sender_type = msg.get('sender_type')
            sender = msg.get('sender', 'N/A')
            sender_type_map = {
                1: '用户',
                2: '团队成员',
                3: '系统'
            }
            sender_text = sender_type_map.get(sender_type, str(sender_type))
            # 当发送人是团队成员时，sender 是客服的 sys_user_id
            if sender_type == 2:
                print(f"    发送人：{sender_text} (客服 ID: {sender})")
            else:
                print(f"    发送人：{sender_text} ({sender})")
            
            # 消息内容
            text = msg.get('text', '')
            if text:
                # 截断长消息
                if len(text) > 100:
                    text = text[:100] + "..."
                print(f"    内容：{text}")
            
            # 发送时间（毫秒转秒）
            send_time = msg.get('send_time')
            if send_time:
                # 如果是 13 位毫秒时间戳，转换为秒
                if send_time > 1000000000000:
                    send_time = send_time // 1000
                send_dt = datetime.fromtimestamp(send_time)
                print(f"    发送时间：{send_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 已读时间（毫秒转秒）
            read_time = msg.get('read_time')
            if read_time:
                # 如果是 13 位毫秒时间戳，转换为秒
                if read_time > 1000000000000:
                    read_time = read_time // 1000
                read_dt = datetime.fromtimestamp(read_time)
                print(f"    已读时间：{read_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 是否撤回
            is_withdraw = msg.get('is_withdraw')
            if is_withdraw:
                print(f"    状态：已撤回")
            
            # 是否回复
            is_reply = msg.get('is_reply')
            if is_reply:
                print(f"    状态：已回复")
    else:
        print(f"\n⚠️  未找到消息")
    
    print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='SaleSmartly 聊天记录查询工具')
    
    # 查询条件（二选一）
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--chat-user-id', type=str, help='用户 ID（与 --session-id 二选一）')
    group.add_argument('--session-id', type=str, help='会话 ID（与 --chat-user-id 二选一）')
    
    parser.add_argument('--page-size', type=int, default=100, help='每页大小（最大 100）')
    parser.add_argument('--all', action='store_true', help='自动获取所有页面数据（当 total > page_size 时）')
    
    parser.add_argument('--days', type=int, default=None, help='查询最近 N 天的消息')
    parser.add_argument('--start-sequence-id', type=str, default=None, help='开始的消息 ID')
    parser.add_argument('--end-sequence-id', type=str, default=None, help='结束的消息 ID')
    parser.add_argument('--msg-content', type=str, default=None, help='关键词筛选（可选）')
    
    args = parser.parse_args()
    
    query_messages(
        chat_user_id=args.chat_user_id,
        session_id=args.session_id,
        page_size=args.page_size,
        days=args.days,
        start_sequence_id=args.start_sequence_id,
        end_sequence_id=args.end_sequence_id,
        msg_content=args.msg_content,
        all_pages=args.all
    )


if __name__ == "__main__":
    main()
