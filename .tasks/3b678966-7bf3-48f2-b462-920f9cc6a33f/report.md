# 独立验收：live S2M 与 Policy Manager 部署入口 PASS

## 准入意见

**准入 PASS。** 候选提交
`041405f0b35b2a173ac3461d297a43141d028026` 已满足复查准则，可以作为
wash-cup 的 Policy Manager 部署入口合入并按更新后的 runbook 使用。

此前对 `a5caa5b57e96fd02de7d6df0cd2ffa5bf0030f5f` 的 live S2M CPU PASS
保持有效；按本次任务要求，没有重跑未变的 live / scheduler 逻辑。

现场执行前仍应先在 Policy Manager 部署目标 child、确认卡片“运行中”，复制该
child 的 WebSocket URL，并以 `--skip-policy` 启动。该结论不代替现场的网络、
UI、homing 和受控动作检查。

## 定向复核结果

- `scripts/launch/x1pro_takeover.sh:58-93` 显式解析
  `--skip-policy`；该分支要求无空白、以 `ws://` 或 `wss://` 开头的
  `RB_POLICY_URL`，且不要求 `RB_POLICY_SSH` 或 checkpoint 环境。
- `x1pro_takeover.sh:106-120` 的 skip policy pane 仅输出明确提示，不调用
  `run_policy_server.sh`，因此不会触发其中的 SSH、端口探测或 policy/GPU
  进程。默认无选项分支仍在第 110 行调用手工
  `run_policy_server.sh`，保留原有手工启动行为。
- skip 分支以 `printf %q` 把本次所选 URL 内联传入 scheduler pane。
  `run_scheduler.sh:42-46` 随后将该环境值展开为远端
  `--policy-url`。测试刻意在 tmux pane 注入过期 URL，确认选定 URL 覆盖它，
  且 `RB_POLICY_PORT=8949` 未被用作判断或转发。
- `docs/tutorials/wash-cup-memory.md:29-63` 已按“先在 PM 部署并复制卡片 URL，
  再执行 `x1pro_takeover.sh --skip-policy`”写明步骤，并明确说明 skip 路径不
  探测或启动 policy 进程。

## CPU 验证

所有测试以 `CUDA_VISIBLE_DEVICES=''` 运行；tmux、sleep 和 SSH 在启动器测试中
均替换为本地假实现，未连接现场、未加载模型权重、未占 GPU，也未发送机器人动作。

```text
bash -n scripts/launch/x1pro_takeover.sh                              PASS
pytest -q tests/launcher/test_x1pro_takeover_launch.py                6 passed
pytest -q tests/launcher                                               164 passed
ruff check tests/launcher/test_x1pro_takeover_launch.py               PASS
git diff --check 0a33dd1..041405f                                    PASS
```

新测试文件有一处仅格式化差异：`ruff format --check tests/launcher/test_x1pro_takeover_launch.py` 建议重排第 141 行的 `assert any`。
`ruff check` 通过；仓库没有发现将 formatter 设为本次准入门槛的规则，因此这不是
部署准入阻塞，建议作者在后续整理时执行 `ruff format`。

## 工作区与收尾

- 保留 robot-bridge worktree：
  `/mnt/public/xcj/Projects/workspace/3b678966-7bf3-48f2-b462-920f9cc6a33f/robot-bridge`，
  branch `task/3b678966-7bf3-48f2-b462-920f9cc6a33f`，HEAD
  `0a33dd19ab911ae3808c3ff141e3fd0603c22594`，干净。
- 保留 openpi worktree：
  `/mnt/public/xcj/Projects/workspace/3b678966-7bf3-48f2-b462-920f9cc6a33f/openpi`，
  branch `task/3b678966-7bf3-48f2-b462-920f9cc6a33f`，HEAD
  `a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4`，干净。
- 已删除仅用于候选提交的 detached review worktree 和
  `/tmp/mam-3b678966-recheck-041405f` CPU 测试缓存；无登记 job。
