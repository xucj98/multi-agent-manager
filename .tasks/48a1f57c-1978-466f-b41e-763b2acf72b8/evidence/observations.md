# 48a1f57c 只读查询证据摘要

查询时间：2026-09-12（只读；未安装、未建 worktree/venv、未运行 GPU 或修改活跃任务）。容量均为对**物理源目录**执行的 `du -sh`；没有跟随 worktree 软链接，也没有相加 hardlink 视图。

## 范围与项目映射

- `/mnt/public/xcj/Projects/.mam/env.json`：`MAM_ROOT=/mnt/public/xcj/Projects/multi-agent-manager`，`PROJECT_ROOT=/mnt/public/xcj/Projects`，`MAM_BRANCH=project/state-vla`。
- 本机 `/root/Projects -> /mnt/public/xcj/Projects`；`wuwen-1:/root/Projects` 不存在。所有当前入口使用前者的 canonical `/mnt/public/xcj/...` 路径。
- 当前 `workspace/` 顶层有 7 个目录，均有相同 ID 的 MAM 本地 task record：`19e98…`、`48a1…`、`695b…`、`71e5…`、`7ae4…`、`cbbb…`、`e690…`；未见顶层未登记 workspace。这里只核对 ID/record 是否存在，未读取其他 task 正文。
- 本审计的 workspace 仅有 `evidence/`；没有创建业务仓库 worktree。

## 源仓库与 worktree 注册（`git worktree list --porcelain`）

| repo | 主 checkout / common dir | HEAD | 已登记 worktree 数 |
| --- | --- | --- | ---: |
| openpi | `/mnt/public/xcj/Projects/openpi` / `.git` | `884e62bd7eb8` | 6 |
| robot-bridge | `/mnt/public/xcj/Projects/robot-bridge` / `.git` | `ae8829658644` | 3 |
| RMBench | `/mnt/public/xcj/Projects/RMBench` / `.git` | `2d590d64d618` | 6 |
| opendm | `/mnt/public/xcj/Projects/opendm` / `.git` | `5a4ee39d7416` | 1 |

抽样 workspace 为已注册的 `cbbba844-d96a-45d5-9b2f-c8a3c6f393b1`。其 OpenPI、robot-bridge、RMBench 都有独立 `.venv`；`bin/python` 分别实链到 shared Python 3.11、3.11、3.10。所有抽样的共享入口均可达。

## 物理资源与明确外部依赖

| 路径 | 类型 / realpath | 容量 | 入口或用途 |
| --- | --- | ---: | --- |
| `openpi/checkpoints` | 源库物理目录 | 99G | OpenPI worktree 链接；训练输出 |
| `openpi/data` | 源库物理目录 | 2.6G | OpenPI worktree 链接；其中 wash v3 2.3G |
| `RMBench/assets` / `data` / `eval_result` | 源库物理目录 | 1.3G / 3.2G / 5.0G | RMBench worktree 链接 |
| `RMBench/policy/Mem-0/checkpoints` | 源库物理目录 | 76G | tracked `_download.py` 留在 worktree；3 个 ignored weight child 逐项软链 |
| `RMBench/policy/pi05/checkpoints` | 源库物理目录 | 70G | 抽样 worktree 整根软链 |
| `opendm/checkpoints` / `user_checkpoints` | 源库物理目录 | 18G / 627G | OpenDM worktree 链接；后者被文档和 manifest 明确引用 |
| `cache/shared-python/cpython-3.10.19` / `3.11.14` | 物理共享解释器 | 83M / 92M | 四个 `.local/create_worktree.sh` 固定使用 |
| `cache/dm05-worktree-wheels/*curobo*` | 物理共享 wheel/tool 目录 | 17G | RMBench/OpenDM wrapper 固定使用；含可执行 uv、cuRobo wheel |
| `cache/dm05-worktree-wheels/rmbench-*` / `opendm-*` | 物理共享 wheel 目录 | 52M / 68M | 对应 wrapper 的 PyTorch3D、decord、flash-attn wheel |
| `/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base/params` | 物理外部目录 | 12G | OpenPI `_PI05_BASE_PARAMS`；本机和 wuwen-1 可达 |
| `cache/huggingface/lerobot/{rearrange,put_back}_…shared_memory` | 物理共享目录 | 4.4G / 4.7G | OpenPI RMBench adapter README 明确引用 |
| `cache/huggingface/lerobot/drawer_sorting_x1pro_shared_memory_s2m_15hz_v2` | 物理共享目录 | 5.5G | RMBench drawer offline README 明确引用 |
| `openpi/data/lerobot/wash_cup_…/all_172_…` | 物理源库目录 | 2.3G | OpenPI wash v3 README 明确引用；同 repo-id 的 HF cache 路径当前不存在 |
| `/mnt/public/datasets/x1pro/{wash-cup,table_clean}` | 物理外部目录 | 未全量测量 | 分别被 OpenPI wash 转换与 RMBench drawer 文档明确列为只读 raw input |
| `RMBench/.local/warp-cache` | 源库 `.local` 内物理目录 | 6.0K | 当前脚本默认 `WARP_CACHE_PATH`；每个 worktree 的 `.local` 都回链此处 |

