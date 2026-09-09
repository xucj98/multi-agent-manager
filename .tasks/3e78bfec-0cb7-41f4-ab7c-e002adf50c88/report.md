task_revision: 4fda7e37ecb0e064856b1ea8ccc229b687c6224c

**当前阶段结论：wash 数据层 GO，解锁全172正式转换**

46e619e 的低维 M+1 修复通过，上一阶段7f4d74e发现的末帧标签缺失P2关闭。94d9927的显式source参数及项目相对路径解析通过。本轮不重解码已通过的视频，也未重跑sim100集；沿用已验收的视频/pose映射和full/serial配置。正式172集产物完成后仍需数量、metadata及必要低维读回复核；本次GO不代表全量产物或训练模型wire已验收，不宣称整个数据任务完成。

复用工作区 /mnt/public/xcj/Projects/workspace/3e78bfec-0cb7-41f4-ab7c-e002adf50c88/openpi，从已审a75d173依次fast-forward：

- 94d9927f22f18d15e91fbe69b9bb7fa5ce494502：source参数显式，source/output/config相对路径按项目根解析。
- 46e619e6db6bcd4f9d5d11d31b82e5f51e8522a0：完整terminal memory row，当前审查HEAD。

两份低维样本直接读取稳定共享路径：/mnt/public/xcj/Projects/openpi/data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_2_15hz_s2m_master_v3_source_frame_aligned_smoke。meta/memory/command.txt记录实际46e619e完整commit、cwd、显式dataset-root及--refresh-low-dim-sidecar-only，使用新full_current_feedback YAML。conversion.json为format_version4、episode memory为version2。

| 核验边界 | ep0：真实末帧有GT | ep1：真实末帧无GT |
| --- | --- | --- |
| query M / sidecar行数 | 1216 / 1217 | 1509 / 1510 |
| 最后selected raw index | 2408 | 2989 |
| raw label5半开范围 | [1710,2409) | [1440,2970) |
| sidecar末phase / availability | label_5 / true | unknown / false |
| full(q=M-30)有效phase位置 | 30（此前错误为29） | 20，其余真实缺GT位置mask0 |
| full(q=M-1)有效phase位置 | 1（此前错误为0） | 0，保留正确无GT屏蔽 |
| 最后query serial target mask | true | false |

独立核验直接从raw subtasks半开区间重新展开两个episode完整selected索引对应标签，M+1 phase及availability全部与更新后sidecar一致。robot_action_target的前M行逐值等于既有Parquet actions，第M行重复末action；2,725行actions仍等于下一selected raw master14，state等于当前selected raw follow14，float32误差0。Parquet中的phase/availability保持sidecar前M行，frame_index仍0..M-1；query source/action indices分别等于完整selected mapping[:-1]/[1:]。新selected_source_frame_indices/timestamps完整M+1，旧query/action映射仍M，未新增不存在的query或二次动作移位。

对两集q=0/M-30/M-1调用既有core full与serial API，机器人50行targets均等于原actions按末行clamp，robot weights全1；无效phase dense及14:20权重全0。ep0首query full有效42、ep1为28，说明缺GT处理保留；此前核验过的full/serial输入/反馈配置未在本次改变。converter.build_dataset仍按memory.source_frame_indices的M行写Parquet，observation_and_next_action_rows还逐值检查sidecar前M动作与next master一致及尾动作repeat，代码与落盘样本一致。

路径核验：dataset_root=None立即报显式缺source错误；默认output_base=data/lerobot，解析到本树共享data目标，不再写死账号路径。切换cwd到/tmp后，项目相对source/output/config仍解析正确，full YAML可由公共parser载入。未调用refresh入口或任何视频工具；这里只读取作者已经刷新的低维产物。

