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

## 即时现场快照（2026-09-11 17:18 +08:00）

- **C1 真实 strict smoke 正在运行，未停止。** host `is-ddfwxekq6usner7v-devmachine-0`、GPU1，outer PID `70362`（17:13 启动，17:18 已存活 04:52），bridge `70572`、robot `70647`、policy `70648` 均存活；policy 已加载 `.../20000` checkpoint 并完成 robot/policy metadata 握手。实际命令为 strict RMBench 中 `run_memory_schema_eval.py --variant put_back_full_t_plus_1 --checkpoint .../20000 --run-name put_back_full_t_plus_1_s0_20k_c1_smoke2 --gpu 1 --mode smoke`。
- **当前真实阻塞：Curobo planner 每个 seed preflight 都因旧绝对资产路径失败。** `rmbench_sim_worker.stderr.log` 的最后 traceback 是 `FileNotFoundError: /mnt/public/xcj/Projects/RMBench/assets/embodiments/aloha-agilex/collision_aloha_{left,right}.yml`；该路径不存在，而 strict worktree 的 assets 在 `.../formal/strict-100/RMBench/assets/...`。scheduler 因而记录 `AttributeError: 'put_back_block' object has no attribute 'block'` 与 `ConnectionResetError`，目前 seed `100000–100005` 均 rejected、尚无 accepted rollout 或 video。
- 最近只读检查为 `ps -p 70362,70572,70647,70648`、目标 run 的 `seed_preflight.jsonl` 与 `processes/rmbench_sim_worker.stderr.log` tail；下一验收点是保留本次失败证据后，定位并采用已有 C symlink-vm GPU guard 的最小隔离路径修正，使 strict tree 不改动，再重新运行 C1 的固定 two-rollout smoke。未重跑已通过的 offline 安装/闭包审计，也未启动文档整理。

## 失败分类与 strict 门禁（2026-09-11 17:23 +08:00）

- C1 `put_back_full_t_plus_1_s0_20k_c1_smoke2` 不是有效 smoke：runner 将 worker 的基础设施崩溃包装成 `seed_preflight_failed` 后继续递增 candidate seed。已捕获的固定序列为 `100000–100019`，20/20 `accepted=false`，`episode_diagnostics.jsonl=0`、`video_checks.jsonl=0`，不能计为 rollout、不能替换或跳过严格 100 的对应种子。
- worker 首因已逐条复现：strict 旧版 `curobo_{left,right}.yml` 写死 `/mnt/public/xcj/Projects/RMBench/assets/...`，而 C 该旧路径不存在；Curobo 在 planner child 初始化时抛 `FileNotFoundError`。上层的 `AttributeError: 'put_back_block' object has no attribute 'block'` 和 `ConnectionResetError` 是其后续包装，非任务表现失败。
- 已保留整个失败 leaf 与 `records/strict-c1-smoke2-infrastructure-gate.json`（含 17:23 截面、PIDs、20 个 seeds、0 accepted、两份日志 SHA256）。为防继续扫固定对照种子，已对已核实属于此失效 run 的 outer/bridge `70362/70572` 及随后遗留的 robot/policy `70647/70648` 发送 `SIGTERM`；最终四 PID 均退出。没有停止任何其他进程。
- 门禁状态：`formal_eligible=false`，严格 100 未启动。下一步只处理这个机器路径兼容问题：先对照现有 C entrypoint 的临时 YAML/兼容路径约定，以 strict RMBench assets 建立可审计的外部 shim 或 runtime overlay（不改 strict 三树），随后从同一 `seed=100000` 重跑 C1 two-rollout；只有 0/1 两条 accepted、video/no-video 产物和子进程收尾都通过，才继续 C2/C3。

## C1 路径修正后重启（2026-09-11 17:28 +08:00）

- C-only 外部兼容软链已创建：`/mnt/public/xcj/Projects/RMBench -> .../workspace/2a879870-8dda-4613-a684-0ad48a5e86be/formal/strict-100/RMBench`；它仅满足旧 Curobo YAML 的绝对 assets 路径，不改 strict 三树。`records/strict-rmbench-legacy-assets-shim.json` 记录 target commit `3e69b1e` 和 YAML/collision/URDF SHA256；两份 YAML 均以 strict RMBench `.venv` 在 C1 GPU1 加载为 `cuda:0`，之后三树仍 clean。
- 新的固定-seed C1 smoke 已于 17:28 启动：run `put_back_full_t_plus_1_s0_20k_c1_smoke2_retry1`，outer PID `82805`，bridge `82986`，robot `83074`，policy `83075`，命令/预启动 GPU/strict commits 写入 `strict-c1-smoke2-retry1-launch.txt`。它会重新从 `seed=100000` 执行两条 accepted rollout；旧 leaf 的 20 条基础设施拒绝不会被续用。
- 17:29 观察：服务均存活、checkpoint/policy 尚在加载，driver 的 connection refused 仍是启动重试；新 leaf `seed_preflight.jsonl` 和 worker stderr 都为 0，尚无任何 acceptance/rejection，不能提前声称 smoke 通过。

