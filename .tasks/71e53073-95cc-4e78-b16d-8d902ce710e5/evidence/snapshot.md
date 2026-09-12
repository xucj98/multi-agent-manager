# 集群 C state-vla 只读快照

- 审计任务：71e53073-95cc-4e78-b16d-8d902ce710e5
- 采样窗口：2026-09-12 13:07–13:30 +08:00
- SSH 入口：wuwen-4090-1、wuwen-4090-2、wuwen-4090-3
- 方式：只读 SSH、stat/readlink/find/git/ps 和受限的 /proc/<pid>/environ 白名单查询；没有创建环境、运行 GPU、写远端或读取认证变量。

## 三机与稳定入口

三机的 /mnt/public 都是同一 yrfs 挂载。下列文件在三机 SHA-256 一致：

| 文件 | SHA-256 |
| --- | --- |
| state-vla/README.md | 1bafbae25f742e69c4c76c45a6013f39b65e27a79706169f4c5bc8dda6774276 |
| state-vla/.local/create_worktree.sh | adfc2ce56f81817e5c75e8c2a5c37c618424c500560c53f7eb26dbc9d4bb24a6 |
| RMBench/.local/create_worktree.sh | e23bcac9675612745251dae0f85e798e89033688ee3f3e86442cc1dc8645426c |
| robot-bridge/.local/create_worktree.sh | 35c8379197700a80a47e057ae4474d37788e2382d5d04b328085b43ca175aa01 |
| openpi/.local/create_worktree.sh | 360db0719d69081e4ea20f833265df3a87e9c96747f6c1f89c470e9fc33794b4 |

稳定根为 /mnt/public/xcj/Projects/state-vla。稳定 checkout 均 detached：

| 库 | HEAD |
| --- | --- |
| RMBench | 6139577e360c27f866e4dbb3dd2fc067cc7ddd50 |
| robot-bridge | f0f585a2b5974c60b51cac65277f94d1097591a3 |
| openpi | a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 |

## 活跃 e690 工作树

路径：/mnt/public/xcj/Projects/state-vla/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/c-eval。

| 库 | 当前 HEAD / 分支 | common git dir |
| --- | --- | --- |
| RMBench | 79334268e28ccd91c59049224aad8d0d799d11a7 / task/e6908de7-4b02-465a-987b-a19eba7a315a-c-eval-rmbench | stable RMBench .git |
| robot-bridge | f9626636c4776d8eb15f9c556775cb2d12c000e5 / task/e6908de7-4b02-465a-987b-a19eba7a315a-c-eval-robot-bridge | stable bridge .git |
| openpi | a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4 / task/e6908de7-4b02-465a-987b-a19eba7a315a-c-eval-openpi | stable openpi .git |

三机均见相同 HEAD，三树 git status --porcelain --untracked-files=no 均为空。工作树的 .git 文件分别指向稳定库的 .git/worktrees/RMBench3、robot-bridge3、openpi3。

创建记录（2026-09-12 03:45–03:49 +08:00）中的初始 base 分别为 RMBench 17b55bff1c79a0c5a836d1da089765934cb3a5b0、bridge 8ea6078543a875b5ae223df16891cdc1fe975c66、openpi a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4；当前 RMBench/bridge 已在自己的分支上前进。创建记录的非跟随统计为 51,425,792 / 12,377,600 / 32,592,896 B，symlink 数为 62,638 / 14,485 / 45,074。

## 链接与解释器抽查

非 .venv 链接全部为绝对链接，且没有悬空项：

- RMBench：.local、assets、data、eval_result、logs、policy/DP/checkpoints、policy/pi05/checkpoints。
- robot-bridge：.local、logs；C 包装器显式未创建 eval_result。
- openpi：.local、assets、checkpoints、data、datasets、logs、wandb、offline_test、offline_test_results、policy_records。

所有目标都解析回稳定 state-vla/<repo>/...。 .venv 原始 symlink 分类如下；没有 /root、/home、/tmp、旧 03d538a0-… 或悬空目标：

| 库 | symlink 总数 | 到 shared uv archive | 到 shared Python | 相对链接 |
| --- | ---: | ---: | ---: | ---: |
| RMBench | 62,631 | 62,627 | 1 | 3 |
| robot-bridge | 14,483 | 14,479 | 1 | 3 |
| openpi | 45,064 | 45,060 | 1 | 3 |

