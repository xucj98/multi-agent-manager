# 论文旧材料机械清理（核心设计由Manager完成）
用户已授权清理论文工作空间，只保留当前材料。目标repo /root/Documents/task-state-vla-paper；Manager正在主工作树亲自编写 docs/EXPERIMENT_PLAN.zh-CN.md、RESEARCH_POSITIONING、正文和README，不得覆盖这些修改。

先读MAM AGENTS/README/.local/README，回 CODEX_THREAD_ID，查询本TASK-ID，创建独立worktree（base 0847046），必要repo路径用绝对路径，读涉及AGENTS。任务仅机械清理，不设计论文。

按明确清单 git rm 这些已被新材料取代的跟踪文件：review.md、claude/plan.md、claude/review.md、docs/EXPERIMENT_TODO.md、docs/STORY_AND_CLAIMS.md、docs/REVIEW_2026-08-04_INDUCTIVE_BIAS.md、docs/REVIEW_RESPONSE.md、docs/REVIEW_ROUND2_2026-08-04.md、docs/REVIEW_ROUND3_2026-08-04.md、docs/REVIEW_ROUND4_2026-08-04_TITLE_AND_THESIS.md、docs/EXPERIMENT_PLAN_20260910.zh-CN.md、docs/RELATED_WORK_POSITIONING_20260910.zh-CN.md、docs/PAPER_NARRATIVE_20260910.md。提交仅含这些删除；原材料可由旧HEAD恢复，不在paper里建另一个archive。

当前主树原先就有未跟踪ROADMAP.zh-CN.md，以及docs/MEMORY_CONFIG、MEMORY_DESIGN_FRAMEWORK、MEMORY_SCHEMA_SAMPLES、MEMORY_SCHEMA_SWAP_T、docs/memory_config整个目录。不要删改任何未跟踪材料。把ROADMAP逐字副本备份到本task workspace的preserved/并记sha256，Manager会在确认备份后移除主树过期ROADMAP。其余schema文件是有价值材料，保留在paper当前工作空间。

另读新Manager计划（主树只读），仅做机械/事实review：预算加总、链接、seed口径有无互相矛盾。不要重设计或扩scope。交付删除commit、备份hash/路径、发现列表、diff-check。发report并发布，结束turn等待MAM，不轮询。

## 明确追加清理清单
旧figures/source内5个tex及对应figures/*.pdf（overview、target_timeline、simulation_evidence、real_world_suite、real_robot_protocol）均是旧方案图，随旧稿由Git保留，从当前工作树删除；figures/frames的历史原始画面保留不动。旧paper.pdf也删除：Manager已改写LaTeX，但当前无latexmk/TeX编译器，不能把旧PDF伪称新稿。Makefile/README由Manager更新，不要编辑。新的figures未绘制不属于本task。删除commit加上这些明确文件，校验git历史可恢复。
