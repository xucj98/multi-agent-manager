# 当前 MAM 项目 state-vla 资源与 worktree 创建独立审计

审计时点：2026-09-12。范围严格限于 `/mnt/public/xcj/Projects` 当前 MAM 项目，以及该项目脚本、运行入口或软链接实际引用的外部路径。全程只读：未安装、未重建 worktree/venv、未运行 GPU/renderer、未读取活跃进程环境或停止任务。精简查询证据位于 `/mnt/public/xcj/Projects/multi-agent-manager/.tasks/48a1f57c-1978-466f-b41e-763b2acf72b8/evidence/observations.md`。

三个核心库的标准入口和抽样 worktree 基本符合“代码/venv 独立、数据与输出回链稳定源库”的设计。已证实两项运行边界问题：RMBench 历史 manifest 的 `policy/pi05/.venv` 在新 worktree 与 `wuwen-1` 都不可用；WARP cache 因 `.local` 回链而在所有 worktree 间共享。另有一个 OpenPI 数据根的显式传参缺口和一个 source-root Python 版本分歧，应在下次启动前补足 preflight。

## 资源总览

### 项目映射、登记与 worktree

`/mnt/public/xcj/Projects/.mam/env.json` 指定：

- `MAM_ROOT=/mnt/public/xcj/Projects/multi-agent-manager`
- `PROJECT_ROOT=/mnt/public/xcj/Projects`
- `MAM_BRANCH=project/state-vla`

本机 `/root/Projects` 是指向该 `PROJECT_ROOT` 的软链接；`wuwen-1:/root/Projects` 不存在。因此所有可跨节点复用的入口应继续使用 `/mnt/public/xcj/...`，不能把本机别名写入新脚本。

| 仓库 | 稳定 checkout / git common dir | 审计 HEAD | 已登记 worktree | 审计时状态 |
| --- | --- | --- | ---: | --- |
| OpenPI | `/mnt/public/xcj/Projects/openpi` / `.git` | `884e62bd7eb8` | 6 | 主 checkout 无本审计改动 |
| robot-bridge | `/mnt/public/xcj/Projects/robot-bridge` / `.git` | `ae8829658644` | 3 | 有其他任务留下的未跟踪文档，未触碰 |
| RMBench | `/mnt/public/xcj/Projects/RMBench` / `.git` | `2d590d64d618` | 6 | 主 checkout 无本审计改动 |
| OpenDM | `/mnt/public/xcj/Projects/opendm` / `.git` | `5a4ee39d7416` | 1 | 主 checkout 无本审计改动 |

`workspace/` 当前 7 个顶层目录均能对应 `.local/tasks/<TASK-ID>.json`；未见顶层未登记 workspace。`.local` 是 MAM 的 ignored 本地登记状态，`.tasks/48a1…/report.md` 是本任务待发布报告；只核验了 ID 与 record 的对应关系，没有读取其他任务正文。当前审计 task 自身 workspace 只含 `evidence/`，没有业务库 worktree；这是只读审计且无代码改动所致。

抽样使用已登记的 `cbbba844-d96a-45d5-9b2f-c8a3c6f393b1` workspace。其 OpenPI、robot-bridge、RMBench 三库都有独立 `.venv`，且共享实体均可达。这是对现有实际布局的观察，不代表重新创建或验收该任务。

### 物理资源、真实路径与容量

下表容量是对物理源目录的 `du -sh`，不跟随 worktree 的软链接；因此不能把链接端再次相加。受管安装使用 `uv --link-mode hardlink`，venv 的逻辑容量也不应简单当成新增独占空间。

