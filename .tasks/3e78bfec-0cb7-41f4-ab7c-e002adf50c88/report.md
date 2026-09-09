task_revision: cddadf8ac605013b664bb8a5cc405f80162b9853

**最终结论：数据与中文操作文档 GO，本数据 review 已完成，可归档作者/reviewer workspace。**

正式172集产物通过最终数量、metadata、低维和固定5集验收；此前S2M动作源、视频/pose漂移、M+1末帧缺失问题均已关闭。中文操作文档补齐并通过。本轮没有数据侧阻塞或待补交项。训练模型、GPU/live与模型字段接入由对应owner/review裁定，不作为本数据任务归档前提，也不在本报告中宣称已通过。

本轮基准为作者最终report `78bf2d4f16c97fa8835ca34b909c78fbcc7c0d78`。复用原独立树 `/mnt/public/xcj/Projects/workspace/3e78bfec-0cb7-41f4-ab7c-e002adf50c88/openpi`，从46e619e fast-forward到文档提交 `377ddff2279180092ae72f42945af4f758ac20e5`；此次diff只有examples/rmbench/README.md与examples/x2robot/README.md。正式转换冻结commit仍为 `46e619e6db6bcd4f9d5d11d31b82e5f51e8522a0`，没有把后续文档commit误记成数据生成版本。

**正式产物与本轮独立读回**

稳定目录：`/mnt/public/xcj/Projects/openpi/data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_172_15hz_s2m_master_v3_source_frame_aligned`。

| 项目 | 实际独立核验结果 |
| --- | ---: |
| episodes / Parquet文件 | 172 / 172 |
| LeRobot query行 | 143,698 |
| M+1 sidecar行合计 | 143,870 |
| query中phase不可用行 | 13,944 |
| M+1尾行中phase不可用行 | 98 |
| 视频文件（仅路径/stat，不解码） | 516，三相机各172，全部非空 |
| source annotation副本 | 172，逐字节等于raw |
| 正式目录文件总字节数 | 2,435,751,136（约2.27 GiB） |

- meta/info.json、episodes.jsonl、episodes_stats.jsonl、完整sidecar以及实际Parquet文件的episode索引/长度一致；frame_index逐集0..M-1、全局index连续0..143697。视频相对路径集合严格等于三相机×episode000000..000171，无缺失、额外或空文件。本轮没有用stat结果替代先前的实际视频映射验收；视频正确性沿用已通过的固定代码和两集三相机60位置审查。
- 正式172集低维列独立读回：所有state/actions为有限M×14；sidecar phase、raw_series、availability和robot_action_target等长M+1。robot前M行逐值等于Parquet actions、末行重复末动作；observation/action source映射分别为完整selected[:-1]/[1:]，selected时间戳和query/action时间戳对应。没有新增query、删掉缺GT query或二次动作移位。
- 从172份实际raw subtasks半开区间独立重建selected索引上的phase/availability，与正式sidecar及Parquet前M行全部一致，得到13,944+98两类不可用数。缺GT的semantic/raw值为unknown，availability=false；两种合法次序仍为120集1>2>3>4>5、52集2>1>3>4>5。172 accepted和72 rejected唯一且互斥，正式selected/processed列表恰好等于accepted列表。
- 必要raw数值读回覆盖episode 0/1/2/3/4/86/171：七集全部selected timestamp按独立最近邻复算一致；当前follow和下一selected master的14维值逐行等于正式state/action，float32最大误差0。七集source header均为robot-bridge-v260630、30 Hz；包含两种phase次序及数据中后段。另核对所有episode的state/action stats count/min/max与Parquet一致。
- 两个曾经阻塞的末帧在正式产物仍正确：ep0末raw2408为label_5/true，full(q=M-30,M-1)有效数[30,1]；ep1末raw2989为unknown/false，有效数[20,0]。本轮只用公共core读取低维样本，没有重跑旧测试套件。

**固定5集、metadata、命令与清理**

conversion.selection.offline_episode_ids严格等于accepted前5，且都出现在正式训练Parquet中；info.splits为train=0:172，未划出holdout。固定5集共5,525 query，完整ID如下：

| episode / query数 | ID | phase次序 |
| --- | --- | --- |
| 0 / 1216 | wash_cup_auto_wzy_0831@wash_cup_pi05_sm2sm_15hz_h3f3oro_a30_dm10dh30po20_bs64_steps30k-29999@2026_08_31_11_24_04 | 1>2>3>4>5 |
| 1 / 1509 | wash_cup_auto_wzy_0831@wash_cup_pi05_sm2sm_15hz_h3f3oro_a30_dm10dh30po20_bs64_steps30k-29999@2026_08_31_13_02_42 | 1>2>3>4>5 |
| 2 / 702 | wash_cup_auto_wzy_0831@wash_cup_pi05_sm2sm_15hz_h3f3oro_a30_dm10dh30po20_bs64_steps30k-29999@2026_08_31_13_12_09 | 1>2>3>4>5 |
| 3 / 1115 | wash_cup_lyw_08_18@MASTER_SLAVE_MODE@2026_08_18_14_29_42 | 2>1>3>4>5 |
| 4 / 983 | wash_cup_lyw_08_18@MASTER_SLAVE_MODE@2026_08_18_14_31_08 | 2>1>3>4>5 |

