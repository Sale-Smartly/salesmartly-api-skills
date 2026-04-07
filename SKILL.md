---
name: salesmartly-api-skills
description: SaleSmartly 全功能 API 技能。29 个核心脚本，覆盖客户/会话/营销/WhatsApp 管理。
triggers:
  # === 高置信度触发词（小模型友好）===
  - "客户"
  - "销售"
  - "发消息"
  - "聊天记录"
  - "WhatsApp"
  - "分配"
  - "跟进"
  - "反馈"
  # === 中等置信度触发词 ===
  - "查客户"
  - "查销售"
  - "销售数据"
  - "客户列表"
  - "分配会话"
  - "客户跟进"
  - "待跟进"
  - "客户反馈"
  # === 具体场景触发词 ===
  - "昨天卖得怎么样"
  - "今天有多少咨询"
  - "VIP 客户有哪些"
  - "给张三发消息"
  - "把这个客户给小王"
  - "结束这个会话"
  - "查聊天记录"
  - "WhatsApp 设备"
  - "批量分配"
  - "批量回聊"
  - "在线时长"
  - "成员统计"
---

# SaleSmartly API Skills

> 29 个核心脚本 | 100% API 覆盖 | 所有脚本支持 `--json` 结构化输出

---

## 红线规则

**禁止直接使用 curl/Python/HTTP 客户端调用 SaleSmartly API，必须使用 `scripts/` 中的脚本。**

```bash
# ✅ 正确
uv run scripts/query-customers.py --days 7

# ❌ 禁止
curl -X GET "https://developer.salesmartly.com/api/v2/..."
```

脚本自动处理签名计算、SSL 验证、分页、时间格式转换、错误提示。详见 [NO-DIRECT-API.md](NO-DIRECT-API.md)。

---

## Few-shot 示例

### 示例 1：查询销售数据

**用户**: "查一下昨天的销售数据"

**调用**:
```bash
uv run scripts/daily-sales-report.py --days 1
```

### 示例 2：查询 VIP 客户

**用户**: "有哪些 VIP 客户"

**调用**:
```bash
uv run scripts/query-customers.py --tags "VIP"
```

### 示例 3：模糊意图澄清

**用户**: "我想看看数据"

**澄清话术**:
```
请问具体是：
1. 销售数据（每日销售额）
2. 客户数据（新增客户、客户列表）
3. 会话数据（客服接待量）
4. 其他数据（请具体说明）
```

### 示例 4：批量操作

**用户**: "批量分配这些客户给小李"

**调用**:
```bash
uv run scripts/batch-assign-session.py \
  --chat-user-ids abc123,def456 \
  --assign-sys-user-id 456 \
  --sys-user-id 789 \
  --action start
```

### 示例 5：WhatsApp 设备管理

**用户**: "添加一个 WhatsApp 设备"

**调用**:
```bash
uv run scripts/add-whatsapp-device.py --country us
```

---

## 用户意图映射

| 用户说法 | 调用脚本 | 关键参数 |
|---------|---------|---------|
| "查一下昨天的销售" | `daily-sales-report.py` | `--days 1` |
| "今天有多少咨询" | `customer-stats.py` | `--days 1` |
| "有哪些客户" | `query-customers.py` | `--days 7` |
| "VIP 客户有哪些" | `query-customers.py` | `--tags "VIP"` |
| "查客户 abc123" | `query-customers.py` | `--chat-user-id abc123` |
| "看看聊天记录" | `query-messages.py` | `--chat-user-id <ID>` |
| "查昨天的聊天" | `query-all-messages.py` | `--yesterday` |
| "把这个客户给小王" | `assign-session.py` | `--chat-user-id`, `--assign-sys-user-id` |
| "批量分配客户" | `batch-assign-session.py` | `--chat-user-ids`, `--action start` |
| "批量回聊客户" | `batch-talk-back.py` | `--chat-user-ids`, `--sys-user-id` |
| "结束这个会话" | `end-session.py` | `--session-id`, `--chat-user-id` |
| "查客户详细信息" | `get-customer-history.py` | `--chat-user-id` |
| "WhatsApp 设备" | `query-whatsapp-apps.py` | `--status 1` |
| "客户反馈" | `check-customer-feedback.py` | `--days 7` |
| "待跟进客户" | `find-followup-customers.py` | `--days 7` |
| "在线时长" | `online-duration-report.py` | `--today` |
| "成员会话统计" | `member-session-stats.py` | `--today` |

---

## ID 字段说明

| 对象 | 正确字段 | 错误字段 | 说明 |
|------|---------|---------|------|
| **客服 ID** | `sys_user_id` | `id` | `id` 是成员关系 ID，不要用于业务场景 |
| **客户 ID** | `chat_user_id` | - | 只有一个，不会混淆 |
| **会话 ID** | `session_id` | `chat_session_id` | 优先使用 `session_id` |
| **消息发送人** | `sender` (看 sender_type) | - | sender_type=2 时是客服 sys_user_id |

**口诀**：客服 ID = `sys_user_id`，客服发消息时 `sender` = `sys_user_id`

---

## 错误处理指南

| 错误类型 | AI 回复模板 |
|---------|-----------|
| 配置缺失 | "请先配置 `api-key.json` 文件，填入您的 SaleSmartly API Key 和 Project ID" |
| API 错误 | "连接 SaleSmartly 失败：{错误信息}，请检查 API Key 是否正确" |
| 无数据 | "没有找到符合条件的数据，您可以尝试放宽筛选条件" |
| 参数模糊 | "我没理解{参数}，您是想查昨天、今天还是最近 7 天？" |
| 需要确认 | "您想给{数量}个客户发送消息，确认要发送吗？" |

