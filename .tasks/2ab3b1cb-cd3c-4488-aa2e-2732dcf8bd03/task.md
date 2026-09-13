# P0 全量既有轨迹事实抽取：消费状态与按压事件

使用 gpt-5.6-terra/max。科学问题/判据由 Manager 定义，执行者只实现只读解析和事实统计，不判断算法瓶颈、不改论文/训练/生产代码。读 MAM AGENTS/README/.local，再 mam task show 本 TASK-ID。成果放独立 workspace，无业务改动不必创建业务 worktree。不得新跑 rollout/GPU、下载视频或修改原始文件。

## 已有证据与范围
原始受验快照 /root/Documents/task-state-vla-paper/docs/analysis/accepted_results_20260913.json 中 put_back per_frame(J)/endpoint(T)，train0/1/2，eval0 共600完整episode。索引 /mnt/public/xcj/Projects/workspace/f987cfb5-284b-4074-b0fb-726b969591c7/audit/trace_index.json 可用于路径定位，但核心值必须来自原始 episode_diagnostics.jsonl 和 scheduler stdout，按 processes.jsonl 的 scheduler command→episode context映射。不要把process ordinal当episode ID，不把每query多次trace当独立样本。
Manager已检查 J train0 eval0 episode0：q8 observed_progress completed=240、phase chunk_completed update为move_block_back_to_origin_mat，第9个query input IDs=[3,2]；整集press_count=0、仅center_ready事件。这只是进入cache和被下一query传入的事实，不能推断动作方向或因果。

## 冻结提取合同
1. 对每个episode，按query_id解析每query最终Memory v1 trace，并保留首次/最终logger时间、accepted_progress、observed_progress、actual_k、selected row、updates。记录各query实际输入phase/origin ID，以及previous completion update被next query input采用是否吻合。按该run冻结schema解码，不用凭空硬编码的类别索引。
2. 提取第一次 *实际作为query输入* 的move_block_back_to_origin_mat及对应上一chunk phase update；用前一已完成chunk的observed_progress.completed作为对齐边界。其之前是否有物理button_pressed事件和有效stage_transition（0→1）？对齐前必须核查execution_progress.completed计数单位与diagnostics event.step是否同一policy-row/logical-step轴，并用至少两个成功episode的末累计进度/episode length验证。若不能证明同轴，输出unknown，不做数值时间差。
3. per-episode分别记录：整集无有效按压但后续query已实际消费return状态；存在有效按压但首次消费return更早/同时/更晚；无return输入；未能可靠对齐。区分“预测行含return”“已写cache”“下一query实际输入return”；主统计只用最后一个。实际按压以事件和stage转移各保留，不把仅press_count或demo phase当真实完成。保留恰好同一步的tie，不随意排顺序。
4. 按6个模型×终态success/未按/浅按/其他分组，报告episode级分子分母；另给所有600episode分母的整体描述。不得用108个分层样本算发生率，不按有趣结果筛样本，不做显著性/因果宣称。解析失败不能丢弃，逐项列原因和数量。
5. 新增 machine-readable episode/query事实表及小CSV摘要、可重复脚本、README。每行原始路径/hash、query和event定位清晰；源码来源固定到实际冻结bridge/RMBench版本。可以 gzip 存机械大表。给两个成功、两个失败的完整对齐例，标明是例证。

交付 report+publish 后结束turn，MAM通知Manager。不要等待其他agent、改造trace logger或生成独立验证数据。先做这项零新增训练的分析，后续是否需要状态干预/新增字段由Manager裁决。
