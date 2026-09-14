# C1 put-back J/T train2/eval1 formal100 独立证据核验

结论为 **`pass_with_scope_limits`**：在两条已完成 formal100 的证据范围内，没有发现阻止计入正式结果的缺口。本审查不作科学结论或论文裁决。

| arm | formal leaf | 独立重算 | normal failures |
| --- | --- | ---: | --- |
| J `full_t_plus_1` | `c_put_back_full_t_plus_1_trainseed2_evalseed1_100ep_r3` | **70/100** | `button_not_pressed_after_center=20`、`button_press_insufficient=8`、`pressed_before_block_centered=1`、`block_not_moved_to_center=1` |
| T `full_t_plus_30` | `c_put_back_full_t_plus_30_trainseed2_evalseed1_100ep_r3` | **68/100** | `button_not_pressed_after_center=17`、`button_press_insufficient=15` |

任务本地复核器 [audit_formal_train2_eval1.py](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/8c780b1f-bffe-4f95-b17b-3d16d4de630d/evidence/formal_train2_eval1/tools/audit_formal_train2_eval1.py)（SHA-256 `40ef3541950c1231037438dcf54b1b295b52c925c1e3bd0d7dbae988ddd849ef`）完成 40 项检查。回执 [receipt.json](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/8c780b1f-bffe-4f95-b17b-3d16d4de630d/evidence/formal_train2_eval1/receipt.json) 的 SHA-256 为 `8f18a36aa368cd7f723d8eed62cc9c44fb14e229f7176bbfa2ed741125f0ba29`。

核验覆盖：每叶 final review 及全部 10 个核心引用的本地重哈希；100 条 accepted preflight、episode `0..99`、seed `200000..200099`、`diagnostics.episode_status.terminal`、结果和失败分类；100 个 video-check（仅 `0..4` enabled）、102/102 自有进程退出和 100 个 scheduler exit 0；各 29 个 copied checkpoint metadata 文件与 config 行；H50/K30、首 infer 90 秒、后续 RPC 30 秒、continuous action RNG 的冻结源码链；保存的 C1 inventory、106 份 formal 日志扫描、smoke review/cleanup 链及两条 archived MAM job。

两条 job 身份与 final review 一致：J `0ccf5f61-bd19-4df7-88dc-9ec2f49d79c4` / PID `1301506`，T `1ae7a228-0a13-4074-88ba-8b12886e1676` / PID `1301571`。task-local finalizer SHA-256 为 `a532cd5d6b76c637165b05c9d0a431f820ad11ea6f59d4f9aa763aae201aa423`；基础 finalizer 为 `c85e6eb4c8fda5f2af11550854e1427fbc8fca7b4ce99ecc6064cf5584b1b71a`。

范围限制：本审查没有再次解码视频；已授权删除的 matching-smoke raw leaves 不能重新哈希，改核验保留 review、cleanup、manifest 关系和 C1 不存在 inventory；约 5.26 GB 的每条 checkpoint params/assets tree 未复制或重哈希，改核验 retained input audit/config digest 行；未检查正在运行的 train2/eval2 或 HF 工作。

独立 review worktrees 未改动且 clean：RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。本任务没有源码交付 commit。
