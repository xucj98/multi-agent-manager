# 集群 C state-vla 资源位置与 worktree 创建只读审计

任务：71e53073-95cc-4e78-b16d-8d902ce710e5  
审计时间：2026-09-12 13:07–13:30 +08:00  
审计对象：wuwen-4090-1、wuwen-4090-2、wuwen-4090-3 上的 /mnt/public/xcj/Projects/state-vla  
精简原始证据：[evidence/snapshot.md](evidence/snapshot.md)

## 结论

三台 C 节点的 /mnt/public 是同一 yrfs 共享挂载；稳定三库、e690 活跃工作树、共享 Python、uv cache、wheel、模型、数据和结果都从这个挂载读取。当前 e690 三个 worktree 在三机上的 HEAD、分支和 clean 状态一致；所有审计到的工作树软链接、.venv 链接和解释器均可解析，没有指向 /root、/home、/tmp、已删除 03d538a0-f68e-45e6-9758-8539048b32d7 或传输节点路径的运行期链接。C2 抽样到的 formal 进程直接使用工作树 .venv/bin/python，不依赖 PATH 中的 uv。

资源位置本身满足当前 C 评测的共享部署模式，但不能把本报告视为重新执行的 smoke 或正式评测准入：本任务没有创建环境、运行 GPU、加载模型或重跑 smoke。发现四类已实证的问题或不一致：跨主机 Warp cache 的路径不具备每 run 唯一性；C 包装器的 symlink/bridge 输出行为与仓库环境指南不一致；e690 的相邻执行指南仍给出当前 C 上不存在的旧路径和 drawer 前置资源；逻辑上属于 e690 工作树的 .local 临时输入实际落在稳定共享目录。它们不影响已在运行的 C2 进程的可达性，但应在下一次新工作树或多机并发前处理文档和命名约束，不能对活跃树直接修补。

## 1. 范围、方法和边界

按 MAM AGENTS、README、.local 说明及本任务要求，先读取 MAM task show、C 稳定根 README、三库 AGENTS、三库 worktree 环境说明、真实 C 包装器/补丁/安装器、e690 实验说明与创建记录。本次通过只读 SSH 使用 stat、readlink、find、git、受限 ps 及仅列 cache 白名单的 /proc 环境查询；没有输出认证变量，没有修改/清理远端，没有建环境，也没有运行 GPU。

以下“当前”均指上述采样窗口。共享数据、模型和 uv cache 未做全量 du，避免在活跃共享文件系统上进行昂贵扫描；容量只引用已有创建记录、单个资源 stat 和小范围 cache 的 du。历史测量单列，不能当成本次运行结果。

活跃 e690 根为：

    /mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval

它包含活跃正式评测，整个审计期间未改动该根、其进程、结果 leaf 或 MAM job。

## 2. 三机、稳定 checkout 与工作树总览

### 2.1 共享存储与稳定入口

三机对 /mnt/public 的 findmnt 结果都是 yrfs；C 根 README 和四个创建入口在三机 SHA-256 相同。稳定根为：

    /mnt/public/xcj/Projects/state-vla

| 稳定库 | 当前稳定 HEAD | 分支状态 | 作用 |
| --- | --- | --- | --- |
| RMBench | 6139577e360c27f866e4dbb3dd2fc067cc7ddd50 | detached | 稳定 simulator、资产、数据、结果、共享 .local 和 common git dir |
| robot-bridge | f0f585a2b5974c60b51cac65277f94d1097591a3 | detached | 稳定 bridge、logs、共享 .local 和 common git dir |
| openpi | a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 | detached | 稳定模型代码、checkpoint、数据和 common git dir |

唯一兼容 shim 是：

    /mnt/public/xcj/Projects/RMBench
      -> /mnt/public/xcj/Projects/state-vla/RMBench

同级 /mnt/public/xcj/Projects/robot-bridge 和 openpi 不存在。shim 只服务旧绝对路径；它不是第二份 checkout。

### 2.2 当前 e690 工作树

三机在 13:30 的结果一致，三树 status 都为空：

| 库 | 创建时 base | 当前 HEAD / 分支 | common git dir |
| --- | --- | --- | --- |
| RMBench | 17b55bff1c79a0c5a836d1da089765934cb3a5b0 | 79334268e28ccd91c59049224aad8d0d799d11a7 / task/e6908de7-4b02-465a-987b-a19eba7a315a-c-eval-rmbench | state-vla/RMBench/.git |
| robot-bridge | 8ea6078543a875b5ae223df16891cdc1fe975c66 | f9626636c4776d8eb15f9c556775cb2d12c000e5 / task/e6908de7-4b02-465a-987b-a19eba7a315a-c-eval-robot-bridge | state-vla/robot-bridge/.git |
| openpi | a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 | a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 / task/e6908de7-4b02-465a-987b-a19eba7a315a-c-eval-openpi | state-vla/openpi/.git |

