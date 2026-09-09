task_revision: 5dcc6240831df11028fb4be6bd4de7a1f8a86e60

完成与结论：两项 sim 真实低维数据、M+1 sidecar、四份 P2 full 配置通过独立 CPU 审查，数据层 GO，可供 training owner 接入开跑，不等待 wash。rearrange serial lag30 配置与真实样本也通过。no-memory YAML 通过，但需要只含 robot_action_target、availability={} 的 binding，不能直接套完整三字段 manifest。training owner 的模型/loader 尚无发布交付，本报告不代表 train/offline 闭环通过。wash v2 仍因视频/pose 时间轴漂移 NO-GO。

工作区：/mnt/public/xcj/Projects/workspace/3e78bfec-0cb7-41f4-ab7c-e002adf50c88/openpi。
沿用原树，base 1528b7b08eb119ede615c0520d6da3e8db6804a4；依次 fast-forward 审查：
- 481527346573b73958dcd81591fc8473e20feaff：sim adapter / 4full。
- 38bf82c1753e6e911e6215a6762cccc2a7bb15bd：M+1 完整 sidecar 与路径修正。
- 2c91f9aff8275b42285c93da094302800ec65f4e：serial/no-memory YAML。
- 69ca14825574981989340f8645ab3713208699fb：metadata 继承与 CLI，当前 HEAD。

后两项为作者分支已提交、符合已发布 task 要求的增量。未修改交付代码、未用 GPU、未重转数据、未派 agent。临时脚本及 import cache 已清理；保留 worktree 待 Manager 归档。

**按严重性列出的未闭合事项与接入条件**

1. P1，已报告且 Manager 接受的 wash 阻塞：all_172_15hz_s2m_master_v2 的视频按 MP4 PTS 转 15 Hz，pose/action 按 raw JSON timestamp 选近邻，同一训练 row 的图像和状态来自不同 raw frame。episode0 face q23 为 sidecar46/video43，q765 为1515/1527，q1205 为2387/2407；最后一例相差20 raw frame，约0.67秒。视频对 raw 灰度缩放图 MAE 分别为4.082对0.801、9.461对0.766、3.024对0.676。left wrist 和另一 episode face 同样复现。修复必须让视频、当前 follow、下一 master 与标注共用可审计 source mapping，不能只改 offset。本轮尚未收到正确视频小样本，不重做 wash 全量转换。
2. no-memory 接入条件（本轮发现的具体边界，不要求修改 core）：examples/rmbench/memory_configs/rearrange_blocks_no_memory.yaml 的 memory=[] 合法，但共享 rearrange binding_manifest.json 是三字段完整绑定。将其 series/availability 原样构造 EpisodeMemoryData 并调用 no-memory make_training_sample(..., 0)，实测 MemoryConfigError: availability must contain equal-length bool arrays for memory series keys。core _episode_shape 只允许声明中的 memory field availability；no-memory 无这些字段。使用同一 sidecar，仅选择 robot_action_target 且 availability={} 后，1,250 个真实 query 全通过。training owner 未发布的 memory_data.py 草稿也显式拒绝 extra_availability，其 binding helper 能按 memory_fields 选择字段；no-memory 注册项需要空字段并完成自己的 loader smoke。本项不影响 full/serial，不需新增补尾协议。
3. 文档交付缺口：截至审查 HEAD，examples/rmbench/ 尚无中文 README；CLI --help 可用，metadata 已有实跑命令。作者仍需补中文生成/绑定命令及 no-memory 选字段说明。此项不作为数值阻塞，但不能称 task 全部文档已交齐。

**sim 独立验证**

稳定共享资产根：/mnt/public/xcj/Projects/openpi/data/memory_v1/rmbench/。
每个子目录为 <task>_demo_clean_state_shared_memory，含 episode_memory.json、binding_manifest.json、metadata/。本树 data 软链指向共享 data。

| 任务 | episodes | LeRobot query 行总数 | sidecar 行总数 | 边界 query 数 | P2 两臂 sample 数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| rearrange_blocks | 50 | 20,103 | 20,153 | 1,250 | 2,500 |
| put_back_block | 50 | 17,588 | 17,638 | 1,000 | 2,000 |

