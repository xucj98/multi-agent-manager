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
- episode 0 为 333 steps、video `ok=true`/333 frames；episode 1 为 terminal success，且**正式** `video_checks.jsonl` 记录为 `enabled=true, ok=true, frames=381`。此前将 C2 smoke 的 episode 1 no-video 结果误写为 formal，现已更正；两次 scheduler 均以 `episode_terminal` returncode 0 收尾，outer/robot/policy/worker 继续存活以执行后续固定序列。这一切换不是基础设施停滞。
- 目前只计已落盘的 2/100；继续按原顺序观察，不重启、不挑选或跳过 seed。第 50 条将固定截面核对 accepted 连续性、success 趋势、failure categories、前五视频及 worker 状态。

## 正式 100 前五条视频门禁（2026-09-11 17:54 +08:00）

- 固定序列 `seed100000–100004` 已全部 preflight accepted，严格连续且 `rejected=[]`；五条 diagnostics 已落盘，结果为 3 `Success` / 2 `Fail`。
- 两个 `Fail` 分别为 episode 3/4（seed 100003/100004），均是模型任务终态 `button_not_pressed_after_center`、500 steps；它们不是 worker、renderer、cuRobo、RPC 或路径异常，已按正常表现失败保留在正式序列中。
- 前五条视频均存在且 `ok=true`（frames `333,381,357,500,500`），满足 formal 的前五视频要求；worker stderr 对 `Traceback|FileNotFoundError|ConnectionResetError|AttributeError` 匹配数为 0。正式 job/服务保持运行，继续固定顺序 100000–100099。

## Formal video 与回传路径更正（2026-09-11 18:00 +08:00）

- 已从**正式** leaf 的原始 `video_checks.jsonl` 实读校正：episode 0–4 均为 `enabled=true, ok=true`（frames `333,381,357,500,500`）；episode 5–9 均为 `enabled=false, ok=true`。`config.yaml` 的实际 `eval_video_count=5`，与此一致。17:50 中把 C2 smoke 的 episode 1 no-video 结果误写到 formal 的表述已原位更正；formal episode 1 实际为 video `ok=true, frames=381`，不存在 smoke/formal 混计。
- 当前 active formal 仍在原 leaf `eval_result/memory_chunk_20260910/put_back_full_t_plus_1_s0_20k_100ep`，不移动、不改名、不改路径。完成且通过连续 100、诊断/视频/退出/clean 验收后，才归档到 C 的独立布局 `eval_result/cluster_c_eval_acceptance_20260911/put_back_full_t_plus_1_s0_20k_100ep`，再按相同 `eval_result/<exp-group>/<run>` 布局回传本机；绝不写入或覆盖本机既有 `memory_chunk_20260910` 的 69/100 baseline。
- 后续状态只在固定 50 条核对点、基础设施门禁变化或正式结束时发布，不逐集刷报。

## 三库 fresh 测量与 C 操作手册（2026-09-11 18:03 +08:00）

下表只计三条从全新路径运行 `*.local/create_worktree.sh BASE_COMMIT NEW_BRANCH WORKSPACE_ROOT` 的 exit-0 安装；目录大小按原始 `.metrics` 的不跟随软链统计，未使用 `du -L` 重计共享 cache。`filesystem delta` 是同一共享文件系统窗口差值，仅作占用观测。

| 库 / fresh base | 实耗 | worktree | `.venv` | filesystem delta | shared uv cache 增量 |
| --- | ---: | ---: | ---: | ---: | ---: |
| RMBench `6139577` | 149 s | 23,100,804 B | 13,870,683 B | 21,032,960 B | 2,308 B |
| robot-bridge `f0f585a` | 14 s | 5,714,735 B | 3,045,755 B | 5,554,176 B | 7,548 B |
| OpenPI `a869498` | 36 s | 11,628,322 B | 9,360,481 B | 9,650,176 B | 86,175 B |

