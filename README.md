# SaleSmartly API Skills

> 🤖 SaleSmartly 全功能 API 自动化脚本系统 | 21 个核心脚本 | 100% API 覆盖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![API Coverage](https://img.shields.io/badge/API%20Coverage-100%25-green.svg)](https://salesmartly-api.apifox.cn/llms.txt)

一套专为 **OpenClaw AI 助手** 设计的 SaleSmartly API 自动化系统，支持客户管理、会话管理、营销管理、WhatsApp 集成等全功能。

---

## 🚀 快速开始

### 通过 OpenClaw 对话安装（建议方式 🌟）

在 OpenClaw 中直接说：

```
安装 https://github.com/Sale-Smartly/salesmartly-api-skills 技能
```

AI 会自动克隆项目并安装到 `skills/salesmartly-api-skills/` 目录。

配置完成后，直接对 AI 说：
- "查询最近 7 天的客户"
- "分析昨天的销售数据"
- "查看 WhatsApp 设备状态"
- "推送客户反馈报告到钉钉"

---

## 🔑 配置 API Key

在 `api-key.json` 中配置（不要提交到 Git）：

```json
{
  "apiKey": "your_api_key",
  "projectId": "your_project_id"
}
```

### 获取 API Key

1. 登录 [SaleSmartly 后台](https://www.salesmartly.com/)
2. 进入 **设置** → **API 集成**
3. 点击 **创建 API Key**
4. 复制 **API Key** 和 **Project ID**

---

## 📦 核心功能

| 功能模块 | 说明 |
|----------|------|
| 客户管理 | 查询/创建/更新客户，批量操作标签，导入订单 |
| 团队管理 | 获取团队成员信息 |
| 会话管理 | 查询聊天记录、会话分配、结束会话 |
| 营销管理 | 分流链接管理与数据统计 |
| WhatsApp | 设备全生命周期管理（添加/删除/扫码/代理） |
| 钉钉推送 | 客户反馈报告、待跟进提醒自动推送 |

---

## 📋 脚本列表

完整脚本列表见 `scripts/` 目录：

### 客户管理
- `query-customers.py` - 客户查询
- `create-customer.py` - 创建客户
- `update-customer.py` - 更新客户
- `batch-tags.py` - 批量打标签
- `import-orders.py` - 导入订单
- `customer-stats.py` - 客户统计分析

### 会话管理
- `query-sessions.py` - 会话列表查询
- `query-messages.py` - 聊天记录查询
- `query-all-messages.py` - 完整聊天记录查询
- `assign-session.py` - 分配会话
- `end-session.py` - 结束会话
- `member-session-stats.py` - 客服会话统计
- `online-duration-report.py` - 在线时长报表 ⭐ NEW

### 团队管理
- `query-members.py` - 团队成员查询

### 营销管理
- `query-links.py` - 分流链接查询
- `query-link-records.py` - 链接记录查询

### WhatsApp 管理
- `query-whatsapp-apps.py` - WhatsApp 设备查询
- `add-whatsapp-device.py` - 新增 WhatsApp 设备
- `delete-whatsapp-device.py` - 删除设备
- `get-whatsapp-qrcode.py` - 获取二维码
- `set-whatsapp-proxy.py` - 设置代理

### 报表与反馈
- `daily-sales-report.py` - 每日销售报告
- `daily-feedback-report.py` - 每日反馈报告
- `check-customer-feedback.py` - 客户反馈检查

### 开发工具
- `check-api-updates.py` - 检查 API 更新
- `generate-query-script.py` - 生成查询脚本
- `batch-generate-scripts.py` - 批量生成脚本

---

## 🔒 安全说明

- ✅ 所有 API 密钥通过配置文件加载，不硬编码
- ✅ 完整的 SSL 验证（CERT_REQUIRED + 主机名验证）
- ✅ 无动态代码生成或下载
- ✅ 所有脚本本地执行，不上传数据到外部服务器

---

## 📖 最佳实践

详细使用指南、典型场景案例、反馈渠道请查看：

**[📚 最佳实践指南 → BEST-PRACTICES.md](BEST-PRACTICES.md)**

包含：
- 🎯 5 个典型使用场景（销售复盘/反馈监控/WhatsApp 管理/展会客户/客服绩效）
- 💬 用户反馈渠道（微信群 + GitHub Issues）
- 🛠️ 高级技巧与常见问题
- 📊 效果衡量指标（平均每周节省 8-10 小时）

---

## 👥 用户社区

**微信群**：欢迎加入用户群交流使用心得、反馈问题、获取更新通知

> **如何加入**：
> - 方式 1：GitHub 提交 Issue 附上微信号，管理员邀请入群
> - 方式 2：发送邮件至 `support@salesmartly.com` 申请入群
> - 方式 3：联系你的 SaleSmartly 客户经理邀请
>
> **说明**：微信群二维码有效期 7 天且群满 200 人后无法扫码，请通过以上方式联系入群。

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

<div align="center">

**GitHub**: https://github.com/Sale-Smartly/salesmartly-api-skills

[⭐ Star this repo](https://github.com/Sale-Smartly/salesmartly-api-skills) if you find it useful!

</div>
