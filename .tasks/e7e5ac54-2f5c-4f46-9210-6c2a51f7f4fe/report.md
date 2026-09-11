# Memory 20k：远端八路与本机六路

## 9月11日09:32 本机最后两路小时巡检

已读最新task；09:32:42–43逐项job status均running，无error。两路日志均继续前进，全部已落盘loss/grad_norm/param_norm有限，无可见训练报错。其余12项已收尾归档，本轮未重复checkpoint读取或远端探测。

| 本机GPU | 模型/seed | updates≈ | 最新实际标量 | 剩余ETA |
| --- | --- | --- | --- | --- |
| 0 | put-back t+30 / 2 | 17.0k | Step16900 loss=0.0007, grad_norm=0.0304, param_norm=1804.2034 | 3:03:23 |
| 1 | put-back t+1 / 2 | 17.2k | Step17100 loss=0.0008, grad_norm=0.0331, param_norm=1804.3474 | 2:56:11 |

两路各169/171条有限标量为区间均值；kit为取整进度，ETA不含保存。GPU1预计12:29、GPU0约12:36完成更新。固定运行树仍d10完整SHA、git status为空，未改源码/参数。

资源：GPU0已用73438MiB/空闲7600MiB/100%，GPU1为73406/7633MiB/100%，RAM可用867GiB。本机其他卡已有使用/释放变化，仅记录资源快照，不检查其他task；本任务未启动新GPU工作，eval由Manager安排。

继续active turn和mam wait等待两项结束事件；下一小时10:32巡检。远端全部本任务训练已完成，自有进程退出；既有不可见外部占用边界不变，本轮未重新探测整机。

## 9月11日08:32 本机最后两路小时巡检

已读最新task；08:32:18–19逐项job status均running，无error。两路日志继续前进，所有已落盘loss/grad_norm/param_norm有限，无可见训练报错。其余12项已收尾归档，未重复checkpoint读取或远端探测。

| 本机GPU | 模型/seed | updates≈ | 最新实际标量 | 剩余ETA |
| --- | --- | --- | --- | --- |
| 0 | put-back t+30 / 2 | 16.0k | Step15900 loss=0.0008, grad_norm=0.0339, param_norm=1804.1646 | 4:03:16 |
| 1 | put-back t+1 / 2 | 16.2k | Step16100 loss=0.0009, grad_norm=0.0371, param_norm=1804.3064 | 3:54:11 |

两路各159/161条标量均为有限区间均值。kit为取整进度，ETA不含保存；GPU1预计12:26、GPU0约12:35完成更新。运行树仍d10完整SHA、git status为空，未改源码/参数。

资源：GPU0已用73460MiB/空闲7579MiB/100%，GPU1为73406/7633MiB/100%，RAM可用846GiB。GPU2当前1MiB/0%；GPU3–7已有其他占用，本轮仅记录快照，不检查其他task或清理进程。此前本任务GPU4–7释放证据仍见各项收尾记录；本任务未启动eval或接续GPU工作。

继续active turn及mam wait等待这两项结束事件，释放卡由Manager安排eval；下一小时09:32巡检。远端已完成全部本任务训练，自有进程退出；全机不可见外部占用的既有边界仍保留。

## 9月11日07:37 GPU5完成收尾

本机 GPU5，memory20k_e7e5ac54_rearrange_full_t_plus_30_s2，job `0c82949f-f5c6-4772-aea6-1967e9cc2680`，PID2467721。最终20000保存与Save Finalize完成，MAM wait返回stopped；随后PID及同session/直接子进程均不存在，GPU5=1MiB已用/81038MiB空闲/0%。无自有残留需清理；未留存数值exit code，退出及保存分别有证据。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s2/20000`。
本机固定解释器显式CUDA_VISIBLE_DEVICES为空/JAX_PLATFORMS=cpu，实际读回51叶/3353433872元素，全BF16、全有限、全部参数路径与注册config shape一致，CPU核验exit0。父目录仅20000，有原子commit，仅params/assets/metadata，无optimizer；metadata JSON/JSONL/YAML解析通过，d10/clean/实际command/config协议一致，demo_clean_state来源和norm与验收资产吻合。200条标量均有限，Step20000：grad_norm=0.0321, loss=0.0006, param_norm=1804.5264，未见训练报错。

逐参数shape及完整CPU审计：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_rearrange_full_t_plus_30_s2.json`。
对应training job按结果归档；累计12项完成/2项未完成。本任务不在wuwen-1接续任何GPU工作；05:32发现GPU6/7不可见外部占用的边界继续保留；本机释放卡交Manager安排eval；完整policy GPU恢复/wire/评测未由本任务擅自启动。继续MAM事件等待，运行项08:32巡检。

## 9月11日07:34 GPU7完成收尾

本机 GPU7，memory20k_e7e5ac54_put_back_full_t_plus_30_s1，job `3e67c9de-fc4f-4a94-a2da-7dccbdec9b2e`，PID2467723。最终20000保存与Save Finalize完成，MAM wait返回stopped；随后PID及同session/直接子进程均不存在，GPU7=1MiB已用/81038MiB空闲/0%。无自有残留需清理；未留存数值exit code，退出及保存分别有证据。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s1/20000`。
本机固定解释器显式CUDA_VISIBLE_DEVICES为空/JAX_PLATFORMS=cpu，实际读回51叶/3353433872元素，全BF16、全有限、全部参数路径与注册config shape一致，CPU核验exit0。父目录仅20000，有原子commit，仅params/assets/metadata，无optimizer；metadata JSON/JSONL/YAML解析通过，d10/clean/实际command/config协议一致，demo_clean_state来源和norm与验收资产吻合。200条标量均有限，Step20000：grad_norm=0.0337, loss=0.0006, param_norm=1804.2756，未见训练报错。

逐参数shape及完整CPU审计：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_put_back_full_t_plus_30_s1.json`。
对应training job按结果归档；累计11项完成/3项未完成。本任务不在wuwen-1接续任何GPU工作；05:32发现GPU6/7不可见外部占用的边界继续保留；本机释放卡交Manager安排eval；完整policy GPU恢复/wire/评测未由本任务擅自启动。继续MAM事件等待，运行项08:32巡检。

## 9月11日07:32 本机剩余4路小时巡检

07:32:25–27逐项job status均running，无error；最新日志均前进、全部已落盘loss/grad_norm/param_norm有限，无可见训练报错。累计10项完成收尾并归档，本轮未重复已验收checkpoint读取。

| 本机GPU | updates≈ | 最新实际标量 | 日志剩余ETA |
| --- | --- | --- | --- |
| 0 | 15.0kit/20.0kit | Step 15000: grad_norm=0.0312, loss=0.0007, param_norm=1804.1228 | 5:00:27 |
| 1 | 15.2kit/20.0kit | Step 15200: grad_norm=0.0331, loss=0.0009, param_norm=1804.2634 | 4:48:45 |
| 5 | 19.9kit/20.0kit | Step 19900: grad_norm=0.0287, loss=0.0006, param_norm=1804.5247 | 04:48 |
| 7 | 20.0kit/20.0kit | Step 19900: grad_norm=0.0354, loss=0.0006, param_norm=1804.2734 | 01:40 |

kit为取整进度，GPU7尚未完成，不能以20.0kit判定保存成功。ETA不含保存：GPU7约07:34，GPU5约07:37；GPU1约12:21、GPU0约12:33。运行树仍d10完整SHA且git status为空，未改参数。

本机资源：GPU0/1/5/7各约73405–73406MiB已用/7633MiB空闲/100%；GPU2/3/4/6当前均1MiB/81038MiB空闲/0%，RAM可用876GiB。GPU4/6已由本任务收尾释放；GPU2/3当前空闲仅为资源快照，未检查其他task产物。可用卡及本任务checkpoint交Manager安排eval，本任务不启动新GPU任务。

