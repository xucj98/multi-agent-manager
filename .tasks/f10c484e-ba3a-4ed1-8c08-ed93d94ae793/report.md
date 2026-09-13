# TeX 环境与初始编译报告

- 已安装精简编译依赖：`latexmk` 4.83、TeX Live 2023 的 `texlive-latex-extra`、`texlive-science`、`texlive-fonts-recommended`，以及 Poppler 24.02；未安装 `texlive-full`。系统盘安装增量约 447 MB，安装后仍有约 63 GB 可用空间。
- 在任务 workspace 的隔离快照 `/mnt/public/xcj/Projects/workspace/f10c484e-ba3a-4ed1-8c08-ed93d94ae793/tex-smoke`（源提交 `fb0ad872e3b499034e2a997261df68eb55edc867`）执行 `make paper` 成功。PDF 为 3 页、US Letter、182,784 B；BibTeX 与最终引用解析完成，字体均嵌入且子集化，`pdftotext -layout` 可读。
- 编译无错误。唯一最终 LaTeX 排版警告是 `sections/03_method.tex` 第 13 行附近 `Underfull \hbox (badness 1755)`。
- `make check` 如预期因正文可见的 `TBD` / `INTERNAL EVIDENCE-GATED DRAFT` 失败；其余已检查项（页数、Letter 尺寸、匿名 PDF 元数据、字体）通过。脚本对不存在的可选目录 `figures/source` 会打印一条 `rg` 错误，但不影响上述证据门失败判定；未修改主稿或检查脚本。

主论文目录 `/root/Documents/task-state-vla-paper` 未被本任务修改。环境已可供冻结稿在该目录运行 `make paper`；待 Manager 通知后再做正式 PDF、日志和最终排版验收。
