# 交付报告：论文44批证据版 TeX 编译与排版验收

## 完成状态

已完成构建和排版验收，未作科学审稿。未启动 MAM job；构建和验证均为短进程。

## 交付物

- Worktree：`/mnt/public/xcj/Projects/workspace/c4a00974-4ca9-4f8c-9ae2-aefdc635fa3d/task-state-vla-paper`
- 分支：`task/c4a00974-4ca9-4f8c-9ae2-aefdc635fa3d`
- 冻结源码 base：`adcf8d10674e58ee2a3f5a3e15d0a674cbb7897e`
- 交付 commit：`f558f3ae63c55bf5106229cb50c50c3e29d16189`（clean）
- PDF：`paper.pdf`，SHA-256
  `5344be761ec0707641a7d11525a3ddca72f0036d30430c9e561c6c81e70cd020`
- 证据快照：`docs/analysis/accepted_results_20260914.json`，SHA-256
  `078912ae85b665cb2cb1fe8c8dafb75e6d747bd61ece7242578ad6a774ed122c`
- 可复现构建和验收细节见 worktree 中的 `BUILD_RECEIPT.md`。

## 最小排版调整

44 批正文使原 Figure 2 尺寸下参考文献溢至第 7 页。保留全部正文、表格、Figure 数据、科学数字、限制、字号、栏宽和页边距，仅将 Figure 2 从 `0.87\textwidth` 调至 `0.81\textwidth`，把双栏浮动体与正文间距调为 `0.35\baselineskip`，并将该图的 caption gap 调为 `0.25\baselineskip`。`0.82\textwidth` 已复现为 7 页；`0.81\textwidth` 是最大的已测试 6 页候选。README 已仅更新为本轮 PDF 已构建、待 Manager 验收。

## 验证结果

- `make clean` 后 `make paper` 成功；最终 PDF 为 6 页、US Letter（`612 x 792 pts`）、Author 元数据为空，所有字体 embedded/subset。
- `build/main.log` 无 citation、cross-reference 或 overfull-box warning；有一个 `Underfull \vbox (badness 10000)`，最终 180 dpi 逐页渲染未见空隙异常、重叠、截断或溢出。
- `pdftotext -layout` 在 PDF 中确认内部 `INTERNAL EVIDENCE-GATED DRAFT` marker，及 44 batches、4,400 executions、20 trained models、12 complete three-eval models；put-back train-0 N/S/J/T 为 `17/27/22 (66/300, 22.0%)`、`41/44/51 (136/300, 45.3%)`、`69/68/76 (213/300, 71.0%)`、`70/66/74 (210/300, 70.0%)`。
- 页面 1--6 已逐页渲染检查：无空白页、表格/图形溢出、重叠、裁切或不可读 Figure 2 图例；参考文献 [1]--[7] 均在第 6 页结束。
- `make check` 返回预期的 `make` exit 2，唯一失败为可见 `INTERNAL EVIDENCE-GATED DRAFT` 证据门禁；检查同时确认 6 页、Letter、空 Author 和 embedded/subset fonts。该非零返回不视为构建失败。

## 验收边界

本交付仅证明冻结 44 批源稿的 PDF 构建和可读排版。未改变科学内容，未移除内部草稿标记，未重新计算 Figure 2 数据，未进行科学主张、数据解释或实验设计审稿；未触碰原仓库的未跟踪 `main.pdf`，也未合入主分支或归档任务。