| 用途 | 逻辑路径 | realpath / 存储属性 | 容量 | 创建或使用入口 | 确认 |
| --- | --- | --- | ---: | --- | --- |
| OpenPI 训练输出 | `openpi/checkpoints` | 同路径，稳定源库共享目录 | 99G | OpenPI wrapper 链接；训练配置写入 `checkpoints` | 已测量 |
| OpenPI 数据与 Memory v1 sidecar | `openpi/data` | 同路径；`data/lerobot/wash_cup_…` 物理目录 | 2.6G；wash v3 2.3G，`memory_v1` 22M | wrapper 链接；`examples/x2robot/README.md`、Memory v1 config | 已测量 |
| OpenPI robot norm | `openpi/assets/memory_v1` | 同路径，3 个 `norm_stats.json` 资产 | 3.5K | `config.py` 的 `assets/memory_v1` | 已测量 |
| RMBench simulator assets / data / 结果 | `RMBench/{assets,data,eval_result}` | 同路径，稳定源库共享目录 | 1.3G / 3.2G / 5.0G | RMBench wrapper 链接 | 已测量 |
| RMBench swap-block raw conversion | `RMBench/data/swap_blocks/demo_clean` | 同路径 | 3.2G | OpenDM/RMBench experiment README 引用 | 已测量 |
| Mem-0 模型与数据 | `RMBench/policy/Mem-0/{checkpoints,assets,lerobot_datasets}` | 同路径；checkpoints 由 tracked `_download.py` 与 ignored child 混合构成 | 76G / 20K / 163M | RMBench policy 扫描规则 | 已测量 |
| pi05 模型 | `RMBench/policy/pi05/checkpoints` | 同路径，稳定源库共享目录 | 70G | RMBench policy 扫描规则、评测入口 | 已测量 |
| OpenDM 基础/训练输出 | `opendm/{checkpoints,user_checkpoints}` | 同路径，稳定源库共享目录 | 18G / 627G | OpenDM wrapper、DM05 docs/manifest | 已测量 |
| OpenDM norm / data / logs | `opendm/{norm_stats,data,logs}` | 同路径，稳定源库共享目录 | 81K / 206M / 5.8M | OpenDM wrapper | 已测量 |
| RMBench LeRobot 数据 | `cache/huggingface/lerobot/{rearrange,put_back}_…shared_memory` | `/mnt/public/xcj/cache/...` 物理共享目录 | 4.4G / 4.7G | OpenPI `examples/rmbench/README.md` | 已测量 |
| Drawer LeRobot 数据 | `cache/huggingface/lerobot/drawer_sorting_x1pro_shared_memory_s2m_15hz_v2` | `/mnt/public/xcj/cache/...` 物理共享目录 | 5.5G | RMBench Memory schema README | 已测量 |
| wash / drawer 原始输入 | `/mnt/public/datasets/x1pro/{wash-cup,table_clean}` | 外部物理目录；只沿源码引用核验 | 未全量测量 | OpenPI 转换、RMBench drawer README | 存在已确认 |
| pi05 基础权重 | `/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base/params` | 项目外、但 `config.py` 明确硬编码的物理目录 | 12G | OpenPI `_PI05_BASE_PARAMS` | 本机与 wuwen-1 可达 |
| shared Python | `cache/shared-python/cpython-{3.10.19,3.11.14}` | `/mnt/public/xcj/cache/...` 物理共享解释器 | 83M / 92M | 四个 `.local/create_worktree.sh` | 本机与 wuwen-1 可达 |
| 离线 wheel / uv 工具 | `cache/dm05-worktree-wheels/{rmbench-…,cp310-…curobo…,opendm-…}` | `/mnt/public/xcj/cache/...` 物理共享目录 | 52M / 17G / 68M | RMBench/OpenDM wrapper 的固定参数与 hash 检查 | 已测量 |
| uv package cache | `cache/uv` | `/mnt/public/xcj/cache/uv` | 未全量测量 | 四个 wrapper 固定 `--cache-dir` | 存在已确认 |
| renderer/Warp cache | `RMBench/.local/warp-cache` | 同路径；`.local` 是稳定源库目录 | 6.0K | RMBench memory evaluation 脚本 | 已测量 |

OpenPI 的 99G checkpoints 由多组 RMBench 15G checkpoint、若干 4.9–5.0G 训练输出组成。OpenDM 的 627G `user_checkpoints` 中，`dm05_rmbench_swap_blocks_no_history` 为 164G、`dm05_manager_20260905T145925Z` 为 131G、`dm05_rmbench_swap_blocks_h30_smoke50` 为 104G，其余还有多个 11–44G run。它们并非仅凭名称即可判为可删除：OpenDM 与 RMBench 文档、input manifest 都实际引用其中的 formal checkpoint，且两条 formal 路径在本机与 wuwen-1 都可达。

`JAX_PLATFORMS`、`XLA_PYTHON_CLIENT_*`、`SAPIEN_RENDER_DEVICE` 由训练/评测命令注入；当前标准 create-worktree 入口没有声明固定 JAX/XLA/Torch 通用 cache 根。OpenPI 下载代码在未设 `OPENPI_DATA_HOME` 时会回退到 `~/.cache/openpi`，但本审计未扫描任何用户 home/cache。

