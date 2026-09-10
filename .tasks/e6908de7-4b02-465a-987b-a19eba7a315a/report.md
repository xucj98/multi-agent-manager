# 06:53正式仿真安排：八份20k CPU准备完成，等待本机释放

task_revision: 1ecd0431d361e738b25ab5aba43e07aa0b1b729a

复用原三树/干净版本，无新代码提交。训练owner已发布远端八份最终20000保存和CPU全参数门禁通过。本轮对这八份实际checkpoint逐项运行原入口 --prepare-audit、smoke --dry-run、formal --dry-run（共24次），全部exit0。metadata→Context验证H50/K30、schema/字段/反馈和demo_clean_state来源，审计生成物仅在本worktree .local/memory_schema_eval；未改写checkpoint，未加载GPU模型。

已准备：rearrange t+1/t+30 seed0/1、put-back t+1/t+30 seed0、serial/no-memory seed0。每份实际CPU输出保留于 RMBench/.local/memory_schema_eval/cpu_20k_20260911，既有manifest/evidence位于其inputs同级目录，开跑后由config_source继承到结果run。

首批按发布分配：GPU4=rearrange t+1 seed0（19440/19442），GPU6=rearrange t+30 seed0（19460/19462），GPU5=put-back t+1 seed0（19450/19452），GPU7=put-back t+30 seed0（19470/19472）；各卡独立Warp缓存。仍须owner发布各卡保存/退出/释放且启动前显存确认才执行。GPU0/1不抢占，GPU2/3留wash，wuwen-1停用。

目前八份仅CPU准备完成，GPU smoke/formal尚未启动，无本任务GPU job。保持active turn，通过mam wait等待训练结束事件，再读取owner释放报告；不得将事件或ETA本身当作释放授权。正式运行将登记各job、做50条诊断与100条收尾。旧配置/训练步数不一致的F0成绩不作强制可比基准。

下文保留前轮CPU队列与wash接口交付；wash公共修复由Manager协调，本轮专注正式sim。

---

# 9月11日04:32 CPU评测准备交付

已准备：原README新增14个仿真模型的checkpoint绝对路径和28个独立run名，12个Q2按seed0/1/2、每seed rearrange与put-back各t+1→t+30成对排队，最后serial/no-memory基线。补齐put-back seed2；继续复用原prepare-audit/smoke/formal命令、既有runner/recorder，不新增launcher或调度框架。

每checkpoint须完成保存、owner验收后才准备audit并执行自身smoke2（同run video/no-video）→门禁/产物核对→单GPU串行formal100，第50条按既定10个百分点约定诊断。共同eval候选seed100000起，不按成绩筛选，未就绪整对保留等待项。GPU只允许后续Manager分配的本机空闲卡；wuwen-1结束后停用。

wash已准备输入映射：两20k目标路径、计划结果run、固定LeRobot index0–4及对应原始episode全名见README。按owner“全172ep训练、offline前5ep”要求，从v3 conversion.accepted_episode_ids读取，未另选episode。五集query数1216/1509/702/1115/983（训练长度，不是已完成offline帧数）。五份raw JSON、anno/subtasks.json和15份相机MP4均存在。未扫描全量视频。

## 实际公共接口缺口，需Manager裁定

固定bridge 8ea的scripts/launch/drawer_offline.py：64–65拒绝除旧[1,22,23,24,26]外的episode列表；111–112要求15Hz/H30/K15；123固定move_steps15；90仅支持RMBench checkpoint根。新wash为index0–4、H50/K30，checkpoint在共享OpenPI，不能通过只换manifest运行。现有交互式test_pi0_offline_e2e.sh可起通用服务，但不能补齐下述新memory评估留痕。

底层OpenPiOfflineScheduler已有MemoryContext/S2M反馈，但robot_bridge/scheduler/openpi_offline.py:291–305只配置旧memory/key_state，478–482只为旧memory路径发送评估memory_prediction。robot_bridge/robot/controllers/x2robot_offline.py:499–502只建立旧drawer GT，639–646要求旧双字段固定宽度(执行行数,6)/(1,2)。新wash单phase memory_config无法沿该路径生成完整memory指标/mask；不把action-only运行当新wash offline已验收。

最小修复建议交公共owner：在原offline入口允许manifest定义episode/时序/checkpoint根，保留既有process/metadata/exit管理；在现有controller/scheduler评估接线复用新schema预测及v3 sidecar phase/availability/query-source索引，机器人目标沿已对齐action_at_row/offset0、不二次移位。保留原MemoryContext反馈，不另造wash实现。本任务未改bridge/OpenPI，没有伪造可运行的wash命令；wash命令交付受此接口缺口阻塞，待Manager决定修复范围后继续。

## CPU验证与版本

JAX_PLATFORMS=cpu、CUDA_VISIBLE_DEVICES为空、PYTHONDONTWRITEBYTECODE=1，原OpenPI解释器-B：六类sim配置的repo/schema id/representation/fields与本组规范匹配，MemoryContext均H50/K30；wash两配置Context为H50/K30、单phase。仅解析配置，没有加载权重或做模型infer；尚未对未交接的最终20000运行checkpoint dry-run/audit，这些仍是开跑前门禁。

检查14行checkpoint config/exp_name/seed映射、28个run名唯一且未占用；git diff --check通过。只提交原README（76增/3删），三树干净，未创建临时audit或结果缓存。

workspace: /mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a
- RMBench: 3e69b1e665a8eac0104d261b233f1b3339007e00
- robot-bridge: 8ea6078543a875b5ae223df16891cdc1fe975c66
- openpi: a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4

读取的训练报告发布版本：
- sim owner: a42a004a422c3c0793fc25c41b7996451c9bbd47
- wash owner: a6958430f0a8165a0ee89b38572b1b39445864a5

成果: RMBench/experiments/memory_chunk_20260910/README_memory_schema.zh-CN.md。
本轮已运行仅CPU检查；未启动GPU、smoke/formal/offline，未巡检训练日志或GPU，未登记新job。旧技术验证与drawer结果未重跑，历史已验收结论和清理见report publication 391a9ed18000a98da4f27081e9187aac914c067f。原三树与正式drawer产物继续保留。sim队列已准备，等待checkpoint交接/GPU分配；wash等待上述公共接口裁定，当前不承诺修复耗时。
