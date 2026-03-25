#!/usr/bin/env python3
"""
意图识别路由器（增强版）
支持关键词匹配 + LLM 意图识别 + 降级策略

渐进式更新方案 A:
- 默认使用关键词匹配（零成本，~30% 请求快速匹配）
- 可选启用 LLM 意图识别（高准确率）
- 支持模型自适应（不同模型使用不同 Prompt 复杂度）
"""
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List


class IntentRouter:
    def __init__(self, skill_md_path: Optional[str] = None):
        """
        初始化意图路由器
        
        Args:
            skill_md_path: SKILL.md 文件路径（可选，用于自动提取触发词）
        """
        self.intent_map = self._load_intent_map()
        self.keyword_rules = self._load_keyword_rules()
        
        # 加载 SKILL.md 中的触发词（如果有）
        if skill_md_path:
            self.skill_triggers = self._parse_skill_triggers(skill_md_path)
        else:
            self.skill_triggers = {}
    
    def _load_intent_map(self) -> Dict[str, Dict[str, Any]]:
        """
        加载意图映射表
        
        返回格式:
        {
            "query-customers": {
                "keywords": ["客户", "客户列表", "查客户"],
                "script": "query-customers.py",
                "required_params": [],
                "optional_params": ["days", "tags", "chat_user_id"],
                "priority": 1  # 优先级：数字越小优先级越高
            },
            ...
        }
        """
        return {
            # === 高优先级：具体操作 ===
            "batch-assign-session": {
                "keywords": ["批量分配", "批量分配客户"],
                "script": "batch-assign-session.py",
                "required_params": ["chat_user_ids", "assign_sys_user_id"],
                "optional_params": ["action"],
                "priority": 1
            },
            "batch-talk-back": {
                "keywords": ["批量回聊", "回聊客户"],
                "script": "batch-talk-back.py",
                "required_params": ["chat_user_ids", "sys_user_id"],
                "optional_params": [],
                "priority": 1
            },
            "add-whatsapp-device": {
                "keywords": ["添加 WhatsApp", "新增 WhatsApp"],
                "script": "add-whatsapp-device.py",
                "required_params": ["name", "phone"],
                "optional_params": [],
                "priority": 1
            },
            "delete-whatsapp-device": {
                "keywords": ["删除 WhatsApp", "移除 WhatsApp"],
                "script": "delete-whatsapp-device.py",
                "required_params": ["app_id"],
                "optional_params": [],
                "priority": 1
            },
            "send-message": {
                "keywords": ["发消息", "发送消息", "通知客户"],
                "script": "send-message.py",
                "required_params": ["chat_user_id", "msg"],
                "optional_params": [],
                "priority": 1
            },
            "assign-session": {
                "keywords": ["分配", "分配客户", "分配给", "给小王", "给小李"],
                "script": "assign-session.py",
                "required_params": ["chat_user_id", "member_id"],
                "optional_params": [],
                "priority": 1
            },
            "end-session": {
                "keywords": ["结束会话", "关闭会话"],
                "script": "end-session.py",
                "required_params": ["chat_session_id"],
                "optional_params": [],
                "priority": 1
            },
            
            # === 中优先级：查询类 ===
            "get-customer-history": {
                "keywords": ["客户历史", "客户画像", "详细信息", "跟进记录", "聊天记录"],
                "script": "get-customer-history.py",
                "required_params": ["chat_user_id"],
                "optional_params": ["days"],
                "priority": 2
            },
            "query-all-messages": {
                "keywords": ["所有消息", "全部聊天", "历史消息", "昨天的聊天"],
                "script": "query-all-messages.py",
                "required_params": [],
                "optional_params": ["days", "date", "chat_user_id"],
                "priority": 2
            },
            "query-messages": {
                "keywords": ["聊天记录", "聊天", "消息记录"],
                "script": "query-messages.py",
                "required_params": [],
                "optional_params": ["chat_user_id", "days", "limit"],
                "priority": 2
            },
            "daily-sales-report": {
                "keywords": ["销售", "销售数据", "昨天卖得", "今天卖得", "销售额"],
                "script": "daily-sales-report.py",
                "required_params": [],
                "optional_params": ["days", "date"],
                "priority": 2
            },
            "check-customer-feedback": {
                "keywords": ["客户反馈", "反馈", "投诉"],
                "script": "check-customer-feedback.py",
                "required_params": [],
                "optional_params": ["days"],
                "priority": 2
            },
            "find-followup-customers": {
                "keywords": ["待跟进", "跟进提醒", "需要跟进"],
                "script": "find-followup-customers.py",
                "required_params": [],
                "optional_params": ["days"],
                "priority": 2
            },
            
            # === 低优先级：通用查询 ===
            "query-customers": {
                "keywords": ["客户", "客户列表", "查客户", "有哪些客户", "VIP 客户"],
                "script": "query-customers.py",
                "required_params": [],
                "optional_params": ["days", "tags", "chat_user_id"],
                "priority": 3
            },
            "customer-stats": {
                "keywords": ["客户统计", "有多少客户", "新增客户", "咨询量"],
                "script": "customer-stats.py",
                "required_params": [],
                "optional_params": ["days", "date"],
                "priority": 3
            },
            "query-whatsapp-apps": {
                "keywords": ["WhatsApp", "WhatsApp 设备", "WA 设备"],
                "script": "query-whatsapp-apps.py",
                "required_params": [],
                "optional_params": ["status"],
                "priority": 3
            },
            "member-session-stats": {
                "keywords": ["成员统计", "销售统计", "客服统计"],
                "script": "member-session-stats.py",
                "required_params": [],
                "optional_params": ["days", "member_id"],
                "priority": 3
            },
            "online-duration-report": {
                "keywords": ["在线时长", "工作时长"],
                "script": "online-duration-report.py",
                "required_params": [],
                "optional_params": ["days", "member_id"],
                "priority": 3
            },
            "query-sessions": {
                "keywords": ["会话列表", "查询会话"],
                "script": "query-sessions.py",
                "required_params": [],
                "optional_params": ["status", "member_id"],
                "priority": 3
            },
            "create-customer": {
                "keywords": ["创建客户", "添加客户", "新建客户"],
                "script": "create-customer.py",
                "required_params": ["nickname"],
                "optional_params": ["phone", "remark"],
                "priority": 3
            },
            "update-customer": {
                "keywords": ["更新客户", "修改客户", "编辑客户"],
                "script": "update-customer.py",
                "required_params": ["chat_user_id"],
                "optional_params": ["remark", "tags", "phone"],
                "priority": 3
            },
            "batch-tags": {
                "keywords": ["批量打标签", "批量标签"],
                "script": "batch-tags.py",
                "required_params": ["chat_user_ids", "tags"],
                "optional_params": [],
                "priority": 3
            },
            "import-orders": {
                "keywords": ["导入订单", "订单导入"],
                "script": "import-orders.py",
                "required_params": ["file"],
                "optional_params": [],
                "priority": 3
            },
            "query-link-records": {
                "keywords": ["链接记录", "短链记录"],
                "script": "query-link-records.py",
                "required_params": [],
                "optional_params": ["days", "link_id"],
                "priority": 3
            },
            "query-links": {
                "keywords": ["短链列表", "链接列表"],
                "script": "query-links.py",
                "required_params": [],
                "optional_params": ["status"],
                "priority": 3
            },
            "query-members": {
                "keywords": ["成员列表", "客服列表", "销售列表"],
                "script": "query-members.py",
                "required_params": [],
                "optional_params": ["status"],
                "priority": 3
            },
            "get-whatsapp-qrcode": {
                "keywords": ["WhatsApp 二维码", "WA 二维码", "扫码"],
                "script": "get-whatsapp-qrcode.py",
                "required_params": ["app_id"],
                "optional_params": [],
                "priority": 3
            },
            "set-whatsapp-proxy": {
                "keywords": ["WhatsApp 代理", "WA 代理", "设置代理"],
                "script": "set-whatsapp-proxy.py",
                "required_params": ["app_id", "proxy_host", "proxy_port"],
                "optional_params": [],
                "priority": 3
            },
            "daily-feedback-report": {
                "keywords": ["反馈报告", "每日反馈"],
                "script": "daily-feedback-report.py",
                "required_params": [],
                "optional_params": ["days", "date"],
                "priority": 3
            },
        }
    
    def _load_keyword_rules(self) -> Dict[str, List[str]]:
        """
        加载关键词规则（简化版，用于快速匹配）
        
        返回格式:
        {
            "query-customers": ["客户", "客户列表", "查客户"],
            "daily-sales-report": ["销售", "销售数据"],
            ...
        }
        """
        rules = {}
        for intent_name, intent_data in self.intent_map.items():
            rules[intent_name] = intent_data["keywords"]
        return rules
    
    def _parse_skill_triggers(self, skill_md_path: str) -> Dict[str, List[str]]:
        """
        解析 SKILL.md 中的触发词列表
        
        从 SKILL.md 的 frontmatter 中提取 triggers 字段
        """
        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取 frontmatter
            if not content.startswith('---'):
                return {}
            
            end_idx = content.find('---', 3)
            if end_idx == -1:
                return {}
            
            frontmatter = content[4:end_idx].strip()
            
            # 简单解析 YAML（只处理 triggers 字段）
            triggers = {}
            current_intent = None
            for line in frontmatter.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    keyword = line[2:].strip().strip('"\'')
                    if current_intent:
                        if current_intent not in triggers:
                            triggers[current_intent] = []
                        triggers[current_intent].append(keyword)
                elif ':' in line and not line.startswith('#'):
                    key = line.split(':')[0].strip()
                    if key == 'triggers':
                        current_intent = 'global'
            
            return triggers
        except Exception as e:
            print(f"⚠️ 解析 SKILL.md 触发词失败：{e}")
            return {}
    
    def keyword_match(self, message: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        关键词快速匹配（带优先级）
        
        Args:
            message: 用户消息
        
        Returns:
            (intent_name, params) 或 None
        """
        message_lower = message.lower()
        
        # 存储所有匹配结果
        matches = []
        
        # 遍历所有意图的关键词
        for intent_name, intent_data in self.intent_map.items():
            keywords = intent_data["keywords"]
            priority = intent_data.get("priority", 3)
            
            for keyword in keywords:
                if keyword.lower() in message_lower:
                    # 提取简单参数
                    params = self._extract_simple_params(message, intent_name)
                    matches.append((intent_name, params, priority, len(keyword)))
        
        if not matches:
            return None
        
        # 排序：优先级高的在前，关键词长的在前（更具体）
        matches.sort(key=lambda x: (x[2], -x[3]))
        
        # 返回最佳匹配
        best_match = matches[0]
        return best_match[0], best_match[1]
    
    def _extract_simple_params(self, message: str, intent_name: str) -> Dict[str, Any]:
        """
        简单参数提取（规则驱动）
        
        支持的参数模式:
        - 时间：昨天/今天/最近 N 天
        - ID: chat_user_id / customer_id
        - 标签：VIP / 重要客户
        """
        params = {}
        
        # 时间参数
        if '昨天' in message:
            params['days'] = 1
        elif '今天' in message:
            params['days'] = 0
        elif '最近' in message or '近' in message:
            match = re.search(r'最近 (\d+) 天|近 (\d+) 天', message)
            if match:
                params['days'] = int(match.group(1) or match.group(2))
        
        # 标签参数
        if 'VIP' in message:
            params['tags'] = 'VIP'
        elif '重要' in message:
            params['tags'] = '重要客户'
        
        # ID 参数（简单模式）
        id_match = re.search(r'(abc\w+|chat_\w+|customer_\w+)', message, re.IGNORECASE)
        if id_match and 'chat_user_id' in self.intent_map.get(intent_name, {}).get('optional_params', []):
            params['chat_user_id'] = id_match.group(1)
        
        return params
    
    def classify_intent(self, message: str, use_llm: bool = False, model_profile: str = "L2") -> Dict[str, Any]:
        """
        意图识别主入口
        
        Args:
            message: 用户消息
            use_llm: 是否使用 LLM 增强识别（默认 False，仅用关键词）
            model_profile: 模型画像 (L1/L2/L3)
        
        Returns:
            {
                "skill": "query-customers",
                "params": {"days": 7},
                "confidence": 0.95,
                "method": "keyword" | "llm",
                "fallback": False
            }
        """
        # Step 1: 关键词匹配（零成本，快速路径）
        keyword_result = self.keyword_match(message)
        if keyword_result:
            intent_name, params = keyword_result
            return {
                "skill": intent_name,
                "params": params,
                "confidence": 0.85,  # 关键词匹配置信度
                "method": "keyword",
                "fallback": False
            }
        
        # Step 2: LLM 意图识别（可选，高成本）
        if use_llm:
            llm_result = self._llm_classify(message, model_profile)
            if llm_result and llm_result.get("skill"):
                return llm_result
        
        # Step 3: 降级策略 - 无法识别
        return {
            "skill": None,
            "params": {},
            "confidence": 0.0,
            "method": "none",
            "fallback": True,
            "clarification_needed": True,
            "suggestion": self._get_clarification_suggestion(message)
        }
    
    def _llm_classify(self, message: str, model_profile: str = "L2") -> Optional[Dict[str, Any]]:
        """
        LLM 意图识别（模型自适应）
        
        L1 模型：完整 Prompt + 推理过程 + Few-shot 示例
        L2 模型：简化 Prompt + 少量示例
        L3 模型：最小 Prompt + 直接输出
        
        Args:
            message: 用户消息
            model_profile: 模型画像 (L1/L2/L3)
        
        Returns:
            意图识别结果或 None
        """
        # 构建 Prompt
        prompt = self._build_adaptive_prompt(message, model_profile)
        
        # 调用 LLM（这里需要根据实际环境调整）
        # 注意：这是一个示例实现，实际使用时需要集成到 OpenClaw 的 LLM 调用流程
        try:
            # 伪代码：实际使用时替换为真实的 LLM 调用
            # response = call_llm(prompt, model_profile)
            # return self._parse_llm_response(response)
            print(f"⚠️ LLM 调用未实现（model_profile={model_profile}）")
            return None
        except Exception as e:
            print(f"⚠️ LLM 意图识别失败：{e}")
            return None
    
    def _build_adaptive_prompt(self, message: str, model_profile: str) -> str:
        """
        构建自适应 Prompt
        
        L1: 完整 Prompt（包含推理过程、多个示例、详细说明）
        L2: 简化 Prompt（包含少量示例、关键说明）
        L3: 最小 Prompt（仅包含必要信息）
        """
        # 意图列表
        intent_list = "\n".join([
            f"  - {intent_name}: {data['keywords'][:3]}"
            for intent_name, data in list(self.intent_map.items())[:10]
        ])
        
        if model_profile == "L1":
            # L1 模型：完整 Prompt
            return f"""你是一个 SaleSmartly API 技能路由助手。

## 可用技能
{intent_list}
... (更多技能)

## 任务
分析用户消息，识别应该调用哪个技能。

## 输出格式
{{
    "skill": "技能名称",
    "params": {{"参数名": "参数值"}},
    "confidence": 0.0-1.0,
    "reasoning": "推理过程"
}}

## 示例
用户：查一下昨天的销售数据
输出：{{"skill": "daily-sales-report", "params": {{"days": 1}}, "confidence": 0.95, "reasoning": "用户询问销售数据，时间范围是昨天"}}

用户：有哪些 VIP 客户
输出：{{"skill": "query-customers", "params": {{"tags": "VIP"}}, "confidence": 0.9, "reasoning": "用户查询客户列表，带有 VIP 标签筛选"}}

## 用户消息
{message}

请分析并输出 JSON："""

        elif model_profile == "L2":
            # L2 模型：简化 Prompt
            return f"""你是 SaleSmartly 技能路由助手。

可用技能：{intent_list}

用户消息：{message}

输出 JSON 格式：{{"skill": "技能名", "params": {{}}, "confidence": 0.0-1.0}}

示例：
- "查昨天销售" → {{"skill": "daily-sales-report", "params": {{"days": 1}}, "confidence": 0.95}}
- "有哪些 VIP 客户" → {{"skill": "query-customers", "params": {{"tags": "VIP"}}, "confidence": 0.9}}

请输出 JSON："""

        else:
            # L3 模型：最小 Prompt
            return f"""技能路由：{message}

输出：{{"skill": "...", "params": {{}}, "confidence": 0.0-1.0}}"""
    
    def _get_clarification_suggestion(self, message: str) -> str:
        """
        生成澄清建议（当无法识别意图时）
        """
        # 检测消息中是否包含某些关键词
        if any(kw in message.lower() for kw in ["客户", "销售", "消息", "WhatsApp"]):
            return "我检测到您可能想查询 SaleSmartly 相关数据，但需要更多信息。请问您具体想：\n1. 查询客户列表？\n2. 查看销售数据？\n3. 发送消息？\n4. 其他操作？"
        
        return "抱歉，我没有理解您的意图。请问您想使用哪个 SaleSmartly 功能？（例如：查客户、看销售、发消息等）"


# ==================== 命令行测试接口 ====================

if __name__ == "__main__":
    import sys
    
    router = IntentRouter()
    
    if len(sys.argv) > 1:
        # 命令行测试模式
        test_message = " ".join(sys.argv[1:])
        print(f"测试消息：{test_message}\n")
        
        # 关键词匹配
        result = router.classify_intent(test_message, use_llm=False)
        print(f"关键词匹配结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 交互模式
        print("意图识别测试（输入 q 退出）\n")
        while True:
            message = input("用户消息：").strip()
            if message.lower() in ['q', 'quit', 'exit']:
                break
            
            result = router.classify_intent(message, use_llm=False)
            print(f"识别结果：{json.dumps(result, ensure_ascii=False, indent=2)}\n")
