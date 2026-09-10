# 安装与更新

在本机安装，`wuwen-1` 无需安装 MAM。本机已提供 pipx；以下命令安装 `main` 上已提交的工具代码，更新时再次执行安装命令：

```bash
pipx install --force 'multi-agent-manager @ git+file:///mnt/public/xcj/Projects/multi-agent-manager@main'
```

首次安装后，将命令目录加入 PATH：

```bash
pipx ensurepath --force
export PATH="$PATH:/root/.local/bin"
mam --help
```

`ensurepath` 为后续终端保存 PATH，`export` 让当前终端立即生效。命令入口为 `/root/.local/bin/mam`，可以从任意目录调用；`mam --help` 不需要项目配置。pipx 使用独立 Python 环境，安装内容固定于安装时的 Git 提交。

运行任务、job、wait 或 workspace 命令前，在项目目录或其祖先目录放置 `.mam/env.json`：

```json
{
  "MAM_ROOT": "/absolute/path/to/mam-worktree",
  "PROJECT_ROOT": "/absolute/path/to/projects",
  "MAM_BRANCH": "project/state-vla"
}
```

`MAM_ROOT` 可以是普通 checkout 或 linked worktree，必须已有配置中的本地分支。`PROJECT_ROOT` 下保留业务仓库与 `workspace` 的既有布局。安装来源的 `main` 只承载工具代码；项目任务和报告发布到 `MAM_BRANCH`，发布前该 MAM worktree 必须 checkout 在此分支。
