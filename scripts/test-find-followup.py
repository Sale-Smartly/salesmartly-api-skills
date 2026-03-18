#!/usr/bin/env python3
"""
SaleSmartly 脚本自动化测试

测试 find-followup-customers.py 的功能

Usage:
    uv run scripts/test-find-followup.py
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
            timeout=120,
            cwd="/home/admin/.openclaw/workspace/skills/salesmartly-agent"
        )
        
        success = result.returncode == 0
        
        if success:
            print(f"✅ 测试通过")
        else:
            print(f"❌ 测试失败")
            print(f"错误输出：{result.stderr}")
        
        # 检查关键输出
        output = result.stdout + result.stderr
        
        return {
            'success': success,
            'output': output,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ 测试超时（>120 秒）")
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


def test_basic_query():
    """测试基本查询功能"""
    result = run_command(
        ['uv', 'run', 'scripts/find-followup-customers.py', '--days', '7', '--limit', '5'],
        '基本查询（7 天未联系，限制 5 个）'
    )
    
    if not result['success']:
        return False
    
    # 检查关键输出
    checks = [
        ('正在获取客户数据', '获取客户'),
        ('个唯一客户', '去重统计'),
        ('正在分析客户联系情况', '分析联系情况'),
        ('找到', '找到结果'),
        ('个需要跟进的客户', '结果统计'),
    ]
    
    all_passed = True
    for keyword, desc in checks:
        if not check_output_contains(result['output'], [keyword], desc):
            all_passed = False
    
    return all_passed


def test_dingtalk_notification():
    """测试钉钉推送功能"""
    result = run_command(
        ['uv', 'run', 'scripts/find-followup-customers.py', '--days', '7', '--limit', '5', '--dingtalk'],
        '钉钉推送测试'
    )
    
    if not result['success']:
        return False
    
    # 检查钉钉发送成功
    return check_output_contains(result['output'], ['钉钉通知已发送'], '钉钉推送确认')


def test_different_days():
    """测试不同天数参数"""
    test_cases = [
        ('1', '1 天未联系'),
        ('3', '3 天未联系'),
        ('30', '30 天未联系'),
    ]
    
    all_passed = True
    for days, desc in test_cases:
        result = run_command(
            ['uv', 'run', 'scripts/find-followup-customers.py', '--days', days, '--limit', '3'],
            f'参数测试：{desc}'
        )
        
        if not result['success']:
            all_passed = False
    
    return all_passed


def test_performance():
    """测试性能（处理速度）"""
    print(f"\n{'='*60}")
    print(f"⚡ 性能测试")
    print(f"{'='*60}\n")
    
    start_time = datetime.now()
    
    result = run_command(
        ['uv', 'run', 'scripts/find-followup-customers.py', '--days', '7', '--limit', '20'],
        '性能测试（全量处理）'
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n⏱️  执行时间：{duration:.2f} 秒")
    
    # 性能标准：应该在 2 分钟内完成
    if duration < 120:
        print(f"✅ 性能达标（< 120 秒）")
        return True
    else:
        print(f"⚠️  性能较慢（> 120 秒），建议优化")
        return True  # 不视为失败，只是警告


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🚀 SaleSmartly 脚本自动化测试")
    print("="*70)
    print(f"📅 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    tests = [
        ('基本查询测试', test_basic_query),
        ('不同天数参数测试', test_different_days),
        ('钉钉推送测试', test_dingtalk_notification),
        ('性能测试', test_performance),
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