- 原始测量：C `workspace/2a879870-8dda-4613-a684-0ad48a5e86be/records/current-{rmbench,robot-bridge,openpi}-fresh-create.{log,metrics}`；三条均记录 `uv_symlink=PASS`。RMBench 的历史离线解析/闭包和 bridge client 缺包恢复日志仍单列在同一 records，未计入上表。
- 稳定手册已实际写入 `C:/mnt/public/xcj/Projects/state-vla/README.md`（SHA256 `c7d45eec90b52bc0ed0cb972f21d46b84f3697b150a1429e919e0a5156dede5f`），内容含三机共享、三参数 worktree 命令、GPU 检查、smoke2→commit→formal、50/100 gate、独立 exp-group 回传和清理边界。写入前已从三份 `.metrics` 逐项校验表中五项数字；不触碰 active strict tree。
- 正式结果说明将在独立 worktree `C:workspace/2a879870-8dda-4613-a684-0ad48a5e86be/docs/rmbench-formal-record`、branch `task/2a879870-8dda-4613-a684-0ad48a5e86be-c-formal-record`（base `3e69b1e`）完成，避免修改活跃 strict worktree。

## Formal 100 基础设施门禁失败（2026-09-11 18:14 +08:00）

- 唯一 C2 strict formal leaf 在达到 50 条前异常结束，outer `9732`/MAM job 已停止，runner exit 2。它**不是** 100/100 结果，不能归档到 `cluster_c_eval_acceptance_20260911`、不能回传为成绩，也不能与本机 69/100 比较。
- 原始 `seed_preflight.jsonl` 有 23 条：episode 0–21 / seed `100000–100021` 连续 `accepted=true`；episode 22 / seed `100022` 的 `accepted=null`、`response.status=error`，原文为 `RMBench worker 'reset' failed: RPC failed (EOFError: worker closed the RPC stream during a frame)`。该 seed 不能静默跳过或用后续 seed 替换。
- 22 条有效 terminal 中为 14 success、8 正常任务失败（`button_not_pressed_after_center=6`、`button_press_insufficient=2`）；episode 22 的 `accepted_reset_error` 是基础设施记录，不能纳入这 22 条或称为任务失败。前五视频与 5 后 no-video records 均通过，但不足以使此 leaf formal eligible。
- worker 在 episode 22 的 354 steps 后立即写入 svulkan2 `Your GPU driver does not support Vulkan` / `ErrorIncompatibleDriver`，随后 RPC EOF。没有 Python traceback；C host 可读 dmesg 未见 OOM/Xid；robot/policy 按 runner shutdown 退出、19420/19422 已关闭、GPU2 回到 4 MiB。三台已通过 smoke 的 worker log 均无该 svulkan2 error，因此不把它当作可忽略的固定 warning。
- 失败快照和 SHA256 已固化在 C `records/strict-formal-100-infrastructure-gate.json`（gate SHA256 `8e91aa33361c56250d9508217abee45725cdd98db4269b819256aa1507c1f825`）及同前缀的 preflight/diagnostics/video/process/worker/stdout 副本。`formal_eligible=false`；strict 三树、稳定 shim、失败 leaf 均未改动。
- 下一步是只读定位 renderer/worker 生命周期的首因，采用不改 strict 源码的最小 C 环境门禁后，从**新 leaf**重启固定 `100000–100099`；在新的 run 前 50 条有效健康检查通过前，不修订当前验收专属文档或移动任何结果。

## C2 renderer/RPC 复现门禁（2026-09-11 18:30 +08:00）