三个 current HEAD 都是创建 base 的后代。RMBench 从 17b55bff 前进到 7933426，提交说明为“配置：固定 C 首次 infer 90 秒预算”；bridge 从 8ea6078 前进到 f962663，提交说明为“Allow a bounded cold-start policy inference budget”。e690 当前运行配置固定要求 bridge f962663 和 openpi a869498，并只要求 RMBench 的 f022badd 为当前 HEAD 的祖先；实际满足这些判断。

每个 worktree 的 .git 是普通文本文件而不是独立 git 目录，分别指向稳定源库 .git/worktrees/RMBench3、robot-bridge3、openpi3。这解释了源码 branch 隔离与 git objects/common refs 共享的关系。

创建记录的时间为 03:45–03:49，记录的非跟随大小与链接数如下。这是当时创建完成的记录，不是本次重新测量。

| 库 | 记录耗时 | regular files | directories | symlinks | bytes，不跟随链接 |
| --- | ---: | ---: | ---: | ---: | ---: |
| RMBench | 52 s | 1,990 | 5,198 | 62,638 | 51,425,792 |
| robot-bridge | 17 s | 529 | 1,499 | 14,485 | 12,377,600 |
| openpi | 32 s | 1,033 | 4,265 | 45,074 | 32,592,896 |

## 3. 资源清单与物理位置

### 3.1 源码、数据、模型和结果

| 逻辑资源 | 实际位置 / realpath | 共享性、创建者和使用者 | 当前状态 |
| --- | --- | --- | --- |
| 稳定源码 | state-vla/RMBench、robot-bridge、openpi | 三机共享；稳定源持有 common git dir | 三库均为真实目录，不是二次软链接 |
| e690 源码与私有 .venv | state-vla/workspace/e690…/c-eval/<repo> | 共享工作树；C1 创建，C1/C2/C3 都可运行 | 当前三树 clean；.venv 目录属于工作树 |
| RMBench simulator 资产 | state-vla/RMBench/assets，子项 embodiments、objects | 稳定共享；e690 RMBench/assets 是绝对软链接 | 存在 |
| RMBench benchmark 数据 | state-vla/RMBench/data，当前有 put_back_block | 稳定共享；e690 RMBench/data 是绝对软链接 | 存在 |
| RMBench 结果与日志 | state-vla/RMBench/eval_result、logs | 稳定共享；e690 的 eval_result/logs 都链接至此 | memory_chunk_20260910 正在写入；不可随工作树删除 |
| RMBench policy 资产 | stable policy/DP/checkpoints、policy/pi05/checkpoints | 稳定共享；仅这两个符合当前扫描条件并被 e690 链接 | 存在 |
| bridge 日志 | state-vla/robot-bridge/logs | 稳定共享；e690 bridge/logs 链接至此 | 有 policy_server、scheduler、robot_server 子项 |
| OpenPI 模型与数据根 | state-vla/openpi/assets、checkpoints、data、datasets | 稳定共享；e690 对应根均链接至此 | checkpoints 有 6 个 rmbench 20k 配置根 |
| OpenPI 运行记录根 | state-vla/openpi/logs、wandb、offline_test、offline_test_results、policy_records | 稳定共享；e690 对应根均链接至此 | 当前均为真实稳定目录 |
| e690 的审计输入 | e690/RMBench/.local/memory_schema_eval/inputs 的 realpath 为 state-vla/RMBench/.local/memory_schema_eval/inputs | 逻辑上从 e690 访问，物理上稳定共享；由运行入口写入 | 有 input_audit.json 和 input_manifest.json，按 variant 和 checkpoint 路径 hash 命名 |
| 当前 formal leaf | e690/RMBench/eval_result 的 realpath 为 stable RMBench/eval_result | 稳定共享；runner 及记录器写入 | C2 采样到 serial_lag30 与 no_memory formal 进程 |

当前活跃 checkpoint 采用稳定 OpenPI 根，例如：

    state-vla/openpi/checkpoints/
      pi05_rmbench_rearrange_blocks_serial_lag30/
        memory20k_e7e5ac54_rearrange_serial_lag30_s0/20000

    state-vla/openpi/checkpoints/
      pi05_rmbench_rearrange_blocks_no_memory/
        memory20k_e7e5ac54_rearrange_no_memory_s0/20000

