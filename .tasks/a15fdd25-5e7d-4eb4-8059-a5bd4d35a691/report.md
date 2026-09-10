task_revision: b97432188b17d8b51ba6dfbcc423d8adf2cebf9d

完成：四个F0正式run均已完成100条、核验并归档job，无本任务活跃进程。row50本轮最终核验38/100；前三run沿用已验收结论，没有重跑评测或全面诊断。GPU1释放检查通过，可移交e690。全部F0结束后已提交最终实验README；workspace保留，等待Manager集成/归档。

| run（H50/K30） | GPU | 最终结果 | 原runner PID；已归档MAM job |
| --- | ---: | ---: | --- |
| row30 | 0 | 92/100 | 1933083；a19ad5c6-4449-41c3-a077-2d67e80c5286 |
| row20 | 1 | 86/100 | 2227400；d358726f-3671-42d9-b3ac-801f15ddcdb7 |
| row1 | 0 | 21/100 | 2371167；2b4a98cd-a13e-4051-b466-dfc60c25bce4 |
| row50 | 1 | 38/100 | 2533991；b6ed2008-54fb-4056-86a9-6264abdec918 |

row50于2026-09-10 14:24:07.974 +08:00完成，比主历史93/100低55pp。失败首因为未按按钮57、第二块未到中间4、按压不足1；62个失败均为正常700步限制终止。100个连续成对seed、2017query（row50均标记模型预测未执行行）、前5视频、metadata/smoke身份及100个scheduler退出0核验通过，0候选拒绝/运行错误，全部自有进程已退出。总耗时11091.974秒，95个无视频完整周期均值102.662秒；最终完整结果保留，不改配置或删除失败。阈值解释沿用已完成的中点协议/基础设施调查，未发现运行异常。

GPU1移交条件已满足：15:00:29核查全部已知自有PID及本workspace/GPU0或1进程扫描为空，GPU1无计算进程，19310/19312无监听，快照1MiB/0%。GPU1可交e6908de7；GPU0先前已按要求释放供Carver 35c9e781。没有替接手任务启动进程。已用mam job list --task实时查询，本任务无未归档job；task status仅用于发布/缓存信息。

workspace：/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691

实际交付commit：

- RMBench：fad91fb2c874443ffa0894bba70d16c8173eeb36。
- robot-bridge：bc842036e3735390f35fe1138aa7b19f5ae2f95b。
- openpi：58d6f2155acc3af03017677bb3f536101e6699f4。

RMBench fad91fb2为全部F0进程退出后的纯文档提交，只修改experiments/memory_chunk_20260910/README.md。四个run的RMBench实际运行来源仍是f022badd11228e5763a301339a5d1fe5574962b4，运行metadata不回写为文档commit；bridge/OpenPI源码未变。

README交付内容：四run最终结果/失败分布/时序、固定协议与完整运行commit、主RMBench真实产物路径、直接执行命令、严格smoke门禁与人工中点规则、P1/F0时序区别、清理边界及MAM实时查询方式。按要求新增README_memory_schema.zh-CN.md导航，目标已在主xcj-dev验证存在，本分支仅加链接、不复制正文或合入新runtime。doc仅在F0全部结束后修改；表格数字与已有最终JSON对照、链接目标和git diff --check均通过，三树工作区干净，没有为文档重跑GPU smoke。

正式证据的真实目录（各目录均有final_review_0100.json、config.yaml、command.txt、checkpoint_metadata/及smoke结论/清理记录）：

- /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_100ep_seed0/
- /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row20_100ep_seed0/
- /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row1_100ep_seed0/
- /mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row50_100ep_seed0/

GPU1交接证据为row50目录gpu1_handoff_verification.json；此前GPU0交接证据在row1目录。主历史基线仍为/mnt/public/xcj/Projects/RMBench/eval_result/pi05_rearrange_shared_memory_representation/full_key_state_seed0@ckpt30k_step30_100ep_seed0/的93/100；同seed前50只作辅助。中点与逐query细节见各run JSON及历史publication，不再复制展开。

清理完成：四个F0 smoke原始目录均已删除，保留正式metadata门禁结论、smoke_gate_summary.json及smoke_cleanup_receipt.json，不保留整包压缩档。全部F0结束后也清理了已无后续门禁用途的旧P1加载smoke，原结论/检查摘要和清理receipt保存在row30正式目录legacy_p1_smoke_summary.json、legacy_p1_smoke_cleanup_receipt.json；未重新评测。其他任务的BF16产物未触碰。

后续：本任务已无评测或轮询工作；由Manager完成最终文档集成及workspace归档。新schema、BF16与GPU接手任务继续由各自owner负责。