- 直接读取共享落盘 sidecar 与全部100集 Parquet 数值列。期望标签独立按 scene_info 的连续半开 micro_stages、phase_sequence、task_facts 以及 language 段长展开，未调用作者标签生成函数作为期望值。所有 M+1 memory 行逐项一致；末 stage end=M+1、语言段长总和=M+1，raw 最后一观察 M 真实存在。rearrange ep0 phase 边界140/254，button confirmed 为零基 segment_4 的结束210；put ep0 phase 边界138/247、origin=front。
- 每集 robot_action_target、memory series、各 memory availability 等长 M+1。机器人前M行逐值等于 Parquet action[:,:14]，第M行重复末动作，float32最大误差0。独立读取 raw metadata/robot_edge_samples.json，100集均满足 raw_N=M+1、state前两行=raw前两行、action首行=raw[1]、action末两行=raw末两行。中间行 sidecar/action 也全量一致；未重新恢复/读取 raw HDF5 全部中间行，不将本检查表述为全量 raw HDF5 复读。
- converted key_state_target_ids 与独立当前 truth 全量一致；key_state_input_ids 前20行initial，之后严格等于 target[q-20]，manifest 未绑定这一 lagged input。phase 新 domain 含 unknown 前缀，通过语义字符串重映射，没有把旧 phase ID 当新 ID。sim 现有 availability 全 true，真实末帧也为 true。
- robot binding 为 source=sidecar、key=series.robot_action_target、semantics=action_at_row；六份 YAML robot offset0/stride1，没有二次动作移位。Parquet frame_index 仍逐集0..M-1、episode_index和总帧数不变，adapter query_indices=range(M)，robot observation 仍 M×14。M+1 只扩低维监督。training owner 草稿 MemoryLeRobotDataset 的 len/query 分别来自 base dataset / 原 frame_index，并校验 sidecar query_count；这只是只读静态核对，未导入/执行对方未提交代码，不能替代其正式交付。
- 两任务各自 P2 YAML 解析后结构比较，除 id 与 phase offset/stride 外完全相同：H50/K30、当前 reference 输入（首 query initial）、infer cache、独立 argmax、chunk_completed/last_executed 反馈、归一化声明、机器人及其他字段目标/权重均相同。phase 为 q+j+1 对重复q+30，共同 mask=(q+j+1<=M)&(q+30<=M)，固定H归约。
- 4,500个 P2 sample 的 mask、逐坐标 loss_weights、机器人 targets、非phase targets 两臂一致；invalid phase dense/weight皆0，padding皆0，机器人权重保持1。样本覆盖 q=0/1/29/30/31、各语义转换 b 的 b-49/b-30/b-1/b/b+1、M-50/M-31/M-30/M-29/M-1。每集 q=M-30 恰好前30个phase有效，第30个目标取真实raw M，后20无效；q=M-29 phase全无效但机器人保留；q=M-1的50行机器人全部重复末动作。rearrange350个、put200个所选query的两臂phase标签确实不同，覆盖有区分力的跨阶段样本。
- rearrange serial 与 full 的有序语义 domain 相同；named previous lag固定30，q<30输入initial，q>=30输入真实q-30；target为当前q的单query布局，不套P2 future mask，尾部仍监督当前GT。current_condition=train reference/infer selected、独立argmax、query_selected/query反馈符合计划。1,250个query的输入/目标/动作逐值通过。no-memory空字段/空updates/H50/K30/offset0通过同数query，前提为上述robot-only binding。

路径与 metadata：38bf82c 删除适配器账号硬编码根路径，dataset_root/source_data_root 显式必填，默认输出由项目根/data构造。已从 /tmp 工作目录传项目相对源路径实际加载两任务ep0，结果正确；manifest sidecar_path 为 data/...，运行时不引用作者临时工作树。69ca148 的两份共享 metadata/git_commit.txt 均为该完整commit，保存实际命令、四份rearrange/两份put配置。临时目录metadata copy smoke和共享落盘核验通过：每任务 converted meta 8文件、raw metadata 4文件及配置均逐字节等于源。源配置均为 demo_clean_state，原 source/convert command 与provenance保留。历史生成命令记录实际作者Python路径属于provenance，运行时binding/output不依赖它。

