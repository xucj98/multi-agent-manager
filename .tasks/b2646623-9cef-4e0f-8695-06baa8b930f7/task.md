# MAM列表与查询体验：精简输出、正文显示、按需探测

## 目标与范围

用户已同意下述四项体验改进。你负责实现，Manager验收后另派空白review并安装。先读MAM AGENTS/README的开发验证；通过mam workspace add为multi-agent-manager创建独立worktree，base为04eee7a5cf20b4011406dbddc99bbbb148d7e1b8。只在你自己的worktree修改实现/必要测试/少量README，不修改共享MAM代码、不改正在运行的任务记录、不安装到系统、不占GPU、不派agent。

## 接口行为

1. `mam task list`默认每个任务一行，只含标题、task状态、完整UUID、绑定agent ID、agent状态，按这个顺序。保留默认排除归档及--archived/--all语义；不显示workspace/repos/jobs/report/archive细节。标题中的换行等不能打散成多行；ID不截断，不新增缩写ID机制。agent状态复用现有只读probe_agents能力，只查询本次选中的已绑定agent，不探测job/SSH；状态取不到显示unknown，未绑定明确显示未绑定，不冒称idle或完成。task状态仍是现有工作流状态，不从agent/job状态反推或新增状态机。
2. `mam task list --json`保留完整结构化任务信息，并可提供与列表相同的agent状态。保持既有字段，供脚本消费。无需为所有命令改变默认输出。
3. `mam task show`默认输出实际发布revision和未经JSON转义的Markdown正文。--file task/report、--revision的选择语义保持；`--json`恢复原有结构化对象，字段/content不丢失。其他命令尤其create/publish/status/job/workspace默认JSON保持，避免无关破坏。
4. `mam task status`不再隐式探测/刷新job进程；继续展示已保存的job检查结果和checked_at，以及workspaces/publications/drafts/requirements_changed等现有信息。实时进程检查仍由`mam job list`负责，archive/job add等原有必要检查不受影响。
5. `mam job list`先按task/status等静态条件筛选，再做必要的进程/agent查询，避免为了默认列表或--attention查询已归档agent。注意running/stopped是实时状态，不能先用旧缓存状态错误排除可能已经变化的非归档job。--attention原有“停止且agent不active才待处理；unknown单列”语义保留。此次不新增缓存守护进程、新命令或复杂的跨主机批处理框架。

## 简洁与验证

使用标准库与现有打印/探测函数。目标为小幅改动（若预计超过约200行生产实现增量先解释）；不改任务存储格式、UUID、发布/归档/删除逻辑及生命周期。README仅补默认输出与--json用途，避免重复CLI帮助或新增大段管理规定。

测试重点：默认列表确实一任务一行且无详情、完整UUID/中文标题/空列表/未绑定或探测失败；--json信息完整；show正文和revision及历史--revision选择正确；status不调用进程探测；job过滤不联系已归档agent且不遗漏因实际状态变化产生的attention。复用现有测试框架，避免庞大模拟系统。按README跑完整标准库单测与diff-check；在自己的环境用临时测试root做CLI验收，不能以真实MAM根目录作可变测试数据。

交付干净commit和简短report：task_revision、workspace/HEAD、改动范围、验证、已知行为变化。任务记录共享checkout只编辑自己的report并经mam publish发布；实现代码留独立worktree等Manager合并。预计40分钟内给首个可review交付。
