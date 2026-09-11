# put-back 基线窄审阅：no-memory 快速裁定

## 结论

**PASS：`pi05_rmbench_put_back_block_no_memory` 可准入，未发现阻塞项。**

审阅对象为 OpenPI `a7f3e07346cee7260cdc3a618eedc38c0702da61` 相对
`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` 的两个新增配置；此先行裁定只覆盖
no-memory，不等待 serial。

## 独立 CPU 证据

- 注册项使用 `put_back_block_demo_clean_state_shared_memory`、
  `rmbench_put_back_block_robot` 和其 `state/actions` 各 14D norm。与既有
  `rearrange_blocks_no_memory` YAML 同构，只有配置 ID 不同；其 factory 参数只替换
  put-back 数据和 norm 资产。
- materialized config 为 Pi0.5、action `32x50`、batch `32`、20,000 steps、
  `save_interval=20000`、`save_dtype=bfloat16`、`save_full_state=False`、pi05_base
  loader，和既有协议一致。
- 强制 `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu` 的真实 put-back 首 batch：state、
  action 与 loss weights 都是 `[32, 32]`、`[32, 50, 32]`、`[32, 50, 32]`；
  `key_state_*` sidecar 均为 `None`，机器人前 14 维共有 22,400 个有效权重，后 18 个
  padding 维为零。
- 同一真实 sidecar 的 query 138 复核表明 robot target 从
  `robot_action_target[q]` 开始按 stride 1 取 50 行；no-memory 的 input/target 分别为
  `(0,)` / `(50, 0)`，无 memory loss，padding 权重为零。
- `scripts/worktree_env_smoke.py`、新增配置定向 pytest（`1 passed in 6.50s`）和变更
  Python 文件的 `ruff check` 均通过。

## GPU 证据边界

用户通知作者已完成 no-memory 的 GPU 50-step smoke 与 checkpoint-only 恢复。本审阅未使用
GPU，也未独立重跑或验收该作者侧证据；以上 PASS 是配置和独立 CPU 准入结论。

## 后续范围

serial 的同类核对继续进行，但不应阻塞已 ready 的 no-memory 模型。

工作区：`/mnt/public/xcj/Projects/workspace/15254a5f-20ec-46f5-b118-4f0f42ba684f/openpi`
（branch `task/15254a5f-20ec-46f5-b118-4f0f42ba684f`，HEAD `a7f3e07346cee7260cdc3a618eedc38c0702da61`）。