`/mnt/public/xcj/cache/uv` 已确认存在且是 wrapper 指定的共享 uv cache；为避免对巨型通用 cache 做全量扫描，本审计未测其总量。

## wrapper 声明与抽样实际链接

- OpenPI wrapper：固定 Python 3.11、共享 uv/cache；链接 `.local`、`assets`、`checkpoints`、`data`、`datasets`、`logs`、`wandb`、`offline_test*`、`policy_records`。抽样全部为到稳定源库的可达软链，`.venv/bin/python -> cache/shared-python/.../python3.11`。
- robot-bridge wrapper：固定 Python 3.11、共享 uv/cache；只链接 `.local`、`logs`、`eval_result`。抽样全部一致，`.venv/bin/python -> .../python3.11`。
- RMBench wrapper：固定 Python 3.10、共享 uv/cache、指定 PyTorch3D/cuRobo wheel；链接 `.local`、`assets`、`data`、`logs`、`eval_result` 和扫描到的 ignored policy 资源。抽样中 `Mem-0/assets`、`Mem-0/lerobot_datasets`、`DP/checkpoints`、`pi05/checkpoints` 都回链源库；`Mem-0/checkpoints` 本身保留 tracked `_download.py`，但 Qwen3、m1_mix 和 mem0_swap 的 ignored 子目录逐项回链，因此未复制 76G。
- OpenDM wrapper：固定 Python 3.10、共享 uv/cache、固定 decord/flash-attn wheel；链接 `.local`、必需 `data`、`checkpoints`、`norm_stats`、`user_checkpoints`、`logs`，并创建独立 `.venv`。当前无已登记的 OpenDM linked worktree 可抽样。

所有 wrapper 都由 `.local/create_worktree.sh BASE_COMMIT NEW_BRANCH WORKSPACE_ROOT` 进入；wrapper 检查稳定源库并用 `git show BASE_COMMIT:<managed script>` 执行受该 commit 约束的受管脚本。受管脚本使用 `uv --link-mode hardlink`，并在安装时做 hardlink inode probe；本审计没有重建以重复该安装检查。

## 精确远端可达性（wuwen-1）

只查询了项目脚本/软链明确引用的路径：

- 可达：`/mnt/public/xcj/Projects`、RMBench、shared Python 3.10/3.11、固定 uv、12G pi05 base params、robot-bridge 主 checkout `.venv/bin/python`、两条 OpenDM formal checkpoint 路径。
- 不可达：`/mnt/public/xcj/Projects/RMBench/policy/pi05/.venv/bin/python`。本机该链接实际指向 `/root/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11`；该 exact target 在 wuwen-1 不存在。
- 未查询 wuwen-nx-aic：当前入口没有对该节点的实际路径引用。

## 关键源码证据定位

- OpenPI `scripts/worktree_env/create_worktree_env.sh:223-340`；robot-bridge `scripts/worktree_env/create_worktree_env.sh:223-309`；RMBench `script/worktree_env/create_worktree_env.sh:224-500`；OpenDM `script/worktree_env/create_worktree_env.sh:203-334`。
- RMBench `experiments/memory_chunk_20260910/commands/run_pi05_rearrange_full_smoke.sh:22,64-65,84` 将 WARP cache 放在 `$RMBENCH_ROOT/.local/warp-cache/...`；`run_memory_schema_eval.py:149-158` 同样使用 `.local/warp-cache`。
- RMBench 历史 job manifest 仍写 `policy/pi05/.venv/bin/python`，例如 `experiments/pi05_multitask_state_token_serial_soft/jobs_eval.json:7`。
- OpenPI `src/openpi/training/config.py:1239,1314-1384`：当前 Memory v1 配置引用 `/mnt/public/cache/.../pi05_base/params`、wash repo-id，并在 metadata 中声明 `HF_LEROBOT_HOME`。入口脚本没有为该变量赋值；`examples/x2robot/README.md:22` 指向源库 data，且同 repo-id 在所列 HF cache 路径不存在。
- Drawer 路径由 RMBench `experiments/memory_chunk_20260910/README_memory_schema.zh-CN.md:120-124` 明确引用；raw wash/table-clean 由该文档和 OpenPI `examples/x2robot/README.md:7,36` 明确引用。