继续MAM等待并仅按新完成事件核验；剩余运行项下一小时08:32巡检。远端8项已完成，自有进程全退出；此前不可见外部占用边界仍见06:06汇总，本轮未重复探测远端。

## 9月11日07:24 GPU6完成收尾

本机 GPU6，memory20k_e7e5ac54_put_back_full_t_plus_1_s1，job `f04d1b9c-4a77-4034-ac6c-c7240d9b20a8`，PID2467722。最终20000保存与Save Finalize完成，MAM wait返回stopped；随后PID及同session/直接子进程均不存在，GPU6=1MiB已用/81038MiB空闲/0%。无自有残留需清理；未留存数值exit code，退出及保存分别有证据。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s1/20000`。
本机固定解释器显式CUDA_VISIBLE_DEVICES为空/JAX_PLATFORMS=cpu，实际读回51叶/3353433872元素，全BF16、全有限、全部参数路径与注册config shape一致，CPU核验exit0。父目录仅20000，有原子commit，仅params/assets/metadata，无optimizer；metadata JSON/JSONL/YAML解析通过，d10/clean/实际command/config协议一致，demo_clean_state来源和norm与验收资产吻合。200条标量均有限，Step20000：grad_norm=0.0348, loss=0.0007, param_norm=1804.3906，未见训练报错。

逐参数shape及完整CPU审计：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_put_back_full_t_plus_1_s1.json`。
对应training job按结果归档；累计10项完成/4项未完成。本任务不在wuwen-1接续任何GPU工作；05:32发现GPU6/7不可见外部占用的边界继续保留；本机释放卡交Manager安排eval；完整policy GPU恢复/wire/评测未由本任务擅自启动。继续MAM事件等待，运行项07:32巡检。

## 9月11日07:23 GPU4完成收尾

本机 GPU4，memory20k_e7e5ac54_rearrange_full_t_plus_1_s2，job `b3d46ac6-b2b7-4ea2-b3ad-df74a2bdac7e`，PID2467720。最终20000保存与Save Finalize完成，MAM wait返回stopped；随后PID及同session/直接子进程均不存在，GPU4=1MiB已用/81038MiB空闲/0%。无自有残留需清理；未留存数值exit code，退出及保存分别有证据。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/memory20k_e7e5ac54_rearrange_full_t_plus_1_s2/20000`。
本机固定解释器显式CUDA_VISIBLE_DEVICES为空/JAX_PLATFORMS=cpu，实际读回51叶/3353433872元素，全BF16、全有限、全部参数路径与注册config shape一致，CPU核验exit0。父目录仅20000，有原子commit，仅params/assets/metadata，无optimizer；metadata JSON/JSONL/YAML解析通过，d10/clean/实际command/config协议一致，demo_clean_state来源和norm与验收资产吻合。200条标量均有限，Step20000：grad_norm=0.0318, loss=0.0005, param_norm=1804.5598，未见训练报错。

逐参数shape及完整CPU审计：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_rearrange_full_t_plus_1_s2.json`。
对应training job按结果归档；累计9项完成/5项未完成。本任务不在wuwen-1接续任何GPU工作；05:32发现GPU6/7不可见外部占用的边界继续保留；本机释放卡交Manager安排eval；完整policy GPU恢复/wire/评测未由本任务擅自启动。继续MAM事件等待，运行项07:32巡检。

## 9月11日06:32 本机剩余6路小时巡检

06:32:20–24逐项job status均running，无error；最新日志全部前进，已落盘loss/grad_norm/param_norm均有限，无可见训练报错。远端8项已收尾归档，本轮未重复读取其checkpoint或探测远端。

| 本机GPU | updates≈ | 最新实际标量 | 日志剩余ETA |
| --- | --- | --- | --- |
| 0 | 14.0kit/20.0kit | Step 14000: grad_norm=0.0366, loss=0.0010, param_norm=1804.0712 | 6:04:07 |
| 1 | 14.2kit/20.0kit | Step 14200: grad_norm=0.0356, loss=0.0010, param_norm=1804.2085 | 5:57:06 |
| 4 | 19.2kit/20.0kit | Step 19100: grad_norm=0.0290, loss=0.0005, param_norm=1804.5385 | 50:36 |
| 5 | 19.0kit/20.0kit | Step 18900: grad_norm=0.0320, loss=0.0006, param_norm=1804.4998 | 1:04:59 |
| 6 | 19.2kit/20.0kit | Step 19100: grad_norm=0.0305, loss=0.0006, param_norm=1804.3707 | 50:36 |
| 7 | 19.0kit/20.0kit | Step 19000: grad_norm=0.0316, loss=0.0006, param_norm=1804.2550 | 1:01:03 |

kit为取整进度，ETA不含保存。GPU4/6预计约07:23、GPU7约07:33、GPU5约07:37；GPU1约12:29、GPU0约12:36完成更新。资源快照：本任务六卡各约73405–73406MiB已用、7633MiB空闲、100%利用率，本机8卡均仍占用；RAM可用836GiB、共享盘9.1TiB。运行树d10cc01完整SHA、git status为空；未改源码/参数。

保持MAM wait等待新完成事件；本机GPU恢复/wire/评测仍待可用卡与Manager排期，未抢占训练。远端06:05不可见外部占用边界仍以已发布收尾汇总为准，不将本任务退出等同整机空闲。下一运行项小时巡检07:32，先到的结束事件立即处理。

## 9月11日06:06 远端八路收尾交接汇总

远端8路均已自然完成实际20000 updates，最终保存成功；8份checkpoint的CPU全参数读取/BF16/有限值/注册config逐参数shape、metadata解析、norm与资产一致性检查通过。各exp下仅最终20000，原子提交完成，无optimizer。8个training job均已按结果归档，旧六路缓冲已全部落盘，每路200条标量均有限；未重复已验收checkpoint全量读取。

| wuwen-1 GPU | 配置/seed | Step20000 loss | 保存完成时间 |
| --- | --- | --- | --- |
| 0 | rearrange full t+1 / 0 | 0.0007 | 05:03:04 |
| 1 | rearrange full t+30 / 0 | 0.0007 | 04:58:03 |
| 2 | serial lag30 / 0 | 0.0133 | 05:08:39 |
| 3 | no-memory / 0 | 0.0004 | 05:18:31 |
| 4 | put-back full t+1 / 0 | 0.0006 | 06:04:59 |
| 5 | put-back full t+30 / 0 | 0.0006 | 05:34:52 |
| 6 | rearrange full t+1 / 1 | 0.0007 | 04:41:29 |
| 7 | rearrange full t+30 / 1 | 0.0007 | 04:36:01 |

**退出与资源边界：** 每项结束时登记PID/同session及直接子进程均已消失、对应GPU曾降至4MiB/0%；06:05整机收尾快照再次确认8个登记PID全不存在，compute-apps为空。原detach未留数值退出码，不能补称exit0；保存finalize和进程消失分别有证据。

**整机目前不空闲：** 06:05 GPU0–3各74099MiB/100%，GPU6/7分别14885/14569MiB及85%/86%，GPU4/5各4MiB/0%。上述新占用没有本机可见compute PID，本任务未启动任何接续GPU任务，不能将占用归为本任务残留；未清理不明进程。请Manager按集群/其他虚拟机资源归属协调，不能凭本任务结束宣布整机空闲。

本机6路继续冻结训练，最后一次合并检查为05:32，均running/可见标量有限；GPU4–7预计07:18–07:37，GPU0/1预计12:29–12:36（ETA不含保存）。本阶段未抢占本机卡、未运行GPU恢复或评测。

所有checkpoint路径及各项CPU结果见下文收尾节；统一位于共享 `/mnt/public/xcj/Projects/openpi/checkpoints/<config>/<exp>/20000`。新检查逐参数shape审计在本task workspace的closure目录；首两份结果已直接留于报告。尚待：本机6路自然完成及收尾、实际20000完整policy checkpoint-only GPU恢复/wire、Manager安排的评测交接。GPU恢复仅能安排本机空闲卡，wuwen-1不接续。

