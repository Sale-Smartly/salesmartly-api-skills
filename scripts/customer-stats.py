#!/usr/bin/env python3
"""
客户统计分析 - 深度分析客户数据

功能:
- 客户总量统计
- 客户来源分析
- 客户标签分布
- 活跃客户统计
- 新增客户趋势

使用:
uv run scripts/customer-stats.py
uv run scripts/customer-stats.py --days 30
"""

import json
import sys
import urllib.request
import urllib.parse
import ssl
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# 加载 API 配置
SCRIPT_DIR = Path(__file__).parent.absolute()
API_CONFIG = SCRIPT_DIR / "api-key.json"

if not API_CONFIG.exists():
    # 尝试工作目录
    API_CONFIG = Path("api-key.json")
    
if not API_CONFIG.exists():
    print("❌ 错误：api-key.json 不存在")
    print("请先配置 API Key")
    sys.exit(1)

with open(API_CONFIG, 'r') as f:
    config = json.load(f)

API_KEY = config.get("apiKey")
PROJECT_ID = config.get("projectId")
BASE_URL = "https://developer.salesmartly.com"

def get_sign(params):
    """生成 API 签名"""
    import hashlib
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_parts = [API_KEY]
    for k, v in sorted_params:
        sign_parts.append(f"{k}={v}")
    sign_str = "&".join(sign_parts)
    return hashlib.md5(sign_str.encode()).hexdigest()

def api_request(endpoint, params=None):
    """发送 API 请求"""
    if params is None:
        params = {}
    
    params["project_id"] = PROJECT_ID
    sign = get_sign(params)
    
    # 构建查询字符串（不包含 sign）
    query_params = dict(params)
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    url = f"{BASE_URL}{endpoint}?{query_string}"
    
    try:
        # 创建 SSL 上下文（跳过证书验证）
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        # 添加 External-Sign header（sign 只在 header 里）
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SaleSmartly-Agent/1.0",
            "External-Sign": sign
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"❌ API 请求失败：{e}")
        return None

def get_all_customers(days=30):
    """获取所有客户数据"""
    # 计算时间范围
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())
    
    import json
    updated_time_str = json.dumps({"start": start_time, "end": end_time}, separators=(',', ':'))
    
    all_customers = []
    page = 1
    page_size = 100
    
    while True:
        params = {
            "page": str(page),
            "page_size": str(page_size),
            "updated_time": updated_time_str
        }
        
        result = api_request("/api/v2/get-contact-list", params)
        if not result or result.get("code") != 0:
            break
        
        customers = result.get("data", {}).get("contact_list", [])
        if not customers:
            break
        
        all_customers.extend(customers)
        
        # 检查是否还有更多数据
        total = result.get("data", {}).get("total", 0)
        if len(all_customers) >= total:
            break
        
        page += 1
    
    return all_customers

def analyze_customers(customers):
    """分析客户数据"""
    if not customers:
        return {}
    
    # 标签统计
    all_tags = []
    for customer in customers:
        tags = customer.get("tags", [])
        if tags:
            all_tags.extend(tags)
    
    tag_counts = Counter(all_tags)
    
    # 来源统计（如果有）
    sources = Counter(c.get("source", "未知") for c in customers)
    
    # 意向度统计（如果有）
    intentions = Counter(c.get("intention", "未知") for c in customers)
    
    # 负责人统计
    owners = Counter(c.get("owner_name", "未分配") for c in customers)
    
    return {
        "total": len(customers),
        "tags": tag_counts,
        "sources": sources,
        "intentions": intentions,
        "owners": owners
    }

def generate_report(days=30):
    """生成客户分析报告"""
    print("\n" + "=" * 60)
    print("📊 客户统计分析报告")
    print("=" * 60)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    print(f"\n📅 分析周期：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print("-" * 60)
    
    # 获取客户数据
    print("\n⏳ 正在获取客户数据...")
    customers = get_all_customers(days)
    print(f"✅ 获取到 {len(customers)} 个客户")
    
    # 分析数据
    if customers:
        stats = analyze_customers(customers)
    else:
        stats = {"total": 0, "tags": Counter(), "sources": Counter(), "intentions": Counter(), "owners": Counter()}
    
    # 总体统计
    print(f"\n📈 总体统计")
    print(f"   客户总数：{stats['total']} 个")
    if days < 30:
        print(f"   平均每天新增：{stats['total'] / days:.1f} 个")
    
    # 标签分布
    if stats['tags']:
        print(f"\n🏷️  客户标签分布 (Top 10)")
        for tag, count in stats['tags'].most_common(10):
            percentage = (count / stats['total']) * 100
            bar = "█" * int(percentage / 2)
            print(f"   {tag:15} {count:4}个 ({percentage:5.1f}%) {bar}")
    
    # 意向度分布
    if stats['intentions'] and any(k != "未知" for k in stats['intentions'].keys()):
        print(f"\n🎯 客户意向度分布")
        for intention, count in stats['intentions'].most_common():
            if intention != "未知":
                percentage = (count / stats['total']) * 100
                bar = "█" * int(percentage / 2)
                print(f"   {intention:15} {count:4}个 ({percentage:5.1f}%) {bar}")
    
    # 负责人分布
    if stats['owners']:
        print(f"\n👔 客户负责人分布 (Top 5)")
        for owner, count in stats['owners'].most_common(5):
            percentage = (count / stats['total']) * 100
            bar = "█" * int(percentage / 2)
            print(f"   {owner:15} {count:4}个 ({percentage:5.1f}%) {bar}")
    
    # 建议
    print(f"\n💡 优化建议")
    if stats['tags']:
        top_tag = stats['tags'].most_common(1)[0]
        print(f"   - 最多客户标签：{top_tag[0]} ({top_tag[1]}个)")
    
    if stats['intentions']:
        high_intent = sum(c for i, c in stats['intentions'].items() if i in ["高", "很高", "A", "B"])
        if high_intent:
            print(f"   - 高意向客户：{high_intent}个 (占比 {high_intent/stats['total']*100:.1f}%)")
    
    print("\n" + "=" * 60)
    print("💡 提示：运行 'uv run scripts/daily-sales-report.py' 查看每日报告")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="客户统计分析")
    parser.add_argument("--days", type=int, default=30, help="分析最近 N 天 (默认 30)")
    
    args = parser.parse_args()
    
    generate_report(args.days)
