# 论文旧材料机械清理与新计划只读核算

## 交付

- 独立 worktree：`/mnt/public/xcj/Projects/workspace/bf0feac7-d9ac-436b-a61e-8c9952f4855d/task-state-vla-paper`
- 基线：`08470467b5465f1d819a40db4d5cd415091daf9e`
- 删除提交：`a5cd5e662201b2e0ce7773969bda14de269eefa2`（`chore: remove superseded paper materials`）
- 提交内容仅为 24 个明确指定的旧材料删除：2,595 行文本删除，外加旧图/PDF 二进制文件删除；没有改写 Manager 的新计划、正文或 README。

已删除的路径如下，亦记录于 task workspace 的 `deleted-files.txt`：

```text
claude/plan.md
claude/review.md
docs/EXPERIMENT_PLAN_20260910.zh-CN.md
docs/EXPERIMENT_TODO.md
docs/PAPER_NARRATIVE_20260910.md
docs/RELATED_WORK_POSITIONING_20260910.zh-CN.md
docs/REVIEW_2026-08-04_INDUCTIVE_BIAS.md
docs/REVIEW_RESPONSE.md
docs/REVIEW_ROUND2_2026-08-04.md
docs/REVIEW_ROUND3_2026-08-04.md
docs/REVIEW_ROUND4_2026-08-04_TITLE_AND_THESIS.md
docs/STORY_AND_CLAIMS.md
figures/overview.pdf
figures/real_robot_protocol.pdf
figures/real_world_suite.pdf
figures/simulation_evidence.pdf
figures/source/overview.tex
figures/source/real_robot_protocol.tex
figures/source/real_world_suite.tex
figures/source/simulation_evidence.tex
figures/source/target_timeline.tex
figures/target_timeline.pdf
paper.pdf
review.md
```

所有旧材料仍可由 Git 历史恢复。`figures/frames/*` 的历史原始画面未动；主树原有的未跟踪 memory schema/config 材料、checkpoint、数据集和评测产物也均未触碰。`Makefile` 与 `scripts/check_submission.sh` 对 `paper.pdf` 的引用是构建输出/检查输入，保留不改。

## ROADMAP 逐字备份

- 原文副本：`/mnt/public/xcj/Projects/workspace/bf0feac7-d9ac-436b-a61e-8c9952f4855d/preserved/ROADMAP.zh-CN.md`
- SHA-256 sidecar：`/mnt/public/xcj/Projects/workspace/bf0feac7-d9ac-436b-a61e-8c9952f4855d/preserved/ROADMAP.zh-CN.md.sha256`
- 大小：14,234 bytes
- SHA-256：`78a94fb2809e7253aa22859a4dc4e3dbfdc85c5ae0019c0cd7d960672221008f`

该副本位于 task workspace；在归档会清理 workspace 前，应由 Manager 转存为持久证据。

## 校验

- 提交前 `git diff --cached --check` 通过；最终 `git diff --check HEAD^ HEAD` 也通过。
- worktree 的最终 `git status --short` 为空。
- 对 Manager 主树新计划、研究定位、README 与 RAL 要求进行了只读审阅；本次没有编辑主树。
- 新正文中的本地 Markdown 链接均可解析，且未引用本提交删除的旧图。

## 新计划只读核算结果

未发现预算、seed 口径或链接的明显相互矛盾，且没有对计划作设计性改动。核算结果如下：

- 主比较为 36 个模型、108 个评测批次；U/T/C 为 12/9/9，F/D 为 45+24，外部 E 为 27，因此总计为 `(108 + 45 + 24 + 27) × 100 = 23,400` episodes。
- 非 E 的新训练数为 42；计入 E 的 9–20 个等价训练后为 51–62。估算 `1,020–1,240 GPUh`，加 20% 余量后为 `1,224–1,488 GPUh`，算术正确。
- `12 × 7 × 24 = 2,016 GPUh`、重复训练/评测条目、真机 `2 × 4 × 30 = 240`，以及覆盖波次 `600 / 12 = 50h ≈ 2.1 天`均一致。
- NativeMEM 的表述准确：官方源码公开但仍为 WIP，未提供官方 release 或权重；复现需要自行完成 Stage-1 tokenizer、缓存和 Stage-2。计划已把未知工程代价写明。`click_button` 不应在未核对环境前等同于 `press_button`。