本轮已按MAM wait连续处理远端8项结束事件并发布交接，下一本机小时巡检06:32；如Manager通知提前结束事件则按同协议处理。

## 9月11日06:05 GPU4完成收尾

wuwen-1 GPU4，memory20k_e7e5ac54_put_back_full_t_plus_1_s0，job `463092be-02b4-4bfa-bf12-8eae2416a244`，PID12435。最终20000保存与Save Finalize完成，MAM wait返回stopped；随后PID及同session/直接子进程均不存在，GPU4=4MiB已用/81046MiB空闲/0%。无自有残留需清理；未留存数值exit code，退出及保存分别有证据。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000`。
本机固定解释器显式CUDA_VISIBLE_DEVICES为空/JAX_PLATFORMS=cpu，实际读回51叶/3353433872元素，全BF16、全有限、全部参数路径与注册config shape一致，CPU核验exit0。父目录仅20000，有原子commit，仅params/assets/metadata，无optimizer；metadata JSON/JSONL/YAML解析通过，d10/clean/实际command/config协议一致，demo_clean_state来源和norm与验收资产吻合。200条标量均有限，Step20000：grad_norm=0.0304, loss=0.0006, param_norm=1804.4258，未见训练报错。

逐参数shape及完整CPU审计：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_put_back_full_t_plus_1_s0.json`。
对应training job按结果归档；累计8项完成/6项未完成。本任务不在wuwen-1接续任何GPU工作；05:32发现GPU6/7不可见外部占用的边界继续保留；完整policy GPU恢复/wire/评测仍待本机空闲卡及Manager安排。继续MAM事件等待，运行项06:32巡检。

## 9月11日05:35 GPU5完成收尾

wuwen-1 GPU5，memory20k_e7e5ac54_put_back_full_t_plus_30_s0，job `6e2601ea-e091-4e63-9c31-e90895ca5ffe`，PID12436。最终20000保存与Save Finalize完成，MAM wait返回stopped；随后PID及同session/直接子进程均不存在，GPU5=4MiB已用/81046MiB空闲/0%。无自有残留需清理；未留存数值exit code，退出及保存分别有证据。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s0/20000`。
本机固定解释器显式CUDA_VISIBLE_DEVICES为空/JAX_PLATFORMS=cpu，实际读回51叶/3353433872元素，全BF16、全有限、全部参数路径与注册config shape一致，CPU核验exit0。父目录仅20000，有原子commit，仅params/assets/metadata，无optimizer；metadata JSON/JSONL/YAML解析通过，d10/clean/实际command/config协议一致，demo_clean_state来源和norm与验收资产吻合。200条标量均有限，Step20000：grad_norm=0.0302, loss=0.0006, param_norm=1804.2913，未见训练报错。

逐参数shape及完整CPU审计：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_put_back_full_t_plus_30_s0.json`。
对应training job按结果归档；累计7项完成/7项未完成。本任务不在wuwen-1接续任何GPU工作；05:32发现GPU6/7不可见外部占用的边界继续保留；完整policy GPU恢复/wire/评测仍待本机空闲卡及Manager安排。继续MAM事件等待，运行项06:32巡检。

## 9月11日05:32 剩余8路小时巡检

已读最新要求，05:32:48–54逐项job status均running，无error。累计6项training job已完成收尾/归档；剩余8路最新日志均前进、所有已落盘loss/grad_norm/param_norm有限，无Traceback/CUDA/OOM等可见报错。未重复读取任何已验收checkpoint参数。

| host/GPU | updates≈ | 最新实际标量 | 日志剩余ETA |
| --- | --- | --- | --- |
| wuwen-1/4 | 19.5kit/20.0kit | Step 19400: grad_norm=0.0315, loss=0.0006, param_norm=1804.4135 | 32:28 |
| wuwen-1/5 | 20.0kit/20.0kit | Step 19900: grad_norm=0.0318, loss=0.0007, param_norm=1804.2891 | 02:06 |
| 本机/0 | 13.0kit/20.0kit | Step 13000: grad_norm=0.0368, loss=0.0010, param_norm=1804.0103 | 7:03:24 |
| 本机/1 | 13.3kit/20.0kit | Step 13200: grad_norm=0.0350, loss=0.0011, param_norm=1804.1437 | 6:56:32 |
| 本机/4 | 18.2kit/20.0kit | Step 18200: grad_norm=0.0313, loss=0.0007, param_norm=1804.5131 | 1:45:36 |
| 本机/5 | 18.0kit/20.0kit | Step 17900: grad_norm=0.0353, loss=0.0007, param_norm=1804.4702 | 2:04:33 |
| 本机/6 | 18.2kit/20.0kit | Step 18200: grad_norm=0.0334, loss=0.0008, param_norm=1804.3468 | 1:49:58 |
| 本机/7 | 18.0kit/20.0kit | Step 18000: grad_norm=0.0296, loss=0.0006, param_norm=1804.2294 | 2:01:20 |

进度kit为取整值，远端GPU5仍running、Step19900，不把20.0kit当作完成。ETA不含最终保存；远端GPU5预计05:35、GPU4约06:05结束更新。本机GPU4–7约07:18–07:37，GPU0/1约12:29–12:36。冻结worktree仍d10cc01完整SHA、git status为空，未改参数。

05:32:55资源：远端GPU0–3各4MiB/0%，GPU4/5各73489MiB/100%，RAM可用876GiB；本机8卡均约73405–73408MiB/100%，RAM可用836GiB，共享盘可用9.1TiB。

**需Manager知悉的资源变化：** 远端GPU6/7此前在本任务收尾时均4MiB/0%，本轮分别出现14449/14499MiB及85%/86%利用率。本任务没有启动任何新GPU进程；必要只读身份核对中nvidia-smi compute-apps仅列仍在训练的PID12435/12436，未显示GPU6/7对应占用进程，故不能归因为本任务残留（可能其他虚拟机占用）。未尝试终止不明进程；整机空闲状态须在最终释放时据实核对，不承诺外部占用会消失。

MAM继续等待新结束事件，只验收新checkpoint；GPU恢复/wire/评测仍待本机空闲卡和Manager排期，wuwen-1不接续GPU任务。运行项下一小时06:32检查；先到的结束事件立即收尾。

## 9月11日05:18 GPU3完成收尾

wuwen-1 GPU3，memory20k_e7e5ac54_rearrange_no_memory_s0，job `2774d038-5a23-4184-b16a-92fa1fd88019`，PID4186839。最终20000保存与Save Finalize完成，MAM wait返回stopped；随后PID及同session/直接子进程均不存在，GPU3=4MiB已用/81046MiB空闲/0%。无自有残留需清理；未留存数值exit code，退出及保存分别有证据。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_no_memory/memory20k_e7e5ac54_rearrange_no_memory_s0/20000`。
本机固定解释器显式CUDA_VISIBLE_DEVICES为空/JAX_PLATFORMS=cpu，实际读回51叶/3353433872元素，全BF16、全有限、全部参数路径与注册config shape一致，CPU核验exit0。父目录仅20000，有原子commit，仅params/assets/metadata，无optimizer；metadata JSON/JSONL/YAML解析通过，d10/clean/实际command/config协议一致，demo_clean_state来源和norm与验收资产吻合。200条标量均有限，Step20000：grad_norm=0.0207, loss=0.0004, param_norm=1804.2346，未见训练报错。

逐参数shape及完整CPU审计：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_rearrange_no_memory_s0.json`。
对应training job按结果归档；累计6项完成/8项未完成。释放的wuwen-1 GPU保持空闲；完整policy GPU恢复/wire/评测仍待本机空闲卡及Manager安排。继续MAM事件等待，运行项05:32巡检。

## 9月11日05:09 GPU2完成收尾

