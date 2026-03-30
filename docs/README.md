# 开发者文档

这些文档供**技能包开发者**参考，AI 执行任务时**不会加载**。

---

## 📚 文档列表

| 文档 | 用途 | 大小 |
|------|------|------|
| [INTENT-RECOGNITION-GUIDE.md](./INTENT-RECOGNITION-GUIDE.md) | 意图识别优化指南 - 提升不同 LLM 模型下的准确率 | 15KB |
| [PROGRESSIVE-UPDATE-GUIDE.md](./PROGRESSIVE-UPDATE-GUIDE.md) | 渐进式更新方案 - 四阶段部署计划 | 7.3KB |
| [SKILL-OPTIMIZATION.md](./SKILL-OPTIMIZATION.md) | SKILL.md 优化建议 - 结构化改进清单 | 12KB |

---

## 🎯 使用场景

- **新增功能** → 参考 `PROGRESSIVE-UPDATE-GUIDE.md`
- **优化意图识别** → 参考 `INTENT-RECOGNITION-GUIDE.md` + `SKILL-OPTIMIZATION.md`
- **日常维护** → 参考 `../CHANGELOG.md` + `../RELEASE-CHECKLIST.md`

---

## 📁 与 references/ 的区别

| 目录 | 用途 | 读者 |
|------|------|------|
| `docs/` | 开发者指南、计划、建议 | **人类开发者** |
| `references/` | API 文档、签名规则、字段说明 | **AI 执行任务时** |

AI 只在需要时加载 `references/` 中的文档，不会加载 `docs/`。
