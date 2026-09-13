# MAM native-v2 fallback：已验收版本集成、安装与生产验收

你使用 gpt-5.6-terra/max 执行已批准发布，Manager 负责裁决。读 AGENTS、README、.local/README、docs/development.md 和 docs/install.md。本次只集成与安装，不设计新功能或修改已审查代码。

## 已通过的准入

源任务 b49a5b40-1d18-40e6-bc28-c5c57dc011f3 的完整 source 是 3f2738abcfc9cbe50b25222562fc58b2bac0a7ff（核心 46af8c2，基线 bc8726f）。独立 review 052c3051 最终 report 4580953c243b45b5c1d688bf3261aa990801d34a，核心 215 项独立通过。Manager 亲自实测的完整真实原生 v2 闭环已 PASS：
.tasks/b49a5b40-1d18-40e6-bc28-c5c57dc011f3/native-v2-fallback-evidence.json，
SHA-256 b87e37cbb0214f53f447f23d13c297863fdf14d753869756c895aead699858bf。
实际拒绝一次、Manager active 不打断、fixture restart 去重、root idle 实际收到一条通知、同 child native followup 归档、两事件移 history、source before/after 完全一致，14 receipts 已外存且 fixture 已停机并删除。不要重跑此 fixture 或新建原生测试 child。

## 执行范围

1. 核查当前 main 与 source 的祖先关系和 primary worktree 的无关 dirt。保护 docs/wash-cup-shared-memory-token-usage-audit.zh-CN.md 和其他 task/report 草稿，禁止 stash/reset/覆盖它们。main 当前 bc8726f，先 git fetch origin main，若 origin 有不在 source 的新代码则报告具体差异，不盲目覆盖。以正常 fast-forward（或经祖先验证的 compare-and-swap ref 更新）将 source 合入 main，再将 main 合入 project/state-vla。project 的 .tasks 发布可能由其他 agent 并发进行，操作前重新核对 HEAD，不强制改该分支。不要 push。
2. 用 mam workspace add 本任务 --repo multi-agent-manager --base main 建立干净、准确 3f2738a 的独立安装 worktree。阅读其规范，不复用作者 editable 树作长期安装源。确认 MAM_ROOT 仍 primary project/state-vla 且 manager 仍 01a09657-e0f3-7352-b726-aba5bbd5d498。
3. 非交互执行标准 bash scripts/install.sh（可显式 MAM_SERVICE_MANAGER 为上述 root），保存完整有界安装 transcript 到本 task 的 evidence 目录。安装器自带必须完成的单元测试、wait 行为检查、随机未知 ID API 检查、六个 terra/max 模型 turn 的普通持久线程真实 delivery fixture，然后才替换本项目生产 daemon。不要绕过或用上面的原生 fixture 代替这些 gate。当前 App Server 实际 trace 环境此前已匹配，预计无需重启；不要自动给 yes、不要重启 App Server 或更改 Codex DB/features。若安装器因需要 App Server 重启退出，保留现场并报告具体目标/原因，由 Manager 决定，不能扩大操作。
4. 安装后确认 pipx installed package 的 wake_runtime.py 与已验收 source 内容一致、实际 singleton daemon 使用安装包且健康、Manager binding 保留。核对现存 training/eval task/job 数和身份未变（观测/合法归档变动需与活动 owner 区分）。新 fallback 后续可能出现真实 blocked 旧 job 升级，这不等于安装失败，不人工清除 state。不得对训练、eval、生产 task/job 做归档/改绑或停止。
5. 发布 report：准确安装 source/merge commit、测试数与三个 live gate、安装退出状态、App Server 是否重启、生产 daemon 前后 PID/identity/manager、保留证据路径和SHA，明确普通 thread 测试与真实原生测试的边界。可执行工作结束正常退出，MAM 后续唤醒，不轮询。预计超30分钟程序登记 job；本次安装预计短无需额外 job。异常只做本次安全可逆收尾，不为通过验收擅改产品实现。
