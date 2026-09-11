# retry1 实际执行失败（2026-09-11 08:04）

按 Manager 新授权，从干净固定 bridge `124049fb78d29db1d77d13a9fd4a4b698fcfe6e9` / OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` 使用 GPU2、端口19580/19582启动原入口。源码/解释器握手、频率/H/K门禁均通过。full 首个推理结果在 execute RPC 被拒绝：`Memory v1 prediction IDs must be integers`。未完成任何 episode，0执行action行，serial未启动，无可报告的完整action/phase指标。

首因已用无GPU CPU探针确认：`robot_bridge/robot/controllers/base.py:205` 的 handle_execute 对 actions 所有值统一 np.asarray(dtype=float32)，将 scheduler 原有 int32 memory_prediction_ids、int64 memory_model_rows 和整数 query index 全部转为 float32（query变为0维数组），随后 offline controller 的整数契约拒绝。此前直接调用 execute 的CPU测试绕过了该handle入口；实际RPC暴露了该测试缺口。证据 execute_dtype_probe.json 保留字段dtype/shape。

产物目录：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry1`，保留 launcher.log/launcher_exit.json、provenance、served_metadata、checkpoint metadata、config及exit。full/0/exit.json=1，policy_exit.json=-15且shutdown_requested=true（退出清理）；GPU2已恢复1MiB/0%，19580/19582无监听，两库源码未改。

停止后未重试、未覆盖产物。建议 Manager 裁定最小接线修复：在既有execute marshalling入口保持语义ID/行索引整数与query标量契约，同时保持机器人浮点action行为；补通过 handle_execute/真实传输入口的CPU回归，而非只调用execute。该项涉及此前限定之外的controller/base，故本轮仅定位并报告，不擅自修改。正式双模型5ep验收仍未通过，更不代表真机效果或架构重构完成。

以下为此前修复和首轮失败历史。

# 07:45 裁定小修交付：待 Manager 复核

新 bridge commit：`124049fb78d29db1d77d13a9fd4a4b698fcfe6e9`，基于固定 `fda269c1`；原 workspace 干净保留，OpenPI 未改。仅修改 launcher 及必要测试/fixture，无架构重构、无 controller/scheduler 修改、无 GPU 重试。

`_validate_served_metadata` 对 Memory v1 从 `memory_config.protocol.execution.rows` 验证实际运行 K，与 scheduler._move_steps 及 manifest execution_rows 一致；保持模型频率/H 校验。顶层采样 query_stride 缺失或 None 时不将其当成 K 缺失；若提供则单独按 manifest 采样 stride 校验，不要求其等于 K。legacy 原 query_stride 门禁保留。schema K 与实际调度/manifest K 冲突仍拒绝。

首次真实 served_metadata 的顶层 query_stride 是缺失字段，先前错误文本的 None 是 metadata.get 的结果。已将真实文件的 policy_hz/action_horizon/memory_config 投影作为 `tests/launcher/fixtures/wash_full_20k_timing.json`（保留缺字段原状），避免合成 fixture 再次漏掉真实情况。

CPU 验证：launcher 定向测试 18 passed；ruff E/F、git diff --check 通过。测试覆盖真实缺字段/None、采样 stride7 与执行K30可共存、已提供采样stride冲突、schema/manifest/scheduler K冲突、频率/H冲突和旧drawer规则。另直接读取首轮完整 served_metadata 与未修改的 wash manifest 调用门禁，CPU PASS；未加载模型。

复测：`CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q tests/launcher/test_offline_preflight.py`。

等待 Manager/指定验收任务复核与通知后再用 GPU2。重试输出固定为 `/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry1`，原失败目录保留首因/命令/metadata，不覆盖。尚无正式offline指标或真机效果验证；今日真机交付需另给明确模型/代码路径及限制。

以下为首轮失败与此前交付历史。

# 正式 offline 首次启动失败（2026-09-11 07:40）

