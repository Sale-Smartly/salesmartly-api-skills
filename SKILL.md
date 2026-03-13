---
name: salesmartly-api
description: SaleSmartly 全功能 API 技能。支持客户管理、团队管理、会话管理、营销管理、WhatsApp 集成。可根据 API 文档自动生成脚本。
---

# SaleSmartly API 技能

> 提供 SaleSmartly 全功能 API 查询与管理能力，支持自动脚本生成

## 核心能力

1. **客户管理** - 查询、创建、更新客户，批量操作标签，导入订单
2. **团队管理** - 获取团队成员信息
3. **会话管理** - 查询聊天记录、会话分配、结束会话
4. **营销管理** - 分流链接管理与数据统计
5. **集成管理** - WhatsApp 设备全生命周期管理
6. **自动生成** - 从 API 文档自动生成查询脚本

## 配置方式

### 配置文件（推荐）

在 `api-key.json` 中配置：

```json
{
  "apiKey": "your_api_key",
  "projectId": "your_project_id"
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

### 会话管理

```bash
# 查询聊天记录
uv run scripts/query-messages.py --chat-user-id <用户 ID> --days 7

# 全量记录
uv run scripts/query-all-messages.py --page-size 50

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

## 🤖 自动生成脚本

### 批量生成

```bash
uv run scripts/batch-generate-scripts.py
```

从 `https://salesmartly-api.apifox.cn/llms.txt` 自动获取所有 API 并生成脚本。

### 单个生成

```bash
uv run scripts/generate-query-script.py --api-id 276530997e0
```

### API 列表

目前支持 **17 个 API 端点**：

- 客户管理：5 个 API
- 团队管理：1 个 API
- 会话管理：4 个 API
- 营销管理：2 个 API
- WhatsApp 集成：5 个 API

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

## 注意事项

1. **API 域名**: `https://developer.salesmartly.com`
2. **时间戳**: 13 位毫秒自动转换为秒
3. **SSL**: 跳过证书验证
4. **分页**: page_size 最大 100

## 相关文档

- [API 文档](https://salesmartly-api.apifox.cn/llms.txt)
- [签名规则](https://help.salesmartly.com/docs/API-Header)
