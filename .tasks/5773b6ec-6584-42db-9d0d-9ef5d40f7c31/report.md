# 集群 C state-vla 三库评估环境

## 状态（2026-09-11）

严格对照已由 Manager 批准：本机 `put_back_full_t_plus_1_s0_20k_100ep` 为
`69/100`、31 个正常任务失败、0 个 runtime error；C 的合格区间为 `64–74/100`。
C 只会在三机 smoke 通过、代码干净和产物门禁通过后启动单次正式 100 rollout；届时立即登记本机 MAM job。

## 连通性、稳定路径与风险

- `wuwen-4090-1/-2/-3` 均可 SSH。三机的 C `/mnt/public` 是同一 yrfs；C 的
  `state-vla`、`/mnt/public/xcj/cache/uv` 和 shared Python 路径可跨机读取。
- -1/-2 是 8×RTX 4090、driver `550.127.08`；-3 是 4×RTX 4090、driver `580.82.07`。
  每次 GPU smoke/正式启动前重新检查占用；不触碰其他人的服务或进程。
- 稳定解释器为 shared CPython 3.11.14（bridge/OpenPI）和 3.10.19（RMBench）；稳定 uv 是
  `state-vla/.cache/tools/uv/uv`，版本 `0.9.25`。所有 C 安装调用固定
  `/mnt/public/xcj/cache/uv` 且指定 `--link-mode symlink`，不使用 hardlink。
- 初始 C uv cache 为 `6,237,245,686` bytes。首次 bridge 安装正在向共享 cache 补齐缺失包，
  因此耗时和 cache 增长会与随后的命中安装区分记录。缓存是后续三机环境的稳定依赖，不会作为本任务临时产物清理。
- C 的 550/580 driver 差异和 PyTorch3D/cuRobo 二进制兼容性仍必须用实际 renderer/cuRobo 与三机 eval smoke 验证，不能仅以导入结果代替。

## 源码与本机受管改动

C 稳定源码根为 `/mnt/public/xcj/Projects/state-vla`，origin 保持 GitHub：

| 仓库 | C 源码提交 |
| --- | --- |
| robot-bridge | `f0f585a2b5974c60b51cac65277f94d1097591a3` |
| OpenPI | `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` |
| RMBench | `6139577e360c27f866e4dbb3dd2fc067cc7ddd50` |

GitHub 缺少直接 refs 的 OpenPI/RMBench 提交使用本任务临时 bundle 导入；不误称为 origin 的远端 ref。
本机 MAM worktree 中的最小 installer 兼容改动已提交，保持默认 hardlink 行为，仅为 C 增加受校验的 opt-in symlink 模式：

| 仓库 | 提交 |
| --- | --- |
| robot-bridge | `bdb41821039820f45c3f73ebc7db3c941a999b49`, `3ebf9d075e5e64a350ddb35cd8632e3abd04373c` |
| OpenPI | `3435a2b60bfb34197adeb8fe54ad750aeb78a5ed` |
| RMBench | `c59c6561de72092f95c14582ebaf8b1fe8728d00` |

这些 patch 已针对 current 和严格旧版 installer 的五种组合全部实测可应用。

## C 本地入口、资产和校验

- 已部署且 gitignored：
  - `state-vla/.local/create_worktree.sh`
  - `state-vla/{robot-bridge,openpi,RMBench}/.local/create_worktree.sh`
  - `state-vla/.local/patches/*-uv-symlink.patch`
- 各仓包装器均保留三参数接口：
  `bash .local/create_worktree.sh BASE_COMMIT NEW_BRANCH WORKSPACE_ROOT`。
  通用入口只从稳定 source 根建立 worktree，临时取出指定 commit 的安装脚本、施加已提交的 symlink patch、验证 `.venv` 至 uv cache 的真实 symlink，并防止创建 bridge `eval_result` 与 OpenPI `user_checkpoints`。
- 已经通过 `wuwen-nx-aic → wuwen-4090-aic` 同步并逐文件验证最小输入，而非复制全量训练数据：

| 输入 | C 目标 | 校验 |
| --- | --- | --- |
| checkpoint `20000` | `state-vla/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000` | 60 files、5,258,412,876 bytes，manifest `cb4032ce56b471eabb2f5138925af5cbce800cfbea8630aab85d44d9c665ab79` 全部通过 |
| embodiments、objects、`demo_clean_state`、PyTorch3D/cuRobo wheel | `state-vla/RMBench/{assets,data}` 与 `state-vla/.cache/{wheels,curobo}` | 355 files，manifest `22353e70420a0e474173413b3c18df6dc015506faf8352f31e06107f16bfcd4c` 全部通过 |

