# 独立review：MAM任意job归档及task归档门禁

Review source delivery (source TASK-ID: 4078184c-26e3-4386-88f3-e3ff8f5473bb):
{
  "task": "4078184c-26e3-4386-88f3-e3ff8f5473bb",
  "commits": {
    "multi-agent-manager": "330252072cb3c2a834a69a9d63cd1e34627668fa"
  }
}

Source task requirements:

# MAM job 归档

## 目标
允许归档任意已登记job，无需实际进程停止。archive只结束MAM跟踪并保留历史，绝不停止进程。task归档要求其所有job已archived，不检查已归档job的实际存活。保留既有worktree路径/改动等清理保护，不扩展CLI或新增状态。

## 执行
从MAM main建立本任务独立worktree，阅读AGENTS、开发指南和设计文档。修改job archive、task archive中相关门禁及必要wait过滤，去掉归档时不必要的远端探测。running/stopped/unknown均可archive；--note仍必填；重复归档沿既有幂等行为。保留原进程身份、历史观测、归档时间和原因，不能伪写stopped。已归档job不再触发wait待办，不再周期探测。
同步README、CLI help、docs/task-management-design.zh-CN.md中的相关语义，文字简洁。不要改无关文档或生产.tasks记录，不安装、不合并、不push、不触碰实际PM。

## 验收交付
必要测试覆盖运行中的真实本地sleep被归档后仍存活、unknown/SSH不可达无需连接即可归档、未归档job仍阻止task归档、全部archived后无需进程停止、wait排除归档job。测试自己的sleep最后自行清理。运行适当测试及开发规定全套；提交代码，report写commit/改动/测试/限制，发布后结束turn，Manager安排独立review。不要空等待或无变化汇报。

## 术语确认
用户明确仍叫“归档”。命令、help、文档维持archive/归档命名，不改成取消登记或结束跟踪接口；结束跟踪仅说明归档效果。

Source report:

# 交付报告

- 完成：`mam job archive` 现在可归档 running、stopped 或 unknown/待核实的已登记 job，不触发进程探测或停止进程；保留原身份、最后观测、归档时间和原因。`mam task archive` 仅在所有 job 已归档后执行，不检查已归档 job 的实际存活。已归档 job 不再触发 `mam wait` 的待办或探测。
- 文档与帮助：同步 README、设计文档和 `task/job archive --help`，保留“归档 / archive”术语与现有命令。
- Workspace：`/mnt/public/xcj/Projects/workspace/4078184c-26e3-4386-88f3-e3ff8f5473bb/multi-agent-manager`
- 交付 commit：`330252072cb3c2a834a69a9d63cd1e34627668fa`（`fix: archive jobs without probing processes`）
- 验证：`.venv/bin/python -B -m unittest discover -s tests -v`，115 项通过；覆盖运行中的本地 sleep 归档后仍存活并清理、SSH 不可达/unknown 无需连接即可归档、未归档 job 阻止 task archive、全部归档后无需进程退出、wait 排除已归档 job。
- 限制：按任务要求，归档只结束 MAM 跟踪；仍在运行的外部进程需由其所有者或外部流程自行结束。

## 独立验收范围
在独立MAM worktree固定330252072cb3c2a834a69a9d63cd1e34627668fa，读取源任务已发布要求和报告。检查job归档无条件于进程存活、不探测/不杀进程、保留历史身份/观测/原因、幂等；task仅允许所有job已归档，不放松已有worktree清理保护；wait及查询不探测或唤醒归档job。核查README/help/design简洁一致，术语仍为归档。独立运行115项全套及必要真实sleep验证。不要操作生产PM或修改生产登记。只报告实质问题及证据，明确通过/不通过；报告发布后结束turn。