wuwen-1 GPU2，memory20k_e7e5ac54_rearrange_serial_lag30_s0，job `d682fab7-3cbc-4b7e-a31a-b959bbd2695c`，PID9003。最终20000保存与Save Finalize完成，MAM wait返回stopped；随后PID及同session/直接子进程均不存在，GPU2=4MiB已用/81046MiB空闲/0%。无自有残留需清理；未留存数值exit code，退出及保存分别有证据。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_serial_lag30/memory20k_e7e5ac54_rearrange_serial_lag30_s0/20000`。
本机固定解释器显式CUDA_VISIBLE_DEVICES为空/JAX_PLATFORMS=cpu，实际读回56叶/3353474844元素，全BF16、全有限、全部参数路径与注册config shape一致，CPU核验exit0。父目录仅20000，有原子commit，仅params/assets/metadata，无optimizer；metadata JSON/JSONL/YAML解析通过，d10/clean/实际command/config协议一致，demo_clean_state来源和norm与验收资产吻合。200条标量均有限，Step20000：grad_norm=0.2686, loss=0.0133, param_norm=1805.6949，未见训练报错。

逐参数shape及完整CPU审计：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_rearrange_serial_lag30_s0.json`。
对应training job按结果归档；累计5项完成/9项未完成。释放的wuwen-1 GPU保持空闲；完整policy GPU恢复/wire/评测仍待本机空闲卡及Manager安排。继续MAM事件等待，运行项05:32巡检。

## 9月11日05:03 GPU0完成收尾

wuwen-1 GPU0，memory20k_e7e5ac54_rearrange_full_t_plus_1_s0，job `89dcc92f-365e-409a-87d3-e6e82b66adba`，PID4186829。最终20000保存与Save Finalize完成，MAM wait返回stopped；随后PID及同session/直接子进程均不存在，GPU0=4MiB已用/81046MiB空闲/0%。无自有残留需清理；未留存数值exit code，退出及保存分别有证据。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/memory20k_e7e5ac54_rearrange_full_t_plus_1_s0/20000`。
本机固定解释器显式CUDA_VISIBLE_DEVICES为空/JAX_PLATFORMS=cpu，实际读回51叶/3353433872元素，全BF16、全有限、全部参数路径与注册config shape一致，CPU核验exit0。父目录仅20000，有原子commit，仅params/assets/metadata，无optimizer；metadata JSON/JSONL/YAML解析通过，d10/clean/实际command/config协议一致，demo_clean_state来源和norm与验收资产吻合。200条标量均有限，Step20000：grad_norm=0.0345, loss=0.0007, param_norm=1804.5520，未见训练报错。

逐参数shape及完整CPU审计：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_rearrange_full_t_plus_1_s0.json`。
对应training job按结果归档；累计4项完成/10项未完成。释放的wuwen-1 GPU保持空闲；完整policy GPU恢复/wire/评测仍待本机空闲卡及Manager安排。继续MAM事件等待，运行项05:32巡检。

## 9月11日04:59 第三份20000 checkpoint收尾

wuwen-1 GPU1，rearrange full_t_plus_30 seed0，job `db46bdd0-0ec2-41c1-9c98-baca9ffd6f5b`，PID4186841。04:58:03.156完成最终保存，04:58:08 MAM wait返回stopped；随后PID及同session/直接子进程均消失，GPU1=4MiB/81046MiB空闲/0%。数值exit code未留存；退出和保存完成证据分别成立，无自有残留需清理。

checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0/20000`。

本机固定解释器显式禁用GPU，CPU实际读取51叶/3353433872元素，全BF16/全有限且注册模型参数路径与shape逐项匹配，exit0。父目录仅20000，原子commit存在，仅params/assets/metadata，无optimizer。metadata的9JSON/6JSONL/6YAML解析通过，d10/clean/command/config协议一致，demo_clean_state来源及norm hash5d84df27…吻合。200条落盘标量全有限；Step20000 loss=0.0007、grad_norm=0.0348、param_norm=1804.5471，无可见训练报错。

完整CPU审计（含逐参数shape）保存在 `/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/closure/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0.json`。该training job按结果归档；累计3项完成/11项未完成。GPU1/6/7释放后保持空闲；GPU完整policy恢复/评测继续等待本机空闲卡及Manager排期。MAM继续等待，运行项05:32巡检。

## 9月11日04:42 第二份20000 checkpoint收尾

04:47补齐两份seed1 metadata内容核验：每份9个JSON、6个JSONL、6个YAML均解析成功；保存norm与已验收共享资产JSON一致，SHA256=`5d84df27e9fce3c6ec28585319ed293fa59fc1822063ecfa0e95c5bf4478606b`。该检查仍在本机显式禁用GPU，仅检查已结束两项。

wuwen-1 GPU6，rearrange full_t_plus_1 seed1，job `95a88ee3-1a90-4e2e-baa1-50a1cd6f4eb0`，PID4186835，04:41:29.545最终保存并完成Save Finalize，MAM wait 04:41:34返回stopped；随后/proc PID及同session/直接子进程均不存在，GPU6已用4MiB、空闲81046MiB、0%。无自有残留需清理；数值exit code未留存，退出与保存成功分别有证据。

交接checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/memory20k_e7e5ac54_rearrange_full_t_plus_1_s1/20000`。父目录仅20000；commit_timestamp存在，items仅params/assets/metadata，无optimizer。command记录d10完整SHA/clean/冻结cwd/GPU6/seed1，数据记录demo_clean_state，norm及上游metadata已保存。

本机显式CUDA_VISIBLE_DEVICES为空、JAX_PLATFORMS=cpu，固定树解释器实际restore_params为numpy；51叶、3353433872元素全BF16且有限，参数路径与jax.eval_shape注册模型逐项shape一致，检查exit0。缓冲退出后200条标量全部有限，Step20000：loss=0.0007、grad_norm=0.0352、param_norm=1804.5416。

training job按结果归档，GPU6/7释放后保持空闲。两份seed1配对checkpoint已完成CPU参数完整性与释放检查；完整policy恢复/wire/GPU评测仍待本机空闲卡及Manager排期。其余12路继续冻结，mam wait接续事件；运行项下次05:32小时巡检。

## 9月11日04:39 首份20000 checkpoint收尾与交接

wuwen-1 GPU7，rearrange full_t_plus_30 seed1，job `fa1d8437-1fb7-48a5-8d37-2233e8e06767`，PID4186832，已自然结束。04:36:01日志确认最终20000原子提交、Save Finalize done；MAM wait于04:36:05返回stopped（当时zombie），随后/proc PID已不存在，同session/直接子进程为空。GPU7已用4MiB、空闲81046MiB、利用率0%，没有需要清理的自有残留。原detach未留独立exit-code文件，数值退出码不可追溯；实际退出及保存成功分别由进程检查和finalize日志证实，不将stopped直接等同exit0。

