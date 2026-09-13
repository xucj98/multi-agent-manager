# MAM native v2唤醒拒绝修复：独立代码review

使用gpt-5.6-terra/max。按MAM AGENTS、README任务/执行与交付、docs/development.md和详细设计操作。先mam task show本TASK-ID并读源任务b49a5b40的已发布task/report；从交付commit `46af8c2afd3790a8e1d0538e4f624170753e67fc` 建本任务独立MAM worktree（repo multi-agent-manager），不要修改源作者tree或生产状态。

独立审核完整diff（base bc8726f），审查精确unsupported识别及旧state迁移、blocked source到Manager升级的持久签名/去重、新job批次、active/paused/unknown/wait行为、accept后重启/失效/归档/rebind、Manager缺失/自身/递归情况、普通RPC和transport-uncertain未退化、service status与文档是否准确。特别检查实际cycle先后顺序与既有_maintain_accepted、_event_condition和过期清理的交互，不只读新增helper或照单接受215test报告。

运行适当独立验证及规定全量 `.venv/bin/python -B -m unittest discover -s tests -v`。如果发现问题，报告具体复现和最小修正建议；小修也先报告Manager，不自行合并/安装/重启production。评估上线所需的最小实际验收：普通thread liveprobe不覆盖原生v2child；不能仅mock通过声称真实限制消失。不要向外部/真实用户线程发实验通知。提交清楚PASS/FAIL/条件、问题优先级/文件行、验证证据和剩余风险到report并publish。回CODEX_THREAD_ID供绑定（本次spawn仅返回canonical name）。完成可执行审阅正常结束turn，MAM通知Manager。

## Manager 裁决和追加终审（2026-09-13）
Manager 接受 1b6d351 的条件 PASS：215测试证据有效，P3说明需修正；executor active 不代表 stopped job 已收尾的保守语义合理。源作者继续做仅文档修正，并准备隔离真实 native-v2 fallback 操作脚本；不重启生产。
作者提交后可用原生 collaboration.followup_task 通知本 reviewer 接续，读取源任务新 report，独立审查新增 docs diff 和 fixture 脚本的隔离、身份、重复投递/重启与清理边界。不重复 215 全套，除非新增代码影响产品逻辑。fixture Manager 计划使用当前 root，原生 child 计划复用你自己的 UUID；必须先给出脚本审查结论，未经 root 明确准入不执行 fixture，不改生产 task/job/daemon/App Server，不新增线程或主动归档本生产 review task。若 root 准入后收到 fixture followup，务必按完整 fixture root/config/job ID 核实，仅操作 fixture job；本任务绑定保持不变。
更新本 task report 并 publish，使 MAM 根据新 report revision 通知 Manager；当前可执行事项完成后正常结束 turn。
