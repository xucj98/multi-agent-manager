# wash-cup Memory v1 交付与现场交接状态

## 已交付代码

- robot-bridge：`f0f585a2b5974c60b51cac65277f94d1097591a3`，包含功能提交
  `3906dd0032637410359be6dd5006b3f793f3191c` 的 bridge 本地
  `robot_bridge.memory_config`，以及 TUI 文档的 tmux 环境刷新恢复。
  Manager 已确认独立 review PASS、fast-forward 合入并 push GitHub。
- OpenPI：保持干净的
  `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，未修改、未引入 bridge 依赖。
- bridge 与 OpenPI 当前各自维护本地 `memory_config.py`。bridge scheduler、takeover
  和 offline 直接使用 `robot_bridge.memory_config`；已删除为 scheduler 手工安装
  `openpi-client` wheel 的专用脚本和文档流程。
- 现场流程维持：WSL checkout → 配置 `RB_*` → `push_code.sh auto` →
  `x1pro_takeover.sh` → `:8088`。若已有 tmux server，文档明确逐项
  `tmux set-environment -g` 刷新所需 `RB_*`，避免默认 TUI 路径继承旧拓扑变量。

## CPU 验证

全部为 CPU-only，未加载模型、未占 GPU、未发机器人动作：

```bash
env -u PYTHONPATH PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES='' \
  .venv/bin/python -m pytest -q \
  tests/test_memory_config.py \
  tests/scheduler/test_memory_context.py \
  tests/scheduler/test_memory_v1_schedulers.py \
  tests/scheduler/test_openpi_takeover.py \
  tests/robot/controllers/test_memory_v1_offline.py \
  tests/launcher/test_offline_preflight.py \
  tests/launcher/test_x1pro_takeover_launch.py \
  tests/policy/test_openpi_metadata.py
# 109 passed in 24.53s
```

bridge venv 不含 `openpi_client`；真实 wash full/serial metadata 均成功建立
`MemoryContext`，保留 H50/K30 与各自 full/serial layout。bridge 本地 schema 文件与
OpenPI `a869` 的原文件 SHA-256 一致：
`6287bddad81cd635556ef6b0b75b3abd64248289d74f101e1fa3a07db176aa80`。

## full Policy Manager 长服务：只读观测

MAM job `9f91cf1c-8505-48e3-bd6e-cc7e8093a914` 保持**未归档**，用于现场反馈。通过
`jx-4090-2-via-nx-aic` 于 `2026-09-11T18:58:36Z` 的只读核验结果：

- host：`jxlrtc-dual-gpu-002`；PM parent PID `3646`。
- job PID `2264677` 存在，状态 `Sl`，启动于 `2026-09-11T01:25:02Z`。
- 进程为 OpenPI venv 的 `scripts/run_policy_server.py --port 8951`，cwd 为
  `/home/xucuijie/Projects/robot-bridge`，policy_dir 为已登记的 wash full 20k checkpoint。
- `ss` 显示 `0.0.0.0:8951` 正由 PID `2264677` 监听。

本轮没有 stop、restart、deploy 或修改 PM；也没有连接或修改机器人。服务仍由 Policy
Manager 管理，现场需要保留它直至用户明确结束测试。若后续进程停止，Manager 应先记录实际
观测后再 archive job，不能据 unknown 直接判定停止。

`2026-09-11T19:00:36Z`，为保持 active 运行的 `mam wait` 对该 job 的 SSH 状态查询超时，
返回 `cannot determine state ... SSH query timed out`。这不是 PID 已停的证据，也不覆盖上面的
成功观测；本 task 未重试、未修改网络或服务。收尾方案是保留 job 与 task，待 SSH 恢复后由
Manager 做一次只读 PID/监听核验；只有确认 PID 已不存在后才 archive。

## 本地收尾与现场剩余事项

- 原 workspace 保留：
  `/mnt/public/xcj/Projects/workspace/4296391f-6e8e-4f99-b6ab-e53bb85af99b`；未新建 worktree。
  bridge 和 OpenPI 工作树均干净，任务级 `.pytest_cache`、`.ruff_cache`、源码
  `__pycache__` 和临时文件已清理，保留 `.venv` 与 Git 历史。
- 可部署提交不等同于已完成现场部署或真机动作验证。现场人员应沿现有 TUI/runbook 同步后，
  在 idle 状态核对 metadata、14D、15Hz、H50/K30、phase 与 `memory_diagnostics`，再按其
  安全流程决定受控动作。
- 本 task 与 full job 均暂不 archive，等待用户现场反馈；无需重复 CPU、offline 或远端部署工作。

## 本地 SSH 复用：等待稳定性修正

为避免 `mam wait` 对既有 policy-host alias 的重复建连触发跳板超时，按最新授权只修改了本机
`jx-4090-2-via-nx-aic` 的 SSH 配置。原 `~/.ssh/config` 已备份为
`~/.ssh/config.mam-4296391f-20260912T0304Z.bak`；新增且仅新增：

```sshconfig
Host jx-4090-2-via-nx-aic
    ControlMaster auto
    ControlPersist 15m
    ControlPath ~/.ssh/mam-control/%C
```

socket 目录 `~/.ssh/mam-control` 的权限为 `0700`。原 `User xucuijie`、`HostName 127.0.0.1`、
`Port 22022`、`ProxyJump wuwen-nx-aic`、认证和全部其他 host 配置均未改动。

本机 master PID `141501` 已建立。经同一 alias 的三次只读 `id -un; hostname` 探测分别为
486ms、284ms、264ms，均返回 `xucuijie` / `jxlrtc-dual-gpu-002`；没有查询模型、发送动作或
修改远端。恢复时，在不再需要本地复用连接后，以该备份覆盖 `~/.ssh/config`，并在 socket
目录清空后删除 `~/.ssh/mam-control`；这只影响本地 SSH，不影响 PM child。
