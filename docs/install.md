# 安装与更新

依赖 bash、curl、Python >=3.10、git 和 pipx。

MAM 支持一台机器上同时存在多个 MAM 实例，每个实例对应一个 `PROJECT_ROOT`，有自己独立的 service。

## 首次使用

### 安装

```bash
curl -fsSL "https://raw.githubusercontent.com/xucj98/multi-agent-manager/main/scripts/install.sh" | bash
```

### 配置实例

`.mam/env.json` 的配置项如下：

| 配置项 | 必填 / 默认值 | 用途 |
| --- | --- | --- |
| `MAM_ROOT` | 必填 | 保存任务文件与实例状态的 worktree 绝对路径 |
| `PROJECT_ROOT` | 必填 | 包含各仓库和 workspace 的目录绝对路径 |
| `MAM_BRANCH` | 必填 | `MAM_ROOT` 中用于发布任务文件的已有本地分支 |
| `HOOK_TIMEOUTS.workspace_add` | 可选 / 1800 秒 | 创建 workspace 的 hook 时限 |
| `HOOK_TIMEOUTS.before_task_archive` | 可选 / 60 秒 | 归档前检查的 hook 时限 |

```bash
project=/absolute/path/to/PROJECT_ROOT
mam_branch=project/PROJECT_NAME

git clone --branch "v$(mam --version)" git@github.com:xucj98/multi-agent-manager.git "$project/multi-agent-manager"
cd "$project/multi-agent-manager"
git switch -c "$mam_branch"
mkdir -p "$project/.mam"

cat > "$project/.mam/env.json" <<JSON
{
  "MAM_ROOT": "$project/multi-agent-manager",
  "PROJECT_ROOT": "$project",
  "MAM_BRANCH": "$mam_branch",
  "HOOK_TIMEOUTS": {
    "workspace_add": 1800,
    "before_task_archive": 60
  }
}
JSON
```

### 准备 hooks

根据 [项目 hooks](#项目-hooks) 进行配置。

### 启动 service

```bash
cd "$project"
mam service start
mam service status
```

## 更新

操作者确认所有使用 MAM 的实例，安排 agent 暂停工作、停止 service。维护期间暂停 MAM 调用及 `MAM_ROOT` 文件编辑。task 和 job 可以保留，长进程继续运行。

升级按以下顺序进行：

1. 逐实例执行 `mam service stop`。
2. `curl -fsSL "https://raw.githubusercontent.com/xucj98/multi-agent-manager/main/scripts/install.sh" | bash` 更新 MAM。
3. 进入各实例的 `PROJECT_ROOT`，分别运行 `mam service upgrade`。
4. 各个实例按 `docs/upgrades/VERSION.md` 适配、验证配置及 hooks。
5. 各个实例运行 `mam service start` 和 `mam service status` 启动 service 并确认。

详细说明见 [install.sh](designs/install.md) 和 [mam service upgrade](designs/service.md#实例升级)。

## 升级 Codex 后检查

无需重装 MAM，单独运行：

```bash
mam-codex-check --output mam-compatibility.json
```

检查当前 Codex 接口及真实 MAM 消息投递，使用两个隔离的 `gpt-6-sol/high` 会话，结束后清理。退出码 `0` 表示通过；JSON 保存诊断、耗时和 token 用量。该命令不修改现有 MAM 实例。

## 项目 hooks

hooks 由项目维护，规则写在 `.local/README.md` 或各仓库的 README.md、AGENTS.md。MAM 调用项目入口，由它决定如何调用 repo hook。

```text
MAM_ROOT/.local/hooks/          # 项目入口
PROJECT_ROOT/REPO/.local/hooks/ # repo 入口
```

入口为带 shebang、可执行且非软链接的普通文件。MAM 以 `MAM_ROOT` 为 cwd 调用项目入口，通过 stdin 传入 JSON。

| 项目入口 | 时机与职责 | 缺失时 |
| --- | --- | --- |
| `workspace_add` | 登记创建后执行，创建 worktree、环境和共享软链接；MAM 核对仓库、路径和分支。 | 拒绝创建 |
| `before_task_archive` | 全部 job 已归档、`MAM_ROOT/.tasks/TASK-ID/` Git 干净后，删除资源前检查项目收尾条件。 | 直接继续归档 |

ready worktree 的重复 `mam workspace add` 直接复用；创建失败修复后以相同 base 重试。`before_task_archive` 只检查、可重复执行，成果整理在调用前完成。

### 输入与返回

两个入口共用以下 JSON 结构，路径均为绝对路径：

| 字段 | 内容 |
| --- | --- |
| `schema_version`、`event` | 协议版本 `1`；事件为入口名称 |
| `project_root`、`mam_root` | 当前实例的根目录 |
| `task` | `id`、`title`、`status`、`workspace`、`task_dir`（`MAM_ROOT/.tasks/TASK-ID/`） |
| `repos` | 登记仓库数组：`name`、`source`、`path`、`branch`、`base`、`state`、`removed`、`branch_removed`、交付 `commit`；无交付时 commit 为 null |
| `repo` | 创建时为本次仓库名；归档时为 null |
| `jobs` | 已保存的 job 摘要；不隐式探测进程 |
| `options` | 本次 `note` 与 `force`；创建时为 null 和 false。force 表示是否强制删除 worktree 和 `task/TASK-ID` 分支，不能绕过 hook。 |

退出码 0 表示通过；非 0、启动失败或超时会报错，输出用于诊断。`before_task_archive` 拒绝时保留资源；创建失败可能留下部分 worktree。hook 应同步完成，不启动脱离进程组的进程或调用修改 MAM 状态的命令。超时见 [.mam/env.json](#配置实例)。

### 部署模板

从 [templates/hooks](../templates/hooks/) 复制需要的入口到对应 `.local/hooks/`，赋予执行权限并补充项目规则。`project/` 下的模板向 repo 转发上下文，以源仓库为 cwd；`project/before_task_archive` 逐库检查，任一拒绝即停止。`repo/before_task_archive` 默认通过，需要项目补充检查。

`repo/workspace_add` 适配 `.local/create_worktree.sh BASE_COMMIT BRANCH WORKSPACE_ROOT`；MAM 通过配置好的项目 hook 调用它。

### 验证项目 hooks

使用独立测试实例、仓库及产物路径，把验证命令和预期结果写入项目 `.local/README.md`：

1. 创建测试任务并运行 `mam workspace add`，检查路径、分支、base、环境与共享链接，运行项目最小 smoke。
2. 满足 MAM 归档前提后，验证 `before_task_archive` 的拒绝和通过两种情况；确认拒绝时资源保留，归档后 workspace 和 `task/TASK-ID` 分支清理、外部产物保留。
