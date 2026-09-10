# 独立 code review 要求
审查 table-1000 一键环境实施。源任务当前首提交2af4b12，其最新增量commit d30dca0e56005df548323c603c0c36e43e1afa96 已把三方包策略改为uv symlink，editable copy；后续还将完成全局cache整合配置。请先从git show阅读这两个commit（读真实仓库AGENTS），待迁移agent/manager确认cache窗口完成后用mam workspace add本TASK --repo table-1000 --base 最新交付commit创建独立review worktree；不要在缓存迁移时运行uv/pip安装。
必须审查：主repo实体资产/outputs且无顶层业务软链；各worktree独立.venv，三方包symlink到持久 /mnt/public/xcj/cache/uv，editable指向自己源码；.cache->canonical/.cache，outputs->canonical/outputs/TASK-ID；三参数.local入口遵循base版本，路径配置可维护；失败恢复/幂等/错误与既有数据安全；cache不可clean/prune生命周期；实际热创建时间/字节证据，不再追求本机不支持的hardlink。按可复现影响报告严重级别，避免对未要求的跨平台或任意恶意输入过度设计。允许与实施agent协调指出候选问题，裁决归manager；不修改实施代码。
先回报CODEX_THREAD_ID，遵循MAM规范及report发布。不派发agent。

# 独立 code review table-1000 一键 worktree 环境

Review source delivery (source TASK-ID: b52655b9-cb65-4c6e-94be-2cad789235e6):
{
  "task": "b52655b9-cb65-4c6e-94be-2cad789235e6",
  "commits": {
    "table-1000": "2af4b120fc5655df40101ab2bb77a9ef9c2192b9"
  }
}

Source task requirements:

# 目标
实现 table-1000 纳入 MAM 的一键 worktree 环境：创建独立 worktree、独立 .venv、uv hardlink 复用缓存、资产软链接，使空白上下文 subagent 仅靠文档即可完成准备和 smoke。
# 范围与要求
先阅读 MAM AGENTS.md、README 核心原则/执行与交付、.local/README.md，了解 mam workspace add 实际调用的 .local 协议。通过 ssh wuwen-2 只读调研 /mnt/public/xcj/Projects 下各 repo 的 .local 参考（若别名不可用，调查本机 ssh 配置及可用对应主机，明确报告）。可并行调研旧源 /mnt/public/xcj/table-1000 的依赖与 smoke 入口，不修改源。
迁移 agent 正在创建 /mnt/public/xcj/Projects/table-1000/table-1000 与共享资产，请与 manager/迁移 agent 协调 base 和资产位置。canonical repo 就绪后，用 mam workspace add TASK-ID --repo table-1000 --base COMMIT 创建独立 worktree；若尚无 .local 入口无法执行，调研受支持引导流程并报告 manager，允许最小 bootstrap 后回到 MAM 协议。
在 task worktree 实施 .local 脚本/文档、需要的依赖锁定和 AGENTS.md 引导。确保新 worktree 有独立 .venv，通过 uv --link-mode hardlink（cache 同文件系统）节约时间空间；共享资产的软链接完整且安全；脚本幂等、失败清楚、可从新任务一键使用。不要硬链接可被工作修改的源代码；不复制旧 venv。根据实际项目做有意义 smoke，验证 hardlink inode 及 venv 独立性。不要运行正式训练。不要自行派发下级 agent。
# 交付验收
提交代码，报告 commit、精确一键命令、依赖来源、cache/资产路径、测试及边界；发布 mam report；后续另有独立 review 和空白上下文验收。

# Manager 验收补充
默认一键环境须覆盖当前实际 ManiSkill/reference 工作流，不能只安装 CPU/dev 测试依赖而让后续 agent 手动补核心 simulator/torch。按现有 README/pyproject/旧环境核验依赖；至少执行真实资产加载及场景 smoke，GPU 可用时包含渲染/模拟。可以合理分层安装但默认入口需完成当前工作流。参考 wuwen-2 的版本化脚本加 .local wrapper 模式。验证任意 cwd 的底层入口、重复执行与失败恢复、独立 venv 以及真实 cache inode hardlink 证据。

# 用户追加：outputs 也纳入软链接管理
用户询问软链接数量并明确 outputs 类目录也应软链接。当前 primary 与 task worktree 各只有 .cache 一条顶层链接。请完善集中成果目录：PROJECT_ROOT/outputs/main 供 primary，PROJECT_ROOT/outputs/TASK-ID 供 task worktree，并在各 repo 创建 outputs 软链接指向对应目录，避免多 agent 覆盖且归档 worktree 后保留成果。已有 worktree outputs 内容要安全迁移，遇冲突不能覆盖；不要把历史研究备份当默认输出目录。对数据流核验是否还有其他真正需要共享/集中留存的 repo 顶层目录，按必要性实现并列清单。更新文档、smoke 与 report，明确每个 worktree 顶层业务软链总数/去向（区分 Python venv 内部软链）。

