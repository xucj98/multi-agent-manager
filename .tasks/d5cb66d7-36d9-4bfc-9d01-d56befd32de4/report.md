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
