# 项目迁移执行简报

本执行阶段已完成四个业务仓库的物理搬迁和新 MAM 实例配置；独立空白 agent 验收及最终 `.tasks` 同步仍待 manager 收尾。

## 已完成

- 同一 `/mnt/public` 挂载点内使用目录级 rename，将 `RMBench`、`openpi`、`robot-bridge`、`opendm` 移至 `/mnt/public/xcj/Projects/state-vla/`。原顶层仅保留旧 `.mam`、旧 `multi-agent-manager`、旧 `workspace` 和新 `state-vla`，未删除其他内容。
- 所有业务仓库的 `.git`、本地分支、未推送对象、ignored 数据/模型/评测产物与用户未跟踪文件随目录保留。迁后核对的 local branch / local-only commit 数依次为 RMBench `61/225`、openpi `27/94`、robot-bridge `58/35`、opendm `14/32`；robot-bridge 的 `docs/design/low-dimensional-memory-design-space.zh-CN.md` 仍未跟踪。
- 从旧 MAM 的 `project/state-vla@565ec1a` 用 `git clone --no-local` 创建 `/mnt/public/xcj/Projects/state-vla/multi-agent-manager`，恢复原 GitHub `origin`，确认新旧 `.git` common dir 不同且无 `objects/info/alternates`。新 branch 保留原提交链，并以 `5524856` 提交将全部受跟踪非 `.tasks` 文件树对齐 `origin/main@ec047d3`；`.tasks` 树保持 clone 时内容。
- 创建新项目 `/mnt/public/xcj/Projects/state-vla/.mam/env.json`，其 `PROJECT_ROOT`、`MAM_ROOT` 均指向新实例，`MAM_BRANCH=project/state-vla`。新 `.local` 只包含 `README.md`、`create_worktree.sh`、`wuwen-11.md`、`wuwen-4090.md`；未复制旧 service/tasks/waits/archive/session。两份远端说明只更新了明确回传当前 A 项目根的路径，保留远端集群路径与 C 的兼容路径。未跟踪 `.tasks/838bfe79-ab08-4c58-9843-f8e84423f0e1/report.md` 已保留到新 clone。
- 修复 RMBench、OpenDM、robot-bridge ignored `.venv` 的启动器、激活脚本、`pyvenv.cfg`、editable `.pth` 和必要 Python 链接中的迁移路径。未修改历史文档或做全局路径替换。

## 验证

- 四个迁后仓库的 `git rev-parse`、`git status` 与 primary worktree 均正常；RMBench、OpenDM、robot-bridge 的 CPU import 分别通过 simulator imports、`opendm` editable import、`robot_bridge` editable import。
- 四个 `.local/create_worktree.sh` 均通过 `bash -n` 和 `--help` 入口检查；实际 `mam workspace add` 留给独立空白 agent 验收。
- 从新项目根读取 `mam task show` 成功；新 service 状态为 `disabled`、无 Manager/job/runtime。旧 MAM service 仍为 `healthy`，未停止或改写；OpenDM 编辑器/terminal 未终止，cwd 已解析到新目录。

## 待收尾

- manager 安排独立空白 agent 对新实例执行实际 `mam workspace add` 验收。
- 本报告发布后，最终验收/归档阶段仅把旧实例新产生的本任务 `.tasks` 内容同步到新 `project/state-vla`，不得回带旧代码树或 runtime/session。
- RMBench 的既有未映射 submodule 状态及 openpi 的未初始化 submodule 保持原状，未做远端或子模块初始化操作。
