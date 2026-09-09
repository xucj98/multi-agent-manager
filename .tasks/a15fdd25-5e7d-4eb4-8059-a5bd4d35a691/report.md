task_revision: 8e32a7c3a018ee5ff8d5eefbd6858e05495d172f

完成与未完成：

完整 F0 smoke/正式100入口、四份固定配置、中文README和候选版本检查已在首次新smoke前提交，准备阶段完成。本轮未启动GPU smoke、正式100或训练。尚未收到Manager对bc842036候选无阻塞的确认；确认后可先运行row30两条smoke。正式阶段仍须smoke验收后另行放行，同一F0 scope后续各行不再重复向用户请求授权。

workspace与交付commit：

- 继续复用 /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691 下原有RMBench、robot-bridge、openpi独立worktree与环境，没有重建workspace或修改主checkout。
- RMBench：425afaf23b0f8dd6655f18e27c497cbc83cb6798（实验：固定终止修复版本并补齐 F0 正式入口），仅修改experiments/memory_chunk_20260910/。前序9e8fccb四份配置与d1a64cb中文文档反馈保留。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b，精确fast-forward合入fd38513→92b365c→bc84203。没有合后续live进度或新memory wire改动。
- OpenPI：58d6f2155acc3af03017677bb3f536101e6699f4，继续使用本任务editable环境；bridge自己的轻量openpi-client指向同任务OpenPI。
- 三个worktree均已核对干净；commit message与提交文件摘要已核对。

入口与固定协议：

- 统一入口：experiments/memory_chunk_20260910/commands/run_f0.py，替代原run_f0_smoke.py，支持--row、--mode smoke/formal、--dry-run、--check-smoke和--detach。旧shell入口继续作为共同启动实现，历史旧smoke默认值保留。
- 四份配置仍是configs/f0_row{1,20,30,50}.yaml。H50来自同一个旧shared-full 30k checkpoint，K30固定，legacy_full_feedback_selector为index 0/19/29/49，所有旧memory字段共同选行。
- 保留原模型、phase/empty_mat_side/button_press_status字段、归一化、编码、解码，不注入新memory_config。row50只读取模型预测，不读取未来GT。
- 旧P1评测场景仍为demo_clean_eval；eval seed0、起始候选100000、instruction generation100，每个正式run串行100 accepted rollouts。新训练/转换来源仍必须为demo_clean_state，不能用缺metadata/详细子任务标注的demo_clean替代；旧checkpoint metadata已记录rearrange_blocks_demo_clean_state_shared_memory。
- 仅GPU0，policy显存比例0.40；启动前只查询GPU0显存、利用率、计算进程，已有计算进程则拒绝启动。
- 每个row各自smoke两条（一video、一no-video）→检查产物及source→核对干净commit→该row正式100，顺序row30/20/1/50。保留完整recorder配置/source检查，不增加selector白名单。

