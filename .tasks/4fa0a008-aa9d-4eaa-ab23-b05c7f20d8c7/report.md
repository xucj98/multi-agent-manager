# 论文 40 批证据版：编译与排版交付

## 交付

- 论文交付 commit：`3425c3a1c767152bf78668079535b306dd4e3893`
  (`Build forty-batch evidence paper`)，基线冻结提交为
  `8dc182a2db6d8cfbb1db2780dc5ea3814ea5970f`。
- 工件：`paper.pdf`，SHA-256
  `8316dad1c0ba902d39abddff044b0ba191b83209b101dd771bde5ed03ce73d32`；
  简洁构建回执见 `BUILD_RECEIPT.md`。
- Worktree 为 Manager 授权的手动回退：
  `/mnt/public/xcj/Projects/workspace/4fa0a008-aa9d-4eaa-ab23-b05c7f20d8c7/task-state-vla-paper`，
  分支 `task/4fa0a008-aa9d-4eaa-ab23-b05c7f20d8c7`，common Git directory 为
  `/root/Documents/task-state-vla-paper/.git`。MAM repo 登记未伪造；worktree
  留待验收与后续按 Git worktree 流程清理。

## 排版调整

冻结稿首次编译为 7 页，第 7 页只含参考文献 [7]，其余页面空白。按 Manager 已发布裁决，交付仅将 Figure 2 的
`current_evidence.pdf` 宽度从 `0.93\textwidth` 调为 `0.87\textwidth`；没有改动正文、数字、引用、IEEE 字号、栏宽或页边距。
最终为 6 页，所有参考文献位于第 6 页，图中文字仍清晰。

## 验证

- 串行执行 `make clean && make paper` 成功；最终 `build/main.log` 无 citation、cross-reference、overfull 或 underfull-box warning。
- `pdfinfo`：6 页、US Letter (`612 x 792 pts`)；PDF Author 元数据为空。`pdffonts`：全部字体 embedded 且 subset。`pdftotext` 成功。
- PDF 文本已核对包含 40 complete batches / 4,000 executions / 20 trained models / nine complete three-batch models、rearrange J train-0 `87/87/90 (264/300)`，以及独立 action RNG-stream 对照说明。
- 逐页渲染检查第 1--6 页：无表格/图溢出、重叠、空白页、错误的最终参考文献断页；Figure 2 的轴、图例和注释可读。
- `make check` 预期返回非零（`make` exit 2）：唯一拒绝原因是可见的 `INTERNAL EVIDENCE-GATED DRAFT` 标记。检查同时确认页数、Letter、匿名 Author 元数据和嵌入字体，未报告 `??` 交叉引用或 identity-bearing source finding。

本交付只证明 TeX 工件与排版状态；不是空白 GPT-6 论文审稿、新实验验收或第二轮科学 PASS。临时渲染与构建试验文件已清理，保留忽略的可复核 build 输出与 PDF。
