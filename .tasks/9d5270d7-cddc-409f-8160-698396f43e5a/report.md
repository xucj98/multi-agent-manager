# C1 put-back J/T train2/eval2 formal100 独立审计

结论：在本任务限定的正式证据范围内，没有发现应阻断计入正式结果的缺口。独立重算结果与 owner 声称一致：

| Arm | 正式结果 | 独立重算失败类别 |
| --- | --- | --- |
| J `full_t_plus_1` | 68/100 (0.68) | `block_not_moved_to_center=2`，`block_not_returned_to_origin_mat=1`，`button_not_pressed_after_center=19`，`button_press_insufficient=9`，`pressed_before_block_centered=1` |
| T `full_t_plus_30` | 73/100 (0.73) | `button_not_pressed_after_center=14`，`button_press_insufficient=13` |

对两叶均重哈希了 final review 及其 10 个核心引用，重算 100 条连续 episode `0..99`、accepted preflight、环境 seeds `300000..300099`、terminal diagnostics、结果和失败类别；核验 100 条 video check（仅 `0..4` 启用）和 102 start/102 exit 的进程记录。远端只读库存记录同样显示各叶 100 个 episode JSON、5 个预期视频、无额外文件；106 个 formal worker log/叶没有基础设施失败标记，保留的单条 SAPIEN Vulkan ICD warning 为非致命记录。

两叶配置均为 train seed 2 / eval seed 2、`demo_clean_eval`、H50/K30（action horizon 50、execution rows 30）、首个 inference 90 秒、后续默认 30 秒，并引用相应的 train2 checkpoint。29 个 checkpoint metadata 文件/叶已重哈希并和 input audit/config metadata rows 对照；params/assets 仅核验保存的行清单与摘要，未重哈希其约 5.26 GB 内容。冻结审查 worktree 均 clean，HEAD 为 RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`；静态核对到 OpenPI `jax.random.key(0)` 后逐 inference split、无状态 backend reset，以及可配置的首 inference timeout。

matching smoke 的 review/cleanup/hash 链和两个已归档 MAM job 已核验；远端库存确认两条已授权删除的 smoke raw leaf 均不存在。完整可复算收据在 `evidence/formal_train2_eval2/receipt.json`，SHA-256 `88c5d263c462364920d02df6cadcf3da0cd0006d85a48c3389b15fdf30cc5133`；审计器为 `evidence/formal_train2_eval2/tools/audit_formal_train2_eval2.py`，SHA-256 `7203773d30c8992f7060f9cf1e90643375b996fc5f04f14a5d3f302a4caeb9be`。

范围限制：未运行模型/GPU/仿真/训练，未重解码正式视频，未重哈希已删除 smoke raw 或多 GB params/assets，未检查 HF；因此结论只覆盖保留的正式证据、远端只读清单和冻结源码。
