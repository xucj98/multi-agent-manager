# MAM 开发指南

本文适用于 Multi-Agent Manager（MAM）开发，包括修改代码和文档。

# 文档修改原则

修改文档时，应该明确阅读对象和使用场景，并尽量保持简洁，只提供必要的信息。
1. AGENTS.md, README.md 是给 manager 和 subagent 日常使用的高频入口。
2. install.md 用于首次使用需要安装 mam 的场景，不应该包含如何开发 mam 的内容。 `.local/create_worktree.sh` 是用作开发的，使用者不需要准备。
3. development.md 是给 mam 的开发者用的。
4. 上述几个文档都随 MAM 上传 git，MAM 可以被部署到各个集群，因此其中不应该有本地环境特定的说明。本地环境说明保留在 `.local/README.md` 中不上传 git。
5. roadmap 只列后续任务和要做什么。接口说明按顶层命令拆分，只写用途、参数、返回内容和使用约束；内部实现和测试过程留在代码与测试中。

## Python 与 editable 安装

首次开发 MAM 需要先准备 `.local/create_worktree.sh` 并验证可用性，已有 `.local/create_worktree.sh` 可跳过此条。MAM 的 `pyproject.toml` 要求 Python >=3.10，应选择可用的解释器；`scripts/local_create_worktree.sh` 只是没有站点默认值的复制模板。

创建 MAM worktree 时，入口会建立 `.venv`，并执行：

```text
pip install --no-deps --editable WORKTREE
```

MAM 使用 `flit_core` 作为 PEP 517 构建后端，因此首次安装需要配置的包索引或预置缓存提供该构建后端；`--no-deps` 只跳过运行时依赖，不跳过构建后端解析。

## 开发 worktree

先从 github 同步 MAM 的 `main`，再为代码任务从该分支创建独立 worktree：

```text
mam workspace add TASK-ID --repo mam-dev --base main
```

执行者在该 worktree 中修改和提交；任务交接时沿用原目录、分支和环境。Manager 编写规划及核心文档时可直接修改主 checkout，无需为自己的工作创建 task 或 worktree。任务、报告和 review 的日常流程见 [README](../README.md#任务管理) 与 [执行与交付](../README.md#执行与交付)。

## 验证与合并

开发和 review 使用各自 worktree 的 `.venv/bin/mam`，不修改系统 pipx 安装或全局 `mam` 入口。自动化测试使用临时仓库和模拟的 Codex 接口；手工验收另建 PROJECT_ROOT、MAM_ROOT 和 `.mam/env.json`，通过测试版本的绝对路径执行命令。测试服务只处理测试实例，不能接管或停止其他实例的服务。

在 MAM 开发 worktree 中运行：

```bash
.venv/bin/python -B -m unittest discover -s tests -v
```

提交任务分支并发布 report 后，由 Manager 验收，必要时安排独立 review，并对其结论作出裁决。验收后的改动合入 `main`；生产实例升级另行安排，不随合并自动更新已安装版本或正在运行的服务。归档前确认交付已合入 `main` 或明确可以舍弃，必要报告和附件已留存；安装与项目配置仍见[安装说明](install.md)。
