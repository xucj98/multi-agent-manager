# 最终窄复核：native journal 与安装器恢复（未通过）

审查 workspace：/mnt/public/xcj/Projects/workspace/8d648d66-b920-4a00-9472-cb7651412028/multi-agent-manager。

审查分支 HEAD 为 `918e678`，已合并当前 `main@549ebe6`（任务所列 runtime `86bc968` 的集成提交为 `36df252`，installer `fe108cc` 的集成提交为 `549ebe6`）。本轮只复核先前两个 P1、其文档和新增测试；未修改实现、未重启生产 App Server，也未重复真实 smoke。

## 结论

安装器 P1 已修复，但 native P1 仍有一个同一初始化交接中的静默漏消息路径，因此当前不能通过。

### [P1] journal 在 bounded scan 与 open 之间替换时仍会静默跳过本次输入

- 位置：`multi_agent_manager/wait_runtime.py:342-390`。
- `36df252` 正确修复了普通 discovery window：`_lookup_start_offset()` 找到本次 boundary 之前的记录，随后从该 offset 读取。新回归和独立 `Path.glob()` 注入均确认在候选查找期间写入的 current `user.text` 会被返回。
- 但 scan 关闭旧 descriptor 后，`_open()` 会无条件打开 path 的当前 inode 并执行旧 offset；两者之间不保存或核对 scanned inode。若 journal 在此窗口替换为同 header 的新文件、且新文件大小不少于旧 offset，`_refresh_handle()` 只看到新 descriptor 的 inode 和足够的 size，不会报 rotation/truncate，于是从 current native input 之后开始读。
- 最终代码复现：先让旧 journal 的 offset 落在一个历史行末，在 patched `_open()` 前原子替换为含 current-turn `user.text` 的同 session journal，并在后面补足数据使新文件不小于旧 offset。结果为 `current-input-silently-skipped=1`，`poll()==[]`，没有错误。该输入发生在 invocation 之后，不是历史 replay。
- 影响：已知会 rotation 的 journal 在很窄的 setup 时序仍可让 native Manager 输入静默等到其它事件或一小时超时，违反“覆盖 invocation 或明确错误”的要求。最小修复是把 scan 的 `st_dev/st_ino` 带到 `_open()` 并在 seek 前核对（不匹配则明确错误），或保留同一 descriptor 从 scan 到 watcher 建立；补这条 replacement-window 回归。

## 已通过的先前安装器 P1

- `scripts/install.sh:1288-1344` 在 TERM 前运行完整 launch-plan preflight、创建私有 recovery artifact 并 arm exit/HUP/INT/TERM guard；TERM 后的 departure/launch/verification 失败会非零并打印单一 `Recovery command: bash …/recover-app-server.sh`。
- artifact 目录和 recovery script 为 mode `700`，captured plan 为 `600`；新增测试验证失败/信号不泄露 plan environment、释放 lock，并保留恢复命令。独立隔离验证了该命令可从有效 captured plan 启动 wrapper（`recovery-command-returned=0`、`protected-plan-mode=600`、`recovery-launch-started=1`）。
- `docs/install.md:34` 清楚说明非零、单独终端执行和恢复仍可能因 wrapper 不可执行而失败，符合 Manager 已接受的精确人工恢复路径；不要求自动 rollback。

## 验证

- `test_wait_runtime.py`：36 passed；`test_wait_compat.py`：32 passed。
- `bash -n scripts/install.sh`、`git diff --check 87f02d3..HEAD`：通过。
- 早前已记录的真实 native `send_input -> reason=message` 和 102-test full suite 未按本次窄复核要求重复；它们不覆盖上述 replacement-window 路径。
- 所有额外复现和 recovery 测试在临时目录完成并清理。
