# 参与共建

感谢你愿意把真实使用体验带回项目。这个仓库最需要的不是泛泛的功能建议，而是“你原来怎样完成这项工作、希望 Agent 帮你省掉哪一步、什么输出才算真正可用”。

## 可以怎样贡献

- 提交一个鸿蒙产品、开发或测试场景。
- 报告可以稳定复现的问题。
- 补充 AppGallery、HDC、Hypium 或 Android/HarmonyOS 功能盘点的工作流。
- 改进提示词、字段规范、输出模板和公开示例。
- 增加不依赖真实用户数据的合成测试样本。

## 提交 Issue 前

1. 写清楚目标平台、应用版本、日期范围和期望输出。
2. 说明已经执行的步骤、实际结果和停止位置。
3. 日志只保留复现所需片段；移除用户名、账号、设备标识、调试地址、Cookie 和令牌。
4. 真实评论若不能可靠脱敏，请改写成合成样本。

## 本地验证

在仓库根目录准备验证依赖：

```powershell
py -3.11 -m pip install PyYAML
```

验证插件：

```powershell
py -3.11 scripts/validate_repository.py
py -3.11 C:\path\to\plugin-creator\scripts\validate_plugin.py plugins/harmonyos-mobile-app-research
```

如果修改了某个 `SKILL.md`，还应运行：

```powershell
py -3.11 C:\path\to\skill-creator\scripts\quick_validate.py plugins/harmonyos-mobile-app-research/skills/<skill-name>
```

## Pull Request

- 一个 PR 聚焦一个问题或一个场景。
- 在说明中写清楚“为什么改、改了什么、怎样验证”。
- 不提交采集产物、设备日志、浏览器会话、凭据或真实用户原文。
- 新增脚本应提供最小可运行示例；新增 Skill 应说明输入、流程、输出和停止条件。

第一次参与可以从带有 `good first issue` 标签的问题开始，也可以在 Discussions 中先描述场景。

## 贡献许可

提交到 MIT 覆盖范围内的代码、Skill、提示词、规范、模板和通用文档，将按照仓库根目录的 MIT License 提供。现成报告目录不属于 MIT；向这些目录贡献材料前，请先通过 Issue 确认版权和授权范围。完整边界见 [LICENSE-SCOPE.md](LICENSE-SCOPE.md)。
