# put-back 基线窄审阅：最终裁定

## 结论

**PASS：`pi05_rmbench_put_back_block_no_memory` 可准入，未发现阻塞项。**

**PASS（配置与 CPU 范围）：`pi05_rmbench_put_back_block_serial_lag30` 未发现配置阻塞。**
serial 自身的作者 GPU smoke 尚未执行，因为 GPU6 为外部作业占用；这是一项独立训练 gate，
不是本次配置 review 的缺陷，也不应阻塞 no-memory。

审阅对象为 OpenPI `a7f3e07346cee7260cdc3a618eedc38c0702da61` 相对
`a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` 的两个新增配置；结论仅限此次 YAML、
注册和样本对齐增量，不扩展到全 loader/schema。

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

## serial 额外证据

- YAML 与 `rearrange_blocks_serial_lag30` 同构，只把任务字段替换为 put-back 的
  `phase`（4 类）和 `origin_mat`（5 类）。50 个真实 sidecar episode 的两字段均在声明
  词表内，且每条均为 `query_count + 1` 行。
- serial config 固定 `previous=30`，`current_condition` 为 `train: reference / infer: selected`，
  policy metadata 为 `serial_train_conditioning=teacher_forcing`。真实 episode 的 query 138
  取到 input `(q-30)=(move_block_to_center, front)`、target
  `(q)=(press_button, front)`，两个 token target 均有效，排除了当前/滞后错配。
- 强制 CPU 的真实首 batch 给出 serial input/target/mask 均为 `[32, 2]`、64 个有效 target；
  action/loss 权重仍为 `[32, 50, 32]`，前 14 个机器人维有效、padding 维全零。

## GPU 证据边界

源任务已发布 no-memory 的 GPU7 50-step、BF16 model-only 保存和 checkpoint-only 恢复记录，
并标注其可单独放行。该记录属于作者侧证据；本审阅未使用 GPU，也未独立重跑或冒称已验收。
serial 的作者 GPU smoke 尚未启动，原因是 GPU6 的外部占用。

## 后续范围

no-memory 可立即按其单模型放行流程推进；serial 在 GPU 资源可用后再完成作者侧 smoke gate。

工作区：`/mnt/public/xcj/Projects/workspace/15254a5f-20ec-46f5-b118-4f0f42ba684f/openpi`
（branch `task/15254a5f-20ec-46f5-b118-4f0f42ba684f`，HEAD `a7f3e07346cee7260cdc3a618eedc38c0702da61`）。
