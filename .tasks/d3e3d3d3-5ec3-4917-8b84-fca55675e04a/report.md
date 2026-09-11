# 独立 review：准入 PASS

- 最终 bridge 候选：`f0f585a2b5974c60b51cac65277f94d1097591a3`，基于
  `3906dd0032637410359be6dd5006b3f793f3191c`；`f0f585a` 仅恢复
  `docs/tutorials/wash-cup-memory.md` 的 tmux 环境刷新说明。
- 审查 worktree：`/mnt/public/xcj/Projects/workspace/d3e3d3d3-5ec3-4917-8b84-fca55675e04a/robot-bridge`，已 fast-forward 至候选且干净。
- OpenPI 复核：源 task 的 OpenPI worktree 为干净的
  `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`；本候选没有 OpenPI 交付改动。

## 核对证据

- `robot_bridge/memory_config.py:1` 与固定 OpenPI
  `a869:packages/openpi-client/src/openpi_client/memory_config.py` 字节完全一致，二者 SHA-256 均为
  `6287bddad81cd635556ef6b0b75b3abd64248289d74f101e1fa3a07db176aa80`。
- `robot_bridge/scheduler/memory_context.py:19,113` 和
  `robot_bridge/robot/controllers/x2robot_offline.py:72,188` 均改为 bridge 本地模块；未发现
  runtime `openpi_client` import，旧 wheel 安装脚本与 wheel 测试已删除。
- 在 `PYTHONPATH` 清空、`openpi_client` 不可导入、`CUDA_VISIBLE_DEVICES=''` 的 bridge `.venv` 中，
  纯模块未加载 OpenPI/JAX/Torch/硬件 SDK。真实 full/serial metadata 均成功建 context：H50/K30，
  full 为 `(50, 1)` action rows，serial 为 `(1, 1)` query。
- CPU 定向回归：`130 passed, 1 skipped in 45.52s`，覆盖本地 schema、真实 metadata、scheduler、takeover、offline、launcher 与 TUI 脚本语法。
- 现场短流程见 `docs/tutorials/wash-cup-memory.md:15-50`：checkout 后加载 RB 配置、既有 tmux
  变量刷新、`push_code.sh auto`、TUI、`:8088` 检查；无手工 wheel/OpenPI 安装要求，GUI 可常驻。

默认 Ruff 对逐字复制的上游模块报现代化/导入排序建议；另有 3 个 E501 位于候选未改的
`policy/backends/openpi.py` 基线行。为保持用户要求的两份模块一致，未格式化该文件；这不影响
本次运行时或部署准入。

## 结论

**准入部署 `f0f585a2b5974c60b51cac65277f94d1097591a3`。** 本 review 仅做本地 CPU 验证；真机动作、远端部署和 GPU 推理未执行。测试缓存与临时文件已清理，保留 worktree 供验收归档。
