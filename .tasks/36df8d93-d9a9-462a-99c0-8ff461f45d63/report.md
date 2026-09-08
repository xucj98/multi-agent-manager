task_revision: 39420d6dff0778767510d9d1a4281c04b1afdeb3

# MAM 安装与精简文档空白验收

通过。未修改实现、AGENTS/README、设计文档或全局环境。

固定验收版本：

- 原代码与安装验收 base：`21e873ecd9a1150fa1f41698da44b5dd5af30d49`。
- PATH 文档修复：`9cba56975dd7879552976cc514100eebd09122f6`（仅 `README.md`）。

完成与依据：

- 从非 Git 的 `/tmp` 使用 `/root/.local/bin/mam` 成功执行帮助、list、status 和 workspace add；顶层帮助显示默认管理根为 `/mnt/public/xcj/Projects/multi-agent-manager`。
- pipx 入口解析到独立 venv。安装包模块位于该 venv 的 site-packages，PEP 610 元数据为 Git `file:///mnt/public/xcj/Projects/multi-agent-manager`、明确 commit `21e873ecd9a1150fa1f41698da44b5dd5af30d49`，没有 editable 标记；两个环境的 `pip check` 均通过。
- 使用已安装的 `mam task workspace add` 创建唯一仓库 `multi-agent-manager`，base/HEAD 均为 `21e873ecd9a1150fa1f41698da44b5dd5af30d49`。私有 `.venv` 的 `mam` 为该 worktree 的 editable 安装，源码归属与 workspace 一致。
- 在私有环境执行 `.venv/bin/python -B -m unittest discover -s tests -v`：21 项通过，13.623 秒；`git diff --check a5e94eefdb4e12d9e7ddf4c915d08cf5096b0a10 16963ec49206a4cd94c0d6334c215a7a8dc22063` 通过。
- 只读审阅该提交范围：pyproject console script、固定默认根、`mam task` 子命令结构、旧脚本移除、归档记录不回写和本地 worktree editable 入口均与要求一致；对应普通安装、历史路径只读和环境入口测试已覆盖。实际运行顶层、task、workspace、job、archive 及各原子子命令的 `--help`，均成功且 README 所列入口可用。
- 用安装后的 mam 登记本机 `localhost` 短 CPU 进程 `56829171-4c66-443b-8d92-731d9fd11539`：running → stopped → archived。两次真实 `job list` 都经 App Server 查询绑定 agent，返回 `active`；进程已退出，job 已归档，无临时文件遗留。
- 第 7 条增量：从不含 `/root/.local/bin` 的 `env -i` 初始 PATH 在 `/tmp` 分别运行 `bash -ic` 与 `bash -lic`；两者的 `command -v mam` 均为 `/root/.local/bin/mam`，`mam --help` 均通过。未依赖本工具进程继承的 PATH，也未修改全局环境。

文档结论：现行 AGENTS（14 行）和 README 职责、发布边界、workspace 和报告格式清楚；CLI 帮助承接参数细节，未见影响使用的歧义或重复。精简提交为 46 行新增、94 行删除；`9cba569` 以 3 行新增、1 行删除补入 `pipx ensurepath --force`、当前终端 export 及两者区别，和实际 shell 行为一致。login shell 中 `/root/.local/bin` 出现两次，但命令解析正常，无阻断影响。

workspace 与交付：`/mnt/public/xcj/Projects/workspace/36df8d93-d9a9-462a-99c0-8ff461f45d63/multi-agent-manager`，分支 `task/36df8d93-d9a9-462a-99c0-8ff461f45d63`，完整 HEAD `21e873ecd9a1150fa1f41698da44b5dd5af30d49`；worktree clean，保留待 Manager 验收归档。

未覆盖（任务限定）：设计文档、此前已验收的核心算法和删除边界、SSH/wuwen-1、GPU 及业务环境测试；追加 PATH 验收未重复代码回归。问题：无。
