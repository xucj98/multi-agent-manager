# MAM 开发指南

本文面向 MAM 代码和文档开发者。

## 准备开发项目

开发项目名称为 `mam-dev`，`MAM_BRANCH` 设置成 `project/mam-dev`，项目的目录结构如下：

```text
mam-dev/                      # `PROJECT_ROOT`
  multi-agent-manager/        # `MAM_ROOT`，保存任务、报告和实例状态，使用 `MAM_BRANCH`
  mam-dev/                    # 开发库，代码与长期文档在这里开发，交付合入 `main`
  workspace/TASK-ID/mam-dev/  # subagent 的任务 worktree，使用独立的 `task/TASK-ID` 分支和 `.venv`
```

先按[安装指南](install.md)配置 `mam-dev` 项目实例：`PROJECT_ROOT` 为该项目目录，`MAM_ROOT` 为其中的 `multi-agent-manager`，`MAM_BRANCH` 为 `project/mam-dev`。

然后单独 clone 开发库，目录名为 `mam-dev`，使用 `main` 分支：

```bash
project=/absolute/path/to/mam-dev
git clone git@github.com:xucj98/multi-agent-manager.git "$project/mam-dev"
cd "$project/mam-dev"
git switch main
python3 -m venv .venv
.venv/bin/python -m pip install --no-deps --editable .
```

