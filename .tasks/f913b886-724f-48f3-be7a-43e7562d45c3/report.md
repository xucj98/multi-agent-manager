# RMBench C 离线锁安装窄审阅

## 裁定

**代码准入 PASS**：`423291f4a819cabe9190ca440b12232449073299` 相对
`c59c6561de72092f95c14582ebaf8b1fe8728d00` 的可选离线锁路径没有发现
阻断问题。它只修改 `script/worktree_env/create_worktree_env.sh`，默认的
hardlink/常规解析分支保持原样；仅在显式传入 `--offline-lock-dir` 时采用四阶段
`--no-deps` 安装。

这不是 C 三机 sim/policy smoke 或正式 100 rollout 的验收；那些仍由现场 owner
按源任务门禁完成。

## 证据

- 参数目录会被规范化，且两个锁均要求为普通文件、不可为软链。离线路径依次安装
  21 个 CU121 闭包包、243 个 PyPI 闭包包、固定 `torch==2.4.1` /
  `torchvision==0.19.1`，以及哈希校验过的 PyTorch3D 和 cuRobo wheel。
- C 稳定 wrapper 只在临时提取的 installer 上顺序施加 symlink 和 offline-lock
  patch，并显式 `export UV_OFFLINE=1`；fresh RMBench 的实际 Git HEAD 是干净的
  `6139577e360c27f866e4dbb3dd2fc067cc7ddd50`。它没有把安装补丁写入运行树。
- C 两锁 SHA256 分别为
  `5bcc1a0b9c714c1c3613d37ece462e192b929bde6b2dc0806c1b12f87088b084`
  与 `4b2cacf413ac88ed00d931bbe46ea8c74dcbf806024a5fc0b9ec51d1b823d1b6`；
  264 条均精确 pin、解析无错误、跨锁无重复。它们与本机 268 个安装分发包的
  版本逐项相符；另外四个为 torch、torchvision、PyTorch3D、cuRobo。
- C fresh 日志显示四阶段均成功（21、243、2、1、1 包），`uv link mode: symlink`
  和两次 cache-link probe 均 PASS。只读运行的原始
  `uv pip check --python .../fresh/current-rmbench/RMBench/.venv/bin/python`
  检查 268 个包并输出 `All installed packages are compatible`。37 个 simulator
  直接 requirements 也均已安装且无版本违例；关键版本为 torch `2.4.1+cu121`、
  torchvision `0.19.1+cu121`、PyTorch3D/curobo `0.7.8`、sapien `3.0.0b1`、
  numpy `1.26.4`、Pillow `11.3.0`、ffmpeg `1.4`。
- C patch 的 SHA256 与本机 `6139577 -> c59c656` 及
  `c59c656 -> 423291f` 的逐字节 `git diff --binary` 完全一致。对严格旧版
  `3e69b1e665a8eac0104d261b233f1b3339007e00`，两 patch 顺序
  `git apply --check` 通过，且本机严格工作树前后保持干净。C formal 树尚未创建，
  所以尚无现场严格运行树可被污染；创建时仍应保留该 HEAD/clean 检查。

## 本次验证与边界

- 本机审阅工作树：
  `/mnt/public/xcj/Projects/workspace/f913b886-724f-48f3-be7a-43e7562d45c3/RMBench`
  （`task/f913b886-724f-48f3-be7a-43e7562d45c3`，基于 `423291f`）。未产生业务提交。
- 通过：`git diff --check c59c656..423291f`、`bash -n`、本机目标 venv 的
  `uv pip check`（268 包）。在不暴露 GPU 的 CPU import fixture 中，torch、
  torchvision、sapien、PyTorch3D、curobo 均可导入，`torch.cuda.is_available()` 为
  `False`。
- 对 C 的操作全部为 SSH 只读检查（文件、Git 状态、日志与 `uv pip check`）；未在 C
  写入、安装或使用 GPU。
- 已仅在本审阅工作树内清理 `.venv` 下的 `__pycache__`/`.pyc`；复查未发现
  `__pycache__`、pytest、ruff 或 mypy cache，且未跟随任何共享软链。

## 未验收范围

现场 CPU/GPU simulator、renderer/cuRobo、三机两 rollout smoke 和严格 100 rollout
不在本 review 范围内，不能由本结论替代。
