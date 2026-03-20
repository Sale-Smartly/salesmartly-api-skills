---
name: salesmartly-api-skills
description: SaleSmartly 全功能 API 技能。26 个核心脚本，覆盖客户/会话/营销/WhatsApp 管理。
triggers:
  - "查客户"
  - "查销售"
  - "发消息"
  - "销售数据"
  - "客户列表"
  - "聊天记录"
  - "WhatsApp"
  - "分配会话"
  - "客户跟进"
---

# SaleSmartly API Skills

> 📦 SaleSmartly 全功能 API 自动化脚本系统 | 26 个核心脚本 | 100% API 覆盖

---

## 🚨 红线规则（AI 必须遵守！）

### ⛔ 禁止直接调用 API

**无论任何情况，都不得直接使用 curl/Python/HTTP 客户端调用 SaleSmartly API！**

**❌ 错误做法**：
```bash
# 禁止这样做！
curl -X GET "https://developer.salesmartly.com/api/v2/get-contact-list?..."
```

```python
# 禁止这样做！
requests.get("https://developer.salesmartly.com/api/v2/get-contact-list", ...)
```

**✅ 正确做法**：
```bash
# 必须使用脚本！
uv run scripts/query-customers.py --days 7
```

### 为什么必须使用脚本？

| 问题 | 直接调用 API | 使用脚本 |
|------|-------------|---------|
| **签名计算** | 容易出错（排序、编码） | 自动处理 |
| **SSL 验证** | 可能跳过验证，不安全 | 统一配置 |
| **分页处理** | 容易只获取第一页 | `--all` 自动获取 |
| **时间格式** | 毫秒/秒容易混淆 | 自动转换 |
| **错误处理** | 需要自己解析 | 统一错误提示 |
| **配置管理** | 硬编码 API Key | 配置文件加载 |
| **数据格式化** | 原始 JSON 难读 | 表格/摘要输出 |

### 脚本已覆盖所有 API

**26 个脚本 = 100% API 覆盖率**，没有任何理由绕过脚本！

如果脚本缺少某个功能：
1. 检查是否有其他脚本已实现
2. 如果没有，先添加功能到脚本
3. **永远不要**临时用 curl/Python 直接调用

---

## 🗣️ 用户意图映射（AI 必读！）

**当用户说以下话时，按对应方式处理：**

| 用户说法 | 意图 | 调用脚本 | 关键参数 |
|---------|------|---------|---------|
| "查一下昨天的销售" | 销售数据 | `daily-sales-report.py` | `--yesterday` |
| "昨天卖得怎么样" | 销售数据 | `daily-sales-report.py` | `--yesterday` |
| "今天有多少咨询" | 客户统计 | `customer-stats.py` | `--today` |
| "有哪些客户" | 查询客户 | `query-customers.py` | `--days 7` |
| "VIP 客户有哪些" | 查询客户 | `query-customers.py` | `--tags "VIP"` |
| "最近 7 天新增客户" | 查询客户 | `query-customers.py` | `--days 7` |
| "查客户 abc123 的信息" | 查询单个客户 | `query-customers.py` | `--chat-user-id abc123` |
| "给张三发消息" | 发送消息 | `send-message.py` | `--chat-user-id`, `--msg` |
| "通知所有 VIP 客户" | 批量发送 | 先 `query-customers.py` 再 `batch-send-message.py` | 需用户确认 |
| "看看聊天记录" | 查询消息 | `query-messages.py` | `--chat-user-id` |
| "查昨天的聊天" | 查询消息 | `query-all-messages.py` | `--yesterday` |
| "把这个客户给小王" | 分配会话 | `assign-session.py` | `--chat-user-id`, `--member-id` |
| "批量分配客户" | 批量分配 | `batch-assign-session.py` | `--chat-user-ids`, `--assign-sys-user-id`, `--action start` |
| "释放这些客户" | 结束分配 | `batch-assign-session.py` | `--chat-user-ids`, `--task-id`, `--action end` |
| "批量回聊客户" | 批量回聊 | `batch-talk-back.py` | `--chat-user-ids`, `--sys-user-id` |
| "结束这个会话" | 结束会话 | `end-session.py` | `--chat-session-id` |
| "查客户详细信息" | 客户画像 | `get-customer-history.py` | `--chat-user-id` |
| "查张三的聊天记录" | 客户历史 | `get-customer-history.py` | `--chat-user-id`, `--days 30` |
| "WhatsApp 设备" | 查询设备 | `query-whatsapp-apps.py` | `--status 1` |
| "添加 WhatsApp" | 新增设备 | `add-whatsapp-device.py` | `--name`, `--phone` |
| "客户反馈" | 检查反馈 | `check-customer-feedback.py` | `--days 7` |
| "待跟进客户" | 跟进提醒 | `find-followup-customers.py` | `--days 7` |