meta/memory/command.txt记录真实46e619e完整commit、作者执行cwd、显式raw source、output-base=data/lerobot、新full_current_feedback YAML及15Hz/320×240/H264/8workers实跑参数；无max-episodes限制或refresh-only标志。conversion.json version4记录S2M master/offset0、M+1布局、JSON source-clock和ffmpeg source-index选择；episode memory version2。annotation_layers与172份subtasks副本逐字节等于其source路径；无独立git_commit.txt或候选training configs目录。正式目录不依赖即将归档的作者workspace，command中的历史cwd/Python路径仅作provenance。

正式关键metadata SHA-256：

- command.txt：`3b94c5778b38b7850986955ac51ff4d0ec7a8918a4462b334c10f317215183f4`
- conversion.json：`834c9cb32f2248930b6cad7d9160fe4bf88caba1ef19406e380c071f8f826857`
- raw_episode_memory.json：`24fa39433dc0f097715e2d08d1b348dfa2ffb1854a3c2de18726f37650e2eebc`

MAM task status确认作者转换job `0ef32d88-c3fa-41df-b93c-d01379c20e70` 已archived，probe为stopped。当前wash产物父目录只剩正式v3目录，旧错误/技术smoke及incomplete目录均不在；本review未对raw源执行任何写入。

**中文文档验收**

377ddff的两份README均为中文，源码脚本、memory YAML和共享数据路径与当前代码/实际产物一致。wash说明完整筛选、缺GT处理、follow→next master、JSON共同映射、M/M+1、正式数量/commit及覆盖保护；RMBench说明仅用demo_clean_state、拒绝lagged input作current truth、action offset0、M+1与query范围以及六份配置。命令从项目根执行，显式给source，不依赖export根路径变量；已运行两个实际脚本的--help确认命令入口及参数存在，未执行README的生成命令。重新生成须换run-name，不能覆盖已验收正式目录。sim此前已通过的数值/配置及63319ac metadata结论保持，不重跑100集检查；训练侧no-memory按空memory字段选择binding的既有边界保持。

本轮验证用本树.venv、PYTHONDONTWRITEBYTECODE=1、CUDA_VISIBLE_DEVICES=''、JAX_PLATFORMS=cpu，独立内联脚本只读取JSON/Parquet数值与文件stat；未打开视频、未重编码、未运行训练/GPU或派agent。作者24tests通过是其最终report中的验证，本轮未冒充重复执行。`git diff --check 46e619e..HEAD`与工作树状态检查通过，原交付代码无本地修改；临时脚本/cache清理完成，两个workspace留给Manager归档。

本轮数量/两个边界的简短复现（在审查worktree执行，无视频解码）：

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python - <<'PY'
import json
from pathlib import Path
import pyarrow.parquet as pq
from openpi_client.memory_config import EpisodeMemoryData, load_memory_config
r = Path('data/lerobot/wash_cup_x1pro_s2m_memory_v1/all_172_15hz_s2m_master_v3_source_frame_aligned')
episodes = json.loads((r/'meta/memory/raw_episode_memory.json').read_text())['episodes']
files = sorted((r/'data').rglob('*.parquet'))
print(len(files), sum(pq.read_metadata(p).num_rows for p in files), len(list((r/'videos').rglob('*.mp4'))))
print(sum(len(e['memory']['series']['phase']) for e in episodes),
      sum(e['memory']['availability']['phase'][:-1].count(False) for e in episodes),
      sum(not e['memory']['availability']['phase'][-1] for e in episodes))
c = load_memory_config('examples/x2robot/memory_configs/wash_cup_phase_full_current_feedback.yaml')
for e in episodes[:2]:
    mem = e['memory']
    m = len(mem['series']['phase'])-1
    ep = EpisodeMemoryData(series=mem['series'], availability=mem['availability'])
    print(e['episode_index'], mem['series']['phase'][-1], mem['availability']['phase'][-1],
          [int(c.make_training_sample(ep, q).target_mask.sum()) for q in (m-30, m-1)])
# 172 143698 516
# 143870 13944 98
# 0 label_5 True [30, 1]
# 1 unknown False [20, 0]
PY
```

历史问题与验证记录已保存在此前发布版本：7f4d74e记录视频映射通过及发现末行缺失，144a37e记录46e619e修复后的M+1边界GO，2e8437d记录sim独立核验。上述历史待交状态均已关闭，不再作为当前结论。当前正式172集与中文README均已验收，无剩余数据侧事项；可合入377ddff并由Manager归档两数据workspace。
