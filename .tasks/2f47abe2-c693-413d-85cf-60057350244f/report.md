task_revision: 0257a1ffa92d8bdbbbd0d6181023a3f963377293

# 四库本地环境入口独立验收简报（草稿）

状态：环境入口代码与实际构建验收通过；已发现的文档引用问题待 Manager 收尾。

本次更新由 Manager 根据 Popper 最终回复及其已执行命令代录；执行者自己的 report.md 写入被 bwrap 挂载故障阻断。

workspace：`/mnt/public/xcj/Projects/workspace/2f47abe2-c693-413d-85cf-60057350244f`（其下 robot-bridge 已实际创建）。

## 审阅的作者交付

| 仓库 | 最终提交 |
| --- | --- |
| RMBench | `75486ee277b991a83c3e43f13e68bbf453f6d1d5` |
| OpenDM | `9f46ce78f972e53980a2eeb6efee9e0aaa58a812` |
| openpi | `831afd54a4b10aa911068898617de8fa380ae09e` |
| robot-bridge | `9c5056f1d6dfd155a111db6c28ea5cff469348df` |

## 已验证

- 四条提交链均从任务指定的原始 base 线性演进，作者 worktree 均 clean；`git diff --check` 通过。
- 四个稳定源的 `.local/create_worktree.sh` 均为可执行普通文件，并被对应 `.gitignore` 覆盖；openpi 的最终提交已补齐根 `.local` 忽略规则。
- wrapper 与最终受管脚本均通过 Bash 语法检查。四个 wrapper 对旧 base 均在创建 worktree 前以状态码 2 报出 `BASE_COMMIT predates the .local/create_worktree.sh contract`。
- 受管脚本改为要求可执行的 `.local/create_worktree.sh`，不再引用 `LOCAL_README`；稳定 `--source-root` 由 wrapper 显式传入。共享软链列表的实现未被本轮改动改写。
- RMBench 的 SAPIEN 渲染/cuRobo GPU smoke 与 OpenDM 的 CUDA smoke 均已恢复；本验收尚未使用 GPU。

## 待修正的缺陷

1. RMBench `75486ee277b991a83c3e43f13e68bbf453f6d1d5:docs/guidelines/rmbench.md:44` 仍把机器私有入口指定为 `.local/README.zh-CN.md`。最终稳定源已经没有该文件，且当前入口要求 `.local/create_worktree.sh`，会把使用者引向已删除的旧 gate。应更新该项目规范后再完成文档验收。
2. robot-bridge 最终树仍有活跃设计/教程引用已删除的 `.local/README.zh-CN.md`，包括 `configs/benchmark/unified_sim/README.zh-CN.md:11`、`docs/design/unified-sim-real-runtime.md:59,182`、`docs/tutorials/drawer-offline.zh-CN.md:39` 与 `docs/tutorials/rmbench-benchmark-runner.zh-CN.md:5`。历史 `.worklogs/` 记录不在本问题范围；其余当前文档应改为现行 `.local/create_worktree.sh` 约定或不再指向不存在的文件。

## 实际构建验收

- 固定 base：`c4848e1bab4083ad6944ce641ef72c1287451439`；worktree 分支 `task/2f47abe2-c693-413d-85cf-60057350244f`。
- 三参数本地入口创建成功，安装 74 个包，uv pip check 通过。
- .local、logs、eval_result 均正确链接稳定原仓库实体，editable robot_bridge 来自自己的 worktree。
- 本机和 wuwen-1 均在同一共享路径执行 `.venv/bin/python scripts/worktree_env_smoke.py`，退出码均为 0。
- 未使用 GPU、未启动业务服务或修改现用环境。

## 后续事项

- Manager 修正上述旧文档引用。
- CLI 就绪后另由空白执行者完成多库创建与归档。
- 当前 worktree 保留供新工具登记与归档；测试临时文件由执行者处理。
