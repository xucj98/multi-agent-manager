# 完成：现有状态—动作—事件诊断材料与验证集审计

已在独立 workspace 完成只读审计，没有运行 GPU rollout、训练或评测，没有打开/下载视频，也没有修改 RMBench、openpi、robot-bridge 或论文正文。

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
- J/T 的 final logger trace 保留执行进度得到的 actual K；S 的 query-selected trace 没有真实 actual-K，日志 `actual_k=0` 未被误解为物理执行零行。raw logits、raw actions、动作方向、RNG、policy timing 与独立 lock-state 均明确标为当前未记录。
- 冻结配置、H/K 名义时间轴、qpos/TOPP 物理时长限制、训练/评测隔离和两个 50-episode train-only metadata 的 held-out 缺口均已记录。建议了 opt-in `query_trace.jsonl` 的 P0 hook，未改生产代码。

验证：

```text
python3 -m py_compile build_index.py
python3 build_index.py --output trace_index.json
python3 -m json.tool trace_index.json
```

随后运行结构/来源断言：15 runs、1,500 episode、108 个去重选中样本、15 个 snapshot hash match、15 个连续 accepted preflight、1,500 个 trace 映射、每个 selected sample 的诊断/episode/preflight/scheduler SHA-256 和路径均完整；全部通过。

最终文件 SHA-256：

```text
build_index.py   de7aa2d19a59bfacee58a0189b5c27ec7d14b58099bebed325ffa4bbba01292a
trace_index.json 60ecb3fbb5e10d1b0379db2293ab86c3b5baa74c51c50e319639f21e2bdc51cd
audit.md          30e4b0b0a1ce2e93bb22a27e9ad34c77121386a44009a92454ce76054919495f
```

该审计 workspace 本身不是 git repository，因此没有业务交付 commit；MAM 根目录中的其他未提交改动未触碰。