Manager 授权后从固定干净 bridge `fda269c1f333dabdb5628c083a4dba3db0938333`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` 启动，GPU2 启动前 1MiB/0%，独立端口 19580/19582 空闲。原 launcher 顺序 wash_full/wash_serial，统一目录 `/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep`。

首因：full 真实权重加载和 source/interpreter provenance 握手通过后，episode 执行前 metadata 门禁拒绝 `Served metadata query_stride=None does not match manifest 30`。实际 policy_hz=15、action_horizon=50，memory_config.protocol.execution.rows=30、completion=synchronous_rows。没有 infer/执行行/指标产物，serial 未启动，不能宣称 offline 验收通过。

launcher 返回1；policy_exit.json 为 returncode=-15、shutdown_requested=true，属于失败后的服务回收。full/0/exit.json 原始 starting 状态保留，另保存 launcher_exit.json 说明失败发生在 iteration 前；launcher.log、served_metadata.json、provenance.json、checkpoint metadata/config 等首轮产物完整保留。退出后核查 GPU2 1MiB/0%，19580/19582 无监听。未修改源码，未覆盖输出、未重试。

恢复方案待 Manager 裁定：针对 Memory v1 使用已存在的 schema execution.rows 验证 K/stride；保留 legacy query_stride 校验，若同时有显式 query_stride 与 schema rows 则拒绝冲突。只小修 launcher 并加该真实 metadata 形状的 CPU 回归，经指定 reviewer 复查后以 Manager 指定的新输出位置恢复；不在原失败目录覆盖重跑。原 fda CPU/mock 验证未覆盖真实 checkpoint 缺失顶层 query_stride 的情形，此次真实启动已暴露该缺口。

以下保留此前代码交付记录；其中 checkpoint 尚未就绪的描述仅为历史状态，两个20k现已就绪。

# 交付报告（2026-09-11 05:45 CST；正式 GPU offline 待 Manager 调度）

## 实施范围

已在独立 worktree `/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/robot-bridge` 的分支 `task/b86b3d02-29f2-437a-a5e7-db427a7df96c` 完成公共 offline 入口和指标修复。新 wash-cup 单 phase full/serial（H50/K30）与既有 drawer 双字段配置共用同一 controller、scheduler 和 launcher；新增固定 wash 5 集 manifest（LeRobot index 0–4），保留既有 drawer 入口、真机反馈路径、process/exit/metadata 产物管理。

实现提交：`fda269c1f333dabdb5628c083a4dba3db0938333`（`fix(offline): gate actual policy source and reject timing conflicts`）。worktree 干净，保留给 Manager 安排独立 review；未自行 review、合并或部署。

## 关键决定

- checkpoint 的 `memory_config` 与 `openpi_client.memory_config.make_training_sample()` 是 action GT、memory target、时间语义和 availability mask 的唯一来源，避免训练、推理与 offline 各自定义 offset。
- S2M action 保持 `action_at_row` / offset 0；full 使用逐帧 `t+j+1`，serial 使用当前 query，没有额外移位。
- 仅对实际 drain 的 action 计分；NPZ 保存 action/memory prediction、GT、mask、query/source/model-row 和执行行。count 求和，accuracy 按 sample 或 transition count 加权。
- 从既有 `drawer_offline.py` 泛化为配置驱动的 `offline_replay`，没有复制 launcher 或另建 wash 专用调度器；legacy drawer payload 仍走原分支。

## 07:22 Manager 裁定修复

新提交 `fda269c1f333dabdb5628c083a4dba3db0938333`，基于首版 `3a364a6`。本次仅改 launcher、wash manifest 和定向测试，controller/scheduler 未改。

- P1：启动服务和创建正式输出前，使用 `--policy-python` 的 CPU 探针解析实际 `openpi.policies.policy_config` 模块位置、Git root/commit、解释器路径/prefix/version 和二进制 SHA256；不导入 policy_config，不加载模型。对实际 root 执行 Git clean 检查（包括 untracked 与 submodule dirty）。顶层 `source_commits.OpenPI` 与 `policy_runtime` 来自实际源码；checkpoint root 只记录路径，不充当源码身份。
- 握手后校验现有 served provenance 的 source root/module/commit 和 interpreter 字段，重新检查源码 clean/commit；任何缺失或不一致在 episode 前拒绝，沿用 ExitStack 回收 policy 服务。scheduler 的 shutdown callback 也提前到 metadata 验证前注册。
- P2：dataset 与显式 expected metadata/execution rows 同时出现且冲突时明确报错。wash 删除重复 expected 字段及 scheduler.move_steps，时序只由 dataset 声明并与 checkpoint 校验；旧 drawer 有效参数不变。
- 删除未使用的 `--replay` 任意选节，保留现有两种节自动识别、必要 root 映射及旧路径适配。没有新增配置格式或依赖快照框架。

定向 CPU 验证：`21 passed`（新增 launcher 失败保护测试、memory offline、legacy drawer、已有 policy provenance）；ruff E/F 和 git diff --check 通过。真实 wash/drawer dry-run 通过；实际独立 OpenPI 解释器探针确认模块来自本任务 OpenPI worktree，commit `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，clean 检查通过。测试包含 dirty 源码拒绝、root/commit/module/interpreter/binary 握手不符拒绝、episode 前拒绝并回收 policy、三种 metadata 时序冲突及 execution rows 冲突。