## worktree 创建审计

### OpenPI

**参数合同与受管脚本。** `.local/create_worktree.sh BASE_COMMIT NEW_BRANCH WORKSPACE_ROOT` 只接受三个位置参数。它验证自己位于稳定主 checkout、解析 `BASE_COMMIT`，并从该 commit 读取 `scripts/worktree_env/create_worktree_env.sh` 后执行；旧 commit 缺少 `.local` contract 会被拒绝。目标固定为 `WORKSPACE_ROOT/openpi`，branch 由调用者传入。这样避免从 linked worktree 误把临时 checkout 当共享源。

**声明的创建行为。** 受管脚本创建 git worktree，链接稳定源库的 `.local`、`assets`、`checkpoints`、`data`、`datasets`、`logs`、`wandb`、`offline_test`、`offline_test_results`、`policy_records` 和其他已存在的 `offline_test*`。它用固定的 CPython 3.11、固定 uv 与 `cache/uv` 新建工作树私有 `.venv`，用 lockfile `sync --frozen --link-mode hardlink` 安装，并为 transformers patch 写入私有 inode；不链接 `.venv`、build/cache/site-packages。

**抽样实际。** cbbb workspace 的上述所有已存在共享条目均是到 `/mnt/public/xcj/Projects/openpi/<name>` 的可达软链；`openpi/.venv/bin/python` 指向 `/mnt/public/xcj/cache/shared-python/cpython-3.11.14-…/bin/python3.11`。这与声明一致。清理该 workspace 会移除其源码、git worktree 记录和独立 `.venv`，但不会释放 99G checkpoints、2.6G data 或任何共享 logs/结果。

**数据与权重入口。** 当前 Memory v1 配置的 base 参数是可达的项目外路径 `/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base/params`；当前 wash v3 物理数据则在已链接的 `openpi/data/lerobot/...`。后者的训练身份使用 `HF_LEROBOT_HOME`，详见发现 3。

### robot-bridge

**参数合同与受管脚本。** 同样采用三个位置参数与 `BASE_COMMIT` 版本绑定，目标固定为 `WORKSPACE_ROOT/robot-bridge`。它验证共享源、目标不存在、branch 合法和 `uv.lock` 与 `pyproject.toml` 一致。

**声明的创建行为。** 仅链接稳定源库 `.local`、`logs` 和 `eval_result`，刻意不创建或链接 checkpoint/dataset/OpenPI 根。它用固定 CPython 3.11、共享 uv cache 产生工作树私有 `.venv`，`uv sync --frozen --active --link-mode hardlink --extra dev` 后运行 hardlink probe 与 `pip check`。模型和数据继续由 config/环境参数引用。

**抽样实际与清理语义。** cbbb workspace 的 `.local`、`logs`、`eval_result` 都回链稳定源库；其 Python 指向 shared CPython 3.11。删除该 workspace 不会删除 208M bridge logs 或共享 eval 结果。

**主 checkout 环境。** 主 checkout 的 `.venv/bin/python` 却指向 `/mnt/public/tjh/miniconda3/bin/python3.13`（CPython 3.13），与标准 worktree 的 CPython 3.11 不同；该确切路径在 wuwen-1 也可执行。这是 source-root 遗留/维护环境，不是 wrapper 的标准运行环境，见发现 4。

### RMBench

**参数合同与受管脚本。** 入口同样为三个位置参数，目标固定为 `WORKSPACE_ROOT/RMBench`。它使用 CPython 3.10、共享 uv cache、固定 PyTorch3D wheel 目录和 cuRobo 目录，并检查 wheel SHA-256。受管脚本支持可选 `--opendm-root`，但标准三参数 wrapper 不传它，因此默认只安装 simulator profile，不安装 OpenDM editable client。

**声明的创建行为。** 必需且非空的 `assets`、`data` 被整体链接；`eval_result`、`logs`、`.local` 链接到稳定源库。对 `policy/*`，脚本只考察语义资源名 `checkpoints/assets/data/datasets/lerobot_datasets/ignoredassets/norm_stats/stats/statistics`，排除 `.venv`、cache、build、wheel、source 等环境目录；含 tracked 下载脚本的根不会整体链接，而是将 ignored 的资源 child 逐项链接。新 `.venv` 是工作树私有，安装 torch/cuRobo/PyTorch3D 后做 hardlink probe；GPU/render smoke 明确不属于创建入口。