首份交接checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s1/20000`。

- 父目录仅20000，无临时checkpoint；_CHECKPOINT_METADATA有commit_timestamp，items仅assets/metadata/params，无train_state或optimizer。
- metadata/command.txt记录d10cc01完整SHA、clean、冻结cwd、GPU7、seed1和原实际命令；train_config.yaml记录batch32/20000/BF16/save_full_state=false，datasets.json为demo_clean_state、50episodes，norm与上游数据/sidecar metadata均已保存。
- 本机固定树解释器，显式 `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -B`，JAX仅CpuDevice。通过既有restore_params(checkpoint/params, restore_type=np.ndarray)实际读回全部51叶、3353433872元素，全部BF16且数值有限。另用注册config.model.create的jax.eval_shape对比checkpoint metadata，51/51参数路径与shape完全一致。两次CPU核验均exit0，未占GPU，未修改运行源码。
- 退出后缓冲已落盘：Step100至20000共200条，loss/grad_norm/param_norm全部有限；Step20000为loss=0.0007、grad_norm=0.0345、param_norm=1804.5209。这是区间均值证据。
- 已完成保存/参数CPU读取/形状/metadata文件/释放检查；完整policy checkpoint-only GPU恢复、wire及正式评测尚待本机空闲卡和Manager排期，未将CPU参数读回称为完整policy推理通过。本机仍全占用，wuwen-1释放卡保持空闲。

对应training job按本记录归档；其余13路保持冻结，继续mam wait jobs --task接续结束事件，运行项按05:32小时频率核查。

## 9月11日04:32 巡检与接续收尾

已读最新04:32收尾条款。04:33:43–48实时job status确认14路running，无error；04:33–04:34日志及资源快照如下。

| host/GPU | updates≈ | 最新实际标量 | 剩余ETA |
| --- | --- | --- | --- |
| wuwen-1/0 | 19.5kit/20.0kit | 未落盘 | 29:14 |
| wuwen-1/1 | 19.6kit/20.0kit | 未落盘 | 24:10 |
| wuwen-1/2 | 19.4kit/20.0kit | 未落盘 | 34:49 |
| wuwen-1/3 | 19.3kit/20.0kit | 未落盘 | 44:48 |
| wuwen-1/4 | 18.6kit/20.0kit | Step 18500: grad_norm=0.0316, loss=0.0007, param_norm=1804.3907 | 1:31:18 |
| wuwen-1/5 | 19.0kit/20.0kit | Step 19000: grad_norm=0.0342, loss=0.0006, param_norm=1804.2703 | 1:01:01 |
| wuwen-1/6 | 19.9kit/20.0kit | 未落盘 | 07:31 |
| wuwen-1/7 | 20.0kit/20.0kit | 未落盘 | 02:00 |
| 本机/0 | 12.1kit/20.0kit | Step 12000: grad_norm=0.0360, loss=0.0010, param_norm=1803.9397 | 8:02:00 |
| 本机/1 | 12.3kit/20.0kit | Step 12300: grad_norm=0.0340, loss=0.0010, param_norm=1804.0759 | 7:54:54 |
| 本机/4 | 17.3kit/20.0kit | Step 17200: grad_norm=0.0352, loss=0.0008, param_norm=1804.4784 | 2:48:42 |
| 本机/5 | 17.0kit/20.0kit | Step 17000: grad_norm=0.0343, loss=0.0008, param_norm=1804.4375 | 3:03:18 |
| 本机/6 | 17.3kit/20.0kit | Step 17200: grad_norm=0.0338, loss=0.0007, param_norm=1804.3140 | 2:49:00 |
| 本机/7 | 17.1kit/20.0kit | Step 17100: grad_norm=0.0315, loss=0.0007, param_norm=1804.2007 | 3:00:23 |

14路均前进、未见训练报错；8路已落盘loss/grad_norm/param_norm均有限（区间均值），旧远端6路仍未落盘，有限loss未证实。20.0kit是取整显示，不是完成证明；ETA不含保存。远端GPU7约04:36、GPU6约04:41首先结束更新，其余最晚约06:05。

04:34资源：远端8卡均100%，已用73489–73507MiB、空闲7543–7561MiB，RAM可用792GiB；本机8卡均100%，本任务六卡各空闲7633MiB，不能抢占。源码/参数冻结，未启动新GPU任务。

已启动mam wait jobs --task接续等待完成事件。只对实际结束项核验20000最终保存、metadata/参数BF16及完整性、退出和自有子进程/显存释放，处理后归档training job。wuwen-1释放后停用；CPU检查在本机显式禁用GPU，GPU恢复/评测等待本机空闲卡及Manager排期。其他运行项下一小时05:32检查。

## 9月11日03:32 十四路小时巡检

已读最新任务，沿冻结协议执行。逐个job status实时检查：2026-09-11 03:33:34–36+08:00，14路均running、无error，身份由MAM内部核对。

日志/资源快照为 `2026-09-11T03:34:28+08:00`。14路更新较上次全部前进，最新日志距采样0.1–8.4秒，未见Traceback/CUDA error/OOM/RESOURCE_EXHAUSTED错误。全部仍未达到20k，无提前结束，本轮无清理或归档。

| host/GPU | config / seed | PID | MAM job | 最新 updates | 最新可见 loss@step | s/update | 剩余 ETA |
| --- | --- | ---: | --- | ---: | --- | ---: | --- |
| wuwen-1/0 | rearrange full t+1 / 0 | 4186829 | `89dcc92f-365e-409a-87d3-e6e82b66adba` | 约 18.6k | 未落盘 | 3.7 | 约 1h29m |
| wuwen-1/1 | rearrange full t+30 / 0 | 4186841 | `db46bdd0-0ec2-41c1-9c98-baca9ffd6f5b` | 约 18.7k | 未落盘 | 3.7 | 约 1h23m |
| wuwen-1/2 | rearrange serial lag30 / 0 | 9003 | `d682fab7-3cbc-4b7e-a31a-b959bbd2695c` | 约 18.5k | 未落盘 | 3.7 | 约 1h34m |
| wuwen-1/3 | rearrange no-memory / 0 | 4186839 | `2774d038-5a23-4184-b16a-92fa1fd88019` | 约 18.4k | 未落盘 | 3.8 | 约 1h44m |
| wuwen-1/4 | put-back full t+1 / 0 | 12435 | `463092be-02b4-4bfa-bf12-8eae2416a244` | 约 17.6k | 0.0006@17600 | 3.8 | 约 2h30m |
| wuwen-1/5 | put-back full t+30 / 0 | 12436 | `6e2601ea-e091-4e63-9c31-e90895ca5ffe` | 约 18.1k | 0.0007@18000 | 3.7 | 约 2h00m |
| wuwen-1/6 | rearrange full t+1 / 1 | 4186835 | `95a88ee3-1a90-4e2e-baa1-50a1cd6f4eb0` | 约 18.9k | 未落盘 | 3.7 | 约 1h07m |
| wuwen-1/7 | rearrange full t+30 / 1 | 4186832 | `fa1d8437-1fb7-48a5-8d37-2233e8e06767` | 约 19.0k | 未落盘 | 3.7 | 约 1h01m |
| 本机/0 | put-back full t+30 / 2 | 2944062 | `dcb7d214-5351-4301-b0cd-1bac56f59de3` | 约 11.1k | 0.0012@11100 | 3.6 | 约 9h01m |
| 本机/1 | put-back full t+1 / 2 | 2918573 | `ee13298c-d10c-4fa4-9be9-875b417fb9a1` | 约 11.4k | 0.0011@11300 | 3.7 | 约 8h56m |
| 本机/4 | rearrange full t+1 / 2 | 2467720 | `b3d46ac6-b2b7-4ea2-b3ad-df74a2bdac7e` | 约 16.3k | 0.0008@16200 | 3.7 | 约 3h49m |
| 本机/5 | rearrange full t+30 / 2 | 2467721 | `0c82949f-f5c6-4772-aea6-1967e9cc2680` | 约 16.1k | 0.0009@16000 | 3.7 | 约 4h03m |
| 本机/6 | put-back full t+1 / 1 | 2467722 | `f04d1b9c-4a77-4034-ac6c-c7240d9b20a8` | 约 16.3k | 0.0007@16200 | 3.7 | 约 3h48m |
| 本机/7 | put-back full t+30 / 1 | 2467723 | `3e67c9de-fc4f-4a94-a2da-7dccbdec9b2e` | 约 16.1k | 0.0007@16100 | 3.7 | 约 4h00m |

kit为日志三位有效数字取整；ETA按近期速率估计并四舍五入至分钟，不计最终保存。当前约3.6–3.8秒/update。wuwen-1预计今日04:36–06:05完成更新，当前未见超出12:00预留截止时间风险；本机GPU4–7约07:23–07:38，GPU0/1约12:30–12:36完成更新。

远端GPU4/5各176/180条、本机GPU0/1各111/113条、本机GPU4/5/6/7各162/160/162/161条已落盘loss/grad_norm/param_norm全部有限。最新完整标量：

| host/GPU | Step | loss | grad_norm | param_norm |
| --- | ---: | ---: | ---: | ---: |
| wuwen-1/4 | 17600 | 0.0006 | 0.0301 | 1804.3630 |
| wuwen-1/5 | 18000 | 0.0007 | 0.0344 | 1804.2440 |
| 本机/0 | 11100 | 0.0012 | 0.0384 | 1803.8700 |
| 本机/1 | 11300 | 0.0011 | 0.0355 | 1803.9907 |
| 本机/4 | 16200 | 0.0008 | 0.0338 | 1804.4349 |
| 本机/5 | 16000 | 0.0009 | 0.0354 | 1804.3932 |
| 本机/6 | 16200 | 0.0007 | 0.0307 | 1804.2756 |
| 本机/7 | 16100 | 0.0007 | 0.0336 | 1804.1643 |

以上为区间均值证据，不扩展为每个update原始loss证明。旧远端GPU0/1/2/3/6/7的Step标量仍各为零，有限loss尚未证实；保持stdout缓冲边界，不注入/重启。

两机HEAD均为 `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，git status为空。未改运行树或参数，未重复smoke和恢复验证。结束后按任务核对退出状态、唯一20000 BF16 checkpoint/metadata及完整参数/无optimizer/恢复要求、登记进程及子进程退出和显存释放；仅清理确认属于本任务的残留。wuwen-1训练自然结束、保存释放后整机不再使用，直到另行允许。实际20000 checkpoint的GPU恢复/评测只能安排本机空闲卡，不能抢占仍在训练的卡；可先在本机进行不占GPU的完整性检查。本轮未启动额外任务。

