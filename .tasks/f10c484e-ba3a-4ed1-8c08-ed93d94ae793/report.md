# TeX 环境、证据图与冻结稿验收报告

- 已安装并验证精简工具链：`latexmk` 4.83、TeX Live 2023（`texlive-latex-extra`、`texlive-science`、`texlive-fonts-recommended`）及 Poppler 24.02；未安装 `texlive-full`。
- 新增本任务独占的 `figures/current_evidence.py` 和 `figures/current_evidence.pdf`。脚本只读取 `docs/analysis/accepted_results_20260913.json`（SHA-256 `81be95c41d83824bfe748027dfcc1a2eecd77520c4d2219c5301b02e4c491f9b`），运行时验证 30 个完整批次、每批 100 outcomes、3,000 次执行及 18 个唯一训练模型。图左显示 put-back J/T 的 eval-0 100-episode 点；图右显示 rearrange S 的三个 100-episode eval 批次及每个训练模型的 300-episode 聚合。图为单页双栏矢量 PDF，字体嵌入且子集化；右 panel 已仅保留带样本量的图例。
- 按授权最小修复 `scripts/check_submission.sh`：身份信息扫描只在可选的 `figures/source` 存在时纳入该目录；所有页数、Letter、TBD、交叉引用、匿名性和字体门禁未变。`bash -n` 与 `git diff --check` 通过。
- 冻结稿在 `/root/Documents/task-state-vla-paper` 执行 `make paper` 成功，产物为 `paper.pdf`：5 页、US Letter、236,955 B、SHA-256 `0d735d72594b2b61256e0878f88472954b0791fe960f7d088be602599db362bc`。`paper.pdf` 与 `build/main.pdf` 哈希一致。
- 最终 LaTeX/BibTeX 日志没有 error、undefined citation/reference、overfull 或 underfull；`build/main.blg` 的 `warning$ -- 0`。`pdffonts` 确认全部嵌入并子集化；PDF 文本无 `??`，参考文献可提取。5 页均已 150 dpi 渲染检查，未见裁切、重叠或表格越界；证据图位于第 4 页并清晰可读。
- `make check` 按预期以退出码 2 失败，唯一门禁原因是正文可见的 `INTERNAL EVIDENCE-GATED DRAFT`；页面尺寸、匿名 PDF 元数据、字体和交叉引用检查均通过，且不再报不存在的 `figures/source`。

正式构建日志保留于 `/root/Documents/task-state-vla-paper/build/main.log`、`build/make-paper-final.log` 和 `build/make-check-final.log`。本任务未改动科学正文、表格或科学文档；Manager 对冻结稿的正文/表格修改保留原状。
