# C3 renderer gate 解释器 symlink 窄修复独立 review

## 目标与范围
作为独立 reviewer，核验源任务 e6908de7-4b02-465a-987b-a19eba7a315a 的最新窄修复是否解决虚拟环境解释器被 Path.resolve 跟随 symlink 到 base Python、导致 numpy 缺失的启动前故障，是否引入门禁语义回归。此任务由新 Manager 01a09657-e0f3-7352-b726-aba5bbd5d498 派发，执行模型 gpt-5.6-terra，reasoning effort max。

唯一运行时代码审阅范围：RMBench bf34743334efc98440fa9b05e3f2f05e8303846a..2e9677ce8ec9f623395184f63f32ddafa66e5e44。
交付候选所在树 /mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench-r3-lifecycle-gate。
注意 mam task create --review 自动记录的是源任务注册的主 worktree commit；本次候选明确是上面的独立树 2e9677c，不是自动捕获的 3775d4a。先核验 SHA/父提交和实际 diff，避免审错树。

## 执行
先阅读 MAM AGENTS.md、README 核心原则/任务管理/执行与交付、.local/README.md；mam task show 本 TASK-ID，并读取源任务当前已发布 task/report 的最新章节。创建独立 worktree：mam workspace add e755c753-4acf-4958-85f4-7595fba739a0 --repo RMBench --base 2e9677ce8ec9f623395184f63f32ddafa66e5e44，再读该树 AGENTS.md 和相关代码/环境规范。
检查 Path(os.path.abspath(...)) 保留 symlink、相对路径与 ~ 展开处理、worker 实际调用路径，检查测试能捕获旧故障且不是只复述实现。执行适当 CPU tests；需要时使用临时最小 venv 重现旧行为/验证新行为。禁止 GPU 作业、部署、改动活跃运行树、合并或修改候选代码；发现 blocker 给出可核验条件和建议，由 Manager 裁决。
保持 scope 窄；bf3474 门禁主体和 291d6d8 文档已被 18db597f review 通过。不要把已撤回的旧 checkout 文档问题重新列为 blocker。C3 40-reset 尚未实测，新 CPU review 不能宣称它已通过。

## 交付与验收
在本任务 report.md 写明 PASS/BLOCKED/需补证、准确审阅 SHA 和 diff 范围、发现及严重度、实际命令和结果、证据文件位置、未验证部分（尤其 C3 GPU gate）。发布 mam task publish e755c753-4acf-4958-85f4-7595fba739a0 --file report，然后报告 Manager；不自行归档 task/worktree，不自行通知源执行者部署。
无可执行事项后正常结束 turn，由 MAM 唤醒 Manager；不得自建轮询或反复发无变化状态。
