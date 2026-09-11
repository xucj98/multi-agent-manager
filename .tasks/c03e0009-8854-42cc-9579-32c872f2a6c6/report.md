# OpenPI symlink transformers 覆盖定向复核

## 结论

**发现问题，需作者修复后再验收。** 正常 Python 模式下，本提交的 symlink 路径修复、默认 hardlink 覆盖、原子替换与 smoke 核查均通过；但安装器和 smoke 把 cache 边界及覆盖完整性都放在 Python `assert` 中。若继承 `PYTHONOPTIMIZE=1` 或以 `python -O` 启动，断言会被移除，安全保证和 smoke 检查都会失效。

## 问题

- **[P2] 优化模式可越过路径边界并误报 smoke 成功。**
  - `scripts/worktree_env/create_worktree_env.sh:307,311` 的 venv 与已解析父目录边界检查均为 `assert`。在最小 uv 文件级 symlink fixture 中，把 `transformers/models` 设为指向 fixture cache 的目录 symlink 后，普通模式会在第一份 patch 前拒绝且 cache 的 5 个文件未变；以 `PYTHONOPTIMIZE=1 python -O` 运行同一安装块时，5 个 patch 都被写入 cache（`optimized_boundary=REPRO cache_modified_files=5`）。
  - `scripts/worktree_env_smoke.py:19,23-25` 的根路径、内容、非 symlink 与私有 inode 检查同样全为 `assert`。优化模式下，含未替换 symlink 覆盖的 fixture 核心检查仍以 0 退出（`optimized_smoke_core=REPRO exited_successfully_with_symlinked_overrides`）。
  - 建议将这些运行时保护改为显式条件加 `RuntimeError`/`SystemExit`，不要依赖可被 `-O` 消除的 `assert`。

## 正常模式证据

- 独立 `/tmp` cache 的 uv 0.9.25 / CPython 3.13.9 小 wheel fixture 复现真实文件级 symlink：`find_spec(...).origin` 保持 venv 拼写，而 `.resolve()` 落入 cache。新逻辑替换 5 个 transformers patch 后，每个目标均为非 symlink、`st_nlink == 1`、内容与源 patch 一致，cache 字节及 inode 未变（`symlink_fixture=PASS files=5`）。
- hardlink fixture 起始时每个目标与 cache 共用 inode；同一替换块后 5 个目标均为私有 inode，cache 内容及 inode 未变（`hardlink_fixture=PASS files=5`）。脚本默认值仍为 `hardlink`，并传给 uv。
- 普通模式路径边界负向 fixture 在首次替换前拒绝 cache-backed 子目录，cache 保持未变（`path_boundary=PASS`、`path_boundary_cache=PASS files=5`）。
- smoke 核心在正确私有覆盖时通过，并能拒绝人为恢复的单个 symlink 覆盖（`smoke_core_positive=PASS`、`smoke_core_negative=PASS`）。
- `git diff --check`、`bash -n scripts/worktree_env/create_worktree_env.sh` 与 `ast.parse(scripts/worktree_env_smoke.py)` 均通过。

## 范围与交付

- 审阅 workspace：`/mnt/public/xcj/Projects/workspace/c03e0009-8854-42cc-9579-32c872f2a6c6/openpi`
- 审阅提交：`958eeaedc4c841e2f1b31c51572ddecc449ba5cb`（相对 `3435a2b60bfb34197adeb8fe54ad750aeb78a5ed`）
- 未修改业务代码，无交付 commit。
- 未做完整 OpenPI 安装、GPU、C 或三机 smoke；这些仍由源任务负责。
- 本次 `/tmp` fixture/cache 与生成的 bytecode 已清理到可恢复废纸篓；worktree 按要求保留供 Manager 验收。
