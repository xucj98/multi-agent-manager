# 安装与更新

在运行 agent 的本机安装。以下命令安装 GitHub 仓库 `main` 上的工具代码；更新时重新执行 `pipx install`：

```bash
apt install -y pipx
pipx install --force 'multi-agent-manager @ git+ssh://git@github.com/xucj98/multi-agent-manager.git@main'
```

首次安装后，将命令目录加入 PATH：

```bash
pipx ensurepath --force
export PATH="$PATH:$HOME/.local/bin"
mam --help
```

`ensurepath` 为后续终端保存 PATH，`export` 让当前终端立即生效。默认命令入口为 `~/.local/bin/mam`，可以从任意目录调用；`mam --help` 不需要项目配置。pipx 使用独立 Python 环境，安装内容固定于安装时的 Git 提交。

开发 MAM 自身时，`mam workspace add TASK-ID --repo multi-agent-manager --base COMMIT` 会调用 MAM 仓库的环境脚本，在新 worktree 中执行 `pip install --no-deps --editable`。MAM 使用 `flit_core` 作为构建后端，因此该安装步骤需要包索引或已有缓存提供构建后端；`--no-deps` 只跳过运行时依赖。使用已经安装好的 `mam` 管理其他仓库时，不会执行这一步；其他仓库如何安装环境，由它们自己的入口决定。

MAM 仓库自己的 `.local/create_worktree.sh` 是被忽略的部署配置，应选择本机可用的 Python ≥3.10；这个版本下限仅属于 MAM。MAM 仓库中的 `scripts/local_create_worktree.sh` 是无站点默认值的复制模板，配套 `scripts/create_worktree.sh` 会验证所选解释器，不要求特定挂载路径。被管理的其他仓库自行定义其 `.local/create_worktree.sh` 和依赖要求；例如 table-1000 当前环境使用 Python 3.12。

运行任务、job、wait 或 workspace 命令前，在项目目录或其祖先目录放置 `.mam/env.json`：

```json
{
  "MAM_ROOT": "/absolute/path/to/mam-worktree",
  "PROJECT_ROOT": "/absolute/path/to/projects",
  "MAM_BRANCH": "project/state-vla"
}
```

`MAM_ROOT` 可以是普通 checkout 或 linked worktree，必须已有配置中的本地分支。`PROJECT_ROOT` 下保留业务仓库与 `workspace` 的既有布局。安装来源的 `main` 只承载工具代码；项目任务和报告发布到 `MAM_BRANCH`，发布前该 MAM worktree 必须 checkout 在此分支。
