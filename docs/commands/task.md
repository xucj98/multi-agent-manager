# mam task

`mam task` 提供任务创建、绑定执行者、发布、查看、归档的功能。

## 创建与交接

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task create --title TITLE` | Manager | 生成 TASK-ID，创建 task.md、report.md 草稿和空 workspace；返回任务及文件、目录路径，状态为“进行中”。 |
| `mam task create --title TITLE --review TARGET-TASK-ID` | Manager | 创建 review 任务，在草稿中引用源任务当前已发布的要求、简报和已登记的交付代码 commit。 |
| `mam task bind TASK-ID --agent AGENT-ID` | Manager、执行者 | 将已启动的执行者绑定到任务；执行者可用自己的 CODEX_THREAD_ID 自绑定。一个未归档任务对应一个执行者，一个执行者同时绑定一个任务。 |
| `mam task rebind TASK-ID --agent AGENT-ID --note NOTE` | Manager | 将已绑定的任务交给新执行者，保留 TASK-ID、workspace、worktree、job 和发布记录，并记录交接双方、时间和理由。 |

`rebind` 必须由当前实例已登记的 Manager 调用。交接前让旧、新执行者结束 turn 并解除 wait；新执行者不能是 Manager，也不能绑定其他未归档任务。无法确认双方已空闲时，命令会拒绝交接。新执行者接续原 workspace，无需再次创建。

创建 worktree 和环境见 [mam workspace](workspace.md)。

## 编辑、发布与查看

`FILE` 为 `task` 或 `report`。Manager 编辑 task.md，执行者编辑 report.md；普通编辑工具保存的是草稿，通过 publish 才成为已发布内容。

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task show TASK-ID [--file FILE] [--json]` | 所有人 | 返回 MAM_BRANCH 上当前已发布的内容；默认读取 task.md，`--file report` 读取 report.md；`--json` 同时返回文件和发布信息。 |
| `mam task publish TASK-ID --file FILE` | 文件负责人 | 单独提交指定草稿到 MAM_BRANCH，返回发布 commit；发布 report 时记录各已就绪 worktree 的 HEAD 为交付 commit，任务变为“待验收”。 |
| `mam task list [--archived\|--all]` | 所有人 | 默认列出未归档任务；`--archived` 仅列已归档任务，`--all` 列出全部。表格包含标题、任务状态、TASK-ID、agent 和 agent 状态。 |
| `mam task status TASK-ID` | 所有人 | 返回精简 JSON，包含任务、workspace、仓库交付、发布记录和已保存的 job 观测，并提示未发布草稿；不会刷新进程状态。 |

发布前，MAM_ROOT 必须处于 MAM_BRANCH。publish 只提交指定文件，保留其他文件的草稿和暂存内容；附件不会随 report 自动提交。已发布内容的历史由 Git 保存。

执行者和 reviewer 始终以 MAM_BRANCH 上最新发布的 task.md 为准。Manager 追加要求时先更新并发布 task.md，再通知执行者读取。report 无需绑定任务要求的版本；reviewer 根据最新要求、report 和交付代码验收，不符合要求则报告返工。

## 归档

| 接口 | 使用者 | 具体操作 |
| --- | --- | --- |
| `mam task archive TASK-ID --note NOTE` | Manager | 在所有 job 已归档后，记录结束结论，移除已登记的 worktree、独立环境、任务分支和 workspace；保留任务、报告、附件和历史登记，状态变为“已归档”。 |

归档前由 Manager 确认交付代码已合入主分支或明确可以舍弃，必要报告与附件已提交留存。worktree 中未提交的改动、未知文件，以及 workspace 中未登记的内容会阻止归档；当前 `tmp/` 也需事先清理。共享软链接的目标不会被删除。

归档返回清理结果；若清理未完成，任务仍未归档，可按错误提示处理后重试。取消任务也用 archive，并在 note 中说明原因。

## 待开发

### 调用者与任务定位

`TARGET` 可以是 TASK-ID 或原生协作路径，如 `/root/worker`。已绑定执行者省略 TARGET 时，MAM 从 CODEX_THREAD_ID 找到其当前任务；Manager 显式指定 TARGET。尚未绑定执行者的任务和历史归档仍用 TASK-ID。

MAM 自动查询并登记执行者的线程 ID、协作路径及所属协作树。协作路径仅在所属树中解释，不能混用不同 Manager 的同名路径；无法唯一定位时明确报错。TASK-ID 及其 workspace、分支保持稳定，日常操作无需手填执行者 UUID。

| 拟议接口 | 操作 |
| --- | --- |
| `mam task create --title TITLE [--review TARGET]` | 创建任务；review 的源任务也可通过协作路径指定。 |
| `mam task show [TARGET] [--file FILE] [--json]` | 查看已发布的要求或报告。 |
| `mam task status [TARGET]` | 查看任务、交付和已保存的 job 观测。 |
| `mam task publish [TARGET] --file FILE` | 发布指定草稿。 |
| `mam task archive TARGET --note NOTE` | Manager 确认留存或舍弃后归档任务。 |

list 和 status 优先展示执行者的协作路径，保留 TASK-ID 供定位任务和历史记录。

### 执行者开始与接续

用 `mam task start [TASK-ID]` 统一替代 bind/rebind。首次登记或新执行者接手时指定 TASK-ID；已绑定执行者返工时可省略。命令自动识别调用者，返回任务、执行者协作路径、状态和 workspace 路径；不创建 Codex agent，不接收 model、reasoning_effort 或 fork_turns。

| 场景 | 操作结果 |
| --- | --- |
| 任务尚未绑定 | 绑定调用者，状态为 working |
| 当前执行者返工 | 保留绑定和成果，将 pending 改为 working |
| 新执行者接手 | 更新执行者绑定与协作路径并记录交接，保留任务、workspace、worktree、环境、分支、job 和发布记录，状态为 working |
| 当前执行者重复调用，已为 working | 返回当前登记，不重复创建或清理资源 |

Manager 用原生工具创建或通知 subagent；执行者在首次执行、返工或接手时调用 start，再用 `mam task show` 读取最新已发布要求。换人由 Manager 安排，旧执行者须先停止接续；尚在执行或等待中的旧执行者不能被覆盖。保留一个执行者同时只绑定一个未归档任务的约束，已归档任务不能 start。

发布 report 后回到 pending。要求变化仍通过更新 task.md 并发布、通知执行者来处理；不建立 task/report 版本绑定，普通问答和 agent 活跃状态不改变任务状态。新接口实现前，仍使用上文的 bind/rebind。

### 附件与归档

附件提交与归档作为同一项工作，先提供提交接口和 workspace 内的 [`.task` 入口](workspace.md#任务文件入口)，再完善归档检查与清理。

- 附件：执行者通过 `.task/files/` 整理需要保留的文件，再用提交接口发布并取得提交记录；共享管理仓库的 Git 操作由 MAM 完成。接口沿用当前任务自动识别规则，具体参数待定。
- 归档：检查报告、附件和交付代码，确认未发布草稿的处理方式，再清理 tmp、worktree、环境、任务分支及 workspace 中的 `.task` 链接；中央 `.tasks/TASK-ID` 及其已发布记录保留，取消空任务仍可归档。
