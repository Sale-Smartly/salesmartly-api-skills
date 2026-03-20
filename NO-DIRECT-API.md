# 🚫 禁止直接调用 API

**这是 SaleSmartly API Skills 的第一原则！**

---

## 核心规则

> ⛔ **无论任何情况，都不得直接使用 curl/Python/HTTP 客户端调用 SaleSmartly API！**
>
> ✅ **必须使用 `scripts/` 目录中的脚本！**

---

## 为什么？

### 1. 脚本已覆盖所有 API

**26 个脚本 = 100% API 覆盖率**

没有任何 API 是脚本无法调用的。如果脚本缺少功能，应该：
1. 检查是否有其他脚本已实现
2. 如果没有，先扩展脚本功能
3. **永远不要**绕过脚本直接调用 API

### 2. 直接调用 API 的常见问题

| 问题 | 描述 | 脚本如何处理 |
|------|------|-------------|
| **签名错误** | 参数排序、编码容易出错 | 统一签名函数 |
| **SSL 验证** | 可能跳过验证，不安全 | 统一配置（可禁用） |
| **分页遗漏** | 只获取第一页数据 | `--all` 自动获取所有页 |
| **时间格式** | 毫秒/秒容易混淆 | 自动转换（自然语言参数） |
| **错误处理** | 需要自己解析错误码 | 统一错误提示 |
| **配置管理** | 容易硬编码 API Key | 配置文件加载 |
| **数据格式化** | 原始 JSON 难以阅读 | 表格/摘要/JSON 输出 |

### 3. 真实案例

**❌ 错误案例**：
```python
# AI 直接调用 API
import requests
response = requests.get(
    "https://developer.salesmartly.com/api/v2/get-all-message-list",
    params={"project_id": "f9m526", "page": 1}
)
# 问题：
# 1. 没有签名 → API 拒绝请求
# 2. 没有处理分页 → 只获取第一页
# 3. 没有错误处理 → 崩溃
```

**✅ 正确做法**：
```bash
# 使用脚本
uv run scripts/query-all-messages.py --yesterday --summary
# 结果：
# - 自动签名
# - 自动分页
# - 自动错误处理
# - 格式化输出
```

---

## 脚本调用规范

### 基本格式

```bash
uv run scripts/<脚本名>.py [参数]
```

### 常用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--today` | 今天的数据 | `--today` |
| `--yesterday` | 昨天的数据 | `--yesterday` |
| `--days N` | 最近 N 天 | `--days 7` |
| `--all` | 获取所有数据（自动分页） | `--all` |
| `--summary` | 只显示统计摘要 | `--summary` |
| `--quiet` | 安静模式（只输出 JSON） | `--quiet` |
| `--chat-user-id ID` | 指定客户 | `--chat-user-id abc123` |
| `--session-id ID` | 指定会话 | `--session-id xyz789` |

### 示例

```bash
# 查询客户
uv run scripts/query-customers.py --days 7 --page-size 100

# 查询聊天记录
uv run scripts/query-messages.py --chat-user-id abc123 --days 7

# 全量消息（自动分页）
uv run scripts/query-all-messages.py --all --quiet

# 销售报告
uv run scripts/daily-sales-report.py --yesterday
```

---

## 如果脚本功能不足

### 步骤 1：检查现有脚本

```bash
ls scripts/*.py
cat scripts/README.md
```

可能已有脚本实现了你需要的功能！

### 步骤 2：扩展脚本

如果确实缺少功能：

1. 在对应脚本中添加参数
2. 测试通过后提交
3. 更新 `scripts/README.md`

**示例**：添加 `--session-id` 参数

```python
# scripts/query-messages.py
parser.add_argument('--session-id', type=str, help='会话 ID')
```

### 步骤 3：创建新脚本

如果是全新的 API：

1. 参考现有脚本结构
2. 实现 API 调用逻辑
3. 添加参数解析
4. 添加错误处理
5. 更新 `scripts/README.md`

---

## 自检清单

在调用 SaleSmartly API 前，问自己：

- [ ] 我是否在使用 `scripts/` 中的脚本？
- [ ] 我是否在用 `uv run scripts/xxx.py` 命令？
- [ ] 我是否避免了直接使用 `curl`/`requests`/`httpx`？
- [ ] 如果脚本功能不足，我是否先尝试扩展脚本？

**如果以上有任何一个"否"，请停止！重新检查你的方法。**

---

## 相关文件

- `SKILL.md` - 技能主文档（包含用户意图映射）
- `scripts/README.md` - 所有脚本的参数文档
- `ID-FIELDS-GUIDE.md` - ID 字段说明（避免混淆）
- `examples/` - 场景化示例

---

## 总结

> 📌 **记住：脚本是唯一正确的 API 调用方式！**
>
> - 脚本 = 安全 + 可靠 + 易维护
> - 直接调用 = 风险 + 错误 + 难调试
>
> **不要走捷径！使用脚本！**