共享 sidecar SHA-256（69ca148补metadata前后不变）：
- rearrange：d8bf1b2b0c1e6dafb6580861e7bb9ca1293a697388ed70e54e64a21ed053ff3e
- put：51ebacff617854bb2842fa1ae02b0d513b464a959bad527f22fcd7c48dd81989

实现规模：没有新增tail_append解释器、没有修改已验收core、没有重复转换图像。可将逐episode重读相同小metadata外提、减少静态词表重复，但不构成训练阻塞，不建议为精简删掉raw truth/末行校验。

**此前 wash 审查保留证据**

- S2M 63f35c8：state当前对齐follow左/右position、rotation、gripper共14维，action下一对齐master同布局14维；与RMBench 3f7086271dbe49100323496218caf0ed69b761b3 的drawer converter相符，无单位变换。修复产物 /mnt/public/xcj/Projects/openpi/data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_172_15hz_s2m_master_v2 metadata指向63f35c8。ep0/3所有Parquet数值行对raw选定follow/master最大误差0；同raw帧follow/master明显不同，ep0 frame0最大差0.6868467。这证明动作源修复，不能消除视频/pose错位。
- raw /mnt/public/datasets/x1pro/wash-cup 独立扫244集：172合格/72剔除；非互斥原因缺标注16、label6 28、label1..5非各一个有效区间56。次序120集1>2>3>4>5、52集2>1>3>4>5。半开区间[150,255)含150不含255；允许顺序变化，非法标注剔除。
- v2共142,609行，13,404行phase availability=false。真实q22→23缺GT目标使phase dense/weight=0，机器人仍监督；不因缺GT删除整sample或当已知unknown训练。前轮wash adapter/config及client定向29测试通过，本轮未重跑整套。

**复现命令与范围**

在审查worktree执行，均为CPU只读：
```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q -p no:cacheprovider examples/rmbench/test_rmbench_memory_adapter.py
# 38bf82c：9 passed in 2.52s
git diff --check 1528b7b08eb119ede615c0520d6da3e8db6804a4..HEAD
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m examples.rmbench.rmbench_memory_adapter --help
```

关键真实边界最小复现如下。全100集truth/数值与边界sample的独立临时脚本已按task清理；取样集合、公式和资产摘要均列在上文。
```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python - <<'PY'
import json
from pathlib import Path
import numpy as np
from openpi_client.memory_config import EpisodeMemoryData, load_memory_config
for task in ('rearrange_blocks', 'put_back_block'):
    repo = task + '_demo_clean_state_shared_memory'
    doc = json.loads((Path('data/memory_v1/rmbench') / repo / 'episode_memory.json').read_text())
    p = doc['episodes'][0]
    m = p['query_count']
    ep = EpisodeMemoryData(series=p['series'], availability=p['availability'])
    assert all(len(x) == m + 1 for x in ep.series.values())
    samples = []
    for n in (1, 30):
        c = load_memory_config(f'examples/rmbench/memory_configs/{task}_full_t_plus_{n}.yaml')
        s = c.make_training_sample(ep, m - 30)
        np.testing.assert_array_equal(s.target_mask[:, 0], np.arange(50) < 30)
        assert not s.dense_actions[30:, 14:18].any()
        assert not s.action_loss_weights[30:, 14:18].any()
        samples.append(s)
    np.testing.assert_array_equal(samples[0].robot_targets, samples[1].robot_targets)
    np.testing.assert_array_equal(samples[0].action_loss_weights, samples[1].action_loss_weights)
    print(task, 'M=', m, 'P2 valid=', int(samples[0].target_mask[:, 0].sum()))
PY
```

交付边界：本报告仅给独立data/config结论；正式loader查询边界、归一化资产、模型loss、checkpoint/offline闭环应由training/integration owner从明确交付commit完成并报告。不得把CPU GO表述为已有训练/评测成绩。wash正确小样本、中文README尚未交齐。
