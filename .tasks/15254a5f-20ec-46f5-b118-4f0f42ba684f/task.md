# put-back 基线窄审阅

独立 review OpenPI a7f3e07346cee7260cdc3a618eedc38c0702da61（相对a869498），源任务695bc51f。按MAM入口创建独立OpenPI worktree并读库AGENTS。只审此次两个训练配置和YAML/测试增量，不复查全schema。CPU审阅可与作者GPU smoke并行。

确认put-back serial_lag30/no-memory相对既有rearrange基线只改变任务数据/fields/norm资产；demo_clean_state与正确put-back robot14D norm，phase/origin_mat语义及时间offset无错配；serial target/teacher-forcing与no-memory robot-only语义正确，padding/loss不变，默认bs32/20k/pi05_base/BF16 final与原协议一致。必要真实CPU样本或针对性测试，不使用GPU，不运行20k，不改共享树或作者源码。

交付PASS或具体阻塞问题与证据，发布report，注明workspace/commit、检查范围。作者GPU保存恢复单独验收，本review不冒称已通过。清理自己的临时产物，保留独立worktree供Manager归档。优先快速交付可裁定结论，不扩大实验或实现范围。
