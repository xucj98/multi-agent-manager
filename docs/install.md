# 安装与更新

安装者需要一个项目根目录、一个用于保存任务记录的 MAM 分支，以及可用的 Python 和 pipx。任务记录保存在独立的管理分支，不进入 MAM 的代码主分支。

首次安装时选择项目管理分支并创建项目配置：

```bash
project=/absolute/path/to/PROJECT_ROOT
mam_branch=project/PROJECT_NAME

mkdir -p "$project/.mam"
git clone git@github.com:xucj98/multi-agent-manager.git "$project/multi-agent-manager"
cd "$project/multi-agent-manager"
git switch -c "$mam_branch" origin/main

cat > "$project/.mam/env.json" <<JSON
{
  "MAM_ROOT": "$project/multi-agent-manager",
  "PROJECT_ROOT": "$project",
  "MAM_BRANCH": "$mam_branch"
}
JSON

sudo apt install -y pipx
bash scripts/install.sh
```

`MAM_ROOT` 保存任务记录和 service runtime；`PROJECT_ROOT` 保存业务仓库及 task workspace。安装 checkout 可以和 `MAM_ROOT` 使用不同 worktree，但必须属于同一个 Git 仓库。安装器会把 `mam` 安装到用户环境，运行 checkout 的测试，并在需要时更新 App Server 的 wait 配置。配置或验收失败时不会停止已有的项目 service。

如果项目已有配置和任务记录，更新时保留 `.mam/env.json` 及 `MAM_ROOT`，在任一同一 Git 仓库的代码 checkout 中切换到目标版本，再运行：

```bash
git fetch --all
git switch BRANCH-OR-TAG
bash scripts/install.sh
```

安装器只更新当前 checkout 对应的 MAM 程序和该项目的 service；不会把另一个项目的 task、workspace 或 service 状态复制过来。

安装成功后，可在项目目录中查看和管理 service：

```bash
mam service status
mam service start
mam service start --manager AGENT-ID
mam service stop
```

新项目没有 Manager 绑定时，service 会处于 `awaiting_manager`，首次由 Manager 执行 `mam task create` 或 `mam task bind` 后才开始投递。已有任务却无法确定 Manager 时，显式运行 `mam service start --manager AGENT-ID`。

默认工作流是在当前工作完成后结束 turn，由 proactive service 后续投递待办。需要在当前 turn 内等待时，可使用：

```bash
mam wait
mam wait list
mam wait stop manager
mam wait stop --agent AGENT-ID
```

`mam wait` 最多等待一小时；已有待办会立即返回。用户 steer 或 Manager 消息可以解除 wait，`wait stop` 也可手动解除，但这些操作不会停止 job。

## 项目 hooks

hooks 由项目安装与配置者准备。MAM 统一调用项目入口，项目入口决定是否及如何调用 repo hook；MAM 不再自动调用第二层。项目规则写在 `.local/README.md` 或各仓库的 README.md、AGENTS.md。

```text
MAM_ROOT/.local/hooks/                 # MAM 调用的项目入口
  workspace_add
  before_task_archive
PROJECT_ROOT/REPO/.local/hooks/        # 项目入口可调用的仓库入口
  workspace_add
  before_task_archive
```

入口是带 shebang 的可执行普通文件，可以使用 Bash、Python 等语言。MAM 从 `MAM_ROOT` 执行项目 hook，向 stdin 写入一个 JSON 对象；项目 hook 可完成整个操作，也可按项目规则调用 repo hook。

### 触发时机

| 项目入口 | 时机与职责 | 缺失时 |
| --- | --- | --- |
| `workspace_add` | 登记本次创建后执行；创建指定 worktree，按需安装环境、建立共享软链接。返回成功后 MAM 核对所属仓库、路径和分支。 | 拒绝创建 |
| `before_task_archive` | 全部 job 已归档、中央任务目录 Git 干净后，删除资源前检查项目收尾条件。 | 直接继续归档 |

已有 ready worktree 的重复 add 不执行 hook；创建失败后修复并以相同 base 重试，会再次执行。归档前检查应可重复执行，每次归档重试均重新检查；已归档任务不再执行。归档 hook 只检查，实验记录更新、成果转存和远端清理由项目流程提前完成。

### 输入与返回

两个入口使用相同的 JSON 结构，路径均为绝对路径：

| 字段 | 内容 |
| --- | --- |
| `schema_version`、`event` | 协议版本 `1`；事件为入口名称 |
| `project_root`、`mam_root` | 当前实例的根目录 |
| `task` | `id`、`title`、`status`、`workspace`、中央任务目录 `task_dir` |
| `repos` | 登记仓库数组：`name`、`source`、`path`、`branch`、`base`、`state`、`removed`、`branch_removed`、交付 `commit`；无交付时 commit 为 null |
| `repo` | 创建时为本次仓库名；归档时为 null |
| `jobs` | 已保存的 job 摘要；不隐式探测进程 |
| `options` | 本次 `note` 与 `force`；创建时为 null 和 false。force 表示是否强制删除 worktree 和任务分支，不能绕过 hook。 |

退出码 0 表示成功；非 0、启动失败或超时使本次操作失败，MAM 返回入口和错误摘要。输出只作诊断，不作为 MAM 状态。归档 hook 拒绝时 MAM 不开始删除；创建失败可能留下部分 worktree，修复后重试。hook 内不要调用修改 MAM 状态的命令。

可在 `.mam/env.json` 增加 `HOOK_TIMEOUTS`，按入口名设置正数秒数；默认 `workspace_add` 为 1800 秒，`before_task_archive` 为 60 秒。hook 应同步完成，不启动脱离进程组的后台进程；时限覆盖项目到 repo 的整个调用链，超时终止 hook 所在进程组。

### 部署模板

[参考模板](../templates/hooks/)只展示调用和转发，不包含项目的实验验收规则：

- `project/workspace_add`：调用本次源库的同名 repo hook，并将 cwd 切到源库。
- `repo/workspace_add`：将 JSON 转成现有 `.local/create_worktree.sh` 的 `BASE_COMMIT BRANCH WORKSPACE_ROOT` 三参数，复用已有环境脚本。
- `project/before_task_archive`：预留项目检查位置，再逐库调用已配置的同名 repo hook，任一拒绝即停止。转发时将 `repo` 设为该仓库名，cwd 为源库。
- `repo/before_task_archive`：预留单库检查位置，默认通过；按项目需要补充。

部署时将所需模板复制到上述 `.local/hooks/` 并赋予执行权限。创建模板只是一个分派方式；项目可以在项目入口直接创建纯文档 worktree，也可以调用仓库内随 Git 管理的安装脚本。MAM 不自动安装模板，也不回退旧入口；迁移时先配置项目和 repo 入口，旧环境脚本可由适配模板继续调用。
