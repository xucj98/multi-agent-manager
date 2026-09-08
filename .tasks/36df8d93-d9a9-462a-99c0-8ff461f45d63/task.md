# MAM安装与文档空白验收

任务UUID 36df8d93-d9a9-462a-99c0-8ff461f45d63；自己的workspace为Projects/workspace/同UUID。你是无历史上下文的gpt-5.6-terra max，负责只读review和实际验收，不改实现或文档。

稳定管理库：/mnt/public/xcj/Projects/multi-agent-manager。从其AGENTS、README及已安装mam帮助出发，先mam task show读取本任务发布版本。只审阅现行操作文档；docs设计记录不必读、不改。所有agent和管理CLI均在本机，wuwen-1不安装MAM，不启动GPU。

固定验收base：21e873ecd9a1150fa1f41698da44b5dd5af30d49，含代码16963ec、精简文档0613335和pipx安装语法21e873e。原库已改名；下方源材料中的agent-workflow是同一库的历史名称，不是当前操作入口。

## 验收范围

1. 按README确认本机pipx普通安装的mam（/root/.local/bin/mam）从/tmp等非Git目录可用，默认指向正确管理根；确认安装包来自pipx环境且不是editable，发布来源为明确Git提交。可直接审计现有安装与源码，不重复更新全局安装。
2. 通过已安装mam task workspace add，在自己的UUID目录创建repo=multi-agent-manager、base=上述SHA的完整worktree/独立环境；不创建其他业务库或复用作者workspace。检查私有mam的editable源码归属，再用该环境跑完整21项测试。
3. 只读review本次a5e94eef..16963ec的打包、默认根、命令命名、历史记录只读以及环境入口改动。已有核心算法/删除边界已验收，只需结合此次变化和完整回归验证，不展开旧设计或未支持用法。用实际mam help覆盖README所列入口。
4. 使用安装后的mam在本任务登记一个自己的短CPU进程，验证running→stopped→archived与App Server实际状态查询；自己清理进程和临时文件。无需SSH或重复上一轮的业务环境测试。
5. 空白阅读AGENTS/README/CLI帮助，判断是否简洁、职责清晰、存在歧义或重复到影响使用。设计文档未被修改，也未被要求阅读。若发现问题给出具体位置、复现或阅读障碍，由Manager/原作者修复。
6. 发布简短report：task_revision、完成/未完成、workspace及完整交付HEAD、实际命令/结果、问题或限制。保留自己的clean worktree待Manager验收归档；不自行删workspace。报告区分通过/未覆盖，不扩展功能或验证范围。

以上为你的执行要求。以下为源任务与交付的固定参考，非本轮新增实施要求。

---

# MAM安装与精简文档空白验收

Review fixed source delivery:
{
  "task": "5896e59c-e3e8-4043-b6b6-ba6e81f3a7db",
  "task_revision": "77e0800edc758080605c09e57d86950edb60ae22",
  "report_revision": "ea801c2bc31e172129c4c85eb41c0e6f0a549909",
  "commits": {
    "agent-workflow": "16963ec49206a4cd94c0d6334c215a7a8dc22063"
  }
}

Source task:

# MAM打包与仓库改名支持

任务UUID：5896e59c-e3e8-4043-b6b6-ba6e81f3a7db。自己的workspace：/mnt/public/xcj/Projects/workspace/5896e59c-e3e8-4043-b6b6-ba6e81f3a7db。执行者由Manager绑定。先读原管理库AGENTS，并通过已发布CLI show读取本任务及版本。

## 范围

在自己的agent-workflow worktree基于a5e94eefdb4e12d9e7ddf4c915d08cf5096b0a10实施；通过稳定原库 python -B scripts/task.py workspace add创建完整环境。最终项目名multi-agent-manager，命令mam。你负责Python打包、命令结构、相关环境脚本与必要测试。AGENTS/README/设计文档不修改，稳定原库目录迁移和系统pipx安装由Manager执行。

- 将现有标准库核心及job_runtime整理为可安装Python包，提供console script mam。普通安装后可从/tmp等任意cwd直接执行，不依赖当前cwd或包文件在Git仓库中。
- 现有接口统一变为 mam task <原子命令>，例如mam task list、mam task status UUID、mam task workspace add、mam task job list --attention。功能/状态/UUID/发布语义保持，保留--root仅供显式指定管理根/测试；不要新增另一套命令别名或旧scripts/task.py兼容入口。
- 默认管理根为本集群 /mnt/public/xcj/Projects/multi-agent-manager。这是用户明确限定的本机工具，不新增环境变量或配置系统。支持的管理repo名称改为multi-agent-manager；其workspace子目录也同名。历史归档记录只读取展示，不重写历史路径。
- 修改版本化环境入口，使新名的管理库worktree具有独立venv、当前源码可用的mam命令；本地三参数wrapper仍能解析稳定根。可以在开发worktree中editable安装，系统pipx发布安装使用普通非editable方式。无需runtime第三方依赖。
- CLI --help应能独立说明命令作用和参数；帮助保持简短，避免复制完整工作流程。设计文档不作为本次必读或更新对象。
- 保留并适配已有19项核心/runtime测试，补少量有意义的普通安装/任意cwd入口验证。不加数据库/后台服务、远端CLI安装、复杂配置、兼容层或额外provenance。预计净增业务代码/打包声明/入口合计约80–120行，现有代码移动不算新增；发现必要显著超出先向Manager报告原因。

## 迁移期间的交付

原库位置仍为 /mnt/public/xcj/Projects/agent-workflow，当前稳定scripts/task.py负责你的登记和报告发布，调用时用稳定原库的旧CLI，不用尚未迁移的新默认根。提交代码、清理本任务测试产物，在稳定原库本任务report.md写结果并用该旧CLI发布。报告列所依据任务revision、完整交付commit、实际验证及限制。

你不改名原目录、不更新系统pipx、不迁移登记JSON、不修改其他任务或原有GPU实验。Manager会在集成后从旧commit运行CLI归档你的worktree，再移动主目录；这是本次一次性迁移操作，不加入长期兼容代码。随后安排空白agent验证系统安装与新workspace。

Source report:

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