按[项目 hooks](install.md#项目-hooks)为开发库配置 `workspace_add`：将 repo 模板放到 `mam-dev/.local/hooks/workspace_add`，将 `scripts/local_create_worktree.sh` 复制为 `mam-dev/.local/create_worktree.sh`，并将其中的 `python` 设置为本机 Python >=3.10 的绝对路径。项目入口调用该 repo hook，为每个 worktree 创建独立环境。

## 日常开发与单元测试

代码任务从开发库创建 worktree：

```text
mam workspace add TASK-ID --repo mam-dev --base main
```

管理任务使用本实例约定的命令入口，见 `MAM_ROOT/.local/README.md`。测试被修改的 MAM 时，使用 worktree 的 `.venv/bin/mam`。在该 worktree 中运行日常测试：

```bash
.venv/bin/python -B -m unittest discover -s tests -v
```

测试自行创建临时仓库和数据，使用模拟 Codex 接口，覆盖命令、状态处理和迁移用例。每次代码修改后运行相关测试，交付前运行完整测试集。

提交代码、发布 report 后，由 Manager 验收并裁决 review 意见。Subagent 负责合入准备，包括必要的 `main` 同步、冲突处理和验证，使 Manager 可直接合入；同步时机和验证范围按改动影响确定。验收采用的代码由 Manager 合入开发库的 `main`。

Manager 编写规划和核心文档可直接修改该库。通用交付流程见 [README](../README.md#执行与交付)，本项目的成果留存与归档要求见[项目说明](../.local/README.md#本项目收尾规则)。

## 发版集成测试

发版前用候选发布包实际执行首次安装和旧版升级，在任务 worktree 中调用以下脚本。

### 一键创建与测试

只创建指定版本的测试实例，供检查或调试：

```bash
.venv/bin/python scripts/create_mam_test.py --version 0.1.0 --root ../tmp/mam-test
```

`--version` 指定数据所属的版本，`--root` 指定新实例的 `PROJECT_ROOT`。脚本准备对应版本的程序环境、配置、Git 仓库和静态测试数据，输出实例位置、版本及 `mam` 的绝对路径；实例保留供后续操作，daemon 与运行中的 job 由调用方启动。

一键执行完整集成测试，自动调用创建脚本准备实例：

```bash
.venv/bin/python scripts/test_integration.py --root ../tmp
```

默认从当前 checkout 构建候选发布包，覆盖首次安装、上一版本升级及从 0.1.0 开始的完整迁移链。`--from VERSION` 可指定起始版本，`--to VERSION` 可指定已发布的目标版本，例如：

```bash
.venv/bin/python scripts/test_integration.py --from 0.1.0 --to 0.2.0 --root ../tmp
```

创建脚本使用新目录；已有实例保留并报错。完整测试成功时退出码为 `0`，失败时为非 `0`，输出场景结果与日志位置。测试只清理本次创建的资源。

### 目录与程序环境

测试实例命名为 `mam-test`，放在关联任务的 `workspace/TASK-ID/tmp/mam-test`：

```text
workspace/TASK-ID/
  mam-dev/.venv/bin/mam         # 当前开发代码
  tmp/
    mam-test/
      .mam/env.json             # 测试实例配置
      multi-agent-manager/      # 测试实例的 MAM_ROOT
      workspace/                # 测试任务的 workspace
    mam-test-2/                 # 多实例场景
    mam-test-install/           # 发版测试专用的 pipx 安装目录与命令入口
```

实例配置与程序安装分开。测试当前代码时可以复用 worktree 的 `.venv`；配置好 `mam-test` 后，从它的目录调用被测程序：

```bash
task_root=/absolute/path/to/PROJECT_ROOT/workspace/TASK-ID
cd "$task_root/tmp/mam-test" && \
  "$task_root/mam-dev/.venv/bin/mam" service status
```

MAM 从当前目录向上查找 `.mam/env.json`，因此这里使用 `mam-test` 的数据。发版的安装与升级场景使用 `mam-test-install` 中的独立 pipx 环境，先安装旧版，再通过 `install.sh` 更新为候选版；多个测试实例共用这份安装。

### 各版本的测试数据

公共创建脚本负责准备目录和版本环境，再调用 `tests/fixtures/VERSION/create.py`。每个版本的生成脚本在对应版本的环境中运行，使用该版本的接口生成配置、hooks、数据库和任务文件，并返回创建的记录标识供测试核对。

已发布版本的程序引用与生成脚本保留在测试基线中；候选版由集成测试入口提供本地发布包。数据结构未变化时可复用生成逻辑，但仍使用指定版本的程序写入数据。0.1.0 的生成脚本以已确认的旧版基线补齐。

### 测试资源与场景

测试入口自动准备以下资源：

| 测试资源 | 准备内容 |
| --- | --- |
| 程序安装 | 固定的旧版程序、候选发布包和 `mam-test-install`；通过测试入口使用候选包运行 `install.sh` |
| 测试实例 | `mam-test`、`mam-test-2` 两个旧版实例，各自有 `.mam/env.json`、`MAM_ROOT`、`MAM_BRANCH`、hooks 和 daemon；另建空实例测试首次使用 |
| 旧版数据 | 用旧版程序生成合成数据，包含 task、job、workspace、Manager、未投递消息和投递记录；首个基线固定为 0.1.0 |
| Git 与文件 | 临时仓库和 worktree，以及已发布的 task、report、附件和未提交草稿 |
| 运行进程 | 登记两个受控测试程序为 job：一个贯穿升级持续运行，另一个在 daemon 停机期间退出 |
| Codex | 迁移场景使用可控的模拟接口；当前 Codex 的真实兼容性与投递测试使用专门的测试会话 |

完整测试自动完成：创建旧版实例、启动测试 daemon 和 job、保存初始记录、停止 daemon、运行候选版本的 `install.sh`、逐实例执行 `mam service upgrade`、启动新版 daemon 并验收。

验收核对数据版本、`MAM_BRANCH`、任务文件与草稿，验证持续运行的 job 仍受跟踪、停机期间退出的 job 产生通知，以及原有消息与投递记录得到保留。

还需覆盖重复升级、中断后重试、Git 冲突和 `.local/` 备份恢复。每个场景输出通过或失败及对应原因。

测试结束后停止测试 daemon、程序和会话，清理本次创建的实例、安装目录及中间文件。结果报告与诊断日志保留供验收，必要材料按 [文件留存原则](../README.md#文件留存原则) 随任务 report 保存。

`install.sh` 在用户安装时运行日常自动化测试和当前 Codex 的兼容性验收；完整的旧版升级集成测试在发版前完成。

## 文档维护

只保留读者需要的操作和约束，讨论经过留在任务报告中：

- `README.md`、`AGENTS.md` 面向日常使用；`install.md` 面向安装配置；本页面向开发。
- 已有明确名称的对象直接使用原名，如 `MAM_BRANCH`、`install.sh`；中文用于解释用途。
- roadmap 只列任务和要做什么。
- `docs/designs/` 帮助使用者深入理解 MAM 的行为和设计思考，也帮助开发者在不阅读源码的情况下了解系统整体。内容包括接口用法和设计说明，保持通俗简洁，不涉及具体实现细节。
- 环境专属说明写入项目 `.local/README.md`，公共文档适用于各部署环境。

## 版本与发版

每个正式版本提供以下内容：

| 内容 | 要求 |
| --- | --- |
| 版本信息 | 唯一版本号、对应 Git tag 和上一版本；命令显示版本，开发构建附 commit |
| 源码发布包 | 包含程序、`install.sh`、hooks 模板、迁移脚本和测试；内容与对应 Git tag 一致 |
| 版本说明 | `CHANGELOG.md` 中该版本的条目，说明新增功能、修复和兼容性变化 |
| 升级适配说明 | `docs/upgrades/VERSION.md`，说明从上一版本升级时的配置变化与默认值、hooks 和项目文件的适配操作及验证方法；没有额外适配时明确写明 |
| 数据迁移脚本 | 从上一版本迁移到本版本；无变化时为空操作。完整保留自 0.1.0 起的历次迁移脚本 |
| 测试数据生成脚本 | `tests/fixtures/VERSION/create.py`，用于一键创建该版本的 `mam-test` 实例 |
| 测试与验收记录 | 本版单元测试、集成测试用例及结果；记录测试版本、升级路径和实际验证的 Codex 版本，结果随发版任务 report 留存 |

版本说明回答“本版改了什么”，升级适配说明回答“项目需要做什么”。跨多个版本升级时，按顺序阅读各版适配说明；项目 hooks 仍由各项目负责调整。

实例的数据版本与 service 状态结构版本分别记录。迁移规则见 [mam service upgrade](designs/service.md#实例升级)，操作流程见[安装说明](install.md#更新)。保留固定的 0.1.0 程序与生成脚本作为首个测试基线。

日常测试和[发版集成测试](#发版集成测试)通过后发布。安装阶段的测试与结果说明见 [install.sh](designs/install.md#安装与测试)。

## 单实例固定版本试用

集成验收通过后，将已合入 `main` 的确定版本部署到 `mam-dev` 实例试用，使用独立的 pipx 环境和 `mam-dev` 入口。该实例的安装、升级命令和当前版本记录在 `MAM_ROOT/.local/README.md`，Manager 与 subagent 使用同一入口。