三台机器上，uv 均不在 PATH，而下列解释器均存在且可执行：

| worktree | 最终解释器 |
| --- | --- |
| RMBench | /mnt/public/xcj/cache/shared-python/cpython-3.10.19-linux-x86_64-gnu/bin/python3.10 |
| robot-bridge | /mnt/public/xcj/cache/shared-python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 |
| openpi | /mnt/public/xcj/cache/shared-python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11 |

## 安装器与关键资源

中央 C 包装器以绝对 uv、共享 Python、/mnt/public/xcj/cache/uv 和 --link-mode symlink 调用从指定 base 用 git show 取出的受管安装器。RMBench 另外设置 UV_OFFLINE=1，使用离线锁、PyTorch3D wheel 和 cuRobo wheel；bridge 使用 --no-eval-result；openpi 使用冻结 lock、GIT_LFS_SKIP_SMUDGE=1 与 private transformers 替换文件。

| 资源 | SHA-256 |
| --- | --- |
| CPython 3.10.19 | 685193c2432feb9d2a2b3ba129d976a7fd4172c60e1622b7b7ffd4308c40f6a5 |
| CPython 3.11.14 | 76c511e63e25d9f60ca560f47f69598c0d1ec2a1b9fa165a3c64d5707681ef81 |
| stable uv | 6db762293e2843c7cd7420dd35db124480eebe6b15df1f3ed05407bd905bf55f |
| PyTorch3D wheel | 10b96025d4be54d7fbeb4a49de8622206cbdc0b1dd13bee8300d600dd1c78b51 |
| cuRobo wheel | 780a878713cad48043b4537268c860e52393ddeb46709a6377409f9c65f4f988 |

## 运行期与节点私有路径

采样时 C2 有 e690 的 formal runner、robot server 和 policy server；命令直接执行 worktree 的 .venv/bin/python。子进程显式设置 WARP_CACHE_PATH 到 RMBench/.local/warp-cache/memory_chunk_20260910/schema/gpu2 或 gpu3 下的 robot/policy，以及 policy 的 XLA_PYTHON_CLIENT_MEM_FRACTION=0.4。该逻辑路径经过 .local 解析到稳定 RMBench；采样时相应 Warp 目录尚不存在。

未发现 HF_HOME、HF_HUB_CACHE、TORCH_HOME、JAX_COMPILATION_CACHE_DIR、XLA_CACHE_DIR、CUDA_CACHE_PATH 或 task 命名 /tmp 路径。三机的 ICD 文件 /usr/share/glvnd/egl_vendor.d/10_nvidia.json 都存在。共享 HuggingFace 路径 /mnt/public/xcj/cache/huggingface 和 /mnt/public/cache/openpi 均不存在。

C1 的 /root/.cache 是到 /mnt/public/xcj/cache 的符号链接；因此其 /root/.cache/uv 和 pip 实际是共享路径（约 23,224,213 KiB 和 4,310,482 KiB 的局部 du 读数）。C2/C3 的 /root/.cache 在各自 overlay 上：没有 uv/HF/JAX/XLA 目录，torch/warp/pip 分别约 76/876/2,944 KiB。该差异不影响上述 worktree 解释器，但会影响未显式指定 cache 的将来程序。

RMBench 资产下可见 embodiments/aloha-agilex/meshes 与 objects；assets/data 深度四以内未见名为 raw 或 converted 的目录。stable openpi/data 与 openpi/datasets 在快照时为空。抽查的 20k checkpoint 含 _CHECKPOINT_METADATA、params、assets、metadata；assets/<robot>/norm_stats.json 和 params/_METADATA 存在。当前 memory-schema evaluator 从 checkpoint metadata 校验 datasets repo_id 和 demo_clean_state 来源，并不在此入口遍历上述空的 OpenPI 数据根。

## 已知路径排除

/mnt/public/xcj/Projects/RMBench 是唯一兼容 shim，解析到稳定 state-vla/RMBench；同级 robot-bridge/openpi shim 不存在。旧任务 03d538a0-f68e-45e6-9758-8539048b32d7 的常见 workspace/tmp 根均不存在；当前 e690 的非 venv 链接和文本扫描没有该 ID 或传输入口 wuwen-nx-aic/wuwen-4090-aic。
