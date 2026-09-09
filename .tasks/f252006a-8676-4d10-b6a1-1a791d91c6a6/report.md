task_revision: 18a99cbea563d961481f6f75fb0c03feef0b4e86

进行中。紧急环境解阻的独立 openpi commit：`0dc120c69f4b5cce7c0d6a10bd0e92412870fc0e`（`fix: lock openpi-client PyYAML dependency`）。

该 commit 只改根 `uv.lock` 两行：在 workspace package `openpi-client` 的 dependencies 与 requires-dist 中声明既有锁定的 `pyyaml>=6.0`；未变更来源、版本、解析结果或其他包。验证：`uv lock --check --offline` 通过（仅现有 deprecated dev-dependencies warning）。

Memory client 精简、定向测试与 paper schema patch/P2 英文示例仍在本任务 worktree 中，尚未提交；不会混入上述依赖修复 commit。
