# 07:47 首批四模型匹配smoke全部通过，四卡formal100已启动

按06:53授权，在owner分别发布GPU4/6/7/5训练保存、CPU验收、进程退出和释放后逐卡接用；每次启动前显存均1MiB/0%，端口空闲，原三树干净。GPU0/1不抢占，GPU2/3留wash，wuwen-1停用。未修改源码/配置，未重跑技术50或旧drawer。

## 已完成：四个20k自身smoke

| variant（均训练seed0） | GPU | smoke结果 | 视频帧数 | 两条logical steps | config SHA256 |
| --- | ---: | --- | ---: | --- | --- |
| rearrange_full_t_plus_1 | 4 | 2/2，门禁PASS | 393 | 393/407 | 6f1d367559353dc42fa548f5ab9f700d216dfa08dd0f746dd98234f1d43a3afb |
| rearrange_full_t_plus_30 | 6 | 2/2，门禁PASS | 392 | 392/405 | 336b3e2454acdb33328d491a834c9ef81ed2f5d4514581d90f2e26ed94ba1bb5 |
| put_back_full_t_plus_1 | 5 | 1/2，门禁PASS | 333 | 333/500 | 7f9fa778a054e7138201069a4ebf7d6884d43e1e3fa6168e305e79751f0c5585 |
| put_back_full_t_plus_30 | 7 | 2/2，门禁PASS | 332 | 332/329 | c0b903e28db9d52717a6ca61c873c692156ae3ea711e4ee5881c3e0e9e83ae5b |

smoke run名均 `<variant>_s0_20k_smoke2`。四次CLI均exit0，既有validate_smoke_run验证当前manifest/source通过；每run两条accepted rollout无runtime_error，video/no-video各一集，视频逐帧读通。input_audit与input_manifest经config_source继承副本逐字节一致。每run两scheduler exit0，policy/robot正常runner_shutdown -15，所有start对应进程均已退出。

put-back t+1第二条为正常step_limit_reached（500步），不改参数或重抽样。这里的成功数仅为smoke结果，不替代正式100成绩。真实20000权重恢复与新wire由匹配smoke覆盖，不再另跑技术验证。

## 正在运行：四个formal100

| GPU | run | 实际启动CST | PID | MAM job |
| --- | --- | --- | ---: | --- |
| 4 | rearrange_full_t_plus_1_s0_20k_100ep | 2026-09-11T07:32:29.513716+08:00 | 3319712 | af7dd7c9-682c-4a78-9e6e-946cbf47672f |
| 6 | rearrange_full_t_plus_30_s0_20k_100ep | 2026-09-11T07:33:30.188818+08:00 | 3321184 | 1e72397f-0602-4018-bc7c-4e112ad7501a |
| 5 | put_back_full_t_plus_1_s0_20k_100ep | 2026-09-11T07:46:46.988207+08:00 | 3352946 | a58e56cc-2281-4d88-89af-53bdee13a768 |
| 7 | put_back_full_t_plus_30_s0_20k_100ep | 2026-09-11T07:43:56.270325+08:00 | 3344284 | 1803ad5f-b94a-4b64-bdc1-2c7f8ed9339c |

host均is-dcfi2kjdq7g3k6aa-devmachine-0。各run单GPU串行100，sim/policy同卡，分别引用自身smoke。robot/policy端口依次GPU4=19440/19442、GPU5=19450/19452、GPU6=19460/19462、GPU7=19470/19472；各卡独立Warp缓存。正式前重新核对空闲显存/端口与三树干净，可靠detach，立即登记各MAM job。

实际command/cwd/PID/启动时间保留于本worktree .local/memory_schema_eval/launches/<run>.json；临时启动日志同名.log。正式run沿既有recorder保存实际命令、配置、checkpoint/served metadata和source；smoke验证摘要保存为正式目录smoke_verification.json（新启动项在runner建目录后复制）。不在空run目录提前写入文件。

rearrange两项已完成正式首条并继续推进，put-back两项正在启动/首条阶段。尚未完成100，不宣称正式成绩。保持active turn，通过mam wait jobs --task等待并结合日志检查；第50条正常诊断，新20k尚无真正可比旧基准，不强行引用不同训练/模型/F0成功率。保留正常失败与全部100条，结束核对产物/退出、archive job，保留smoke门禁摘要后清理自有smoke和临时缓存。

## 剩余队列与位置

14项按README既定训练seed配对队列推进，不按中途表现筛选。目前12份已完成owner保存/CPU门禁交接及本入口audit/smoke dry/formal dry（各exit0）；只剩本机训练中的put-back seed2两项待交接。未开始的10个formal仍在队列，不因首批开跑宣称任务完成。

workspace: /mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a
- RMBench: 3e69b1e665a8eac0104d261b233f1b3339007e00
- robot-bridge: 8ea6078543a875b5ae223df16891cdc1fe975c66
- openpi: a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4

正式结果根: /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/。
CPU准备输出: 本RMBench/.local/memory_schema_eval/cpu_20k_20260911；临时audit/manifest在inputs/，checkpoint保持只读。三树继续冻结，后续全部运行结束再更新实验README，避免改变运行source身份。

旧drawer正式产物原样保留。wash公共接口缺口已交Manager协调，详见前轮report bf6d8e8f167bf5e1d705afcc3eb1f06b5f82c28b，本轮不跨写公共实现。
