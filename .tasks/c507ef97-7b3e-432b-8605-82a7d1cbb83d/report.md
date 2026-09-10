# Table-1000 空白上下文独立验收报告

## 结论

PASS。未修改 Table-1000 源码、文档或测试脚本，也未运行正式训练或长数据生成。

## 基线与 workspace

- canonical primary `main` 的记录提交：`b56e55ef6c799c800c12573bde1b0a7a3c25556c`。
- 独立 workspace：`/mnt/public/xcj/Projects/table-1000/workspace/c507ef97-7b3e-432b-8605-82a7d1cbb83d/table-1000`。
- 分支：`task/c507ef97-7b3e-432b-8605-82a7d1cbb83d`；验收后 `HEAD` 仍为上述提交，`git status --short --branch` 无源码改动。
- 本任务是只读验收，无交付 commit。

## 一键环境与隔离证据

先按 MAM 执行规范创建本任务 worktree，随后从该新任务环境执行仓库文档的一键入口：

```bash
bash /mnt/public/xcj/Projects/table-1000/table-1000/scripts/worktree_env/mam_workspace_add.sh \
  c507ef97-7b3e-432b-8605-82a7d1cbb83d \
  b56e55ef6c799c800c12573bde1b0a7a3c25556c
```

该命令退出码为 `0`，首次创建本任务 `.venv` 用时 `5 s`。`du -sh .venv` 为 `21M`（实际磁盘占用），`du -sh --apparent-size .venv` 为 `7.7M`。安装器明确报告：

- 私有 venv：`workspace/c507ef97-7b3e-432b-8605-82a7d1cbb83d/table-1000/.venv`，不是软链；Python prefix 与该路径一致。
- 包存储：`/mnt/public/xcj/cache/uv`，模式为 `symlink`；安装器的 package-link 验证通过。抽样的包文件 `.venv/share/man/man1/ttx.1` 解析到 `/mnt/public/xcj/cache/uv/archive-v0/TWYN3sDSKssJPuc_/fonttools-4.63.0.data/data/share/man/man1/ttx.1`。
- editable `table1000` 导入解析到本 worktree 的 `src/table1000/__init__.py`。
- worktree 顶层仅有业务软链 `.cache -> /mnt/public/xcj/Projects/table-1000/table-1000/.cache` 与 `outputs -> /mnt/public/xcj/Projects/table-1000/table-1000/outputs/c507ef97-7b3e-432b-8605-82a7d1cbb83d`。
- primary checkout 顶层无业务软链；其 `.cache`、`outputs` 均为真实目录。

## 文档 smoke 验收

按 `docs/guide/worktree-environment.md` 执行：

```bash
source scripts/worktree_env/activate.sh
TABLE1000_SMOKE_CUDA_VISIBLE_DEVICES=1 bash scripts/worktree_env/smoke.sh
```

为保留实际退出码，stdout/stderr 写入任务 outputs 中的 `smoke/acceptance-smoke-rerun.log`，退出码写入 `smoke/acceptance-smoke-rerun.exit`。命令退出码 `0`，用时 `98 s`。

- preflight 的 `readiness` 为 `import=true`、`cpu_state=true`、`render=true`、`gpu=true`；环境包版本为 ManiSkill `3.0.1`、SAPIEN `3.0.3`、Torch `2.6.0+cu124`。
- 真实缓存 GSO 资产 `Markings_Letter_Holder` probe 通过，`overall_pass=true`，COACD 缓存复用。
- ManiSkill CPU、render、GPU smoke 均报告 `reset_ok=True`、`step_ok=True`；GPU 使用空闲的物理 GPU 1。
- Table-10 `t1k-dev-office-0002-v1` 的 `red-then-blue` reference replay 在 `physx_cpu` 下完成，`valid=true`。
- 聚焦测试 `tests/unit/test_data_validation.py tests/unit/test_cli.py`：`40 passed in 3.38s`。

产物均在文档规定的任务输出目录：

- `/mnt/public/xcj/Projects/table-1000/table-1000/outputs/c507ef97-7b3e-432b-8605-82a7d1cbb83d/smoke/preflight.json`
- `/mnt/public/xcj/Projects/table-1000/table-1000/outputs/c507ef97-7b3e-432b-8605-82a7d1cbb83d/smoke/gso-asset-probe.json`
- `/mnt/public/xcj/Projects/table-1000/table-1000/outputs/c507ef97-7b3e-432b-8605-82a7d1cbb83d/smoke/reference-replay.json`
- `/mnt/public/xcj/Projects/table-1000/table-1000/outputs/c507ef97-7b3e-432b-8605-82a7d1cbb83d/smoke/acceptance-smoke-rerun.log`
- `/mnt/public/xcj/Projects/table-1000/table-1000/outputs/c507ef97-7b3e-432b-8605-82a7d1cbb83d/smoke/acceptance-smoke-rerun.exit`

## 交付前清理与说明

执行 `bash scripts/worktree_env/cleanup.sh`，退出码 `0`；未发现 worktree 中 `.venv` 之外的 `__pycache__`、`.pytest_cache`、`.ruff_cache` 或 `.table1000-runtime-cache` 残留，`.venv` 与 `outputs` 均按文档保留供验收/归档。

未遇到无法按仓库文档自行恢复的环境或说明问题。MAM 的通用 `--repo REPO` 占位参数不接受绝对路径；目标仓库文档指定的仓库名 `table-1000` 可正常使用，未构成该一键入口的歧义或阻塞。