两个已抽查叶都含 _CHECKPOINT_METADATA、params、assets、metadata。当前运行命令由 checkpoint metadata 和配置推导，不需要把 checkpoint 复制到工作树。

按名称和浅层目录审计，RMBench 的模拟器资源还包括 assets/embodiments/aloha-agilex/meshes 与 assets/objects；RMBench assets/data 在深度四以内没有名为 raw 或 converted 的目录。stable openpi/data 与 openpi/datasets 在快照时为空目录。当前 memory-schema evaluator 只从 checkpoint 读取 train config、datasets metadata 的 repo_id、assets/params/metadata 和 upstream source_data_config.yaml，以确认 demo_clean_state 来源、schema、H50/K30 与归一化资产的可审计性；它没有在该入口中遍历或加载 openpi/data、openpi/datasets 的训练样本。每个已抽查 20k checkpoint 都有 assets/<robot>/norm_stats.json 与 params/_METADATA。这个结论限定于当前 evaluator，不外推到训练或 drawer offline。

### 3.2 共享安装资源

| 资源 | 路径 | 用途与验证 |
| --- | --- | --- |
| C 中央创建器 | state-vla/.local/create_worktree.sh | SHA-256 为 adfc2ce…4bb24a6；选择库、固定 Python/cache、从 base 取安装器并套 C 补丁 |
| 稳定 uv | state-vla/.cache/tools/uv/uv | 55,401,344 B，SHA-256 为 6db762…05bf55；创建记录使用 uv 0.9.25 |
| uv cache | /mnt/public/xcj/cache/uv | 三机共享、可写；所有已抽查 venv 的依赖 symlink 最终指向 archive-v0 |
| CPython 3.10.19 | /mnt/public/xcj/cache/shared-python/cpython-3.10.19-linux-x86_64-gnu/bin/python3.10 | RMBench .venv/bin/python 的最终目标；SHA-256 为 685193…c40f6a5 |
| CPython 3.11.14 | /mnt/public/xcj/cache/shared-python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 | bridge/openpi .venv/bin/python 的最终目标；SHA-256 为 76c511…81ef81 |
| PyTorch3D wheel | state-vla/.cache/wheels/pytorch3d/pytorch3d-0.7.8-cp310-cp310-linux_x86_64.whl | RMBench 离线安装；54,377,993 B，SHA-256 为 10b960…78b51 |
| cuRobo wheel | state-vla/.cache/curobo/wheel/nvidia_curobo-0.7.8-cp310-cp310-linux_x86_64.whl | RMBench 离线安装；67,284,731 B，SHA-256 为 780a87…4f988 |
| RMBench 离线锁 | state-vla/.local/locks/RMBench-cp310-split-lock-v1/cu121.txt、pypi.txt | 普通文件，不是链接；SHA-256 分别为 5bcc1a…8b084、4b2cac…23d1b6 |
| C 安装器补丁 | state-vla/.local/patches | 包含三库 symlink-mode patch、RMBench offline-lock patch 及 lazy-probe patch |

中央创建器传入 --link-mode symlink。因而“工作树私有 .venv”只表示 venv 目录本身在工作树；大部分三方文件并不复制，仍依赖共享 uv archive。当前原始链接分类如下：

| .venv | 总链接 | 共享 uv archive | 共享 Python | 相对链接 | 悬空、/root、/home、/tmp、旧任务目标 |
| --- | ---: | ---: | ---: | ---: | --- |
| RMBench | 62,631 | 62,627 | 1 | 3 | 0 |
| robot-bridge | 14,483 | 14,479 | 1 | 3 | 0 |
| openpi | 45,064 | 45,060 | 1 | 3 | 0 |

相对链接是 venv 内部链接，例如 lib64 -> lib；其余依赖链接为绝对共享路径。非 .venv 链接也全部通过 find -xtype l 检查，无悬空项。

### 3.3 节点私有和默认 cache

三机都没有 PATH 中的 uv，但三个工作树解释器在三机都存在且可执行。因此 C2/C3 运行依赖共享解释器、共享 venv 链接和共享 uv archive，不依赖 C1 的 shell PATH 或 node-private uv。