- 当前没有活跃 formal：原 C2 叶已按 infrastructure gate 保留，不能产生 50 条健康截面；README 的定向修订继续延后到新的 formal 前 50 个已完成 episode 的健康切片之后。
- 只读源码确认 strict worker 的每次 `reset` 都会调用 task `setup_demo`；RMBench `Base_Task.setup_scene()` 每次都会创建 `sapien.SapienRenderer()`。失败正发生在 episode 22 的下一次 reset/renderer 创建，非模型终态。
- C2 的系统 NVIDIA ICD 实际位于 `/etc/vulkan/icd.d/nvidia_icd.json`（API `1.3.277`），而 SAPIEN 3.0.0b1 只自动检查 `/usr/share/vulkan/icd.d`，于是此前 worker 落到内置 ICD（API `1.2.140`）；前者已在同 GPU 的独立 renderer+scene 初始化中通过。该差异是当前假设，尚不声称已修复根因。
- 已在空闲 C2 GPU2 启动独立 gate，outer PID `63260`：严格 RMBench/bridge 原树、正式 `demo_clean_eval` config、连续 seed `100000+` 的 **40 次**真实 worker reset 生命周期，显式 `VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json`，专用 WARP cache、无 policy、无 result leaf。源树及失败 leaf 均不改；原始命令、GPU preflight、逐 reset JSON 和 stderr 分别保存在 `C:workspace/2a879870-8dda-4613-a684-0ad48a5e86be/records/strict-c2-renderer-gate-*`。
- 下一验收点是超过旧 episode-22 故障点的 40/40 accepted、无 svulkan2 incompatible-driver/RPC EOF、进程退出与 GPU 回收。仅该门禁通过后，才会以**新 leaf**从 seed `100000–100099` 启动新的严格 formal，并在前 50 个已完成 episode 取切片检查（不要求文件实时恰为 50 行）。

### Renderer gate retry1（18:32 +08:00）

- 上一 gate 的 PID `63260` 已自行退出，原因是我在直调 worker 时漏设 controller 原有的 `cwd=RMBench`，导致相对 `assets/objects/objaverse/list.json` 不存在；这是 **gate harness 配置错误**，不是 formal、模型或 Vulkan 结论，原 log/JSON 完整保留。
- 已以 controller 的真实 cwd、同一 strict roots 和同一 C2 GPU2 重启 retry1，outer PID `63504`；仍为 40 次 reset、系统 ICD、独立 cache/无 result leaf。此 retry 才是当前运行中的门禁。

## 运行边界更新与稳定手册修订（2026-09-11 18:45 +08:00）

- Manager 已明确：40 reset 只验证 renderer/worker 生命周期，绝不替代新环境下的 policy smoke2。gate 通过后依次执行 C2 系统 ICD 环境的完整 video/no-video smoke2，再从新 leaf 固定 `100000–100099` formal；任一再次基础设施异常保留首因并停止，不循环 100。
- retry1 当前已完成 11/40 个连续 accepted reset，尚无 `ErrorIncompatibleDriver`、Vulkan、RPC EOF、traceback 或路径错误；继续运行。它不写 evaluator result leaf，也不改变 strict 三树。
- 按最新指令，稳定 `C:/mnt/public/xcj/Projects/state-vla/README.md` 已先行定向修订为 90 行通用手册：task 参数替代旧固定 commits、明确 MAM 本机与 SSH C1 创建/C2-C3 运行、说明旧 client 不由三条建树命令自动复现、把当前验收细节留给实验说明，并将 50 中检改为前 N 个已完成 diagnostics 的切片。前/后 SHA256 为 `c7d45eec...dede5f` → `1bafbae2...74276`；任务 records 的 `state-vla-README-targeted-revision.json` 六项检查均通过。

## C2 renderer 生命周期门禁失败：停止新 rollout（2026-09-11 18:46 +08:00）

