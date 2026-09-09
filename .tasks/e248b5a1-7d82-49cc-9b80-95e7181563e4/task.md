# 实验后续资产：swap/cover/battery状态版与drawer训练数据恢复

## 目标

为论文第二批训练准备缺失资产。首批rearrange/put-back/pi05 base已由81d2任务验收，不能重复复制。你仅负责有界定位、传输和完整性核验，不改代码、不占GPU、不创建代码worktree。所有文件落稳定共享cache，不落临时worktree成为资产源。

## 范围与来源

插入最高优先级的小额补核：data任务7c8fbc25报告rearrange/put-back完整converted已可用，但原始data/<task>/demo_clean_state的scene_info.json/language_annotation.json尚未恢复，也缺每集末尾action的raw独立核对。先从旧集群准确源恢复两任务50ep的小JSON/配置等metadata到主RMBench对应data稳定位置，保留结构；不要复制demo_clean。rearrange需empty_mat_side、block1_place、press_return、language_annotation.segment_4；put-back需origin_mat_name、center_pick/center_place/button_return。对于含图像的大HDF5，优先在源端用已有h5py环境只读导出各集robot joint/action相关数组的shape、首末两行及来源路径（必要时source文件时间/大小），生成小JSON供dataagent对照，避免为核对末尾动作先传整套图像。若源端无法读取或权限不通，给准确缺口再裁定；这个补核不要求从raw重转已恢复数据。每个小项完成马上同步Manager，后续再继续swap/cover/battery/drawer。

仿真需swap_blocks、cover_blocks、battery（准确任务名以RMBench实验记录为准）的demo_clean_state原始或converted标签数据。优先已有可追溯LeRobot converted，核对source_data_config/key_state_config/episode metadata，确认详细子任务边界可读后才传输。demo_clean缺metadata，明确不能fallback；不存在就列缺失，不自造标签。只读RMBench实验记录/旧训练metadata确定准确repo_id，再检查已知HF cache父目录，避免全盘递归。

真机drawer sorting对应RMBench/policy/pi05/checkpoints/pi05_x1pro_drawer_sorting_s2m_{full_state,serial_soft}两模型，旧完整训练集119ep converted最初调查本地缺失；本地table_clean原始5ep是offline回放输入，不能冒充完整训练集。核对实际旧metadata里的repo_id、state/action、字段和目录，恢复已存在且需要的完整训练集及前序metadata。先检查本地是否已有，避免重复。

传输经ssh wuwen-nx-aic，从zx-data rsync到/mnt/public对应镜像路径。nx和本集群共享/mnt/public；zx-data和wuwen-11共享旧/mnt/public3。至多2条约10MB/s链路，第二条开始至少晚60秒；当前前任务链路已结束，仍在启动前检查自有MAM jobs避免和别任务争用。单次多dataset可以一条链顺序传，不用大量后台小rsync。预计>1h用mam job登记真实nx host/PID，记录源、目标、开始、结束、校验，不登记ssh父端冒充实际进程。

## 交付与收尾

原始小metadata的本集群统一目标为/mnt/public/xcj/Projects/RMBench/data/<task>/demo_clean_state，与已完成rearrange/put-back一致。源端/mnt/public3/xcj/rmbench路径保留在provenance即可，后续swap/cover/battery不要在本地另造/mnt/public/xcj/rmbench数据树。若已开始复制到该旧镜像父路径，待该项传输完成校验后再将仅本task新建的小标注目录移到主RMBench data，核对无现有冲突并清理空目录；不重传、不影响正在运行的rsync。

每项先报确切来源、预计字节量及metadata是否充分；必要资产可直接传输，不需再问Manager。每项完成checksum dry-run与episode/frame计数后及时报ready，不等全部。报告实际路径、来源、数量、可读metadata及缺口，不声称训练语义/模型加载已通过。引用首任务经验即可，不复制旧日志。

report按当前task_revision发布；清理本task临时partial/transfer脚本/日志（关键校验结果已摘要进report），归档jobs，workspace应可直接由mam task archive清除，避免上次asset-recovery未登记目录阻塞归档。共享正式资产保留。不自行派agent。
