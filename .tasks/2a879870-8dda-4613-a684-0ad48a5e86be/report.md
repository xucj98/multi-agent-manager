# C 接续现场快照（2026-09-11 16:31 +08:00）

- 已接管 C 写入；16:00 后复查无遗留 uv、rsync 或 eval。原 owner 的 cache、checkpoint、assets 与 `workspace/5773.../records` 均只读复用，未重传。
- RMBench 原入口的真实错误不是 torch wheel 缺失：它在 `UV_OFFLINE=1` 下以 CU121 PyTorch index 联立解析 `torchvision==0.19.1` 的 `numpy/pillow` 传递依赖，因离线 PyPI registry records 不在该 index 而报 `requirements are unsatisfiable`。随后固定闭包诊断唯一缺项为 `ffmpeg==1.4` sdist；该 cache record 已在旧 task 完成补齐。
- 最短修复已在本机 RMBench 隔离 worktree 提交为 `423291f4a819cabe9190ca440b12232449073299`：新增可选 `--offline-lock-dir`，仅 C 启用时按 CU121 依赖、PyPI 依赖、torch/vision、本地 PyTorch3D/cuRobo 四阶段 `--no-deps` 安装；默认 hardlink/常规解析未变。`bash -n`、`git diff --check` 及原 owner c59 worktree 的可应用检查通过。
- C 稳定 RMBench 源为 `6139577`，不含本机 `c59` object；因此保持既有“提取 installer 后 patch”的边界。C `.local` 已保存两份精确锁（SHA256 `5bcc1a0b...b084`、`4b2cacf4...d1b6`）和小 patch，并已实际检查它们按顺序可应用于 current `6139577` 与 formal `3e69b1e`。
- 本任务 fresh current 创建正在收尾测量：`workspace/2a879870-8dda-4613-a684-0ad48a5e86be/fresh/current-rmbench/RMBench`，branch `task/2a879870-8dda-4613-a684-0ad48a5e86be-c-current-rmbench`。安装 `16:28:22–16:30:51` exit 0，四阶段离线安装通过，C wrapper 已输出 `uv_symlink=PASS` 和 `C symlink worktree ready`；cache 当前增量为 2,308 bytes。worktree/venv `du` 记录仍在完成，尚未把它当成三机 smoke 或正式 eval。

待续：完成 RMBench CPU/GPU 真实 sim/policy/renderer/cuRobo 检查，创建 strict 旧版三库运行树，三机 2-rollout smoke，随后才登记并运行单次严格 100 rollout。