## C1 retry 实际进展（2026-09-11 17:30 +08:00）

- 兼容路径生效后的第一个固定 seed 已验证：retry1 `seed_preflight.jsonl` 记录 `seed=100000, accepted=true`；这是对原 20 条基础设施 rejection 的直接反证。worker stderr 仅见 SAPIEN 的现有警告，没有旧 `FileNotFoundError`，真实 scheduler 已进入 episode 0，`ffmpeg` 正在写 `episode0.mp4`。
- 此时 `episode_diagnostics.jsonl` / `video_checks.jsonl` 仍为 0，episode 0 尚未结束；不能把 accepted preflight 当作 two-rollout PASS。C1 的 outer/bridge/robot/policy 均保持运行，下一验收点仍是 episode 0 video、episode 1 no-video、两条诊断和服务退出。

## C1 strict two-rollout PASS 与稳定 shim（2026-09-11 17:34 +08:00）

- C1 retry1 已完整结束并通过：preflight 固定为 `(episode0, seed100000, accepted=true)`、`(episode1, seed100001, accepted=true)`；两条 terminal status 均为 `success`。episode 0 写入 `episode0.mp4`（297,342 bytes、333 帧、video check `ok=true`），episode 1 的 no-video check 为 `enabled=false, ok=true`；`_result.txt` 已生成，任务进程与 19410/19412 端口均已退出。
- 依照 Manager 裁定，等 C1 停止后才处理 shim。`strict/assets` 与稳定 `state-vla/RMBench/assets` 已用递归 regular-file SHA256 与 symlink spelling 全量比对：346 entries、完全相同、manifest `12c45bfc94b606c7c4df515d11999bf2e689e4fd89e5dc09dc2265811e280fd8`；证据 `records/strict-vs-stable-assets-equivalence.json`。随后将 `/mnt/public/xcj/Projects/RMBench` 原子从 task strict tree 改指稳定 `/mnt/public/xcj/Projects/state-vla/RMBench`，记录 `strict-rmbench-legacy-assets-shim-switch.json`；strict tree 仍 clean。
- C2 GPU2 与 C3 GPU0 已只读确认空闲并能看到共享 strict tree/旧路径入口。下一步从稳定 shim 启动 C2 same fixed seeds 的真实 smoke；C1 retry1 是唯一有效 C1 smoke，先前 `...c1_smoke2` 仍是 20 条基础设施失败 leaf，显式不计入任何对照/正式结果。

## 三机真实 smoke 当前运行（2026-09-11 17:36 +08:00）

- C1 已 PASS 并结束；C2/C3 现已实际启动（均用稳定 shim、同一 strict commits、固定从 seed100000 开始）：C2 host `is-ddj72hiexddjfwo6-devmachine-0` / GPU2 / outer PID `3635` / run `put_back_full_t_plus_1_s0_20k_c2_smoke2`，17:35 启动；C3 host `is-ddj72jhhjdy7hiyj-devmachine-0` / GPU0 / outer PID `3631` / run `put_back_full_t_plus_1_s0_20k_c3_smoke2`，17:36 启动。
- 各自 prelaunch 记录（GPU idle、端口、leaf 不存在、三树 clean、stable shim target 和完整命令）分别为 `strict-c2-smoke2-{prelaunch-gpu.csv,launch.txt}`、`strict-c3-smoke2-{prelaunch-gpu.csv,launch.txt}`。两个结果 leaf、端口和 WARP cache GPU 子目录互不重叠；当前仅处于 model/service startup，尚未将 C2/C3 称为通过。

## C2/C3 已进入真实 rollout（2026-09-11 17:39 +08:00）

- C2 GPU2 与 C3 GPU0 均已通过 startup：各自 `seed=100000` 的 preflight 均为 `accepted=true`，真实 scheduler 正在执行 episode 0 并写各自 `episode0.mp4`。两端 worker 无 `FileNotFoundError`、`AttributeError`、`ConnectionResetError` 或 traceback；这在稳定 shim 下实际验证了 renderer/cuRobo/sim/policy 链路。
- 当前两端 `episode_diagnostics` 和 `video_checks` 仍未落盘，因此没有提前宣布 PASS。下一验收点仍是每机 episode 0 terminal+video check、episode 1 (`seed100001`) accepted+no-video check、`_result.txt`、所有服务退出及 strict 三树 clean。

## 三机 smoke PASS，strict 100 已登记启动（2026-09-11 17:45 +08:00）