本轮未发现剩余数据侧阻塞。CPU定向检查：

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q -p no:cacheprovider examples/x2robot/test_wash_cup_memory_adapter.py examples/x2robot/test_wash_cup_memory_config.py
# 14 passed in 8.24s
git diff --check a75d173..HEAD
```

关键边界最小复现，在上述审查worktree执行，不打开视频：

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python - <<'PY'
import json
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from openpi_client.memory_config import EpisodeMemoryData, load_memory_config
root = Path('data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_2_15hz_s2m_master_v3_source_frame_aligned_smoke')
c = load_memory_config('examples/x2robot/memory_configs/wash_cup_phase_full_current_feedback.yaml')
for e in json.loads((root/'meta/memory/raw_episode_memory.json').read_text())['episodes']:
    i = e['episode_index']
    mem = e['memory']
    a = pq.read_table(root/'data/chunk-000'/f'episode_{i:06d}.parquet', columns=['actions'])['actions'].to_pylist()
    m = len(a)
    ep = EpisodeMemoryData(series=mem['series'], availability=mem['availability'])
    assert all(len(v) == m+1 for v in ep.series.values())
    assert len(ep.availability['phase']) == m+1
    np.testing.assert_array_equal(ep.series['robot_action_target'][:-1], a)
    np.testing.assert_array_equal(ep.series['robot_action_target'][-1], a[-1])
    print(i, m, ep.series['phase'][-1], ep.availability['phase'][-1],
          [int(c.make_training_sample(ep, q).target_mask.sum()) for q in (m-30, m-1)])
# 0 1216 label_5 True [30, 1]
# 1 1509 unknown False [20, 0]
PY
```

未修改交付代码，未占GPU，未运行转换/训练或派agent；本轮独立检查使用内联脚本，不留临时脚本/cache，worktree继续保留。下面为历史阶段记录，旧P2阻塞已由本节关闭。

---

**历史阶段报告：7f4d74e5b4200114e4e8e2c7d1e66b7b22202aa3（task revision b46616e1efd03c474dde2570695e499fab0c0df4）**

**恢复后的 wash 阶段结论**

新 v3 两集的实际视频/pose/action 共同 source mapping 通过；773d177 的视频漂移修复可以接受。a75d173 的 full current / serial lag30 闭环 YAML 语义也通过。但完整 wash 数据侧 GO 暂不能签：raw memory sidecar 仍只有 M 行 phase/availability，丢掉一个真实存在的 M+1 末帧标签。此项为新发现的 P2，见下面精确复现；不涉及重编码已通过的视频。可继续基于已验证 source mapping 的视频/机器人转换准备，训练使用前须补全低维 sidecar 并复核。

sim 既有数值/P2/serial 结论保持，未重跑100集检查。63319ac 的 metadata 小增量及两份实际共享产物已通过；数据 command 文件含 commit/cwd/命令，候选训练 YAML 和独立 git_commit.txt 已移除，sidecar 数值 SHA-256 与上一阶段相同。

工作区继续使用 /mnt/public/xcj/Projects/workspace/3e78bfec-0cb7-41f4-ab7c-e002adf50c88/openpi，在原69ca148上依次 fast-forward：
- 63319ac984492cd8bfd8a71158200220a6e14e38
- 773d177b93b6a6d8569a6761ae74118bef5d4adc
- a75d1737539d5497b2e8d3569756ef0dc67d5ed2（本轮审查HEAD）

未修改交付代码，未使用GPU，未重转任何数据，未派agent。仅CPU解码既有raw/v3视频及读取两集数值。临时review_wash.py与相关cache已清理，worktree保留。

**P2：wash phase/availability 尾行丢失，需在训练前补齐**

代码位置：examples/x2robot/wash_cup_memory_adapter.py:685 先将完整 source_frame_indices 截为 row_indices=indices[:-1]，:689 只为 row_indices 生成标签，:692-697 序列化 M 行 phase/availability 且 tail=None。conversion 的 video_source_frame_indices 虽为 M+1，但不是可直接绑定的 M+1 memory series。

