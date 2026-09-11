# 集群 C uv symlink 三库环境入口独立复核

## 结论

**代码准入：PASS。** 未发现阻塞 C 安装或严格旧版本运行树的代码问题；下列三个已提交增量可进入现场安装验收：

| 仓库 | 基线 | 复核提交 |
| --- | --- | --- |
| robot-bridge | `f0f585a2b5974c60b51cac65277f94d1097591a3` | `bdb41821039820f45c3f73ebc7db3c941a999b49`、`3ebf9d075e5e64a350ddb35cd8632e3abd04373c` |
| openpi | `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4` | `3435a2b60bfb34197adeb8fe54ad750aeb78a5ed` |
| RMBench | `6139577e360c27f866e4dbb3dd2fc067cc7ddd50` | `c59c6561de72092f95c14582ebaf8b1fe8728d00` |

这是代码层结论，不表示 C 环境、三机 smoke 或 C100 已验收通过。

## 已核实的代码语义

- 三库新参数均为受限的 `--link-mode {hardlink,symlink}`，默认值仍为 `hardlink`；正常本机入口不传该参数时保留原行为。
- robot-bridge 与 OpenPI 的唯一依赖安装命令 `uv sync` 均使用 `--link-mode "$LINK_MODE"`；RMBench 将所有 `uv pip install`（torch、requirements、PyTorch3D、cuRobo、可选 OpenDM editable）集中经过带同一参数的 `uv_pip_install`，没有漏传。
- symlink 分支不以字符串或缓存目录存在为依据：它遍历新 `.venv` 的实际 symlink，`resolve(strict=True)` 后要求 target 位于 `cache_dir.resolve()` 下，并输出 link 与真实 target。C 总 wrapper 安装后以同一逻辑再次验证。
- 三个 C wrapper 保留 `BASE_COMMIT NEW_BRANCH WORKSPACE_ROOT` 接口；通用 wrapper 固定 C 的共享 CPython、共享 uv cache 和稳定 source root，不使用 `/root` 私有解释器或临时源码。底层脚本为每个 worktree 创建独立 `.venv`，共享资产仍链接到稳定源。
- robot-bridge 的 `--no-eval-result` 是 opt-in，默认本机仍保留原共享 `eval_result`；C wrapper 显式选择它，避免在 bridge 建立第二个结果根。现有冲突、tracked/ignored、非空数据和目标已存在保护均未被删改。
- bridge/OpenPI 的既有 CPU smoke 会断言包实际从当前 worktree 导入；RMBench 根不是可安装 Python project，simulator 入口从本 worktree 根运行，OpenDM 则在提供时 editable 安装到该 venv。

## C 入口和严格版本复核（只读）

- 读取时 C 的 `state-vla/{robot-bridge,openpi,RMBench}` 均处于上述基线且 `git status --porcelain` 为空。
- C 的三个 `.local/patches/*-uv-symlink.patch` 与上述候选增量逐字一致：robot-bridge `8d79da7c83016c16e8e2aea31d888451dd9cf39b2c7d7c45b2d816b7c56dd627`、OpenPI `557bfa67e0f46f1119969605902b2ccfecc540c01345e2690f5a2f0dddda2791`、RMBench `4f9528ed9aedc446c11915c6887feaba1f6a9a02bc3c98eb213fdbf6c955e97a`。
- 用 C 中实际 patch 做 `patch --dry-run` 均通过：三个 current 基线，以及严格 bridge `8ea6078543a875b5ae223df16891cdc1fe975c66`、严格 RMBench `3e69b1e665a8eac0104d261b233f1b3339007e00`；OpenPI 严格树与 current 同为 `a869498...`。
- C 通用 wrapper 从 `BASE_SHA` 提取 installer 到 `.cache` 临时文件再 patch 并运行，trap 清理临时文件；运行 worktree 保持目标 commit 的受管文件，不会把 symlink patch 写入严格运行树或冒充为固定版本。

## 非阻塞加固建议

当前校验遍历整个 `.venv`，而非先限定 `lib/python*/site-packages`。在本流程中 `.venv` 是新建且校验紧随 uv 安装，实际通过的链接应来自包安装；但最终可将扫描根收窄到实际 site-packages，以排除未来无关缓存链接导致的假阳性，并让日志直接表达验收所需的 site-packages → uv cache 证据。此项不阻塞当前代码准入。

## 真实环境待验收项

源任务最新报告（13:36 +08:00）记录 bridge 的离线创建和 CPU smoke 已完成；OpenPI 首次离线入口因 uv cache 相对路径修复待续，RMBench 尚未创建。以下均仍由作者现场完成，不能由本 review 代替：

1. 三个全新 current worktree 各实际运行一次本地入口，记录命令、起止/exit、worktree/.venv 独占空间与共享 cache 增量；不以 `du -L` 重复计入共享 cache。
2. 每个成功环境保留实际 `site-packages` symlink 的 link/`readlink -f`/target 证据、独立 venv、稳定资产链接、worktree clean 状态和对应 CPU smoke；bridge/OpenPI 还须证明 editable 导入来自新 worktree。
3. 严格 formal tree、旧 bridge 的正规 local `openpi_client` wheel、renderer/cuRobo 检查，以及 -1/-2/-3 各 2 rollout（一条有视频、一条无视频）真实 eval 和完整产物。
4. 单次登记的 C100 必须固定批准版本、模型/数据/seed/H/K/memory 协议，结果为 `64–74/100` 才符合本机 `69/100` 的 ±5pp 门槛；50 rollout 仅作中点检查，结果回传后再验收。
5. C `state-vla/README.md` 在只读检查时尚不存在，仍需按源任务交付稳定、实测过的操作手册。

## 本地验证与工作区

- 三个候选 diff 均通过 `git diff --check` 和 `bash -n`；`--help` 暴露新接口，非法 `--link-mode copy` 在任何副作用前被拒绝。
- 未运行 uv 安装、未使用 GPU、未写入 C，也未修改业务代码、分支或远端。
- 独立 worktree（均 clean）：
  - `/mnt/public/xcj/Projects/workspace/76b4c5b8-7b5a-4a55-8ed6-c744fda074d5/robot-bridge`
  - `/mnt/public/xcj/Projects/workspace/76b4c5b8-7b5a-4a55-8ed6-c744fda074d5/openpi`
  - `/mnt/public/xcj/Projects/workspace/76b4c5b8-7b5a-4a55-8ed6-c744fda074d5/RMBench`

本 review 无交付代码 commit。
