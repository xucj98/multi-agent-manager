# `.local` 历史材料清理审计

审计目标是生产目录 `/mnt/public/xcj/Projects/multi-agent-manager/.local`；独立审计 worktree 为 `/mnt/public/xcj/Projects/workspace/2c4d4a5b-61a7-4f39-9b9b-c0dad5d5479a/multi-agent-manager`（`task/2c4d4a5b-61a7-4f39-9b9b-c0dad5d5479a`）。未修改 MAM 代码、并行 rebind 实现、task/job/workspace 登记或用户 dirty 文档。

## 已清理

- 删除 78 个已核实的历史文件，共 960,288 bytes（约 0.92 MiB）：已完成交接的 `MANAGER_HANDOFF.md`、`MANAGER_CURRENT.md` 与 `handoff-snapshot-20260912/`；仅用于测试线程 `01a090a5-928a-7022-a9d7-f4d768fbd896` 的 `hook-probe/`；已归档 native-wait 辅助/失败 smoke 文件、零字节 stderr、8 个安装或测试尝试日志；以及 UI probe 的旧 bashrc 提示、旧入口记录和 self-test 输出。
- `hook-probe` 的作用是只为上述测试线程观测 `UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`Stop` 和 `Interrupt` 的事件元数据，不记录提示正文或工具参数，也不改变 wait/服务行为。清理前确认没有相关 watcher/recorder 进程，项目 `.codex/hooks.json` 已不存在。
- 从 `/root/.codex/config.toml` 删除了 5 条精确匹配、均指向已不存在项目 hook 文件的 probe trust-state；其余配置未触及。修改后 TOML 解析成功，项目 probe hook state 为 0。
- 交接删除前确认当前 Manager 已登记在 `.local/service/manager.json`，而研究约束已留在已发布 task/report 以及 RMBench 实验台账/论文项目中，未在 `.local` 重造交接副本。

## 入口恢复与暂留依赖

- `/usr/local/bin/codex` 原为本探针的 root-owned 324-byte wrapper。替换前重新核对其精确内容、身份、权限和 npm 目标；目标 `/usr/local/lib/node_modules/@openai/codex/bin/codex.js` 存在，未见 wrapper 后 npm 升级覆盖。已原子恢复记录中的 symlink `../lib/node_modules/@openai/codex/bin/codex.js`。
- `ui-probe` 的作用是 Windows App 的 `app-server proxy` 元数据采集器：透明转发字节，只追加 initialize、thread/turn/collab 等元数据。入口恢复后 `codex --version` 返回 `codex-cli 0.154.0`。
- 活跃 Windows proxy 仍依赖 `.local/ui-probe/proxy_tap.py` 和 `.local/ui-probe/proxy-metadata.jsonl`，后者会随用户流量追加；两者暂留以避免影响当前连接。源码没有既有的无中断关闭日志 sink 接口，因此未改运行中代理，也未 kill/restart proxy 或 App Server。连接自然退出后可删除这两个剩余 probe 文件。

## 有意保留

- 核心 `.local/README.md`、`create_worktree.sh`、`tasks/`、`service/`、`waits/` 及锁：均为当前 MAM 状态或运行依赖。
- `native-wait-coordinated-900-1789145948-{meta.json,output.txt,result.json}`：已归档 task `21a41c32-660a-4cc5-9cf5-a7c656bcbeb5` 的发布报告明确引用的最小真实成功 smoke 证据；其余辅助记录已删除。
- `.local/history-migration-20260911/`：包含可验证的完整旧 Git history bundle 和本地记录 tar，属于迁移前唯一历史备份；bundle 验证通过，tar 可读。
- `.local/archives/3b1cdd78-c7b9-4174-a132-497b485fcfaf/legacy-source-patches.tar.gz` 及索引：任务 `3b1cdd78-c7b9-4174-a132-497b485fcfaf` 明确要求保留的旧源码 patch/未跟踪源码归档；tar 可读，SHA-256 仍为 `c99c21bd7c38361212b0975e1705b6f2efeb09a45f40d872d5c1416ca10466e4`。

## 验证

- `mam service status`：`healthy: true`、当前 Manager 为 `01a09657-e0f3-7352-b726-aba5bbd5d498`。
- `/usr/local/bin/codex` 是已恢复的 symlink，`codex --version` 成功；现有 proxy/App Server 未重启。
- 用户的 `docs/wash-cup-shared-memory-token-usage-audit.zh-CN.md` 仍保持原有 dirty 状态；未做 task 归档。
