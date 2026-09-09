task_revision: 36369a501cb897ffb94493d6ab37825664d6f89b

完成与未完成：

- 已在 manager 正式解除 eval 依赖后，移除 25 个已注册旧 Git worktree，并删除 8 个任务指定旧目录：
  - `workspace/bridge-mem0-remaining-execution-20260908`
  - `workspace/bridge-remaining-evals-20260908`
  - `workspace/bridge-runtime-integration-20260908`
  - `workspace/mem0-official-eval-turing-01a07a23`
  - `workspace/mem0-single-training-final-eval-prep-20260908`
  - `workspace/workspace-handoff-audit-20260908-0845`
  - `RMBench-sync-upstream-mem0`
  - `mem0-swap-blocks-single-20260907`
- 其中 21 个 worktree 用普通 `git worktree remove` 移除。4 个精确 `--force` 目标为旧 `RMBench-sync-upstream-mem0`、`fa2-eval/RMBench`（仅 `_tmp_visual`），以及经理已确认被主库覆盖的 `bridge-runtime-integration` 的 `RMBench-mem0`、`openpi`。
- 已删除 `/mnt/public/xcj/Projects/curobo-0.7.8.tar.gz`。删除前 `tar -tzf` 成功；逻辑大小为 58,897,152 B，`st_blocks` 对应 58,900,480 B。主 `RMBench/.venv` 的 editable `.pth` 仍指向 `RMBench/envs/curobo/src`，源码树未动。
- 已同文件系统 rename 到主 `RMBench` 持久路径，并使主路径成为实体目录：`Qwen3-VL-2B-Instruct`（4,266,683,392 B）、`m1_mix`（30,610,686,464 B）、`mem0_swap_blocks_single_20260907`（45,939,858,432 B）、`lerobot_datasets`（170,791,936 B）、`assets`（20,480 B）。旧路径在删除前改为兼容软链，保证冻结 workspace 与历史命令解析；rename 本身不宣称释放空间。
- 交接审计目录仅保全历史源码 patch、未跟踪源码和 base/ref 索引。归档为 `/mnt/public/xcj/Projects/multi-agent-manager/.local/archives/3b1cdd78-c7b9-4174-a132-497b485fcfaf/legacy-source-patches.tar.gz`，SHA-256 `c99c21bd7c38361212b0975e1705b6f2efeb09a45f40d872d5c1416ca10466e4`。归档含 583 条目、26 组 `tracked.patch`/未跟踪源码/`HEAD-and-refs.txt`，并保留原 26 份 `SHA256SUMS` 作为来源哈希映射；旁路索引为同目录 `legacy-source-patches.index.md`。旧审计日志未保留。
- 所有旧 worktree HEAD 原本已有命名 ref 或 archive ref。额外创建四个最小保护 tag 后才删除其唯一临时分支：
  - RMBench `archive/legacy-worktree-cleanup-20260909/rmbench-bridge-runtime-integration-20260908` → `0fe76da8c632`
  - RMBench `archive/legacy-worktree-cleanup-20260909/rmbench-mem0-single-training-final-eval-prep-20260908-fa2-eval` → `7799400078f8`
  - OpenDM `archive/legacy-worktree-cleanup-20260909/opendm-bridge-runtime-integration-20260908` → `0d6ddb9de4cd`
  - robot-bridge `archive/legacy-worktree-cleanup-20260909/robot-bridge-bridge-runtime-integration-20260908` → `efabbb6378ce`
  随后仅删除 13 个与旧 worktree 一一对应的 `codex/*` 临时分支；未改 `xcj-dev`、`main`、已有 archive refs、主 checkout 或结果任务分支。
- 未完成项：无。按 MAM 要求，本任务 workspace 留待 manager 归档；结果任务 `65c5f4dc-5ee6-4125-ac56-43e5db00c495` workspace 已由 manager 归档。Projects 顶层新出现的 `eval_result/` 与 `eval_result.tar` 不在本任务范围内，已验证仍存在且未触碰。

workspace、各库交付 commit：

- 本任务 workspace：`/mnt/public/xcj/Projects/workspace/3b1cdd78-c7b9-4174-a132-497b485fcfaf`（无业务代码 worktree）。
- 本任务没有新业务代码 commit；交付为上述精确清理、持久模型路径、保护 tag 与本 report。最终主 checkout HEAD：RMBench `681a928e266818bb430674c547b6458793bda227`、OpenDM `5a4ee39d7416565f7d59004558460bc7219850d7`、openpi `71c80db723a242c61cfe429dd6794e9ece3cbcf1`、robot-bridge `b17f6c53ffbc1030972a9820cf592f28b937d501`。

验证结果与成果位置：

- manager 确认结果任务最终只保留 RMBench 三组 `5 + 9 + 1` run，robot-bridge `eval_result` 已不存在；本地与 `wuwen-1` 对 7 个旧根路径的 cwd/fd 预检均为零匹配。
- 最终 `git worktree list` 仅保留四个主 checkout；8 个指定旧目录、13 个原计划临时分支和 cuRobo tar 均再次验证为 absent。
- `RMBench/.venv/bin/python` 可实际导入 cuRobo，解析到 `RMBench/envs/curobo/src/curobo/__init__.py`（`0.0.0`）；tar 删除后 editable source 仍独立可用。五个持久模型/数据目录与 patch archive SHA-256 也已复核。
- 删除前按各旧目录单独 `du` 的分配空间合计为 109,314,982,400 B。该值不能当作物理释放量：Git worktree、环境和缓存之间可能共享 hardlink，跨目录相加会重复计数（例如单独统计的 mem0-single 为 29,498,912,256 B，而跨根去重快照为 7,232,937,472 B）。唯一有精确逻辑与 block 记录的单文件回收是上述 cuRobo tar；模型迁移是 rename 而非删除。
- `robot-bridge/docs/design/low-dimensional-memory-design-space.zh-CN.md` 仍是主 checkout 的用户未跟踪设计文档；未修改。
