# 独立审阅 MAM 项目隔离与分支发布迁移

Review source delivery (source TASK-ID: 25a3fcd3-962b-4448-9650-e4281e5ea1c1):
{
  "task": "25a3fcd3-962b-4448-9650-e4281e5ea1c1",
  "commits": {
    "multi-agent-manager": "4d5d393109810797b35d25ff3ba074604cc81c26"
  }
}

Source task requirements:

# MAM 多项目配置与发布分支

在独立 MAM worktree 实施，base 801901f414fa1f9dcc5791dd179e0865a92593d6。先遵循AGENTS和README。

## 用户决策
mam 从当前目录逐级向上找最近 .mam/env.json。三个必填键 MAM_ROOT、PROJECT_ROOT（绝对路径）、MAM_BRANCH（有效本地分支名）。找不到报错；最近文件无效报错，不向上回退。取消硬编码root和环境默认回退；不另建项目注册系统。建议删除--root，以免与唯一配置来源冲突；测试改用临时项目env.json。help在无配置时可用。
MAM_ROOT隔离所有task/job/wait/锁/归档登记，PROJECT_ROOT/workspace管理任务工作区，业务仓库来源PROJECT_ROOT/REPO（保持现有布局），MAM_BRANCH是已发布task/report所在分支。所有写死main的发布/读要求/状态逻辑改用配置分支；发布要求MAM checkout在该分支，不自动切换。MAM_ROOT可以是普通checkout或linked worktree，不要primary()将linked根错误归并。保留现有并发发布、边界安全、进程身份保护。

## 交付与验证
修改代码、测试、设计文档和install文档相关内容；README/AGENTS由Manager修改，避免同时编辑。覆盖两独立项目隔离、子目录发现、最近优先、缺失/坏配置、路径别名、linked MAM根、非main发布且main不变、错误分支拒绝、已有记录/job不损坏；完整测试通过。用旧安装mam在共享根发布交付报告，Manager在验收后才迁移生产。不要更改现有生产分支、配置、运行中的训练和环境；不得自行安装合并。清理短测试产物，保留worktree。报告给出commit、修改文件、测试和Manager迁移注意事项。

## Manager迁移决策补充
用户已确认本轮由Manager在实现/review完成后重写main历史，仅从main全历史过滤.tasks；project/state-vla保留原始完整历史。MAM开发worktree从main取基线，代码交付回main；生产MAM checkout处于project/state-vla。不要让新代码要求发布分支必须名为main，也不要把项目记录合回main。你无需执行历史迁移；在报告中核对独立发布分支与开发main共存是否受现有workspace add/primary逻辑影响。README已由Manager提交bdccfd0，可只读核对。

接口使用者审计：scripts/create_worktree.sh 当前最后一行使用 --root，删除参数时需同步修正并实际验证一键创建，避免新main无法创建worktree。所有仓库内入口对移除参数的调用需扫描（不改历史.tasks）。安装从main取代码，不依赖生产checkout分支为main。

Source report:

# 交付：MAM 项目配置发现与独立发布分支

## 完成项

- `mam` 从当前目录向上查找最近的 `.mam/env.json`，要求 `MAM_ROOT`、`PROJECT_ROOT` 和现有本地 `MAM_BRANCH`；没有配置或最近配置无效时明确报错，不回退到上层配置。
- 管理记录、任务草稿、job、wait 和锁位于 `MAM_ROOT`；业务仓库和 task workspace 从 `PROJECT_ROOT` 派生。配置路径会解析为实际绝对目录，MAM 根可为普通 checkout 或 linked worktree。
- 已移除 CLI 的 `--root` 和默认根。已发布 task/report 的读取、状态和发布均使用 `MAM_BRANCH`；发布要求 MAM worktree 当前 checkout 正是该分支，不自动切换。
- 修正 `scripts/create_worktree.sh`：新建的 MAM task worktree 在自身目录运行无 `--root` 的 smoke，因此通过祖先 `.mam/env.json` 发现项目配置。
- 更新任务管理设计与安装文档。README、AGENTS 未修改。

## 交付位置

- worktree：`/mnt/public/xcj/Projects/workspace/25a3fcd3-962b-4448-9650-e4281e5ea1c1/multi-agent-manager`
- 分支：`task/25a3fcd3-962b-4448-9650-e4281e5ea1c1`
- commit：`4d5d393109810797b35d25ff3ba074604cc81c26` (`feat: configure MAM per project`)
- 修改文件：`multi_agent_manager/cli.py`、`scripts/create_worktree.sh`、`tests/test_task.py`、`docs/task-management-design.zh-CN.md`、`docs/install.md`。

## 验证

运行 `.venv/bin/python -B -m unittest discover -s tests -v`，37 项全部通过。

覆盖两项目隔离、子目录和最近配置、缺失/坏配置、路径别名、linked MAM 根、非 `main` 发布而 `main` 不变、错误分支拒绝且已有 job 不变，以及从 primary `main` 创建 task worktree、由 linked `project/state-vla` MAM 根管理的端到端入口。

## Manager 迁移注意

- 本交付未执行生产迁移、历史过滤、安装或合并。将代码交付到 `main` 后，保留 Manager 已提交的 README 更新（`bdccfd0`）。
- 按已确认的方案，只从 `main` 历史过滤 `.tasks`；`project/state-vla` 保留完整历史。安装仍从 `main` 取得工具代码，生产 `MAM_ROOT` 可 checkout 在 `project/state-vla`。
- 在项目目录放置 `.mam/env.json`，令 `MAM_ROOT` 指向生产 MAM worktree、`PROJECT_ROOT` 指向业务仓库父目录、`MAM_BRANCH` 为 `project/state-vla`。发布前确认该 MAM worktree 已 checkout 到配置分支。
- 使用更新后的 `scripts/create_worktree.sh`；其 smoke 不再接受 `--root`，从新 task worktree 的祖先目录发现配置。

## 独立验收
读取源任务最新要求与报告，创建独立MAM worktree，从4d5d393109810797b35d25ff3ba074604cc81c26审阅。Manager已创建project/state-vla预备分支供新脚本只读发现配置，生产仍在main且安装仍是旧CLI；交付报告使用当前安装mam在共享MAM根发布，不切生产分支，不安装合并。
重点独立检查：最近env发现/不回退/--root移除、不同项目记录与锁/wait隔离、linked MAM根不误归并、PROJECT_ROOT业务源和工作区、发布精确修改目标分支而main不变、并发发布和旧登记安全。运行完整测试及实际一键创建入口。核对README（main bdccfd0）与设计/install文档无冲突。审计主分支开发/项目分支发布流程，避免旧主分支硬编码和脚本遗留。报告实际问题及严重度，或GO和验证证据。清理临时产物，保留本任务worktree。不要访问GPU或改变训练。

文档核对补充：设计文档开头仍链接README的#等待和#工作区，当前README已是#休眠管理且工作区步骤在#执行与交付；可作为小修复提交到本review分支。其余实际代码问题先报告给Manager裁定。

Manager已在源任务追加移除REPOS五库硬编码：允许PROJECT_ROOT下任意合法单层仓库名，保留路径边界/primary/script校验。作者将交付增量commit；本review需以最终commit复核此项，当前可继续其余独立检查，等增量到达再给最终结论。
