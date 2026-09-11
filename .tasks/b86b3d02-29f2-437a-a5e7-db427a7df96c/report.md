# 最终文档与清理交付：准备由 Manager 合并归档

RMBench 新交付commit `6139577e360c27f866e4dbb3dd2fc067cc7ddd50`，基于创建时当前xcj-dev `f94fb475458be193d525e984749b204063025023`；独立workspace `/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/RMBench`。仅修改 `experiments/memory_chunk_20260910/EXPERIMENT_LEDGER.zh-CN.md` 和该组 `README.md` 导航，未修改active sim源树、源码或其他sim结果。

台账更新两wash模型实际20k保存与训练验收、稳定训练日志/checkpoint路径、正式retry2各5ep指标及汇总、实际执行query计数口径、source/退出/释放证据；明确full逐行与serial逐query不可直接排名、训练内回放非泛化或闭环成功率。两次失败以独立历史小节记录首因、完整commit和参数化历史命令，不计入成功结果。

检查：新增13处文档路径链接均存在；表格数据来自正式artifact_audit.json；git diff --check通过；新RMBench环境CPU基础import通过（未运行GPU/render smoke，文档收尾无需GPU）。三个worktree均干净：bridge `dd0914b170fe5d227f24d36b07d90c0e422b7e58`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`、RMBench如上。

Git失败记录提交后，已删除共享eval_result/memory_chunk_20260910下 `wash_memory_v1_20k_offline5ep` 与 `wash_memory_v1_20k_offline5ep_retry1` 两个诊断完成的失败目录，逻辑大小208481577 bytes（约198.82 MiB）。已清理本task三worktree共25处__pycache__/pytest/ruff缓存，不跟随共享软链接、不删除.venv或共享缓存。正式retry2原有443文件SHA256前后一致，原数据和两份共享checkpoint保留。清理回执：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry2/final_cleanup_receipt.json`。

当前正式结果唯一入口：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry2`，稳定模型路径见Git台账。历史report/命令的task workspace仅是当时运行留痕，不是归档后的部署入口；未来运行应由Manager另建对应固定commit环境。下方历史报告中“失败目录保留”和workspace交接描述已由本段收尾覆盖。

本task实现、独立复核、正式offline、文档和清理均完成，无在跑进程或剩余实施项；未自行合并或归档，worktree保留供Manager合并验收后归档。

以下保留成功运行与历史交付记录。

# GPU2 retry2 正式 offline 完成（2026-09-11 08:41:34–08:44:06 CST）

依据08:40准入，从原干净固定bridge `dd0914b170fe5d227f24d36b07d90c0e422b7e58` / OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` 执行，同一GPU2顺序full→serial各固定5ep[0..4]。launcher用时151.29秒、退出0；10个episode exit均0。两个policy exit=-15、shutdown_requested=true，是launcher完成后的主动回收。未改源码、未改训练、未合并部署。运行小于1小时，未登记长job。