## GPU0 配对项启动（发布 task 的 16:11 授权段）

已读取发布 `7a4f4bcbc54871434f70a43e1be6dd72ee068b97` 的 GPU0 放行要求。实际启动主机时钟为 `2026-09-10T16:10:23+08:00`，启动既定 Q2 put-back full_t_plus_30 seed2，与 GPU1 的 t+1 seed2 配对，不扩展实验清单。

启动前本机 GPU0 已用1 MiB、空闲81,038 MiB、利用率0；MemAvailable=886,691,171 KiB。固定 worktree HEAD=`d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，git status 为空；解释器可执行，put-back norm SHA-256=`7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261`。独立日志和 checkpoint exp 目录均未存在，未覆盖或混写。

- host：`is-dcfi2kjdq7g3k6aa-devmachine-0`；GPU0；PID/session ID：`2944062`；start_ticks：`27664648`。
- MAM job：`dcb7d214-5351-4301-b0cd-1bac56f59de3`；16:10:52 登记实时状态 running。
- config：`pi05_rmbench_put_back_block_full_t_plus_30`；seed2；exp_name：`memory20k_e7e5ac54_put_back_full_t_plus_30_s2`。
- 实际日志：`/mnt/public/xcj/Projects/openpi/logs/memory20k_e7e5ac54_put_back_full_t_plus_30_s2.log`。
- 最终 checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s2/20000`。

沿原 d10 配置：单GPU batch32、实际20k updates、同 pi05_base/demo_clean_state/norm、H50/K30，save_full_state=False、save_dtype=bfloat16、save_interval=20000，仅最终模型和metadata；未重跑门禁或改源码。用一次性 subprocess.Popen、start_new_session=True、stdin=DEVNULL、排他创建日志、stderr=STDOUT、close_fds=True 脱离工具会话。实际 command/cwd/env：

```bash
cd /mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi
export OPENPI_DATA_HOME=/mnt/public/cache/openpi
export HF_HUB_OFFLINE=1
export HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.90
export PYTHONDONTWRITEBYTECODE=1
unset JAX_PLATFORMS PYTHONPATH
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_30 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_30_s2 --seed=2 --no-wandb-enabled
```

首次检查于 `2026-09-10T16:26:41+08:00` 完成，仅检查新增 GPU0。通过 `mam job status dcb7d214-5351-4301-b0cd-1bac56f59de3` 获取实时 JSON：running、checked_at=16:26:41，原 PID/boot_id/start_ticks 身份匹配；进程状态 R，cwd、实际 command、GPU/env 与登记一致，日志确认 local_batch_size: 32。

首个真实 optimizer update 日志为16:14:59（1 update）；最新16:26:32为135 updates，最近129/132/135 updates均约3.7秒/update，日志剩余ETA为20:13:14（约20h13m，预计9月11日12:40左右完成更新，不计最终保存）。Step100已实际落盘 `grad_norm=1.1468, loss=0.1493, param_norm=1802.3861`，三项均有限；这是区间均值证据。未见Traceback/CUDA/OOM等错误，最新日志距采样8.9秒。

GPU0已用73,405 MiB、空闲7,633 MiB、利用率100%、59°C；MemAvailable=876,849,534 KiB（约836.2 GiB）。HEAD仍为d10cc01完整SHA，git status为空，put-back norm hash保持7a014e42...。本次启动登记与首次真实更新/有限loss检查均完成；原十三路本轮未提前复查，未改源码/参数或重复门禁。该次首次检查约定16:57合并巡检（已完成，见首节）；实时结构化状态继续使用job status，不解析job list表格。

## 15:41 授权的本机 GPU1：put-back t+1 seed2 启动

已读发布 task `a3a5c390b8daac7f74637988edd712142c5c16af` 末节授权，于 `2026-09-10T15:42:52+08:00` 启动既定 Q2 剩余的 put-back full_t_plus_1 seed2。启动前 GPU1 实测已用 1 MiB、空闲 81,038 MiB、利用率 0；MemAvailable=885,382,269 KiB。固定树 HEAD 为 `d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，git status 为空，解释器可执行；put-back norm SHA-256 为 `7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261`。独立 log/checkpoint exp 路径均未存在。

- host：`is-dcfi2kjdq7g3k6aa-devmachine-0`；GPU1；PID/session ID：`2918573`；start_ticks：`27499635`。
- MAM job：`ee13298c-d10c-4fa4-9be9-875b417fb9a1`，15:43:16 登记实时确认 running。
- config：`pi05_rmbench_put_back_block_full_t_plus_1`；seed2；exp_name：`memory20k_e7e5ac54_put_back_full_t_plus_1_s2`。
- log：`/mnt/public/xcj/Projects/openpi/logs/memory20k_e7e5ac54_put_back_full_t_plus_1_s2.log`。
- 最终 checkpoint：`/mnt/public/xcj/Projects/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s2/20000`。
- 原 config/环境：batch32、实际20k updates、H50/K30、同 pi05_base/demo_clean_state/norm，save_full_state=False、save_dtype=bfloat16、save_interval=20000；未改源码或重复50step。

实际 cwd 为本任务 d10 固定 openpi worktree；通过一次性 subprocess.Popen、start_new_session=True、stdin=DEVNULL、stdout=独占创建的日志、stderr=STDOUT、close_fds=True 脱离短工具会话。实际 command/env：

```bash
cd /mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi
export OPENPI_DATA_HOME=/mnt/public/cache/openpi
export HF_HUB_OFFLINE=1
export HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.90
export PYTHONDONTWRITEBYTECODE=1
unset JAX_PLATFORMS PYTHONPATH
CUDA_VISIBLE_DEVICES=1 .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_1 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_1_s2 --seed=2 --no-wandb-enabled
```

15:58:21 合并快照首次确认：新路原 PID 身份、cwd/command/env 均匹配，日志确认 local_batch_size: 32，15:58:12 已完成 119 次真实 optimizer update，近期 3.7 秒/update，剩余 ETA 约 20h25m。Step100 实际落盘 grad_norm=1.1383、loss=0.1523、param_norm=1802.3861，三项均有限。GPU1 已用 73,405 MiB、空闲 7,633 MiB、利用率100%、67°C，未见训练错误；未提前轮询原十二路。截至该15:58快照，配对项未获授权；最新GPU0授权/启动见报告首节。

## 本机四路启动留痕（10:39 授权，10:58 已验收）

本机 host=`is-dcfi2kjdq7g3k6aa-devmachine-0`。四路均于 `2026-09-10T10:42:31+08:00` 启动并登记本机 MAM job；全部来自原 Q2 预算。10:40–10:42 启动核验：GPU4–7 各占 1 MiB、空闲 81,038 MiB、利用率 0，RAM MemAvailable=942,653,119 KiB（约 899 GiB）；四组 checkpoint/log 路径均不存在。固定 worktree HEAD=`d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，git status 为空；解释器、两份已验收 norm 沿用原环境。

