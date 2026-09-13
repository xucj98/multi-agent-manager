# HF 完整轨迹工程核查

任务 revision：`d8c9ed6c376ac1e88aeaf658ce49033fe1e63d20`。本次只做源码和既有工具的操作边界核查；未运行 GPU、仿真环境、模型、测试、C0/C1/P 或任何 profile，未修改冻结源码、gate、helper 或评测产物。

审阅 worktree 均为 clean：

- robot-bridge：`/mnt/public/xcj/Projects/workspace/9c7622d0-45e6-4952-8b63-744d7e151a8c/robot-bridge`，`ffa122494c19e1c0154e877010f7b470967ccfc6`
- RMBench：`/mnt/public/xcj/Projects/workspace/9c7622d0-45e6-4952-8b63-744d7e151a8c/RMBench`，`6abebf08d084d0be43aa56ebe158dc8395fa58e4`

## 1. get_obs 的副作用边界

`robot_bridge/robot/controllers/rmbench_sim_worker.py:RMBenchSimWorker.get_obs` 先处理 `wait_condition`：有剩余队列目标时调用 `_drain_to()`。后者逐行执行 `env.take_action()`，会推进物理状态、逻辑步和 episode 状态；这不是相机 capture 的副作用。随后，有 `image_ts` 时调用 `env.get_obs()`，没有 `image_ts` 时才调用 `get_obs_for_policy()`。

实际 simulation scheduler 的 `openpi_simulation.py:build_obs_request` 固定发送 `{"cmd": "get_obs", "image_ts": [0.0]}`。rolling 模式还会写入 `wait_condition`。因此工程 HF 路径走的是完整 `env.get_obs()`；只要请求带有等待条件，就必须把此前 drain 的动作推进和新鲜观测分开归因。

对 reset 后、没有上述 drain 的一次新鲜相机观测，`RMBench/envs/_base_task.py:Base_Task.get_obs` 的可见调用链为：

1. `_update_render()`：在 `self.crazy_random_light == false` 时，更新 wrist camera pose 并调用 `scene.update_render()`；
2. `cameras.update_picture()`：对相机调用 `take_picture()`；
3. 读取 RGB/状态等，并覆写 `self.now_obs` 缓存。

检查到的 `Camera.update_picture`、`get_rgb/get_rgba`、`camera.get_picture("Color")` 路径没有显式 `scene.step()`，也没有 NumPy 或 Python `random` 调用。因此在 `random_light=false`、`crazy_random_light_rate=0` 实际令 `crazy_random_light` 为 false 的前提下，源码只支持这个窄结论：上述**新鲜 camera-observation 路径本身**没有可见的物理 step 或 NumPy/Python RNG 消耗。它仍更新 renderer/camera pose 和 `now_obs`，并不是无状态读取。worker 之后还取 diagnostics；各 task 的 diagnostics 是否绝对无隐藏状态变化，不能仅由这一段静态调用链保证。

不能把该结论扩展到 reset/初始化。每次 setup 会重设 NumPy RNG（`_base_task.py`；Python `random.seed` 已注释），而 `Camera.load_camera/create_camera` 无条件执行 `np.random.randn(3)` 和 `np.random.uniform(..., high=random_head_camera_dis)`，即使距离上限为 0 仍消耗 NumPy RNG。相机加载完成后 `Base_Task.load_camera` 显式 `scene.step()`。所以关掉 light 随机化不能证明 reset、相机初始化、renderer/SAPIEN 数值行为或完整轨迹等价。

## 2. 现有五个 profile 与十个 episode attempts

C3 既有只读工具根为：

```text
/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c3-highfreq-engineering-20260914/.local/highfreq_engineering
```

`hf_engineering.py` 的 profile 映射、矩阵生成和 scheduler contract 已覆盖以下恰好五个 profile、十个 attempts：

| profile | task / attempts | scheduler contract |
|---|---:|---|
| `c_hf_j_shadow_rs30_degradation_rearrange_trainseed0_eval0_2ep` | rearrange_blocks；2（100000、100001） | shadow，legacy continuous action RNG，interval 30，`max_k=None`；K30 boundary 不 probe |
| `c_hf_j_hf_fixed_rearrange_trainseed0_evalseed0_smoke2` | rearrange_blocks；2（100000、100001） | hf_fixed，H50/K30，interval 5，独立 episode reset key |
| `c_hf_j_hf_fixed_put_back_trainseed0_evalseed0_smoke2` | put_back_block；2（100000、100001） | hf_fixed，H50/K30，interval 5，独立 episode reset key |
| `c_hf_j_hf_event_rearrange_trainseed0_evalseed0_smoke2` | rearrange_blocks；2（100000、100001） | hf_event，H50/K30，interval 5，独立 episode reset key |
| `c_hf_j_hf_event_put_back_trainseed0_evalseed0_smoke2` | put_back_block；2（100000、100001） | hf_event，H50/K30，interval 5，独立 episode reset key |

其中 `j_hf_fixed` 和 `j_hf_event` 都映射为 `reset=False, max_k=30, interval=5`；r_s=30 只有上表 rearrange 的一项。它只能验证无 probe 的队列路径，不能命名或解释为 HF-fixed 的退化等价，也不能新增 put-back r_s=30。

工具的直接执行单位是单 profile：

```bash
python hf_engineering.py run --profile <上述任一 profile 名>
```

`run --profile` 每次只选择一个 profile，`run_profile()` 只启动其一次 benchmark smoke；不会自动补跑 matched baseline、shadow、其他 profile 或 formal100，且该工程 leaf 会记录 `formal100_started=false`。工具的 `prepare`/ `dry-run` 会生成其输入和命令；本次只读核查没有调用它们。静态检查时，五个 profile 尚无对应的 `commands/`、`executions/`、`schedulers/` 或 `audits/profiles/` 产物。

## 3. 既有等价 gate 的边界

`hf_engineering.py:compare_matched_pair()` 会将 matched baseline/shadow 留存的 `action_rows` 以 Python list 精确相等比较，不等即失败；该检查只由 `hf_engineering.py audit --pair ...` 触发，并非 `run --profile` 的自动步骤。

另一个 `hf_queued_event_audit_v2.py` 是历史离线审计。它保留并要求历史 `audits/failures/matched_action_equivalence_failure.json` 所代表的 exact mismatch 仍存在。该历史失败不能改写成 PASS，也不能充当新五个工程 profile 的运行入口条件。正式矩阵仍须由各 formal run 自己满足 matching smoke 和 identity 要求；工程 smoke leaf 不满足 matching-smoke gate。

## 4. 最小执行编排建议

若 Manager 按另行授权启动这十个 attempts，最小 task-private outer runner 应只按固定顺序调用五次既有的 `run --profile`（每次 profile 内含两集），并在 runner 私有目录保存每次实际命令、开始/结束时间、stdout/stderr、退出码和 helper 返回的路径。它不应：

- 调用 `audit --pair`，不自动添加 baseline/shadow/formal；
- 重定向、覆盖或修改 frozen helper 的硬编码 state 目录、manifest、scheduler、command 或历史 failure；
- 删除既有 leaf 后重跑；helper 的 `write_once()` 和已有 result/outer-log 拒绝逻辑应保留；
- 新建 put-back r_s=30，或把 r_s=30 解释为 HF-fixed 等价。

若单项 helper 拒绝已有产物或返回失败，outer runner 应保留该项的原始输出和退出状态，使后续验收能区分“未启动”“工具拒绝”和“benchmark 失败”。这套编排只组织已有命令，不能据此主张观测、数值、随机状态或完整轨迹等价，也不构成 formal 准入。

