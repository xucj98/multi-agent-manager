# 迁移独立验收

独立验证 /mnt/public/xcj/Projects/state-vla 下 RMBench、openpi、robot-bridge、opendm 及新的 multi-agent-manager。用户要求空白 GPT-5.6-terra max agent 能按迁后入口正常使用 mam，特别是实际 mam workspace add。本任务登记在旧 MAM，只用于本次独立验收；先读旧入口与任务，然后从新目录读新入口，独立核对不能只复述执行简报。

范围：核对新 env MAM_BRANCH=project/state-vla；非 .tasks tracked 内容与 origin/main 一致、旧分支历史仍在；本地保留分支、用户文档和正式数据/checkpoints/eval 均在；三套环境 CPU 验证；5库 .local/create_worktree.sh（含 MAM）实际运行是否可用。禁止启动 train/eval，禁止停止旧 MAM service，禁止使用旧 workspace 作为新测试的结果。

可以在新项目下创建一个专门的临时验收 task（按 CLI 帮助正确绑定，报告其 TASK-ID），通过新 mam workspace add 对五库创建独立 worktree，各用当前 primary HEAD 为 base；检查 worktree 路径全部在新 state-vla/workspace、Git common dir 指向新库、环境可用，无错误旧路径。新 clone 不复制 runtime；本轮不建立持久 service/manager 身份，若创建 task 有隐含副作用请先查明再执行。旧登记 task 与新验收 task 要区分。测试结束清理临时文件并归档新验收 task，确认没有测试 workspace/branch/未提交附件残留。发现工具本身不支持或现存代码有阻塞，停止对应项，向 manager 报告具体原因，不擅自大改业务代码。

报告简短，给实际验证结果/失败项/修复建议。临时文件仅本 task workspace/tmp，最后清理；发布旧实例本 task report。最终任务文档迁入新 MAM 和 paper 项目进展更新由 manager 另行调度，不要与执行者并发改 Git。