明确输入：新样本 episode0，M=1216，video/source mapping=1217；最后query1215的state raw2406，action raw2408，保留的第1216个video frame也为raw2408。raw subtasks.json 的label5范围为[1710,2409)，故raw2408的phase必须是label_5、availability=true。

实测：sidecar memory.series.phase 和 availability.phase 都长1216。以这些落盘字段和Parquet actions构造现有EpisodeMemoryData，full(q=1215) 的首个t+1 phase target mask=false、14:20六维weight全0；full(q=1186=M-30)仅29个phase有效。期望分别为1个和30个。仅在内存中补真实label_5/true并重复末action形成M+1后，实测分别恢复为1/30，机器人50行target与原样本完全一致。

episode1提供相反边界：M=1509、末selected raw2989超出label5范围[1440,2970)，这一额外memory行应保留unknown/availability=false，不能无条件补true。phase/availability目前同样只有M行。

修复要求沿已确定契约：低维memory series/availability完整M+1，robot_action_target前M行保持已对齐actions、最后重复末action；query/state仍为M行，不能二次动作移位。末帧标签和availability应从既有raw ranges及完整selected mapping推导。当前视频及source index provenance已包含所需末帧，不应因此再转视频。此处不要求新增tail_append或改core。

**已通过的两集实际产物检查**

样本路径：/mnt/public/xcj/Projects/openpi/data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_2_15hz_s2m_master_v3_source_frame_aligned_smoke

metadata/command实际位于meta/memory/command.txt，记录commit773d177、作者cwd和当时运行命令；当时用旧full_t_plus_1 YAML只校验转换契约，样本不作为正式训练配置交付。此次真实数值调用使用审查HEAD的新full_current_feedback和serial_lag30 YAML。

| 项目 | ep0 | ep1 |
| --- | ---: | ---: |
| raw JSON与每路raw视频帧数 | 2410 | 2991 |
| v3每路视频/完整source mapping行数 | 1217 | 1510 |
| Parquet query行数 | 1216 | 1509 |
| 无phase GT的query行 | 30 | 69 |
| 独立配置边界query数 | 30 | 37 |

1. 不调用作者选帧helper，以每个目标时刻 timestamp[0]+k/15 对全部raw timestamp求绝对距离argmin，复算完整selected mapping，逐项等于sidecar。索引严格递增；Parquet observation/action source indices分别等于mapping[:-1]/mapping[1:]；各source timestamp逐值相等，query frame_index保持0..M-1。
2. 直接从raw JSON按左position/rotation/gripper、右position/rotation/gripper拼14维，2,725行state逐值等于当前selected follow、action逐值等于下一selected master，最大float32误差0。同raw帧follow/master最大差ep0为4.49447、ep1为1.96506，验证没有把follow误作action。current raw phase/availability依subtasks半开区间独立展开，Parquet和sidecar前M行全部一致。
3. 实际CPU ffmpeg解码两集三相机，各10位置，共60位置：q=0/1/23/100/floor(M/2)/765/1205/M-2/M-1/M。raw候选在声明映射n附近±25帧，raw/converted分别scale=320:240,format=gray后计算像素MAE；未依靠帧数作为唯一证明。声明映射的MAE全在1.0317–2.2024。运动/原漂移位置均与预期raw index精确匹配；少数静止首尾帧邻近帧有小于0.06的MAE差异，属于重复/近似图像与有损编码下无法仅按argmin区分的情况，不将这些位置声称为唯一像素匹配。

ep0 face 原问题点的本轮证据（新v3图像对候选raw帧的MAE，与旧报告缩放方式不同，不跨报告直接比较MAE数值）：

| query | 正确source | 正确MAE | 原v2实际source | 对原错误source的MAE |
| --- | ---: | ---: | ---: | ---: |
| 23 | 46 | 1.9888 | 43 | 6.2712 |
| 765 | 1515 | 1.8763 | 1527 | 12.1389 |
| 1205 | 2387 | 1.5923 | 2407 | 5.0308 |

