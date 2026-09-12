# C3 renderer gate 解释器 symlink 窄修复：独立 CPU review

## 裁决

**PASS（限本次代码与 CPU 验证范围）。** 未发现 P0/P1/P2 blocker。候选
`2e9677ce8ec9f623395184f63f32ddafa66e5e44` 是指定范围
`bf34743334efc98440fa9b05e3f2f05e8303846a..2e9677ce8ec9f623395184f63f32ddafa66e5e44`
的直接子提交；只改动 `script/renderer_reset_gate.py` 和
`tests/test_renderer_reset_gate.py`（31 additions、1 deletion）。

本 review 没有采用 `--review` 自动保存的源任务主 worktree RMBench
`3775d4a878adb0f840c1f8a9e12aa014fb185a53`，它不是本次候选。独立 review
worktree 是
`/mnt/public/xcj/Projects/workspace/e755c753-4acf-4958-85f4-7595fba739a0/RMBench`
，分支 `task/e755c753-4acf-4958-85f4-7595fba739a0`，HEAD 为上述 `2e9677c`，
最终 `git status --short` 为空。

## 发现

- **无 blocker。** `run_gate()` 现在先 `expanduser()`，再使用
  `Path(os.path.abspath(...))`。这会将相对路径锚定到与此前 `resolve()` 相同的
  调用时工作目录，却不跟随最终解释器 symlink；`~` 仍按 `Path.expanduser()`
  展开。`is_file()` 继续对目标做有效性检查。
- 实际调用链没有第二次解析该路径。候选将字符串传给
  `RMBenchSimulationController`；冻结 bridge
  `f9626636c4776d8eb15f9c556775cb2d12c000e5` 的
  `rmbench_simulation.py` 将它原样保存，并以
  `subprocess.Popen([self._worker_python, "-u", ...])` 启动 worker。因此
  venv 的 `bin/python` 路径会实际抵达 child process。
- 新测试不是对源码文本的复述：它创建真实 symlink，并断言 controller factory
  收到的解释器仍是 absolute symlink。独立将父提交实现与候选实现都运行在同一
  fixture 后，父提交配置的路径不是 symlink，候选配置的路径是 symlink；故新增
  断言会在旧实现失败。该 unit test 不自行 spawn bridge child，但下面的真实
  controller CPU check 已补足该边界。

## CPU 证据

在独立 RMBench worktree 中，实际 `.venv/bin/python` 是 symlink：

```text
.venv/bin/python -> /mnt/public/xcj/cache/shared-python/cpython-3.10.19-linux-x86_64-gnu/bin/python3.10
```

对同一解释器的直接复现显示：

```text
candidate absolute symlink path:
  sys.prefix = .../RMBench/.venv
  import numpy = PASS

old Path.resolve() target:
  sys.prefix = .../cache/shared-python/cpython-3.10.19-linux-x86_64-gnu
  ModuleNotFoundError: No module named 'numpy'
```

进一步以真实 `RMBenchSimulationController` 做仅 metadata 的 CPU child-process
验证（设置 `CUDA_VISIBLE_DEVICES=''`，没有 reset、仿真或 GPU）：保留 symlink
时 `get_metadata()` 成功且 worker log 无 numpy error；替换成同一路径的旧
resolved base interpreter 时，controller 在 metadata 阶段以
`RMBenchWorkerError` 失败，worker stderr 含 `ModuleNotFoundError` 和 `numpy`。
这复现了报告中的 C3 启动前故障，并验证候选到真实 `Popen` 的修复路径。

临时 CPU fixture 还验证了 relative worker path 与 `~/...` 输入均正确展开为
absolute path，同时保留 symlink，两个 receipt 均为 `passed=True`。所有临时
fixture、controller log 和 pycache 已清理；可复核的命令与输出摘要保留在本报告。

已执行且通过：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_renderer_reset_gate.py
# 3 tests OK
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_renderer_lifecycle.py
# 2 tests OK
PYTHONDONTWRITEBYTECODE=1 /root/.local/bin/python3.10 tests/test_renderer_reset_gate.py
# 3 tests OK
PYTHONDONTWRITEBYTECODE=1 /root/.local/bin/python3.10 tests/test_renderer_lifecycle.py
# 2 tests OK
PYTHONDONTWRITEBYTECODE=1 /root/.local/bin/python3.10 -m py_compile script/renderer_reset_gate.py
git diff --check bf34743334efc98440fa9b05e3f2f05e8303846a..2e9677ce8ec9f623395184f63f32ddafa66e5e44
```

额外动态验证的关键命令是：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/robot-bridge \
.venv/bin/python <temporary controller get_metadata harness>
```

其结果为 `controller_symlink_worker_get_metadata=PASS`，以及
`controller_old_resolved_worker_get_metadata=FAIL_AS_EXPECTED`。

## 未验证边界与后续条件

本 review 没有部署候选、修改活跃树、启动 GPU 作业或运行 C3 的 40-reset。
因此 PASS 只证明解释器启动前回归已修复，**不**证明 C3 renderer lifecycle gate
通过。Manager 若接受本结论，仍须按既有协议将冻结候选同步到 C3，并以新的 receipt
执行 40/40 reset；之后每个 fresh formal 仍要走其匹配 video/no-video smoke 门禁。