复测命令（bridge worktree 根）：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONPATH=../openpi/packages/openpi-client/src .venv/bin/python -m pytest -q tests/launcher/test_offline_preflight.py tests/robot/controllers/test_memory_v1_offline.py tests/robot/controllers/test_drawer_offline.py tests/policy/test_openpi_provenance.py
```

本轮 CPU 修复已完成，等待 Manager 交原独立 reviewer 复查；GPU offline 仍须 Manager 明确授权及 checkpoint 门禁通过。

## CPU 验证

- 相关完整套件：`49 passed, 1 skipped`，覆盖新 full、serial、多字段、缺失 mask、canonical S2M action GT、scheduler 转发、memory feedback、旧 drawer 和 transform/metadata 契约。
- `ruff check --select E,F`、`py_compile`、manifest JSON 校验和 `git diff --check` 均通过。
- 新 wash 真实 5 集无 GPU dry-run 通过：15 Hz source-frame sidecar 映射与 query 数为 1216、1509、702、1115、983；两个预定 checkpoint 均如实显示 `ready: false`。
- 既有 drawer manifest 的无 GPU dry-run 也通过，固定 episode `[1,22,23,24,26]`、15 Hz / H30 / K15 与两个既有 checkpoint 路径保持可用。

## 预计剩余时间与 07:27 安排

接口实现、CPU 门禁和提交已于 05:44 完成，剩余实现时间为 0；原版之后已按 07:22 裁定完成上述小修；安排 wash offline 需原独立 reviewer 复查通过，不省略该门禁。

正式 offline 仍需训练产物出现后由 Manager 分配 GPU。固定输入共 5,525 个逻辑执行行 / 模型；K30 对应各集 41/51/24/38/33 次 infer，共 187 次 / 模型（最终以实际日志验证），正式运行会评估 full 和 serial 两个模型；没有在本轮加载模型或占用 GPU，故不把未经测得的 GPU 吞吐时间写成 ETA。启动前先重跑同一 dry-run 确认两个 `20000` 目录转为 `ready: true`。

正式命令草案（**不要在本 task 中自行启动**；由 Manager 在已分配 GPU 后执行，替换输出目录名）：

```bash
cd /mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/robot-bridge
PYTHONPATH=/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/openpi/packages/openpi-client/src \
  .venv/bin/python scripts/launch/drawer_offline.py \
  --manifest configs/input_manifests/wash_cup_memory_v1_offline5.json \
  --raw-root /mnt/public/datasets/x1pro/wash-cup \
  --checkpoint-root OpenPI=/mnt/public/xcj/Projects/openpi \
  --policy-python /mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/openpi/.venv/bin/python \
  --output /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_5ep_RUN_ID
```

桥接 worktree 的 `.venv` 未安装 light `openpi_client`，所以该 `PYTHONPATH` 是命令的一部分；policy 进程继承 Manager 的 GPU 分配环境。

## Manager 裁定与外部前提

当前没有需要 Manager 裁定的实现阻塞，也未发现需要改变算法或大规模重构的证据。

唯一外部前提是两个预定 wash 20k checkpoint 目录当前尚不存在。这不阻塞本次代码交付，也不请求现在预留 GPU；若 07:27 时目录仍未出现，正式 offline 将因训练产物尚未就绪延后，而不是以未完成接口验收替代。
