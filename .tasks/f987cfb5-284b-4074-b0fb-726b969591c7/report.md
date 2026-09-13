# 完成：现有状态—动作—事件诊断材料与验证集审计

已在独立 workspace 完成只读审计，没有运行 GPU rollout、训练或评测，没有打开/下载视频，也没有修改 RMBench、openpi、robot-bridge 或论文正文。

本次修订基于先前已发布的 report revision `4e073166efb2723d253e002dcee0040f40ddc2e9`，补正了 J/T 输入、终态标签、有效损失、actual K 与 qpos/TOPP/RNG 的冻结证据。

成果位于：

```text
/mnt/public/xcj/Projects/workspace/f987cfb5-284b-4074-b0fb-726b969591c7/audit/
├── audit.md          # 中文审计：字段边界、冻结 N/J/S/T 合同、seed/held-out、P0 hook
├── build_index.py    # 可重复的本地/远端只读索引构建器
└── trace_index.json  # 15 个 target run、1,500 episode 和选中样本的机器可读证据
```

核心结果：

- 核对的 snapshot 为 `accepted_results_20260913.json`，SHA-256 为
  `81be95c41d83824bfe748027dfcc1a2eecd77520c4d2219c5301b02e4c491f9b`。
- 15 个目标 JSONL 的 SHA-256 都与 snapshot 一致；每个 leaf 都有连续的 0–99 episode、100 条可解析 scheduler trace，合计 1,500 episode、27,674 query、63,638 trace 状态记录。
- 所有保留的 preflight 是每 episode 一条 accepted record，final seed 连续；报告明确限定为“未在保留记录中观察到 retry”，因为 runner 代码允许 reset rejection 后 `seed+1` 重试。
- 索引为每个 episode 保留 env seed、终态分类/reason、诊断原始行哈希、episode context/preflight/scheduler log 哈希及路径；每类至多两个升序样本，并提供 J/T eval0 与 S 跨 eval-seed 的模型聚合样本集。
- `complete_no_press` 已明确为内部机械别名“未记录有效按压（终态标签）”；它不表示整个任务完成，且 `button_press_insufficient` 仍单列。
- J/T 的 final logger trace 保留 execution progress 得到的 actual K，即已完成的 policy-row 数；S 的 query-selected trace 没有真实 actual-K，日志 `actual_k=0` 未被误解为零 policy row 或零物理 tick。raw logits、raw actions、动作方向、RNG、policy timing 与独立 lock-state 均明确标为当前未记录。
- 修订后的冻结训练证据表明：J/T 普通 query 读取当前 reference，只有 index=0 的首帧为 initial，推理读取 cache；J、T、N 保存的 `key_state_loss_weight=0.1` 在 disabled 分支不生效，S serial CE 的有效 multiplier 为 schema-derived 1.0，action FM 同时存在且固定 padded-D=32 分母。审计表已分别列出 N/J/S/T 的有效系数和分母。
- 审计现以训练 OpenPI `d10cc01…`、评测 OpenPI `a869498…`、bridge `8ea607…` / `f962663…` 与每个 target config 保存的 RMBench runtime commit 给出行级证据。qpos/TOPP 的 1/250 仅是仿真/轨迹采样；没有把它写成固定 policy control-Hz。训练/评测隔离和两个 50-episode train-only metadata 的 held-out 缺口也已记录。建议了 opt-in `query_trace.jsonl` 的 P0 hook，未改生产代码。

验证：

```text
python3 -m py_compile build_index.py
python3 build_index.py --output trace_index.json
python3 -m json.tool trace_index.json
```

随后运行结构/来源断言：15 runs、1,500 episode、108 个去重选中样本、15 个 snapshot hash match、15 个连续 accepted preflight、1,500 个 trace 映射、每个 selected sample 的诊断/episode/preflight/scheduler SHA-256 和路径均完整；全部通过。修订版还检查 `complete_no_press` 解释、J/T 的 policy-row actual-K unit、S 的未记录标记和冻结源码引用。

最终文件 SHA-256：

```text
build_index.py   3896ef62373cf1e053674e21a75d4323ee10b809a3f7812dac733225bfbf911c
trace_index.json 3ca213ca9a692028b1fe1583bfa38a7820fb0ab3e3620d389a995825e30d2ef3
audit.md          d0c5fbda84db958757576b7898608bec888a3c2289ac5e370f3f7310c780e121
```

该审计 workspace 本身不是 git repository，因此没有业务交付 commit；MAM 根目录中的其他未提交改动未触碰。
