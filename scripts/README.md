# SaleSmartly API Scripts - 脚本列表

> 📦 20 个 Python 脚本，100% 覆盖 SaleSmartly API 核心功能

---

## 📋 快速索引

### 🔴 高频使用（每日必用）

| 脚本 | 功能 | 常用参数 | 示例 |
|------|------|---------|------|
| [daily-sales-report.py](#daily-sales-reportpy) | 销售日报 | `--today`, `--days` | `--today` |
| [query-customers.py](#query-customerspy) | 客户查询 | `--days`, `--tags` | `--days 7` |
| [query-all-messages.py](#query-all-messagespy) | 聊天记录 | `--today`, `--session` | `--today` |
| [find-followup-customers.py](#find-followup-customerspy) | 待跟进客户 | `--days`, `--limit` | `--days 3` |

### 🟡 中频使用（每周几次）

| 脚本 | 功能 | 常用参数 | 示例 |
|------|------|---------|------|
| [customer-stats.py](#customer-statspy) | 客户统计 | `--days`, `--source` | `--days 30` |
| [query-members.py](#query-memberspy) | 团队成员 | 无 | - |
| [query-sessions.py](#query-sessionspy) | 会话列表 | `--status`, `--member` | `--status 1` |
| [member-session-stats.py](#member-session-statspy) | 客服会话统计 | `--days`, `--status` | `--days 7` |
| [assign-session.py](#assign-sessionpy) | 分配会话 | `--session`, `--member` | `--session 123 --member 456` |

### 🟢 低频使用（按需调用）

| 脚本 | 功能 | 常用参数 | 示例 |
|------|------|---------|------|
| [create-customer.py](#create-customerpy) | 创建客户 | `--name`, `--phone` | `--name 张三 --phone 13800138000` |
| [update-customer.py](#update-customerpy) | 更新客户 | `--id`, `--tags` | `--id 123 --tags VIP` |
| [batch-tags.py](#batch-tagspy) | 批量打标签 | `--customer-ids`, `--tags` | `--customer-ids 1,2,3 --tags VIP` |
| [import-orders.py](#import-orderspy) | 导入订单 | `--file` | `--file orders.csv` |

### 🔵 WhatsApp 管理

| 脚本 | 功能 | 常用参数 | 示例 |
|------|------|---------|------|
| [query-whatsapp-apps.py](#query-whatsapp-appspy) | 设备列表 | 无 | - |
| [add-whatsapp-device.py](#add-whatsapp-devicepy) | 添加设备 | `--name` | `--name 客服 1` |
| [delete-whatsapp-device.py](#delete-whatsapp-devicepy) | 删除设备 | `--app-id` | `--app-id 123` |
| [get-whatsapp-qrcode.py](#get-whatsapp-qrcodepy) | 获取二维码 | `--app-id` | `--app-id 123` |
| [set-whatsapp-proxy.py](#set-whatsapp-proxypy) | 设置代理 | `--app-id`, `--proxy` | `--app-id 123 --proxy http://proxy.com` |

### 🟣 反馈与报告

| 脚本 | 功能 | 常用参数 | 示例 |
|------|------|---------|------|
| [daily-feedback-report.py](#daily-feedback-reportpy) | 每日反馈报告 | `--days` | `--days 1` |
| [check-customer-feedback.py](#check-customer-feedbackpy) | 客户反馈检查 | `--days`, `--sensitive` | `--days 7` |

### 🟤 其他工具

| 脚本 | 功能 | 常用参数 | 示例 |
|------|------|---------|------|
| [query-messages.py](#query-messagespy) | 消息查询 | `--session`, `--limit` | `--session 123` |
| [get-customer-history.py](#get-customer-historypy) | 客户历史 | `--customer-id` | `--customer-id 123` |
| [end-session.py](#end-sessionpy) | 结束会话 | `--session` | `--session 123` |
| [query-link-records.py](#query-link-recordspy) | 链接记录 | `--url` | `--url https://...` |
| [query-links.py](#query-linkspy) | 链接管理 | 无 | - |

### ⚙️ 开发与维护

| 脚本 | 功能 | 常用参数 | 示例 |
|------|------|---------|------|
| [check-api-updates.py](#check-api-updatespy) | 检查 API 更新 | 无 | - |
| [generate-query-script.py](#generate-query-scriptpy) | 生成查询脚本 | `--api-id` | `--api-id 123` |
| [batch-generate-scripts.py](#batch-generate-scriptspy) | 批量生成脚本 | 无 | - |

---

## 📖 详细文档

### daily-sales-report.py

**功能**：生成当日销售活动总结

**API**: `/api/v2/daily-sales-report`

**参数**：
```bash
--date DATE      # 指定日期（YYYY-MM-DD 格式）
--days N         # 最近 N 天
--today          # 今天
--yesterday      # 昨天
```

**示例**：
```bash
# 查询今天的销售数据
uv run scripts/daily-sales-report.py --today

# 查询最近 7 天的销售趋势
uv run scripts/daily-sales-report.py --days 7

# 查询指定日期
uv run scripts/daily-sales-report.py --date 2026-03-15
```

**输出**：
```
📊 销售数据报表 - 2026-03-17
┌────────────┬────────┬────────┬────────┐
│ 日期       │ 成交数 │ 金额   │ 转化率 │
├────────────┼────────┼────────┼────────┤
│ 今天       │ 5 单    │ ¥30,000│ 12.5%  │
└────────────┴────────┴────────┴────────┘
```

---

### query-customers.py

**功能**：查询客户列表，支持多种筛选条件

**API**: `/api/v2/get-contact-list`

**参数**：
```bash
--page N           # 页码（默认 1）
--page-size N      # 每页数量（默认 20）
--days N           # 最近 N 天创建的客户
--filter-by TYPE   # 筛选类型（created/updated/last_contact）
--tags TAG1,TAG2   # 按标签筛选
--source SOURCE    # 按来源筛选（小红书/抖音/官网等）
```

**示例**：
```bash
# 查询最近 7 天新增的客户
uv run scripts/query-customers.py --days 7

# 查询 VIP 标签的客户
uv run scripts/query-customers.py --tags VIP

# 查询来自小红书的客户
uv run scripts/query-customers.py --source 小红书

# 分页查询（第 2 页，每页 10 个）
uv run scripts/query-customers.py --page 2 --page-size 10
```

**输出**：
```
👥 客户列表
┌──────┬────────┬──────────┬────────┬────────────┐
│ 姓名 │ 标签   │ 来源     │ 状态   │ 创建时间   │
├──────┼────────┼──────────┼────────┼────────────┤
│ 张三 │ VIP    │ 小红书   │ 意向   │ 2026-03-15 │
│ 李四 │ 普通   │ 抖音     │ 新咨询 │ 2026-03-16 │
└──────┴────────┴──────────┴────────┴────────────┘
```

---

### query-all-messages.py

**功能**：查询聊天记录，支持自然语言时间参数

**API**: `/api/v2/get-all-message-list`

**参数**：
```bash
--today            # 今天
--yesterday        # 昨天
--days N           # 最近 N 天
--session ID       # 指定会话 ID
--contact ID       # 指定联系人 ID
--type TYPE        # 消息类型（text/image/file）
--limit N          # 返回数量限制（默认 100）
```

**示例**：
```bash
# 查询今天的聊天记录
uv run scripts/query-all-messages.py --today

# 查询最近 3 天的聊天记录
uv run scripts/query-all-messages.py --days 3

# 查询指定会话的聊天记录
uv run scripts/query-all-messages.py --session 12345

# 查询最近 50 条消息
uv run scripts/query-all-messages.py --limit 50
```

**输出**：
```
💬 聊天记录 - 2026-03-17
┌────────────────────┬────────────┬──────────────┐
│ 时间               │ 发送者     │ 内容         │
├────────────────────┼────────────┼──────────────┤
│ 2026-03-17 10:30   │ 客户       │ 产品多少钱？ │
│ 2026-03-17 10:31   │ 客服       │ 您好，...    │
└────────────────────┴────────────┴──────────────┘
```

---

### find-followup-customers.py

**功能**：找出 N 天未联系的客户，生成待跟进列表

**API**: `/api/v2/get-contact-list` + 最后联系时间分析

**参数**：
```bash
--days N           # N 天未联系（默认 7）
--limit N          # 返回数量限制（默认 20）
--dingtalk         # 推送到钉钉
--export FILE      # 导出到 CSV 文件
```

**示例**：
```bash
# 查询 3 天未联系的客户
uv run scripts/find-followup-customers.py --days 3

# 查询 7 天未联系的客户，限制 50 个
uv run scripts/find-followup-customers.py --days 7 --limit 50

# 查询并推送到钉钉
uv run scripts/find-followup-customers.py --days 3 --dingtalk

# 查询并导出到 CSV
uv run scripts/find-followup-customers.py --days 7 --export followup.csv
```

**输出**：
```
⏰ 待跟进客户列表 - 3 天未联系
┌──────┬────────┬────────────┬────────────┐
│ 姓名 │ 标签   │ 最后联系   │ 待办事项   │
├──────┼────────┼────────────┼────────────┤
│ 张三 │ VIP    │ 3 月 14 日   │ 报价跟进   │
│ 李四 │ 意向   │ 3 月 13 日   │ 合同确认   │
└──────┴────────┴────────────┴────────────┘
```

---

### customer-stats.py

**功能**：深度分析客户数据

**API**: `/api/v2/get-contact-list` + 统计分析

**参数**：
```bash
--days N           # 分析最近 N 天（默认 30）
--source           # 按来源分析
--tags             # 按标签分析
--trend            # 显示趋势图
```

**示例**：
```bash
# 分析最近 30 天的客户数据
uv run scripts/customer-stats.py --days 30

# 按来源分析客户分布
uv run scripts/customer-stats.py --days 30 --source

# 按标签分析客户分布
uv run scripts/customer-stats.py --tags
```

**输出**：
```
📊 客户统计分析 - 最近 30 天

客户总量：1,234 人
新增客户：345 人
流失客户：23 人

客户来源分布：
┌──────────┬────────┬────────┐
│ 来源     │ 数量   │ 占比   │
├──────────┼────────┼────────┤
│ 小红书   │ 156    │ 45.2%  │
│ 抖音     │ 98     │ 28.4%  │
│ 官网     │ 56     │ 16.2%  │
│ 其他     │ 35     │ 10.2%  │
└──────────┴────────┴────────┘
```

---

### member-session-stats.py

**功能**：统计指定时间范围内每个客服的接待会话数（按活跃/已结束分类）

**API**: 
- `/api/v2/get-member-list`
- `/api/v2/get-session-list`

**参数**：
```bash
--today            # 统计今天
--yesterday        # 统计昨天
--days N           # 统计最近 N 天
--start-date DATE  # 开始日期（YYYY-MM-DD）
--end-date DATE    # 结束日期（YYYY-MM-DD）
--status N         # 会话状态（0=活跃，1=已结束，不传则统计全部）
--member ID        # 指定客服 ID
```

**示例**：
```bash
# 统计 2026 年 3 月所有客服的会话数（活跃 + 已结束）
uv run scripts/member-session-stats.py --start-date 2026-03-01 --end-date 2026-03-31

# 统计今天的会话
uv run scripts/member-session-stats.py --today

# 只统计活跃会话
uv run scripts/member-session-stats.py --status 0 --days 30

# 只统计已结束会话
uv run scripts/member-session-stats.py --status 1 --days 30

# 统计指定客服的会话
uv run scripts/member-session-stats.py --member 167 --days 7
```

**输出**：
```
📊 团队客服会话统计
====================================================================================================
客服              角色           总会话        活跃       已结束       
----------------------------------------------------------------------------------------------------
未分配             -            8          0        8         
客服167           普通成员         3          3        0         
客服216571        普通成员         0          0        0         
----------------------------------------------------------------------------------------------------
总计                           11         3        8         
====================================================================================================
```

**说明**：
- **按成员统计**：遍历所有成员，分别查询活跃和已结束会话数量
- **未分配会话**：自动统计 `sys_user_id=0` 的已结束会话（未分配给任何客服）
- **直接使用 total**：API 返回的 `total` 字段，避免获取大量列表数据
- **北京时间**：所有时间计算使用北京时间（UTC+8）

**注意事项**：
- ⚠️ API 的 `sys_user_id=0` 对活跃会话筛选有 Bug，未分配活跃会话不统计
- ✅ API 的 `sys_user_id=0` 对已结束会话筛选正常
- ⚠️ API 的时间筛选参数对 `total` 生效，对 `list` 可能返回空数组（使用 total 即可）
- **单独查询**：使用 `--status 0` 或 `--status 1` 单独查询
- **详细模式**：`--verbose` 显示每个会话的详细信息
- **自动分页**：自动获取所有页面数据，无需手动分页

---

### query-members.py

**功能**：查询团队成员列表

**API**: `/api/v2/get-member-list`

**参数**：无

**示例**：
```bash
uv run scripts/query-members.py
```

**输出**：
```
👥 团队成员
┌──────┬────────┬────────────┬────────┐
│ 姓名 │ 角色   │ 邮箱       │ 状态   │
├──────┼────────┼────────────┼────────┤
│ 小王 │ 客服   │ wang@...   │ 在线   │
│ 小李 │ 销售   │ li@...     │ 离线   │
└──────┴────────┴────────────┴────────┘
```

---

### query-sessions.py

**功能**：查询会话列表

**API**: `/api/v2/get-session-list`

**参数**：
```bash
--status N         # 会话状态（0=全部，1=进行中，2=已结束）
--member ID        # 指定成员 ID
--days N           # 最近 N 天
```

**示例**：
```bash
# 查询进行中的会话
uv run scripts/query-sessions.py --status 1

# 查询小王的会话
uv run scripts/query-sessions.py --member 123

# 查询最近 7 天的会话
uv run scripts/query-sessions.py --days 7
```

---

### assign-session.py

**功能**：分配会话给指定成员

**API**: `/api/v2/assign-session`

**参数**：
```bash
--session ID       # 会话 ID（必需）
--member ID        # 成员 ID（必需）
```

**示例**：
```bash
uv run scripts/assign-session.py --session 12345 --member 678
```

---

### create-customer.py

**功能**：创建新客户

**API**: `/api/v2/create-contact`

**参数**：
```bash
--name NAME        # 客户姓名（必需）
--phone PHONE      # 手机号
--email EMAIL      # 邮箱
--source SOURCE    # 来源
--tags TAG1,TAG2   # 标签
```

**示例**：
```bash
uv run scripts/create-customer.py --name 张三 --phone 13800138000 --tags VIP
```

---

### update-customer.py

**功能**：更新客户信息

**API**: `/api/v2/update-contact`

**参数**：
```bash
--id ID            # 客户 ID（必需）
--name NAME        # 新姓名
--phone PHONE      # 新手机号
--tags TAG1,TAG2   # 新标签（覆盖原有标签）
--add-tags TAG1    # 添加标签
--remove-tags TAG1 # 移除标签
```

**示例**：
```bash
# 更新客户姓名
uv run scripts/update-customer.py --id 123 --name 李四

# 添加 VIP 标签
uv run scripts/update-customer.py --id 123 --add-tags VIP

# 移除普通标签
uv run scripts/update-customer.py --id 123 --remove-tags 普通
```

---

### batch-tags.py

**功能**：批量给客户打标签

**API**: `/api/v2/batch-update-contact-tags`

**参数**：
```bash
--customer-ids ID1,ID2,ID3  # 客户 ID 列表（必需）
--tags TAG1,TAG2            # 标签列表（必需）
--operation add/remove      # 操作类型（默认 add）
```

**示例**：
```bash
# 给多个客户添加 VIP 标签
uv run scripts/batch-tags.py --customer-ids 1,2,3 --tags VIP

# 从多个客户移除普通标签
uv run scripts/batch-tags.py --customer-ids 1,2,3 --tags 普通 --operation remove
```

---

### import-orders.py

**功能**：批量导入订单

**API**: `/api/v2/import-orders`

**参数**：
```bash
--file FILE        # CSV 文件路径（必需）
--dry-run          # 预演模式（不实际导入）
```

**示例**：
```bash
# 导入订单
uv run scripts/import-orders.py --file orders.csv

# 预演模式（检查数据）
uv run scripts/import-orders.py --file orders.csv --dry-run
```

---

### query-whatsapp-apps.py

**功能**：查询 WhatsApp 设备列表

**API**: `/api/v2/get-individual-whatsapp-list`

**参数**：无

**示例**：
```bash
uv run scripts/query-whatsapp-apps.py
```

**输出**：
```
📱 WhatsApp 设备列表
┌──────┬────────┬────────────┬────────┐
│ 名称 │ 状态   │ 最后在线   │ 消息数 │
├──────┼────────┼────────────┼────────┤
│ 客服 1 │ 在线   │ 刚刚       │ 123    │
│ 客服 2 │ 离线   │ 2 小时前   │ 456    │
└──────┴────────┴────────────┴────────┘
```

---

### add-whatsapp-device.py

**功能**：添加新的 WhatsApp 设备

**API**: `/api/v2/add-whatsapp-device`

**参数**：
```bash
--name NAME        # 设备名称（必需）
```

**示例**：
```bash
uv run scripts/add-whatsapp-device.py --name 客服 3
```

---

### delete-whatsapp-device.py

**功能**：删除 WhatsApp 设备

**API**: `/api/v2/delete-whatsapp-device`

**参数**：
```bash
--app-id ID        # 设备 ID（必需）
```

**示例**：
```bash
uv run scripts/delete-whatsapp-device.py --app-id 123
```

---

### get-whatsapp-qrcode.py

**功能**：获取 WhatsApp 登录二维码

**API**: `/api/v2/get-whatsapp-qrcode`

**参数**：
```bash
--app-id ID        # 设备 ID（必需）
```

**示例**：
```bash
uv run scripts/get-whatsapp-qrcode.py --app-id 123
```

---

### set-whatsapp-proxy.py

**功能**：设置 WhatsApp 设备代理

**API**: `/api/v2/set-whatsapp-proxy`

**参数**：
```bash
--app-id ID        # 设备 ID（必需）
--proxy URL        # 代理地址（必需）
```

**示例**：
```bash
uv run scripts/set-whatsapp-proxy.py --app-id 123 --proxy http://proxy.example.com:8080
```

---

### daily-feedback-report.py

**功能**：生成每日客户反馈报告

**API**: `/api/v2/get-feedback-list`

**参数**：
```bash
--days N           # 最近 N 天（默认 1）
--dingtalk         # 推送到钉钉
```

**示例**：
```bash
# 生成今天的反馈报告
uv run scripts/daily-feedback-report.py --today

# 生成最近 7 天的反馈报告并推送钉钉
uv run scripts/daily-feedback-report.py --days 7 --dingtalk
```

---

### check-customer-feedback.py

**功能**：检查客户反馈中的敏感词

**API**: `/api/v2/get-all-message-list` + 敏感词分析

**参数**：
```bash
--days N           # 检查最近 N 天（默认 7）
--sensitive        # 只显示敏感词消息
--dingtalk         # 发现敏感词立即推送钉钉
```

**示例**：
```bash
# 检查最近 7 天的反馈
uv run scripts/check-customer-feedback.py --days 7

# 只查看敏感词消息
uv run scripts/check-customer-feedback.py --days 7 --sensitive

# 发现敏感词立即推送钉钉
uv run scripts/check-customer-feedback.py --days 7 --dingtalk
```

---

### query-messages.py

**功能**：查询指定会话的消息

**API**: `/api/v2/get-message-list`

**参数**：
```bash
--session ID       # 会话 ID（必需）
--limit N          # 返回数量（默认 20）
--type TYPE        # 消息类型（text/image/file）
```

**示例**：
```bash
uv run scripts/query-messages.py --session 12345 --limit 50
```

---

### get-customer-history.py

**功能**：获取客户完整画像（基本信息 + 订单 + 标签 + 聊天记录）

**API**: 多个 API 组合

**参数**：
```bash
--chat-user-id ID   # 客户 ID（必需，与 --phone 二选一）
--phone PHONE       # 手机号（与 chat-user-id 二选一）
--days N            # 查询最近 N 天的消息（默认 30 天）
--message-limit N   # 返回多少条消息（默认 10 条）
--dingtalk          # 发送到钉钉群
```

**使用场景**：
- ✅ 已知客户 ID，查询完整画像
- ✅ 已知手机号，查询客户信息
- ✅ 查看特定客户的聊天记录和跟进历史

**示例**：
```bash
# 通过客户 ID 查询（推荐）
uv run scripts/get-customer-history.py --chat-user-id abc123

# 通过手机号查询
uv run scripts/get-customer-history.py --phone 8613800138000

# 查询客户最近 7 天的聊天记录
uv run scripts/get-customer-history.py --chat-user-id abc123 --days 7

# 只返回 5 条消息
uv run scripts/get-customer-history.py --chat-user-id abc123 --message-limit 5
```

**与 query-customers.py 的区别**：
- `query-customers.py` → 批量查询客户列表（按时间/标签筛选）
- `get-customer-history.py` → 查询单个客户详细信息（已知 ID 或手机号）

---

### end-session.py

**功能**：结束会话

**API**: `/api/v2/end-session`

**参数**：
```bash
--session ID       # 会话 ID（必需）
```

**示例**：
```bash
uv run scripts/end-session.py --session 12345
```

---

### query-link-records.py

**功能**：查询链接访问记录

**API**: `/api/v2/get-link-records`

**参数**：
```bash
--url URL          # 链接地址
--days N           # 最近 N 天
```

**示例**：
```bash
uv run scripts/query-link-records.py --url https://example.com --days 7
```

---

### query-links.py

**功能**：查询链接管理列表

**API**: `/api/v2/get-links`

**参数**：无

**示例**：
```bash
uv run scripts/query-links.py
```

---

### check-api-updates.py

**功能**：检查 SaleSmartly API 是否有更新

**参数**：无

**示例**：
```bash
uv run scripts/check-api-updates.py
```

---

### generate-query-script.py

**功能**：根据 API ID 自动生成查询脚本

**参数**：
```bash
--api-id ID        # API ID（必需）
```

**示例**：
```bash
uv run scripts/generate-query-script.py --api-id 12345
```

---

### batch-generate-scripts.py

**功能**：批量生成所有 API 的查询脚本

**参数**：无

**示例**：
```bash
uv run scripts/batch-generate-scripts.py
```

---

## 🔧 通用参数

所有脚本支持以下通用参数：

```bash
--help             # 显示帮助信息
--verbose          # 详细输出模式
--debug            # 调试模式
--output FORMAT    # 输出格式（table/json/csv）
```

---

## 📝 最佳实践

### 1. 使用配置文件

确保 `api-key.json` 在正确位置：
```bash
# 脚本目录
skills/salesmartly-api-skills/api-key.json

# 或工作目录
~/.openclaw/workspace/api-key.json
```

### 2. 使用 uv 运行

推荐使用 `uv` 而不是直接 `python3`：
```bash
# ✅ 推荐
uv run scripts/query-customers.py --days 7

# ❌ 不推荐（可能缺少依赖）
python3 scripts/query-customers.py
```

### 3. 敏感信息保护

- ✅ `api-key.json` 已添加到 `.gitignore`
- ✅ 不要将真实配置提交到 Git
- ✅ 使用 `api-key.json.example` 作为模板

### 4. 批量操作

批量操作前先测试单个：
```bash
# 先测试一个客户
uv run scripts/update-customer.py --id 123 --tags VIP

# 确认无误后批量操作
uv run scripts/batch-tags.py --customer-ids 1,2,3 --tags VIP
```

---

## ❓ 常见问题

### Q: 提示找不到 api-key.json？

**A**: 确保配置文件在正确位置：
```bash
# 方法 1：在脚本目录运行
cd ~/.openclaw/workspace/skills/salesmartly-api-skills
uv run scripts/query-customers.py

# 方法 2：复制配置文件到当前目录
cp api-key.json .
```

### Q: 如何查看脚本的完整参数？

**A**: 使用 `--help` 参数：
```bash
uv run scripts/query-customers.py --help
```

### Q: 输出太多怎么办？

**A**: 使用 `--limit` 或 `--page-size` 限制数量：
```bash
uv run scripts/query-customers.py --days 7 --page-size 10
```

### Q: 如何导出结果为 CSV？

**A**: 使用 `--output csv` 参数：
```bash
uv run scripts/query-customers.py --days 7 --output csv > customers.csv
```

---

## 📚 相关文档

- [SKILL.md](../SKILL.md) - 技能使用说明
- [examples/](../examples/) - 场景化示例
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南

---

**最后更新**: 2026-03-18
