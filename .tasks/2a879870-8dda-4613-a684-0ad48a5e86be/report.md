# C 接续现场快照（2026-09-11 16:31 +08:00）

- 已接管 C 写入；16:00 后复查无遗留 uv、rsync 或 eval。原 owner 的 cache、checkpoint、assets 与 `workspace/5773.../records` 均只读复用，未重传。
- RMBench 原入口的真实错误不是 torch wheel 缺失：它在 `UV_OFFLINE=1` 下以 CU121 PyTorch index 联立解析 `torchvision==0.19.1` 的 `numpy/pillow` 传递依赖，因离线 PyPI registry records 不在该 index 而报 `requirements are unsatisfiable`。随后固定闭包诊断唯一缺项为 `ffmpeg==1.4` sdist；该 cache record 已在旧 task 完成补齐。
- 最短修复已在本机 RMBench 隔离 worktree 提交为 `423291f4a819cabe9190ca440b12232449073299`：新增可选 `--offline-lock-dir`，仅 C 启用时按 CU121 依赖、PyPI 依赖、torch/vision、本地 PyTorch3D/cuRobo 四阶段 `--no-deps` 安装；默认 hardlink/常规解析未变。`bash -n`、`git diff --check` 及原 owner c59 worktree 的可应用检查通过。
- C 稳定 RMBench 源为 `6139577`，不含本机 `c59` object；因此保持既有“提取 installer 后 patch”的边界。C `.local` 已保存两份精确锁（SHA256 `5bcc1a0b...b084`、`4b2cacf4...d1b6`）和小 patch，并已实际检查它们按顺序可应用于 current `6139577` 与 formal `3e69b1e`。
- 本任务 fresh current 创建正在收尾测量：`workspace/2a879870-8dda-4613-a684-0ad48a5e86be/fresh/current-rmbench/RMBench`，branch `task/2a879870-8dda-4613-a684-0ad48a5e86be-c-current-rmbench`。安装 `16:28:22–16:30:51` exit 0，四阶段离线安装通过，C wrapper 已输出 `uv_symlink=PASS` 和 `C symlink worktree ready`；cache 当前增量为 2,308 bytes。worktree/venv `du` 记录仍在完成，尚未把它当成三机 smoke 或正式 eval。

待续：完成 RMBench CPU/GPU 真实 sim/policy/renderer/cuRobo 检查，创建 strict 旧版三库运行树，三机 2-rollout smoke，随后才登记并运行单次严格 100 rollout。

## 阶段状态（2026-09-11 17:06 +08:00）

- `423291f` 已获独立 review 准入；fresh RMBench 的原 v3 / fresh `uv pip check`、freeze、两锁与实际 268 distribution 的版本对照均保存在 C `workspace/2a879870-8dda-4613-a684-0ad48a5e86be/records/`，不再重复安装或闭包审计。
- 为真实 rollout 新建唯一严格三树 `C:/mnt/public/xcj/Projects/state-vla/workspace/2a879870-8dda-4613-a684-0ad48a5e86be/formal/strict-100/{RMBench,robot-bridge,openpi}`：分别固定 `3e69b1e`、`8ea6078`、`a869498`，均 clean。C1 创建实耗依次为 RMBench 148 s（离线锁）、bridge 14 s、OpenPI 36 s；三机 rollout 尚未启动。
- 旧 bridge 的本地 `openpi-client` wheel 已由匹配 `ffa308d` package tree 的 strict OpenPI 源、显式 Python 3.11、`UV_OFFLINE=1` 构建，SHA256 `ab85f668f27b648f21d41e98546ebf1b7c2c1ed603e79982fd593872a3dc47d2`。首次 build 未显式指定解释器而失败的原始日志保留为 `strict-openpi-client-build.log`；retry 成功日志为 `strict-openpi-client-build-retry1.log`。
- **当前真实阻塞（未忽略）**：wheel 已以 local `uv pip --no-deps` 安装到 strict bridge venv，但 `uv pip check` 明确报缺 `dm-tree>=0.1.8` 和 `tree>=0.2.4`；因此 client scheduler smoke 和任一 rollout 均未开始。此为新缺依赖，不是 profile metadata 警告。原文在 `strict-openpi-client-install-retry1.log`。
- 下一验收点：从严格 OpenPI lock/cache 将这两个 client 闭包依赖以 symlink 安装到 strict bridge venv，`uv pip check` 与 `MemoryContext` smoke 必须通过；随后在 C1/C2/C3 空闲 GPU 依次运行固定 checkpoint 的 smoke mode（严格 runner 自动两条、episode 0 video / episode 1 no-video），检查完整产物、video、子进程退出及三树 clean。通过后才可登记单次 100 rollout。

## 即时状态（2026-09-11 17:12 +08:00）

- 17:06 所报 client 闭包缺口已消除：严格 OpenPI 已安装版本生成的 7 项局部闭包（`absl-py`、`attrs`、`dm-tree`、`setuptools`、`svgwrite`、`tree`、`wrapt`）已用 C1 shared uv cache 的 symlink 模式装入 strict bridge；`uv pip check` exit 0，真实 `openpi_client` + `MemoryContext` smoke exit 0。记录为 `strict-openpi-client-install-retry2.log`。此前 retry1 的失败原文仍保留，未将其标为可忽略。
- 严格 runner 的 `--prepare-audit` 已完成，固定 checkpoint 的 H50/K30、schema、输入审计与 manifest 均通过；C1 GPU1 的 `--dry-run` 已输出实际 robot/policy/scheduler 命令。记录：`strict-rollout-prepare-audit.log`、`strict-rollout-c1-smoke-dry-run.log`。
- **正在运行：无。** Manager 17:12 未见本任务安装/eval 进程是准确的：安装与 dry-run 已结束，实际 rollout 尚未启动。最新命令是 C1 的启动前门禁，确认 `GPU1=1 MiB`、无 compute app、目标 run leaf 不存在、strict 三树 clean；记录于本次 task records/终端检查。
- **当前阻塞：无。** 下一条已授权命令为从 strict RMBench 目录用 strict OpenPI Python 执行 `run_memory_schema_eval.py --variant put_back_full_t_plus_1 --checkpoint .../20000 --run-name put_back_full_t_plus_1_s0_20k_c1_smoke2 --gpu 1 --mode smoke`。该 runner 自动执行两条 accepted rollout：episode 0 video、episode 1 no-video。完成后先验收产物/服务退出/clean，再依次在 C2 GPU2 与 C3 GPU0 跑同协议 smoke；尚未进入正式 100。
