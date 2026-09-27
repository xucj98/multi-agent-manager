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

提交任务分支并发布 report 后，由 Manager 验收，必要时安排独立 review，并对其结论作出裁决。验收后的改动合入 `main`；实例升级另行安排，不随合并自动更新已安装版本或正在运行的服务。任务相关的一次性验证记录放 `PROJECT_ROOT/workspace/TASK-ID/tmp`；Manager 无关联任务的文件放 `PROJECT_ROOT/workspace/tmp` 并按工作分目录，阶段收尾清理。自动化测试内部自行创建并清理的临时目录不受此约定限制。

## 单实例固定版本试用

Manager 完成 review 和合并后，确定验收 commit `COMMIT`，在当前项目的 `PROJECT_ROOT/.mam/runtime/COMMIT` 创建非 editable 的独立安装。以下路径只服务该项目；不更改 pipx、系统 mam 或全局 shell 配置：

```bash
SOURCE_REPO=/absolute/path/to/mam-source  # 已合入验收 commit 的 MAM 源码仓库
RUNTIME="$PROJECT_ROOT/.mam/runtime"
mkdir -p "$RUNTIME/$COMMIT/src"
git -C "$SOURCE_REPO" archive "$COMMIT" | tar -xf - -C "$RUNTIME/$COMMIT/src"
python3 -m venv "$RUNTIME/$COMMIT/venv"
"$RUNTIME/$COMMIT/venv/bin/pip" install --no-deps "$RUNTIME/$COMMIT/src"
"$RUNTIME/$COMMIT/venv/bin/mam" --help
```

安装完成后先用该绝对路径在隔离测试实例验证。在修改 PATH 前记录当前命令的真实路径、原 PATH、`runtime/current` 目标和本实例服务状态。停止本实例服务，原子更新 `runtime/current` 指向 `COMMIT` 目录，再从项目根目录以新入口启动服务并检查 `mam service status`。需要验证 daemon 确实运行所选版本时，检查其 PID 命令行中的 Python 和包路径是否来自 `runtime/COMMIT/venv`。服务只处理当前 `.mam/env.json` 指定的实例。

```bash
OLD_MAM=$(readlink -f "$(command -v mam)")
OLD_PATH=$PATH
OLD_CURRENT=$(readlink "$RUNTIME/current" 2>/dev/null || true)
"$OLD_MAM" service stop
ln -sfn "$RUNTIME/$COMMIT" "$RUNTIME/.next"
mv -Tf "$RUNTIME/.next" "$RUNTIME/current"
export PATH="$RUNTIME/current/venv/bin:$PATH"
"$RUNTIME/current/venv/bin/mam" service start
"$RUNTIME/current/venv/bin/mam" service status
```

`PATH` 只影响设置它的 shell 及子进程；在同一 shell 切换到其他目录仍使用该版本。已运行的 agent 需在自己的 shell 前置同一路径，或使用新入口绝对路径。回退时用新入口停止本实例服务，将 `current` 指回事先记录的 `OLD_CURRENT`；首次试用若此前没有 `current`，则移除该链接。恢复 `PATH="$OLD_PATH"`，用固定的 `OLD_MAM` 绝对路径启动并检查服务。首次试用旧版本来自原 PATH，不能只切回 `current` 而留下新版本的 PATH 前缀。原有任务、job 和 workspace 保留。提交留存和归档仍按 [task](commands/task.md#附件与归档) 处理。