直接命令（从本任务RMBench根目录执行，无需export根目录变量）：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --mode smoke --dry-run
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --mode formal --dry-run
```

Manager确认候选review无阻塞后的实际smoke命令（当前未执行）：

```bash
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --mode smoke --detach
```

smoke完成后的只读产物/source检查：

```bash
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --check-smoke
```

Manager正式阶段放行后的100入口（当前未执行）：

```bash
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0.py --row 30 --mode formal --detach
```

--detach使用start_new_session=True，打印host、真实runner PID和共享run_dir。正式启动后立刻据输出执行mam job add登记当前task；进程结束后记录结论并archive job。跨四行启动日志共用主实验组_queue.log，各run的stdout.log和processes/由recorder创建，不提前污染非空leaf。短smoke无需MAM job。其它行使用相同命令替换--row，不能交叉引用row30 smoke。

source身份与验证证据：

- 最终RMBench source_content_sha256：0ab8e017ac29152fee838a33c4d42f78d3908af4c181d6573743966f6d1786d1。
- 最终bridge source_content_sha256：cc79d3bd6130ada19ab1631fced4b6e34c71d34ed587123250089d664251b1b8。
- 两者用当前bridge runner的source_content_hash计算。入口每次输出这两个hash；OpenPI精确HEAD/干净状态预检，真实policy source、依赖和配置仍由正式metadata握手及完整recorder门禁核对。
- 四行共8次dry-run全部通过。同一row的smoke/formal命令仅差--mode、--result-run与正式所需--smoke-run-dir，其余服务命令、缓存路径、scheduler参数、GPU0与超时完全一致。dry-run前后源码身份未变化，未创建F0结果或启动GPU。
- --check-smoke复用官方validate_smoke_run，额外核对完整scheduler配置和smoke保存的RMBench/bridge源码hash；实际formal启动前同样预检。正式runner获取真实服务metadata后继续执行完整assert_smoke_compatible；预检不替代该检查。
- 用真实旧smoke验证：新候选hash预检按预期拒绝，报“smoke tested source content differs from formal source”。本row新smoke尚不存在时，--check-smoke按预期报missing，在任何GPU调用前退出。
- 新入口ruff、shell bash -n、git diff --check通过。历史握手metadata未发现旧run leaf或worker_log_path混入待比较身份；真实新候选握手及GPU闭环仍待smoke验证。
- 本轮bridge候选CPU定向集合为53 passed in 2.42s，包含terminal完整run_iteration回归、scheduler生命周期和benchmark流程：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/robot-bridge
CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q tests/scheduler/test_openpi_simulation.py tests/scheduler/test_lifecycle.py tests/benchmark
```

此前两个问题的当前状态：

1. terminal额外infer：候选bc842036已删除临时policy-client代理。OpenPISimulationScheduler先提交terminal反馈/trace，再返回None，公共循环的最小None hook直接skip infer/execute，保留reset/error路径。CPU回归确认terminal时policy请求只有reset、零infer，robot请求只有get_obs，actual_k=10且next_query=false。待Manager确认独立review结论，不自行将CPU结果当作GPU验收。
2. 跨row smoke门禁：Manager已裁定每行各自两条smoke，当前完整配置检查保留。入口在第一次smoke前已补齐正式逻辑，所有行完成前冻结代码、配置与README；结果和MAM report可以正常更新。不得smoke后再新增正式入口、改cache命令路径或修改源码文档而导致source hash失配。

成果与计划真实保存位置：

- eval_result软链接指向共享主RMBench：/mnt/public/xcj/Projects/RMBench/eval_result。
- 新row30 smoke计划目录：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_smoke_20260910/。当前尚未创建。
- row30正式目录：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/。其它row只替换行号，所有结果在同一主实验组。
- Manager已验收的旧加载锚点：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/pi05_rearrange_full_k30_oldfull_smoke_20260910/。旧bridge b17f6c5、OpenPI71c80db，不可代替新F0 smoke。
- 旧smoke结果1/2：seed100000失败button_press_insufficient，100001成功；episode0.mp4为700帧、521128 bytes且可读，episode1视频关闭且不存在；两个scheduler exit0、robot/policy正常shutdown，当时官方validator通过。产物包括config、command、继承metadata、诊断、视频检查和进程记录。
- 旧冷启动两条smoke共406秒、checkpoint restore日志7.95秒，两条长700/406 logical steps，仅是旧环境粗略吞吐锚点，不承诺新F0正式100耗时。

运行与后续监控：

当前无新进程或MAM job，不轮询占用GPU，也未使用GPU1/远端卡。保留workspace和GPU0预留。下次动作是Manager对候选无阻塞确认到达后，检查GPU0并启动row30两条smoke，随后核对video/no-video、metadata、逐query trace与正常退出。正式阶段获准启动后先检查服务与首条episode，接近50条前检查进度；第50条由实验负责人手动比较固定历史基线（93/100为主、同seed first50为辅助），偏差超过10个百分点调查协议/基础设施并记录，不删除不利episode，不把人工调查宣称为runner自动完成。最终核对100条与退出并收尾job。每次阶段交接报告下一监控时机。
