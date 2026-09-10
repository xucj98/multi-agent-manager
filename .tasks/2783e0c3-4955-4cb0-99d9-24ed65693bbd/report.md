# 交付简报：table-1000 仓库与运行资产迁移

## 完成项

- 以真实 `git clone` 建立 canonical repo：
  `/mnt/public/xcj/Projects/table-1000/table-1000`。
  `origin` 的 fetch/push 均为 `git@github.com:xucj98/table-1000.git`，canonical
  base 为 `3fa574ba2793ea44a5a69fecfd82f761a7c1bd4c`（`main` 和 `origin/main`）。
- 旧源 `/mnt/public/xcj/table-1000` 在盘点时为
  `184d6b195bd44956f7a536ddee73177a2bb4d1fa`，确认是 canonical base 的祖先。
  上游在 clone 前已推进，因此刻意采用新 origin HEAD，未把新 clone 回退到旧源。
- 环境任务已将共享运行资产收拢为 canonical 的实体目录
  `/mnt/public/xcj/Projects/table-1000/table-1000/.cache`，一级仅 `assets/` 和
  `maniskill/`；PROJECT_ROOT 的旧 `assets/` 已不存在。worktree 链接和可写 cache
  策略由环境任务维护，本迁移任务不竞争修改。
- 未复制旧 `.venv`（6.0G）或 `.venv.bak-mplib011`（6.0G）。本任务没有启动训练、数据生成或修改 tracked 项目文件；首次引入 canonical clone 按任务允许不建立本任务 worktree，也没有 delivery commit。

## 源工作区状态与保留

旧源保持未动，盘点时唯一的 Git 工作区改动是：

- `.gitignore` 增加 `.venv.bak-mplib011`；
- 未跟踪 `scripts/probe_scene/render_strip.py`。

两项均保存到 canonical 的私有本地记录目录
`/mnt/public/xcj/Projects/table-1000/table-1000/.local/migration-backup/2783e0c3-4955-4cb0-99d9-24ed65693bbd/`：

| 文件 | SHA-256 | 处理 |
| --- | --- | --- |
| `dirty-gitignore.patch` | `2251f0a42e0f4ad8e20a1d99f19def792329619813d41b4e78c07a88b548b21c` | `git apply --check` 已通过；仅在审阅后手动 `git apply --3way`，不会自动覆盖 canonical。 |
| `render_strip.py` | `dcd8024a1a0dee25346c472ad776a47d482a32684a9b21bc7d615cd916735e0b` | 与 canonical 上游已跟踪版本哈希一致，保留作证据，不复制回工作树。 |

完整恢复命令、源/目标、未复制项与风险写在同目录的 `MANIFEST.md`。

## 共享资产与完整性

旧源 `.cache` 指向 `/mnt/public/xcj/table1000-cache`。按当前运行代码的
`TABLE1000_ASSET_DIR`/`MS_ASSET_DIR` 路径，以下输入资产已在 canonical 实体
`.cache` 中可用：

| 目标一级目录 | 文件数 | 字节数 | 相对路径内容 aggregate SHA-256 |
| --- | ---: | ---: | --- |
| `assets/` | 3,280 | 1,816,375,429 | `25946fb209558c22937f1edf1574907be7f50475364b0a908e10df8bf0e05d2b` |
| `maniskill/` | 470 | 87,217,479 | `f792cfe42e9a35b5d593600134a1eced57ecd6774aee35d36586121487b8cd1f` |

`rsync -aHnci` 的复制后校验无输出，两个 aggregate hash 的源/目标值相同；目录内无软链接。最终路径复核确认 `.cache` 是目录、PROJECT_ROOT 没有 `assets/` 业务目录。共享目录应只读使用，worktree 如需可写 cache 应另设本地目录。

未复制 `robotwin-assets/`（3.5G，当前 `robotwin2` 是 placeholder）、`robotwin-source/`（91K）和 `kubric-source/`（20M，均为可重 clone 的未引用源码），以及测试缓存。Git 已带入 tracked 的场景和 catalog `data/`，无需重复复制。

## 受限历史 outputs 备份

旧 `outputs/` 是历史研究产物，包含人类研究标注，不能归类为可再生缓存。已完整备份到：

`/mnt/public/xcj/Projects/table-1000/table-1000/.local/migration-backup/2783e0c3-4955-4cb0-99d9-24ed65693bbd/historical-outputs/`

- 不加入共享资产，也不建立默认 worktree 链接；所有目录为 `0700`、所有普通文件为 `0600`。
- 备份为 56 个文件、13,266,644 bytes，sorted relative-path SHA-256 manifest aggregate 为 `9758b4462046bc86f9f2ef8b7285d723cf791f672a267e10a1687cb1bc0c10b6`。
- 复制前后均未发现打开 `outputs/` 的进程句柄，源树 aggregate 在备份窗口保持稳定。非 SQLite 内容通过 `rsync -rnc` 校验。
- 两份 SQLite 标注库使用 SQLite `backup()` API 从 immutable 只读源生成一致性副本；源和备份均通过 `PRAGMA integrity_check`，逻辑 dump digest 相等。最终源和备份均无 WAL/SHM sidecar。
- 可在选定恢复目的地后显式执行 `rsync -aH historical-outputs/ DESTINATION/`；完整绝对命令和分类说明在备份目录的 `MANIFEST.md`。

