#!/usr/bin/env python3
"""
技能包意图识别测试工具

测试 salesmartly-api-skills 在不同 LLM 模型下的意图识别准确率
"""

import json
import sys
import httpx
from pathlib import Path
from typing import Dict, Any, List


# ==================== 测试用例 ====================

TEST_CASES = [
    # 简单查询
    {
        "id": "001",
        "input": "昨天的客户",
        "expected": {
            "script": "query-customers.py",
            "params": {"days": 1, "filter-by": "created"},
            "min_confidence": 0.9
        },
        "category": "简单查询"
    },
    {
        "id": "002",
        "input": "今天销售怎么样",
        "expected": {
            "script": "daily-sales-report.py",
            "params": {"today": True},
            "min_confidence": 0.9
        },
        "category": "简单查询"
    },
    {
        "id": "003",
        "input": "查张三的聊天记录",
        "expected": {
            "script": "query-messages.py",
            "params": {"chat-user-id": "张三"},
            "min_confidence": 0.9
        },
        "category": "简单查询"
    },
    
    # 复杂查询
    {
        "id": "004",
        "input": "最近 7 天 VIP 客户有哪些",
        "expected": {
            "script": "query-customers.py",
            "params": {"days": 7, "tags": "VIP"},
            "min_confidence": 0.85
        },
        "category": "复杂查询"
    },
    {
        "id": "005",
        "input": "把客户张三分配给客服 li.jian",
        "expected": {
            "script": "assign-session.py",
            "params": {"chat-user-id": "张三", "member-id": "li.jian"},
            "min_confidence": 0.9
        },
        "category": "复杂查询"
    },
    
    # 模糊意图（应该澄清）
    {
        "id": "006",
        "input": "客户张三",
        "expected": {
            "needs_clarification": True,
            "reason": "动作不明确"
        },
        "category": "模糊意图"
    },
    {
        "id": "007",
        "input": "查销售",
        "expected": {
            "needs_clarification": True,
            "reason": "时间范围不明确"
        },
        "category": "模糊意图"
    },
    
    # 边界情况
    {
        "id": "008",
        "input": "所有客户",
        "expected": {
            "script": "query-customers.py",
            "params": {"all": True},
            "min_confidence": 0.85
        },
        "category": "边界情况"
    },
    {
        "id": "009",
        "input": "WhatsApp 设备",
        "expected": {
            "script": "query-whatsapp-apps.py",
            "params": {},
            "min_confidence": 0.85
        },
        "category": "边界情况"
    },
    
    # 多步骤操作
    {
        "id": "010",
        "input": "给所有 VIP 客户发消息",
        "expected": {
            "multi_step": True,
            "steps": [
                {"script": "query-customers.py", "params": {"tags": "VIP"}},
                {"script": "batch-send-message.py", "needs_confirm": True}
            ]
        },
        "category": "多步骤"
    },
]


# ==================== 测试执行 ====================

