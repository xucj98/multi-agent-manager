# `mam wait` Manager 长线程订阅超时修复

## 交付

- Workspace：`/mnt/public/xcj/Projects/workspace/8ba0dfd2-708f-441f-98fc-c8fe9af6e661/multi-agent-manager`
- Branch：`task/8ba0dfd2-708f-441f-98fc-c8fe9af6e661`
- Commit：`c656430 fix: bound wait thread resume history`

`AppServerEventStream.resume()` 现以 `thread/resume` 的 `excludeTurns: true` 建立原有订阅，只有 thread 为 active 时才以 `thread/turns/list` 读取最新一条、`itemsView: notLoaded` 的 turn，用于保留精确的 active turn 映射。初始化声明 `experimentalApi`，这是该有界分页接口所需的 capability。分页期间 turn 恰好完成时，代码仅在该窄窗口额外进行一次 metadata-only `thread/read`，以保留事件队列并从当前状态开始等待。

没有传递 model、sandbox、cwd、personality 或其他线程配置覆盖；无参 wait、自动责任分配、一小时上限、即时 pending 判断和消息精确匹配保持不变。

## 根因与实测

旧实现让 `thread/resume` 对长 Manager thread 直接水合完整 `thread.turns` 历史。对任务中指定的真实 Manager thread 的只读订阅在 `3.006s` 后稳定复现：`App Server request thread/resume timed out`。因此根因是完整历史水合无法在现有 3 秒 App Server 请求窗口内完成，不是 wait 注册或 Manager 身份判定。

改后对同一 thread 的只读订阅成功：总 `0.039s`，返回 `3,138` bytes，仅一条 `inProgress` turn；未读取或输出任何消息正文。未重启生产 App Server，未向 Manager thread 发送消息，未创建模型 turn，也未以 Manager 身份登记 wait。临时 schema 探针目录已移入系统废纸篓。

以本执行者绑定的 `CODEX_THREAD_ID=01a0919c-cd88-7893-a2b1-18afdffa6a0f` 运行 worktree 的无参 `mam wait`，在约 `1.6s` 返回 `empty`；随后 `mam wait list` 没有该执行者的新记录。

## 验证

- `.venv/bin/python -B -m unittest discover -s tests -v`：`111` tests passed，`27.835s`。
- 新增定向覆盖：metadata-only idle resume、活动 thread 的有界分页、超过旧 4 MiB 的兼容响应、订阅前通知保留、分页期间完成后的 metadata 复核。
- `git diff --check` 通过。

## 局限

此任务只修改并验证隔离 worktree；根目录的 pipx 安装和生产服务未改动。Manager 合并/安装该 commit 后，仍应自行在其真实长对话中运行 `mam wait` 做最终验收。
