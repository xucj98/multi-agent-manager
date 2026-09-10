task_revision: 9f18ec39a280351dd3b678d9e6704087b2f2eccf

## CPU 准备完成，等待 GPU0 移交

未启动 GPU、训练、转换或 rollout，也未登记 MAM job。GPU0 仍由 F0 使用；收到
Manager 的完成核验与移交通知后，才按下列已冻结输入执行两条 BF16 smoke，再启动单卡
串行正式 100。

### 固定工作区与 CPU 检查

- workspace：`/mnt/public/xcj/Projects/workspace/35c9e781-7d2e-49a1-bb4c-25d77b865b3a`
- RMBench：`f022badd11228e5763a301339a5d1fe5574962b4`
- robot-bridge：`bc842036e3735390f35fe1138aa7b19f5ae2f95b`
- openpi：`58d6f2155acc3af03017677bb3f536101e6699f4`

三库 worktree 均干净。RMBench simulator import、robot-bridge
`scripts/worktree_env_smoke.py` 与 openpi `scripts/worktree_env_smoke.py` 均在
`CUDA_VISIBLE_DEVICES=''` 下通过。

FP32 参照从真实产物读取：
`f0_rearrange_full_h50_k30_row30_100ep_seed0` 为 92/100，固定
`rearrange_blocks`、`demo_clean_eval`、H50、K30、row30/index29、seed 0、接受
seed 100000--100099、前 5 条视频。其 `command.txt` 记录的源 manifest SHA 与当前
F0 源 manifest 一致，均为
`44a06fdbe40fa382de0371ff395afa4441b289fb7aeb97df6fb88fad050248c3`。

### 导出依赖与派生审计

已读取 ad6 已发布 report `04eee7a5cf20b4011406dbddc99bbbb148d7e1b8`。正式输入只读
使用：

`/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000`

其 `metadata/export_validation.json` 记录原 51 个 FP32 叶子经两条 BF16 restore
路径比较，3,353,433,872 元素的值不一致和 uint16 位模式不一致均为 0；`assets` 与继承
metadata 的原文件 hash 已由 ad6 核对。没有重做导出或复制 checkpoint。

任务私有输入位于：

- `.local/precision_validation/precision_rearrange_full_row30_bf16.manifest.json`
- `.local/precision_validation/precision_rearrange_full_row30_bf16.hash-evidence.json`

后者的 SHA256 为
`f9e39caceaa674840b8956057e4c1bb90993e484776707662ef0a85286a36e89`。它覆盖实际 BF16
checkpoint 的 31 个 `params/assets` 文件（5,257,196,338 bytes）和 8 个 metadata 文件
（37,206 bytes）。bridge 现有 `verify_audited_checkpoint` 与
`verify_audited_metadata` 已在 CPU 上重新逐文件验证，通过的 tree digest 为
`93188775f326dd9a20615359eb864771330e56b42f8a8ba1d7ca3b1c6af43d54`，metadata digest
为 `06fda2eb304188c093c80558db2e94bb8180c89d2f5e3ef07dde59215231d52e`。

### 命令与 manifest 差异审核

`run_f0.py` 将旧 checkpoint 和源 manifest 写死，不能直接调用。后续复用它实际生成的
底层 `rmbench_benchmark.py` 命令、robot/policy 服务命令、端口 19300/19302、GPU0 Warp
cache、scheduler 配置和所有 timeout；不增加 launcher 或修改任何源码。

派生 manifest 的 `pi05_rearrange_full` run/profile、`config_source`、`command_source`、
fixed seed/test_num/task/video 设置以及其他 checkpoint 都逐项与 F0 源 manifest 相同。
唯一输入变更为：

1. 增加 `OpenPI` source alias，并将该 run 的 checkpoint path 改为上面的 BF16 目录；
2. 将 params/assets、metadata、导出验证文件的 audit 路径与 hash 改为本任务私有证据；
3. policy server 继承原 `RB_OPENPI_POLICY_CONFIG=pi05_full_key_state`，仅将
   `RB_OPENPI_POLICY_DIR` 改为 BF16 目录；
4. 结果 leaf 分别为
   `precision_rearrange_full_row30_bf16_smoke_20260910` 和
   `precision_rearrange_full_row30_bf16_100ep_seed0`；formal 只额外引用前者作为
   `--smoke-run-dir`。

启动命令会同时传入
`--source-root OpenPI=/mnt/public/xcj/Projects/openpi`，因此 runner 的 policy metadata
握手会要求实际加载目录与派生 manifest 的 BF16 path 一致；随后沿原有 audit 验证所有
params/assets、metadata、scheduler 和 smoke source，不能静默落回 FP32 checkpoint。

### GPU 阶段计划

Manager 移交 GPU0 后，先在同卡执行 BF16 自己的两条 smoke（episode 0 视频、episode 1
无视频），核对真实 policy path、row30 trace、视频帧和完整 metadata；通过后按干净的
固定 SHA 可靠 detach 正式 100，并立即 `mam job add` 登记实际 host/PID。第 50 条人工
比较 FP32 参照，偏差超过 10 个百分点时保留结果并调查协议或异常。

源 manifest 的历史吞吐为 55.1 episode/hour，100 条约 1 小时 49 分；两条 smoke 约 2 分
多，加上服务启动、50 条人工检查和收尾，GPU0 预留约 2 小时。正式完成后再清理本任务
smoke 与临时输入，保留 BF16 checkpoint 和正式产物。

完成与未完成：CPU 环境、导出依赖、派生 manifest/audit 与差异审核已完成；BF16 smoke、
正式 100、50 条检查、逐 seed 配对统计和结果 README 尚未开始，等待 GPU0 移交。

workspace、各库交付 commit：上述三库均为固定 F0 SHA，当前无源码改动或新增 commit。
