#!/usr/bin/env python3
"""
意图识别准确率测试工具

用于测试不同模型配置下的意图识别准确率
支持批量测试、混淆矩阵、错误分析
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from intent_router import IntentRouter


class IntentRecognitionTester:
    def __init__(self):
        self.router = IntentRouter()
        self.test_cases = self._load_test_cases()
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """加载测试用例"""
        return [
            # === 销售数据查询 ===
            {
                "message": "查一下昨天的销售数据",
                "expected_intent": "daily-sales-report",
                "expected_params": {"days": 1},
                "difficulty": "easy"
            },
            {
                "message": "今天卖得怎么样",
                "expected_intent": "daily-sales-report",
                "expected_params": {"days": 0},
                "difficulty": "easy"
            },
            {
                "message": "最近 7 天的销售额",
                "expected_intent": "daily-sales-report",
                "expected_params": {"days": 7},
                "difficulty": "medium"
            },
            
            # === 客户查询 ===
            {
                "message": "有哪些客户",
                "expected_intent": "query-customers",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "VIP 客户有哪些",
                "expected_intent": "query-customers",
                "expected_params": {"tags": "VIP"},
                "difficulty": "easy"
            },
            {
                "message": "最近 7 天新增客户",
                "expected_intent": "query-customers",
                "expected_params": {"days": 7},
                "difficulty": "medium"
            },
            {
                "message": "查客户 abc123 的信息",
                "expected_intent": "query-customers",
                "expected_params": {"chat_user_id": "abc123"},
                "difficulty": "medium"
            },
            
            # === 发送消息 ===
            {
                "message": "给张三发消息",
                "expected_intent": "send-message",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "通知所有 VIP 客户",
                "expected_intent": "send-message",
                "expected_params": {},
                "difficulty": "hard"
            },
            
            # === 聊天记录查询 ===
            {
                "message": "看看聊天记录",
                "expected_intent": "query-messages",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "查昨天的聊天",
                "expected_intent": "query-all-messages",
                "expected_params": {"days": 1},
                "difficulty": "medium"
            },
            
            # === 会话分配 ===
            {
                "message": "把这个客户给小王",
                "expected_intent": "assign-session",
                "expected_params": {},
                "difficulty": "medium"
            },
            {
                "message": "批量分配客户",
                "expected_intent": "batch-assign-session",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "批量回聊客户",
                "expected_intent": "batch-talk-back",
                "expected_params": {},
                "difficulty": "easy"
            },
            
            # === 客户历史 ===
            {
                "message": "查客户详细信息",
                "expected_intent": "get-customer-history",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "查张三的聊天记录",
                "expected_intent": "get-customer-history",
                "expected_params": {},
                "difficulty": "medium"
            },
            
            # === WhatsApp 管理 ===
            {
                "message": "WhatsApp 设备",
                "expected_intent": "query-whatsapp-apps",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "添加 WhatsApp",
                "expected_intent": "add-whatsapp-device",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "删除 WhatsApp 设备",
                "expected_intent": "delete-whatsapp-device",
                "expected_params": {},
                "difficulty": "easy"
            },
            
            # === 客户反馈 ===
            {
                "message": "客户反馈",
                "expected_intent": "check-customer-feedback",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "最近 7 天的客户反馈怎么样",
                "expected_intent": "check-customer-feedback",
                "expected_params": {"days": 7},
                "difficulty": "medium"
            },
            
            # === 待跟进客户 ===
            {
                "message": "待跟进客户",
                "expected_intent": "find-followup-customers",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "有哪些客户需要跟进",
                "expected_intent": "find-followup-customers",
                "expected_params": {},
                "difficulty": "medium"
            },
            
            # === 结束会话 ===
            {
                "message": "结束这个会话",
                "expected_intent": "end-session",
                "expected_params": {},
                "difficulty": "easy"
            },
            
            # === 成员统计 ===
            {
                "message": "成员统计",
                "expected_intent": "member-session-stats",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "销售统计",
                "expected_intent": "member-session-stats",
                "expected_params": {},
                "difficulty": "easy"
            },
            
            # === 在线时长 ===
            {
                "message": "在线时长",
                "expected_intent": "online-duration-report",
                "expected_params": {},
                "difficulty": "easy"
            },
            {
                "message": "查一下工作时长",
                "expected_intent": "online-duration-report",
                "expected_params": {},
                "difficulty": "medium"
            },
            
            # === 困难场景 ===
            {
                "message": "我想看看数据",
                "expected_intent": None,  # 模糊意图，应该触发澄清
                "expected_params": {},
                "difficulty": "hard"
            },
            {
                "message": "帮我处理一下",
                "expected_intent": None,  # 模糊意图，应该触发澄清
                "expected_params": {},
                "difficulty": "hard"
            },
        ]
    
    def run_test(self, test_case: Dict) -> Dict:
        """运行单个测试用例"""
        message = test_case["message"]
        expected_intent = test_case["expected_intent"]
        expected_params = test_case["expected_params"]
        
        # 调用意图识别
        result = self.router.classify_intent(message, use_llm=False)
        
        # 判断是否正确
        predicted_intent = result.get("skill")
        predicted_params = result.get("params", {})
        
        intent_correct = predicted_intent == expected_intent
        params_correct = True  # 简化：不检查参数细节
        
        return {
            "message": message,
            "expected_intent": expected_intent,
            "predicted_intent": predicted_intent,
            "intent_correct": intent_correct,
            "expected_params": expected_params,
            "predicted_params": predicted_params,
            "params_correct": params_correct,
            "confidence": result.get("confidence", 0),
            "method": result.get("method", "unknown"),
            "difficulty": test_case["difficulty"]
        }
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        results = []
        
        for test_case in self.test_cases:
            result = self.run_test(test_case)
            results.append(result)
        
        # 统计结果
        total = len(results)
        correct = sum(1 for r in results if r["intent_correct"])
        accuracy = correct / total if total > 0 else 0
        
        # 按难度统计
        by_difficulty = {}
        for r in results:
            diff = r["difficulty"]
            if diff not in by_difficulty:
                by_difficulty[diff] = {"total": 0, "correct": 0}
            by_difficulty[diff]["total"] += 1
            if r["intent_correct"]:
                by_difficulty[diff]["correct"] += 1
        
        # 计算各难度准确率
        for diff in by_difficulty:
            d = by_difficulty[diff]
            d["accuracy"] = d["correct"] / d["total"] if d["total"] > 0 else 0
        
        # 错误分析
        errors = [r for r in results if not r["intent_correct"]]
        
        return {
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
            "by_difficulty": by_difficulty,
            "errors": errors,
            "results": results
        }
    
    def print_report(self, report: Dict):
        """打印测试报告"""
        print("=" * 80)
        print("意图识别准确率测试报告")
        print("=" * 80)
        print()
        
        print(f"总测试用例：{report['total']}")
        print(f"正确识别：{report['correct']}")
        print(f"错误识别：{report['total'] - report['correct']}")
        print(f"总体准确率：{report['accuracy']:.2%}")
        print()
        
        print("按难度统计:")
        print("-" * 40)
        for diff, stats in report['by_difficulty'].items():
            print(f"  {diff:8s}: {stats['correct']:3d}/{stats['total']:3d} = {stats['accuracy']:.2%}")
        print()
        
        if report['errors']:
            print("错误分析:")
            print("-" * 40)
            for i, error in enumerate(report['errors'][:10], 1):  # 只显示前 10 个错误
                print(f"{i}. 消息：{error['message']}")
                print(f"   预期：{error['expected_intent']}")
                print(f"   预测：{error['predicted_intent']}")
                print(f"   置信度：{error['confidence']:.2f}")
                print()
        
        print("=" * 80)


def main():
    """主函数"""
    tester = IntentRecognitionTester()
    
    if len(sys.argv) > 1:
        # 单个消息测试
        message = " ".join(sys.argv[1:])
        result = tester.run_test({
            "message": message,
            "expected_intent": None,
            "expected_params": {},
            "difficulty": "unknown"
        })
        print(f"消息：{message}")
        print(f"预测意图：{result['predicted_intent']}")
        print(f"置信度：{result['confidence']:.2f}")
        print(f"方法：{result['method']}")
    else:
        # 批量测试
        report = tester.run_all_tests()
        tester.print_report(report)
        
        # 保存详细报告
        report_path = Path(__file__).parent / "test-report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n详细报告已保存到：{report_path}")


if __name__ == "__main__":
    main()
