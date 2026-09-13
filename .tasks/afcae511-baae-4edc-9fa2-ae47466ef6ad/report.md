# C1 put-back J/T train1·eval1 两批正式证据独立核验

已按发布任务 `96def958a3ce351e0a7877d40fd9dc38f0d4addb` 对源任务最新已发布 report `3cbcc4ce504b2aad8171425d5badf2d68cb3d6ed` 指定的两个完成 leaf 做只读核验。没有读取或改动 eval2、没有启动模型/仿真/GPU、没有修改源码、训练、checkpoint、源任务或论文。

核验对象均在 C1：

| arm | formal leaf | final review SHA-256 | 原始 diagnostics 重算 |
| --- | --- | --- | --- |
| J `full_t_plus_1` | `c_put_back_full_t_plus_1_trainseed1_evalseed1_100ep_r3` | `f02b472b80d9009bca1d26df66a77c343ea4e48d8c39a1b68c70e607f6d13cc3` | 47 success / 53 failure |
| T `full_t_plus_30` | `c_put_back_full_t_plus_30_trainseed1_evalseed1_100ep_r3` | `94f4e4297d3b63b69b09a4296a1ef0684b3bb138c57d9b250767e305e6ca752b` | 46 success / 54 failure |

两份 `final_review.json` 哈希均与任务声明一致。每份 final review 所列的 10 个相对原始 artifact（config、command、summary、preflight、diagnostics、processes、scheduler、video 和两份 copied input）均独立重哈希并逐项匹配。

原始记录重算结果如下：两批各有 100 条 accepted preflight 和 100 条 `episode_diagnostics`，episode ID 严格为 `0..99`，环境 seed 严格为 `200000..200099`，全部 100 条 `diagnostics.episode_status.terminal=true`。嵌套 `episode_status.success`、diagnostics success 和 result 文本三者一致。J 的正常失败为 `button_not_pressed_after_center=35`、`button_press_insufficient=18`；T 为 `40`、`14`；失败终态原因均为 `step_limit_reached`，与 47/100、46/100 算术一致。两批各有 100 个可解析的 `episode<N>.json`，且编号无缺口或重复。

两批均有 100 条 `video_checks`，全部 `ok=true`，编号连续；策略记录为 episode `0..4` 启用视频、其余不启用，启用文件存在且非空。没有在本次审计中重新解码 MP4；保留的 owner final-review 解码收据分别记录 J 的 328/322/355/356/321 帧和 T 的五个 500 帧视频。

每个 leaf 的 `processes.jsonl` 独立统计为 204 条：102 start、102 matching exit；100 个 scheduler exit 均为 0，robot/policy/scheduler 的 start/exit 身份集合相同。对完整 106 份文本运行日志（含 scheduler/worker、`eval_log.txt` 与 `_result.txt`）重新扫描，13 个既定基础设施 marker 均为 0；每批只有 1 条既有的非致命 `Failed to find Vulkan ICD file` warning。没有用当前端口或 PID 作为历史证明，以避免将仍运行的 eval2 对同一 C1 端口的合法复用混入本审计。

命令和 config 均确认 `put_back_block` / `demo_clean_eval`、training seed 1、eval seed 1、各自正确的 s1/20000 checkpoint、H50/K30（action horizon 50、move steps 30）、policy key 0 和 `fresh OpenPI Policy server per run` RNG 生命周期。正式命令含对应 matching smoke 引用。scheduler config 的 first infer 为 90 秒；冻结 runtime 的 `SchedulerBase` 仅把该预算用于首个 infer，之后不带 override 调用，而 transport 的默认 receive timeout 为 30 秒。

审计时 C1 runtime 三库都 clean，且 HEAD 分别为 RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `f9626636c4776d8eb15f9c556775cb2d12c000e5`、OpenPI `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。

matching smoke 已按规范删除 raw leaf，但保留链可核验：J smoke review `5bccf52dea1cec24f364d1edf874338ec1504add3ecbbfc7cfecf7801d64216f` 与 cleanup receipt `27554f8d38e3f5e72d25aef6e34bc2b45b044ba4f9691a6e5ffb8c45530cc33b`；T 分别为 `7a0954c15764ddbd801d242245932c9a47a4be04d2f4cab8bba5b55c646b3f85` 与 `4f95d22649baa237eff7042c3e4233d92ad929d04971b8e3ec0e852dca8a5331`。两份 cleanup receipt 都绑定 formal final-review hash、matching smoke 名称、retained copied input hash 和 completed-2 terminal/video/scheduler checks。删除后的 raw smoke artifact 不能再次重哈希，这是唯一固有的范围限制；本报告不把 surviving review/cleanup 误称为 raw smoke 重验。

本任务的独立只读 receipt 在 `evidence/c1_jt_train1_eval1_readonly_audit.json`，SHA-256 `78f0c059cc0508bdad91ed8555411a3f26595ba6657989fec40cd219337a34c9`，含 52 项通过检查、每个原件路径/claimed/actual hash、原始 JSONL 重算、日志 aggregate hash、视频策略、process 统计与上述限制。

在限定范围内，未发现阻止 Manager 将这两批作为完整正式评测证据纳入论文候选统计的证据缺口。此结论不替代 Manager 的独立抽核或论文裁决，也不对已删除 smoke raw leaf、未重复 MP4 解码、eval2 或任何超出这两批的结果作主张。
