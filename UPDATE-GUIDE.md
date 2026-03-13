# SaleSmartly API 脚本更新指南

## 🚀 快速更新（推荐）

### 一键更新所有脚本

```bash
cd /home/admin/.openclaw/workspace/skills/salesmartly-agent
uv run scripts/batch-generate-scripts.py
```

**工作流程：**
1. 自动从 `https://salesmartly-api.apifox.cn/llms.txt` 获取最新 API 列表
2. 对比现有脚本，跳过已存在的
3. 为新增的 API 生成脚本
4. 显示生成报告

### 更新单个 API 脚本

```bash
# 1. 从 llms.txt 找到 API ID
# 例如：新增客户 → 276530997e0

# 2. 运行生成器
uv run scripts/generate-query-script.py --api-id 276530997e0

# 3. 重命名生成的脚本（如果需要）
mv scripts/query-__*.py scripts/create-customer.py
```

## 📋 API ID 列表

从 llms.txt 获取的 API 映射：

| API 名称 | API ID | 脚本文件 |
|---------|--------|---------|
| 获取客户列表 | 258167563e0 | query-customers.py |
| 新增客户 | 276530997e0 | create-customer.py |
| 批量操作标签 | 296178103e0 | batch-tags.py |
| 更新客户资料 | 296183457e0 | update-customer.py |
| 导入客户订单 | 311462851e0 | import-orders.py |
| 获取团队成员 | 310397215e0 | query-members.py |
| 获取聊天记录（指定用户） | 317790952e0 | query-messages.py |
| 获取聊天记录（全量） | 385681563e0 | query-all-messages.py |
| 会话分配 | 323506414e0 | assign-session.py |
| 结束会话 | 339565482e0 | end-session.py |
| 获取分流链接列表 | 326349441e0 | query-links.py |
| 获取分流链接记录表 | 326351442e0 | query-link-records.py |
| 获取 WhatsApp APP 列表 | 326572731e0 | query-whatsapp-apps.py |
| 获取 WhatsApp 登录二维码 | 328937730e0 | get-whatsapp-qrcode.py |
| 新增 WhatsApp App 设备 | 334587546e0 | add-whatsapp-device.py |
| 设置 WhatsApp 代理 | 334594569e0 | set-whatsapp-proxy.py |
| 删除 WhatsApp App 设备 | 334595469e0 | delete-whatsapp-device.py |

## 🤖 让 AI 帮你更新

### 方式 1：直接命令

```
帮我更新 SaleSmartly API 脚本
```

我会：
1. 读取最新的 llms.txt
2. 对比现有脚本
3. 生成新增的 API 脚本
4. 报告更新结果

### 方式 2：指定 API

```
帮我生成 SaleSmartly 新增客户的脚本
```

我会：
1. 查找对应的 API ID
2. 生成脚本
3. 测试基本功能

### 方式 3：检查更新

```
检查 SaleSmartly API 是否有更新
```

我会：
1. 获取最新 API 列表
2. 对比已实现的脚本
3. 列出缺失的 API

## 📝 手动更新流程

### 步骤 1：查看 API 文档

访问：https://salesmartly-api.apifox.cn/llms.txt

找到新增或变更的 API，记录 API ID（如 `276530997e0`）

### 步骤 2：生成脚本

```bash
cd /home/admin/.openclaw/workspace/skills/salesmartly-agent
uv run scripts/generate-query-script.py --api-id <API_ID>
```

### 步骤 3：测试脚本

```bash
uv run scripts/<生成的脚本>.py --help
uv run scripts/<生成的脚本>.py --page 1 --page-size 5
```

### 步骤 4：重命名（如果需要）

```bash
mv scripts/query-__*.py scripts/<有意义的名字>.py
```

## ⚠️ 注意事项

1. **API 变更**：如果 API 参数变更，需要手动更新脚本
2. **签名规则**：所有脚本使用相同的签名算法，无需修改
3. **配置文件**：确保 `api-key.json` 配置正确
4. **测试**：生成后务必测试新脚本

## 🔧 脚本生成器选项

### batch-generate-scripts.py

```bash
# 默认：输出到 scripts/ 目录
uv run scripts/batch-generate-scripts.py

# 自定义输出目录
uv run scripts/batch-generate-scripts.py --output ./new-scripts/
```

### generate-query-script.py

```bash
# 使用 API ID
uv run scripts/generate-query-script.py --api-id 276530997e0

# 使用完整 URL
uv run scripts/generate-query-script.py --api-url https://salesmartly-api.apifox.cn/276530997e0.md

# 自定义输出目录
uv run scripts/generate-query-script.py --api-id 276530997e0 --output ./my-scripts/
```

## 📖 相关文档

- [API 文档](https://salesmartly-api.apifox.cn/llms.txt)
- [签名规则](https://help.salesmartly.com/docs/API-Header)
- [README.md](README.md) - 完整使用说明
