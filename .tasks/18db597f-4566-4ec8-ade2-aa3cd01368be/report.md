# 独立 review 更正：r3 40-reset gate 与整合文档

## 结论

- 代码：**PASS**（bf34743334efc98440fa9b05e3f2f05e8303846a；此前已接受）。
- 文档：**PASS**（291d6d8017d11baf65aafca3805fe20a61619fa2）。

本报告取代先前报告的三项文档 blocker。它们错误地把文档当作在 291d6d8 自身旧工作树中执行；README 实际明确指定另一个固定的 C r3 runtime，因此该比较不适用。

## 审阅对象与边界

- 独立 RMBench worktree：/mnt/public/xcj/Projects/workspace/18db597f-4566-4ec8-ade2-aa3cd01368be/RMBench，HEAD bf3474，其基线为 7747793。
- 独立 robot-bridge worktree：同 task 路径，HEAD f9626636，仅用于真实 controller API 对照。
- 文档按精确提交 291d6d8 只读审阅。
- 未运行 GPU、SAPIEN/native worker、远端命令或正式评测，也未改动运行时或源代码。

## 文档更正依据

README 第 8–12 行明确要求在 c-eval-renderer-r3/RMBench 的 C r3 checkout 运行，并固定 RMBench 7747793、robot-bridge f9626636、OpenPI a869498。因此文档是给该命名 checkout 的操作指南，并未声称其命令应在 291d6d8 的旧本地 parent 执行。

静态核对该命名 runtime：

- 7747793 是 bf3474 的祖先；两者间的 run_memory_schema_eval.py 与 memory_schema_eval.yaml 没有差异。
- runner 第 218、220 行定义 --training-seed 和 --eval-seed，第 245–246 行要求普通 20k audit/smoke/formal 显式提供二者；README 第 115、120、126 行与此一致。
- runner 第 230–233 行要求 formal 提供 --smoke-run，README 第 123–128 行按同一 train/eval 前缀提供 matching smoke；第 267–274 行实际生成 train<N>--eval<M> 审计后缀，与 README 第 137–141 行一致。
- YAML 第 7–9 行固定 robot_bridge_commit: f9626636…；rmbench_base: f022… 是 r3 基线的祖先。此前声称 bridge SHA 不匹配的结论不成立。
- README 第 94–103 行的 gate 命令与 bf3474/script/renderer_reset_gate.py 的实际 CLI 参数一致，且文档正确要求工具先经 review、同步到 r3 tree、目标卡空闲后才运行。

没有发现需要改写 selector、命令或文档的实际歧义。

## 代码与 CPU 证据

gate 仍是有界的 40-reset 工具：固定 episode 0..39 和 seed 100000..100039，不启动 policy、不写 rollout/result leaf，receipt 与 worker log 均拒绝写入 eval_result。真实 bridge 对照确认 RMBenchSimulationController 的 reset RPC、accepted/episode_status 响应和 shutdown 回收路径与 gate 调用相符。

此前在 CPU-only 条件完成：

    tests/test_renderer_reset_gate.py    2 passed
    tests/test_renderer_lifecycle.py     2 passed
    Python 3.10 重复上述两项            4 passed
    selected robot-bridge pytest         5 passed
    AST/YAML static-doc-contract          PASS

临时 CPU fixture 还确认 native marker 会令 receipt passed=false，episode 22 proxy error 会保留错误、completed_count=22 且 passed=false。

gate 尚未实际部署或运行；r3 GPU gate、matching smoke 和 r3 formal 仍为 pending。六份 r2 EOF partial 仍按“22 条 accepted terminal 加 episode 22 reset-error”处理，不计分、不自动重试；put-back B 六项仍是 C-ready，尚待各自 smoke/formal。

两个独立审阅树均为 clean；没有留下临时产物。
