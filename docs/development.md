# MAM 开发指南

本文只适用于修改 Multi-Agent Manager（MAM）代码。

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
mam workspace add TASK-ID --repo multi-agent-manager --base main
```

在该 worktree 中修改和提交。任务、报告和 review 的日常流程见 [README](../README.md#任务管理) 与 [执行与交付](../README.md#执行与交付)。

## 验证与合并

在 MAM 开发 worktree 中运行：

```bash
.venv/bin/python -B -m unittest discover -s tests -v
```

提交任务分支并发布 report 后，由独立 review 验收。Manager 将验收后的改动合入 `main`，再带入项目管理分支；安装与项目配置仍见[安装说明](install.md)。
