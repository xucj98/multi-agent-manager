# 独立 review：r3 40-reset gate 与整合文档

## 范围与审阅树

- RMBench：`/mnt/public/xcj/Projects/workspace/18db597f-4566-4ec8-ade2-aa3cd01368be/RMBench`，独立分支 `task/18db597f-4566-4ec8-ade2-aa3cd01368be`，HEAD `bf34743334efc98440fa9b05e3f2f05e8303846a`，基线 `77477931bee18c2476bea36b400ab45dc67d9ebe`。
- robot-bridge：同一 task 的独立 worktree，HEAD `f9626636c4776d8eb15f9c556775cb2d12c000e5`，用于真实 API 对照。
- 文档按精确提交 `291d6d8017d11baf65aafca3805fe20a61619fa2` 相对 `295effbbab8347b1ba43dca051740cbfde82089a` 只读审阅。

未运行 GPU、SAPIEN/native worker、远端命令或正式评测；两个审阅树均 clean，临时 `py_compile` cache 已清理并保留 worktree 供 Manager 验收。

## 代码：PASS（仅限 `bf3474`）

`script/renderer_reset_gate.py` 保持为有界工具：固定 `put_back_block/demo_clean_eval`、episode `0..39`、seed `100000..100039`、无 policy/action/recorder/result leaf，receipt 与 worker log 均拒绝写入 `eval_result`。它把物理 `--device` 映射成 worker 的 `CUDA_VISIBLE_DEVICES=<GPU>` 与 `SAPIEN_RENDER_DEVICE=cuda:0`，并记录系统 ICD、两个 git state、metadata、每条 reset、marker 和原子 receipt。

我没有只接受候选自身的 fake proxy。冻结 bridge 的真实 API 是：`RMBenchSimulationController(config)` 在构造时启动 worker，`reset(**request)` 直接转发 RPC；真实 worker 的 `_reset_response()` 返回 `accepted` 与 `episode_status`。gate 提供的 `task/config/seed/episode_id/video` 与该签名一致，且仅在 `accepted=true`、`state=ready`、`terminal=false` 时继续。`shutdown()` 使用真实 controller 的进程内回收路径；冻结 bridge 的现有测试证明 stuck worker 会被 reaped，seed reject 与 accepted 后 setup failure 可区分。

CPU 验证均在 `CUDA_VISIBLE_DEVICES=''` 下完成：

```text
python3 tests/test_renderer_reset_gate.py                 # 2 passed
python3 tests/test_renderer_lifecycle.py                  # 2 passed
/root/.local/bin/python3.10 上重复上述两项              # 4 passed
python3 -m py_compile script/renderer_reset_gate.py
python3 script/renderer_reset_gate.py --help
robot-bridge pytest 5 selected                             # 5 passed
```

选取的 bridge 测试覆盖真实 proxy 的 request id/卡死 worker 回收、worker 的 seed rejection 与 reset failure、scheduler reset wire contract 和 controller handler 路径。另以临时 CPU fixture 直接调用候选 `run_gate()`：40 条 accepted 且 stderr 含 `ErrorIncompatibleDriver` 时 receipt `passed=false`；episode 22 抛 proxy error 时 `completed_count=22`、`passed=false`、保留 error。故 native marker 或 EOF 不会被误报为 PASS，且不会跳过 seed。

这不是 native/GPU 验证；gate 仍应保持 pending，待独立 review 结果同步后才可在获授权的空闲目标卡运行。

## 文档：BLOCKER（`291d6d8`）

`README_memory_schema.zh-CN.md` 的 r3 smoke/formal 三条示例不可执行，不能合入为当前使用说明。

1. 第 115、120、126 行传入 `--training-seed` 与 `--eval-seed`。同一精确提交的 `commands/run_memory_schema_eval.py:185-205` 只定义 `variant/checkpoint/run-name/gpu/mode/smoke-run/technical-smoke/prepare-audit/dry-run`，没有这两个参数；argparse 会在 audit、smoke 或 formal 前拒绝命令。
2. README 第 10–12 行指定 r3 bridge `f9626636`，但同提交的 `configs/memory_schema_eval.yaml` 固定 `robot_bridge_commit: 8ea6078`，脚本第 212–215 行要求当前 bridge HEAD 与该旧 SHA 相等。因此即使删去无效参数，r3 路径也会在运行前被该断言拒绝。
3. README 第 138 行声称审计输入目录有 `--train<N>--eval<M>` 后缀；实际脚本第 226–228 行只使用 `variant--<checkpoint-hash>`。这会误导清理和并发留痕判断。

修复应先让实际 r3 runner/config 的冻结 SHA 与已部署三树一致，再只记录入口实际支持的 seed 选择方式；若确实需要这两个 selector，应先作为代码变更实现并测试。随后把审计目录说明同步到真实实现。完成前，文档命令不能作为 C r3 启动依据。

其余状态陈述经 targeted 证据核对没有发现矛盾：两个新 r2 `final_review.json` 的 SHA 与文档一致，均为 `completed100_verified`、33/100、100 terminal、0 runtime errors/worker markers；put-back B 六项 C-ready 与训练 owner `695bc51f` 的最终报告一致。e690 已发布证据也保持六份 EOF partial 为 22 terminal + episode 22 的 reset-error，均不计分；文档没有把 gate、smoke 或 r3 formal 误写成已完成。

## 交接

代码候选可独立进入下一步 review；文档提交须先修复上述三项一致性 blocker。没有部署、合入或改动活跃 runtime。
