# 2026-09-08 工作区生命周期实施

## 已确认范围

用户批准建立 agent-workflow；Manager 亲自编写本库 AGENTS、README 与四库 AGENTS。各库保留受版本管理的完整 worktree 脚本，`.local/create_worktree.sh` 为不进 Git 的本集群三参数入口。环境创建不新增 provenance 台账。

四库入口已集成：RMBench `6898ed3`、robot-bridge `24be5d2`、openpi `1f6a7c8`、OpenDM `46fb0f9`。文档链接检查通过，Manager 的临时 workspace 已清理，Git 提交引用保留。

## 分工

- Lovelace：四库 worktree 本地入口和环境文档；workspace `workflow-env-entry-20260908`。
- Ptolemy：轻量任务登记与回收工具；workspace `workflow-tool-20260908`。
- Manager：规范、集成、独立验收与回收；公共工具接口完成后补齐操作示例。

脚本完成后安排独立空白验收，复用已有测试手段，不启动 GPU。已有正式评测的源码、环境和结果不在本次修改范围；robot-bridge 结果迁移仍等待 900 rollout 完成。

## 文档空白验收

Chandrasekhar 首次只读审阅指出日志路径、任务编号、分支名称、原仓库位置和 checkpoint 核对范围五处歧义，Manager 亲自修正后复核通过。未创建验收环境或临时 workspace。

最终四库文档提交：RMBench `c0b2e37`、robot-bridge `c09e815`、openpi `be73ed2`、OpenDM `c4aa406`。Manager 文档 workspace 已回收。后续工作日志统一在本仓库，各库历史工作日志保留原位。