| 节点 | /root/.cache 拓扑 | 审计到的默认 cache | 解释 |
| --- | --- | --- | --- |
| C1 | /root/.cache 是到 /mnt/public/xcj/cache 的符号链接 | uv 23,224,213 KiB；pip 4,310,482 KiB；torch 70 KiB；warp 846 KiB | 这些读数是共享存储，不是 C1 独占副本 |
| C2 | overlay 内真实目录 | 无 uv、HF、JAX、XLA；torch 76 KiB；warp 876 KiB；pip 2,944 KiB | node-private 默认 cache |
| C3 | overlay 内真实目录 | 无 uv、HF、JAX、XLA；torch 76 KiB；warp 876 KiB；pip 2,944 KiB | node-private 默认 cache |

C1 的差异来自父目录 /root/.cache 的链接，而非 uv 子目录链接。中心包装器始终显式使用 /mnt/public/xcj/cache/uv，因此当前创建流程不依赖这种差异；但任何未设置 cache 环境变量的未来程序在 C1 会写共享路径，在 C2/C3 会写本地 overlay。

本次没有发现 /mnt/public/xcj/cache/huggingface、/mnt/public/cache/openpi、/root/.cache/huggingface、/root/.cache/jax、/root/.cache/xla、/root/.cache/sapien 或 /root/.cache/mesa。三机的 renderer ICD 文件 /usr/share/glvnd/egl_vendor.d/10_nvidia.json 均存在；它是节点私有系统资源，不在共享挂载中。

## 4. Worktree 创建审计：RMBench

### 调用入口、参数和实际创建记录

库入口为 state-vla/RMBench/.local/create_worktree.sh，内容只将库名 RMBench 转交给中央创建器。统一参数顺序为：

    BASE_COMMIT NEW_BRANCH WORKSPACE_ROOT

e690 创建时的等价调用参数为：

    17b55bff1c79a0c5a836d1da089765934cb3a5b0
    task/e6908de7-4b02-465a-987b-a19eba7a315a-c-eval-rmbench
    /mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval

记录显示在 C1 创建，完成耗时 52 秒。中央创建器先在稳定 RMBench 解析 base SHA，再以 git show BASE:script/worktree_env/create_worktree_env.sh 取该 commit 的受管安装器至 state-vla/.cache 的临时文件，套用 symlink、offline-lock 与 lazy-probe 补丁，最后以 --workspace、--ref、--branch、--source-root 调用。临时安装器受 trap 清理；本次审计未触发创建器。

### 实际软链接

下面每条均为绝对软链接，目标已存在且本次无悬空项：

| worktree 路径 | 物理目标 |
| --- | --- |
| .local | state-vla/RMBench/.local |
| assets | state-vla/RMBench/assets |
| data | state-vla/RMBench/data |
| eval_result | state-vla/RMBench/eval_result |
| logs | state-vla/RMBench/logs |
| policy/DP/checkpoints | state-vla/RMBench/policy/DP/checkpoints |
| policy/pi05/checkpoints | state-vla/RMBench/policy/pi05/checkpoints |

安装器要求 assets、data 是已存在的审计过资源；输出根 eval_result、logs 归稳定源。policy 下按 ignored、无 tracked 冲突、无 source/.venv/cache/build 的语义资产规则扫描。当前来源中只有 DP 和 pi05 的 checkpoints 被实际链接，不能把指南列出的所有候选名误写成实际已链接资产。

### Python、依赖和运行边界

RMBench 固定 CPython 3.10.19、稳定 uv 和 /mnt/public/xcj/cache/uv，显式设 UV_OFFLINE=1。它用上表两份离线锁安装 PyTorch/cu121 与 PyPI 闭包，再从稳定 wheel 路径安装 PyTorch3D 0.7.8 和 nvidia-curobo 0.7.8。创建记录确认 symlink=PASS、uv link mode: symlink 和 offline dependency locks。它不在创建阶段启动 GPU 工作。

创建时 C1 需要稳定源、git、patch、绝对 uv、共享 Python、共享 cache、两份锁和两个 wheel 都可读。C2/C3 运行时只需共享工作树、稳定资源、共享 Python 与 uv archive；实际 e690 命令可直接运行 .venv/bin/python。

删除该 worktree 只会移除其 git worktree 元数据、源码副本、.venv 目录及其中的 symlink。它不会删除 assets/data/eval_result/logs/policy checkpoint、stable .local、共享 Python、uv cache、wheel 或锁。尤其不能跟随 eval_result 或 .local 链接删除稳定目录。

## 5. Worktree 创建审计：robot-bridge

### 调用入口、参数和实际创建记录

库入口将 robot-bridge 转交给同一个中央创建器。e690 创建时使用：

    8ea6078543a875b5ae223df16891cdc1fe975c66
    task/e6908de7-4b02-465a-987b-a19eba7a315a-c-eval-robot-bridge
    /mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval

创建记录显示 C1、17 秒、uv 0.9.25、CPython 3.11.14。当前分支随后前进到 f962663；当前 e690 运行配置明确检查这个 commit，因此不能把创建 base 和当前运行版本混为一谈。

### 实际软链接

| worktree 路径 | 物理目标 |
| --- | --- |
| .local | state-vla/robot-bridge/.local |
| logs | state-vla/robot-bridge/logs |

中央 C 包装器额外传 --no-eval-result。故 bridge/eval_result 在稳定源和 e690 worktree 中都没有创建；RMBench/eval_result 是唯一评测输出所有者。这个差异是有意的 C 部署策略，且创建记录和创建器结束检查都能证明。

### Python、依赖和运行边界

受管安装器用冻结 uv.lock、--extra dev、CPython 3.11.14、共享 uv cache 与 symlink mode 创建 venv；创建记录的 lockfile SHA-256 是 d0b8ab334df0387d2d53dcf7c6acc29a48252b733b0d6c187e46e19136180b58。当前 14,479 条依赖链接指向共享 archive，1 条解释器链接指向共享 Python，另有 3 条内部相对链接。

C2 活跃 formal 的 outer runner 和 robot server 都直接使用此工作树的 .venv/bin/python。它使用 worktree 源码、共享 logs、RMBench 的资源和 OpenPI checkpoint；bridge 本身不创建数据集、checkpoint 或 OpenPI 根。

删除该 worktree 会移除 bridge 源码、私有 venv 和本地 git worktree 记录，但保留稳定 logs、.local、共享 Python/cache，以及 RMBench 的评测结果。不得为了清理 bridge 而新建或删除 bridge/eval_result。

## 6. Worktree 创建审计：openpi

### 调用入口、参数和实际创建记录

库入口将 openpi 转交给中央 C 创建器。创建参数为：

    a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4
    task/e6908de7-4b02-465a-987b-a19eba7a315a-c-eval-openpi
    /mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval

该库当前 HEAD 未变化。记录显示 C1、32 秒、uv 0.9.25 和 CPython 3.11.14。

### 实际软链接

| worktree 路径 | 物理目标 |
| --- | --- |
| .local | state-vla/openpi/.local |
| assets | state-vla/openpi/assets |
| checkpoints | state-vla/openpi/checkpoints |
| data | state-vla/openpi/data |
| datasets | state-vla/openpi/datasets |
| logs | state-vla/openpi/logs |
| wandb | state-vla/openpi/wandb |
| offline_test | state-vla/openpi/offline_test |
| offline_test_results | state-vla/openpi/offline_test_results |
| policy_records | state-vla/openpi/policy_records |

所有条目为绝对链接且当前存在。创建器会附加所有通过约束的 offline_test* 根；当前 e690 恰好只有表中这十条非 venv 链接。

### Python、锁、LFS 和 transformers 私有补丁

安装器要求 tracked uv.lock，执行 lock --check 及 sync --frozen --active，带 GIT_LFS_SKIP_SMUDGE=1、CPython 3.11.14、共享 uv cache 和 symlink mode。创建记录的 lockfile SHA-256 是 a7208df75353ecf362154790d70d1d77f21e6de572cbbcb743f0e4e604f82ab2。

openpi 的 C patch 将原先基于 hardlink 的 transformers 替换逻辑改为保留 venv spelling，从而不向共享 uv archive 写入。创建日志写有“transformers patch: private files installed”。本次抽查五个替换文件都为 .venv 内普通文件，与工作树 src/openpi/models_pytorch/transformers_replace 中的 SHA-256 相同：Gemma 的 configuration/modeling、PaliGemma modeling、SigLIP check/modeling。其余 45,060 条依赖链接仍指向共享 archive，解释器链接指向共享 CPython。

C2 的 policy server 实际使用 openpi/.venv/bin/python，并以 stable openpi/checkpoints 作为 policy 目录。删除 openpi worktree 只移除源码、私有 venv、五个私有 transformers 替换文件和 git worktree 元数据；不会删除稳定 checkpoints/data/datasets、各记录根、共享 Python/cache 或 wheel。

## 7. 活跃运行期资源、cache 和删除边界

### 7.1 C2 的实测运行命令路径

采样时 C2 有两套 e690 formal outer runner、robot server、policy server。它们使用：

    e690/c-eval/robot-bridge/.venv/bin/python
    e690/c-eval/openpi/.venv/bin/python

