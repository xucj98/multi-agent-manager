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

## Manager对 fda59da 复审的裁决（2026-09-13）
接受 reviewer ad8df989efb6ce953b096474729ec4684b61124b 的三项具体问题；Manager已直接核对代码，且只读 service status 独立复现 `-m` 的 `Store requires a project configuration`。核心 runtime46af8c2条件PASS不变，本次仅修验收脚本/操作文档。之前Manager指定的 `-I -m multi_agent_manager.cli` 在本库循环导入下不成立，本节明确替代该旧要求。

请在原worktree最小修正：
1. 全部controlled CLI argv统一为 `[SOURCE_PYTHON, "-I", "-c", "from multi_agent_manager.cli import main; raise SystemExit(main())"]`，receipt、README/helper帮助和runbook一致。保留真实module-path核验，不通过改产品Store/isinstance或导入结构绕过验收工具错误。必须在临时独立项目以shadow PYTHONPATH实际执行task show、service status、service stop和task archive验证；仅--help/语法检查不够，不能启动真实scheduler/App Server。
2. 在fixture stop且status running=false后、start前记录专用stopped receipt或相等冻结counter。restarted必须相对该stopped counter至少+2，仍绑定原blocked的source/escalation/task/job/Manager/child/旧daemon身份与attempts；不能用最初blocked的旧计数。最小负例覆盖blocked10→旧daemon12→stop12→新daemon13必须拒绝、达到14才满足周期数。停止receipt必须有停机观测与来源身份，不能接受任意人为counter。
3. `_source_identity`用现有隔离Git helper拒绝非空 `git status --porcelain`，记录clean状态及HEAD/modulepaths。提供最小可调用核验，在首次fixture start前、最终停机后再次核对与prepare同一HEAD/clean/modulepaths；dirty tracked、untracked importable source和HEAD改变需被拒绝。测试在独立临时clone/venv中进行，不能污染真实author tree或production。运行中editable源不能改动，任何漂移使验收失败并保留现场。

只补三个针对性正负例，测试新增调用的真实入口和时序，避免再用与实现相同假设的合成case替代行为检查；原核心215无新runtime变更无需重跑。不新增通用框架/超出三项的重构。提交干净版本、publish report、原生followup同reviewer复审差异与上述证据。仍未准入真实fixture或生产安装/重启。当前可做工作完成正常结束turn。

## Manager 真实隔离验收进度（2026-09-13 11:18 UTC）

独立复审 4580953c243b45b5c1d688bf3261aa990801d34a 已通过 3f2738a 的三项窄修，Manager 接受并依 runbook 实际执行。此前“不运行真实 fixture”的限制已由本节推进到受控隔离验收；生产安装仍待完整闭环。

- Source 保持干净 3f2738abcfc9cbe50b25222562fc58b2bac0a7ff，module/CLI/source Git 身份已在 prepare 和 before-start 实读一致。
- Fixture root: /mnt/public/xcj/Projects/.native-v2-fallback-fixture-20260913T1116Z；其中 project 为唯一 CLI cwd、state 为独立 MAM_ROOT。
- Fixture TASK-ID eda0b0e4-d0b8-4439-a418-2bc56610d631，JOB-ID e85234e2-e078-494b-82b1-7c37d6722d61，本地 detached sleep 90 PID 1020130。Root 原生 followup 同一 child 01a096ab-e5f3-7672-8ff3-36328d3fcfb7 已实际完成登记；其生产审查 4006fc83 未修改。
- blocked.json 已通过：真实 direct-input 精确拒绝，source attempts=1/blocked/no retry；唯一 Manager escalation pending/attempts=0。Root active 保持待投递。
- stopped.json 已保存 service running=false/disabled 与冻结 cycles=13，现已仅重启 fixture service；下一步核验至少两个新 cycles 并写 restarted.json。未收到真实 idle-root notification，不能提前写 delivered attestation。
- restarted 后 root 必须结束 turn，实际收到带同 TASK/JOB/精确错误的 MAM Message 才按 runbook 验 delivered；然后 native followup 同 child 仅归档此 fixture job，核 history、停止 fixture、verify-source after-stop、归档 fixture task并将 receipts 保留到 fixture 外再 guarded cleanup。
- Source author 此期间不得修改 editable 源；生产 daemon、App Server、生产 task/job 均不在本次验收修改范围。

## Manager 完整闭环裁决（2026-09-13 11:22 UTC）

真实 fixture 已 PASS：restarted 从 stopped cycles13 到17且不同daemon PID；Manager随后在实际新turn收到同TASK/JOB/精确拒绝通知，delivered accepted/attempts1；root原生followup同child后真实job archive及child-archive receipt完成，两事件按原signature转history且 resolution 为 condition changed or resolved。child最终回答遇到provider503发生在成功归档/写receipt之后，Manager实读确认，无重复归档。fixture停机、source after-stop身份复核、task archive和guarded cleanup均完成。

14份回执永久外存本任务 native-v2-fallback-evidence.json，SHA256 b87e37cbb0214f53f447f23d13c297863fdf14d753869756c895aead699858bf。临时fixture目录已删除。正式集成和标准安装已委派 a0c09804-1b5b-4df3-abf0-986ff19381af，原source保持干净供版本核对。

对用户表述必须准确：本修复补的是明确v2 direct-input拒绝后的Manager转交与停止无效重试，没有恢复AppServer对原生subagent的直接turn/start，也不代表所有失败均为同一已知原因；一般transient/unknown错误保持原语义，不误报为此unsupported类别。