**抽样实际。** cbbb workspace 的 `.local`、assets、data、logs、eval_result 都回链稳定源库，Python 指向 shared CPython 3.10。`policy/pi05/checkpoints`、`policy/DP/checkpoints`、`policy/Mem-0/assets`、`policy/Mem-0/lerobot_datasets` 也回链源库。`policy/Mem-0/checkpoints` 在 worktree 中保留为小目录，是因为 tracked `_download.py` 必须留下；其 Qwen3、m1_mix、mem0_swap 三个 76G weight child 均为回链软链，没有复制模型。此处与文档的“tracked 下载脚本不整体链接”一致。

**缓存与清理语义。** `RMBench/.local/warp-cache` 是稳定源库的 ignored 路径，cbbb 的 `.local` 又回链该目录。worktree 删除不会清除任何 shared assets/data/eval/logs/warp cache/policy checkpoint。RMBench 主 checkout 自带 8.0G `.venv` 与 83M `.python`；它和工作树环境不是同一路径。`policy/pi05/.venv` 另有 8.0G，且不是可移植资源，见发现 1。

### OpenDM（关联库补充）

OpenDM 同样提供三参数 wrapper，目标为 `WORKSPACE_ROOT/opendm`。它固定 CPython 3.10、共享 uv cache 与 decord/flash-attn wheel，要求 `data` 已存在且非空，链接 `.local`、`data`、`checkpoints`、`norm_stats`、`user_checkpoints`、`logs`，并创建私有 `.venv`。主 checkout 的 `.venv` 为 8.6G，Python 指向同仓库 `.python/cpython-3.10.19-…`；标准 wrapper 改用 `/mnt/public/xcj/cache/shared-python/cpython-3.10.19-…`。当前没有已登记的 OpenDM linked worktree，故未声称该路径的实际链接已抽样。

`user_checkpoints` 是有意共享的训练输出根：文档默认将训练写入该路径，RMBench 的 manifest 又按 `OpenDM/user_checkpoints/...` 引用 formal checkpoint。清理任一 OpenDM worktree 不会释放这 627G；这说明清理边界清晰，但不构成“可直接删除”的证据。

## 发现与建议

### 1. 已证实：RMBench 历史 pi05 interpreter 对新 worktree 与 wuwen-1 都不可用（P1）

**路径与证据。** 本机稳定源库 `RMBench/policy/pi05/.venv/bin/python` 是软链，realpath 为 `/root/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11`。抽样 cbbb worktree 中该 `.venv` 不存在，因为 RMBench create-worktree 规则明确排除 policy `.venv`。`wuwen-1` 上该 exact target 及经共享项目路径访问的 `RMBench/policy/pi05/.venv/bin/python` 都不存在。与此同时，`experiments/pi05_multitask_state_token_serial_soft/jobs_eval.json` 等历史 manifest 仍把 `policy/pi05/.venv/bin/python` 写为执行器。

**触发与影响。** 在新建 RMBench worktree 中，或在 wuwen-1 上按这些 manifest 执行时，进程会在启动前找不到 interpreter；这不是 GPU 可用性问题，而是路径/环境合同不成立。当前统一 Memory 脚本已改用 workspace 的 `openpi/.venv`，但旧 manifest 仍保留此入口。

**最小建议。** 不迁移现有模型。为这类 manifest 明确传入/解析 `$OPENPI_ROOT/.venv/bin/python`，或为 policy pi05 建立受标准 wrapper 管理的独立 profile；在每个节点的启动前只做 `test -x` preflight，并把选择的解释器写进 run metadata。

### 2. 已证实：WARP cache 因共享 `.local` 而不是 worktree 私有（P2）

**路径与证据。** 标准核心 wrapper 都将 `.local` 链接到稳定源库；抽样 cbbb 的三个 worktree 也都如此。`run_pi05_rearrange_full_smoke.sh` 默认将 `WARP_CACHE_ROOT` 设为 `$RMBENCH_ROOT/.local/warp-cache/memory_chunk_20260910/$RESULT_RUN`，`run_memory_schema_eval.py` 同样拼接 `.local/warp-cache`。解析后均落到 `/mnt/public/xcj/Projects/RMBench/.local/warp-cache`；现有目录已有 f0/gpu0、f0/gpu1 和一个 history run 的 robot/policy 子目录。

