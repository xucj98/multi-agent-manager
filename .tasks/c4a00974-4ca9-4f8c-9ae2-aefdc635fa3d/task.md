# 论文44批证据版：TeX编译与排版验收（不做科学审稿）

使用 gpt-5.6-terra / max。你只负责构建与排版验收，科学主张、数据解释和实验设计由Manager完成。不派subagent、不作独立科学审稿。先读MAM AGENTS/README任务与执行说明及.local/README，用本TASK-ID读取已发布要求。

源仓库 `/root/Documents/task-state-vla-paper`，冻结commit `adcf8d10674e58ee2a3f5a3e15d0a674cbb7897e`。Manager已完成44批源稿：4400次正式执行、20个评过的训练模型、12个完整3eval模型；put-back train0 N/S/J/T=66/136/213/210 out of300（22.0/45.3/71.0/70.0%）。原始证据快照 `docs/analysis/accepted_results_20260914.json` SHA256 `078912ae85b665cb2cb1fe8c8dafb75e6d747bd61ece7242578ad6a774ed122c`。稿件仍是内部实证研究草稿，有意保留submission marker，不宣称机制已证实或再次通过GPT6科学审稿。

建立独立worktree `/mnt/public/xcj/Projects/workspace/c4a00974-4ca9-4f8c-9ae2-aefdc635fa3d/task-state-vla-paper`、branch `task/c4a00974-4ca9-4f8c-9ae2-aefdc635fa3d`，base为上述commit。论文仓库位于PROJECT_ROOT外且无MAM源码环境installer，Manager授权沿前次builder同样的手动git worktree方式；不要为此建立新TeX环境或修改MAM。不在原仓库构建/写文件，不触碰原仓库untracked main.pdf。

本机TeX Live/latexmk/Poppler已安装。读README、Makefile、既有BUILD_RECEIPT；用现有构建命令生成paper.pdf，检查引用/溢出、页数Letter/字体/Author元数据与逐页视觉。正文/Tables/现有Figure数据和数字不改；新快照没有改变Figure2所展示的原eval0/serial数据，不需要重算统计图。可做必要且可审阅的局部排版调整（保持可读字号、页边距、模板），优先保留现有6页；不能为了页数删除科学限制或改变数字。若6页容纳不了而需实质删文，报告具体位置由Manager裁决。

`make check`因INTERNAL EVIDENCE-GATED DRAFT返回非零是预期，仍逐项核对其余检查；不能移除标记或将非零一概算构建失败。用pdftotext检查44/4400/20/12及put-back四系统的三组计数和百分比实际进入PDF；逐页渲染检查无重叠/截断/不可读图例。保存最终PDF SHA、源码base、编译/检查结果和可复制命令到BUILD_RECEIPT.md。允许README仅把PDF待构建状态更新为本轮已构建但待Manager验收，历史首次科学审稿身份不变。

交付精确clean commit（paper.pdf、BUILD_RECEIPT.md、必要最小layout/README），在本任务report发布结果、worktree/base/commit、PDF SHA和验收边界。保留worktree供Manager独立验收，不自行合入主仓库或归档。一般构建无需MAM job；若出现预计>30分钟的新长进程，先按MAM登记。完成当前可做工作后正常结束turn，由MAM通知Manager。