产物根：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry2`。每集config/exit/metrics/NPZ/JPG齐全；每模型checkpoint路径、训练/转换metadata及hash、policy命令/日志、served_metadata、policy_exit均保留；顶层provenance记录真实源码/解释器、manifest、命令。`artifact_audit.json`及`audit_artifacts.py`保存本次产物核验结果和可复跑检查，`resource_release.json`保存回收结果。

启动前GPU2=1MiB/0%、19580/19582无监听，两真实checkpoint dry-run ready；启动时clean和真实policy源码/解释器握手、15Hz/H50/K30门禁全部通过。结束后两库仍干净，GPU2=1MiB/0%、两端口无监听，/proc按实际argv检查无本run launcher/policy进程。

每模型执行行依次1216/1509/702/1115/983，共5525；实际NPZ执行记录中的唯一query依次41/51/24/38/33，共187。该计数来自真实已执行产物，不是把逻辑行数当infer次数；原policy日志没有逐请求计数器，未声称额外的独立服务计数。所有query/model row/执行游标与K30及尾部一致。检查action/GT有限、形状正确，memory整数ID与bool mask正确；从NPZ重新计算action MAE、phase有效计数/accuracy与metrics一致；继承metadata各文件hash及served身份与启动探针一致。

| 模型 | ep | 执行行 | 推理query | action MAE | phase accuracy | 有效phase样本 | transition accuracy（数） |
|---|---:|---:|---:|---:|---:|---:|---:|
| wash_full | 0 | 1216 | 41 | 0.03604275 | 98.903879% | 1186 | 75.00%（4） |
| wash_full | 1 | 1509 | 51 | 0.01466552 | 99.930556% | 1440 | 100.00%（5） |
| wash_full | 2 | 702 | 24 | 0.01417364 | 97.740964% | 664 | 60.00%（5） |
| wash_full | 3 | 1115 | 38 | 0.02179482 | 99.884125% | 863 | 80.00%（5） |
| wash_full | 4 | 983 | 33 | 0.02070949 | 99.777778% | 900 | 80.00%（5） |
| wash_full 汇总 | — | 5525 | 187 | 0.02182205 | 99.366713% | 5053 | — |
| wash_serial | 0 | 1216 | 41 | 0.04609120 | 100.000000% | 39 | 100.00%（4） |
| wash_serial | 1 | 1509 | 51 | 0.02273091 | 100.000000% | 47 | 100.00%（5） |
| wash_serial | 2 | 702 | 24 | 0.02053581 | 100.000000% | 22 | 100.00%（5） |
| wash_serial | 3 | 1115 | 38 | 0.03005073 | 100.000000% | 30 | 100.00%（5） |
| wash_serial | 4 | 983 | 33 | 0.03278577 | 100.000000% | 31 | 100.00%（5） |
| wash_serial 汇总 | — | 5525 | 187 | 0.03085954 | 100.000000% | 169 | — |

汇总action按执行行加权，phase按有效样本加权。full按实际drain逐行评估、serial按query评估，且availability/边界mask会排除无效目标；5053与169不能当作同一采样粒度直接比较。GT仅评分，模型反馈按既定memory配置。固定5ep属于既定数据集，不是新划分的泛化测试；本结果是offline动作/phase指标，不是闭环成功率或真机实验效果，也不代表原始scheduler架构重构完整完成。

真机交接代码路径：bridge `/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/robot-bridge`；OpenPI为同级`openpi`，commit如上。本轮未启动真机或更改其部署。模型路径：
- wash_full: `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_full_current_feedback/memory20k_ad6bb77e_wash_full_s0/20000`
- wash_serial: `/mnt/public/xcj/Projects/openpi/checkpoints/pi05_x1pro_wash_cup_s2m_serial_lag30/memory20k_ad6bb77e_wash_serial_s0/20000`

实际命令（原run已存在，禁止覆盖重跑）：

```bash
CUDA_VISIBLE_DEVICES=2 PYTHONPATH=/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/robot-bridge:/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/openpi/packages/openpi-client/src \
/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/robot-bridge/.venv/bin/python scripts/launch/drawer_offline.py --manifest configs/input_manifests/wash_cup_memory_v1_offline5.json --raw-root /mnt/public/datasets/x1pro/wash-cup --checkpoint-root OpenPI=/mnt/public/xcj/Projects/openpi --policy-python /mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/openpi/.venv/bin/python --policy-port 19580 --robot-port 19582 --output /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry2
```

前两次失败保留原始日志、命令、metadata/provenance、exit和dtype探针，只删除两处已不用的raw input软链接视图，不动原始数据；清理清单为`failure_temp_cleanup.json`。本次无实现阻塞、运行及回收完成，供Manager验收及后续文档/台账整合。

以下保留历史报告；旧待准入/失败状态已由上述结果更新。

# 08:12 RPC 最小接线修复交付：CPU 集成通过，待 Helmholtz 独立复核

交付 bridge commit：`dd0914b170fe5d227f24d36b07d90c0e422b7e58`，基于 `124049fb78d29db1d77d13a9fd4a4b698fcfe6e9`；原 workspace `/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/robot-bridge` 已提交且干净。OpenPI 仍为 `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，本轮未修改。

仅改 offline controller 和必要测试（2文件，controller +16行）：Memory v1 的局部 handle_execute 保留 prediction IDs、model rows 的整数数组与 query 整数标量，交现有 execute 严格校验；机器人 arms/phase 仍转换 float32。未配置 Memory v1 时委托原 base handler。没有修改通用 base、server、scheduler、launcher 或模型代码，没有浮点截断为整数来接受错误请求。

真实 CPU 集成使用 localhost WebSocket/codec、实际 policy server、RobotServer、scheduler 与 offline handle_execute，fake policy 仅替换模型推理。full/serial 各连续完成两集（共4集），每集8行，H4/K3按3+3+2执行；各模式6次infer、2次policy reset，最终dataset_done/stop且队列idle。断言RPC后的int32 prediction IDs、int64 model rows、Python int query和float32 arms；核对每条实际drain action与canonical GT（MAE=0）、memory prediction/GT/availability mask、有效样本数与phase accuracy、反馈缓存、尾部与下一集reset，确认GT/target未进policy观测。

同一真实RPC链路另发送4种非法输入（两模式均测）：非整数prediction IDs、非整数model rows、浮点query、0维浮点数组query。全部返回对应类型错误、无排队且执行游标仍为0；随后正常整集仍完成。此前绕过handle_execute的测试缺口已补齐，本轮未发现需扩大写集的后续接线问题。

验证：`27 passed in 21.48s`；ruff E/F 和 git diff --check 均通过。可复制命令（在上述bridge workspace）：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONPATH=../openpi/packages/openpi-client/src .venv/bin/python -m pytest -q tests/robot/controllers/test_memory_v1_offline.py tests/robot/controllers/test_drawer_offline.py tests/robot/controllers/test_x2robot_offline_phase.py tests/scheduler/test_memory_v1_schedulers.py
.venv/bin/python -m ruff check --select E,F robot_bridge/robot/controllers/x2robot_offline.py tests/robot/controllers/test_memory_v1_offline.py
```

本轮CPU-only，未加载真实模型、未启动GPU、未改运行中的训练。实现与必要验证已完成，无需Manager裁定新的技术阻塞。请 Helmholtz / 独立任务 `4296391f-6e8e-4f99-b6ab-e53bb85af99b` 复查该增量；当前会话无agent消息工具，不能直接发送通知，交付通过本报告及对Manager的回复通知。

独立复核及Manager准入前不启动GPU2 retry2。后续固定输出 `/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_20k_offline5ep_retry2`，仍须固定干净源码、卡/端口/source握手门禁和真实两模型各5ep指标/退出验收。前两次失败原始证据保留未覆盖。CPU fake-policy集成不代表正式offline通过，不代表真机效果或原始架构重构完整完成。

以下保留历史交付和失败记录。

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