**触发与影响。** 不同 worktree 只要复用相同 group/result-run（或调用者没有覆盖默认值），就会向相同 cache 路径写入。workspace 删除也不会清掉它。当前未观察到冲突或损坏，因此问题是并发与清理边界风险，不是已发生的数据错误。

**最小建议。** 保持现有共享资产布局，但要求启动命令显式设置含 TASK-ID 与 result-run 的 `WARP_CACHE_ROOT`；创建前拒绝已有非空目标，任务归档后按该唯一目录核对再清理。

### 3. 已证实的配置缺口：wash v3 的数据根未由标准入口绑定（P2）

**路径与证据。** 当前 OpenPI Memory v1 wash 配置使用 repo-id `wash_cup_x1pro_s2m_memory_v1/all_172_…`，并在 policy metadata 中声明 `data_root_env=HF_LEROBOT_HOME`。物理转换数据存在于并由 worktree 链接的 `openpi/data/lerobot/wash_cup_…/all_172_…`（2.3G）；相同 repo-id 在已引用的 `/mnt/public/xcj/cache/huggingface/lerobot/` 下不存在。标准 create-worktree 只链接 `data`，没有设置或校验 `HF_LEROBOT_HOME`；OpenPI checkpoint metadata 仅会记录调用者已有的该变量。

**触发与影响。** 干净 worktree 若调用者未显式传入正确数据根，LeRobot 数据发现位置取决于外部环境而非 worktree 合同，可能查找错误 cache、尝试下载或直接失败。本审计没有读取任何活跃训练进程环境，因此不将此结论扩大为当前 20k 训练已错误。

**最小建议。** 在 wash 启动 manifest/README 中显式设置 `HF_LEROBOT_HOME=/mnt/public/xcj/Projects/openpi/data/lerobot`，并在 CPU preflight 中检查该 repo-id 目录和 sidecar；继续把实际值写入 checkpoint metadata。

### 4. 已证实的维护分歧：robot-bridge 主 checkout 与标准 worktree 使用不同 Python（P3）

**路径与证据。** 稳定主 checkout 的 `robot-bridge/.venv` 为 CPython 3.13，home 为 `/mnt/public/tjh/miniconda3/bin`；标准 wrapper 和抽样 worktree 使用 shared CPython 3.11。两者都当前可执行，且该 3.13 路径在 wuwen-1 也可达，因此不是跨节点失效。

**触发与影响。** 若开发者在主 checkout 直接复现，再在 worktree/远端执行，同一代码会经过两套解释器与依赖解。它扩大了诊断差异，尤其不利于将 source-root smoke 当作 worktree 结论。

**最小建议。** 将主 checkout `.venv` 标记为非标准维护环境；任务命令固定以工作树 `.venv/bin/python` 为准，并在启动记录中打印 Python realpath/version。

### 维护观察，不构成删除建议

- OpenPI checkpoints、RMBench eval_result、OpenDM user_checkpoints 都是可写的共享源目录，所有新 worktree 通过软链复用。当前命名中已包含多组实验/run，但 wrapper 不对输出名加锁或自动分 TASK-ID；并发时仍应在启动命令层保证唯一 output/run 名。
- 627G OpenDM `user_checkpoints` 中存在 smoke、retry 等名称，但文档和 manifest 仍引用其中的 formal 子树。本审计没有建立完整引用图或 hash 去重，不能以目录名或容量推断可删除。
- `/mnt/public/cache/openpi/...` 位于项目根外，却是当前 OpenPI config 的明确可达依赖，并在 wuwen-1 可达。它应在资源表中保留为 traced external dependency，而不是被误判为无关集群目录。

## 未覆盖 / 未确认

- 未运行 GPU、SAPIEN、Warp、cuRobo、训练、评测或重建环境；没有重复任何 smoke。
- 未读取活跃训练的完整命令、环境、日志或凭据，因此不判断正在运行任务的实际 HF/JAX/Torch cache 值。
- 未对 `/mnt/public/xcj/cache/uv`、原始 wash/table-clean 数据、全局 HuggingFace/Torch/JAX cache 做递归容量扫描；只测量了脚本/文档直接点名的具体项目资源。
- 未扫描任何用户 home、无关项目或集群 C；wuwen-1 只验证了精确项目依赖路径，wuwen-nx-aic 因无当前项目引用未连接。
- 未对 627G user checkpoints、99G OpenPI checkpoints 或 76G Mem-0 weights 做 hash 级重复检测；worktree 内的软链/目录类型与可达性已核验。
