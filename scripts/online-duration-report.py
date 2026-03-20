#!/usr/bin/env python3
"""
在线时长报表查询脚本

功能：查询客服在指定日期范围内的在线时长统计数据
API：GET /api/v2/get-online-duration-report

作者：SaleSmartly AI Agent
版本：1.0.0
创建时间：2026-03-19
"""

import argparse
import hashlib
import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================================
# 配置
# ============================================================================

# API 配置
API_BASE_URL = "https://developer.salesmartly.com"
API_ENDPOINT = "/api/v2/get-online-duration-report"

# 配置文件路径（相对于脚本所在目录）
CONFIG_DIR = Path(__file__).parent.parent
CONFIG_FILE = CONFIG_DIR / "api-key.json"


# ============================================================================
# 工具函数
# ============================================================================

def load_config():
    """加载 API 配置"""
    if not CONFIG_FILE.exists():
        print(f"❌ 配置文件不存在：{CONFIG_FILE}")
        print(f"   请创建配置文件并填写 API Key 和 Project ID")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    api_key = config.get('apiKey') or config.get('api_key')
    project_id = config.get('projectId') or config.get('project_id')
    
    if not api_key:
        print("❌ 配置文件中缺少 apiKey")
        sys.exit(1)
    
    if not project_id:
        print("❌ 配置文件中缺少 projectId")
        sys.exit(1)
    
    return api_key, project_id


def calculate_sign(api_key, params):
    """
    计算 API 签名
    
    签名规则：
    1. 将所有参数按 ASCII 码升序排序
    2. 拼接成 key=value&key=value 格式
    3. 在开头添加 apiKey
    4. 对整个字符串进行 MD5 加密
    
    Args:
        api_key: API Key
        params: 参数字典
    
    Returns:
        签名（32 位十六进制字符串）
    """
    sign_parts = [api_key]
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    
    sign_str = "&".join(sign_parts)
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    return sign


def format_duration(seconds):
    """
    格式化时长（秒 → 小时：分钟：秒）
    
    Args:
        seconds: 时长（秒）
    
    Returns:
        格式化后的字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}小时{minutes}分钟{secs}秒"
    elif minutes > 0:
        return f"{minutes}分钟{secs}秒"
    else:
        return f"{secs}秒"


def format_duration_hours(seconds):
    """
    格式化时长（秒 → *时*分*秒）
    
    Args:
        seconds: 时长（秒）
    
    Returns:
        格式化后的字符串（*时*分*秒）
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours}时{minutes}分{secs}秒"


# ============================================================================
# API 调用
# ============================================================================

def get_online_duration_report(api_key, project_id, start_date, end_date, sys_user_id=None):
    """
    获取在线时长报表
    
    Args:
        api_key: API Key
        project_id: 项目 ID
        start_date: 开始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
        sys_user_id: 客服 ID（可选，筛选指定客服）
    
    Returns:
        API 返回的数据字典
    """
    # 构建请求参数
    params = {
        'project_id': project_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    if sys_user_id is not None:
        params['sys_user_id'] = sys_user_id
    
    # 计算签名
    sign = calculate_sign(api_key, params)
    
    # 构建请求 URL
    query_string = urllib.parse.urlencode(params)
    url = f"{API_BASE_URL}{API_ENDPOINT}?{query_string}"
    
    # 创建请求
    req = urllib.request.Request(url)
    req.add_header('External-Sign', sign)
    req.add_header('User-Agent', 'SaleSmartly-Agent/1.0')
    
    # SSL 配置（兼容缺少 CA 证书的系统）
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)
            return data
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误：{e.code} {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"❌ 网络错误：{e.reason}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误：{e}")
        return None
    except Exception as e:
        print(f"❌ 未知错误：{e}")
        return None


# ============================================================================
# 输出函数
# ============================================================================

