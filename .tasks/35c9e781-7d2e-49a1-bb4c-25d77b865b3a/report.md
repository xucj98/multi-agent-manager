task_revision: 1dc0d33b8783f532702f33e597802d390d943c41

## CPU 留痕修正完成，GPU0 已移交

未改动三库源码，未重新导出、训练或复核全量权重。Manager 已在本 task 的 13:04
末节确认 F0 row1 完成、GPU0 的自有 PID/端口均已退出；GPU1 仍属 F0，不使用。

### 固定输入、主基线与资源预算

本次主配对参照固定为 F0 row30 的真实完整产物：

`RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/episode_diagnostics.jsonl`

其结果为 **92/100**，同一 seed 的前 50 条为 45/50。私有副本保留该 run 的
`config.yaml`、`command.txt` 和 `final_review_0100.json`，分别与源文件 SHA256
一致：

- config：`017ec9a140cd96e151165eccf1de51114988fec5a073cabd1f0b43074304fc4c`
- command：`075af2637974eab085e01b2eab175d2c823e76737b7656a7674fbca24dcd5280`
- final review：`a186c9b137619956d3387215afc9dca56f12116554dc85b932624c52b415e7ce`

主比较和 50 条中点检查均以 92/100 为完整基线，45/50 仅作同 seed 的辅助比较。
近期 F0 row30 的实测规划吞吐为 39.119719 ep/h，正式 100 加两条 smoke、服务启动和
检查预留约 3 小时；历史 93/100 与 55.1 ep/h 不用于本次比较或排程。

### 派生 manifest / lineage 差异

正式运行冻结使用任务私有目录：

`/mnt/public/xcj/Projects/workspace/35c9e781-7d2e-49a1-bb4c-25d77b865b3a/.local/precision_validation/inputs/precision_rearrange_full_row30_bf16`

- `input_manifest.json` SHA256：
  `f03b5c67b521774fe1a2bd9df511a13d7ae583ad7630cedfed0fd50a09df5ca8`
- `input_audit.json` SHA256：
  `869c6a8ff8cf22d2e8869b373b74caf89a0657d79da8db49031a73631bcc20cd`
- run 的 `config_source` 是
  `Audit/precision_rearrange_full_row30_bf16` 整个目录，`command_source` 为其中
  的 F0 command 副本；启动同时传入
  `--source-root Audit=/mnt/public/xcj/Projects/workspace/35c9e781-7d2e-49a1-bb4c-25d77b865b3a/.local/precision_validation/inputs`。

已用既有 `script.eval_diagnostics.inherit_metadata` 在 CPU 实际复制检查。
`checkpoint_metadata/lineage/config_source` 中无 skipped 项，`input_manifest.json`、
`input_audit.json` 及三份 F0 基线文件均与私有输入逐文件 SHA 一致；另有
`lineage/command_source/command.txt` 副本。检查目录为：

`/mnt/public/xcj/Projects/workspace/35c9e781-7d2e-49a1-bb4c-25d77b865b3a/.local/precision_validation/cpu_inheritance_check_v1`

相对 F0，派生输入只更换 `pi05_rearrange_full` 的 checkpoint 到已发布 BF16 路径、
其 params/assets 与 metadata audit/evidence，以及增加 `OpenPI`/`Audit` source
aliases；H50/K30、row30/index29、task、seed、采样、视频规则、legacy loader、
robot/policy 服务和 scheduler 均继承 F0。正式 smoke 将再次检查实际输出的 lineage。

BF16 checkpoint 只读路径为
`/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000`。
ad6 已发布的 `metadata/export_validation.json` 证明 51 个叶子、3,353,433,872 个元素在
两条 BF16 restore 路径上的数值与 uint16 位模式差异均为 0；本任务没有重复该全量验证。

### BF16 smoke 与正式启动

GPU0 上的 BF16 自己的两条 smoke 已完成，均为 Success（seeds 100000、100001）；episode 0
生成 382 帧视频，episode 1 按无视频路径完成。既有 smoke gate 已通过，记录的 config SHA256 为
`4e5cea45b647a12fa59327fc489174f6b631300a98105081ed7e149aa9e95dc0`。真实 policy path 为
BF16 checkpoint，params/assets digest 为
`93188775f326dd9a20615359eb864771330e56b42f8a8ba1d7ca3b1c6af43d54`，metadata digest 为
`06fda2eb304188c093c80558db2e94bb8180c89d2f5e3ef07dde59215231d52e`。每集执行的 trace 都是
selector index29 / row30（分别 13、14 个已执行块），且真实输出完整继承了五个 Audit
config_source 文件和 command_source。

正式 100 已于 **2026-09-10 13:20:30 +08:00** 在 GPU0 可靠脱离启动，主 runner 为
`is-dcfi2kjdq7g3k6aa-devmachine-0:2710786`，MAM job 为
`577e7ab0-eb55-4c65-bed5-3b725e958435`（实时 `mam job list --task` 状态为 running）。正式产物为：

`RMBench/eval_result/memory_chunk_20260910/precision_rearrange_full_row30_bf16_100ep_seed0`

首条 accepted rollout 已完成：episode 0 / seed 100000 / **Success**，391 step，12/12 任务条件为真、
无 failure reason，视频 391 帧通过。formal config 仍记录 BF16 checkpoint 和私有 manifest
SHA256 `f03b5c67b521774fe1a2bd9df511a13d7ae583ad7630cedfed0fd50a09df5ca8`；14 个已执行 query
trace 全部为 selector index29 / row30。runner 已在 formal 中接受同卡 smoke compatibility
(`4e5cea45b647a12fa59327fc489174f6b631300a98105081ed7e149aa9e95dc0`)。

### 后续检查

保持同一连续 run、GPU0 与冻结输入。按最新 MAM 规则以
`mam job list --task 35c9e781-7d2e-49a1-bb4c-25d77b865b3a` 刷新实际 job 状态；第 50 条按
92/100 主基线与 45/50 同 seed 辅助基线检查，完成后做逐 seed 配对统计、失败类别与结果 README。

完成与未完成：CPU 环境、输入留痕、基线修正、CPU/真实输出继承检查与两条 BF16 smoke 已完成；
正式 100 运行中，首条检查通过；50 条检查、100 条收尾、逐 seed 配对统计和结果 README 尚未完成。

workspace、各库交付 commit：RMBench
`f022badd11228e5763a301339a5d1fe5574962b4`；robot-bridge
`bc842036e3735390f35fe1138aa7b19f5ae2f95b`；openpi
`58d6f2155acc3af03017677bb3f536101e6699f4`。三库工作树干净，无源码交付 commit。

