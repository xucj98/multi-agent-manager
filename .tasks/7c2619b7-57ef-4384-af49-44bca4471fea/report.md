# put-back HF-fixed 两集独立证据核验

任务 revision：`2fe08463234f922c5103e0cc8ae5540b54b1c198`。本次仅对已完成的 `c_hf_j_hf_fixed_put_back_trainseed0_evalseed0_smoke2` 做只读核验：没有运行 GPU、模型、仿真、helper、`audit --pair` 或新增测试，也没有修改冻结源码、工具或结果。未审阅 event/rearrange。

本地独立 review worktree 均 clean：OpenPI `0ce566bd34f99cb4775422f012ab67c16aa53885`、robot-bridge `ffa122494c19e1c0154e877010f7b470967ccfc6`、RMBench `6abebf08d084d0be43aa56ebe158dc8395fa58e4`。C3 runtime 的三库 `git status --porcelain` 也均为 0 行。

## 原件、身份与完整性

只读从 `wuwen-4090-3` 拉取并在本任务 evidence 中复哈希；随后再次对远端读取相同 SHA-256。关键链条一致：

- stage receipt：`2bd6cf0cdd6384b0923bf39f8a884067c7f7d7551d244846ee15807b9f21e875`
- trace contract：`7483ffca1dc661a84ef30e0b6db967731c12025be84f375f7eb1386ac6673a9b`
- helper review：`efd2a6d9e00c5cba72d37901bb44f8bcd784ab788cc5a2ad081e949f58fa00dd`
- execution receipt：`593196af4b14bf5d537bf4f3cc4c7d39286bb167d6d242d0631d93aa6c2ec393`
- rolling 原件：episode 0 `56432735be91341e5792a2012e3ecaf3a6285286031ba4c6834698fee4bfc603`；episode 1 `4ac88ef952486f227f9962a6608a0182c816d12ebcb3386bbc16bd174696cd64`

命令、manifest、input audit 和两处 scheduler YAML 相互引用的哈希均一致；两份 scheduler YAML 字节相同（`1b411a2a…16bee8f9`）。运行记录的实际 checkpoint 是 `.../pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0/20000`，checkpoint tree digest 为 `d29535bf…da940de`，metadata digest 为 `3b5d9b56…f08622a4`。runtime metadata 中 bridge/RMBench/OpenPI commit 与冻结版本相符，且本地重算的 worker、`_base_task.py` SHA 与 runtime metadata 留存值相同。

配置中的 domain randomization 为 `random_light=false`、`crazy_random_light_rate=0`、`random_background=false`、`random_head_camera_dis=0`、`random_table_height=0`。checkpoint 的 Memory v1 字段顺序为 `[phase, origin_mat]`，故 phase 使用 selected-id 第 0 列；83 个比较均按此字段顺序独立重算。

## reset 与初始条件边界

两次外部 accepted reset 的原始请求分别为：

| episode | requested seed | accepted |
|---:|---:|---|
| 0 | 100000 | true |
| 1 | 100001 | true |

`BenchmarkRunner._loop` 的种子起点和 accepted 后递增逻辑与这两个请求一致。scheduler 由 `--episode-file` 接收已经 accepted 的 reset snapshot；源码说明该路径记录它而不再向 controller 发第二个 reset。

worker 的 `reset()` 每个外部请求会先以该请求的 seed 执行 `setup_demo + play_once` preflight，然后以**同一个请求 seed**再次 `setup_demo` 成为 active episode。因此没有发现 episode 1 被错误地重置为 100000。

但 `episode0.json`/`episode1.json` 保存的 `episode_info/task_facts` 来自 preflight `play_once`，不是 active environment 的独立初始快照。两份 preflight facts 的 origin 都是 `right`，initial block pose 也相同。冻结 `put_back_block` 在当前禁用连续随机化的配置下只以 `np.random.randint(0,4)` 选择四个 mat 之一，所以不同 seed 落到同一有限离散条件是可能的。这不足以指认 reset bug，也不足以把两集称为已证实的不同初始条件对照。

注意 scheduler YAML 的 `reset_episode_rng: false` 不表示 HF-fixed 没有 reset。`openpi_simulation._rolling_resets_action_rng` 对 `hf_fixed`/`hf_event`/`hf_periodic` 无条件为 true；原始 JSONL 每集各有一次 `policy_rng_reset`，并记录 `action_rng_lifecycle=explicit_episode_reset`，与源码一致。该 flag 仅是 matched baseline/shadow 的 opt-in。

## 轨迹时间合同重算

我没有使用 `plan_progress`/`plan_terminal` 顶层滞后一轮的 `logical_step` 判断观测时刻，而是以 `source_step + completed_rows` 重建。两集结果相同：

- 17 个 normal `action_plan`，source steps 为 0、30、…、480；16 个实际 K30，最后一个计划执行 20 行、因 step limit 丢弃 10 行，总完成 500 行。
- 99 个 forecast consumption，absolute target steps 为 5、10、…、495；每项的 `forecast_source_step=current_step-5`、model index=4，并与对应 action/probe forecast 的 selected IDs 逐项一致。
- 83 个 probe，准确位于 `5..495` 的 5 行间隔且排除所有 K30 boundary；action stream call 为 1..17，probe stream call 为 1..83，二者连续。这里是协议记录的 stream/call，不是内部 PRNG key。
- 83 个 probe 的输入 memory IDs 都等于同一步已消费 forecast 的 selected IDs；边界后的下一 normal action 输入也等于 boundary consumption。phase comparison 的 old/new IDs、model indices 和 absolute target steps 都与 metadata field order 和 source forecast 重算一致。
- 没有 trigger、clear record、clear return 或中途 normal action。可以记录 non-trigger deviation streak，但它不等于 replan。
- 最终均为 `step_limit_reached` / logical step 500。这里任务失败是完整的 terminal 结果，不被当作基础设施异常或成功率结论。

两个 scheduler child 均以 `episode_terminal` / return code 0 退出；benchmark summary 为 `completed`、error 为 null，execution return code 为 0，ports 已释放。outer log 有启动期间的连接重试，但没有留下 runtime error。episode 0 的 500-frame video 检查通过；episode 1 按 smoke 合同禁用视频且检查通过。

## 结论与限制

记录的两集在工程身份、原件哈希、终态/视频/进程收尾及 17/83/99/500 的 HF-fixed 时间合同上没有发现阻断；本地 receipt 的 261 项离线检查均通过。stage 分类仍为 `matching_smoke_only_no_formal100_started`，不能作为 HF 有效、matching-smoke gate 已满足或 formal 准入的结论。

本地 JSON receipt：[receipt.json](/mnt/public/xcj/Projects/multi-agent-manager/.tasks/7c2619b7-57ef-4384-af49-44bca4471fea/receipt.json)，SHA-256 `a01a93ebee11144f6c60a10b1182272416d0420d64b2c14c94efd14fea0ac79f`。它也明确保留以下边界：不把 wire stream 当内部 PRNG key，不把 policy timing 当作独立确认的端到端同步时延，也不能凭现有 preflight facts、相同轨迹或 seed 标签断言两集 active 初始条件不同或存在 bug。