def print_report(data, start_date, end_date, sys_user_id=None):
    """
    打印报表数据
    
    Args:
        data: API 返回的数据
        start_date: 开始日期
        end_date: 结束日期
        sys_user_id: 客服 ID
    """
    if data is None:
        return
    
    if data.get('code') != 0:
        print(f"❌ API 错误：{data.get('msg')}")
        return
    
    report_list = data.get('data', {}).get('list', [])
    
    if not report_list:
        print(f"\n📊 在线时长报表")
        print(f"   日期范围：{start_date} 至 {end_date}")
        print(f"   没有找到数据")
        return
    
    # 打印表头
    print(f"\n📊 在线时长报表")
    print(f"   日期范围：{start_date} 至 {end_date}")
    if sys_user_id:
        print(f"   客服 ID：{sys_user_id}")
    print(f"   共 {len(report_list)} 个客服")
    print()
    
    # 打印表格
    print("=" * 140)
    print(f"{'客服昵称':<30} {'ID':<10} {'登录时长':<20} {'在线时长':<20} {'忙碌时长':<20} {'离线时长':<20}")
    print("-" * 140)
    
    # 统计总计
    total_login = 0
    total_online = 0
    total_busy = 0
    total_offline = 0
    
    for item in report_list:
        nickname = item.get('nickname', 'N/A')
        uid = item.get('sys_user_id', 0)
        login_duration = item.get('login_duration', 0)
        online_duration = item.get('online_duration', 0)
        busy_duration = item.get('busy_duration', 0)
        offline_duration = item.get('offline_duration', 0)
        
        print(f"{nickname:<30} {uid:<10} {format_duration_hours(login_duration):<20} "
              f"{format_duration_hours(online_duration):<20} {format_duration_hours(busy_duration):<20} "
              f"{format_duration_hours(offline_duration):<20}")
        
        total_login += login_duration
        total_online += online_duration
        total_busy += busy_duration
        total_offline += offline_duration
    
    # 打印总计
    print("-" * 140)
    print(f"{'总计':<30} {'':<10} {format_duration_hours(total_login):<20} "
          f"{format_duration_hours(total_online):<20} {format_duration_hours(total_busy):<20} "
          f"{format_duration_hours(total_offline):<20}")
    print("=" * 140)
    
    # 打印详细时长（秒）
    print(f"\n📝 详细数据（秒）:")
    print(f"   总登录时长：{format_duration(total_login)}")
    print(f"   总在线时长：{format_duration(total_online)}")
    print(f"   总忙碌时长：{format_duration(total_busy)}")
    print(f"   总离线时长：{format_duration(total_offline)}")
    
    # 计算比例
    if total_login > 0:
        online_ratio = (total_online / total_login) * 100
        busy_ratio = (total_busy / total_login) * 100
        offline_ratio = (total_offline / total_login) * 100
        
        print(f"\n📈 状态比例（占登录时长）:")
        print(f"   在线：{online_ratio:.1f}%")
        print(f"   忙碌：{busy_ratio:.1f}%")
        print(f"   离线：{offline_ratio:.1f}%")


def print_json(data):
    """
    以 JSON 格式输出
    
    Args:
        data: API 返回的数据
    """
    if data:
        print(json.dumps(data, ensure_ascii=False, indent=2))


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='在线时长报表查询脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询今天的在线时长
  python online-duration-report.py --today
  
  # 查询昨天的在线时长
  python online-duration-report.py --yesterday
  
  # 查询指定日期范围
  python online-duration-report.py --start 2026-03-01 --end 2026-03-31
  
  # 查询指定客服的在线时长
  python online-duration-report.py --today --user-id 36294
  
  # 输出 JSON 格式
  python online-duration-report.py --today --json
        """
    )
    
    # 日期参数（互斥组）
    date_group = parser.add_mutually_exclusive_group(required=True)
    date_group.add_argument('--today', action='store_true',
                           help='查询今天')
    date_group.add_argument('--yesterday', action='store_true',
                           help='查询昨天')
    date_group.add_argument('--start', type=str, metavar='DATE',
                           help='开始日期（YYYY-MM-DD）')
    date_group.add_argument('--days', type=int, metavar='N',
                           help='查询最近 N 天')
    
    # 结束日期
    parser.add_argument('--end', type=str, metavar='DATE',
                       help='结束日期（YYYY-MM-DD），与 --start 配合使用')
    
    # 客服筛选
    parser.add_argument('--user-id', type=int, metavar='ID',
                       help='客服 ID，筛选指定客服')
    
    # 输出格式
    parser.add_argument('--json', action='store_true',
                       help='输出 JSON 格式')
    
    # 配置覆盖
    parser.add_argument('--api-key', type=str,
                       help='API Key（覆盖配置文件）')
    parser.add_argument('--project-id', type=str,
                       help='Project ID（覆盖配置文件）')
    
    args = parser.parse_args()
    
    # 加载配置
    api_key = args.api_key
    project_id = args.project_id
    
    if not api_key or not project_id:
        api_key, project_id = load_config()
    
    # 计算日期范围
    today = datetime.now().date()
    
    if args.today:
        start_date = today
        end_date = today
    elif args.yesterday:
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif args.start:
        start_date = datetime.strptime(args.start, '%Y-%m-%d').date()
        if args.end:
            end_date = datetime.strptime(args.end, '%Y-%m-%d').date()
        else:
            end_date = start_date
    elif args.days:
        end_date = today
        start_date = today - timedelta(days=args.days - 1)
    else:
        print("❌ 请指定日期范围")
        sys.exit(1)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # 调用 API
    data = get_online_duration_report(
        api_key=api_key,
        project_id=project_id,
        start_date=start_date_str,
        end_date=end_date_str,
        sys_user_id=args.user_id
    )
    
    # 输出结果
    if args.json:
        print_json(data)
    else:
        print_report(data, start_date_str, end_date_str, args.user_id)


if __name__ == '__main__':
    main()