# 用户最新布局要求（覆盖之前路径约定）
用户明确：主仓库不要软链接，PROJECT_ROOT 下面只有 workspace、mam 及各个 repo。保留 MAM 必需隐藏 .mam 配置；所有业务实体目录归属 canonical repo。请由本环境任务协调并完成：将项目 assets 实体迁为 canonical/.cache 实体（先安全移除已核验旧软链），canonical/outputs 为实体，worktree/.cache -> canonical/.cache，worktree/outputs -> canonical/outputs/TASK-ID。uv cache 和本机配置收拢 canonical/.local 内；不再保留 PROJECT_ROOT/assets、outputs、cache 等业务目录。迁移任务负责备份目录收拢 canonical/.local/migration-backup，与你直接协调。更新所有路径、文档、已有worktree软链与验收；确保主repo顶层无业务软链，worktree仅链接实际需要资产/成果，清理先前空目录。主repo Python自身venv内部系统解释器软链无需改变。

# 用户纠正：wuwen-2 是不同集群
wuwen-2只作只读设计参考，与本机并不共享/mnt/public；禁止通过远端创建环境/hardlink解决本机需求。此前manager基于同路径可能共享的探针/远端方案已撤销。如果已创建本任务临时探针，仅清理这些探针并报告。现有本机copy安装可继续真实smoke及代码review，但不能宣称hardlink验收通过。针对本机yrfs跨目录硬链EPERM给出可行选择，等待manager裁决；不得擅自将环境迁/root或改变用户主repo无软链布局。

Source report:

# 阶段性交付（待 symlink 隔离验证后确定默认包链接策略）

- worktree：`/mnt/public/xcj/Projects/table-1000/workspace/b52655b9-cb65-4c6e-94be-2cad789235e6/table-1000`
- 分支：`task/b52655b9-cb65-4c6e-94be-2cad789235e6`
- 当前提交：`2af4b120fc5655df40101ab2bb77a9ef9c2192b9` (`feat: add MAM worktree environment setup`)

已提交版本化的 MAM `.local` wrapper 模板、任意 cwd 的
`mam_workspace_add.sh`、完整 CUDA 12.4/Python 3.12 ManiSkill 安装入口、激活和
smoke 脚本，以及空白上下文可读的 `AGENTS.md` 与环境指南。精确入口为：

```bash
bash /mnt/public/xcj/Projects/table-1000/table-1000/scripts/worktree_env/mam_workspace_add.sh \
  TASK-ID BASE-COMMIT
```

默认依赖是现有完整锁 `requirements/lock-linux-cu124-py312.txt`，使用仅 PyPI 与
官方 PyTorch CUDA 12.4 index、`--no-deps`、`unsafe-best-match`，保留
`torch==2.6.0+cu124`、`mani-skill==3.0.1`、`sapien==3.0.3` 和
`mplib==0.2.1`。

布局已按最新要求实现：canonical 的 `.cache/`、`.local/uv-cache/`、`outputs/`
均为实体目录；task worktree 仅有 `.cache -> canonical/.cache` 与
`outputs -> canonical/outputs/TASK-ID` 两个顶层业务链接，`.venv` 为私有实体
目录。旧 worktree 的真实 `outputs/` 在全量冲突预检后才迁移，任何同名文件或链接
都会拒绝而不覆盖。smoke 产物改写到 task `outputs/smoke/`。

本机 yrfs 已实测拒绝跨目录 hardlink（同一 `st_dev` 仍返回 `EPERM`），且
`cp --reflink=always` 返回 `Operation not supported`。实现因此在默认严格
`hardlink` 模式安装前创建临时跨目录链接并核验 inode/link count；当前主机正确
提前失败，绝不把 uv copy fallback 计作 hardlink 通过，临时 probe 已清理。远端
`wuwen-2` 只进行了只读检查，未创建文件、安装环境或修改远端项目；该方案已按用户
纠正停止。

代码已提供显式 `hardlink`、`symlink`、`copy` 模式入口。当前默认仍为严格
`hardlink`；`symlink` 作为节省空间候选，要求 canonical `.local/uv-cache` 作为
不可 clean/prune 的持久 package store，第三方包可指向它，而 editable table1000
始终以 `--link-mode copy --no-deps -e` 安装到自身 worktree。默认是否切换到
symlink，等待独立 A/B 升级、卸载、editable 隔离和空间实测结论后再作小提交。

验证（现有本机 copy 环境，仅验证真实运行，不声称硬链接）：

- `Markings_Letter_Holder` GSO 真实资产 probe：PASS；
- ManiSkill CPU：PASS；Table-10 0002 `red-then-blue` reference replay：`valid=true`；
- GPU 1 ManiSkill render 与 GPU physics：PASS；
- `tests/unit/test_data_validation.py tests/unit/test_cli.py`：40 passed；
- `bash -n scripts/worktree_env/*.sh` 与 `git diff --check`：PASS；
- canonical `.cache` / `outputs` 为实体，当前 task 的两个业务链接、输出目标和
  source/worktree `pyproject.toml` inode 分离均已核验。
