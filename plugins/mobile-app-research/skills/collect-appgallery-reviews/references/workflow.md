# AppGallery 评论采集流程

## 1. 环境与设备

准备 HDC、64 位 Python、Hypium 和在线设备。Windows PowerShell 示例：

```powershell
$toolchain = "<OpenHarmony SDK>\toolchains"
$env:Path = "$toolchain;$env:Path"
hdc list targets -v
python -c "import hypium; print(hypium.__file__)"
```

只选择 `Connected` 的目标。将目标写入 `HDC_TARGET`，不要依赖离线历史地址。

## 2. 进入正确页面

1. 解锁设备并启动 `com.huawei.hmsapp.appgallery`。
2. 通过搜索框控件输入应用名称并触发搜索按钮。
3. 点击匹配的 `app_name` 控件进入详情。
4. 滚动到 `评分与评论`，点击 `查看全部`。
5. 点击分段控件中的 `最新`。
6. 转储 UI Tree，确认 `CommentDetailPostInfo0` 等字段显示“几小时前”“昨天”或当前日期。

默认页通常是“最有帮助”。不要仅凭按钮存在就认为已切换排序。

## 3. UI Tree 字段

评论字段使用以下键：

- `CommentDetailUsername{index}`
- `CommentDetailStars{index}`
- `CommentDetailStarMessage{index}`
- `CommentDetailText{index}`
- `CommentDetailPostInfo{index}`

同一条评论可能在一屏只显示部分字段。跨相邻屏按索引合并，评论文本保留更长版本。

## 4. 日期定位与采集

解析“几分钟前”“几小时前”“今天”“昨天”“前天”、`MM/DD`、`YYYY/MM/DD` 和 `M月D日`。

- 页面晚于目标月份且相距较远：快速向上惯性滚动。
- 接近目标月上边界：改为普通快速滑动。
- 位于目标月份：使用重叠滑动并逐屏保存 UI Tree。
- 整页早于最早目标月份：保存该边界页后停止。
- 页面早于目标范围但仍需续跑：快速向下定位到断点或目标日期。

## 5. 断点续跑

每屏保存 `screen_####.json`，并更新进度中的可见索引、日期范围和计数。

重启后：

1. 跳过损坏或未写完的 JSON。
2. 从有效 UI Tree 重建历史记录。
3. 转储 `resume_probe.json`。
4. 用发布时间、评分和评论文本前缀匹配历史评论。
5. 计算 `saved_index - current_index`，保存到 `screen_offsets.json`。
6. 远离断点时快速滚动，接近时缩短步长。
7. 无法可靠匹配时停止，避免错误合并。

## 6. 后台运行

Windows 中使用隐藏进程并分离标准输出：

```powershell
Start-Process -FilePath "<python.exe>" `
  -ArgumentList "<collector.py>" `
  -WorkingDirectory "<workspace>" `
  -WindowStyle Hidden `
  -RedirectStandardOutput "<work>\collector.stdout.log" `
  -RedirectStandardError "<work>\collector.stderr.log"
```

监控 `progress.json` 和日志中的 `PROGRESS`/`DONE`，不要用持续截图监控。

## 7. 完整性补采

先运行 CSV 校验，统计日期范围、重复、缺失字段和索引空档。若空档集中在某段：

1. 从当前边界反向进入该段。
2. 使用 40%–50% 小步长产生更多重叠。
3. 只补扫缺口区间。
4. 重建月度输出并再次校验。

虚拟列表可能仍留下少量边缘空档。交付时明确报告，不要把记录数等同于市场展示的总评论数。

## 8. 故障处理

- Hypium 找不到设备：将 HDC 工具目录加入当前进程 `PATH`。
- UI Tree 为空：检查锁屏、前台应用和当前窗口；不要继续盲滑。
- 页面日期方向错误：重新确认“最新”排序。
- 任务中断：先检查后台进程，避免重复启动两个采集器。
- 输出乱码：以 UTF-8 读取 JSON/Markdown，以 `utf-8-sig` 写 CSV。
