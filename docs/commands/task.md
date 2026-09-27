# mam task

`mam task` 创建任务、登记执行者、发布要求和成果、查询及归档。任务可用 TASK-ID 或 AGENT-PATH 定位；AGENT-PATH 是当前原生协作树内的完整执行者路径，如 `/root/worker`。Manager 显式指定任务；已绑定执行者可按下表省略任务参数。首次发布、未绑定或已归档任务使用 TASK-ID。路径身份无法确认或不唯一时返回错误，不跨树猜测。

## 创建与开始

| 接口 | 操作 |
| --- | --- |
| `mam task create --title TITLE [--review TASK-ID\|AGENT-PATH]` | 创建 TASK-ID、task.md/report.md 草稿、files/ 和 workspace，状态为 working；review 引用源任务当前已发布的要求、报告与代码交付记录。 |
| `mam task start [TASK-ID]` | 执行者从 CODEX_THREAD_ID 登记原生路径与树根，进入 working；首次登记和换人时指定 TASK-ID，已绑定执行者返工可省略。重复调用幂等。 |
| `mam task list [--archived\|--all]` | 默认列出未归档任务，选项查看归档或全部；表格包含任务、状态、TASK-ID、执行者路径或旧记录的 AGENT-ID、线程状态，空列表仍有表头。 |

Manager 用原生工具创建或通知 subagent。换人前让旧执行者结束 turn 和可选 wait；旧执行者活跃、等待中或状态无法确认时，start 拒绝交接。新执行者正在调用 start 属于正常状态。接手保留 TASK-ID、workspace、worktree、环境、分支、job 和发布记录，并记录交接。一个执行者只绑定一个未归档任务。原有 bind 仅允许当前执行者自绑定并走 start 校验；rebind 仍可供 Manager 兼容调用，但必须确认双方空闲、身份及 wait 状态。start 不创建 Codex agent，不接受 model、effort 或 fork 参数。

## 编辑、发布与查看

| 接口 | 操作 |
| --- | --- |
| `mam task show [TASK-ID\|AGENT-PATH] [--file task\|report] [--json]` | 读取 MAM_BRANCH 当前最新已发布文档，默认 task；不读取草稿，--json 同时返回正文和发布信息。 |
| `mam task publish TASK-ID\|AGENT-PATH` | Manager 发布任务要求，必须显式指定任务，返回发布 commit。 |
| `mam task report [TASK-ID\|AGENT-PATH]` | 执行者一起提交报告和 `.task/files/` 附件，记录交付代码，任务进入 pending；返回发布 commit。 |
| `mam task status [TASK-ID\|AGENT-PATH]` | 返回任务、执行者路径与树根、仓库交付、发布记录、草稿提示和保存的 job 观测；不探测 job。 |

Manager 编辑 task.md；执行者经 workspace 的 `.task/report.md` 和 `.task/files/` 编辑简报、附件。report 草稿用于记录当前进展，更新草稿不改变状态；完成交付后再发布。publish 只提交 task.md；report 将报告与附件放入同一个提交，校验失败时不发布。

附件先整理到 `.task/files/`，report 同步其中的新增、修改、删除和可执行位变化。仅附件变化也会发布；报告和附件均无变化时不创建新 commit。附件仅接受普通文件（包括可执行文件），不接受符号链接。发布保留无关暂存内容和其他草稿。

`report` 记录各就绪 worktree HEAD 为交付 commit，任务进入 pending；返工后即使报告文字不变，重新发布也会更新交付 HEAD 并进入 pending。`publish` 发布 task.md、线程活跃或普通问答不会自动改变任务状态。执行者和 reviewer 始终以最新已发布 task.md 为准；report 不绑定要求版本。

## 附件与归档

| 接口 | 操作 |
| --- | --- |
| `mam task archive TASK-ID\|AGENT-PATH --note NOTE [--discard-drafts] [--discard-code]` | Manager 显式指定任务，完整预检后清理资源，保留中央任务记录和发布历史。 |

归档要求所有 job 已归档、仓库 worktree 无未提交或未知内容、任务/报告/附件无未发布草稿，且交付代码已包含在各源仓库的主分支中（优先检查 main/master，否则检查主 checkout 当前分支）。仅在 `--note` 说明舍弃理由时，才使用 `--discard-drafts` 忽略草稿或 `--discard-code` 舍弃未合入提交。报告中的 commit hash 本身不是 Git 对象的永久留存。取消无交付的空任务可直接归档。

预检通过后，MAM 清理本任务 tmp、worktree、独立环境、分支、`.task` 链接和 workspace；不跟随共享链接，也不删除中央 `.tasks/TASK-ID` 或 Manager 的 `workspace/tmp`。清理中途失败会保留进度；重试时重新检查仍存在的草稿和交付分支，新增内容需要重新发布或在本次命令中明确舍弃。归档任务仍可用 TASK-ID 查询历史记录。