## 验证与后续风险

- `git fsck --no-dangling` 在 canonical clone 通过；origin URL、HEAD 与 `origin/main` 一致。
- environment agent 负责 `.local` 环境入口、独立 venv、canonical `.cache` 实体和 worktree 链接；本任务只在 `.local/migration-backup/` 保存私有迁移证据。PROJECT_ROOT 不保留 `migration-backup` 或 `assets` 业务目录。
- 当前资产覆盖 ManiSkill reference 路径；未来启用 RoboTwin/Kubric 后需要按其许可、provenance 与运行需求单独迁移/下载未复制缓存。

## 统一用户缓存迁移（最终完成）

用户授权的全局缓存实体为 `/mnt/public/xcj/cache`；最终
`/root/.cache` 是指向该目录的符号链接，新增的
`/mnt/public/xcj/cache/shared-python` 已保留。原 `/root/.cache` 是实体目录，
盘点为 1,867 个目录、3,140 个普通文件、62 个链接，普通文件共
5,130,120,620 bytes；sorted relative-path aggregate SHA-256 为
`51b55f04e0a07813d0a574e5874bf138b80f08636e6ae0375da53d7662627039`。
合并前，既有全局缓存已私有快照到 canonical 的：

`/mnt/public/xcj/Projects/table-1000/table-1000/.local/migration-backup/2783e0c3-4955-4cb0-99d9-24ed65693bbd/cache-conflicts/global-cache-pre-home-merge`

home/global 没有非 root 路径冲突；原 home 树在原子切换前完成两次完整内容校验。
APC 已退出（记录的 PID 不存在且 8770 无监听）后，再次确认无打开句柄，删除了
经校验的旧实体 `/root/.cache.pre-migration-2783e0c3`。最终复核确认 home 链接、
全局 cache 实体、`shared-python` 均仍正确。

canonical 临时 uv 源
`/mnt/public/xcj/Projects/table-1000/table-1000/.local/uv-cache` 的迁移前盘点为
32,387 个节点（3,139 目录、29,142 普通文件、106 链接；普通文件
6,207,456,020 bytes）。它已收拢到实体目录 `/mnt/public/xcj/cache/uv`，未执行
`uv cache clean/prune`，也未手工删除最终全局缓存中的包。

预检结果为 32,319 个 canonical source-only 节点、2,023 个 global target-only
节点、30 个相同共享节点和 38 个冲突节点。38 个冲突均为索引/元数据；
`archive-v0` payload 冲突和 lock 冲突均为 0，且没有依赖冲突的 source-only 相对链接。
裁决是保留既有 global target，使用 `rsync -aH --ignore-existing` 仅复制
source-only 节点，绝不覆盖 archive payload。

38 个冲突的两侧均已在私有迁移备份中保全：

| 一侧 | 位置（均位于 canonical migration-backup） | 普通文件 | 链接 | 普通文件 bytes |
| --- | --- | ---: | ---: | ---: |
| canonical source | `cache-conflicts/uv-conflicts/canonical-source` | 26 | 12 | 558,825 |
| 既有 global target | `cache-conflicts/uv-conflicts/global-target` | 26 | 12 | 556,801 |

两个归档根目录及其目录/普通文件权限已核对为 `0700`/`0600`。最终验证包括：两个旧源
均无打开句柄；uv 的 `--ignore-existing` 元数据检查没有遗漏 source-only 节点；排除
38 个已归档冲突根的 checksum dry-run 验证非冲突内容；38 个冲突归档根的内容哈希或
链接目标均分别与 canonical 源和最终 global target 相符。随后仅删除了 canonical
`.local/uv-cache` 旧实体；`/mnt/public/xcj/cache/uv` 已复核为实体目录。

历史 `outputs/` 私有备份未被本次缓存迁移改变，仍为 56 个普通文件、13,266,644 bytes、
aggregate SHA-256 `9758b4462046bc86f9f2ef8b7285d723cf791f672a267e10a1687cb1bc0c10b6`，
并保持 `0700`/`0600` 权限。环境拥有的 `.local/create_worktree.sh` 和
`.local/worktree-env.conf` 未由本任务修改；环境任务已收到可恢复 uv 安装的通知。

迁移记录未展示缓存内容、包路径、凭据或 token。完整证据见 canonical 的
`.local/migration-backup/2783e0c3-4955-4cb0-99d9-24ed65693bbd/MANIFEST.md`。

