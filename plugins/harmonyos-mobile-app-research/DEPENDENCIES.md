# 依赖与安装

## 1. 基础环境

所有用户需要：

- 支持插件的 Codex CLI 或 ChatGPT 桌面应用；
- Git；
- 能访问插件市场仓库的网络环境。

运行 Python 脚本时推荐 Python 3.11 或更高版本。Windows ARM64 环境优先使用 `py -3.11` 或实际安装的 Python 路径，避免 Microsoft Store 的 `python3` 占位程序。

## 2. 纯分析技能

以下技能主要由模型读取 CSV、JSONL、Markdown 与图表完成，不要求 HDC、ADB 或登录社交平台：

- `app-review-tagging`
- `app-satisfaction-analysis`
- `app-satisfaction-report`

如果要在本地批量生成 DOCX、图表或 Excel，可选安装：

```powershell
py -3.11 -m pip install python-docx matplotlib pandas openpyxl
```

这些包不是安装插件本身的前置条件。

## 3. AppGallery 与 HarmonyOS 真机采集

适用技能：

- `collect-appgallery-reviews`
- `collect-appgallery-updates`
- `inventory-mobile-app-features` 的 HarmonyOS 路径

需要：

1. Windows、macOS 或 Linux 上可用的 HDC；
2. 可解锁并允许调试的 HarmonyOS 测试设备；
3. Python 3.11+；
4. 使用 Hypium 脚本时安装：

   ```powershell
   py -3.11 -m pip install -r plugins/harmonyos-mobile-app-research/requirements-harmony.txt
   ```

验证：

```powershell
hdc version
hdc list targets -v
py -3.11 -c "import hypium; print(hypium.__file__)"
```

只有 `hdc list targets -v` 明确显示 `Connected` 才开始采集。端口可达不代表设备已连接。

目标值必须由当前会话显式提供：

```powershell
$env:HDC_TARGET = '<Connected目标>'
```

不要把目标值固化到公共脚本或提交记录。

## 4. Android 真机盘点

`inventory-mobile-app-features` 的 Android 路径需要 Android Platform Tools：

```powershell
adb version
adb devices -l
```

只操作用户授权的测试设备。无线调试地址、配对码、序列号和账号信息不得进入公开证据。

## 5. 小红书应用舆情

`collect-xiaohongshu-app-sentiment` 的采集阶段依赖单独安装的 Agent Reach，并由它选择可用的小红书后端。分析脚本本身只使用 Python 标准库。

验证：

```powershell
agent-reach doctor --json
```

若 Agent Reach 不可用，仍可对用户已经提供的脱敏 JSON/CSV 做整理与分析，但不要声称完成了线上采集。插件不会读取浏览器 Cookie；需要登录态时必须使用用户自己控制的现有会话。

## 6. 故障边界

- `hdc` 找不到：安装开发工具并把 HDC 所在目录加入 `PATH`。
- HDC 显示 `Offline`：停止采集，重新检查设备授权和网络路由；不要继续复用旧地址。
- `hypium` 导入失败：确认 pip 与运行脚本使用同一个 Python。
- 小红书后端不可用：报告采集阻塞，不自动登录或借用 Cookie。
- 没有真机：使用截图、录屏、UI Tree、已有清单或合成 fixture，只把结果标记为材料核验，不声称完整行为验证。
