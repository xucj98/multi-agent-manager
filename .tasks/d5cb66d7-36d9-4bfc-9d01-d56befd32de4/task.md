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

## Manager裁决：独立review通过，授权集成与安装
Manager已阅读review492c83a2（report77dce45aa36305866269012777f8ba87165b6590）、独立核对候选diff、wait注册/取消及Manager锁路径、scheduler currentness和测试内容。接受精确候选bc8726f3e2f13351c52650f03bc88bd76a68ed25（base2cb730944dc7574feaff92253ef09644ae06c1da）上线；review的206全套和7定向测试通过，先前疑似锁ABBA因active_wait_records每次仅持有单锁已排除。

授权你执行具体集成/安装，实际task rebind仍由Manager执行，不冒用Manager CODEX_THREAD_ID。先读docs/install.md。核对/fetch最新origin/main，候选基线若无变化，可安全更新本地main包含候选，再将main合入project/state-vla管理分支；禁止force/reset覆盖用户改动。可用短期独立main checkout完成常规ff merge；不要让.tasks进main。不推送远端（本阶段仅本机集成安装）。

生产根 /mnt/public/xcj/Projects/multi-agent-manager 有用户dirty docs/wash-cup-shared-memory-token-usage-audit.zh-CN.md，以及未跟踪.task报告；逐路径保留，不stash、不git add全树。记录这些文件前后hash/index，合并只含已review候选。不要改变正在进行的实验runtime。

按安装器bash scripts/install.sh正常运行，从包含验收候选的checkout安装；安装器要求的source tests、真实兼容/投递fixture验收不可跳过（6个预定terra/max模型turn是既定验收）。先确认当前AppServer的trace环境已满足，不能重启或替换Windows正在使用的AppServer/proxy；若安装器要求AppServer TERM则停止该步并报告具体原因，保持现有连接。允许安装器按文档替换本项目MAM daemon，保留原Manager绑定、队列/历史，不清.local/service，不伪造healthy。

验收必须给出：main/项目分支SHA、已安装rebind --help和包代码路径、安装receipt及兼容/live delivery结果、service healthy和原Manager UUID、user dirty文件hash保持、工作树及installer临时产物清理情况。报告新增上线结果并publish；如失败给准确阶段/错误，不盲重装多次。完成后正常结束turn用MAM唤醒。原实现worktree先保留待最终归档。
