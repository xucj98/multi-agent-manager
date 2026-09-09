task_revision: 329b650d618949779b0f5dfcb6b1fa07dc944d33

完成：openpi worktree `/mnt/public/xcj/Projects/workspace/f252006a-8676-4d10-b6a1-1a791d91c6a6/openpi` 的交付链为 `0dc120cf850e13a8fab71974f4f7e29778c13406`（最小 PyYAML lock 修复）、`f6327197459bf830c6b5d0b9ba5d643bc5e0cbd3`（精简 memory config API）和 `0f37cfc1ae42e4703b741f0f05fd1e3c58c87e89`（availability）。最后一个 commit 是独立 review 的最终代码对象；review task `d82c6b70-a8af-460e-92d1-d7e9ddc521ff` 已包含其增量核查要求。

client 仅修改 `packages/openpi-client`。实现从 de79 的 1,480 行收敛到 986 行，定向测试从 357 行到 334 行；当前总计 1,320 行。保留 `load_memory_config`、resolved metadata、sample/model-spec helper 和同一 field vocabulary/offset source，删除重复映射和不再需要的兼容入口。没有改 `src/openpi`、scripts、examples 或 robot-bridge。

最终数据接口为 `EpisodeMemoryData(series, constants={}, events={}, tail=None, availability={})`（实际为 default factory）。availability 仅接受 memory `reference.kind: series` 的 key 到 episode 等长 bool 数组；省略表示完整标注，缺 series key 仍报错。false 时训练输入用 field initial，目标 ID/mask/逐坐标权重/dense 编码全零；其他 memory 字段与 robot target/weight 保留。它与 `target.validity` 独立，未将 all_in_bounds 声称为多候选时刻的 annotation-availability 交集。

论文交付物位于 workspace 根目录 `paper-artifacts/`，未进入 openpi：`memory.schema.patch`、`p2_phase_per_frame.example.yaml`、`p2_phase_repeated_endpoint.example.yaml`、`README.md`。两个单 phase P2 比较组均为可单独 load 的英文 YAML，采用 current-reference input、H50/K30、shared public mask、fixed_horizon、同一 `robot_action` target 和 `chunk_completed/last_executed`；仅 phase target `offset/stride` 为 1/1 或 30/0。共享论文 schema 已由并行方更新为与 patch target 相同内容；reverse apply check 通过，执行者未修改共享论文 checkout。Manager 可据此保留或清理 artifacts。

验证：`python -m pytest -q packages/openpi-client/src/openpi_client/memory_config_test.py` 为 12 passed；Ruff check、Ruff format check、`git diff --check` 和 `uv lock --check --offline` 通过。两份 artifact YAML 用 Draft 7 校验通过，并由 client loader/sample helper 验证 H50/K30、公共边界 mask 与 target-only diff。未启动 GPU smoke 或正式训练。
