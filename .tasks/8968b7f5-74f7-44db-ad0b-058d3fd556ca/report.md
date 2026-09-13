# P0 选中 query 诊断记录接口：当前状态报告

## 当前状态

**未通过 GPU 诊断验收，等待 Manager 裁决。** v2 有界恢复在 C2 preflight 阶段停止，未进入 J full_t_plus_1 runner，也未进入 S、记录验收或 logging off/on 配对。因此没有新的 90 秒首次 policy RPC 结果，也没有新的诊断 JSON/NPZ 可验收。

本报告对应任务 revision 5223fb70aa219e92ad34d9c73aad1172e18fa207。已停止的 v2 MAM job 797d3940-a1b9-4ab1-bbba-57f03beff8aa 已于 2026-09-13T18:57:04Z 归档。

## v2 配置与部署

v2 仅按授权在 J/S scheduler config 中增加 params.policy_first_infer_timeout: 90.0；正常 RPC 仍使用冻结的 30 秒默认值。结果、诊断和 manifest 使用新的 timeout90-v2 路径。没有修改三库源码、环境、权重、RNG、依赖、共享 cache、checkpoint、GPU 映射、episode、seed、query 或容量限制。

- J config SHA-256：59aeb0fb748ce5017580bf25c5a7ca425fd2f8b4ce66b5f72610b2dc8d9da041
- S config SHA-256：1348358152825df1ece05697c60421d7ca760efc0c23c38fe69c797b88f66f89
- v2 tools manifest SHA-256：f7899e550cd13a8fa32493ad208d5a9ce58b260ac4ae6fde17e557fe3ce5151f
- task-private deployment manifest SHA-256：c8ec1b8b1b06189fac425792e10698a6287adb0860aafac0554de3a0f7a3c6fa
- deployment verifier SHA-256：c04d181524ba4e2357d976584359f5e9c15d9ac666cb3d812971ddf011225931

部署校验器在本机验证了 24 个冻结工具/清单，并对篡改 config 的副本拒绝通过。C2 接收后生成的 deployment receipt 为 passed=true、verified_file_count=24，SHA-256 为 eafdafba8534f86f6514c48da19094f1d902df879a1676726baabb8ae0f9a266。

首次传输曾把工具放到暂存目录的扁平 tools/ 层，移动到预期嵌套目录时停止；这发生在任何运行前。10 个工具和 14 个清单的远端 SHA 均逐项重算一致后，仅移动已有暂存常规文件完成布局，未重传、改内容或覆盖目标。独立传输证据为 c2-query-diagnostic-timeout90-v2/deployment/timeout90_v2_deployment_transfer_attempt1_failure.json，SHA-256 为 8ed7de50887220c56491aa93edea5bef2b5288e6d7af2d5489e5a29e215de1c1。

## v2 实际首因与停止边界

启动前的只读检查通过：C2 GPU6 为 4 MiB/0%，19460/19462 未监听，没有 task-owned 进程，所有新的 J/S result、diagnostic、pair 和 receipt leaf 都不存在；三棵运行树为下列冻结提交且 clean：

- RMBench：f401f5279c95451eb424ac98b831bab5552b2120
- robot-bridge：e147f600dc4329f330a6e2eb0335150b5b3093a3
- OpenPI：bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6

流水线在 preflight 退出，terminal status 为 failed、exit code 1，SHA-256 为 4b7d173e65a451edecdec5855ef3f59f7bbc5e5a428d998d20893e1014cfe039。失败的 preflight receipt SHA-256 为 73698d687811d29adaf2d1cf0e603f5a1d7577a50e3c6b1f1ceecd23821474ed，outer log SHA-256 为 567943c6556c7e80ac566e97cf5601d1185ef3e453c829c55ef803bb5343bc3e。

具体原因是冻结的 c2_timeout90_v2_preflight.py 用 RUN in ps args 检查残留进程，而它自身的解释器命令正包含该 task run 路径。它把自己的 PID 2550668 记录成 “task-owned C2 process remains”，随后拒绝启动。这不是启动前资源检查发现的其他 child，也不是 policy、renderer、CUDA、robot 或 scheduler 故障。

因此：

- J scheduler config validation、J smoke、J acceptance 与 J pair 均未启动。
- S scheduler config validation、S smoke、S acceptance 与 S pair 均未启动。
- v2 result group、diagnostic directories 和 pair directories 内没有新 JSON/NPZ/benchmark 产物。
- 90 秒首次 infer 设置从未实际传给 policy RPC；不能把本次停止解释为恢复成功或失败。
- 没有重复流水线、增加 timeout/资源、修改冻结源码或删除失败证据。

后续如要继续，需要 Manager 对这个明确的 preflight 自匹配缺口作新的窄裁决；当前边界下不自行修改或重跑。

## 清理

终端复核显示：

- task-owned process：无
- 19460/19462 listener：无
- GPU6：4 MiB、0%
- C2 RMBench、robot-bridge、OpenPI worktree：均 clean

所以已归档上述 MAM job；归档不会删除远端 failure receipts、deployment receipt 或 v1 证据。

## v1 证据仍保留

此前 J v1 实际进入第一个选中 query，并在默认 30 秒 policy RPC deadline 前没有响应；记录状态为 policy_response_missing。其 failure receipt 位于 records/c2-query-diagnostic-full_t_plus_1-failure-receipt.json，SHA-256 为 681a5b4b5dc29069d69d1821190cb52e961be4f7009152b27b148533d8a67ad2；更新后的 run-evidence manifest SHA-256 为 4c7991530ce13cf681151dbe93d556344d5dede4f0f098e1b0e42fd3ad5f8d84。

v1 的 renderer gate、Manager 授权的替代 cuRobo CUDA smoke、源码 CPU 测试及提交链均不因 v2 的启动前停止而改变。当前两个开发 worktree 保持：

- OpenPI：/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/openpi，提交 bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6
- robot-bridge：/mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/robot-bridge，提交 e147f600dc4329f330a6e2eb0335150b5b3093a3

本地 v2 工件位于 /mnt/public/xcj/Projects/workspace/8968b7f5-74f7-44db-ad0b-058d3fd556ca/c2-query-diagnostic-timeout90-v2。

