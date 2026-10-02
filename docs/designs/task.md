# mam task

`mam task` 创建任务、登记执行者、发布要求和成果、查询及归档。任务可用 TASK-ID 或 AGENT-PATH 定位；AGENT-PATH 是完整执行者路径，如 `/root/worker`。设置 CODEX_THREAD_ID 时限定调用者的原生协作树；普通终端未设置时，显式路径按本项目登记记录唯一匹配。Manager 显式指定任务；已绑定执行者可按下表省略任务参数。首次发布、未绑定或已归档任务使用 TASK-ID。路径身份无法确认或不唯一时返回错误，可改用 TASK-ID。

## 任务状态

新任务为 `pending`；未归档任务根据执行者和 job 的当前运行情况自动判断 `working`、`pending`。

| 状态 | 条件 |
| --- | --- |
| `working` | 执行者正在运行，或有未归档的 job |
| `pending` | 执行者空闲或尚未绑定，没有未归档的 job，且未设置 `blocked` |
| `blocked` | Manager 暂缓处理，停止自动提醒 |
| `archived` | Manager 完成收尾并调用 `task archive` |

### 任务阻塞

```text
mam task block TASK-ID|AGENT-PATH --note NOTE
```

`task block` 仅由 Manager 判断和调用，状态为 `pending` 才可设置。`--note` 必填，`task status` 展示原因。执行者恢复运行或有未归档的 job 时，`blocked` 自动转为 `working`。

## 创建与开始

| 接口 | 操作 |
| --- | --- |
| `mam task create --title TITLE [--review TASK-ID\|AGENT-PATH]` | 创建 TASK-ID、task.md/report.md 草稿、files/ 和 workspace；review 引用源任务当前已发布的要求、报告与代码交付记录。 |
| `mam task start [TASK-ID]` | 执行者从 CODEX_THREAD_ID 登记原生路径与树根；首次登记和换人时指定 TASK-ID，后续继续工作无需重复调用。重复调用幂等。 |
| `mam task list [--archived\|--all]` | 默认列出未归档任务，选项查看归档或全部；表格包含任务、状态、TASK-ID、执行者路径或旧记录的 AGENT-ID、线程状态，空列表仍有表头。 |

Manager 用原生工具创建或通知 subagent。换人前让旧执行者结束 turn；旧执行者活跃或状态无法确认时，start 拒绝交接。新执行者正在调用 start 属于正常状态。接手保留 TASK-ID、workspace、worktree、环境、分支、job 和发布记录，并记录交接。一个执行者只绑定一个未归档任务。原有 bind 仅允许当前执行者自绑定并走 start 校验。start 不创建 Codex agent，不接受 model、effort 或 fork 参数。

## 编辑、发布与查看

| 接口 | 操作 |
| --- | --- |
| `mam task show [TASK-ID\|AGENT-PATH] [--file task\|report] [--json]` | 读取 MAM_BRANCH 当前最新已发布文档，默认 task；不读取草稿，--json 同时返回正文和发布信息。 |
| `mam task publish TASK-ID\|AGENT-PATH` | Manager 发布任务要求，必须显式指定任务，返回发布 commit。 |
| `mam task report [TASK-ID\|AGENT-PATH]` | 一起提交报告和 `.task/files/` 附件，返回发布 commit |
| `mam task status [TASK-ID\|AGENT-PATH]` | 返回任务、执行者、仓库交付、发布记录、草稿提示、阻塞原因、[提醒次数](wakeup.md#提醒次数)和保存的 job 观测；不探测 job。 |

Manager 编辑 task.md；执行者经 workspace 的 `.task/report.md` 和 `.task/files/` 编辑简报、附件。report 草稿用于记录当前进展，完成交付后再发布。publish 只提交 task.md；report 将报告与附件放入同一个提交，校验失败时不发布。

`task report` 要求任务处于 `working` 或 `pending`，且所属 job 已全部归档。

附件先整理到 `.task/files/`，report 同步其中的新增、修改、删除和可执行位变化。仅附件变化也会发布；报告和附件均无变化时不创建新 commit。附件仅接受普通文件（包括可执行文件），不接受符号链接。发布保留无关暂存内容和其他草稿。

`report` 附带记录可读取的 worktree HEAD，供 review 参考。执行者和 reviewer 始终以最新已发布 task.md 为准。

## 附件与归档

| 接口 | 操作 |
| --- | --- |
| `mam task archive TASK-ID\|AGENT-PATH --note NOTE [--force]` | Manager 显式指定任务，检查通过后清理资源，保留中央任务记录和发布历史。 |

归档只要求：

1. 该任务所有 job 已归档。
2. `.tasks/TASK-ID/` 下 Git 干净：没有暂存、未暂存或未跟踪的变更；按 Git 规则忽略的文件不影响检查。检查覆盖整个任务目录，不影响其他任务的草稿。
3. 项目[归档前 hook](../install.md#项目-hooks) 通过；没有配置则跳过。

通过后，MAM 清理登记的 worktree、任务分支和整个 workspace，包括独立环境、tmp 和 ignored 文件。使用者负责提前保存成果；软链接只删除链接本身，中央 `.tasks/TASK-ID` 和 Manager 的 `workspace/tmp` 保留。

默认先由执行者整理干净 worktree，归档使用 `git worktree remove` 和 `git branch -d`。显式 `--force` 时改用 `git worktree remove --force` 和 `git branch -D`，允许清理 worktree 中未提交、未跟踪内容和未合并的任务分支，但不跳过三项归档条件。项目需要的交付检查由 hook 实现。

Git 或文件删除失败会保留清理进度，按错误处理后重试；此前已清理的资源不会恢复。重试重新检查归档条件，已归档任务重复调用直接返回。归档任务仍可用 TASK-ID 查询历史记录。
