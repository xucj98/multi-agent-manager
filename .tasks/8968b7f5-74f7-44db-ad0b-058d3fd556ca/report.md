# P0 选中 query 诊断记录接口：attempt2 结果报告

## 当前状态

**未通过完整 GPU 诊断验收；本次有界恢复已结束，未自动重试。**

本报告对应已发布任务 revision `c13aa2c55aaec8da3e211696b22b4dc613feec27`。授权的 attempt2 已修复并通过 task-private preflight，J（`full_t_plus_1`）两集 smoke 与严格 `recorded` 验收均通过；随后真实 logging off/on pair 在与保存记录的严格输出比较处失败。流水线在该首因停止，S（`serial_lag30`）未启动。

## 自匹配 preflight 修复及部署

旧 v2 preflight 会把自身解释器命令行中的 run 路径当作残留 task 进程。修正版精确解析 `ps` 的 PID，仅忽略 `os.getpid()`；仍拒绝任何其他命令行含 run 路径的 PID，没有放宽脚本名、Python 或祖先进程匹配。

- 修正版 preflight：SHA-256 `194e18392772adab9b699f1505550570432a7dc7b72572bba4d4741fa1215caa`；相对 v2 的最小 diff：`93040a7dfd7df2d3d5709c1d2ec37649def2b4fedc6ad65afcc4f52c515ffffc`。
- CPU 核验通过：自身命令行含 run 路径时被忽略，另一个同样含 run 路径的 PID 被拒绝；receipt SHA-256 `e0b46cab097267daffca57184f2328c6323ad0290c8a4f5b989339c2f29cc582`。
- C2 部署收据为 `passed=true`、26 个冻结文件，SHA-256 `0a2809fd871679bf425fbfc0d9aa443da0ac54b82ec6da9e1b73d9c1011f581d`。运行前 preflight 为 `passed=true`，SHA-256 `e15f54e44bbb3281dc6d5542674ebef69f6b06d07bfae694f4c640e1829dab8a`。

仍使用冻结的 C2 GPU6、端口 19460/19462、episodes `[0,1]`、seeds `100000/100001`、query `1`、H50/K30、最多 2 条记录且每条 64 MiB。首个 policy RPC 为 90 秒，后续 RPC 保持 30 秒；没有修改源码、环境、checkpoint、共享 cache、RNG 或资源上限。C2 三树在运行和收尾时均为 clean：RMBench `f401f5279c95451eb424ac98b831bab5552b2120`、robot-bridge `e147f600dc4329f330a6e2eb0335150b5b3093a3`、OpenPI `bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6`。

## J smoke 与 recorded 验收

J config validation 通过，确认 `policy_first_infer_timeout=90.0`、后续为 30 秒且没有 policy/robot 连接；receipt SHA-256 `cacd0db61d1de6481705cc4ccfe2ba3de5a0053e2c8cdf3916a5057a6daaf6d3`。J acceptance 为 `passed=true`，SHA-256 `35fc6e092c51910b49c522737c044246d76017cb1aaa942b949f681c6992c412`：

- benchmark `completed`，目标和实际均为 2 episodes；两个 scheduler 均以 `returncode=0` 的 `episode_terminal` 退出。
- 两个 scheduler stdout 都包含 `First policy inference uses 90.0s RPC budget.`；验收收据同时记录后续 RPC 为 30 秒。
- `validate_query_diagnostic` 对两条 query-1 记录均返回 `recorded`：
  - episode 0 / seed 100000：JSON `9f7191f0fd1c87464b378450c89524dc25d4c066012228db3792f9bcc9d4b1fe`，NPZ `85cf69da786301ec412ee49b459370db9240cdd7811ad610b4ea505d4a0cb37c`。
  - episode 1 / seed 100001：JSON `e77b9e330051b4a8f6c4355b18e61429134e690404abd141f7dc2ae13eb06d8c`，NPZ `a6e8da809071a0d8363921094c66be0f861246c14dd84491fc651e1bb1024651`。

记录位于 C2 的 `/mnt/public/xcj/Projects/state-vla/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/records/diagnostics-timeout90-v2/full_t_plus_1/`；J 结果组为 `query_diagnostic_c2_20260914_timeout90_v2/query_diagnostic_full_t_plus_1_smoke_20260914_timeout90_v2`。

## 首因：J logging off/on pair 严格比较失败

pair 收据 `/mnt/public/xcj/Projects/state-vla/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/records/pairs-timeout90-v2/full_t_plus_1/episode-000000-query-000001-seq-000001.json` 在 `2026-09-13T19:23:05Z` 至 `19:24:05Z` 运行，`passed=false`，SHA-256 `77e397f3574b09ee389d0aac4637923bf6b39a4feac8c556a067e5d8676af0b3`。

两次直接模型调用本身相等：`logging_off_vs_logging_on=true`；两侧最终 RNG 与保存的 split 后 RNG 都相等，logging-on sidecar 的 input、split 前和 split 后 RNG 也都与保存值相等。失败来自两侧与保存 recorded output 的严格比较，具体差异相同：

```text
output.actions: dtype/shape float32/(50, 14) != float64/(50, 14)
```

也就是说，直接 off/on 输出的 actions 为 `float32`、形状 `(50, 14)`，保存记录中的对应 actions 为 `float64`、形状相同。收据没有证明转换 dtype 后的数值相等，因此不能将这次 pair 视为行为等价通过。外层流水线因此报 `RuntimeError: logging off/on pair comparison failed`。

终态文件 `/mnt/public/xcj/Projects/state-vla/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/records/c2-query-diagnostic-timeout90-v2-preflight-selfpid-attempt2-pipeline-status.json` 为 `failed`、exit code `1`、last phase `full_t_plus_1_logging_off_on_pair`，SHA-256 `eb25a6295defe154371661a2035aea8a58adf50e2dd9524a7767bec8a972111e`。对应 outer log SHA-256 为 `546f471669b36c431b67c050ceea8b8f9fd4b46e4979150fe753cbdb2f47ea78`。

由于该 pair 是第一个失败点，S smoke、S 验收和 S pair 均未执行；收尾时确认 S 的诊断记录、结果 leaf 和 pair 收据均不存在。未增加 timeout、样本、GPU 资源或重跑任何阶段。

## 收尾与保留证据

后置核验以 PID 解析方式排除了检查器自身及祖先，未发现其他 task-owned 进程；19460/19462 未监听。GPU6 当时为 4 MiB、0%，三棵 C2 运行树保持上述冻结提交且 clean。

已归档 MAM job `90d495d9-2ef3-49b8-8073-536c2cf6b920`，归档时间 `2026-09-13T19:31:19Z`。归档只停止 MAM 跟踪，不删除 C2 证据。v1、旧 v2、attempt2 的原始 receipts、logs、configs、manifests 及失败输出均保留；没有覆盖已有 JSON/NPZ 或结果目录。