---

## ⚠️ 重要：ID 字段说明（AI 必读！）

**本文档记录所有容易混淆的 API 字段，使用前必须阅读！**

📄 **详细文档**: `ID-FIELDS-GUIDE.md`

### 快速参考

| 对象 | 正确字段 | 错误字段 | 说明 |
|------|---------|---------|------|
| **客服 ID** | `sys_user_id` | `id` | `id` 是成员关系 ID，不要用于业务场景 |
| **客户 ID** | `chat_user_id` | - | 只有一个，不会混淆 |
| **会话 ID** | `session_id` | `chat_session_id` | 优先使用 `session_id` |
| **消息发送人** | `sender` (看 sender_type) | - | sender_type=2 时是客服 sys_user_id |

**记忆口诀**：
- 客服 ID = `sys_user_id`
- 客服发消息时，`sender` = `sys_user_id`

---

## 🎯 AI 处理流程

### 步骤 1：识别意图
从用户自然语言中提取：
- **动作**：查、发、分配、结束、添加...
- **对象**：客户、销售、消息、会话、设备...
- **条件**：时间（昨天/7 天）、标签（VIP）、关键词...

### 步骤 2：选择脚本
根据意图匹配上表中的脚本

### 步骤 3：构建命令
提取参数，构建完整的命令行

### 步骤 4：执行并格式化
调用脚本，将结果转化为用户友好的格式

### 步骤 5：主动询问
根据结果，提供下一步建议

---

## ⚠️ 错误处理指南

| 错误类型 | AI 回复模板 |
|---------|-----------|
| 配置缺失 | "请先配置 `api-key.json` 文件，填入您的 SaleSmartly API Key 和 Project ID" |
| API 错误 | "连接 SaleSmartly 失败：{错误信息}，请检查 API Key 是否正确" |
| 无数据 | "没有找到符合条件的数据，您可以尝试放宽筛选条件" |
| 参数模糊 | "我没理解{参数}，您是想查昨天、今天还是最近 7 天？" |
| 需要确认 | "您想给{数量}个客户发送消息，确认要发送吗？（回复'确认'继续）" |

---

## 核心能力

1. **客户管理** - 查询、创建、更新客户，批量操作标签，导入订单
2. **团队管理** - 获取团队成员信息
3. **会话管理** - 查询聊天记录、会话分配、结束会话
4. **营销管理** - 分流链接管理与数据统计
5. **集成管理** - WhatsApp 设备全生命周期管理
6. **钉钉推送** - 客户反馈报告、待跟进提醒自动推送到钉钉

## 配置方式

### 配置文件（推荐）

在 `api-key.json` 中配置：

```json
{
  "apiKey": "your_api_key",
  "projectId": "your_project_id"
}
```

### 可选：钉钉推送配置

```json
{
  "apiKey": "your_api_key",
  "projectId": "your_project_id",
  "dingtalk": {
    "webhook": "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
  }
}
```

## 可用命令

### 客户管理

```bash
# 查询客户
uv run scripts/query-customers.py --days 7 --page-size 20

# 新增客户
uv run scripts/create-customer.py --phone 8613800138000 --remark-name "客户名"

# 更新客户
uv run scripts/update-customer.py --chat-user-id <ID> --remark "备注"

# 批量标签
uv run scripts/batch-tags.py --chat-user-ids <ID1>,<ID2> --tag-ids <TAG_ID>

# 导入订单
uv run scripts/import-orders.py --orders <订单 JSON>
```

### 团队管理

```bash
uv run scripts/query-members.py --status active
```

**⚠️ 重要：客服 ID 字段说明（AI 必读！）**

获取成员列表接口返回两个 ID 字段，**极易混淆**：

| 字段名 | 含义 | 用途 | 是否使用 |
|--------|------|------|---------|
| `id` | 成员关系 ID | 仅用于团队成员关系管理（如更新成员信息） | ❌ **不要用于会话分配** |
| `sys_user_id` | 系统用户 ID | **真正的客服 ID**，用于会话分配、查询等所有业务场景 | ✅ **始终使用这个** |

**正确示例**：
```bash
# ✅ 正确：使用 sys_user_id 分配会话
uv run scripts/assign-session.py --chat-user-id 12345 --member-id 180747

# ❌ 错误：不要使用 id 字段
uv run scripts/assign-session.py --chat-user-id 12345 --member-id 185570
```

**记忆口诀**：`sys_user_id` = 系统用户 ID = 真正的客服 ID

### 会话管理

