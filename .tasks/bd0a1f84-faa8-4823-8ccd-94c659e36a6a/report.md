# 独立验收报告：table-1000 迁移完整性

## 结论

**通过（无 P0/P1/P2 迁移缺陷）。** canonical clone、源工作区 dirty
保留以及当前 ManiSkill/Table-1000 运行资产均可由只读核验复现。发现一项
不阻断的 P3 历史成果归档风险，见下文；它不影响当前 benchmark/runtime 启动。

本次按 review 要求未创建运行环境 worktree、未修改 source、canonical、资产或环境脚本，
也未派发下级 agent。源和 canonical 均无 `AGENTS.md`。

## Git clone 与历史

- canonical：`/mnt/public/xcj/Projects/table-1000/table-1000`；其 `main`、
  `origin/main` 和审查时 `git ls-remote origin refs/heads/main` 均为
  `3fa574ba2793ea44a5a69fecfd82f761a7c1bd4c`。fetch/push origin 都是
  `git@github.com:xucj98/table-1000.git`。
- `git fsck --no-dangling` 通过。旧源 HEAD
  `184d6b195bd44956f7a536ddee73177a2bb4d1fa` 在 canonical 对象库中且是该
  canonical commit 的祖先；两点之间为 7 个提交。因而目标没有回退到旧源快照，
  符合上游已推进后 clone 当前 origin 的交付说明。
- canonical 的 ignored `.cache` 是相对链接 `../assets`，实际解析为
  `/mnt/public/xcj/Projects/table-1000/assets`；当前运行代码的默认
  `TABLE1000_CACHE_DIR`、`MS_ASSET_DIR` 与 `TABLE1000_ASSET_DIR` 均能由此
  解析到迁移资产。

## 源 dirty 状态与备份

源 `/mnt/public/xcj/table-1000` 仍保持原状态：仅有修改的 `.gitignore` 与未跟踪的
`scripts/probe_scene/render_strip.py`（忽略项另计）。

- 当前 `.gitignore` diff 与
  `migration-backup/2783e0c3-4955-4cb0-99d9-24ed65693bbd/dirty-gitignore.patch`
  逐字节相同，SHA-256 均为
  `2251f0a42e0f4ad8e20a1d99f19def792329619813d41b4e78c07a88b548b21c`；对
  canonical 执行只读 `git apply --check` 通过。
- 备份的 `render_strip.py` 与源未跟踪文件相同，SHA-256 为
  `dcd8024a1a0dee25346c472ad776a47d482a32684a9b21bc7d615cd916735e0b`；
  canonical 已将同内容文件作为 tracked 文件带入。因此该本地文件没有静默丢失。

## 资产完整性与运行路径

对源 `/mnt/public/xcj/table1000-cache` 和项目共享目录逐树检查；两组
`rsync -aHnci --delete` checksum dry-run 均无输出，且文件数、总字节数、
软链接数和报告中的聚合 hash 一致：

| 树 | 文件数 / 字节数 | 源与目标聚合 SHA-256 |
| --- | ---: | --- |
| `assets/` | 3,280 / 1,816,375,429 | `25946fb209558c22937f1edf1574907be7f50475364b0a908e10df8bf0e05d2b` |
| `maniskill/` | 470 / 87,217,479 | `f792cfe42e9a35b5d593600134a1eced57ecd6774aee35d36586121487b8cd1f` |

两边这两个树都没有软链接。目标 ManiSkill 目录包含
`data/assets/mani_skill2_ycb/info_pick_v0.json` 和 78 个模型目录。

我还以当前 canonical 的代码和数据作静态路径核验：解析 299 个 `data/**/*.yaml` 和
`scripts/probe_scene/configs/*.yaml`，检查 99 个唯一 visual path、20 个锁定的 COACD
manifest，以及 25 个 GSO / 50 个 YCB dataset-model 映射；全部存在于迁移后的
`.cache/assets` 或 `.cache/maniskill` 中，缺失数为 0。此检查覆盖了当前 tracked
scene/config 的资产路径，而不只是目录级复制结果。

## 未复制项判断

- 旧 `.venv`、`.venv.bak-mplib011`、pytest/Ruff cache 均受 `.gitignore` 忽略；目标
  项目中未发现被复制的旧 venv，符合“新环境不能复用旧 venv”的要求。
- 当前 `src/`、`scripts/`、`configs/` 与 README 对
  `robotwin-assets`、`robotwin-source`、`kubric-source` 的直接引用为 0。RoboTwin 2.0
  与 Isaac Lab backend 的构造器都会立即抛出 `BackendNotAvailableError`，且
  `pyproject.toml` 的两个 optional extra 为空；ADR-003 也将二者定义为 placeholder。
  因此 3.5G `objects.zip` 及两个外部源码目录不属于当前运行所需资产。
- 旧 `outputs/` 的代码路径都是显式输出目录或用户显式传入的 `--study-dir`，不是当前
  benchmark 的默认输入；故不复制它不会使迁移后的当前 runtime 缺资产。

## P3：历史输出需单独归档（不阻断）

旧 `outputs/`（约 13M）不仅含渲染和视频，也含
`human-pilot/*/annotations.sqlite3`、`study.json` 与 `participant-tokens.txt`。它们不在
本迁移所定义的当前运行输入路径中，故不要求随运行资产复制；但人类标注结果与访问令牌
不应被笼统视为可再生测试缓存。

建议在后续项目归档说明中把这些成果列为“有意未迁移的历史研究输出”，按需要以受控方式
另行归档（尤其不要把 participant tokens 混入普通共享资产）。另外，未复制的
`robotwin-source` 与 `kubric-source` 现有本地 checkout 分别显示 752 和 193 个删除记录；
若未来需要它们，应从已记录 origin/commit 重新 clone，而不要依赖这两个旧缓存目录。

## 验证范围与限制

- 已执行：Git object/remote/ancestor 核验、源 dirty/backup byte comparison、patch
  applicability、源/目标 checksum rsync、全量聚合 hash、资产树统计和静态运行资产路径
  解析。
- 未执行 ManiSkill simulation 或完整 CLI 数据校验：独立的一键环境任务仍在实施，且本机
  system `python3` 缺少 `numpy`。这正是本迁移不复制旧 venv 后应由环境任务解决的依赖，
  不是资产迁移失败；本 review 没有借用旧 venv 或改动环境来掩盖该边界。