同三位置left/right wrist也均选择正确46/1515/2387。q765 right wrist对正确source MAE=2.2024，对旧1527为38.3557，具有明显区分力。ep0额外保留的视频末帧也实际匹配raw2408。

4. decoded n 与 JSON row 的依据另有源端契约：raw header为robot-bridge-v260630，.done记载同版multipart和总帧数；只读核对robot-bridge主库的docs/reference/data-collection-format.md和scripts/mcap_to_training.py，source转换在同一head-camera frame_ts循环追加JSON并为每个camera写一帧，腕相机按同一时刻取nearest。raw三路均完整解码且帧数与JSON逐集相等，结合上述具体像素匹配支持n=row索引假设。此项没有重新打开MCAP，未声称测量传感器物理同步误差。
5. 转换metadata保留172 accepted/72 rejected，非互斥原因label6=28、非1..5恰一次=56、缺标注=16；次序120正常/52交换1与2。固定offline5恰为accepted前5，且都属于训练合格集，没有holdout。复制的annotation_layers与两集subtasks文件逐字节等于raw。沿用已验收全量筛选结论，不重扫/转换所有视频。

**配置与缺GT边界**

a75d173 full为当前reference输入、首次/缺GT用initial unknown、infer cache，目标q+j+1，chunk_completed/last_executed反馈，phase只按其自身目标越界/availability mask、固定H分母，不套sim的q+30公共约束。serial为同一named previous lag30、负索引或缺GT用initial、目标当前q、train current_condition reference/infer selected、query_selected/query反馈，不按未来q+30屏蔽。两者同domain、独立argmax、H50/K30、robot offset0/stride1。

用两集真实缺GT前缀/阶段间隙、q0/29/30/31及语义边界前后、最后query共67个query验证输入/目标/mask；无GT只屏蔽phase，所有robot target/weight保留，robot尾部按末动作clamp。上述P2尾行缺口是数据序列长度问题，不是新YAML错误。

定向测试（审查树执行）：
```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q -p no:cacheprovider examples/x2robot/test_wash_cup_memory_adapter.py examples/x2robot/test_wash_cup_memory_config.py examples/rmbench/test_rmbench_memory_adapter.py::test_sidecar_metadata_records_command_context_and_only_actual_binding
# 12 passed in 11.24s
git diff --check 69ca148..HEAD
```

尾行问题最小复现（不改共享产物）：
```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python - <<'PY'
import json
from pathlib import Path
import pyarrow.parquet as pq
from openpi_client.memory_config import EpisodeMemoryData, load_memory_config
root = Path('data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_2_15hz_s2m_master_v3_source_frame_aligned_smoke')
e = json.loads((root/'meta/memory/raw_episode_memory.json').read_text())['episodes'][0]
a = pq.read_table(root/'data/chunk-000/episode_000000.parquet', columns=['actions'])['actions'].to_pylist()
mem = e['memory']
episode = EpisodeMemoryData(series={'phase': mem['series']['phase'], 'robot_action_target': a}, availability=mem['availability'])
c = load_memory_config('examples/x2robot/memory_configs/wash_cup_phase_full_current_feedback.yaml')
print(len(a), len(e['video_source_frame_indices']), len(mem['series']['phase']))
print(e['video_source_frame_indices'][-1], mem['source_phase_ranges'][-1])
for q in (len(a)-30, len(a)-1):
    print(q, int(c.make_training_sample(episode, q).target_mask.sum()))
# 当前：1216 1217 1216；最后raw2408位于label5 [1710,2409)
# q1186得到29（应30）；q1215得到0（应1）
PY
```

本轮发布的是阶段审查，未验收正式172集新输出或训练模型wire；未把整个数据任务标记完成。上一阶段sim详细证据保留如下，其wash状态由本轮更新覆盖。

---
**上一阶段历史记录（publication 2e8437d975d3278791846c233dd829d6acf0fc1e，task revision 5dcc6240831df11028fb4be6bd4de7a1f8a86e60）**

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
