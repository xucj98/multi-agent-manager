# 07:34 正式仿真阶段：rearrange seed0两项smoke通过，formal100已启动

复用原三树、既有入口和recorder，无源码变更；GPU0/1仍训练，GPU2/3留wash，wuwen-1停用。按06:53授权，owner发布GPU4/6保存、CPU验收及释放后，本任务各自检查显存1MiB/81038MiB空闲/0%、独立端口空闲再启动。

## 已完成的20k匹配smoke

| checkpoint项 | GPU | smoke run | 结果 | video0帧数 | logical steps |
| --- | ---: | --- | --- | ---: | --- |
| rearrange t+1 seed0 | 4 | rearrange_full_t_plus_1_s0_20k_smoke2 | 2/2 success，门禁PASS | 393 | 393/407 |
| rearrange t+30 seed0 | 6 | rearrange_full_t_plus_30_s0_20k_smoke2 | 2/2 success，门禁PASS | 392 | 392/405 |

两项启动分别07:24:57/07:25:51，最外层CLI均exit0。既有validate_smoke_run核对当前manifest与bridge source通过，两条accepted rollout无runtime_error，video/no-video各一集；MP4逐帧读通。input_audit/input_manifest经config_source继承副本逐字节一致。每项两scheduler exit0，policy/robot按runner_shutdown退出-15，所有start对应PID已不存在。实际20k checkpoint-only恢复已由smoke覆盖，不重复技术50。

smoke config SHA256：
- t+1: 6f1d367559353dc42fa548f5ab9f700d216dfa08dd0f746dd98234f1d43a3afb
- t+30: 336b3e2454acdb33328d491a834c9ef81ed2f5d4514581d90f2e26ed94ba1bb5

上述2/2只是smoke结果，不替代正式100统计。

## 已启动正式100

| GPU | run | 启动时间（CST） | PID | MAM job |
| --- | --- | --- | ---: | --- |
| 4 | rearrange_full_t_plus_1_s0_20k_100ep | 2026-09-11 07:32:29 | 3319712 | af7dd7c9-682c-4a78-9e6e-946cbf47672f |
| 6 | rearrange_full_t_plus_30_s0_20k_100ep | 2026-09-11 07:33:30 | 3321184 | 1e72397f-0602-4018-bc7c-4e112ad7501a |

host均is-dcfi2kjdq7g3k6aa-devmachine-0。可靠detach（Popen start_new_session、stdin=DEVNULL、排他创建日志），实际command/cwd/时间/PID位于本RMBench .local/memory_schema_eval/launches/<run>.json，临时启动日志同名.log；正式run沿既有recorder保存实际配置/命令/继承metadata。各自使用匹配smoke，GPU4端口19440/19442，GPU6端口19460/19462，独立Warp cache。登记时MAM均running，当前正在检查正式首条，尚未声称100完成。

每run在单卡串行100，不按中途成绩重采样；第50条做正常诊断。新20k没有真正可比的旧配置基准，不能强行套用不同训练/模型/F0成功率作为10个百分点门槛。保持active turn，mam wait jobs --task本任务结合日志中检，结束核验完整产物与退出、归档job、清理自身smoke/临时缓存并保留门禁摘要。

## 后续队列与CPU准备

GPU5/7仍待owner分别发布释放，再核对显存后跑put-back t+1/t+30 seed0。14项队列继续按README训练seed成对推进。8份远端20k已完成audit/smoke dry/formal dry（24次exit0）；本机新验收的rearrange t+1 seed2、put-back t+1 seed1也各完成同三项CPU检查，共10份就绪。其余项按owner保存/CPU门禁交接后准备；CPU检查不加载GPU权重。

真实结果根：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/。
原worktree根：/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a。
- RMBench: 3e69b1e665a8eac0104d261b233f1b3339007e00
- robot-bridge: 8ea6078543a875b5ae223df16891cdc1fe975c66
- openpi: a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4

三树源码冻结。CPU queue与wash公共缺口详见前轮report bf6d8e8f167bf5e1d705afcc3eb1f06b5f82c28b；旧drawer正式结果原样保留，不重跑。本阶段不修改wash公共实现。
