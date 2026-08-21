# HarmonyOS Mobile App Research（鸿蒙应用解决方案助手）

![鸿蒙应用解决方案助手：从应用证据到产品行动](docs/assets/social-preview.png)

**让 Codex / ChatGPT 成为你的鸿蒙产品研究 Agent：从 AppGallery 真机证据、用户评论和版本信息出发，完成结构化分析、功能验证与可交付报告。**

[English](README.en.md) · [60 秒安装](#60-秒安装) · [7 个 Skill 的工作流](docs/SKILL_WORKFLOWS.md) · [完整方法论](examples/workflow-methodology/鸿蒙应用研究_工作流程与方法论.md) · [输出参考](#可以直接看到的输出参考) · [许可范围](LICENSE-SCOPE.md)

这不是另一个只负责生成 ArkTS 代码的助手。它把移动应用研究中分散在设备、应用市场、表格、截图和文档里的工作，组织成可以由 Agent 调用、组合和复用的 7 个 Skill。

## 以前要自己查命令，现在只需要说清楚目标

| 过去的工作方式 | 现在可以怎样开始 |
|---|---|
| 连接手机、查找 HDC 命令、确认设备状态，再从终端结果里寻找 UDID | 告诉 Agent：“检查当前鸿蒙测试设备并读取本次调试需要的 UDID；如果目标不唯一，先停下来告诉我。” |
| 手动翻 AppGallery 评论、复制日期和评分、反复清洗表格 | 指定应用和月份，让 Agent 采集最新列表、检查缺口、标签化并输出可审计数据 |
| 靠截图和记忆比较 Android/HarmonyOS 功能 | 让 Agent 沿同一条用户路径逐页检查，生成带证据状态的功能树和差异矩阵 |
| 评论、版本、舆情和功能发现分别写在不同文档里 | 把已有 Skill 像积木一样组合，形成“证据 → 分析 → 判断 → 报告”的完整链路 |

UDID 是已有设备连接与功能盘点能力的延伸场景，不是单独增加的第八个 Skill。Agent 会先确认 HDC 和目标设备状态；它不会在多个设备之间自行猜测。

## 一套可以拆装的研究闭环

![从研究问题到可执行动作的六阶段闭环](examples/workflow-methodology/assets/01_end_to_end_workflow.png)

你可以从任何一个阶段开始：已经有 CSV，就从标签化开始；只想核对版本变化，就单独运行版本采集；只做双端功能补齐，就直接调用功能盘点。

## 从一句话开始

### 场景一：获取当前测试设备的 UDID

> 检查当前可用的 HarmonyOS 测试设备，确认只有一个明确的 Connected 目标后，读取本次调试需要的 UDID，并同时告诉我设备状态和使用的命令；如果设备未连接或目标不唯一，不要猜测。

### 场景二：从应用市场评论到满意度报告

> 为“示例应用”做 2026 年 7 月 HarmonyOS 满意度分析。采集 AppGallery 最新评论与正式版本记录，检查重复和日期缺口，完成标签化、多维分析并生成报告；每个结论都保留证据索引和限制说明。

### 场景三：比较 Android 与 HarmonyOS 功能

> 沿“首页 → 搜索 → 结果页 → 播放页”这条用户路径，逐页核对 Android 与 HarmonyOS 的功能。区分“已验证存在”“仅发现入口”“已验证缺失”“尚未检查”和“受阻”，输出功能树、差异矩阵和重测清单。

### 场景四：复盘一次版本更新

> 收集指定应用最近三个 HarmonyOS 正式版本的更新说明，并比较发布前后的评论主题变化。官方版本记录与用户反馈分开保存，不把时间相关性直接写成因果结论。

## 60 秒安装

前置条件：已安装并登录支持插件的 Codex CLI 或 ChatGPT 桌面应用；已安装 Git 并能访问 GitHub。

```powershell
codex plugin marketplace add joeaoe-hash/harmonyos-mobile-app-research
codex plugin add harmonyos-mobile-app-research@harmonyos-mobile-app-research
```

也可以先执行 `codex`，输入 `/plugins`，切换到 `HarmonyOS Mobile App Research` 市场并安装“鸿蒙应用解决方案助手”。安装或升级后请新建任务，让新版本生效。

升级已有安装：

```powershell
codex plugin marketplace upgrade harmonyos-mobile-app-research
codex plugin add harmonyos-mobile-app-research@harmonyos-mobile-app-research
```

## 7 个 Skill 分别负责什么

| Skill | 解决的问题 | 主要输出 |
|---|---|---|
| `collect-appgallery-reviews` | 按时间窗口采集 AppGallery 最新评论并检查虚拟列表缺口 | CSV、JSON、Markdown、采集检查点 |
| `collect-appgallery-updates` | 整理正式版本、尝鲜和测试计划，保留官方来源边界 | 版本时间线、结构化版本记录 |
| `collect-xiaohongshu-app-sentiment` | 还原帖子与评论语境，识别近期应用讨论主题 | 脱敏样本、主题与情感摘要 |
| `app-review-tagging` | 把自然语言反馈转换成稳定、可审计的标签数据 | JSONL、CSV、标签统计 |
| `app-satisfaction-analysis` | 计算趋势、主题、设备、地域和需求优先级 | 指标表、图表、P0/P1/P2 建议 |
| `app-satisfaction-report` | 把分析结果装配成面向决策的完整报告 | Markdown、DOCX/PDF 报告 |
| `inventory-mobile-app-features` | 按用户路径盘点功能并比较 Android/HarmonyOS | 功能树、证据矩阵、差异与重测清单 |

每个 Skill 的输入、内部步骤、输出、依赖、调用示例和停止条件，见 [Skill 工作流总览](docs/SKILL_WORKFLOWS.md)。

## 可以直接看到的输出参考

- [完整工作流程与方法论（Markdown）](examples/workflow-methodology/鸿蒙应用研究_工作流程与方法论.md)（版权保留，仅供输出参考）
- [可下载工作流程与方法论（DOCX）](examples/workflow-methodology/鸿蒙应用研究_工作流程与方法论.docx)（版权保留，仅供输出参考）
- [报告输出规范](plugins/harmonyos-mobile-app-research/skills/app-satisfaction-report/references/examples/report-method-standard.md)（版权保留，仅供输出参考）
- [完整报告实例](plugins/harmonyos-mobile-app-research/skills/app-satisfaction-report/references/examples/kugou-harmony-satisfaction-gold-example.md)（版权保留，仅供输出参考）

仓库中的公开样本均经过公开发布检查；使用自己的数据时，结果保存在自己的工作区。

## 按任务安装最小依赖

不是每个 Skill 都需要连接真机。

| 能力 | 必需依赖 | 可选依赖 |
|---|---|---|
| 评论标签化、满意度分析、Markdown 报告 | 插件本身 | Python 3.11+ 用于批量处理 |
| CSV 校验、合并、功能差异矩阵 | Python 3.11+ | 无第三方 Python 包 |
| AppGallery 评论/版本真机采集 | Python 3.11+、HDC、已连接 HarmonyOS 设备 | Hypium |
| Android 真机功能盘点 | Android Platform Tools / ADB、测试设备 | UI Tree 与截图工具 |
| 小红书舆情采集 | 单独安装 Agent Reach、用户控制的已登录会话 | OpenCLI 后端 |
| DOCX/PDF 报告 | Codex 文档运行环境 | `python-docx`、`matplotlib`、`pandas`、`openpyxl` |

完整命令和验证步骤见 [DEPENDENCIES.md](DEPENDENCIES.md)。HarmonyOS 真机任务开始前，先确认 `hdc list targets -v` 中存在状态为 `Connected` 的明确目标。

## 鸿蒙电脑、Codex、ChatGPT 与 Cursor

如果你正在搜索“鸿蒙电脑能否安装 Codex”“鸿蒙 PC 如何调用 ChatGPT”“鸿蒙电脑虚拟机运行 Cursor”或“HarmonyOS PC 使用 AI Agent”，当前可行路径是：

`鸿蒙 PC → Windows 虚拟机 → Codex / ChatGPT / Cursor → 本仓库 Skill`

这里描述的是在鸿蒙 PC 的 Windows 虚拟机中使用，不代表 Codex、ChatGPT 或 Cursor 已提供鸿蒙原生桌面版本。

## 从 0.1.0 迁移

`0.2.0` 将插件 ID 从 `mobile-app-research` 改为 `harmonyos-mobile-app-research`。先安装新插件，再在 `/plugins` 中卸载或停用旧的 `mobile-app-research`。后续配置统一使用新名称。

## 验证与共建

在仓库根目录运行插件验证：

```powershell
py -3.11 -m pip install PyYAML
py -3.11 scripts/validate_repository.py
py -3.11 C:\path\to\plugin-creator\scripts\validate_plugin.py plugins/harmonyos-mobile-app-research
```

想贡献真实使用反馈、新场景或文档改进，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，也可以直接提交 Issue 或在 Discussions 中描述你希望 Agent 帮你完成的鸿蒙工作。

如果这个项目让你少查了一次命令、少整理了一张表，或者帮助你更可靠地完成了一次鸿蒙应用研究，欢迎点一个 **Star**。它会帮助更多做鸿蒙产品、开发和测试的人发现这套工作流。

## 许可

本仓库中的 Skill、脚本、提示词、规范、模板、合成样本和通用项目文档采用 [MIT License](LICENSE) 开源。

已经完成的报告、方法论成品、伴读版、图表和排版资产不属于 MIT，继续保留版权。明确的目录边界和使用条件见 [许可范围说明](LICENSE-SCOPE.md)。
