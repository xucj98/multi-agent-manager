# 集群C state-vla 三库评估环境

## 预检与正式对照裁定待办（2026-09-11）

### 已确认的集群C连通性和共享状态

- `wuwen-4090-1`、`wuwen-4090-2`、`wuwen-4090-3` 均可通过 SSH 访问。
- 三机的 `/mnt/public` 都挂载自同一 yrfs；`state-vla`、`/mnt/public/xcj/cache/uv` 和 `/mnt/public/xcj/cache/shared-python` 的 inode 三机一致。`/mnt/public/xcj/Projects/state-vla` 已存在且为空。
- 共享 `uv` 缓存已有 5.9 GB，`shared-python` 为 80 MB；目标 `state-vla/.cache` 尚不存在。三机 `PATH` 均未发现 `uv`，仅有系统 `/usr/bin/python3` 3.12.3，因此仍须验证 shared-python 是否为真实、可跨机执行的解释器，并准备稳定的 uv 可执行文件。
- -1/-2 为 8 张 RTX 4090、驱动 550.127.08；-3 为 4 张 RTX 4090、驱动 580.82.07。-1/-2 的 GPU0 已有约 16.9 GiB 占用，-1 的 GPU3 也有约 1.3 GiB 占用；后续避开这些卡。驱动差异意味着环境须以 550 为最低约束，并在 580 上实测 CUDA 扩展与评测。

### 本机受管 worktree

已通过 MAM 创建干净、独立的检查/补丁 worktree：

| 仓库 | 路径 | base commit |
| --- | --- | --- |
| robot-bridge | `/mnt/public/xcj/Projects/workspace/5773b6ec-6584-42db-9d0d-9ef5d40f7c31/robot-bridge` | `f0f585a2b5974c60b51cac65277f94d1097591a3` |
| openpi | `/mnt/public/xcj/Projects/workspace/5773b6ec-6584-42db-9d0d-9ef5d40f7c31/openpi` | `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` |
| RMBench | `/mnt/public/xcj/Projects/workspace/5773b6ec-6584-42db-9d0d-9ef5d40f7c31/RMBench` | `6139577e360c27f866e4dbb3dd2fc067cc7ddd50` |

三树在创建后均干净。已阅读各库 AGENTS、worktree 环境说明及 RMBench 实验规范；openpi 与 RMBench 的受管环境脚本当前硬编码 uv hardlink 和 hardlink inode 校验，后续会在上述本机 worktree 中作保持默认 hardlink 行为的最小 symlink 模式兼容补丁，再提交供验收。

### 正式100的候选稳定对照与版本差异

已只读检查现有评测负责人任务 `e6908de7-4b02-465a-987b-a19eba7a315a` 的已发布报告。其正式 run `memory_chunk_20260910/put_back_full_t_plus_1_s0_20k_100ep` 已完整完成，报告记录为 69/100 success、100 个 episode、100 个视频和无 runtime error；这是候选对照，不等同于本任务已确认基线。

该 run 的冻结执行树为：RMBench `3e69b1e665a8eac0104d261b233f1b3339007e00`、robot-bridge `8ea6078543a875b5ae223df16891cdc1fe975c66`、openpi `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。本任务指定的环境版本分别是 RMBench `6139577e360c27f866e4dbb3dd2fc067cc7ddd50`、robot-bridge `f0f585a2b5974c60b51cac65277f94d1097591a3`、openpi `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`。RMBench 和 bridge 均不同，不能将两者混为严格同版本对照。

在 Manager 与评测负责人确认下列事实前，不会启动 C 的正式100或传输大模型/数据：

1. 该 69/100 run 是否被确认为稳定、可复用的正式基线；
2. 对应 checkpoint 的精确路径、hash、所需最小 assets/data 及冻结的命令、seed 序列、H/K/memory 协议；
3. 选择在 C 建立上述旧版严格运行树，还是先在本机以本任务新版本完成新的同版本 100 基线。

环境搭建、缓存核验、三库 clone、symlink worktree 入口及不依赖此裁定的验证继续推进；正式评测会在 smoke、干净提交和产物门禁之后登记 MAM job。
