# 已交付：put-back 全量轨迹的消费状态与实际按压对齐事实审计

完成只读、全量抽取，未运行 rollout、训练、GPU 作业或下载视频，未改动 RMBench、robot-bridge、OpenPI、原始日志或论文。成果在独立 workspace：

`/mnt/public/xcj/Projects/workspace/2ab3b1cb-cd3c-4488-aa2e-2732dcf8bd03`

这是纯分析产物，没有业务仓库提交；主仓库已有的无关 dirty changes 未触碰。

## 可重复产物

- 提取脚本：`scripts/extract_putback_trace_alignment.py`（v1.0.1）；执行 `python3 scripts/extract_putback_trace_alignment.py` 即重建 `audit/`。
- 人读报告与四个固定规则例证：`audit/report.md`、`audit/examples.md`。
- 机械事实表：`audit/episode_facts.jsonl.gz`（600 行，episode 为分母）和 `audit/query_facts.jsonl.gz`（8,290 行，每 query 只保留最终 Memory v1 trace）。
- 审阅摘要：`audit/summary_by_model_terminal.csv`（6 model × 4 terminal group，保留零分母组）、`summary_all_episodes.csv`、`axis_validation.csv`、`cache_adoption_summary.csv`、`parse_failures.csv`。
- 冻结和溯源：`audit/extraction_manifest.json`、`source_freeze.json`、`source_inventory.csv`、`run_facts.json`。每个事实行保留原始路径、SHA-256、JSONL/event 或 stdout 行定位、scheduler command 的 `--episode-file` 映射和冻结 schema 解码结果。

使用的稳定审计索引是：

`/root/Documents/task-state-vla-paper/docs/audits/20260913-trace-inventory/trace_index.json`

SHA-256：`3ca213ca9a692028b1fe1583bfa38a7820fb0ab3e3620d389a995825e30d2ef3`。脚本默认指向这个已验收副本，`audit/report.md` 和 manifest 也明确记录它；没有对即将归档的 `f987` workspace 的读取依赖。索引只用于定位和哈希核验 stdout；scheduler 到 episode 的绑定来自各 `processes.jsonl` command 的 `--episode-file`，没有按 process ordinal 绑定 episode。

## 覆盖和机械结果

- 600/600 个 accepted put-back episode，J/T 各 train seed 0–2、每 run 100 个；8,290 个 query。每个 query 都有恰好 3 条 trace logger 记录，并折叠为最终 accepted trace，未把重复 trace 当样本。
- 从每个 run 冻结的 `checkpoint_metadata/train_config.yaml` 解码字段顺序和类别 ID；没有硬编码 numeric category index。解析/身份失败为 0，所有 600 集保留在分母中。
- 进度轴已对 600/600 集验证：冻结 config 的 `execution_progress.completed` 和 `logical_step` 都来自 `take_action_cnt`，单位为 `policy_rows`；最终 observed completed = episode length = logical step，未发现 progress invariant error。因此仅在这一已验证轴上，将前一 completed-chunk 边界与 diagnostics event.step 比较。
- 三种 return 事实分别统计且都为 600：预测 selected row 含 `move_block_back_to_origin_mat`、`chunk_completed` 写入 cache、后续 accepted query 实际输入该 return 状态。主对齐使用第三种事实。
- 物理证据要求同时有 `button_pressed` event 和 0→1 `stage_transition`：393 集有有效按压且早于首次实际消费 return；207 集在实际消费 return 前没有有效按压证据。tie、按压更晚、无 return 输入、不可可靠对齐均为 0。
- cache handoff 完整性是 query 级核验而非 episode rate：7,712 个 `chunk_completed` 更新中，7,690 个有下一实际 query；15,380 个冻结 schema 字段比较全部匹配，mismatch/unknown 均为 0；余下 22 个因为 episode 结束而没有下一 query。

`audit/examples.md` 给出两个成功和两个失败的完整 query/event 对齐例证：J/train0 episode 2、T/train0 episode 0、J/train0 episode 0、J/train0 episode 16。结果仅报告轨迹和事件事实，不对动作方向、机制或因果作宣称。

## 验证

- `python3 -m py_compile scripts/extract_putback_trace_alignment.py` 通过。
- 完整重跑提取器后检查 manifest 的 12 个输出哈希，全部匹配；重读 gzip 事实表确认 600 个唯一 model/episode、六个 model 各 100 集、8,290 个 query、每 query 三条 trace 及最终 accepted record。
- 再次计算稳定 trace index SHA-256，匹配上列冻结值；已清理脚本编译缓存。