- **当前运行：无。** C2 GPU2 已回到 4 MiB、无本任务 compute app；没有启动新的 system-ICD smoke2 或 formal，也没有改动 strict 三树、稳定 shim、原 formal leaf。
- retry1 在严格 worker 的真实 `cwd=RMBench`、`CUDA_VISIBLE_DEVICES=2`、`SAPIEN_RENDER_DEVICE=cuda:0`、显式系统 `VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json` 下，连续完成 episode/seed `0–21` / `100000–100021` 的 22 次 accepted reset。随后的 episode 22 / seed `100022` 在 worker 返回前再次写出 svulkan2 `Your GPU driver does not support Vulkan` / `ErrorIncompatibleDriver`，`timeout` 报 core dump；这与旧 formal 的 22 条完成后 episode22 reset RPC EOF 是同一生命周期边界。
- 因此“C2 自动选择 bundled ICD”不是充分修复；已证实的近因是同一 strict worker 进程的反复 RMBench/SAPIEN renderer 生命周期在第 23 次 reset 崩溃。尚不能把 C++/driver 内部机制断言为已修复。该 test 无 policy、video 或 evaluator result leaf，22 条 reset-only 既不计分，也不与旧 formal 的 22 terminal 结果拼接。
- 失败门禁已固化为 `C:workspace/2a879870-8dda-4613-a684-0ad48a5e86be/records/strict-c2-renderer-gate-retry1-infrastructure-gate.json`，SHA256 `6366eec49d0707f65ca4a542d6f01a9ec65c23205c8502bd2fe661186af0aea3`；原始 log SHA256 `a341ea81afac56a23b4e9d60d63574d52c3d44296f35bf8e67afe5ec9f391b4c`。C2 当前 dmesg 读取被拒、`coredumpctl` 不存在、core 由 apport 接管；这些可用性限制也已写入门禁。
- 按 Manager 边界，**不循环 100**。后续需先对该 renderer 生命周期崩溃作环境/运行时级首因裁定；在此之前 `smoke_eligible=false`、`formal_eligible=false`，50 条中检不存在。

### 有界 cache-cleanup 根因验证已启动（18:50 +08:00）

- 基于 strict 源码差异，C2 GPU2 当前只运行隔离 diagnostic（outer PID `106978`）：同一 25 次 worker reset 生命周期、同一系统 ICD、无 policy/no-video/no result leaf；每 5 次在已关闭的 env 边界调用原 RMBench 已有的 `sapien.render.clear_cache()`。
- 目的仅验证 `clear_cache_freq=5` 在原 evaluator 中存在、但 strict bridge worker 固定 `clear_cache=False` 是否解释第 23 次 renderer 崩溃。它不修改 strict 源，也不会作为 smoke/formal 运行方式或准入依据；结束后记录精确 exit code、日志和结果，再由 Manager 决定是否接受任何后续运行时修复路径。

## Renderer gate 与 CPU-only 分段测量快照（2026-09-11 19:06 +08:00）

- C2 的隔离 `clear_cache_freq=5` 诊断已自行退出 `139`，不是 smoke/formal：同一严格 worker、system ICD、无 policy/result leaf 下，episode/seed `0–18` 的 19 次 reset 均 `accepted=true`，并在每第 5 次关闭后的边界实际调用已有 `sapien.render.clear_cache()`；下一次 renderer 创建仍写出 `ErrorIncompatibleDriver`，随后 `timeout: ... core dump` / `Segmentation fault`。这说明该清理候选在此 harness 中**不足以**消除生命周期崩溃，不能据此改严格运行方式或启动新 smoke/formal。原始 `strict-c2-renderer-cache-gate.{log,exit,launch.txt}` 已保留；退出时 exit 文件为 `139`，未触碰失败后 GPU 上来源不明的残余占用。
- 149 秒问题的 CPU-only profile 已在 C1 以原始入口、同一 `6139577`、同一离线锁和 shared warm cache 启动，且 `CUDA_VISIBLE_DEVICES=`；私有路径为 `workspace/2a879870-8dda-4613-a684-0ad48a5e86be/profile/rmbench-walltrace`，唯一 branch 为 `task/2a879870-8dda-4613-a684-0ad48a5e86be-c-profile-rmbench-walltrace-20260911`。外部 trace 已分别记录 wrapper 预检、git checkout、每个 uv、两次 symlink/rglob 校验与收尾，原 installer 未改。
- 目前该 profile 的全部 uv 安装阶段已完成，managed installer 的第一个 symlink probe 已输出 `symlink=PASS`；原入口正运行其随后 wrapper-level `sorted(venv.rglob("*"))` 验证，尚未退出，因此尚不发布分段归因或占比。退出后会先完成 task 自建 worktree/branch 清理，再从 raw trace 给出实测分段与未解释 residual，不凭猜测优化。

