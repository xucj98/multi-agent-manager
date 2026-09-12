# task rebind 独立 review 与上线前验收

Review source delivery (source TASK-ID: d5cb66d7-36d9-4bfc-9d01-d56befd32de4):
{
  "task": "d5cb66d7-36d9-4bfc-9d01-d56befd32de4",
  "commits": {
    "multi-agent-manager": "bc8726f3e2f13351c52650f03bc88bd76a68ed25"
  }
}

Source task requirements:

# task rebind：原任务的执行者接续

## 授权与目标
用户明确授权新增 task rebind，并同步 README.md 与 docs/task-management-design.zh-CN.md；README 保持简洁操作手册。实际目标是将原 Manager 下三个旧执行者换成当前 Manager 原生新建的 gpt-5.6-terra/max subagent，保留所有任务历史、workspace、分支和运行 job。你只负责实现/测试/文档，不部署生产、不实际换绑、不合入 main；Manager 安排独立 review 后裁决和上线。

## 开始
阅读 MAM AGENTS.md、README核心原则/任务管理/执行与交付、.local/README.md、docs/development.md、docs/task-management-design.zh-CN.md。Manager 已 git fetch origin main；核验 main 与 origin/main，按开发指南从最新 main 用 mam workspace add d5cb66d7-36d9-4bfc-9d01-d56befd32de4 --repo multi-agent-manager --base main 创建独立树。不要修改生产根代码或 .local/service、tasks、waits。先发 CODEX_THREAD_ID 供绑定。

## 接口与行为要求
建议接口 mam task rebind TASK-ID --agent AGENT-ID --note NOTE；如果需要显式旧 ID 防止操作竞态，可以加 --from-agent，但保持日常用法简洁。实现前向 Manager 用短消息提出最终接口、锁顺序和状态检查，随后可继续实现无争议部分。
- 原任务必须未归档且已有执行者；原 bind 行为不变。新 agent 不可已绑定另一个未归档任务，也不可是当前 Manager；查证 agent 身份/状态，不把未知或无法联系当 idle。重试同一目标应无破坏、无重复交接历史，是否作为幂等 no-op 明确文档和测试。
- 更换前旧执行者必须已结束当前 turn，防止两个 agent 同写 workspace。running/stopped job 本身不能阻止换绑；旧 agent active 或状态无法核实应有明确拒绝和操作提示，不提供静默抢占/停止 job。notLoaded 可通过只读元数据确认是可接续旧线程；必要行为依照现有状态语义。新 agent 可以先作只读准备，但换绑前不接管写操作。
- 原 TASK-ID、task/report 和 publication、workspace、repos路径/分支、job ID/PID/身份/观测/历史、源 review 关系等保持。不复制/移动/重建 worktree，不重启、归档或重复登记进程。记录最小交接审计（旧/新 agent、时间、note、Manager调用者）并在 task status 合理展示。
- 与现有 scheduler 的 service-start/service-cycle 锁及 bindings/task 锁协调，避免 daemon 在检查与修改之间投递给旧执行者；尊重现有锁顺序，避免死锁。旧 executor 的 pending/accepted/uncertain wake 需在下一轮按现有 currentness 失效，当前 job 后续投递新 agent，review 路由和 Manager 待办正确。不清空 service state/历史/队列；不新增平行 scheduler。
- 单项目 Manager 绑定不变，不把 rebind 实现成 Codex parent 元数据改写。旧任务发布记录保留；新 agent 读取原任务/报告并继承原 workspace，文档说明此为交接时例外，不再次创建同名 worktree。

## 验证/交付
有意义的单元/集成测试应覆盖：成功换绑且 workspace/jobs/publications不变、旧active/unknown拒绝、目标重复绑定/Manager/无效拒绝、归档/未绑定任务拒绝、重试幂等、调度旧收件人失效及新执行者 stopped-job投递、与 optional wait 的边界、并发/锁相关行为。可按实际设计调整测试组织，避免仅镜像实现。
运行 .venv/bin/python -B -m unittest discover -s tests -v 全套，通过后提交独立分支，git diff --check/clean，report 写准确commit、行为、命令结果和风险。README 只加操作命令与必要交接步骤/限制；详细协议、锁和状态语义写设计文档，顺手将设计文档仍过时的 >1h 长job阈值与当前 >30min 规范一致，不扩展其他无关文档。
发布 mam task publish d5cb66d7-36d9-4bfc-9d01-d56befd32de4 --file report。保留 worktree 待独立review，无可执行事项正常结束turn，不轮询。

Source report:

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
# 独立 review：task rebind

源任务 d5cb66d7-36d9-4bfc-9d01-d56befd32de4，候选提交 bc8726f3e2f13351c52650f03bc88bd76a68ed25，base 2cb730944dc7574feaff92253ef09644ae06c1da。先阅读源任务的已发布 task/report，再核对实际 diff；不要只复述实现者报告。

## 范围
- 阅读 MAM AGENTS、README、.local/README、docs/development.md、docs/task-management-design.zh-CN.md。
- 用 mam workspace add 492c83a2-d96a-452a-84ba-c3365cf42cea --repo multi-agent-manager --base bc8726f3e2f13351c52650f03bc88bd76a68ed25 创建独立 review worktree；不改生产代码、服务状态或绑定，不部署。
- 重点核验 Manager 身份，旧/新 idle/notLoaded 与 unknown 拒绝，同目标幂等，归档/重复绑定拒绝，task/report/publications/workspaces/branches/jobs/identity/observation/review 的保留。
- 核验全局锁序：service、bindings、task 与 wait 锁之间所有相关路径，包括 scheduler/bind/archive/optional wait 注册和取消，验证无反向锁依赖或可复现竞态。报告所述锁序与设计一致性也需核对。
- 验证旧 pending/accepted/uncertain 收件人 currentness 失效与新执行者路由、Manager/review 路由，不能清 service 队列/历史或漏掉 stopped job。
- README 保持简洁；设计准确解释交接语义与边界。查看测试是否掩盖真实 AppServer 行为或仅镜像实现。
- 运行 .venv/bin/python -B -m unittest discover -s tests -v 全套；仅为实际风险补必要复现实验，可用隔离临时目录/假的 transport，不触碰生产 AppServer turn 或本项目状态。

## 交付
先返回 CODEX_THREAD_ID 绑定。发布 report，明确 PASS/FAIL、所核验 SHA、真实命令结果，问题须提供文件行/触发条件/影响/建议，区分阻断与非阻断。无阻断即可给出可上线意见，但最终由 Manager 裁决。不合并、不重写候选实现；有问题通知 Manager。正常结束 turn，由 MAM 唤醒，不轮询。