put-back norm SHA-256=`7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261`；rearrange norm SHA-256=`5d84df27e9fce3c6ec28585319ed293fa59fc1822063ecfa0e95c5bf4478606b`。本机启动轮次未重跑 50gate、重建环境或变更源码，也未另读远端进度/标量/显存；入口 mam task status 当时会自动探测已登记 PID。本节仅保留已获 Manager 接受的 10:58 本机启动结果；本次十二路最新状态见上表。

`10:58:36+08:00` 首次验证完成：四个原 PID 均存活，`start_ticks=25697503` 与 MAM 登记身份一致，实际 cwd/解释器、GPU 编号、seed 与命令一致；四路日志均确认 batch32。首个 optimizer progress：GPU4=10:48:08，GPU5=10:48:14，GPU6/7=10:47:30。各路均已越过 100 updates，Step 100 的 loss/grad_norm/param_norm 已实际落盘且全部有限。

| 本机 GPU | config / seed | PID | MAM job | 10:58 updates | Step-100 loss | 10:58 稳定 s/update | 10:58 剩余 ETA |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| 4 | rearrange full t+1 / 2 | 2467720 | `b3d46ac6-b2b7-4ea2-b3ad-df74a2bdac7e` | 116 | 0.1497 | 3.706 | 约 20h28m |
| 5 | rearrange full t+30 / 2 | 2467721 | `0c82949f-f5c6-4772-aea6-1967e9cc2680` | 113 | 0.1482 | 3.749 | 约 20h43m |
| 6 | put-back full t+1 / 1 | 2467722 | `f04d1b9c-4a77-4034-ac6c-c7240d9b20a8` | 131 | 0.1521 | 3.703 | 约 20h26m |
| 7 | put-back full t+30 / 1 | 2467723 | `3e67c9de-fc4f-4a94-a2da-7dccbdec9b2e` | 131 | 0.1491 | 3.732 | 约 20h36m |

Step-100 完整标量：GPU4 `grad_norm=0.9720, loss=0.1497, param_norm=1802.3862`；GPU5 `grad_norm=0.9748, loss=0.1482, param_norm=1802.3861`；GPU6 `grad_norm=1.1473, loss=0.1521, param_norm=1802.3861`；GPU7 `grad_norm=1.1548, loss=0.1491, param_norm=1802.3861`。这是四路各自首个已落盘区间均值，未用“没有 nan 文本”替代数值证据。

10:58 启动检查的稳定耗时取 30 updates 以后最近 16 个 progress 间隔的每 update 耗时中位数，ETA=(20000−当前进度)×稳定耗时；未用初始加载/编译阶段外推。预计完成落在 `2026-09-11 07:24–07:42+08:00`，仍以之后稳定吞吐及最终保存为准。10:58 资源：本机四卡各用 73,406 MiB、空闲 7,633 MiB、利用率 100%，温度 60–72°C；MemAvailable=877,748,034 KiB（约 837.1 GiB）。固定树 HEAD 再次核验为 d10，git status 为空。

实际启动采用一次性 `subprocess.Popen`，`start_new_session=True`、`stdin=DEVNULL`、`stdout=各自日志`、`stderr=STDOUT`、`close_fds=True`；日志通过排他 `open('x')` 创建。四 PID 的 session ID 均等于自身 PID，脱离启动工具会话。未创建通用 launcher 文件。以下为实际 command/cwd/env：

```bash
cd /mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi
export OPENPI_DATA_HOME=/mnt/public/cache/openpi
export HF_HUB_OFFLINE=1
export HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.90
export PYTHONDONTWRITEBYTECODE=1

CUDA_VISIBLE_DEVICES=4 .venv/bin/python -u -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_1_s2 --seed=2 --no-wandb-enabled
CUDA_VISIBLE_DEVICES=5 .venv/bin/python -u -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_30 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_30_s2 --seed=2 --no-wandb-enabled
CUDA_VISIBLE_DEVICES=6 .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_1 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_1_s1 --seed=1 --no-wandb-enabled
CUDA_VISIBLE_DEVICES=7 .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_30 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_30_s1 --seed=1 --no-wandb-enabled
```

与原 config 相同：batch32、20,000 optimizer updates、H50/K30、单卡、从 pi05_base 初始化，`save_interval=20000`、`save_full_state=False`、`save_dtype=bfloat16`；只变 seed 与 exp_name。两份 sim 数据仍为 demo_clean_state。

| 本机 GPU | 独立 exp_name | 完成后 checkpoint（相对共享 `/mnt/public/xcj/Projects/openpi/`） |
| --- | --- | --- |
| 4 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s2` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/memory20k_e7e5ac54_rearrange_full_t_plus_1_s2/20000` |
| 5 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s2` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s2/20000` |
| 6 | `memory20k_e7e5ac54_put_back_full_t_plus_1_s1` | `checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s1/20000` |
| 7 | `memory20k_e7e5ac54_put_back_full_t_plus_30_s1` | `checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s1/20000` |

四份实际日志为 `/mnt/public/xcj/Projects/openpi/logs/<上表 exp_name>.log`。本节启动时 GPU0/1 分配 F0、GPU2/3 分配 wash；当前分配以本次巡检节的 Manager 更新为准。

## 远端八路启动留痕

八个正式单卡 batch32、20,000-update run 已从本任务独立 worktree/解释器、独立 exp_name 可靠 detach，并登记到 MAM；当前 PID、job 和进度见本次十二路表。CPU firstfull `6a32847`、full/serial GPU50/restore 和 put-back loader 的授权沿发布 task 执行。GPU4/5 于 08:47 使用 `.venv/bin/python -u -B` 启动，旧六路保持实际 `.venv/bin/python -B`。

八项实际使用 `CUDA_VISIBLE_DEVICES=<分配卡>`、`XLA_PYTHON_CLIENT_MEM_FRACTION=0.90`、`HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot`、`OPENPI_DATA_HOME=/mnt/public/cache/openpi`，均从本任务固定 worktree 的独立解释器启动。Manager 已告知主树合入 `a869498` 并获 CPU GO，本运行树继续固定 d10。最新远端八路状态见本次合并巡检表。

## workspace、各库交付 commit

- openpi worktree：`/mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi`
- branch：`task/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe`；HEAD/base：`d10cc01d44c10e5ed0cd8c228d9409dd6cabac50`，未修改源码。
- `.venv/bin/python scripts/worktree_env_smoke.py` 在本机和 `wuwen-1` 均通过；两端 editable `openpi` / `openpi_client` 都解析到本任务 worktree。远端解释器为该树的 `.venv/bin/python`。

## CPU、数据和 Memory v1 核对

