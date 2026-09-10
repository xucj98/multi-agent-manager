# 阶段性交付（待 symlink 隔离验证后确定默认包链接策略）

- worktree：`/mnt/public/xcj/Projects/table-1000/workspace/b52655b9-cb65-4c6e-94be-2cad789235e6/table-1000`
- 分支：`task/b52655b9-cb65-4c6e-94be-2cad789235e6`
- 当前提交：`2af4b120fc5655df40101ab2bb77a9ef9c2192b9` (`feat: add MAM worktree environment setup`)

已提交版本化的 MAM `.local` wrapper 模板、任意 cwd 的
`mam_workspace_add.sh`、完整 CUDA 12.4/Python 3.12 ManiSkill 安装入口、激活和
smoke 脚本，以及空白上下文可读的 `AGENTS.md` 与环境指南。精确入口为：

```bash
bash /mnt/public/xcj/Projects/table-1000/table-1000/scripts/worktree_env/mam_workspace_add.sh \
  TASK-ID BASE-COMMIT
```

默认依赖是现有完整锁 `requirements/lock-linux-cu124-py312.txt`，使用仅 PyPI 与
官方 PyTorch CUDA 12.4 index、`--no-deps`、`unsafe-best-match`，保留
`torch==2.6.0+cu124`、`mani-skill==3.0.1`、`sapien==3.0.3` 和
`mplib==0.2.1`。

布局已按最新要求实现：canonical 的 `.cache/`、`.local/uv-cache/`、`outputs/`
均为实体目录；task worktree 仅有 `.cache -> canonical/.cache` 与
`outputs -> canonical/outputs/TASK-ID` 两个顶层业务链接，`.venv` 为私有实体
目录。旧 worktree 的真实 `outputs/` 在全量冲突预检后才迁移，任何同名文件或链接
都会拒绝而不覆盖。smoke 产物改写到 task `outputs/smoke/`。

本机 yrfs 已实测拒绝跨目录 hardlink（同一 `st_dev` 仍返回 `EPERM`），且
`cp --reflink=always` 返回 `Operation not supported`。实现因此在默认严格
`hardlink` 模式安装前创建临时跨目录链接并核验 inode/link count；当前主机正确
提前失败，绝不把 uv copy fallback 计作 hardlink 通过，临时 probe 已清理。远端
`wuwen-2` 只进行了只读检查，未创建文件、安装环境或修改远端项目；该方案已按用户
纠正停止。

代码已提供显式 `hardlink`、`symlink`、`copy` 模式入口。当前默认仍为严格
`hardlink`；`symlink` 作为节省空间候选，要求 canonical `.local/uv-cache` 作为
不可 clean/prune 的持久 package store，第三方包可指向它，而 editable table1000
始终以 `--link-mode copy --no-deps -e` 安装到自身 worktree。默认是否切换到
symlink，等待独立 A/B 升级、卸载、editable 隔离和空间实测结论后再作小提交。

验证（现有本机 copy 环境，仅验证真实运行，不声称硬链接）：

- `Markings_Letter_Holder` GSO 真实资产 probe：PASS；
- ManiSkill CPU：PASS；Table-10 0002 `red-then-blue` reference replay：`valid=true`；
- GPU 1 ManiSkill render 与 GPU physics：PASS；
- `tests/unit/test_data_validation.py tests/unit/test_cli.py`：40 passed；
- `bash -n scripts/worktree_env/*.sh` 与 `git diff --check`：PASS；
- canonical `.cache` / `outputs` 为实体，当前 task 的两个业务链接、输出目标和
  source/worktree `pyproject.toml` inode 分离均已核验。