## CPU-only 149 秒分段 trace 完成、C2 cache-cleanup gate 终态（2026-09-11 19:15 +08:00）

- C1 的任务私有 profile 已按原始入口 `RMBench/.local/create_worktree.sh`、同一 base `6139577` 和同一离线锁完成，`CUDA_VISIBLE_DEVICES=`，installer exit `0`；没有修改 strict tree、算法或包版本。UV artifact cache 是已复用状态、未清理/传输，但没有把 filesystem metadata 称为 warm。此轮 creation 墙钟为 **151.783 s**，只是一轮带外部时间戳的复测，不替代原 149 s 数字。
- 实测分段：`uv --version` + `uv venv` + 五次 pip subprocess 为 `45.060 s`；五次 pip 为 `44.894 s`，其自身 `Installed` 计时合计 `43.060 s`，命令边界外差额 `1.834 s`。`git worktree add / checkout` 为 `3.093 s`，非-uv 预检为 `2.390 s`，shared links 为 `0.355 s`。
- 实际主要占比是两个**未改动的原入口** symlink 校验 Python subprocess：managed installer 的 `sorted(venv.rglob("*"))` 为 `80.486 s`，C wrapper 的同类验证为 `20.348 s`，合计 `100.834 s / 66.4%`。这与 Manager 对已存在 venv 的两次暖重扫 `9.8 s` 是不同状态下的观测；本 trace 只证明这次新建树入口时的实测边界，不臆断两者差异的根因，也未据此优化流程。
- raw evidence 位于 C `workspace/2a879870-8dda-4613-a684-0ad48a5e86be/records/rmbench-walltrace-20260911/{events.tsv,bash-debug.tsv,installer.log,manifest.txt,summary.json,summary.md}`；raw SHA256 写入 `summary.json`。profile worktree、branch、profile parent 和 managed 临时 installer 均已验证 absent。清理的 `git worktree remove` 耗 `46.283 s`，单列在 summary，未混入 creation 指标。
- C2 的 bounded cache-cleanup diagnostic 已终态 `exit=139`：25 次请求中 `0–18` / `100000–100018` 的 19 次 reset accepted，已有 `clear_cache()` 实际发生在 episode `4,9,14`；随后未记录下一次 acceptance 即再次出现 svulkan2 `ErrorIncompatibleDriver`、core dump 和 `Segmentation fault`。因此该候选不足以消除生命周期问题；它没有 policy 或 result leaf，不能作为 smoke/formal。退出后 GPU2 为 4 MiB、无 compute app，三个 strict tree clean。
- 新 gate receipt 为 C `records/strict-c2-renderer-cache-gate-infrastructure-gate.json`，SHA256 `fc49aba51a9a41a516ec888c005d8973ac4def7da31d09b97f46394dd84ee950`；保留 raw log/exit/launch hash。按已发布边界，不再自动启动 C2 新 smoke 或 formal，等待独立的 renderer 根因裁定。

## 恢复执行阶段（2026-09-12）

- 已读取最新 Resume 裁定。复用原 failed-22/system-ICD/cache-cleanup 三份证据与全部环境，未重传或重建 renderer 环境。
- renderer 最小候选为 RMBench `envs/_base_task.py` 8 insertions/1 deletion：进程内保留一个 SapienRenderer，scene/physics/camera 设置仍在原 setup_scene 重建。独立本机树 `workspace/2a879870-8dda-4613-a684-0ad48a5e86be/RMBench-renderer`、C 树 `state-vla/workspace/2a879870-8dda-4613-a684-0ad48a5e86be/diagnostic/renderer-reuse/RMBench`，branch `codex/2a879870-renderer-lifecycle`，base `3e69b1e`。
- C2 GPU2 的原 bounded harness 已实际启动 40 reset，PID 144583，记录 `records/renderer-reuse-20260912/{launch.json,driver.log,result.json,exit}`；使用原 strict Python/bridge，candidate RMBench cwd，system ICD。等待跨越旧失败点；此为诊断，不作为 smoke/formal，未宣称协议等价已实证。
- 创建优化已在现有 RMBench task worktree及 C .local 提取 installer 边界准备：两处 sorted(rglob) 改为惰性 rglob，保持“至少一个可解析至配置cache内的真实软链”的原判定；不写 venv 链接或覆盖私有文件。CPU-only fresh 创建/空间/清理 PID 130867 已启动，证据 `records/create-lazy-probe-20260912`。