```bash
# 查询会话列表（活跃会话）
uv run scripts/query-sessions.py --page 1 --page-size 10

# 查询已结束会话
uv run scripts/query-sessions.py --session-status ended --page-size 10

# 按客服 ID 筛选
uv run scripts/query-sessions.py --sys-user-id 1366 --page-size 10

# 按时间范围筛选（最近 7 天）
uv run scripts/query-sessions.py --days 7 --page-size 10

# 组合筛选 - 已结束会话 + 时间范围
uv run scripts/query-sessions.py --session-status ended --days 30 --page-size 10

# 测试环境
uv run scripts/query-sessions.py --config api-key-dev.json --page 1 --page-size 10

# 查询聊天记录
uv run scripts/query-messages.py --chat-user-id <用户 ID> --days 7

# 全量记录
uv run scripts/query-all-messages.py --page-size 50

# 分配会话（单个）
uv run scripts/assign-session.py --chat-user-id <ID> --member-id <成员 ID>

# 批量分配会话（多个客户）
uv run scripts/batch-assign-session.py --chat-user-ids <ID1>,<ID2> --assign-sys-user-id <客服 ID> --sys-user-id <操作者 ID> --action start

# 批量分配会话（仅无进行中会话的客户）
uv run scripts/batch-assign-session.py --chat-user-ids <ID1>,<ID2> --assign-sys-user-id <客服 ID> --sys-user-id <操作者 ID> --action start --assign-type 0

# 结束分配（释放客户）
uv run scripts/batch-assign-session.py --chat-user-ids <ID1>,<ID2> --assign-sys-user-id <客服 ID> --sys-user-id <操作者 ID> --action end --task-id <任务 ID>

# 批量回聊（异步处理）
uv run scripts/batch-talk-back.py --chat-user-ids <ID1>,<ID2> --sys-user-id <客服 ID>

# 结束会话
uv run scripts/end-session.py --chat-session-id <会话 ID>
```

**⚠️ 重要：聊天记录发送人 ID 说明（AI 必读！）**

消息记录中的 `sender` 字段含义取决于 `sender_type`：

| sender_type | 含义 | sender 字段值 |
|-------------|------|--------------|
| 1 | 用户发送 | 客户的 `chat_user_id` |
| 2 | 团队成员发送 | **客服的 `sys_user_id`** ← 真正的客服 ID |
| 3 | 系统消息 | 系统标识 |

**正确示例**：
```python
# 当 sender_type = 2 时
sender = 180747  # 这是客服的 sys_user_id，不是成员 id！
```

**记忆口诀**：客服发消息时，`sender` = `sys_user_id`

# 分配会话
uv run scripts/assign-session.py --chat-user-id <ID> --member-id <成员 ID>

# 结束会话
uv run scripts/end-session.py --chat-session-id <会话 ID>
```

### 营销管理

```bash
# 分流链接
uv run scripts/query-links.py --days 30

# 链接记录
uv run scripts/query-link-records.py --link-id <链接 ID>
```

### WhatsApp 管理

```bash
# 查询设备
uv run scripts/query-whatsapp-apps.py --status 1

# 新增设备
uv run scripts/add-whatsapp-device.py --name "设备名" --phone 8613800138000

# 获取二维码
uv run scripts/get-whatsapp-qrcode.py --id <设备 ID>

# 设置代理
uv run scripts/set-whatsapp-proxy.py --id <设备 ID> --proxy-host <主机> --proxy-port <端口>

# 删除设备
uv run scripts/delete-whatsapp-device.py --id <设备 ID>
```

### 数据分析

```bash
# 每日销售报告
uv run scripts/daily-sales-report.py --date 2026-03-17

# 客户统计
uv run scripts/customer-stats.py --days 7
```

## 🔄 更新技能（AI 指令）

> **当用户说"更新 salesmartly-api-skills"或"更新 salesmartly skill"时，执行以下操作：**

```bash
# 1. 确认技能目录
cd skills/salesmartly-api-skills

# 2. 检查是否是 git 仓库
git status

# 3. 拉取最新代码
git pull origin main

# 4. 告知用户结果
echo "✅ salesmartly-api-skills 已更新到最新版本"
```

**GitHub 仓库**: https://github.com/Sale-Smartly/salesmartly-api-skills

---

## 📝 手动更新（用户自行操作）

```bash
cd skills/salesmartly-api-skills
git pull origin main
```

## API 签名规则

```python
import hashlib

# 1. Token 放最前面
# 2. 参数按字母排序
# 3. 用 & 连接
# 4. MD5 加密（32 位小写）

sorted_params = sorted(params.items(), key=lambda x: x[0])
sign_parts = [api_key]
for k, v in sorted_params:
    sign_parts.append(f"{k}={v}")
