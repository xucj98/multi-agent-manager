# 论文实验完成数的只读核验

用户要当前论文新增实验设计数、训练完成数、评测完成数。你负责原始产物的去重数量核验，Manager 独立核对论文计划并裁决口径。

先读 AGENTS/README/.local/README。只读不改实验或台账、不启停 job，不需要 worktree。证据存自己的 workspace。先回 CODEX_THREAD_ID 绑定。

范围：20260910 memory_chunk 新实验（不算旧pilot/F0/BF16部署验证、smoke、gate、失败重试）。核对 /mnt/public/xcj/Projects/openpi/checkpoints 下相关20k模型：Q2 12，能力baseline B共12（rearrange full以外serial/no-memory各3，putback serial/no-memory各3），wash full/serial各3共6，U full_initial双任务各3共6。这只是待验证假设，若发现额外计划或口径差异请报告。

训练完成必须20000产物及已验收记录可查，区分26/36等推测数字与真实证据；未完训练给实际step/预计时间仅当易查，不为ETA展开长分析。读MAM published reports/archived tasks与实际checkpoint，不把存在空目录当完成。

评估：本机 /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910；C共享 /mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910（ssh wuwen-4090-1）。核对正式完成100ep结果按 checkpoint/trainseed/evalseed 去重，本机与C镜像只算一次；重试/失败partial/smoke/gate不算。区分独立100ep批次数、至少完成一批的模型数、完成3个eval seed共300ep的模型数。列当前running批次数可用MAM+真实树证据。wash两项已完成5ep offline单列（训练集回放，不算闭环成功率），wash seed1/2与U目前可能仍训练。不要遍历巨大视频/模型内容。

交付简短可复核的分组计数及run/checkpoint manifest、采样时刻、未知项；report.md发布。若快速得到可靠数字先通知Manager，再收尾。不要等review或其他agent，完成结束turn由MAM唤醒。
