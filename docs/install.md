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