---

## 核心能力

1. **客户管理** - 查询、创建、更新客户，批量操作标签，导入订单
2. **团队管理** - 获取团队成员信息，会话统计，在线时长
3. **会话管理** - 查询聊天记录、会话分配、批量回聊、结束会话
4. **营销管理** - 分流链接管理与数据统计
5. **集成管理** - WhatsApp 设备全生命周期管理
6. **数据分析** - 销售报告、客户反馈分析、跟进提醒、钉钉推送

## 配置方式

在 `api-key.json` 中配置（也支持环境变量 `SALESMARTLY_API_KEY` / `SALESMARTLY_PROJECT_ID`）：

```json
{
  "apiKey": "your_api_key",
  "projectId": "your_project_id",
  "dingtalk": {
    "webhook": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
  }
}
```

---

## 可用命令

### 客户管理

```bash
uv run scripts/query-customers.py --days 7 --page-size 20
uv run scripts/query-customers.py --chat-user-id <ID>
uv run scripts/create-customer.py --phone 8613800138000 --remark-name "客户名"
uv run scripts/update-customer.py --chat-user-id <ID> --remark "备注"
uv run scripts/batch-tags.py --ids <ID1>,<ID2> --update-label-names "VIP" --update-type append
uv run scripts/import-orders.py --chat-user-id <ID> --order-id <ORDER_ID>
uv run scripts/get-customer-history.py --chat-user-id <ID>
uv run scripts/find-followup-customers.py --days 7
uv run scripts/customer-stats.py --days 30
```

### 团队管理

```bash
uv run scripts/query-members.py --status active
uv run scripts/member-session-stats.py --today
uv run scripts/online-duration-report.py --today
```

### 会话管理

```bash
uv run scripts/query-sessions.py --days 7 --page-size 10
uv run scripts/query-messages.py --chat-user-id <ID> --days 7
uv run scripts/query-all-messages.py --yesterday
uv run scripts/assign-session.py --session-id <SID> --chat-user-id <ID> --assign-sys-user-id <客服ID>
uv run scripts/batch-assign-session.py --chat-user-ids <ID1>,<ID2> --assign-sys-user-id <客服ID> --sys-user-id <操作者ID> --action start
uv run scripts/batch-talk-back.py --chat-user-ids <ID1>,<ID2> --sys-user-id <客服ID>
uv run scripts/end-session.py --session-id <SID> --chat-user-id <ID>
```

### 营销管理

```bash
uv run scripts/query-links.py --days 30
uv run scripts/query-link-records.py --page-size 50
```

### WhatsApp 管理

```bash
uv run scripts/query-whatsapp-apps.py --status 1
uv run scripts/add-whatsapp-device.py --country us
uv run scripts/get-whatsapp-qrcode.py --id <设备ID>
uv run scripts/set-whatsapp-proxy.py --id <设备ID> --is-proxy 1 --host <主机> --port <端口>
uv run scripts/delete-whatsapp-device.py --id <设备ID>
```

### 数据分析

```bash
uv run scripts/daily-sales-report.py --days 1
uv run scripts/daily-feedback-report.py
uv run scripts/check-customer-feedback.py --days 7
```

---

## 通用参数

所有脚本支持以下参数：

| 参数 | 说明 |
|------|------|
| `--json` | 输出结构化 JSON（Agent 解析用） |
| `--quiet` | 安静模式，最少输出 |
| `--config <path>` | 指定配置文件路径 |

JSON 输出格式：
```json
{"success": true, "data": {...}, "meta": {"total": 100, "page": 1}}
{"success": false, "error": {"code": 10001, "message": "..."}}
```

---

## 分页处理

**大数据量查询必须使用 `--all` 参数自动翻页：**

```bash
uv run scripts/query-customers.py --days 7 --all
```

| 场景 | 是否需要翻页 |
|------|-------------|
| 今天的新增客户 (< 50) | 通常不需要 |
| 最近 7 天的客户 (100-500) | **需要** |
| 所有客户 (500-2000+) | **必须** |
| 聊天记录 (数千条) | **必须** |

---

## 其他注意事项

1. **API 域名**: `https://developer.salesmartly.com`
2. **时间戳**: 13 位毫秒自动转换为秒
3. **分页限制**: page_size 最大 100
4. **SSL 验证**: 默认启用完整 SSL 验证

## 相关文档

- [GitHub 仓库](https://github.com/Sale-Smartly/salesmartly-api-skills)
- [API 文档](https://salesmartly-api.apifox.cn/llms.txt)
- [签名规则](https://help.salesmartly.com/docs/API-Header)
- [禁止直接调用 API](NO-DIRECT-API.md)

---

## 场景示例

查看 `examples/` 目录中的场景化示例：

| 示例 | 场景 | 文件 |
|------|------|------|
| 01 | 查询销售数据 | `examples/01-查询销售数据.md` |
| 02 | 查询客户 | `examples/02-查询客户.md` |
| 03 | 发送消息 | `examples/03-发送消息.md` |

---

## 最佳实践

### 1. 先确认，再执行
涉及修改/发送的操作，先向用户确认：
```
AI: 您想给 156 个客户发送消息，确认吗？
```

### 2. 主动提供下一步
查询后主动询问：
```
AI: 找到 23 个 VIP 客户。需要我：
   1. 导出联系方式
   2. 发送活动通知
   3. 查看详细信息
```

### 3. 模糊时多问一句
```
AI: 您想查哪个时间范围的销售？昨天 / 今天 / 最近 7 天 / 指定日期
```

### 4. 使用 --json 获取结构化数据
当需要对结果做进一步处理时，使用 `--json` 参数获取机器可读输出。
