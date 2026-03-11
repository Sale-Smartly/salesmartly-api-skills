# SalesSmartly API 脚本更新指南

## 🚀 快速更新命令

### 方式 1：直接对我说（推荐）

```
帮我更新 SalesSmartly API 脚本
```

我会自动：
1. 检查最新的 API 文档
2. 对比现有脚本
3. 生成缺失的脚本
4. 报告更新结果

### 方式 2：使用检查脚本

```bash
cd /home/admin/.openclaw/workspace/skills/salesmartly-agent
uv run scripts/check-api-updates.py
```

**输出示例：**
```
======================================================================
📊 SalesSmartly API 脚本更新检查
======================================================================

📄 获取最新 API 列表...
✅ 找到 17 个 API

======================================================================
📋 检查结果
======================================================================

✅ 已实现：17/17
   • V2 > 客户管理 - 新增客户
     脚本：create-customer.py (7127 bytes)
     API: /api/v2/add-contact [POST]
   ...

======================================================================
📊 总结
======================================================================
API 总数：17
已实现：17 (100%)
未实现：0

✅ 所有 API 脚本已实现！
======================================================================
```

### 方式 3：批量生成

```bash
# 一键生成所有缺失的脚本
uv run scripts/batch-generate-scripts.py
```

### 方式 4：单个生成

```bash
# 1. 从 llms.txt 找到 API ID
# 2. 运行生成器
uv run scripts/generate-query-script.py --api-id 276530997e0
```

## 📋 API 列表（17 个）

### 客户管理（5 个）

| API | API ID | 脚本 | 状态 |
|-----|--------|------|------|
| 获取客户列表 | 258167563e0 | query-customers.py | ✅ |
| 新增客户 | 276530997e0 | create-customer.py | ✅ |
| 批量操作标签 | 296178103e0 | batch-tags.py | ✅ |
| 更新客户资料 | 296183457e0 | update-customer.py | ✅ |
| 导入客户订单 | 311462851e0 | import-orders.py | ✅ |

### 团队管理（1 个）

| API | API ID | 脚本 | 状态 |
|-----|--------|------|------|
| 获取团队成员 | 310397215e0 | query-members.py | ✅ |

### 会话管理（4 个）

| API | API ID | 脚本 | 状态 |
|-----|--------|------|------|
| 获取聊天记录（指定用户） | 317790952e0 | query-messages.py | ✅ |
| 获取聊天记录（全量） | 385681563e0 | query-all-messages.py | ✅ |
| 会话分配 | 323506414e0 | assign-session.py | ✅ |
| 结束会话 | 339565482e0 | end-session.py | ✅ |

### 营销管理（2 个）

| API | API ID | 脚本 | 状态 |
|-----|--------|------|------|
| 获取分流链接列表 | 326349441e0 | query-links.py | ✅ |
| 获取分流链接记录表 | 326351442e0 | query-link-records.py | ✅ |

### WhatsApp 集成（5 个）

| API | API ID | 脚本 | 状态 |
|-----|--------|------|------|
| 获取 WhatsApp APP 列表 | 326572731e0 | query-whatsapp-apps.py | ✅ |
| 获取登录二维码 | 328937730e0 | get-whatsapp-qrcode.py | ✅ |
| 新增设备 | 334587546e0 | add-whatsapp-device.py | ✅ |
| 设置代理 | 334594569e0 | set-whatsapp-proxy.py | ✅ |
| 删除设备 | 334595469e0 | delete-whatsapp-device.py | ✅ |

## 🔍 更新场景

### 场景 1：SalesSmartly 新增 API

**步骤：**
1. 运行检查：`uv run scripts/check-api-updates.py`
2. 查看未实现的 API
3. 对我说："帮我生成新增的 API 脚本"
4. 或手动生成：`uv run scripts/batch-generate-scripts.py`

### 场景 2：API 参数变更

**步骤：**
1. 检查 API 文档是否有变化
2. 删除旧脚本：`rm scripts/<旧脚本>.py`
3. 重新生成：`uv run scripts/generate-query-script.py --api-id <API_ID>`
4. 测试新脚本

### 场景 3：定期检查

建议每周运行一次检查：

```bash
uv run scripts/check-api-updates.py
```

## 📖 相关文档

- [API 文档](https://salesmartly-api.apifox.cn/llms.txt) - 官方 API 列表
- [README.md](README.md) - 完整使用说明
- [UPDATE-GUIDE.md](UPDATE-GUIDE.md) - 详细更新流程

## 💡 提示

1. **脚本生成器会自动跳过已存在的脚本**
2. **手写的核心脚本不会被覆盖**
3. **所有生成的脚本都包含 API ID，方便追踪**
4. **建议定期运行检查脚本，保持同步**

## 🤖 AI 命令示例

```
# 检查更新
检查 SalesSmartly API 是否有更新

# 生成缺失脚本
生成 SalesSmartly 缺失的 API 脚本

# 生成单个脚本
帮我生成 SalesSmartly 新增客户的脚本

# 重新生成
重新生成 SalesSmartly 更新客户资料的脚本
```