而非 uv run 或 PATH 中的 uv。runner 的结果目录经 e690/RMBench/eval_result 解析到 stable RMBench/eval_result/memory_chunk_20260910/<run>。当前运行还通过 source-root 明确传入 e690 RMBench、stable OpenPI checkpoint 和 e690/RMBench/.local 下的 Audit 输入目录。

policy 子进程带：

    WARP_CACHE_PATH=
      e690/RMBench/.local/warp-cache/memory_chunk_20260910/schema/gpu2/policy
      或 gpu3/policy

robot 子进程使用相同层次的 robot 路径。policy 还带 XLA_PYTHON_CLIENT_MEM_FRACTION=0.4。没有发现 HF_HOME、HF_HUB_CACHE、HUGGINGFACE_HUB_CACHE、TRANSFORMERS_CACHE、TORCH_HOME、XLA_CACHE_DIR、JAX_COMPILATION_CACHE_DIR、CUDA_CACHE_PATH、TMPDIR、TEMP、TMP 或 XDG_CACHE_HOME 的显式值。上述 XLA 变量是显存分数，不是磁盘编译 cache 路径。

RMBench/.local 本身是链接，因此这些 WARP_CACHE_PATH 的物理父根会是：

    /mnt/public/xcj/Projects/state-vla/RMBench/.local/warp-cache/...

采样两次都没有发现 schema/gpu2 或 schema/gpu3 的实际目录。不能据此判断 Warp 从未写过 cache，只能确认活跃命令配置了该路径而本次采样未见落盘目录。

### 7.2 共享结果、审计输入与删除

RMBench 的 eval_result、logs、.local 都是稳定共享对象。尤其 memory_schema_eval/inputs 不是随 e690 目录物理消失的 task-private 文件：worktree 的 .local 链接使其持久化在 stable RMBench/.local。e690 指南要求在 formal 完成、确认结果已继承 input_audit/input_manifest 后清理对应输入；操作时必须按真实 stable 路径和 owner 边界执行，不能将整个 .local 当作可删工作树内容。

共享 uv archive 同样不能在任意一个 worktree 删除时清理。当前三 venv 依赖它；删除 cache 会让仍存在的 .venv 失效。稳定数据、模型、结果、.local、shim、离线锁和 wheel 的生存期都独立于单个 worktree。

### 7.3 HuggingFace、Torch、JAX/XLA、Warp、renderer 和临时路径

| 类别 | 当前可证实的位置 | 结论 |
| --- | --- | --- |
| HuggingFace | /mnt/public/xcj/cache/huggingface、/mnt/public/cache/openpi、三机 root/.cache/huggingface 都不存在 | 当前 simulation 进程未设置 HF cache 环境；未做模型下载测试，不能证明后续任务永远不需要 HF |
| Torch | C1 的默认 torch 位于共享 cache 下；C2/C3 位于各自 root/.cache/torch | 没有 TORCH_HOME 显式覆盖；当前体积很小 |
| JAX/XLA | 三机未发现 root/.cache/jax/xla，活跃 policy 没有持久编译 cache 环境变量 | 只有 XLA_PYTHON_CLIENT_MEM_FRACTION=0.4；没有对 JAX 实际按默认行为写 cache 作推断 |
| Warp | 活跃命令显式使用 stable RMBench/.local/warp-cache 的 gpu 编号目录 | 路径存在于配置，采样时对应目录未落盘 |
| renderer | 三机都有 /usr/share/glvnd/egl_vendor.d/10_nvidia.json；活跃命令有 SAPIEN_RENDER_DEVICE=cuda:0 | 系统 ICD 是节点私有资源；未发现 SAPIEN/Mesa cache 目录 |
| temporary | 未找到 task 名或 state-vla 名的 /tmp 路径 | 安装器临时文件位于 state-vla/.cache 并由 trap 清理；未把此结论外推为所有第三方库均不会用 /tmp |

e690 的 drawer offline 指南要求的 /mnt/public/xcj/cache/huggingface/lerobot/drawer_sorting_x1pro_shared_memory_s2m_15hz_v2 和 /mnt/public/datasets/x1pro/table_clean 在 C 当前均不存在。这是 drawer 入口的未满足前置条件，不影响正在运行的 simulation checkpoint 评测；不得为本审计自动传输、建链接或下载数据。

### 7.4 已删除工作树和传输节点排除

已检查常见的旧 03d538a0-f68e-45e6-9758-8539048b32d7 workspace 与 /tmp 根，均不存在。当前 e690 的非 venv 软链接、.venv 原始目标和非二进制文本扫描没有该 ID，也没有 wuwen-nx-aic 或 wuwen-4090-aic。静态源码中可见的 /root、/home、/tmp 文本来自上游测试/辅助脚本，未出现在当前 e690 的解释器、链接或抽样运行命令中。