- CPU CLI 已用 `CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu` 调用 `scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --help`。确认 `--exp-name`、`--seed`、`--no-wandb-enabled` 可用；本批 config 默认 batch=32、`num_train_steps=20000`、`save_interval=20000`、`save_full_state=False`、`save_dtype=bfloat16`、`fsdp_devices=1`。
- 新 sim 输入没有 fallback 到 `demo_clean`：六个 config 分别绑定 `rearrange_blocks_demo_clean_state_shared_memory` 或 `put_back_block_demo_clean_state_shared_memory`。转换器 `validate_converted_dataset` 会拒绝 `task_config != demo_clean_state`；两份 sidecar 均记录 `task_config: demo_clean_state` 和相应的 `raw_metadata_root`。
- LeRobot 根 `HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot` 在本机和远端均可由 metadata API 打开：rearrange 50 episodes / 20,103 frames，put-back 50 episodes / 17,588 frames。两份 sidecar 在远端可读；其 `M` query / `M+1` series 留痕与任务要求一致。
- 远端 CPU 下六个 config 都可解析并创建 MemoryDataAdapter，sidecar 路径指向本树 `data/memory_v1/rmbench/<repo_id>/episode_memory.json`。rearrange 的 robot-only norm 可读且只含 `state`、`actions`，每个 mean/std/q01/q99 为 14 维；base 参数完成标记可读。

## 03:34:28 两机资源快照

| host / GPU | 每卡已用 / 空闲 MiB | 利用率 | 温度 | 主机 MemAvailable |
| --- | --- | --- | --- | --- |
| wuwen-1 / 0–7 | 73,489–73,507 / 7,543–7,561 | 全部100% | 51–68°C | 831,290,397 KiB（约 792.8 GiB） |
| 本机 / 0,1,4–7 | 73,405–73,406 / 各7,633 | 全部100% | 58–71°C | 877,348,620 KiB（约 836.7 GiB） |

共享/mnt/public可用9,994,901,651,456 bytes（约 9.09 TiB），未见资源压力；无异常扩查。

历史准备快照：

采样于 `2026-09-10T07:53:19+08:00`，只读检查、未分配 GPU：`wuwen-1` 的 GPU0..7 均为 A100-SXM4-80GB，单卡 `memory.used=4 MiB`、`memory.free=81,046 MiB`、utilization=0。主机可用 RAM 895 GiB，`/mnt/public` 可用 9.2 TiB；`logs/` 可写且 `/usr/bin/setsid` 存在。此为快照，正式每一路启动前仍要重新检查实际显存，且不根据进程列表推断空闲。

## 实际启动上下文

所有命令从 `wuwen-1` 上的固定树执行；不设 `JAX_PLATFORMS=cpu`，不传 `--overwrite` / `--resume`，所以已有目录会拒绝混写。`scripts/train.py` 的现有 checkpoint metadata 会保存实际 command、cwd、commit、resolved TrainConfig、dataset metadata 与 sidecar metadata。

```bash
cd /mnt/public/xcj/Projects/workspace/e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe/openpi
export OPENPI_DATA_HOME=/mnt/public/cache/openpi
export HF_HUB_OFFLINE=1
export HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.90
export PYTHONDONTWRITEBYTECODE=1
```

每条实际命令用 `nohup setsid` 脱离短 session；启动后记录 shell 返回的真实 PID，并从管理机执行对应的 `mam job add e7e5ac54-2f5c-4f46-9210-6c2a51f7f4fe --host wuwen-1 --pid <pid> --note "..."`。

```bash
# GPU0
CUDA_VISIBLE_DEVICES=0 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_1_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_1_s0.log 2>&1 &

# GPU1
CUDA_VISIBLE_DEVICES=1 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_30 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_30_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0.log 2>&1 &

# GPU2
CUDA_VISIBLE_DEVICES=2 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_serial_lag30 --exp-name=memory20k_e7e5ac54_rearrange_serial_lag30_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_serial_lag30_s0.log 2>&1 &

# GPU3
CUDA_VISIBLE_DEVICES=3 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_no_memory --exp-name=memory20k_e7e5ac54_rearrange_no_memory_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_no_memory_s0.log 2>&1 &

# GPU4 — 08:47 实际命令，PID 12435
CUDA_VISIBLE_DEVICES=4 nohup setsid .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_1 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_1_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_put_back_full_t_plus_1_s0.log 2>&1 &

# GPU5 — 08:47 实际命令，PID 12436
CUDA_VISIBLE_DEVICES=5 nohup setsid .venv/bin/python -u -B scripts/train.py pi05_rmbench_put_back_block_full_t_plus_30 --exp-name=memory20k_e7e5ac54_put_back_full_t_plus_30_s0 --seed=0 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_put_back_full_t_plus_30_s0.log 2>&1 &

# GPU6
CUDA_VISIBLE_DEVICES=6 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_1_s1 --seed=1 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_1_s1.log 2>&1 &

# GPU7
CUDA_VISIBLE_DEVICES=7 nohup setsid .venv/bin/python -B scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_30 --exp-name=memory20k_e7e5ac54_rearrange_full_t_plus_30_s1 --seed=1 --no-wandb-enabled </dev/null >logs/memory20k_e7e5ac54_rearrange_full_t_plus_30_s1.log 2>&1 &
```

## 八个独立输出

所有相对路径以上述 fixed worktree 为根；`checkpoints` 与 `logs` 是共享源树软链接，因此正式产物实际保留在 `/mnt/public/xcj/Projects/openpi/`。八项已放行 run 均使用下列独立输出；GPU4/5 已在其独立目录启动，不与其他 run 混写。

| GPU | config / seed | exp_name | checkpoint（完成后唯一的 20000） | log |
| --- | --- | --- | --- | --- |
| 0 | rearrange full t+1 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s0` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/memory20k_e7e5ac54_rearrange_full_t_plus_1_s0/20000` | `logs/memory20k_e7e5ac54_rearrange_full_t_plus_1_s0.log` |
| 1 | rearrange full t+30 / 0 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s0` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0/20000` | `logs/memory20k_e7e5ac54_rearrange_full_t_plus_30_s0.log` |
| 2 | rearrange serial lag30 / 0 | `memory20k_e7e5ac54_rearrange_serial_lag30_s0` | `checkpoints/pi05_rmbench_rearrange_blocks_serial_lag30/memory20k_e7e5ac54_rearrange_serial_lag30_s0/20000` | `logs/memory20k_e7e5ac54_rearrange_serial_lag30_s0.log` |
| 3 | rearrange no-memory / 0 | `memory20k_e7e5ac54_rearrange_no_memory_s0` | `checkpoints/pi05_rmbench_rearrange_blocks_no_memory/memory20k_e7e5ac54_rearrange_no_memory_s0/20000` | `logs/memory20k_e7e5ac54_rearrange_no_memory_s0.log` |
| 4 | put-back full t+1 / 0 | `memory20k_e7e5ac54_put_back_full_t_plus_1_s0` | `checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000` | `logs/memory20k_e7e5ac54_put_back_full_t_plus_1_s0.log` |
| 5 | put-back full t+30 / 0 | `memory20k_e7e5ac54_put_back_full_t_plus_30_s0` | `checkpoints/pi05_rmbench_put_back_block_full_t_plus_30/memory20k_e7e5ac54_put_back_full_t_plus_30_s0/20000` | `logs/memory20k_e7e5ac54_put_back_full_t_plus_30_s0.log` |
| 6 | rearrange full t+1 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_1_s1` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_1/memory20k_e7e5ac54_rearrange_full_t_plus_1_s1/20000` | `logs/memory20k_e7e5ac54_rearrange_full_t_plus_1_s1.log` |
| 7 | rearrange full t+30 / 1 | `memory20k_e7e5ac54_rearrange_full_t_plus_30_s1` | `checkpoints/pi05_rmbench_rearrange_blocks_full_t_plus_30/memory20k_e7e5ac54_rearrange_full_t_plus_30_s1/20000` | `logs/memory20k_e7e5ac54_rearrange_full_t_plus_30_s1.log` |

下一检查：`2026-09-11T04:32:00+08:00`，远端八路与本机GPU0/1/4–7合并为十四路巡检，由 Manager 按计划唤醒。若收到 MAM job attention 或异常通知则提前处理。十四路的 20k 完成、唯一 20000 BF16 checkpoint、完整参数/无 optimizer/恢复验证与评测交接仍待训练结束后完成。
