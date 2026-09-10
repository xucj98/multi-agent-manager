# Review 要求
独立审查本任务引用的迁移交付。只读核验新 clone origin/历史、源 dirty 备份、资产完整性和未复制项是否确实非当前运行所需。检查 source/canonical 的 AGENTS.md。此次没有代码改动，因此只读迁移验收不强制创建运行环境 worktree，避免与正在进行的一键环境实施竞争。不要修改源/资产/环境脚本。查阅实际代码判断资产遗漏，验证关键报告证据。报告可复现问题、严重级别和修复建议；无问题也明确证据和测试范围。先回报 CODEX_THREAD_ID 用于绑定，按 MAM 协议发布 report。不要派发下级 agent。

# 独立 review table-1000 迁移完整性

Review source delivery (source TASK-ID: 2783e0c3-4955-4cb0-99d9-24ed65693bbd):
{
  "task": "2783e0c3-4955-4cb0-99d9-24ed65693bbd",
  "commits": {}
}

Source task requirements:

# 目标
将 /mnt/public/xcj/table-1000 重新 clone 到 /mnt/public/xcj/Projects/table-1000/table-1000，迁移运行所需资产，为环境实施者提供准确清单。
# 范围与要求
先阅读 MAM AGENTS.md、README 核心原则/执行与交付、.local/README.md；检查源 repo 的 AGENTS.md、Git 状态、remote、分支、未提交工作和资产布局。通过真实 git clone 建立新 repo，保留可用 origin；不要修改、清理或覆盖源 repo。明确源未提交文件如何保留，不能静默丢失。资产复制到项目内稳定共享位置，由 worktree 软链接引用，避免重复复制；记录来源、大小、复制验证。不复制旧 venv 当作新环境。
本任务为首次仓库引入，允许先创建 canonical clone；需要修改 tracked 文件时仍建立独立 worktree。与环境实施 agent 协商共享资产位置、canonical branch/base；环境代码交由对方完成，不竞争修改。请尽快向 manager 报告 clone 可用路径/base 和资产概况。
# 交付验收
提供 clone remote/commit、源 dirty 状态处理、资产清单及完整性检查、后续风险；遵循 mam report 发布协议，保留验收材料。不得启动正式训练或数据生成。不要自行派发下级 agent。

Source report:

# 交付简报：table-1000 仓库与运行资产迁移

## 完成项

- 以真实 `git clone` 建立 canonical repo：
  `/mnt/public/xcj/Projects/table-1000/table-1000`。
  `origin` 的 fetch/push 均为 `git@github.com:xucj98/table-1000.git`，canonical
  base 为 `3fa574ba2793ea44a5a69fecfd82f761a7c1bd4c`（`main` 和 `origin/main`）。
- 旧源 `/mnt/public/xcj/table-1000` 在盘点时为
  `184d6b195bd44956f7a536ddee73177a2bb4d1fa`，确认是 canonical base 的祖先。
  上游在 clone 前已推进，因此刻意采用新 origin HEAD，未把新 clone 回退到旧源。
- 建立共享运行资产目录
  `/mnt/public/xcj/Projects/table-1000/assets`；canonical 的 ignored `.cache`
  为相对软链接 `../assets`。已通知环境任务使用同一路径建立 worktree 链接。
- 未复制旧 `.venv`（6.0G）或 `.venv.bak-mplib011`（6.0G）。本任务没有启动训练、数据生成或修改 tracked 项目文件；首次引入 canonical clone 按任务允许不建立本任务 worktree，也没有 delivery commit。

## 源工作区状态与保留

旧源保持未动，盘点时唯一的 Git 工作区改动是：

- `.gitignore` 增加 `.venv.bak-mplib011`；
- 未跟踪 `scripts/probe_scene/render_strip.py`。

两项均保存到
`/mnt/public/xcj/Projects/table-1000/migration-backup/2783e0c3-4955-4cb0-99d9-24ed65693bbd/`：

| 文件 | SHA-256 | 处理 |
| --- | --- | --- |
| `dirty-gitignore.patch` | `2251f0a42e0f4ad8e20a1d99f19def792329619813d41b4e78c07a88b548b21c` | `git apply --check` 已通过；仅在审阅后手动 `git apply --3way`，不会自动覆盖 canonical。 |
| `render_strip.py` | `dcd8024a1a0dee25346c472ad776a47d482a32684a9b21bc7d615cd916735e0b` | 与 canonical 上游已跟踪版本哈希一致，保留作证据，不复制回工作树。 |

完整恢复命令、源/目标、未复制项与风险写在同目录的 `MANIFEST.md`。

## 共享资产与完整性

旧源 `.cache` 指向 `/mnt/public/xcj/table1000-cache`。按当前运行代码的
`TABLE1000_ASSET_DIR`/`MS_ASSET_DIR` 路径，只迁移以下可用输入资产：

| 目标一级目录 | 文件数 | 字节数 | 相对路径内容 aggregate SHA-256 |
| --- | ---: | ---: | --- |
| `assets/` | 3,280 | 1,816,375,429 | `25946fb209558c22937f1edf1574907be7f50475364b0a908e10df8bf0e05d2b` |
| `maniskill/` | 470 | 87,217,479 | `f792cfe42e9a35b5d593600134a1eced57ecd6774aee35d36586121487b8cd1f` |

`rsync -aHnci` 的复制后校验无输出，两个 aggregate hash 的源/目标值相同；目录内无软链接。共享目录应只读使用，worktree 如需可写 cache 应另设本地目录。

未复制 `robotwin-assets/`（3.5G，当前 `robotwin2` 是 placeholder）、`robotwin-source/`（91K）和 `kubric-source/`（20M，均为可重 clone 的未引用源码），以及 13M ignored outputs/测试缓存。Git 已带入 tracked 的场景和 catalog `data/`，无需重复复制。

## 验证与后续风险

- `git fsck --no-dangling` 在 canonical clone 通过；origin URL、HEAD 与 `origin/main` 一致。
- environment agent 已获得 canonical 路径、精确 base、资产一级布局和完整性值，负责后续 `.local`/独立 venv/worktree 实现。本报告撰写前其在 canonical 中创建的 untracked `.local/` bootstrap 属于该任务，不是迁移改动。
- 当前资产覆盖 ManiSkill reference 路径；未来启用 RoboTwin/Kubric 后需要按其许可、provenance 与运行需求单独迁移/下载未复制缓存。
