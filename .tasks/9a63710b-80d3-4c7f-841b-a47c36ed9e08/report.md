# 集群 C renderer 复用与 worktree 创建优化独立审阅（2026-09-12）

## 裁定

- **候选三机 smoke：准入。** 必须在新、干净的 RMBench candidate worktree 中应用 `17b55bf1c79a0c5a836d1da089765934cb3a5b0`（或只包含它的后继提交），保持每个 worker 的 `SAPIEN_RENDER_DEVICE=cuda:0` 不变，并分别完成 C1/C2/C3 的固定两条 rollout：episode 0 有视频、episode 1 无视频、两条均 accepted/terminal、产物检查和服务退出均通过。
- **正式 100：暂不准入。** 它只能在上述三台 candidate smoke 全部通过、候选三树干净且另起新 result leaf 后启动；40-reset gate 和两 seed 合成对照均不能替代 smoke，更不能与旧失败 22 条或任何新结果拼接。
- **`9c71a3e` 创建优化：准入。** 未发现改变软链隔离、失败语义、私有覆盖或统计口径的缺陷。

没有发现需要先修复的代码阻断项。唯一运行边界是 `_PROCESS_RENDERER` 没有按设备或 renderer 配置分桶：同一 Python worker 内不得在 reset 之间切换 `SAPIEN_RENDER_DEVICE`。本次 runner 每个 worker 固定 `CUDA_VISIBLE_DEVICES=<GPU>` 且固定 `SAPIEN_RENDER_DEVICE=cuda:0`，三机是独立进程/主机，处于该安全范围。若以后确有同一 worker 切换设备的需求，最小修复应是在首次创建时记录设备并在不一致时 fail-fast（或为每台设备使用独立 worker），不应静默复用。

## renderer 复用审阅

审阅的 renderer 提交为 `17b55bf`，基线为 `3e69b1e`；本任务按要求创建的 RMBench worktree 固定在 `9c71a3e`，因此通过 Git 对象直接审阅了这两个独立增量。`17b55bf` 仅在 `envs/_base_task.py` 增加模块级 `_PROCESS_RENDERER`，并使 `setup_scene()` 首次创建 `SapienRenderer`、之后复用它。每次 `setup_demo()` 仍按原顺序新建 engine、scene、物理参数、地面、材质、灯光、相机和 viewer；`close_env()`/clear-cache 路径、seed、worker、动作、观测和 policy 协议均未修改。调用方复用同一 `TASK_ENV` 并在每条后调用 `close_env()`，所以该改动准确覆盖反复 setup/close 的 renderer 生命周期，而不把 scene 留作跨 episode 状态。

远端 C diagnostic tree 是 `3e69b1e` 上的受控未提交 patch；只读核验的 `envs/_base_task.py` SHA256 为 `fb855180ed2d3b3a764139e4a254599db3082ea40ce327ccd8f8b5f9872714d7`，与 `renderer-source-audit.json` 和 `17b55bf` 一致。它不得直接充当后续 smoke/formal 的脏源码树。

以下采用源任务已发布报告 `9afee17d580fb54e23791e546b022a44a303e9d7` 的最终门禁证据，而非运行中的中间快照；现有证据足以支持候选 smoke：

- C2 `renderer-reuse-20260912-retry1/result.json`（SHA256 `eaeee02954be302de93a17629bf2f9bd9746a01bd69c33bd861b26a2fe827c4e`）为 `passed=true`、40/40 accepted、连续 seed `100000–100039`、`exit=0`、`error=null`；跨越旧的第 23 次初始化边界，driver log 未命中 `ErrorIncompatibleDriver`、`Segmentation fault`、`core dump`、`ConnectionResetError` 或 `RPC EOF`。outer PID 已退出，C2 GPU2 只剩 4 MiB。
- C1 的 `renderer-protocol-20260912-retry2/comparison.json` 与本机镜像 SHA256 同为 `1cf8b855b96c22eb01f1088f1b1410cbd2920caaad091e2fb7b414ff54c0600f`。固定 seed `100000/100001` 的 50×14 float32 动作、初始及执行 30 步后的 qpos、三相机 240×320×3 uint8 图像和状态 metadata 均逐元素相同（9 个数组/seed，max abs 0）；图像非空且有场景变化。该证据覆盖随机初态、动作队列和观测输出，仍不替代 policy/video smoke。

## worktree 创建优化审阅

`9c71a3e` 把 symlink 模式安装后 probe 的 `sorted(venv.rglob("*"))` 改为惰性 `venv.rglob("*")`。旧逻辑和新逻辑都只要求找到一个可严格 resolve 且位于配置 cache 内的链接；cache 外链接、悬空链接和普通私有文件都会被跳过，找不到有效链接仍以 `SystemExit` 非零失败。probe 只读 `.venv`/cache，不写入 cache 或私有覆盖。C wrapper 的补丁仅把同一段 probe 改为惰性遍历，且在临时 managed installer 上应用。

本机在独立 worktree 运行 `bash -n script/worktree_env/create_worktree_env.sh`、两提交的 `git diff --check`，均通过；`.venv/bin/python tests/test_symlink_install_probe.py -v` 通过。该测试直接提取实际 installer heredoc，验证普通私有文件保持普通文件、cache 外和悬空链接不通过、找到首个有效链接后不再消费遍历器、没有有效链接时失败。

只读核对 C 原始 `create-lazy-probe-20260912/metrics.json` 与本机镜像，SHA256 同为 `41c41eeb7e7dc5f1cb9cfe481e5ead2ff55be9954eb50adf71edd343047e7712`。同一 base `6139577`、复用 UV artifact cache、CPU-only fresh 创建一次为 52.926856684 s（exit 0）；两个 probe 为 0.203525066 s 和 0.102121115 s，合计约 0.306 s。先前 151.783 s 是不同时间窗口的一次未优化 trace，因此这里只接受其相对证据，不承诺固定加速比。原始测量以 `du -s -B1` 记录 allocated、以 `du -s --apparent-size -B1` 单列 apparent，未使用 `-L`：worktree/venv allocated 为 51,438,080/41,802,240 B，apparent 为 23,100,627/13,870,506 B，cache allocated 窗口差为 +2,560 B；清理 47.305 s 单列，未混入创建时间。

## 范围、交付与局限

- 工作区：`/mnt/public/xcj/Projects/workspace/9a63710b-80d3-4c7f-841b-a47c36ed9e08/RMBench`
- 分支/审阅 HEAD：`task/9a63710b-80d3-4c7f-841b-a47c36ed9e08` / `9c71a3e95d7e3f6c6b9c07a583a78ef37c012059`；未修改 RMBench 源码。
- 已审阅提交：renderer `17b55bff1c79a0c5a836d1da089765934cb3a5b0`，创建优化 `9c71a3e95d7e3f6c6b9c07a583a78ef37c012059`。
- 只使用源码、任务目录现成证据和只读 C SSH 记录；未重建远端环境、未启动 GPU、未运行 policy rollout 或正式评测。