## 8. 已确认问题、维护成本和待核实项

### 已确认的问题或指南/流程不一致

| 优先级 | 事实与触发条件 | 影响 | 最小改进建议 |
| --- | --- | --- | --- |
| P1 | run_memory_schema_eval.py 只以 GROUP 名和 gpu 编号构造 WARP_CACHE_PATH；.local 物理上在三机共享的稳定 RMBench。若 C1 与 C2 同时都使用 GPU2，二者将写同一个 schema/gpu2/robot 与 policy 路径。 | 不满足任务要求的“每 run 必要 cache 隔离”；可能并发编译/写入冲突或跨主机污染。当前未观察到实际目录或损坏，问题是确定的路径碰撞条件。 | 在下一版命令生成器中将安全 hostname 与 run-id 或 task-id 纳入 cache 根；不要改活跃 e690 命令。 |
| P1 | openpi 的 worktree 环境指南写“hardlink”和基于 hardlink 的私有 inode 补丁；C 中央包装器固定 --link-mode symlink，创建记录和 45,060 个实际链接均证实如此。 | 按指南人工复建会错误预期依赖文件的存储和补丁行为。 | 在指南明确“通用默认 hardlink，C wrapper 强制 symlink”及对应的 private patch 行为。 |
| P1 | bridge 环境指南列 logs、eval_result 都会链接；C 包装器固定 --no-eval-result，实际 e690 只有 logs，且结束检查要求 stable bridge/eval_result 不存在。 | 读者可能寻找或创建错误的 bridge 结果根，破坏 RMBench 单一结果归属。 | 在 bridge 指南或 C 根 README 写清 C override 与 RMBench 结果所有权。 |
| P1 | e690 的 README_memory_schema.zh-CN.md 位于活跃命令旁，却给出 /mnt/public/xcj/Projects/workspace/e690…、/mnt/public/xcj/Projects/openpi/checkpoints 及 GPU0 串行示例；前两个 C 路径当前不存在，实际路径在 state-vla/workspace/e690…/c-eval 和 state-vla/openpi/checkpoints，C2 正在用 GPU2/3。 | 直接照抄可导致路径不存在或在错误资源上启动。 | 顶部增加 C 部署覆盖表，或明确该段仅适用于原本机部署，并指向 C 根 README 与当前 C task 参数。 |
| P2 | e690 指南把 .local/memory_schema_eval/inputs 表述为“本 worktree”临时目录，但 .local 解析到稳定共享 RMBench/.local，当前已有多份输入快照。 | 工作树删除不会删除它；若把它误当 task-local 清理，可能误删其他 run 的输入。 | 文档写明 realpath、owner、完成后按 variant/hash 精确删除的条件。 |

### 已确认的维护成本，不将其误报为故障

1. C1 的 /root/.cache 映射到共享 /mnt/public/xcj/cache，而 C2/C3 的同路径是 node-private overlay。23,224,213 KiB uv 和 4,310,482 KiB pip 是共享实际空间，不是 C1 重复占用；但这种默认 cache 行为差异未在 C 操作手册中显式列出。
2. symlink-mode 有效减少每个 worktree 的依赖复制，但把可运行性绑定到共享 uv archive。共享 cache 是部署基础设施，应有明确 owner 和清理规则。
3. C 根 README 规定 C1 创建、C2/C3 运行，e690 创建记录也符合；但中央包装器没有 hostname 断言。误在 C2/C3 调用会改共享 git/cache/稳定资源，属于流程靠约定而非技术阻止。
4. 创建 base 与当前运行 HEAD 不同是已记录、干净且配置受检查的版本推进，不是工作树脏改。今后报告应始终同时写创建 base、当前 HEAD 和配置约束。

### 待核实项

1. 本次没有观察到两个主机同时使用相同 gpu 编号，因此尚无 Warp cache 的实际竞态或损坏证据；P1 是由确定的共享路径和多机调度条件推出的。
2. 缺少 HuggingFace/drawer 原始数据只证明当前 C 不满足该 drawer 指南给出的前置路径；尚未确认这些数据是否故意未迁移、另有授权位置或由另一个 owner 管理。
3. 未加载模型或触发下载，不能证明 transformers、JAX、Torch、renderer 在所有模型配置下都不会使用未显式设置的默认 cache。
4. 共享 uv/pip 的历史来源、保留期限和其他消费者未从本次只读快照可得；不应据体积推断可删除性。