class IntentRecognitionTester:
    def __init__(self, model_config: Dict[str, Any]):
        self.model = model_config.get("model", "qwen3.5-plus")
        self.api_key = model_config.get("api_key", "")
        self.base_url = model_config.get("base_url", "https://api.dashscope.ai/v1")
        self.skill_md_path = model_config.get("skill_md_path", "SKILL.md")
    
    def load_skill_context(self) -> str:
        """加载 SKILL.md 作为上下文"""
        skill_path = Path(self.skill_md_path)
        if not skill_path.exists():
            return ""
        
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
            # 只取关键部分（避免 token 过多）
            return content[:10000]  # 限制 10K tokens
    
    def build_prompt(self, user_input: str) -> tuple:
        """构建测试 Prompt"""
        skill_context = self.load_skill_context()
        
        system_prompt = f"""你是 SaleSmartly 助手。根据以下技能文档，分析用户意图并调用对应脚本。

## 技能文档摘要
{skill_context[:5000]}

## 输出格式
必须输出 JSON：
```json
{{
  "script": "脚本名.py",
  "params": {{"参数名": "参数值"}},
  "confidence": 0.0-1.0,
  "reasoning": "识别理由"
}}
```

如果意图不明确，输出：
```json
{{
  "needs_clarification": true,
  "question": "澄清问题"
}}
```

## 示例
用户：昨天的客户
输出：{{"script": "query-customers.py", "params": {{"days": 1, "filter-by": "created"}}, "confidence": 0.95}}

用户：客户张三
输出：{{"needs_clarification": true, "question": "请问您要查询、创建还是更新客户张三？"}}
"""
        
        user_prompt = f"用户消息：{user_input}"
        
        return system_prompt, user_prompt
    
    def call_llm(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """调用 LLM"""
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"}
                    }
                )
                resp.raise_for_status()
                result = resp.json()
                content = result["choices"][0]["message"]["content"]
                
                # 解析 JSON
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"error": "无法解析 JSON", "raw": content}
        
        except Exception as e:
            return {"error": str(e)}
    
    def evaluate_result(self, result: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
        """评估结果"""
        evaluation = {
            "passed": False,
            "score": 0.0,
            "details": []
        }
        
        # 检查是否需要澄清
        if expected.get("needs_clarification"):
            if result.get("needs_clarification"):
                evaluation["passed"] = True
                evaluation["score"] = 1.0
                evaluation["details"].append("✅ 正确识别需要澄清")
            else:
                evaluation["details"].append("❌ 应该澄清但未澄清")
            return evaluation
        
        # 检查脚本名
        if result.get("script") == expected.get("script"):
            evaluation["details"].append(f"✅ 脚本正确：{result['script']}")
            evaluation["score"] += 0.5
        else:
            evaluation["details"].append(f"❌ 脚本错误：期望 {expected.get('script')}, 实际 {result.get('script')}")
        
        # 检查参数
        expected_params = expected.get("params", {})
        result_params = result.get("params", {})
        
        param_match = 0
        param_total = len(expected_params)
        
        for key, value in expected_params.items():
            if result_params.get(key) == value:
                param_match += 1
        
        if param_total > 0:
            param_score = param_match / param_total
            evaluation["score"] += param_score * 0.5
            evaluation["details"].append(f"{'✅' if param_match == param_total else '⚠️'} 参数匹配：{param_match}/{param_total}")
        
        # 检查置信度
        min_confidence = expected.get("min_confidence", 0.0)
        result_confidence = result.get("confidence", 0.0)
        
        if result_confidence >= min_confidence:
            evaluation["details"].append(f"✅ 置信度：{result_confidence:.2f} >= {min_confidence}")
        else:
            evaluation["details"].append(f"⚠️ 置信度偏低：{result_confidence:.2f} < {min_confidence}")
        
        # 判断是否通过
        evaluation["passed"] = evaluation["score"] >= 0.8
        
        return evaluation
    
    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试用例"""
        print(f"\n测试用例 #{test_case['id']}: {test_case['input']}")
        print("-" * 60)
        
        # 构建 Prompt
        system_prompt, user_prompt = self.build_prompt(test_case["input"])
        
        # 调用 LLM
        print(f"调用模型：{self.model}...")
        result = self.call_llm(system_prompt, user_prompt)
        
        # 评估结果
        evaluation = self.evaluate_result(result, test_case["expected"])
        
        # 输出结果
        print(f"LLM 输出：{json.dumps(result, ensure_ascii=False, indent=2)}")
        print(f"评估结果:")
        for detail in evaluation["details"]:
            print(f"  {detail}")
        print(f"得分：{evaluation['score']:.2f}/1.00 - {'✅ 通过' if evaluation['passed'] else '❌ 失败'}")
        
        return {
            "test_case": test_case,
            "result": result,
            "evaluation": evaluation
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 60)
        print(f"意图识别测试 - 模型：{self.model}")
        print("=" * 60)
        
        results = []
        passed = 0
        failed = 0
        
        for test_case in TEST_CASES:
            result = self.run_test(test_case)
            results.append(result)
            
            if result["evaluation"]["passed"]:
                passed += 1
            else:
                failed += 1
        
        # 汇总报告
        print("\n" + "=" * 60)
        print("测试汇总报告")
        print("=" * 60)
        print(f"总用例数：{len(TEST_CASES)}")
        print(f"通过：{passed} ({passed/len(TEST_CASES)*100:.1f}%)")
        print(f"失败：{failed} ({failed/len(TEST_CASES)*100:.1f}%)")
        print(f"模型：{self.model}")
        
        # 分类统计
        categories = {}
        for result in results:
            category = result["test_case"]["category"]
            if category not in categories:
                categories[category] = {"passed": 0, "total": 0}
            categories[category]["total"] += 1
            if result["evaluation"]["passed"]:
                categories[category]["passed"] += 1
        
        print("\n分类统计:")
        for category, stats in categories.items():
            rate = stats["passed"] / stats["total"] * 100
            print(f"  {category}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        return {
            "model": self.model,
            "total": len(TEST_CASES),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(TEST_CASES),
            "categories": categories,
            "details": results
        }


# ==================== 主函数 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="技能包意图识别测试工具")
    parser.add_argument("--model", default="qwen3.5-plus", help="模型名称")
    parser.add_argument("--api-key", help="API Key")
    parser.add_argument("--base-url", default="https://api.dashscope.ai/v1", help="API 基础 URL")
    parser.add_argument("--skill-md", default="SKILL.md", help="SKILL.md 文件路径")
    parser.add_argument("--output", help="输出报告文件（JSON）")
    
    args = parser.parse_args()
    
    # 配置
    config = {
        "model": args.model,
        "api_key": args.api_key or "sk-xxx",  # 从环境变量或配置文件读取
        "base_url": args.base_url,
        "skill_md_path": args.skill_md
    }
    
    # 运行测试
    tester = IntentRecognitionTester(config)
    report = tester.run_all_tests()
    
    # 保存报告
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存到：{args.output}")
    
    # 返回退出码
    sys.exit(0 if report["pass_rate"] >= 0.8 else 1)


if __name__ == "__main__":
    main()
