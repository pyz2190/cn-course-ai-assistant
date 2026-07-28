# 贡献指南

## 开发流程

1. 从最新的 `main` 创建分支：`feat/<角色>-<主题>`、`fix/<主题>` 或 `docs/<主题>`。
2. 先确认改动涉及的契约和负责人，再开始编码。
3. 小步提交；提交信息使用动词开头，例如 `add retrieval adapter`。
4. 推送前运行 `npm run check`。
5. 创建 Pull Request，填写影响范围、验证结果和接口变更。

角色简称使用 `a` 至 `e`，例如 `feat/d-retrieval-adapter`。

## 完成定义

一项改动只有在以下条件满足时才算完成：

- 实现与测试同时提交。
- 新增配置已补充 `.env.example`，且没有提交密钥。
- API 或模型变更已更新契约并通过 `npm run contracts:check`。
- 用户可见行为已说明验收方式。
- CI 全部通过，至少一位非作者成员完成评审。

## 代码边界

- `domain/` 只包含稳定的课程领域类型，不依赖 FastAPI、数据库或具体模型 SDK。
- `services/` 组织业务流程，通过端口访问外部能力。
- `adapters/` 实现模型、检索、Canvas、存储等可替换能力。
- API 路由负责协议转换，不放检索或提示词逻辑。
- Web 端只依赖生成的 OpenAPI 类型，不复制后端接口类型。

具体规则见 [协作规范](docs/collaboration.md) 和 [接口变更流程](docs/interface-change.md)。
