task_revision: e831fd8646c900d433edfb409a1fffdd28574dee

# GPU1 执行完成，已交回

按授权顺序完成 d10 step50 full technical smoke2 → serial technical smoke2 → drawer full-state/serial-soft 各5ep offline。没有修改代码、配置、checkpoint、软链接或环境，没有使用 GPU0。

## 技术 sim smoke

| run leaf | 时间（2026-09-10 +08:00） | 正常完成 | 任务结果 | 运行验证 |
| --- | --- | --- | --- | --- |
| technical_rearrange_full_t_plus_1_gpu1_20260910 | 15:07:57–15:16:56 | 2/2 | 0/2 success | PASS |
| technical_rearrange_serial_lag30_gpu1_20260910 | 15:18:47–15:28:35 | 2/2 | 0/2 success | PASS |

- 使用原保留 d10 full/serial 的 50-step checkpoint，实际参数 `--technical-smoke --gpu 1 --mode smoke`；sim 与 policy 共用 GPU1，robot/policy 端口 19410/19412。
- 两 run 均由既有 `validate_smoke_run` 验证通过：各两条 accepted rollout、无 runtime_error、summary status=completed；seed 为100000/100001；episode0 的700帧视频通过读取检查，episode1 无视频。
- full：每集24个 query，trace 中 memory_input_ids 长度3、预测50行；每集23次完整 K30 的 chunk_completed 反馈均选 last_executed row30/index29。
- serial：每集24个 query，memory_input_ids 长度3、预测1行；每集24次 query_selected 反馈均选 query row1/index0。
- checkpoint/served policy/robot metadata 均实际留存；`config_source` 继承的 input_audit.json、input_manifest.json 与原输入逐字节一致。
- 两 run 的 scheduler 均退出0；policy/robot 由 runner_shutdown 终止（-15），全部 start 均有对应 exit，PID 已不存在。
- full config SHA-256：d23f2c717d09a7f71506e09b30b03b59d31f290661bf334b44375fbffe9b2500。
- serial config SHA-256：430a987e7cc9ad880c181eafa8faf42e6022b81c42c70cb593bae72004922bbe。

这里的 PASS 仅表示真实新 wire、反馈、留痕与退出链路通过。50-step 模型的0/2不用于判断20k性能，也不能替代正式20k checkpoint自身的匹配smoke。

## 旧 drawer offline

既有 drawer_offline.py 在 GPU1、robot/policy 端口19510/19512，按 manifest 为两模型各执行固定 `[1,22,23,24,26]`。产物时间15:30:41–15:38:54；入口最终退出0。两模型均为原 RMBench 30000 checkpoint。

| episode | frames（各模型） | full-state robot MAE | serial-soft robot MAE |
| --- | ---: | ---: | ---: |
| 1 | 2068 | 0.016105877 | 0.015136310 |
| 22 | 4369 | 0.014484981 | 0.013961060 |
| 23 | 3838 | 0.013737270 | 0.013419121 |
| 24 | 3798 | 0.013077538 | 0.012691271 |
| 26 | 3320 | 0.013919684 | 0.013556464 |

- 全10集 exit.json returncode=0。每模型17393 frames；10份NPZ可读，全部数值数组/metrics有限，actions与action_gt形状一致，memory_ids与memory_gt形状一致，帧数与metrics一致。
- 两模型各8个继承metadata文件的hash均匹配，served_metadata、真实policy命令、输入manifest/evidence及provenance均保存。
- master_source/phase_source 均为 last_infer。两policy均由既有入口正常收尾，policy_exit记录 shutdown_requested=true、returncode=-15。
- 上述为offline action/memory回归指标，不是闭环success rate；没有据此推断超出本次五集的性能结论。

## 成果与资源收尾

实际结果根：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/`。

- `technical_rearrange_full_t_plus_1_gpu1_20260910/`：实际command/config、metadata继承、逐query trace、视频与退出证据。
- `technical_rearrange_serial_lag30_gpu1_20260910/`：同上。
- `drawer_s2m_v2_regression_5ep_gpu1_20260910/`：provenance.json保存真实启动命令，两个模型目录各包含metadata、served_metadata、policy_exit及5集metrics/NPZ/exit。

GPU1已交回：最终核对显存1MiB、空闲81038MiB、利用率0%，19410/19412/19510/19512无监听，本任务三树解释器进程均不存在。三个程序均不足1小时，未登记长job；mam job list --task 返回 jobs=[]。

已清理本task `.local/memory_schema_eval` 的两份临时audit目录及本task GPU1 Warp缓存。共享实际结果保留供Manager验收，technical结果不进入正式成绩表，验收后清理对应技术smoke。未触碰其他任务进程或结果。

## 固定版本

复用工作区：`/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a`，三库均干净：

- RMBench：`RMBench/`，f414eda7cfc9fb18fa3ccdfd902accdb9908b2e6。
- robot-bridge：`robot-bridge/`，8ea6078543a875b5ae223df16891cdc1fe975c66。
- openpi：`openpi/`，a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。

本轮仅运行并报告，复用已验收commit；没有新代码提交或待修接线问题。20k formal不属于本次运行范围。
