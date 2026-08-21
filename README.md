# HarmonyOS Mobile App Research（鸿蒙应用解决方案助手）

面向 Codex 与 ChatGPT 的移动应用研究插件，包含 AppGallery 评论与版本采集、评论标签化、满意度分析与报告、小红书应用舆情分析，以及 Android/HarmonyOS 功能清单与差异矩阵。

本仓库是 Git-backed Codex 插件市场。插件只提供技能、脚本、模板和合成示例，不包含真实用户名、账号、设备地址、Cookie、令牌、原始评论数据或内部报告。

## 鸿蒙电脑上的使用场景

如果你正在搜索“鸿蒙电脑能否安装 Codex”“鸿蒙 PC 如何调用 ChatGPT”“鸿蒙电脑虚拟机运行 Cursor”或“HarmonyOS PC 使用 AI Agent”：可以先在鸿蒙 PC 内的 Windows 虚拟机中运行 Codex、ChatGPT、Cursor 等工具，再从虚拟机来宾系统使用本仓库的移动应用研究 Skill。实际路径是 `鸿蒙 PC → 虚拟机 → Windows → Codex / ChatGPT / Cursor`，不是鸿蒙原生安装。

## 从这里开始

- [7 个 Skill 的工作原理、流程与用法](docs/SKILL_WORKFLOWS.md)
- [按任务安装依赖](plugins/harmonyos-mobile-app-research/DEPENDENCIES.md)
- [完整工作流程与方法论（Markdown）](examples/workflow-methodology/鸿蒙应用研究_工作流程与方法论.md)
- [可下载工作流程与方法论（DOCX）](examples/workflow-methodology/鸿蒙应用研究_工作流程与方法论.docx)
- [公开分享前的隐私检查](PRIVACY.md)

安装后不需要记住 Skill 名称，直接描述任务即可。例如：

> 为“示例应用”做 2026 年 7 月 HarmonyOS 满意度月报。采集 AppGallery 评论与版本记录，完成脱敏、标签化和多维分析，最后生成 12 页以内的分析报告；每个结论都保留证据和限制说明。

## 安装插件

前置条件：

- 已安装并登录支持插件的 Codex CLI 或 ChatGPT 桌面应用。
- 已安装 Git，并能访问 GitHub。

在终端执行：

```powershell
codex plugin marketplace add joeaoe-hash/harmonyos-mobile-app-research
codex plugin add harmonyos-mobile-app-research@harmonyos-mobile-app-research
```

也可以先执行 `codex`，然后输入 `/plugins`，切换到 `HarmonyOS Mobile App Research` 市场并安装“鸿蒙应用解决方案助手”。

安装或升级后请新建任务，使新增技能和工具生效。

## 从 0.1.0 迁移

`0.2.0` 将插件 ID 从 `mobile-app-research` 改为 `harmonyos-mobile-app-research`。旧插件不会自动变成新插件：先按上面的新命令安装，再在 `/plugins` 中卸载或停用旧的 `mobile-app-research`。GitHub 会把旧仓库地址重定向到新地址，但后续配置应使用新名称。

升级市场与插件：

```powershell
codex plugin marketplace upgrade harmonyos-mobile-app-research
codex plugin add harmonyos-mobile-app-research@harmonyos-mobile-app-research
```

## 依赖分层

不是每个技能都要求连接真机。按任务安装最小依赖即可：

| 能力 | 必需依赖 | 可选依赖 |
|---|---|---|
| 评论标签化、满意度分析、Markdown 报告 | 插件本身 | Python 3.11+ 用于批量处理 |
| CSV 校验、合并、功能差异矩阵 | Python 3.11+ | 无第三方 Python 包 |
| AppGallery 评论/版本真机采集 | Python 3.11+、HDC、已连接 HarmonyOS 设备 | Hypium，见下方安装命令 |
| Android 真机功能盘点 | Android Platform Tools / ADB、测试设备 | UI Tree 与截图工具 |
| 小红书舆情采集 | 单独安装 Agent Reach；用户自己控制的已登录会话 | OpenCLI 后端 |
| DOCX/PDF 报告 | Codex 文档运行环境 | `python-docx`、`matplotlib`、`pandas`、`openpyxl` |

完整说明和验证命令见 [DEPENDENCIES.md](DEPENDENCIES.md)。

## HarmonyOS 采集快速配置

1. 安装包含 HDC 的 HarmonyOS/OpenHarmony 开发工具，并把 `hdc` 加入 `PATH`。
2. 安装 Python 依赖：

   ```powershell
   py -3.11 -m pip install -r plugins/harmonyos-mobile-app-research/requirements-harmony.txt
   ```

3. 连接设备并确认状态：

   ```powershell
   hdc list targets -v
   ```

4. 只使用输出中状态为 `Connected` 的目标；在当前 PowerShell 会话设置目标：

   ```powershell
   $env:HDC_TARGET = '<Connected目标>'
   ```

不要把设备地址、配对码或目标值写进脚本、日志、Issue 或提交记录。

## 隐私边界

- 公开仓库只包含合成示例；示例中的应用、用户、地区、设备和评论均为虚构。
- 采集结果默认保存在使用者自己的工作区，不提交回本仓库。
- 对外分享前移除用户名、账号 ID、设备序列号、无线调试地址、配对码、Cookie、令牌和精确位置。
- 评论正文仍可能包含个人信息；匿名用户名不等于完成脱敏，必须再次检查正文和字段组合。
- 小红书能力不会自动登录、读取 Cookie、发帖、评论、点赞或关注。

详细规则见 [PRIVACY.md](PRIVACY.md)。

## 包含的技能

- `collect-appgallery-reviews`
- `collect-appgallery-updates`
- `collect-xiaohongshu-app-sentiment`
- `app-review-tagging`
- `app-satisfaction-analysis`
- `app-satisfaction-report`
- `inventory-mobile-app-features`

每个 Skill 的输入、内部流程、输出、依赖、使用示例和验证边界见 [Skill 工作流总览](docs/SKILL_WORKFLOWS.md)。完整链路、单 Skill 使用和没有真机时的回退方式都在该文档中说明。

## 验证

在仓库根目录运行：

```powershell
py -3.11 -m pip install PyYAML
py -3.11 C:\path\to\plugin-creator\scripts\validate_plugin.py plugins/harmonyos-mobile-app-research
```

各技能还应使用 Codex 的 `skill-creator/scripts/quick_validate.py` 分别校验。发布前再运行一次隐私扫描，并确认 Git 历史中从未提交真实数据或凭据。

## 许可

当前仓库未附加开源许可证。除 GitHub 服务条款允许的浏览和派生操作外，不自动授予复制、修改或再分发权。仓库所有者可在确认许可范围后另行添加许可证。
