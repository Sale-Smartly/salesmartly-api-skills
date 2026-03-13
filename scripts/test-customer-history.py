#!/usr/bin/env python3
"""
SalesSmartly 客户历史查询 - 自动化测试

测试 get-customer-history.py 的功能

Usage:
    uv run scripts/test-customer-history.py
"""

import sys
import subprocess
import json
from datetime import datetime


def run_command(cmd, description):
    """运行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"🧪 测试：{description}")
    print(f"📝 命令：{' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd="/home/admin/.openclaw/workspace/skills/salesmartly-agent"
        )
        
        success = result.returncode == 0
        
        if success:
            print(f"✅ 测试通过")
        else:
            print(f"❌ 测试失败")
            print(f"错误输出：{result.stderr[:500] if result.stderr else '无'}")
        
        output = result.stdout + result.stderr
        
        return {
            'success': success,
            'output': output,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ 测试超时（>60 秒）")
        return {'success': False, 'output': 'Timeout', 'returncode': -1}
    except Exception as e:
        print(f"❌ 测试异常：{e}")
        return {'success': False, 'output': str(e), 'returncode': -1}


def check_output_contains(output, keywords, description):
    """检查输出是否包含关键词"""
    print(f"\n🔍 检查：{description}")
    
    all_found = True
    for keyword in keywords:
        if keyword in output:
            print(f"  ✅ 找到：{keyword}")
        else:
            print(f"  ❌ 未找到：{keyword}")
            all_found = False
    
    return all_found


def get_test_customer_id():
    """获取一个测试客户 ID"""
    print("\n📋 准备测试数据：获取客户 ID...")
    
    result = subprocess.run(
        ['uv', 'run', 'scripts/query-customers.py', '--page', '1', '--page-size', '1'],
        capture_output=True,
        text=True,
        timeout=30,
        cwd="/home/admin/.openclaw/workspace/skills/salesmartly-agent"
    )
    
    output = result.stdout
    
    # 提取客户 ID
    for line in output.split('\n'):
        if 'ID:' in line:
            customer_id = line.split('ID:')[1].strip()
            print(f"✅ 获取到测试客户 ID: {customer_id}")
            return customer_id
    
    print("❌ 未找到客户 ID")
    return None


def test_query_by_id(customer_id):
    """测试通过 ID 查询"""
    result = run_command(
        ['uv', 'run', 'scripts/get-customer-history.py', '--chat-user-id', customer_id, '--days', '30'],
        '通过客户 ID 查询'
    )
    
    if not result['success']:
        return False
    
    checks = [
        ('找到客户', '找到客户'),
        ('基本信息', '基本信息'),
        ('聊天统计', '聊天统计'),
        ('跟进建议', '跟进建议'),
    ]
    
    all_passed = True
    for keyword, desc in checks:
        if not check_output_contains(result['output'], [keyword], desc):
            all_passed = False
    
    return all_passed


def test_query_by_phone():
    """测试通过手机号查询（需要一个真实存在的手机号）"""
    # 先获取一个有手机号的客户
    print("\n📋 准备测试数据：获取有手机号的客户...")
    
    result = subprocess.run(
        ['uv', 'run', 'scripts/query-customers.py', '--page', '1', '--page-size', '20'],
        capture_output=True,
        text=True,
        timeout=30,
        cwd="/home/admin/.openclaw/workspace/skills/salesmartly-agent"
    )
    
    output = result.stdout
    
    # 查找手机号
    phone = None
    for line in output.split('\n'):
        if '电话：' in line:
            phone = line.split('电话：')[1].strip()
            break
    
    if not phone:
        print("⚠️  跳过手机号测试（未找到有手机号的客户）")
        return True  # 不视为失败
    
    print(f"✅ 找到测试手机号：{phone}")
    
    result = run_command(
        ['uv', 'run', 'scripts/get-customer-history.py', '--phone', phone, '--days', '7'],
        f'通过手机号查询 ({phone})'
    )
    
    if not result['success']:
        return False
    
    return check_output_contains(result['output'], ['找到客户'], '找到客户')


def test_different_days():
    """测试不同天数参数"""
    customer_id = get_test_customer_id()
    if not customer_id:
        return False
    
    test_cases = [
        ('7', '7 天'),
        ('30', '30 天'),
    ]
    
    all_passed = True
    for days, desc in test_cases:
        result = run_command(
            ['uv', 'run', 'scripts/get-customer-history.py', '--chat-user-id', customer_id, '--days', days],
            f'参数测试：{desc}'
        )
        
        if not result['success']:
            all_passed = False
    
    return all_passed


def test_dingtalk_notification():
    """测试钉钉推送"""
    customer_id = get_test_customer_id()
    if not customer_id:
        return False
    
    result = run_command(
        ['uv', 'run', 'scripts/get-customer-history.py', '--chat-user-id', customer_id, '--days', '7', '--dingtalk'],
        '钉钉推送测试'
    )
    
    if not result['success']:
        return False
    
    return check_output_contains(result['output'], ['钉钉通知已发送'], '钉钉推送确认')


def test_missing_parameter():
    """测试缺少参数的错误处理"""
    print(f"\n{'='*60}")
    print(f"🧪 测试：错误处理（缺少参数）")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        ['uv', 'run', 'scripts/get-customer-history.py'],
        capture_output=True,
        text=True,
        timeout=30,
        cwd="/home/admin/.openclaw/workspace/skills/salesmartly-agent"
    )
    
    # 应该返回错误
    if '必须指定' in result.stdout or '必须指定' in result.stderr:
        print(f"✅ 错误处理正确")
        return True
    else:
        print(f"❌ 错误处理不正确")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🚀 SalesSmartly 客户历史查询 - 自动化测试")
    print("="*70)
    print(f"📅 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 先获取测试客户 ID
    customer_id = get_test_customer_id()
    if not customer_id:
        print("\n❌ 无法获取测试客户 ID，终止测试")
        return 1
    
    tests = [
        ('通过 ID 查询测试', lambda: test_query_by_id(customer_id)),
        ('通过手机号查询测试', test_query_by_phone),
        ('不同天数参数测试', test_different_days),
        ('钉钉推送测试', lambda: test_dingtalk_notification()),
        ('错误处理测试', test_missing_parameter),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ 测试异常：{name} - {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计：{passed_count}/{total_count} 测试通过")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
