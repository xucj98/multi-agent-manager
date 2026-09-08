# 四库本地 worktree 入口

## 目标与负责人

负责人：Lovelace（gpt-5.6-terra max）。为 RMBench、openpi、opendm、robot-bridge 提供本集群三参数创建入口。

本任务说明在实施过程中补建，包含截至目前 Manager 已下达的追加要求；后续要求先更新本文件，再通知执行。

## 工作区与修改范围

workspace：`/mnt/public/xcj/Projects/workspace/workflow-env-entry-20260908`，四库各使用其中自己的 worktree。
修改各库受 Git 管理的 worktree 脚本、对应环境说明，以及必要的 `.gitignore`。各原仓库 `.local/create_worktree.sh` 为本机私有交付，允许直接写入。AGENTS.md 由 Manager 编写，不在你的修改范围。

开始和收到更新时阅读本文件；进入各库前阅读其 AGENTS.md 与环境说明。四库各保留自己的完整创建、软链接与安装逻辑。

## 当前要求

- 私有入口只接收 `BASE_COMMIT NEW_BRANCH WORKSPACE_ROOT`，创建 `WORKSPACE_ROOT/<repo>`，固定本集群 uv、Python、cache、wheel、cuRobo 和稳定 source-root。
- 本机与 wuwen-1 共用入口；从 linked worktree 的 `.local` 调用也必须解析回稳定原仓库。
- `.local/create_worktree.sh` 不进 Git；四库 `.gitignore` 均保护 `.local`，尤其补齐 openpi。
- 通用脚本不再依赖 `.local/README.zh-CN.md`。旧说明在验证后删除；不删除已有 `review/`、`mem0-launch-inputs/` 等无关或活跃私有内容。
- 目标 base 选择对应的受版本管理安装逻辑；不支持的旧入口版本在创建前明确报错。保留通用脚本直接调用能力。
- 原有 GPU smoke（包括 RMBench 渲染和 cuRobo 检查、OpenDM GPU 检查）保留，是否运行由任务安排决定。创建入口不自动运行 GPU 或正式实验。
- 环境文档简洁，但保留每库共享目录清单，尤其 RMBench 整体 assets/data、Mem-0 checkpoint/数据，以及含 tracked 下载脚本时的处理方式。
- 环境创建不新增参数清单、依赖版本台账或 provenance 记录。
- 不迁移现有 eval 结果，不改模型代码、现用环境、缓存和编译产物，不切换 main。

## 验证与交付

先做 bash 语法、help/缺参、路径含空格、已有目录或分支拒绝、正确 source-root、旧 README 不存在时的检查。对未改变的重型依赖安装不重复全量验证；独立 reviewer 会用最终入口实际创建 robot-bridge 环境并做 CPU 检查。

提交各库改动，将完成情况、剩余问题、workspace、每库完整 commit、验证结果和私有入口位置写入本目录 `report.md`。测试临时文件和 smoke 由你自行处理；Manager 接收并归档时移除 workspace，报告及提交保留。
