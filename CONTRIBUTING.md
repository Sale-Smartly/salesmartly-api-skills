# 如何贡献

欢迎为 **SaleSmartly AI Skill** 项目贡献代码！🎉

## 🍴 Fork 与克隆

1. Fork 本项目到你的 GitHub 账号
2. 克隆到本地：
   ```bash
   git clone https://github.com/YOUR_USERNAME/salesmartly-api-skills.git
   cd salesmartly-api-skills
   ```

## 🔧 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 或使用 uv
uv run scripts/query-customers.py --help
```

## 📝 提交规范

### 分支命名

- `feature/xxx` - 新功能
- `fix/xxx` - Bug 修复
- `docs/xxx` - 文档更新
- `refactor/xxx` - 代码重构

### Commit Message 格式

```
<类型>: <简短描述>

<详细描述（可选）>
```

**类型说明**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具/配置

**示例**:
```
feat: 新增客户导出功能

- 添加 export-customers.py 脚本
- 支持 CSV 和 JSON 格式导出
- 添加 --format 参数选择输出格式
```

## 🧪 测试

提交前请确保：

1. 脚本能正常运行
2. 没有语法错误
3. 如果有新脚本，添加使用示例到 README

## 📤 提交 PR

1. 推送到你的分支：
   ```bash
   git push origin feature/your-feature
   ```

2. 在 GitHub 上创建 Pull Request

3. 在 PR 描述中说明：
   - 这个 PR 做了什么
   - 为什么需要这个改动
   - 如何测试

## 💡 贡献建议

### 好的贡献

- ✅ 新增实用的 API 脚本
- ✅ 修复 Bug
- ✅ 改进文档
- ✅ 优化代码结构
- ✅ 添加使用示例

### 不建议的贡献

- ❌ 没有实际用途的功能
- ❌ 破坏现有 API 的改动
- ❌ 没有文档的新功能

## ❓ 有问题？

- 提 [Issue](https://github.com/YOUR_USERNAME/salesmartly-api-skills/issues)
- 或在 PR 中讨论

---

感谢你的贡献！🙏
