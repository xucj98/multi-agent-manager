task_revision: 6ea71195b6189b83739e487b4a641bb3fdd404c8

完成：

- RMBench 已提交 CPU 准备版本：498cc4c49e8669dab822e55a2dd060a5e1c68d98（“准备 Memory v1 checkpoint 评测适配器”）。
- 交付仅在 RMBench 的 experiments/memory_chunk_20260910：
  - commands/run_memory_schema_eval.py
  - configs/memory_schema_eval.yaml
  - README_memory_schema.zh-CN.md
- 删除了未提交的 drawer wrapper；README 直接给出既有 robot-bridge/scripts/launch/drawer_offline.py 的两个旧模型、固定五集、输入和输出命令。
- 入口只保留 checkpoint metadata/schema → input audit → derived static manifest 的窄适配。它不管理子进程、GPU 探测、detach、队列日志、结果 recorder 或自定义 smoke 校验；这些均复用 BenchmarkRunner/RMBench recorder。
- technical-smoke 必须是 leaf 50、mode=smoke、run-name 以 technical_ 开头，runner 仍固定两条 accepted rollout（video on/off），manifest 记录 evaluation_kind=technical_smoke。常规 smoke/formal 即使 dry-run 也只接受 config/exp_name/20000；formal 只转交 --smoke-run 给既有 runner 的 validate_smoke_run 和握手后 assert_smoke_compatible。
- 已将本 task OpenPI 分支从 929e398682feb78a043d7252bfe72204e710cc2d fast-forward 到 a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4；未重建环境。配置与说明同步该固定 SHA，bridge 仍固定 8ea6078543a875b5ae223df16891cdc1fe975c66。
- 公共接口缺口已核实：BenchmarkRunner 只消费静态 manifest，provenance 模块只验证逐文件 evidence，均没有 checkpoint→audit/manifest 生产 API；因此未修改 bridge，而由本实验组构造必要输入。
- 另发现 bridge 对完整 checkpoint/metadata 作逐文件集合验证。把 audit 写入 metadata 子树会让 evidence 自引用并必然失败，故完成 checkpoint 的不可变 sidecar 放在 <checkpoint>/eval_inputs/memory_chunk_20260910/<variant>/；通过 run.config_source 由 recorder 继承至结果的 checkpoint_metadata/lineage/config_source/。这保留既有 metadata 留痕，不在 eval_result 创建输入缓存。

workspace、实际版本：

- RMBench：/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/RMBench
  - task/e6908de7-4b02-465a-987b-a19eba7a315a，498cc4c49e8669dab822e55a2dd060a5e1c68d98，干净。
- robot-bridge：/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/robot-bridge
  - task/e6908de7-4b02-465a-987b-a19eba7a315a，8ea6078543a875b5ae223df16891cdc1fe975c66，干净。
- openpi：/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a/openpi
  - task/e6908de7-4b02-465a-987b-a19eba7a315a，a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4，干净；MAM 登记的 base 仍显示初始 929e398，实际 checkout 已按发布要求快进。

CPU 验证：

- 在 a869498 上以 JAX_PLATFORMS=cpu 对两个保留 d10/50 checkpoint 重跑入口 dry-run：
  - full：joint_dense、H50/K30、padded action 32、phase/empty_mat_side/button_press_status、chunk_completed/last_executed、demo_clean_state，metadata 经 _runtime_metadata → MemoryContext。
  - serial：serial_token、同一 H50/K30/32 与字段、query_selected/query、demo_clean_state，metadata 经相同真实路径进入 MemoryContext。
- 将 full checkpoint 传给 serial variant 被 schema 不匹配拒绝；未带 --technical-smoke 的 step 50 被 20k 门拒绝；technical-smoke + formal 被 CLI 拒绝。
- 对真实 d10 technical audit，bridge verify_audited_checkpoint（params/assets）和 verify_audited_metadata（metadata）均通过；derived manifest 标记 technical smoke。还以临时 mock completed checkpoint 验证最终 checkpoint sidecar 不改变 metadata evidence 集合，并可同时通过两种 bridge verifier。
- RMBench recorder.inherit_metadata 已验证可将 config_source 的 input_audit.json 与 input_manifest.json 复制进 checkpoint_metadata/lineage/config_source。
- AST/YAML、git diff --check、bridge benchmark/drawer --help 均通过；入口 help 不含 --detach 或 --check-smoke。
- 没有加载模型、启动仿真或 GPU 进程；MAM jobs 为空。技术审计 .local/memory_schema_eval/technical_inputs、测试临时目录与 /tmp 输出均已清理，未写入 eval_result。

行数与边界：

- 入口为 256 个物理行、230 个非空非注释行，AST 计 170 个语句。约 150 的目标按可执行逻辑只超 20 个语句；保留的增量是六项 metadata/schema 断言、params/assets 与 metadata 两个不同 scope 的逐文件 evidence、不可变 write-once sidecar、派生 manifest，以及调用既有 runner 所必需的服务命令接线。没有通过压缩排版或新增平行 runner 达到表面行数。

未完成与 GPU 后续：

- 当前没有 GPU 授权；未执行 technical smoke、20k 常规 smoke、100 episode formal 或 drawer offline 回归。
- 获授权后先为每个完成 20k checkpoint 执行 --prepare-audit，再执行匹配的两集 smoke；确认 runner 产物后同 checkpoint/formal 使用该 smoke。technical 50 结果只用于新 wire 验证，检查后清理技术结果与 .local 输入。
- 正式 100 episode 需在干净 commit 上由单卡串行运行，启动后立刻 mam job add 登记。入口配置每 episode timeout 为 3600 秒：两集 smoke 的硬上限约 2 小时加启动，正式 100 的实际时间应以 smoke 实测 wall time 乘 50 后再向 Manager 报告，CPU 准备不能可靠给出更窄估计。
- drawer 使用 README 的既有 direct command；其没有 CPU dry-run，GPU 分配后才能运行。

