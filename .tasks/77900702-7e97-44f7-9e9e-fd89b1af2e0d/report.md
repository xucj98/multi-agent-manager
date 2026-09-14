# C1 put-back J/T train1/eval2 正式结果独立审计

结论：`pass_with_scope_limits`。本任务规定的正式计数证据范围内没有发现阻止把两条完整 100-episode 结果交给 Manager 裁决的缺口。

| leaf | 独立重算结果 | 正常失败类别 |
| --- | ---: | --- |
| J `c_put_back_full_t_plus_1_trainseed1_evalseed2_100ep_r3` | **58/100** | `button_not_pressed_after_center=25`；`button_press_insufficient=16`；`block_not_returned_to_origin_mat=1` |
| T `c_put_back_full_t_plus_30_trainseed1_evalseed2_100ep_r3` | **62/100** | `button_not_pressed_after_center=21`；`button_press_insufficient=17` |

`evidence/formal_train1_eval2/receipt.json` 是可复跑的离线收据，SHA-256 为 `eac1c29667fd65894a9b55dc46deef36249c0fba5df8b578d10fbb8230d3605b`。其审计器为 `evidence/formal_train1_eval2/tools/audit_formal_train1_eval2.py`，SHA-256 为 `daf00256ade4f99bf0afcd825324547ccafd804ec68318581f2040e8c0041f7d`；40/40 项通过。收据重哈希了每份 `final_review.json` 引用的 10 个原件，以及每份 `input_audit.json` 中全部 29 个已复制 metadata 条目。

两叶均有 100 条 accepted preflight 和 100 条 terminal diagnostics，episode 是连续 `0..99`，seed 是连续 `300000..300099`；每条诊断的终态来自 `diagnostics.episode_status`。两叶分别有 100 条 video checks，只有 episode `0..4` 启用且全部 `ok=true`。保存的只读 C1 摘要也确认每个 formal leaf 当前有 100 个 `episode*.json` 和恰好 `episode0..4.mp4`，无其余 video；摘要 SHA-256 为 `0d3d38b055aa54e14c470b0c8d136ef01707421d0264def7538eec3449d26c5c`。

`processes.jsonl` 对每叶均显示 102 start / 102 exit，100 个 scheduler exit 均为 0，robot/policy 均以 runner shutdown 的 `-15` 收尾。独立的只读远端日志扫描分别覆盖 106 个日志、33,900,160 和 33,334,608 bytes；所有规定基础设施 marker 为 0，各有一条已知非致命的 SAPIEN Vulkan ICD warning。扫描输出 SHA-256 为 `c36e7d5917cd59fc3df3b01fa929f4057635b386bf302dd3cd3f99ccc2321dff`。

C1 当前冻结 runtime 与审阅 worktree 都 clean，且为 RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。配置和冻结代码交叉核对为 train seed 1、eval seed 2、`demo_clean_eval`、H50/K30、首次 infer 90 秒、后续 RPC 默认 30 秒、随机化关闭。OpenPI 的 JAX RNG 从 key 0 初始化并每次 inference split；backend `reset()` 不重置该 RNG，因此这里的合同是每个 fresh policy server run 内连续 action RNG，并非 episode 间重置。

两份 final review / cleanup 的 SHA 分别与任务锚点一致：J `be14b50e…ccca78` / `2cebc82e…68dcb1`，T `a5bbb1ae…45ffd75` / `79f2141b…6c26f1`。matching smoke 原始 leaf 已获授权删除；保留的 smoke review、formal manifest、cleanup receipt 与 C1 当前“不存在”状态均已核对，不能把这项审计表述为对已删除 smoke raw 的重哈希。两个 source-task job `0f7daad0-ba87-41dc-8efd-57431d03a289` 和 `8883cf5e-9fd9-4255-b120-eac472a20c40` 均 archived，且与 final-review provenance、cleanup receipt 和现存 finalizer 的 MAM ID 映射一致。该链只能证明现存原件相互一致，不能追溯证明历史写入过程。

范围限制：未运行 GPU、模型、仿真或训练，也未触碰 train2；未重新解码视频；未重算多 GB checkpoint params/assets 树，只核验其保留的 input-audit/config 溯源；未复查 HF 或作科学结论。Manager 仍负责最终科学裁决与论文计入决定。