## 9. 历史测量参照，不是本次执行

按任务要求，本机 /root/Projects/RMBench/experiments/cluster_c_eval_acceptance_20260911/README.md 被作为历史参照读取。该文件记录过不同 base、不同共享文件系统窗口的 fresh-create 测量：

| 历史库/base | 历史创建墙钟 | worktree apparent B | venv apparent B | 历史 UV cache 增量 B |
| --- | ---: | ---: | ---: | ---: |
| RMBench 6139577 | 149 s | 23,100,804 | 13,870,683 | 2,308 |
| robot-bridge f0f585a | 14 s | 5,714,735 | 3,045,755 | 7,548 |
| OpenPI a869498 | 36 s | 11,628,322 | 9,360,481 | 86,175 |

同一历史说明还记录 RMBench lazy-probe 优化后的 52.926856684 秒，并明确 apparent-size 不跟随软链接、共享文件系统窗口变化不是独占空间证明。本报告没有复跑这些测量；第 2 节的 e690 52/17/32 秒来自其自己 2026-09-12 的创建记录，二者不能混合比较。

## 10. 指南一致性核对与可发现性

远程指南存在且层次清楚：C 根 README 位于 state-vla/README.md；三库 AGENTS 都会把创建/安装工作指向 docs/worktree_env/README.zh-CN.md；e690 的项目级说明位于活跃 RMBench/experiments/memory_chunk_20260910/README_memory_schema.zh-CN.md。C 根 README SHA-256 为 1bafbae…6774276，三库环境指南在稳定树与 e690 tree 的 SHA-256 相同，故这里比较的是当前远端实际文件，而非本机模板。

| 指南及可发现路径 | 与实际一致的内容 | 有依据的不一致或缺口 |
| --- | --- | --- |
| state-vla/README.md | 明确 C1 创建、C2/C3 运行；参数顺序正确；要求保存创建输出、时间、git status 和不跟随链接统计；明确结果/共享资源不得随工作树删除。e690 记录实际满足这些创建留痕要求。 | 没有揭示中央包装器会从 base 抽取安装器再施加 C patch、固定 symlink mode、bridge 的 --no-eval-result，亦未说明 C1 的 /root/.cache 指向共享 cache；“C1 only”没有脚本级 hostname 检查。 |
| RMBench docs/worktree_env/README.zh-CN.md | 共享 assets/data/eval_result/logs/.local 和语义 policy 资产的描述符合实际；当前 DP/pi05 checkpoint 链接也符合条件扫描。 | 没有 C 离线锁、两个固定 wheel、UV_OFFLINE 与 forced symlink 的部署细节。它不直接声称 hardlink，风险低于另两库。 |
| robot-bridge docs/worktree_env/README.zh-CN.md | .local、logs、冻结 lock、独立 venv 的概念与实际一致。 | 表格无条件列出 eval_result，C 创建器却固定抑制它；这是直接的文档与 C 行为差异。 |
| openpi docs/worktree_env/README.zh-CN.md | 十个共享资源根、LFS skip、冻结 lock、.venv 不整体链接和 editable 指向新树均与实际一致。 | 写为 hardlink 与 hardlink 私有 inode 补丁；实际 C 为 symlink，补丁也为保护共享 archive 而改写。创建日志、patch 和 45,060 条实际链接直接证实差异。 |
| e690 README_memory_schema.zh-CN.md | bridge f962663、OpenPI a869498、90 秒仅首个 infer、smoke 到 formal 的门禁、结果归 RMBench/eval_result、checkpoint 只读等原则与当前运行配置一致。 | 文档中原本机 workspace/checkpoint 路径和 GPU0 示例不适用于当前 C 部署；drawer 的 HF/raw 数据路径也不存在。它虽紧邻实际入口，因而可发现性高、误操作风险也高。 |
| e690 experiments/memory_chunk_20260910/README.md | 其中旧 P1/F0 章节明确保存历史 smoke/结果与结果归属，适合作为历史说明。 | 含旧 bridge/路径示例，不能替代 README_memory_schema、C 根 README 或任务后续授权作为当前 C 执行命令。 |

最小文档收敛方案是在 C 根 README 增加“C wrapper override”小节，并在 e690 指南最顶部增加当前 C 根、worktree 根、checkpoint 根、cache realpath 和旧路径不可用的说明；bridge/openpi 环境指南只需增加一行 C 特例即可。以上均为建议，本审计没有修改任何指南、脚本或远端资源。