- 三台有效 smoke 已全部验收：C1 GPU1 steps `333/381`、C2 GPU2 `333/381`、C3 GPU0 `330/322`；每机 `seed100000/100001` 均 accepted、2/2 terminal success、episode0 video check 与 episode1 no-video check 均 `ok=true`、`_result.txt=Success Rate 1.0`、对应服务/端口退出且 strict 三树 clean。逐机 SHA256 acceptance records：`strict-c1-smoke2-retry1-acceptance.json`、`strict-c2-smoke2-acceptance.json`、`strict-c3-smoke2-acceptance.json`。
- 已从本机原始 `put_back_full_t_plus_1_s0_20k_100ep/launch.json` 对照正式命令；C strict manifest 进一步实读为 `test_num=100`、`seed=0`、`eval_video_count=5`、`demo_clean_eval`、H50/K30。唯一正式 run 以原始名称 `put_back_full_t_plus_1_s0_20k_100ep` 于 C2 GPU2 在 17:44:55 启动，outer PID `9732`，smoke gate 为 C2 valid leaf。
- 长进程已登记 MAM job `c4dad7ca-84fc-4f6b-8a57-312178b35282`，host 使用可探测 SSH alias `wuwen-4090-2`（而非仅 C 内可解析的 hostname），状态 `running`。launch/prelaunch 记录：`strict-formal-100-{launch.txt,prelaunch-gpu.csv,driver.log,outer.pid}`。将首先检查 `seed100000`，到 50 条按固定顺序核对趋势/异常；任一 rejected preflight 均按基础设施门禁处理，绝不计入或静默跳过。

## 正式 100 即时现场（2026-09-11 17:48 +08:00）

- **正在运行**：C2 `wuwen-4090-2` GPU2 的唯一 strict formal run `put_back_full_t_plus_1_s0_20k_100ep`，outer PID `9732`、MAM job `c4dad7ca-84fc-4f6b-8a57-312178b35282` 均仍存活；robot/policy/worker 与 19420/19422 端口存活。稳定 shim 保持指向 `state-vla/RMBench`，未改活跃 strict tree。
- 已实读正式 leaf 原始 JSON：仅 `episode_id=0, seed=100000, accepted=true`；其 terminal diagnostics 为 `success`、333 steps，`episode0.mp4` video check 为 `ok=true`（333 frames）。worker stderr 未见旧绝对路径异常或 traceback，只有既有 SAPIEN warning。
- 当前尚未看到 episode 1 的 preflight/diagnostics/video record，100 条绝未完成；episode 0 scheduler 已以 `episode_terminal` returncode 0 退出，而 outer/服务仍在运行。我正在只读核查其是否处于下一集切换或存在活跃停滞，不做重启、跳 seed 或修改运行路径。
- 下一验收点是固定 `seed100001` 的 accepted preflight 与连续 diagnostics；任何 rejected preflight、非连续 seed 或 worker/基础设施 traceback 都将保留为 formal gate failure，不能计入结果。现场原始路径：`C:/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/put_back_full_t_plus_1_s0_20k_100ep/{seed_preflight,episode_diagnostics,video_checks}.jsonl`，driver：`workspace/2a879870-8dda-4613-a684-0ad48a5e86be/records/strict-formal-100-driver.log`。

## 正式 100 前两条门禁复核（2026-09-11 17:50 +08:00）

- 前一快照后已实证正常切换：`seed_preflight.jsonl` 连续两条且仅两条，`(episode0, seed100000, accepted=true)`、`(episode1, seed100001, accepted=true)`；两条 terminal diagnostics 均为 `success`，无 rejected preflight。
- episode 0 为 333 steps、video `ok=true`/333 frames；episode 1 为 terminal success、no-video check `enabled=false, ok=true`。两次 scheduler 均以 `episode_terminal` returncode 0 收尾，outer/robot/policy/worker 继续存活以执行后续固定序列。这一切换不是基础设施停滞。
- 目前只计已落盘的 2/100；继续按原顺序观察，不重启、不挑选或跳过 seed。第 50 条将固定截面核对 accepted 连续性、success 趋势、failure categories、前五视频及 worker 状态。

## 正式 100 前五条视频门禁（2026-09-11 17:54 +08:00）

- 固定序列 `seed100000–100004` 已全部 preflight accepted，严格连续且 `rejected=[]`；五条 diagnostics 已落盘，结果为 3 `Success` / 2 `Fail`。
- 两个 `Fail` 分别为 episode 3/4（seed 100003/100004），均是模型任务终态 `button_not_pressed_after_center`、500 steps；它们不是 worker、renderer、cuRobo、RPC 或路径异常，已按正常表现失败保留在正式序列中。
- 前五条视频均存在且 `ok=true`（frames `333,381,357,500,500`），满足 formal 的前五视频要求；worker stderr 对 `Traceback|FileNotFoundError|ConnectionResetError|AttributeError` 匹配数为 0。正式 job/服务保持运行，继续固定顺序 100000–100099。
