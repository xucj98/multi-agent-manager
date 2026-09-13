# MAM multi-agent v2 completion wake compatibility

用户要求先安排wuwen-1训练（已派e3bc64f1），再排查为何结束后subagent不收尾/不唤醒Manager。Manager已确定根因，现委派有界修复。用terra/max，回CODEX_THREAD_ID。读MAM AGENTS/README/.local以及docs/development.md和docs/task-management-design.zh-CN.md；从同步后的main独立worktree实施，源树有用户dirty的docs/wash-cup-shared-memory-token-usage-audit.zh-CN.md，不碰。

## 已确认事实（无需重做耗时探索）
本机codex-cli0.154.0，MAM state.json有15个job_stopped（U6+eval9），delivery=rejected，failure_kind=explicit_rpc_rejection，明确错误`App Server request turn/start failed: direct app-server input is not allowed for multi-agent v2 sub-agents`。6U首次检测从2026-09-12T18:55:29Z至19:40:51Z；全被同类错误拒绝。MAM读PID状态成功；执行者未获得新turn。_desired_events有stopped就只投executor，并不生成Manager-ready；_delivery_failure把所有明确拒绝当可重试generic，_desired_events/state仍healthy=true，因此没有升级通知，已阻塞数小时。
先前installer liveprobe用4个thread/start普通持久线程，不是真正原生v2子agent，不能覆盖这条限制。官方https://learn.chatgpt.com/docs/app-server只泛述turn/start，未说明此v2限制；本机generate-json-schema --experimental也未发现公开subagent send-input RPC（不要把API sessions工具当成App Server同接口）。Manager现已用collaboration.followup_task成功唤醒U与eval owners，未改绑定/持久state，现有收尾在进行。

## 修复范围与不变量
1. 精确认出这种明确unsupported v2 direct-input rejection；停止对同一未变待办盲重试。不得把所有RPC error都永久阻断，也不得对transport uncertain做同样处理。
2. 对仍有效的被拒绝executor待办，创建一次持久化Manager升级通知，包含task/executor/job/错误/需要由Manager原生followup的动作。Manager active/paused/wait、重复投递、restart、unknown state、archive/rebind stale保护均保持；按实际未变条件去重，不能每个tick/每个job唤醒Manager无数次。新完成job仍需成为新有意义待办，不因过去unsupported永久丢失；合批合理处理。
3. 不直接伪造multi-agent历史、修改Codex内部数据库/feature flag、替换agent或绕开App Server限制。若找不到真实支持的RPC就以Manager正常turn/start为fallback，由Manager原生工具分发；不假称subagent直接唤醒已恢复。
4. 服务状态区分进程活着与投递受阻。以现有字段/诊断作最小清晰表达；README简短更新操作规则，详细设计说明新持久状态/升级去重/失效语义，修正安装验收的覆盖边界（普通thread成功不保证v2child成功）。不扩成新scheduler。
5. 添加必要回归覆盖明确拒绝→升级一次→manager active不打断→idle投递→executor原生激活/收尾归档后不再错误唤醒；restart、rebind、unknown/paused、manager missing/等于recipient、防递归、一般transient RPC errors重试仍有效。运行规定unittest全套。

先完成diagnosis.md/实现/测试并发布report与commit，等待独立review；不自行安装/重启production或App Server。新的MAM live验证在review后由Manager安排，允许mock明确reject的回归但不能仅mock就宣称真实v2链路恢复。任务当前工作完成后正常结束，不轮询。

## Git基线核实
Manager已git fetch origin main。origin/main=2cb7309是本地main=bc8726f的祖先，故本地main已包含远端，不回退、不覆盖已安装task rebind。请从main=bc8726f创建修复worktree。

## Manager review 裁决与下一步（2026-09-13）
独立 review 052c3051 已对 46af8c2 条件性 PASS，独立全套 215/215；Manager 接受其 P3 文档问题与保守 currentness 解释。请在原作者 worktree 仅做文档修订：设计文档明确 manager==executor 的精确 job_stopped 拒绝仍可 blocked，但不生成 self-escalation；README 精简说明仅向不同的有效 Manager 升级。补充 executor active 不是 job 已收尾，未归档 stopped job 的一次 escalation 仍可保留；Manager 收通知应先核对执行者状态/报告，避免重复原生 followup。保持 README 操作手册简洁，不改核心实现。提交、diff check、发布最终 commit/report；纯文档小修无需重复全套。
另请只读评估最小真实 native-v2 fallback 验收实施方案，优先隔离 fixture project/state、真实原生 child、当前 root Manager 实际 idle 收到一次通知，再由 root followup 让 fixture executor 归档 fixture job。可复用 reviewer 作为原生 child（需 Manager 派发），不触碰生产 task/job 状态、不改变 Codex DB/feature、不新增未知线程。准备可 review 的脚本/操作步骤和清理边界，尚不运行 fixture、不安装、不重启 App Server/生产 daemon。报告已有 installer 的 invocation 和现有环境是否能无需 App Server 重启通过。具体上线由 Manager 在最终审查后安排。

## Manager对追加终审的裁决（2026-09-13）
已读独立review revision b79d4cb，核心46af8c2的条件PASS保持；文档P3已解决。当前5b5ca3b fixture不准入实际执行，尚未对生产运行。接受以下窄修：
- Git初始化子进程统一清除继承GIT_*，禁用system/global config和外部hooks/template；核实生成的toplevel/gitdir属于fixture。不要改用户环境或生产git config。
- source CLI统一使用venv python -I -m multi_agent_manager.cli并在prepare中实读module paths+git commit做身份核对，禁用PYTHONPATH误导；报告确切待测hash。
- stop→start之间以fixture service status确认running false后再start；restart验证明确至少2 cycles的增量，不能仅>baseline。
- escalation精确error和source linkage都校验；delivered attestation含精确错误；archive history按delivered baseline绑定同signature/error/attempts/accepted事实，child归档用明确原生工具回传留证，不从非空report猜操作者。
以上以最小修订和有界无模型临时验证实现，不扩成新产品功能/通用测试框架，不重复核心215测试；README保持简短。修正后提交、发布report，再原生followup同reviewer复核新diff/关键负例。仍不运行真实fixture/production install/restart。root独立验收后会立即派真实fixture步骤。
