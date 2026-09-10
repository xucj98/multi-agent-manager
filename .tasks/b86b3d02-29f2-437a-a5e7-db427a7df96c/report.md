# 交付报告（2026-09-11 05:45 CST；正式 GPU offline 待 Manager 调度）

## 实施范围

已在独立 worktree `/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/robot-bridge` 的分支 `task/b86b3d02-29f2-437a-a5e7-db427a7df96c` 完成公共 offline 入口和指标修复。新 wash-cup 单 phase full/serial（H50/K30）与既有 drawer 双字段配置共用同一 controller、scheduler 和 launcher；新增固定 wash 5 集 manifest（LeRobot index 0–4），保留既有 drawer 入口、真机反馈路径、process/exit/metadata 产物管理。

实现提交：`3a364a6dd87c08753a804e5598ddc85ef832d9b1`（`feat(offline): support memory v1 replay metrics`）。worktree 干净，保留给 Manager 安排独立 review；未自行 review、合并或部署。

## 关键决定

- checkpoint 的 `memory_config` 与 `openpi_client.memory_config.make_training_sample()` 是 action GT、memory target、时间语义和 availability mask 的唯一来源，避免训练、推理与 offline 各自定义 offset。
- S2M action 保持 `action_at_row` / offset 0；full 使用逐帧 `t+j+1`，serial 使用当前 query，没有额外移位。
- 仅对实际 drain 的 action 计分；NPZ 保存 action/memory prediction、GT、mask、query/source/model-row 和执行行。count 求和，accuracy 按 sample 或 transition count 加权。
- 从既有 `drawer_offline.py` 泛化为配置驱动的 `offline_replay`，没有复制 launcher 或另建 wash 专用调度器；legacy drawer payload 仍走原分支。

## Launcher 泛化范围与可简化空间

这次 launcher 的约 520 行增量不全是 root/路径/metadata 兼容层；其中必要的新逻辑还包括 Memory v1 sidecar 的 15 Hz 时钟与 query-count 预检、H/K/执行行门禁、missing-future-checkpoint 的无 GPU dry-run、以及沿用现有的 provenance、metadata 和退出产物。

- **root 注册**：现有输入确实需要两个根。旧 drawer manifest 的 checkpoint 是 `RMBench/...`，继续由已有 `--rmbench` 解析；新 wash manifest 的 checkpoint 和 sidecar 都是 `{root: "OpenPI", path: "..."}`，需要 `--checkpoint-root OpenPI=...`。泛化成可重复的 `NAME=PATH` 并非这两个输入唯一可行的 CLI 设计，`--openpi` 也能满足；保留 alias 形式是为了让 manifest 不写机器绝对路径。可由独立 review 判断是否值得缩为两个固定 flag。
- **多形式路径**：当前两种格式都被实际输入使用：旧 drawer 的 `RMBench/...` 相对前缀和新 wash 的 `{root, path}` 映射。纯绝对路径字符串 fallback 未被这两个 manifest 使用，只是窄的兼容余量，可在确认没有外部 manifest 依赖后删除。
- **多 metadata 模式**：两种现有输入也都需要。旧 drawer 没有 `expected_policy_metadata`，必须从 `dataset` 推导 15 Hz / H30 / stride15；新 wash 明确提供该 mapping，以门禁 15 Hz / H50 / stride30，并额外要求 K30。若允许改写旧 manifest 可以统一成显式 mapping；在“不改旧 drawer 配置”边界下，两种读取方式是必要的。
- `--replay` 显式选节和自动探测中，当前两个 manifest 都可走自动探测；显式选节不是现有输入的必需项，也属于可审查的简化候选。

## CPU 验证

- 相关完整套件：`49 passed, 1 skipped`，覆盖新 full、serial、多字段、缺失 mask、canonical S2M action GT、scheduler 转发、memory feedback、旧 drawer 和 transform/metadata 契约。
- `ruff check --select E,F`、`py_compile`、manifest JSON 校验和 `git diff --check` 均通过。
- 新 wash 真实 5 集无 GPU dry-run 通过：15 Hz source-frame sidecar 映射与 query 数为 1216、1509、702、1115、983；两个预定 checkpoint 均如实显示 `ready: false`。
- 既有 drawer manifest 的无 GPU dry-run 也通过，固定 episode `[1,22,23,24,26]`、15 Hz / H30 / K15 与两个既有 checkpoint 路径保持可用。

## 预计剩余时间与 07:27 安排

接口实现、CPU 门禁和提交已于 05:44 完成，剩余实现时间为 0；因此能赶上 07:27 后安排 wash offline，不需要为赶时间省略验证。

正式 offline 仍需训练产物出现后由 Manager 分配 GPU。固定输入共 5,525 个 query / 模型，正式运行会评估 full 和 serial 两个模型；没有在本轮加载模型或占用 GPU，故不把未经测得的 GPU 吞吐时间写成 ETA。启动前先重跑同一 dry-run 确认两个 `20000` 目录转为 `ready: true`。

正式命令草案（**不要在本 task 中自行启动**；由 Manager 在已分配 GPU 后执行，替换输出目录名）：

```bash
cd /mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/robot-bridge
PYTHONPATH=/mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/openpi/packages/openpi-client/src \
  .venv/bin/python scripts/launch/drawer_offline.py \
  --manifest configs/input_manifests/wash_cup_memory_v1_offline5.json \
  --raw-root /mnt/public/datasets/x1pro/wash-cup \
  --checkpoint-root OpenPI=/mnt/public/xcj/Projects/openpi \
  --policy-python /mnt/public/xcj/Projects/workspace/b86b3d02-29f2-437a-a5e7-db427a7df96c/openpi/.venv/bin/python \
  --output /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/wash_memory_v1_5ep_<timestamp>
```

桥接 worktree 的 `.venv` 未安装 light `openpi_client`，所以该 `PYTHONPATH` 是命令的一部分；policy 进程继承 Manager 的 GPU 分配环境。

## Manager 裁定与外部前提

当前没有需要 Manager 裁定的实现阻塞，也未发现需要改变算法或大规模重构的证据。

唯一外部前提是两个预定 wash 20k checkpoint 目录当前尚不存在。这不阻塞本次代码交付，也不请求现在预留 GPU；若 07:27 时目录仍未出现，正式 offline 将因训练产物尚未就绪延后，而不是以未完成接口验收替代。
