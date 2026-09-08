task_revision: 77e0800edc758080605c09e57d86950edb60ae22

# MAM 打包与仓库改名支持交付

已完成本任务的打包、CLI、环境入口和测试。执行 workspace：`/mnt/public/xcj/Projects/workspace/5896e59c-e3e8-4043-b6b6-ba6e81f3a7db`；唯一代码 worktree：其下 `agent-workflow`；分支：`task/5896e59c-e3e8-4043-b6b6-ba6e81f3a7db`。该工作区由稳定旧 CLI 从指定 base `a5e94eefdb4e12d9e7ddf4c915d08cf5096b0a10` 创建，含独立 venv。

交付仓库为迁移前的 agent-workflow，完整交付 commit：`16963ec49206a4cd94c0d6334c215a7a8dc22063`。打包主提交：`e603dad82bc759c87dc8fd5315b9c8243427c076`，后续提交补全各子命令独立帮助。相对指定 base，7 个文件共 132 行增加、75 行删除（Git 已识别两个模块移动），净增 57 行，包含测试适配。

## 完成内容

- 将核心移到 `multi_agent_manager/cli.py`，进程模块移到同包的 `job_runtime.py`；删除旧 scripts/task.py 入口，不提供旧命令别名或兼容脚本。
- 新增 pyproject.toml，分发名 `multi-agent-manager`，版本 `0.1.0`，Python >=3.10，console script 为 `mam`，运行时依赖列表为空。使用 flit_core 构建后端，构建依赖通过标准隔离构建安装；声明采用 [Flit 的构建与 console script 配置](https://flit.pypa.io/en/stable/pyproject_toml.html)。
- 所有原子命令位于 `mam task` 下：create/bind/workspace add/show/publish/list/status/archive/job add/list/archive。全局 `--root` 的准确位置示例为 `mam --root /absolute/management/root task list`。
- 默认管理根固定为 `/mnt/public/xcj/Projects/multi-agent-manager`，与 cwd、已安装包路径或源码 Git checkout 无关。支持的管理 repo 与创建的子目录均改为 `multi-agent-manager`，其余四库名称不变。
- 归档历史的 list/status/job list 查询保留原有 repo/path 字段，不为已归档任务刷新或重写登记记录；新任务继续按新名称登记。未迁移任何实际 JSON。
- 版本化环境入口创建新名 worktree、私有 venv，并 editable 安装当前源码，使该环境具备 mam。三参数本地 wrapper 的稳定根解析保持动态，未修改稳定原库 wrapper。源码 smoke 用 -B 避免遗留 pyc。
- 顶层及每个子命令的 --help 均可独立显示作用和参数，包含 archive 删除工作区及任务分支的说明。

## 验证

以下命令从上述代码 worktree 执行：

```bash
.venv/bin/python -m pip install --no-deps --editable .
.venv/bin/python -B -m unittest discover -s tests -v
.venv/bin/python -m pip check
bash -n scripts/create_worktree.sh scripts/local_create_worktree.sh
git diff --check
```

最终交付 commit 上结果：21 项全部通过，耗时 13.631 秒；无 skip。原有 19 项核心/runtime 测试全部保留并适配，新补 2 项：

1. 普通非 editable 安装到临时 venv；安装源目录不含 Git，安装后删除该源目录；从 `/tmp` 执行安装后的 mam --help、mam task archive --help、显式 root 的 task list，确认包实际来自安装环境的 site-packages，旧 `mam list` 形式被拒绝。
2. 模拟归档记录包含旧 agent-workflow 的 source/path；list、status、job list 后历史路径、JSON 字节和文件修改时间均保持不变。

既有环境测试也已加强：在临时真实新名主库中运行三参数 wrapper，创建独立 venv 和 editable mam，再从非 Git cwd 查询任务，最后安全归档该 worktree。其他测试继续覆盖并发发布与 index 定向同步、报告/review 版本、创建失败重试、归档删除保护、共享软链接目标保留、本地真实进程与 App Server 协议 fixture。

pip check 返回 `No broken requirements found`；shell 语法和空白检查通过。还实际查看了 mam、mam task job list、mam task archive、mam task workspace add 的独立帮助。

测试 TemporaryDirectory 已清理，自建测试进程已结束；当前工作树没有 tracked/untracked 改动，仅保留正常 gitignored `.venv/`。测试生成的源码 pyc 已清除。

## 迁移边界与交付状态

本任务范围无未完成项。没有修改 AGENTS/README/设计文档、其他任务、稳定原库代码、系统 pipx 或 GPU 实验；没有移动主目录或迁移登记 JSON。

系统级 pipx 非 editable 安装、主目录改名、实际新默认根的验证由 Manager 后续执行。本轮已验证普通安装的包独立运行能力；未声称系统 mam 已安装或新默认目录已迁移完成。当前本任务仍使用迁移前的 agent-workflow worktree，按任务安排由 Manager 使用旧版本 CLI 归档，再迁移原目录。

本报告使用稳定原库的旧 CLI 发布，交付 HEAD 由该入口记录。
