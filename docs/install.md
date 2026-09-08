# 安装与更新

在本机安装，`wuwen-1` 无需安装 MAM。本机已提供 pipx；以下命令安装 main 上已提交的版本，更新时再次执行安装命令：

```bash
pipx install --force 'multi-agent-manager @ git+file:///mnt/public/xcj/Projects/multi-agent-manager@main'
```

首次安装后，将命令目录加入 PATH：

```bash
pipx ensurepath --force
export PATH="$PATH:/root/.local/bin"
mam --help
```

`ensurepath` 为后续终端保存 PATH，`export` 让当前终端立即生效。命令入口为 `/root/.local/bin/mam`，可以从任意目录调用。pipx 使用独立 Python 环境，安装内容固定于安装时的 Git 提交。
