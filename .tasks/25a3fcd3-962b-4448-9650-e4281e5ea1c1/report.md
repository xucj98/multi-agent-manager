# 交付：MAM 项目配置发现与独立发布分支

## 完成项

- `mam` 从当前目录向上查找最近的 `.mam/env.json`，要求 `MAM_ROOT`、`PROJECT_ROOT` 和现有本地 `MAM_BRANCH`；没有配置或最近配置无效时明确报错，不回退到上层配置。
- 管理记录、任务草稿、job、wait 和锁位于 `MAM_ROOT`；业务仓库和 task workspace 从 `PROJECT_ROOT` 派生。配置路径会解析为实际绝对目录，MAM 根可为普通 checkout 或 linked worktree。
- 已移除 CLI 的 `--root` 和默认根。已发布 task/report 的读取、状态和发布均使用 `MAM_BRANCH`；发布要求 MAM worktree 当前 checkout 正是该分支，不自动切换。
- 修正 `scripts/create_worktree.sh`：新建的 MAM task worktree 在自身目录运行无 `--root` 的 smoke，因此通过祖先 `.mam/env.json` 发现项目配置。
- 增量补齐多项目仓库名：`--repo` 不再受五个仓库的固定名单限制，接受 `PROJECT_ROOT` 下任意合法单层目录名；绝对路径、`.`、`..`、正反斜杠和路径逃逸会在登记前拒绝，仍要求 source 为 primary Git checkout 且拥有非软链接 `.local/create_worktree.sh`。
- 更新任务管理设计与安装文档。README、AGENTS 未修改。

## 交付位置

- worktree：`/mnt/public/xcj/Projects/workspace/25a3fcd3-962b-4448-9650-e4281e5ea1c1/multi-agent-manager`
- 分支：`task/25a3fcd3-962b-4448-9650-e4281e5ea1c1`
- 初始 commit：`4d5d393109810797b35d25ff3ba074604cc81c26` (`feat: configure MAM per project`)
- 最终增量 commit：`6c124cee1c6afa709b88c438f34e23d48bddcdf3` (`feat: allow project-local repositories`)
- 修改文件：`multi_agent_manager/cli.py`、`scripts/create_worktree.sh`、`tests/test_task.py`、`docs/task-management-design.zh-CN.md`、`docs/install.md`。

## 验证

运行 `.venv/bin/python -B -m unittest discover -s tests -v`，38 项全部通过。

覆盖两项目隔离、子目录和最近配置、缺失/坏配置、路径别名、linked MAM 根、非 `main` 发布而 `main` 不变、错误分支拒绝且已有 job 不变，以及从 primary `main` 创建 task worktree、由 linked `project/state-vla` MAM 根管理的端到端入口。增量覆盖任意合法项目仓库名的创建/归档、空名和路径型输入拒绝、缺失或软链接入口脚本拒绝。

## Manager 迁移注意

- 本交付未执行生产迁移、历史过滤、安装或合并。将代码交付到 `main` 后，保留 Manager 已提交的 README 更新（`bdccfd0`）。
- 按已确认的方案，只从 `main` 历史过滤 `.tasks`；`project/state-vla` 保留完整历史。安装仍从 `main` 取得工具代码，生产 `MAM_ROOT` 可 checkout 在 `project/state-vla`。
- 在项目目录放置 `.mam/env.json`，令 `MAM_ROOT` 指向生产 MAM worktree、`PROJECT_ROOT` 指向业务仓库父目录、`MAM_BRANCH` 为 `project/state-vla`。发布前确认该 MAM worktree 已 checkout 到配置分支。
- 使用更新后的 `scripts/create_worktree.sh`；其 smoke 不再接受 `--root`，从新 task worktree 的祖先目录发现配置。
- `PROJECT_ROOT` 下无需维护仓库注册配置；任务可直接使用其合法单层 Git 仓库目录名作为 `--repo`。
