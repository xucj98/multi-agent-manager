task_revision: a94c1ec1f6fd5c6d72fa72a6fd674d1ff92e17e7

# MAM 改名、安装与文档精简

仓库已迁至 `/mnt/public/xcj/Projects/multi-agent-manager`，分支 main；原 agent-workflow 目录已移除。历史任务及状态保留，历史路径按原记录保存。本轮未操作正式 GPU 实验及其结果。

实现交付 commit：`16963ec49206a4cd94c0d6334c215a7a8dc22063`；AGENTS/README 精简 commit：`061333562d9f19689872297003daf9c933ff8648`；pipx 安装语法修正：`21e873ecd9a1150fa1f41698da44b5dd5af30d49`；交互终端 PATH 说明：`9cba56975dd7879552976cc514100eebd09122f6`。设计文档保持原样，AGENTS 无设计文档必读要求。

本机通过以下命令完成 pipx 普通安装，命令入口为 `/root/.local/bin/mam`，独立环境为 `/root/.local/share/pipx/venvs/multi-agent-manager`，Python 3.12.3，分发名 multi-agent-manager 0.1.0。安装元数据固定 Git commit 为 `21e873ecd9a1150fa1f41698da44b5dd5af30d49`；后续变更只涉及文档和任务记录。

```bash
pipx install --force 'multi-agent-manager @ git+file:///mnt/public/xcj/Projects/multi-agent-manager@main'
pipx ensurepath --force
```

用户报告交互终端 `mam: command not found`，从不含 `/root/.local/bin` 的初始 PATH 启动交互 Bash 后复现。安装入口、解释器正常，根因是 Bash 初始化未加入 pipx 命令目录。ensurepath 已为本机 `.bashrc` 与 `.profile` 添加该路径；使用干净 PATH，从 `/tmp` 分别启动 `bash -ic` 与 `bash -lic`，`command -v mam` 和 `mam --help` 均通过。已有终端需执行 `export PATH="$PATH:/root/.local/bin"`，或重新打开终端。

实现者与空白验收者的独立环境测试均为 21 项通过；空白验收覆盖 pipx 普通安装、任意目录调用、自己的 worktree/editable 环境、短 CPU job 的 running→stopped→archived 和真实 App Server 状态查询。PATH 增量验收也通过：独立 agent 从干净 PATH 启动两种交互 Bash 均可调用 mam，并认可新增安装说明。报告位于 `.tasks/36df8d93-d9a9-462a-99c0-8ff461f45d63/report.md`，无阻断问题。

Manager workspace：`/mnt/public/xcj/Projects/workspace/6cef08d3-c6c2-432e-808b-7edd7c6cfb1b`，无代码 worktree。实现任务 `5896e59c-e3e8-4043-b6b6-ba6e81f3a7db` 与空白验收任务 `36df8d93-d9a9-462a-99c0-8ff461f45d63` 已关闭执行者、通过 CLI 归档并删除其 workspace 和任务分支。验收固定代码 HEAD 为 `21e873ecd9a1150fa1f41698da44b5dd5af30d49`。本任务完成，无未完成项，简报发布后归档 Manager 的空 workspace。