sign = hashlib.md5("&".join(sign_parts).encode()).hexdigest()
```

## ⚠️ 重要：分页处理规则（AI 必读！）

**大模型常见错误：只获取第一页数据就输出结果！**

### 分页处理流程

**当调用任何返回列表的 API 时，必须按以下步骤处理：**

```
步骤 1：调用 API 获取第一页
  → 检查响应中的 `total` 和 `page_size` 字段

步骤 2：判断是否需要翻页
  → 如果 total > page_size：需要翻页
  → 如果 total <= page_size：只有一页，直接输出

步骤 3：如果需要翻页
  → 计算总页数：total_pages = ceil(total / page_size)
  → 循环调用 API 获取所有页面（page=2, 3, ...）
  → 合并所有页面的数据

步骤 4：输出完整结果
  → 告知用户总数据量
  → 输出完整列表或摘要
```

### 示例：查询客户列表

**❌ 错误做法（只获取第一页）**：
```python
# 只调用一次，忽略 total 字段
result = query_customers(page=1, page_size=20)
# 实际有 986 个客户，但只返回 20 个
print(f"共有 {len(result['list'])} 个客户")  # 错误！
```

**✅ 正确做法（处理分页）**：
```python
# 第一次调用
result = query_customers(page=1, page_size=100)
total = result['data']['total']  # 986
page_size = result['data']['page_size']  # 100

# 判断是否需要翻页
if total > page_size:
    # 需要翻页：获取所有页面
    all_customers = result['data']['list']
    total_pages = (total + page_size - 1) // page_size
    
    for page in range(2, total_pages + 1):
        result = query_customers(page=page, page_size=100)
        all_customers.extend(result['data']['list'])
    
    print(f"共有 {total} 个客户")  # 正确！
else:
    # 只有一页
    print(f"共有 {total} 个客户")
```

### 何时需要特别关注分页？

| 场景 | 数据量预估 | 是否需要翻页 |
|------|-----------|-------------|
| 今天的新增客户 | 通常 < 50 | ❌ 可能不需要 |
| 最近 7 天的客户 | 通常 100-500 | ✅ **需要** |
| 所有客户列表 | 通常 500-2000+ | ✅ **必须** |
| 聊天记录查询 | 可能数千条 | ✅ **必须** |
| 客服团队成员 | 通常 < 50 | ❌ 可能不需要 |

### 脚本参数建议

**对于需要处理大量数据的查询，使用以下参数：**

```bash
# ✅ 推荐：使用较大的 page_size 减少请求次数
uv run scripts/query-customers.py --days 7 --page-size 100

# ✅ 推荐：添加 --all 参数自动获取所有数据
uv run scripts/query-customers.py --days 7 --all

# ✅ 推荐：使用 --summary 先查看统计
uv run scripts/query-customers.py --days 7 --summary
```

### AI 回复模板

**当数据量较大时，主动告知用户：**

```
✅ 共找到 {total} 条记录（{pages} 页）

由于数据量较大，我为您获取了完整列表：
- 显示前 20 条摘要
- 完整数据已保存到文件：xxx.json

需要我详细展示某部分数据吗？
```

---

## 其他注意事项

1. **API 域名**: `https://developer.salesmartly.com`
2. **时间戳**: 13 位毫秒自动转换为秒
3. **分页限制**: page_size 最大 100
4. **SSL 验证**: 默认启用完整 SSL 验证（CERT_REQUIRED + 主机名验证）

## 相关文档

- [GitHub 仓库](https://github.com/Sale-Smartly/salesmartly-api-skills)
- [API 文档](https://salesmartly-api.apifox.cn/llms.txt)
- [签名规则](https://help.salesmartly.com/docs/API-Header)
- [🚫 禁止直接调用 API](NO-DIRECT-API.md) ← **必读！**

---

## 📚 场景示例（新手必读）

查看 `examples/` 目录中的场景化示例：

| 示例 | 场景 | 文件 |
|------|------|------|
| 01 | 查询销售数据 | `examples/01-查询销售数据.md` |
| 02 | 查询客户 | `examples/02-查询客户.md` |
| 03 | 发送消息 | `examples/03-发送消息.md` |

**每个示例包含：**
- 用户可能会怎么说（自然语言）
- AI 思考过程（意图识别）
- 调用命令（具体脚本）
- 预期输出格式
- 错误处理指南

---

## 💡 最佳实践

### 1. 先确认，再执行
涉及修改/发送的操作，先向用户确认：
```
AI: 您想给 156 个客户发送消息，确认吗？
用户：确认
AI: 好的，正在发送...
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
参数不明确时：
```
AI: 您想查哪个时间范围的销售？
   - 昨天
   - 今天
   - 最近 7 天
   - 指定日期
```

### 4. 错误要解释原因
不要只说"失败了"，要说：
```
AI: 查询失败，原因是 API Key 配置错误。
   请在 `api-key.json` 中填入正确的 API Key 和 Project ID。
```
