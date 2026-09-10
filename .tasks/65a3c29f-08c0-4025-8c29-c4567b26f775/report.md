# 通用 memory offline 独立 review（2026-09-11，CPU-only）

## 结论与裁定建议

Memory V1 的离线时序、availability mask、full/serial 指标记录和 S2M 已转换 `action_at_row` 的 robot offset 0 在本次 CPU 审阅范围内正确；wash 单字段与旧 drawer 多字段确实走同一 controller / scheduler / launcher 机制，未发现 wash 专用 GT、反馈或执行算法。`5,525` 也已辨清：它是五集每个模型应执行的 15 Hz 逻辑 query/action 行总数，不是 policy `infer` RPC 数。K=30 时，成功回放应为 `[41, 51, 24, 38, 33]`、合计 `187` 次 `infer` / 模型，执行 `5,525` action 行 / 模型（两模型合计 374 次调用、11,050 行）。

但我不建议把下一次 20k GPU 回放作为正式可追溯验收启动，直到下述 P1 修复完成。它不是 memory 时序错误，而是不满足任务要求的运行时源码 clean gate 与顶层 provenance 绑定。P2 不阻塞当前两个 manifest：它们的重复字段目前相等；应在继续泛化入口前修掉，避免将来静默用错误的一组值验收。

## P1：实际 policy 源码未纳入启动前 clean gate 与顶层 provenance（正式验收阻塞）

**证据。** `scripts/launch/drawer_offline.py:417-443` 只对 bridge repo 和可选 `--rmbench` 执行 `git status --porcelain`。`--policy-python` 实际导入的 OpenPI 源码既不在这项检查中，也没有在顶层 `provenance.json` 中以实际模块根、commit 和解释器身份写入；`source_commits` 是从 checkpoint root alias 得到的 Git HEAD。因此 `--checkpoint-root OpenPI=<存 checkpoint 的 Git 根>` 可以被记成 “OpenPI source”，即使 policy interpreter 从另一份 checkout 或有未提交改动的安装包导入代码。

这不是说实际运行时信息完全缺失：`robot_bridge/policy/backends/openpi.py:212-282,346,402-404` 会从已加载的 OpenPI module 推导实际 Git root、commit、内容摘要和解释器，并且 launcher 在 `scripts/launch/drawer_offline.py:491-497` 把它保存为每个模型的 `served_metadata.json`。问题在于该信息在启动后才取得，未构成启动前 clean gate，也没有与顶层 provenance 的 generic root commit 交叉验证。

**影响。** 正式输出可能在顶层看似固定到了 checkpoint/data root 的 HEAD，而实际 policy 源码或解释器不同；这会破坏复现和“实际运行源码 commit”的验收要求。

**最小修复建议。** 在创建正式输出、启动 policy 前，以 `--policy-python` 运行极小探针，解析实际 `openpi.__file__`（或实际加载的 `openpi.training.config.__file__`）对应的 Git root；对该 root 用现有同样的 clean 检查，并把 root、commit、解释器路径/二进制身份写入顶层 `provenance.json`。收到 `get_metadata` 后，校验该预解析结果与 `served_metadata.provenance.source`、`served_metadata.provenance.interpreter` 一致。保留现有每模型 metadata 作为更细的运行时证据。

## P2：manifest 的重复 timing 字段会静默优先覆盖（当前非阻塞）

**证据与复现。** `_expected_metadata` 在 `scripts/launch/drawer_offline.py:127-146` 发现 `expected_policy_metadata` 时不再读取 `dataset.target_fps/horizon/query_stride`；`_expected_execution_rows` 在 `:149-159` 同样优先顶层字段。独立内存探针同时给出 dataset `15/50/30`、显式 metadata `16/51/31`、dataset execution rows `30`、显式 execution rows `32`，函数无报错并返回 `16/51/31` 和 `32`。

**影响。** 当前 wash manifest 的两套值都是 `15/50/30` 与 `30`，旧 drawer 则只依赖 dataset fallback，故本轮不会错配；但未来编辑一个副本时，数据描述和用于 served-metadata / execution 校验的值可以分叉而不被发现。

**最小修复建议。** 两种来源同时存在时，逐项拒绝不一致；只存在一种时保持现有行为。这样不改变 wash 和 legacy drawer 的有效输入，也不需要改变 checkpoint metadata 优先级规则。

## 已确认的时序与范围

- `openpi_client.memory_config.make_training_sample`（OpenPI `packages/openpi-client/src/openpi_client/memory_config.py:293-370,453-479`）按 checkpoint 内的 schema 取目标。真实 wash YAML 的 robot series 是 `action_at_row`，其 `robot_target.time` 为 `query+row`（offset 0）；full memory 为 `query+row+1`，serial memory 为当前 query。`src/openpi/training/memory_data.py:148-167` 还拒绝对 `action_at_row` 再施加 robot offset。availability 只清除受影响 memory GT/mask，不清除 robot target。
- 离线 controller 从相同 `make_training_sample` 取 GT（bridge `robot_bridge/robot/controllers/x2robot_offline.py:171-248`），仅在 queued action 真正 drain 后追加 record（`:811-848`）；评估按实际执行记录取 action/memory GT，serial 每 query 留一个当前目标（`:1086-1163`）。因此 episode 末尾的 dropped queue 行不进入指标。
- scheduler 先以 completion wait-condition 获取下一观测（`robot_bridge/scheduler/openpi_offline.py:316-348`），policy input 只接收 `MemoryContext` 的历史状态；预测解码后才作为 evaluation execute payload，并在 robot 接受后由 `MemoryContext.accept` 排队、等 completion evidence 更新（`:475-529`）。GT 不进入 policy input、MemoryContext 反馈或未来观测。
- full 的每执行 action 行保留对应 model row；serial 对一整个 drained chunk 只计当前 query 的 row 0。这与同一 source-frame sidecar 的 action-at-query / robot offset 0 对齐一致。

