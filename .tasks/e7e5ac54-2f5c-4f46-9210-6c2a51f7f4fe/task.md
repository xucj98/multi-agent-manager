# Memory首批正式20k训练执行

## 目标、工作区与当前授权

你负责首批已计划的八个单GPU20k训练的执行、监控、checkpoint验收和评测交接。Manager统一判断代码/数据验收，其他owner继续实施；你不修改模型、loader、converter、schema或MAM实现，不重跑整个历史实验，不自行派agent。

先按MAM AGENTS/README读取发布要求，用mam workspace add在本task创建openpi worktree，base=d10cc01d44c10e5ed0cd8c228d9409dd6cabac50；读取openpi AGENTS。独立环境由既有一键入口创建，复用共享assets/data/checkpoints软链接，不挂别人的PYTHONPATH。你本机管理、通过ssh wuwen-1执行训练；两端共享/mnt/public。所有正式进程使用你自己的固定worktree/解释器，运行期间不修改该树的源码或切换版本。

当前只授权CPU准备、环境/CLI/数据路径核对、确定八条可复制命令和输出目录。GPU正式开跑待Manager告知相应模型路径已通过独立CPU review及实际50step保存/恢复；不自行抢跑，不向用户再次请求许可。通过一条路径就能分阶段开其对应训练，不捆绑wash/live。

## 第一批配置和资源

资源：wuwen-1 GPU0..7每卡一个训练。本机GPU0跑F0、GPU1跑训练smoke，不使用。启动前查实际显存，不能只靠看不到其他人的进程判断空闲；不终止别人的进程。每模型单卡batch32、20,000次optimizer update，H50/K30，save_full_state=False、save_dtype=bfloat16，最终只留20000一个checkpoint及assets/metadata。其余优化器参数沿既定config，不为命令长度手写全部默认参数。若OOM或训练不稳定，保留失败事实及时报告Manager，不能静默改变受控batch/模型/数据或混写重试目录。

| GPU | training config | seed |
| --- | --- | --- |
| 0 | pi05_rmbench_rearrange_blocks_full_t_plus_1 | 0 |
| 1 | pi05_rmbench_rearrange_blocks_full_t_plus_30 | 0 |
| 2 | pi05_rmbench_rearrange_blocks_serial_lag30 | 0 |
| 3 | pi05_rmbench_rearrange_blocks_no_memory | 0 |
| 4 | pi05_rmbench_put_back_block_full_t_plus_1 | 0 |
| 5 | pi05_rmbench_put_back_block_full_t_plus_30 | 0 |
| 6 | pi05_rmbench_rearrange_blocks_full_t_plus_1 | 1 |
| 7 | pi05_rmbench_rearrange_blocks_full_t_plus_30 | 1 |

GPU6/7使用研究计划已经批准的wash等待替补：Q2的配对seed1，属于原72次预算，不增加无目的实验。wash v3正在转换，其训练注册配置另行完成；下一批空闲卡优先wash。可先准备这八项，不把未验收wash放进当前八项。

不同config/seed每次使用独立、带明确实验组和seed的exp_name，已有输出拒绝混写；失败重试新目录。使用现有scripts/train.py，不开发通用队列/launcher系统。必要的实际启动命令和分配表写本task report即可，由MAM发布；长进程用可靠detach启动，不依赖短tool session存活。

## 数据、norm和已验收事实

新仿真数据只来自demo_clean_state，不fallback demo_clean。LeRobot根为/mnt/public/xcj/cache/huggingface/lerobot；两任务后缀_demo_clean_state_shared_memory。sidecar在主openpi/data/memory_v1/rmbench/<repo_id>/。数据/配置已独立验收：sim M个图像/query与M+1低维series；robot动作已对齐next frame，offset0，不自行二次移位。full P2共用mask/机器人目标/norm，仅phase目标t+j+1对重复t+30。serial固定lag30/current query/独立argmax，no-memory过滤为robot-only绑定。

base在/mnt/public/cache/openpi/openpi-assets/checkpoints/pi05_base。新机器人norm只含state/actions各14维，memory one-hot identity，不参与stats。rearrange资产在openpi/assets/memory_v1/rmbench_rearrange_blocks_robot；put-back对应资产由实施ownerad6bb77e生成，实际就绪后才能用。不复制/重算每种目标时序的stats，也不能把rearrange统计用到put-back。

当前源版本d10包含CPU实现ffa308d、CLI模板修复5e3bfd6、自包含factory/YAML修复d10。Banach任务9b73b590做独立review；Bernoulli任务ad6bb77e在本机GPU1提供full/serial各50step模型证据。core/数据/actual tokenizer/P2 loss和梯度/serial条件/更新计数已经有通过证据，你不重复整个测试。runtime真实transforms→Context也已7项通过，live执行器修复不阻塞sim训练。

## 启动、留痕、监控和交接

开跑前交准备报告：独立解释器两端可运行、实际checkout SHA、八条命令、exp_name/输出路径、数据/norm就绪状态、可用GPU快照；相对路径按项目根，来源命令中实际环境设置如GPU/JAX/HF根要可还原。Manager放行后立即分阶段启动，每进程用mam job add登记wuwen-1真实PID/用途。

每步沿现有机制保存真实command/cwd/git commit、resolved TrainConfig、上游数据/sidecar metadata/config；不复制代码或新增重复runtime/provenance。首次检查确认不是仅服务启动：实际optimizer更新前进、loss有限、batch32/单GPU与配置一致。根据稳定step耗时估计剩余时间，之后每小时检查一次，不频繁轮询；异常及时处理。agent可报告阶段结果，Manager在计划检查时机唤醒；进程必须保持可靠detach且MAM登记。

完成核对20,000更新、唯一20000 checkpoint、完整参数shape/BF16/无optimizer、assets与metadata、仅checkpoint路径可恢复。base约3.35B参数，裸BF16约6.71GB，不按旧12GB估算硬凑大小。随后向Manager/评测owner提供checkpoint和metadata；每个正式eval仍需自身2rollout video/no-video smoke后100，不在本任务未经安排启动eval。

记录实际结果、清理本任务临时smoke/无用文件后archive已停止job。正式checkpoint保留共享原repo路径；worktree等任务验收且无活跃job后由Manager归档。report包括task_revision、workspace/完整commit、完成/未完成、job及输出路径、下一检查时间。不要修改其他task的task.md/report.md。
