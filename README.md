# SalesSmartly AI Skill

> 🤖 SalesSmartly 全功能 API 自动化脚本系统 | 17 个 API 端点 | 支持自动生成脚本

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![API Coverage](https://img.shields.io/badge/API%20Coverage-100%25-green.svg)](https://salesmartly-api.apifox.cn/llms.txt)
[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](CHANGELOG.md)

一套专为 **OpenClaw AI 助手** 设计的 SalesSmartly API 自动化系统，支持客户管理、会话管理、WhatsApp 集成等全功能，并可根据 API 文档自动生成脚本。

---

## ✨ 特性

- ✅ **100% API 覆盖** - 17 个 API 端点全部实现（客户/团队/会话/营销/WhatsApp）
- ✅ **自动生成脚本** - 从 API 文档自动生成 Python 脚本，无需手写
- ✅ **开箱即用** - 配置 API Key 即可使用，无需复杂环境
- ✅ **独立运行** - 可单独使用，也可集成到 OpenClaw
- ✅ **中文文档** - 完整中文使用说明和示例

---

## 📦 项目结构

```
salesmartly-agent/
├── LICENSE                     # MIT 开源协议
├── README.md                   # 使用说明
├── requirements.txt            # Python 依赖
├── SKILL.md                    # OpenClaw 技能文档
├── api-key.json                # API 配置（需手动创建，不要提交）
├── scripts/
│   # 核心查询脚本（手写）
│   ├── query-customers.py      # 客户查询
│   ├── query-members.py        # 团队成员查询
│   ├── query-messages.py       # 聊天记录查询
│   ├── query-links.py          # 分流链接查询
│   ├── query-whatsapp-apps.py  # WhatsApp 设备查询
│   
│   # 自动生成脚本（从 API 文档）
│   ├── create-customer.py      # 新增客户
│   ├── update-customer.py      # 更新客户资料
│   ├── batch-tags.py           # 批量操作标签
│   ├── import-orders.py        # 导入客户订单
│   ├── query-all-messages.py   # 全量聊天记录
│   ├── assign-session.py       # 会话分配
│   ├── end-session.py          # 结束会话
│   ├── query-link-records.py   # 分流链接记录
│   ├── add-whatsapp-device.py  # 新增 WhatsApp 设备
│   ├── delete-whatsapp-device.py  # 删除 WhatsApp 设备
│   ├── get-whatsapp-qrcode.py  # 获取登录二维码
│   └── set-whatsapp-proxy.py   # 设置设备代理
│   
│   # 数据分析脚本 🆕
│   ├── daily-sales-report.py   # 每日销售报告
│   └── customer-stats.py       # 客户统计分析
│   
│   # 脚本生成器
│   ├── generate-query-script.py     # 单个 API 生成器
│   └── batch-generate-scripts.py    # 批量生成器
│   
│   # 工具脚本
│   └── check-api-updates.py         # API 更新检查器
└── references/
    └── authentication.md       # 认证说明
```

---

## 🚀 快速开始

### 方式 1: 使用 uv（推荐）

```bash
# 1. 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目
git clone https://github.com/YOUR_USERNAME/salesmartly-agent.git
cd salesmartly-agent

# 3. 配置 API Key
cat > api-key.json << 'EOF'
{
  "apiKey": "your_api_key",
  "projectId": "your_project_id"
}
EOF
chmod 600 api-key.json

# 4. 测试运行
uv run scripts/query-customers.py --page 1 --page-size 5
```

### 方式 2: 使用 pip

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key（同上）

# 3. 运行脚本
python scripts/query-customers.py --page 1 --page-size 5
```

### 方式 3: 在 OpenClaw 中使用

如果你使用 OpenClaw AI 助手：

1. 将 `salesmartly-agent/` 文件夹放到 OpenClaw workspace 的 `skills/` 目录下
2. 配置 `api-key.json`
3. 对 AI 说："查询最近 7 天的客户"

---

## 🔑 获取 API Key

1. 登录 [SalesSmartly 后台](https://www.salesmartly.com/)
2. 进入 **设置** → **API 集成**
3. 点击 **创建 API Key**
4. 复制 **API Key** 和 **Project ID**
5. 填入 `api-key.json`

---

## 📋 可用脚本

### 客户管理

| 脚本 | 功能 | 示例 |
|------|------|------|
| `query-customers.py` | 查询客户列表 | `uv run scripts/query-customers.py --days 7` |
| `create-customer.py` | 新增客户 | `uv run scripts/create-customer.py --phone 8613800138000 --remark-name "张三"` |
| `update-customer.py` | 更新客户资料 | `uv run scripts/update-customer.py --chat-user-id <ID> --remark "VIP 客户"` |
| `batch-tags.py` | 批量操作标签 | `uv run scripts/batch-tags.py --chat-user-ids <ID1>,<ID2> --tag-ids <TAG_ID>` |
| `import-orders.py` | 导入客户订单 | `uv run scripts/import-orders.py --orders '<JSON>'` |

### 数据分析 🆕

| 脚本 | 功能 | 示例 |
|------|------|------|
| `daily-sales-report.py` | 每日销售报告 | `uv run scripts/daily-sales-report.py` |
| `customer-stats.py` | 客户统计分析 | `uv run scripts/customer-stats.py --days 30` |

**示例输出**:
```
$ uv run scripts/query-customers.py --page 1 --page-size 3

📊 查询结果 (共 125 个客户)
========================================
[1] 张三 - 86138****0000
    意向度：高
    最后联系：2026-03-10 14:30
    标签：VIP, 已成交
    
[2] 李四 - 86139****1111
    意向度：中
    最后联系：2026-03-08 09:15
    标签：潜在客户
    
[3] 王五 - 86137****2222
    意向度：低
    最后联系：2026-03-05 16:45
    标签：未跟进
========================================
```

---

### 团队管理

| 脚本 | 功能 | 示例 |
|------|------|------|
| `query-members.py` | 查询团队成员 | `uv run scripts/query-members.py --status active` |

**示例输出**:
```
$ uv run scripts/query-members.py --page-size 3

👥 团队成员 (共 8 人)
========================================
[1] 管理员 - admin@company.com (在线)
[2] 销售 A - sales1@company.com (在线)
[3] 销售 B - sales2@company.com (离线)
========================================
```

---

### 会话管理

| 脚本 | 功能 | 示例 |
|------|------|------|
| `query-messages.py` | 查询聊天记录（指定用户） | `uv run scripts/query-messages.py --chat-user-id <ID> --days 7` |
| `query-all-messages.py` | 查询聊天记录（全量） | `uv run scripts/query-all-messages.py --page-size 50` |
| `assign-session.py` | 会话分配 | `uv run scripts/assign-session.py --chat-user-id <ID> --member-id <成员 ID>` |
| `end-session.py` | 结束会话 | `uv run scripts/end-session.py --chat-session-id <会话 ID>` |

---

### 营销管理

| 脚本 | 功能 | 示例 |
|------|------|------|
| `query-links.py` | 查询分流链接列表 | `uv run scripts/query-links.py --days 30` |
| `query-link-records.py` | 查询分流链接记录 | `uv run scripts/query-link-records.py --link-id <链接 ID>` |

---

### WhatsApp 集成

| 脚本 | 功能 | 示例 |
|------|------|------|
| `query-whatsapp-apps.py` | 查询 WhatsApp 设备列表 | `uv run scripts/query-whatsapp-apps.py --page-size 20` |
| `add-whatsapp-device.py` | 新增 WhatsApp 设备 | `uv run scripts/add-whatsapp-device.py --name "设备 1" --phone 8613800138000` |
| `get-whatsapp-qrcode.py` | 获取登录二维码 | `uv run scripts/get-whatsapp-qrcode.py --id <设备 ID>` |
| `set-whatsapp-proxy.py` | 设置设备代理 | `uv run scripts/set-whatsapp-proxy.py --id <ID> --proxy-host 192.168.1.100 --proxy-port 8080` |
| `delete-whatsapp-device.py` | 删除 WhatsApp 设备 | `uv run scripts/delete-whatsapp-device.py --id <设备 ID>` |

**示例输出**:
```
$ uv run scripts/query-whatsapp-apps.py --page-size 3

📱 WhatsApp 设备 (共 5 个)
========================================
[1] 设备 A - 86188****4033
    状态：已登录
    最后在线：2026-03-11 11:30
    
[2] 设备 B - 86189****5044
    状态：待扫码
    二维码：运行 get-whatsapp-qrcode.py 获取
    
[3] 设备 C - 86187****6055
    状态：离线
    最后在线：2026-03-10 18:20
========================================
```

---

## 🤖 自动生成脚本

项目支持从 SalesSmartly API 文档自动生成脚本，无需手写！

### 批量生成所有 API 脚本

```bash
uv run scripts/batch-generate-scripts.py
```

从 `https://salesmartly-api.apifox.cn/llms.txt` 自动获取所有 API 并生成脚本。

### 生成单个 API 脚本

```bash
uv run scripts/generate-query-script.py --api-id 276530997e0
```

### 检查 API 更新

```bash
uv run scripts/check-api-updates.py
```

---

## 🔐 API 签名规则

SalesSmartly API 使用 MD5 签名：

```python
import hashlib

api_key = "your_api_key"
params = {
    "project_id": "f9m526",
    "page": "1",
    "page_size": "20"
}

# 1. 参数按字母排序
sorted_params = sorted(params.items(), key=lambda x: x[0])

# 2. Token 放最前面，用 & 连接
sign_parts = [api_key]
for k, v in sorted_params:
    sign_parts.append(f"{k}={v}")
sign_str = "&".join(sign_parts)

# 3. MD5 加密（32 位小写）
sign = hashlib.md5(sign_str.encode()).hexdigest()
```

详细规则见：[references/authentication.md](references/authentication.md)

---

## ❓ 常见问题

### Q: 报错"签名失败"或"Invalid signature"
**A**: 检查 `api-key.json` 里的 `apiKey` 和 `projectId` 是否正确，注意不要有多余空格。

### Q: 报错"SSL 证书验证失败"
**A**: 脚本已自动跳过证书验证。如仍报错，请检查网络是否能访问 `https://developer.salesmartly.com`

### Q: 返回空数据
**A**: 
- 检查时间范围参数，默认查询最近 7 天
- 确认账号下有数据
- 检查 API Key 权限

### Q: 报错"ModuleNotFoundError: No module named 'requests'"
**A**: 安装依赖：`pip install -r requirements.txt` 或使用 `uv run` 自动安装

### Q: 可以在 Windows 上用吗？
**A**: 可以，所有脚本都支持 Windows/Linux/macOS

### Q: 可以商用吗？
**A**: 可以，MIT 协议允许免费商用

---

## 📖 相关文档

- [SalesSmartly 官网](https://www.salesmartly.com/)
- [API 文档](https://salesmartly-api.apifox.cn/llms.txt)
- [签名规则](https://help.salesmartly.com/docs/API-Header)
- [OpenClaw 文档](https://docs.openclaw.ai)

---

## 🤝 如何贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🤝 与 SalesSmartly 共创

本项目希望与 **SalesSmartly 官方** 及 **广大用户** 共创，打造更好用的自动化工具！

### 📬 如果你有：

- 💡 **功能需求** - 需要某个自动化脚本但不会写
-  **优秀脚本** - 自己开发了好用的脚本想分享
- 🐛 **Bug 反馈** - 发现问题需要修复
- 🔧 **改进建议** - 想让某个功能更好用

### 📱 联系方式

**Telegram**: [@shamy_ssd](https://t.me/shamy_ssd)

👉 点击链接直接聊天：https://t.me/shamy_ssd

欢迎随时联系，一起让 SalesSmartly 更好用！🚀

---

## 📝 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

**最新版本**: v1.0.0 (2026-03-11)
- ✅ 17 个 API 端点全部实现
- ✅ 支持自动生成脚本
- ✅ 完整中文文档

---

## 📄 许可证

本项目采用 MIT 开源协议 - 详见 [LICENSE](LICENSE) 文件

---

## 💡 使用场景

### 场景 1: 销售每日跟进
```bash
# 查看今天需要跟进的客户
uv run scripts/query-customers.py --days 1

# 查看某个客户的聊天记录
uv run scripts/query-messages.py --chat-user-id <客户 ID> --days 7
```

### 场景 2: 客户批量管理
```bash
# 给 VIP 客户批量打标签
uv run scripts/batch-tags.py --chat-user-ids <ID1>,<ID2>,<ID3> --tag-ids <VIP 标签 ID>
```

### 场景 3: WhatsApp 设备管理
```bash
# 查看所有设备状态
uv run scripts/query-whatsapp-apps.py

# 获取二维码扫码登录
uv run scripts/get-whatsapp-qrcode.py --id <设备 ID>
```

### 场景 4: 销售数据分析
```bash
# 导出最近 30 天客户数据
uv run scripts/query-customers.py --days 30 --page-size 100 > customers.json

# 分析分流链接效果
uv run scripts/query-link-records.py --link-id <链接 ID>
```

---

## 🌟 致谢

感谢 SalesSmartly 提供强大的 API 支持！

---

<div align="center">

**Made with ❤️ for SalesSmartly Users**

[⭐ Star this repo](https://github.com/YOUR_USERNAME/salesmartly-agent) if you find it useful!

</div>
