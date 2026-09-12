# task rebind 实现结果

- 新增 `mam task rebind TASK-ID --agent AGENT-ID --note NOTE`。它仅允许已记录的 Manager 调用，在旧/新 agent 均为 `idle` 或 `notLoaded`、没有可验证的 active optional wait 时原子交接任务。
- 原 `TASK-ID`、workspace、worktree、分支、job、发布记录与 review 关系保持；只更新当前 agent，并记录 `handoffs` 审计。相同目标重试返回 `unchanged`，不会追加审计。
- 交接与 scheduler 的 `service-start → service-cycle → bindings → task → wait-*` 锁序协调；旧收件人的 pending、accepted、uncertain stopped-job 待办下一轮失效，后续投递新执行者。
- README 增加简短命令和交接顺序；详细设计说明身份/状态门禁、wait 边界、锁序、幂等与审计，并将设计文档的长 job 阈值同步为 30 分钟。

交付代码：

- workspace: `/mnt/public/xcj/Projects/workspace/d5cb66d7-36d9-4bfc-9d01-d56befd32de4/multi-agent-manager`
- branch: `task/d5cb66d7-36d9-4bfc-9d01-d56befd32de4`
- commit: `bc8726f3e2f13351c52650f03bc88bd76a68ed25` (`feat: add task executor rebind`)

验证：

- `.venv/bin/python -B -m unittest discover -s tests -v` — 206 tests passed。
- `git diff --check` 与提交后差异检查通过。

未执行生产部署或实际 task rebind。真实交接仍需 Manager 先让旧执行者和新执行者结束当前 turn，再由独立 review 验收此提交。

## Manager 授权后的本机集成与安装

集成：

- `git fetch origin main` 后，`origin/main` 仍为授权基线 `2cb730944dc7574feaff92253ef09644ae06c1da`；候选 `bc8726f3e2f13351c52650f03bc88bd76a68ed25` 的唯一父提交也是该基线，且 `git diff --check` 通过。
- 在短期独立 `main` worktree 中以 fast-forward 将本地 `main` 更新为 `bc8726f3e2f13351c52650f03bc88bd76a68ed25`，再以普通无冲突 merge 带入 `project/state-vla`，集成 merge commit 为 `885c7a780ab88a5cded86fe6730f917b607e545f`。
- 安装后验收快照中 `main=bc8726f3e2f13351c52650f03bc88bd76a68ed25`，`project/state-vla=954bd1dbfa8599aff7a5b6a7d3b21d1c5c1b9d9b`；后者在安装期间被其他正常 Manager 发布推进，已核对候选和集成 merge 均为其祖先。未推送远端。

安装回执与验证：

- 从集成后的短期 `main` worktree 执行 `bash scripts/install.sh`，于 `2026-09-12T17:22:15Z` 以 exit status 0 完成。安装器源码全套测试为 `Ran 206 tests in 63.121s`，结果 `OK`。
- 当前 App Server 的 JSON trace 环境在安装前已只读确认就绪；安装输出确认 `The current verified listener already has JSON trace logging.`，未请求确认、未向 App Server/proxy 发送 `TERM`，也未替换它。
- 安装器的 live wait trace compatibility、无模型 API compatibility 和 isolated real delivery acceptance 均为 `PASS`；真实 delivery fixture 明确通过，且固定使用 `6 model turns`。
- 安装后的 `mam task rebind --help` 显示 `usage: mam task rebind [-h] --agent AGENT-ID --note NOTE TASK-ID`。launcher 为 `/root/.local/share/pipx/venvs/multi-agent-manager/bin/mam`；脱离源码目录检查时加载的安装代码为 `/root/.local/share/pipx/venvs/multi-agent-manager/lib/python3.12/site-packages/multi_agent_manager/` 下的 `cli.py` 与 `wake_runtime.py`。
- 安装器替换本项目 daemon 后，`mam service status` 为 `healthy`，Manager 仍为 `01a09657-e0f3-7352-b726-aba5bbd5d498`，pending queue 仍为 0。持久化计数没有清空：安装前 accepted/queued 为 30/80，安装后为 31/81；`.local/service` 未清理。

用户工作区与清理：

- 合并前后，`docs/wash-cup-shared-memory-token-usage-audit.zh-CN.md` 的 SHA-256 均为 `cd1c95f9d0b66c0c66b7232210d6d359a0eca2050bda42acdffef5548276e038`；其 index 仍为 stage 0 的 blob `19f394ecd26de6c9aaa56ecf3ff3a686f59ef4cc`，未进入暂存区。
- 初始以及合并/安装后的校验中，两个原有未跟踪文件 `.tasks/2f6ec567-e628-46ba-94ff-ac97daa009cb/report.md` 与 `.tasks/838bfe79-ab08-4c58-9843-f8e84423f0e1/report.md` 都为空（SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`）。首次发布本报告后的最终核对发现前者被并发的用户工作更新为 SHA-256 `34a691ce943d55d22f632226299b19def7a590967ace3bf0e9221b528b5a3e3d`；它仍未跟踪、未暂存，且不是本次集成或安装写入。后者仍为空。没有 stash、reset、force 或全树暂存。
- 安装器的 `/tmp/mam-install.rpXWFG` fixture 根已由其 trap 删除；短期 installer/main worktree 与本次安装日志已删除。原实现 worktree `/mnt/public/xcj/Projects/workspace/d5cb66d7-36d9-4bfc-9d01-d56befd32de4/multi-agent-manager` 保留且仍在候选 commit。

没有执行任何实际 `mam task rebind`：仅调用了 `--help`。本任务 status 仍保持 executor `01a09671-2851-7763-bb23-a1201043c3cc`，且未出现 handoff 审计记录；实际换绑继续由 Manager 决定并执行。