## CPU 验证（未加载真实 checkpoint、未使用 GPU）

在本任务的 bridge worktree 中，以 `CUDA_VISIBLE_DEVICES=` 和轻量 `openpi_client` 路径运行：

```bash
PYTHONPATH=<openpi-worktree>/packages/openpi-client/src \
  .venv/bin/python -m pytest -q \
  tests/robot/controllers/test_memory_v1_offline.py \
  tests/robot/controllers/test_drawer_offline.py \
  tests/scheduler/test_memory_v1_schedulers.py \
  tests/scheduler/test_openpi_memory_transform_contract.py
```

结果：`18 passed, 1 skipped in 6.66s`。覆盖 full 多字段/mask/canonical action、serial 每 chunk 的当前 query、evaluation payload 不进入 policy input、synchronous completion 的 row 0、非 synchronous wait condition，以及旧 drawer full/serial。

在 OpenPI worktree 中运行：

```bash
PYTHONPATH=packages/openpi-client/src .venv/bin/python -m pytest -q \
  packages/openpi-client/src/openpi_client/memory_config_test.py
```

结果：`18 passed in 0.43s`。另做无落盘 H=7/K=3 双字段反例：query=8、尾端缺失一个 phase GT 时，robot 为已转换 `action_at_row` 的 `t+j`，full memory 为 `t+j+1`，memory phase mask 为 `[true,false,false,false,false,false,false]`，robot target mask 仍全真；serial 的唯一 memory target 是 query=8。该探针通过。

还对真实 wash index 0 使用实际 H50/K30 YAML、真实 raw/sidecar 和确定性假 policy 做完一集 CPU 回放（临时目录已清理）：full 与 serial 都是 `41` 次 infer-like chunk、`1,216` 个实际执行 action 行、action supervision MAE `0.0`；full 记录 `1,216` 个 memory 行、`1,186` 个有效 phase 样本，serial 记录 `41` 个当前-query memory 行、`39` 个有效 phase 样本。首个 action 记录为 query/model-row `[0,0]`，其执行 source frame 为 `2`，验证了 action-at-query 与 source-frame 对齐以及末尾截断后只计实际 drain 行。

真实输入 dry-run 也通过：

- wash `configs/input_manifests/wash_cup_memory_v1_offline5.json` 用 `/mnt/public/datasets/x1pro/wash-cup` 与 OpenPI root 预检了固定 LeRobot index `0–4`，json/source 时间线分别为 `1216/1509/702/1115/983` logical rows，首 source frame 都是 0，终端 frame 分别为 `2408/2989/1390/2208/1947`。
- legacy drawer `configs/input_manifests/unified_sim_real_runtime.json` 用 `/mnt/public/datasets/x1pro/table_clean` 与 RMBench root 预检通过，固定 episode `[1,22,23,24,26]`、15 Hz / H30 / K15、两个既有 checkpoint 都为 `ready: true`。它仍走 legacy manifest 适配而非 wash 专用路径。
- `python -m py_compile` 覆盖 launcher、controller、scheduler、OpenPI backend，且 `git diff --check bd30069f..3a364a6d` 通过。

## Launcher 范围判断

当前两套 manifest 实际需要：wash 的 rooted sidecar/checkpoint 路径和 query-count 预检；legacy drawer 的 `RMBench/...` 路径兼容、固定五集保护及 dataset metadata fallback；共享的 served metadata、进程退出和输出产物管理。它们支持“同一机制、配置差异”的边界，建议保留。

不由当前两个输入必然要求的泛化是：任意绝对字符串 checkpoint fallback、显式 `--replay` 选节、以及超出 `OpenPI`/`RMBench` 的可重复 root-alias registry。可在确认无外部 manifest 依赖后简化；新增代码行数本身不是问题。

## 交付状态与剩余 GPU 验收

- robot-bridge 审阅基线：`3a364a6dd87c08753a804e5598ddc85ef832d9b1`，对照 base `bd30069ffc0b773de13f98f53753566711960858`。
- OpenPI 审阅基线：`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。
- 独立 worktree 保留于 `/mnt/public/xcj/Projects/workspace/65a3c29f-08c0-4025-8c29-c4567b26f775/{robot-bridge,openpi}`；未修改业务代码、作者树、主树或训练树，未合并。

本次 wash dry-run 中两个目标 `.../20000` checkpoint 均为 `ready: false`，所以真实权重 GPU replay 目前也受训练产物未就绪阻塞。P1 修复并出现 checkpoint 后，由 Manager 在分配 GPU 的环境执行正式 full/serial 回放；验收时应核对顶层/served runtime provenance 一致、每模型 187 次 infer 与 5,525 个执行行的实际记录，以及 full/serial NPZ 的行数和 mask。

## 本轮结案状态

Manager 已接受 P1 与 P2，并已向作者发布小修：补实际 policy source 的 clean gate / 顶层 provenance 绑定，拒绝冲突的 metadata 字段，同时删除当前未使用的 `--replay` 与 wash manifest 重复字段。本报告据此结案；上述修复尚未包含在本审阅基线中。收到指定的新 commit 后，仅对这些变更及其直接回归作定向复查，不重复本报告已通过的全套时序验证。两个独立 worktree 保持原样供后续复查。