C 的 remote task root 是
`/mnt/public/xcj/Projects/state-vla/workspace/5773b6ec-6584-42db-9d0d-9ef5d40f7c31`；记录在其 `records/` 下。
目前仅建立了 `current/robot-bridge`，其实际安装命令、时间和磁盘测量日志是
`records/current-robot-bridge-create.log`，安装尚在进行，未将其误报为完成。

## 严格运行树与后续门禁

正式 C tree 将使用同级目录 `workspace/<TASK-ID>/formal/{RMBench,robot-bridge,openpi}`，固定：

| 仓库 | 严格运行提交 |
| --- | --- |
| RMBench | `3e69b1e665a8eac0104d261b233f1b3339007e00` |
| robot-bridge | `8ea6078543a875b5ae223df16891cdc1fe975c66` |
| OpenPI | `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` |

该旧 bridge 的 `openpi_client` 会按其已有 `scripts/deployment/install_openpi_client.sh` 从对应 OpenPI commit 构建的本地 wheel 正规安装到旧 bridge venv；最新 bridge 会单独证明没有此客户端依赖。不会用临时 `PYTHONPATH` 伪造旧环境。

待完成：三个 current `.local` 实测与磁盘表、strict tree 安装/客户端 wheel、renderer/cuRobo 和三机真实 smoke2、单次登记的 C 100 rollout、50 条中点核查、结果回传和最终清理/README。

## 阶段更新（2026-09-11 13:30 +08:00）

bridge 首次 cache-miss 创建从 11:47 开始，解析和本地 editable build 已完成；实际阻塞是
Fastly wheel 下载/解包，日志采样速度约 `45–50 KiB/s`，不适合继续盲等。已停止仅属于本任务的
旧 uv 进程并归档对应 MAM job，保留原始日志。随后从本集群现有 uv cache 精确同步 bridge 所需
`568.86 MB / 6,680 files`（约 94 秒），以 `UV_OFFLINE=1` 和 symlink 模式重新执行，`74` 个包
安装耗时 `8.74 s`；`current/robot-bridge` 的 CPU 环境 smoke 于 13:14 exit 0，`robot_bridge`
可导入，且最新 bridge 环境中 `openpi_client_spec=None`，符合“最新 bridge 不引入客户端依赖”。

OpenPI 的离线依赖计划已从本集群 cache 精确补齐 `8.27 GB / 45,468 files`，传输时段
13:10–13:26，实测 `8.78 MB/s`、无重试。跨机绝对 cache links 已改写为 C 的
`/mnt/public/xcj/cache/uv`（228 条重写、21 条已有效）；10 条直接 wheel link 缺失项存在
source-build/sdist fallback，须由下一步真实离线 `.local/create_worktree.sh` 验证，尚不声称成功。

当前 C 没有运行中的 uv；已完成的是 bridge 离线环境与 CPU smoke、OpenPI cache 预置。尚未创建
OpenPI/RMBench 环境，尚未进行 renderer/cuRobo、三机 smoke2 或正式 100 rollout。依 Manager
验收要求，bridge 这次“失败后补 cache”的过程不计入一键成功耗时；三库缓存齐备后会在全新、可清理
workspace 各实际执行一次入口，并单独记录可复现的一键创建耗时和磁盘变化。

## 执行快照（2026-09-11 13:36 +08:00）

当前 C 没有运行中的 `uv`、create-worktree 或 eval 进程。OpenPI 的首次离线入口于 13:32 在
`lerobot` build-system 的唯一缺项 `poetry-core` 处退出（exit 1，2 秒）；这不是解析、GPU 或公网
重试问题。已从本集群定位 `poetry-core 2.4.1` 的可复用 cache 对象。

首个精确补项 rsync 传输了 `1,435,790` bytes、208 files、耗时 2 秒，但目标校验立即发现该命令未保留
uv cache 的相对目录层级，因此尚未重试安装、也未将其计为成功。错位文件均为本任务刚创建的临时 cache
副本，将先删除，再以保留相对路径的单流 rsync 重放并重建 C 内部 symlink。没有新增三库代码提交；
独立 review `76b4c5b8` 可继续按已发布提交审查。

下一验收点：OpenPI `.local/create_worktree.sh` 在离线 symlink cache 下成功退出、完成其 CPU 环境
smoke；之后才开始 RMBench 的离线 cache 预检与创建。三库 cache 完整后会新建一次可清理验证树，重新
实际运行所有入口作为正式“一键”时间和磁盘测量，当前失败后的人工 cache 补齐过程不混入该结果。