### Renderer 候选可审阅，诊断继续运行

- 本机独立 branch `codex/2a879870-renderer-lifecycle` 已提交候选 `17b55bf`（base `3e69b1e`，仅 `envs/_base_task.py`）。最小 patch 位于本机 `.tasks/2a879870-8dda-4613-a684-0ad48a5e86be/renderer-reuse.patch`；Manager 可据此安排独立源码 review，runtime gate 尚未完成，不提前判定修复成功。
- 澄清首个启动 `renderer-reuse-20260912` 的 supervisor 出现字符串换行 SyntaxError，未进入 sim，原日志保留。已在新目录 `renderer-reuse-20260912-retry1` 以 PID `144614` 启动原40-reset harness，实际已开始导入sim环境；活跃源码未再改。
- `close_env()` 未释放 Gym Env 的 scene/robot/viewer 引用是源码观察；本候选验证的是 renderer context 跨场景持有是否有效，并未把 GPU driver 报错当成已解释的完整根因。源码 AST 只在 setup_scene 改动；行为等价仍需实际 smoke 验证。review 重点包括进程级 context 生命周期、串行 worker 范围及 scene 重建参数保持。

### 创建优化完成（CPU-only，2026-09-12）

- 本机 RMBench task branch 提交 `9c71a3e`：存在性probe改为惰性 rglob。C .local wrapper及提取后installer同步最小patch，备份/diff在 `records/create-lazy-probe-20260912`。原本两处保证仅为“至少存在一个strict resolve后属于指定cache的链接”，不是全量闭包审计；现在同一判定在首个成功项停止。私有 overrides、link-mode、包版本不变。单元测试覆盖私有普通文件、外部/悬空链接、成功后不再消费遍历器；bash -n与diff检查通过。
- 一次同base `6139577`、复用UV artifact cache、CPU-only fresh实测 **52.926856684s / exit0**；两probe为 **0.203525066 / 0.102121115s**，前次未优化trace为151.783s/双probe100.834s。不同窗口共享FS测量，不宣称固定速度保证。
- worktree apparent **23,100,627 B**（含venv），venv apparent **13,870,506 B**；allocated分别 **51,438,080 / 41,802,240 B**。均du不跟随链接，禁止拿allocated与之前apparent混比。cache allocated窗口差 **+2,560 B**。GPU前后相同，无本任务GPU工作。
- profile源码clean；worktree/branch与profile parent均清理，清理 **47.305s** 单列、不混入creation。完整metrics/raw trace/安装日志/patch保留在C上述目录。本机可读summary及wrapper.patch镜像在本MAM `.tasks/2a879870-8dda-4613-a684-0ad48a5e86be/create-lazy-probe-20260912/`。

### 协议对照及登记

- C2 40-reset candidate gate 已登记 MAM job `1ee98405-a6e7-4936-8d78-96aef1d82232`，PID144614，便于外部观察终态；该job是诊断，不是正式100。
- C1 GPU1已确认空闲后启动同环境 base/candidate 顺序对照（PID132690），`records/renderer-protocol-20260912`。各2个固定seed100000/100001；基线保存50条保持初始qpos的诊断动作，candidate原样重放，双方均按原worker队列剩20的条件执行30条，保存前后qpos、三相机图像及状态。此synthetic诊断用于验证reset/动作队列/观察接口，没有替代模型policy smoke或正式结果。
- 下一阶段只在生命周期跨越旧故障点/终态、协议对照完成或异常时汇报；已准备源码与创建优化review材料，formal仍须Manager review与真实smoke门禁。
