# 新增两批 put-back J/T train1 eval2 正式证据核验

terra/max，只读窄范围审计；Manager负责科学裁决和论文。先读 MAM AGENTS/README/.local/README/.local/wuwen-4090.md，运行 mam task show 本 TASK-ID，读取源任务最新已发布 report 69466f383135109789662477684e0680b4291e7a 的最新部分。前次 review 7c2619 已验收归档，本次不再复查 HF。

范围仅 C1 `/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/` 的两个完成 leaf：
- c_put_back_full_t_plus_1_trainseed1_evalseed2_100ep_r3，声称58/100；final_review SHA be14b50e2d1b4834a37349921a7b83fe2eb3721f7262a5d0273cbbdcf2ccca78；cleanup 2cebc82e1a47fc3b90b4da5b05808e1607b539f7e4ff8214ca9cca51c668dcb1。
- c_put_back_full_t_plus_30_trainseed1_evalseed2_100ep_r3，声称62/100；final_review SHA a5bbb1ae0c73326326ead750b46c63ddf805d8e5c8fdaffc9ff2c93ef45ffd75；cleanup 79f2141bf0e859a947a6217b47105ab93062df85b9fe0b21bb716a4ec0d26f1d。

独立重哈希 final review 全部原件引用、preflight/diagnostics 重算100条连续 episode0..99 与 seeds300000..300099、不跳过不拼接；终态字段是 diagnostics.episode_status。重算 success/普通失败类别；核实100个episode/video策略、scheduler/process退出和基础设施日志。视频可依赖owner实际解码收据，明确不重复解码。matching smoke raw已获授权删除：只核查保留review/cleanup/hash链，不能声称重哈希不存在的raw。

实际冻结runtime c-eval-putback-baselines-yaml 三库 RMBench f401f5279c95451eb424ac98b831bab5552b2120 / bridge f9626636c4776d8eb15f9c556775cb2d12c000e5 / OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4；区别于 task登记的源worktree head。核对真实checkpoint train1、eval2、H50/K30、90/30秒、legacy continuous action RNG、metadata来源、command和matching smoke。终验器实际SHA 6368b249c1615ac35f87a813accaf1dfdcc895cf425e76fc442988cb4eb4c885；仅私有MAM ID更正是否与保留原件一致应核实。两个旧jobs 0f7daad0-ba87-41dc-8efd-57431d03a289 / 8883cf5e-9fd9-4255-b120-eac472a20c40 已归档。

不运行GPU/模型/仿真/训练，不拷大资产，不修改结果、冻结源码、owner report或论文；不触碰运行中train2 jobs，不归档源任务。无源码修改，无需无关worktree。小型证据/JSON receipt放本task目录，保留可供Manager独立核算的两叶原始preflight/diagnostics与final_review。可参考已归档afcae511工作流程但不得依其旧结果宣称本次通过。交精简报告、receipt路径/hash、实际检查与限制、是否有阻止计入正式结果的缺口，发布后结束turn。
