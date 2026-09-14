# V 工程独立审查报告

审查基线为 OpenPI `96e37e840f196d3b0945994d9a9bb5980d25ca58`、RMBench `a03fd1c3a40ac89542b7afe80d7188acd3dc2bd9`、robot-bridge `20dae84e5fc2e48f93e72b5c1b8a0001071fec94`。仅使用独立 worktree 和 CPU；未改实现、未启动 GPU、两步 smoke、20k 训练或闭环评测。

## 裁决

**不准入 V 的正式训练或运行时评测。** 训练采样、固定输入合同和普通串行 bridge 路径有可复用基础，但存在一个已复现的跨 episode 状态泄漏；同时，最新任务合同要求的五个真实任务入口、匹配 N 的 norm 复用和非空容量 profile 都没有交付。修复 P1 并补齐这些准入材料后，才应重新审查。

## P1

### reset 与在途 infer 不是原子的，可把旧 episode 帧写回新 episode

`VisualHistoryRuntime.reset()` 只替换缓存对象，而 `_PendingVisualHistory` 没有 generation/epoch；随后任何旧 `commit()` 都会照常写入新缓存。[`visual_history.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/visual_history.py:129) 的 pending 只保存帧，[`reset/prepare/commit`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/visual_history.py:245) 之间没有 generation 或同步保护。`Policy.infer()` 在模型调用前 prepare、完成后 commit，[`policy.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/policies/policy.py:78)，因此 reset 可落在两者之间。

独立 CPU 复现：对 old episode 的 step 0 调用 `prepare`，随后 `reset`，再 `commit(old_pending)`；new episode 的首个 `prepare` 得到 `initial=true`，其像素是旧帧值 17，而不是 new current 值 99。反序完成也会失败：先 prepare step 0/30，按 30、0 顺序 commit 后，下一次请求的 initial 是 step 30，history 顺序为 `[30, 0]`。

这不是只能在测试中构造的状态。bridge transport 明确允许并发客户端，[`websocket.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/robot-bridge/robot_bridge/transport/websocket.py:9)，每个连接直接调用同一个 handler，[`websocket.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/robot-bridge/robot_bridge/transport/websocket.py:56)；handler 对同一 backend 的 `reset`/`infer` 没有串行锁，[`policy/server.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/robot-bridge/robot_bridge/policy/server.py:70)，backend 又直接转发到 OpenPI policy，[`openpi.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/robot-bridge/robot_bridge/policy/backends/openpi.py:349)。

修复应使 pending 绑定 reset generation，并在 commit 时拒绝旧 generation；同时需要把 prepare/commit/reset 与 policy RNG/state 的访问串行化，或在 bridge 明确保证单一 episode/单一请求的排他性。应新增 reset→late-commit 和反序 completion 的回归测试。

### 五个已就绪任务没有实际接入，两个 manifest 不能作为 runtime 准入

RMBench 两个 JSON 的 `jobs` 都为空，九个 task row 的 `task_id`、`repo_id`、`run_name` 全为 `null`，[`jobs_formal_candidates.json`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/RMBench/experiments/pi05_visual_history_v/jobs_formal_candidates.json:1) 和 [`jobs_smoke_candidates.json`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/RMBench/experiments/pi05_visual_history_v/jobs_smoke_candidates.json:1)。README 也明确说明九行故意不填、dry-run 不会启动任何作业，[`README.md`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/RMBench/experiments/pi05_visual_history_v/README.md:60)。

这符合旧的“候选模板”描述，却不满足源任务续约后的要求：至少要接入 `rearrange_blocks`、`put_back_block`、`swap_blocks`、`battery_try`、`cover_blocks`，且各自使用对应的 `demo_clean_state_shared_memory` 数据。当前 V recipe 默认仍是 `rearrange_blocks_demo_clean`，[`config.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/config.py:1319)。没有真实数据验收、非空 CPU batch/dry-run、准确命令或五项任务记录，空 dry-run 不能证明部署路径可用。

### V 没有复用匹配 N 的 robot/action norm，也没有记录 hash

V recipe 没有 `AssetsConfig` 或 norm provenance，[`config.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/config.py:1322)。通用工厂会把没有显式 asset 的 asset ID 设成当前 `repo_id`，[`config.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/config.py:222)。独立 CPU 配置检查也确认默认 asset 为 `rearrange_blocks_demo_clean`，将 repo override 为 `swap_blocks_demo_clean_state_shared_memory` 后 asset 随之变成该 repo，而不是已验收 N 的 robot norm asset。

README 反而要求为 V 用 `--max-frames 10000` 重新计算 norm stats，[`README.md`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/RMBench/experiments/pi05_visual_history_v/README.md:85)。在 source/action 列完全相同的前提下，这引入额外随机采样/资产变化，违背最新合同的匹配 N norm 复用和 hash 记录要求。每个实际任务需要固定 N 的 asset 路径、SHA-256、state/action 列和维度，并让 V recipe/非空作业显式读取该 asset；不应靠人工临时 override。

## P2

### 20k 正式配方不可恢复

`TrainConfig` 的默认 `save_full_state=False`，[`config.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/config.py:1034)，并明确拒绝 `resume=True` 的 model-only checkpoint，[`config.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/config.py:1137)。V recipe 没有覆盖这个默认值，[`config.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/config.py:1337)，formal template 也没有设置 full-state 保存。

