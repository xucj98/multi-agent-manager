# 本机TeX安装与论文编译

用户明确授权在本机安装tex工具并编译论文。你用gpt-5.6-terra/max执行工程，Manager亲自修改科学叙述。阅读MAM AGENTS/README/.local和mam task show本TASK-ID，回CODEX_THREAD_ID供bind。

1. 在本机检查现有TeX、系统包管理和空间。安装足以编译 /root/Documents/task-state-vla-paper/main.tex 的TeX工具（例如latexmk、texlive-latex-recommended/extra、texlive-science、必要字体、poppler-utils；按实际依赖选，不默认texlive-full）。用户已授权系统安装，不必请求确认；不要修改GPU/Codex/MAM服务配置。
2. 先从该paper复制当前tex/bib/cls/bst及必要figure到自己的task workspace临时编译树，运行make paper/latexmk验证环境。Manager同时会改主论文科学内容，禁止覆盖sections/tables/docs内容；只报告编译错误。无科学代码改动无需独立业务worktree；如要修改Makefile/check脚本或修编译语法先发Manager具体diff，不并行写主树。
3. 环境准备好即报告版本和可用性，不等Manager写完。Manager通知稿件冻结后，从主paper运行make paper，生成/root/Documents/task-state-vla-paper/paper.pdf，保留build日志；给页数、编译warning及pdftotext可读性/引用与排版检查。若等待稿件且当前没有别的工作，结束turn，后续Manager用followup继续，不轮询。
4. 写紧凑report并publish。预计>30min的安装/下载需mam job登记；短系统包安装无需。结束后仅清理自己临时构建树，保留正式PDF与构建日志，不能删source/历史实验资产。

## 当前稿件工程验收补充
Manager已亲自重写正文并冻结。你仅负责从docs/analysis/accepted_results_20260913.json生成figures/current_evidence.pdf及可复现Python脚本：左put-back J/T各train seed的eval0 100集成功，右rearrange S三个eval批次及300集模型汇总；核验30批/3000执行/18训练模型。允许将图和脚本直接加入主paper，禁止改正文/科学docs。完成后main make paper、检查页数/字体/reference/overflow并逐页渲染；make check应因内部证据门禁失败，不移除标志。发布完整简报后结束turn以释放论文独立审稿slot。
