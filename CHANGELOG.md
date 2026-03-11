# 更新日志

所有重要的项目变更都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 计划中
- [ ] 添加客户导出功能（CSV/JSON）
- [ ] 添加销售数据统计脚本
- [ ] 改进错误处理和日志输出
- [ ] 添加单元测试

---

## [1.0.0] - 2026-03-11

### ✨ 新增
- **17 个 API 端点全部实现**
  - 客户管理：5 个 API（查询/创建/更新/标签/订单）
  - 团队管理：1 个 API（成员查询）
  - 会话管理：4 个 API（消息查询/会话分配/结束会话）
  - 营销管理：2 个 API（分流链接/记录查询）
  - WhatsApp 集成：5 个 API（设备管理/二维码/代理）

- **自动生成脚本系统**
  - `generate-query-script.py` - 单个 API 生成器
  - `batch-generate-scripts.py` - 批量生成器
  - `check-api-updates.py` - API 更新检查器

- **完整文档**
  - README.md - 详细使用说明
  - SKILL.md - OpenClaw 技能文档
  - UPDATE-GUIDE.md - 更新指南
  - UPDATE-INSTRUCTIONS.md - 快速更新说明
  - CONTRIBUTING.md - 贡献指南
  - CHANGELOG.md - 更新日志

- **开发工具**
  - requirements.txt - Python 依赖声明
  - .gitignore - Git 忽略规则
  - LICENSE - MIT 开源协议

### 🔧 优化
- 统一所有脚本的命令行参数格式
- 改进 API 签名逻辑（支持 POST 接口）
- 优化时间戳处理（13 位毫秒自动转换）
- 跳过 SSL 证书验证（避免企业网络问题）

### 🐛 修复
- 修复 9 个 POST 脚本的签名逻辑（project_id 参与签名）
- 修复文件名不统一问题（全部改为英文）
- 修复时间戳格式导致的查询失败

### 📊 统计
- 脚本总数：19 个
- API 覆盖率：100%
- 文档完整度：100%

---

## 版本说明

### 版本号规则

- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 发布节奏

- **主版本**：重大更新（每季度）
- **次版本**：功能更新（每月）
- **修订版**：Bug 修复（按需）

---

## 贡献者

感谢所有为这个项目做出贡献的人！

- 初始版本和核心功能开发
- 文档完善和社区贡献

---

<div align="center">

**Made with ❤️** | [MIT License](LICENSE)

</div>