CPU 检查得到 `save_full_state=False`、`save_interval=10000`，并且 `dataclasses.replace(recipe, resume=True)` 抛出 `Cannot resume a model-only checkpoint`。最新容量 profile 候选明确要求保存/恢复字段，因此正式入口至少应说明并验证恢复策略；当前中断后不能续跑 20k。

### 推理初始锚点依赖“首个成功 infer 恰好是 step 0”，接口未强制

训练 anchor 固定为 `episode_data_index.from`，[`visual_history.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/visual_history.py:335)。运行时则把首个 prepare 的 current 当 initial，[`visual_history.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/visual_history.py:260)；scheduler 只验证 logical step 非负，[`openpi_simulation.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/robot-bridge/robot_bridge/scheduler/openpi_simulation.py:493)，并允许测试以 step 10 作为首个 V 输入。

现行 RMBench worker reset 后通常从 `take_action_cnt=0` 返回，因此常规串行路径预计满足此隐含前提；但它没有被 V 接口检查、记录或测试。应在 first infer 强制/证明 logical step 0，或者把实际 episode-start frame 明确传入并保存。

## 已确认的正确部分

- 训练 wrapper 只保留 `(source_index - episode_start) % 30 == 0` 的真实 query 行，并从当前 outer row 返回 action target；history 使用严格早于 current 的 K=30 行。[`visual_history.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/visual_history.py:328)
- 独立双 episode fake-data 检查得到 query `0,30,60,90,91,121,151,181`；episode 1 尾部 query 的 action 仍是其 outer-row target `10181`，读取帧仅为 `91,121,151,181`，没有跨 episode 或未来图像。
- temporal/camera 顺序、H50/K30、14D→32D padding、50 demos、seed 0、bs 32、20k 的代码锁定存在；V scheduler 会拒绝错误 action shape、K 不匹配和 `technical_smoke` metadata。
- `image_mask` 确实进入 JAX attention mask：image tokens 的 mask 在 [`pi0.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/models/pi0.py:141) 展开，`make_attn_mask` 同时遮蔽 key/query。[`pi0.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/models/pi0.py:32)
- mask 不减少视觉编码：JAX 在读取 mask 前对每个 slot 调用 `PaliGemma.img`，同一结论也适用于 PyTorch 的 `embed_image` 路径。因此短 history 只减少 attention 的有效 token，仍会编码全部 18 张图；README 的 token/attention 成本是合理的理论提醒，不能代替实测。
- scheduler 首次 infer 前的 backend reset、`OpenPiBackend.reset()` 转发、V identity 的 nonce + logical step、以及普通 N/S/J 默认路径的 CPU 回归均可见且本次测试通过。

## 验证与未验证范围

已通过：

- OpenPI：指定 CPU suite `visual_history_test.py`、`config_test.py`、`checkpoint_metadata_test.py`、`data_loader_test.py`、`policy_test.py`、`pi0_test.py`：**43 passed, 2 deselected**。
- robot-bridge：provenance、metadata、V scheduler suite：**31 passed**。
- 两个 JSON 通过 `python -m json.tool`；三个 review worktree 均干净并通过 `git diff --check`。
- 额外 CPU 脚本完成上述 multi-episode/尾部 action 检查，并复现 stale commit 和反序 commit。

未验证：真实五任务数据和三相机接口、N norm hash 一致性、非空 loader/dry-run、实际 18-image full forward、batch 32/H50/原分辨率峰值显存、吞吐与 p95、两步 GPU 容量 profile、20k 恢复、以及闭环评测。`VisualHistoryLeRobotDataset` 还保留跨整个 persistent data-loader worker 生命周期的原始帧 cache，[`visual_history.py`](../../../workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/openpi/src/openpi/training/visual_history.py:323)，实际数据的 CPU RAM 也应在容量 profile 中记录。
