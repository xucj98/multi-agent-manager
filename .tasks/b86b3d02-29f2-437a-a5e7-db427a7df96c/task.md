# 通用 schema offline 验收路径

## 目标
让新wash-cup单phase full/serial与旧drawer双字段通过同一套offline代码及memory配置工作；差别来自配置，不能另写wash专用推理/反馈/GT算法。只修公共offline接口，不改变正在训练的源码/进程或仿真已验收路径。Manager希望本机07:27左右新模型结束后即可安排offline，先给简短范围和预计耗时，再实现。

## 工作区与代码基线
在本任务独立workspace创建robot-bridge worktree，base bd30069ffc0b773de13f98f53753566711960858。如需读/改openpi，创建其独立worktree，base a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。先读MAM入口与本地说明、目标库AGENTS及robot-bridge/docs/design/conventions.md。不要改其他agent运行中的worktree。MAM主根 /mnt/public/xcj/Projects/multi-agent-manager，任务/报告发布project/state-vla；不要修改MAM工具。

## 已有证据与输入
先读任务e6908de7-4b02-465a-987b-a19eba7a315a最新报告（9e975497），及其RMBench/experiments/memory_chunk_20260910/README_memory_schema.zh-CN.md在3e69b1e提交中的队列/真实路径。旧bridge8ea脚本scripts/launch/drawer_offline.py限制旧5ep、H30/K15、固定checkpoint根；scheduler/openpi_offline.py和controllers/x2robot_offline.py的memory指标仍旧格式。请基于新base确认具体适用位置，不机械改行号。
wash训练owner ad6bb77e-3892-4730-ae1a-7d9cd99a5728最新task/report：两20k checkpoint目录、v3 source-frame-aligned全部172ep，固定LeRobot index0–4，S2M单phase，H50/K30。使用已固定的5集，不拆分训练验证集，不重选数据。旧drawer两个模型与5ep[1,22,23,24,26]已有已验收结果，保持原配置行为。

## 实施边界
- 在既有offline启动/manifest入口用配置指定episode、H/K、checkpoint根，保留process/exit/metadata管理，不复制launcher、不另建调度器。
- 复用checkpoint的memory_config、现有MemoryContext，以及共享样本目标/时间和mask逻辑；训练/推理/offline不能各自重新定义offset。full逐帧(t+j+1)、重复终点和serial当前query语义按配置；S2M机器人action对齐沿既有action_at_row/offset0，不重复移位。
- memory预测、可用性mask及GT接入现有offline评估产物，支持单/多字段。GT仅用于评估，不注入policy输入/反馈。不要把action-only跑通冒称memory offline已验收。
- 保留真机wait-condition get_obs、execute/takeover/reset和已有反馈机制，不扩展session或plugin架构。
- 产物留RMBench/eval_result/memory_chunk_20260910/<run>，逐步保留命令/commit/config及转换/训练metadata；不要复制源码或改checkpoint原件。

## 验收与交付
本轮不占GPU。做有意义的CPU边界测试：相同配置目标与训练样本时序一致、mask缺失正确、单/双字段与不同H/K，旧drawer配置不变；真实5ep输入/文件映射与命令dry-run。不要重复全量转换或旧模型测试。若必须改变算法或需大量重构，先提出具体证据/最小方案供Manager裁决。提交代码和简短报告，列文件/commit、测试、剩余GPU验收及可复制命令。清理自己的临时文件，保留workspace供Manager安排空白独立review；不要自己充当独立review或再建review任务，不自行合并部署。

## 9月11日07:22 Manager裁定：独立review修复
读取review任务65a3c29f-08c0-4025-8c29-c4567b26f775的report草稿/发布稿。接受P1：实际policy源码clean门禁与顶层留痕不能来自checkpoint root alias；须绑定--policy-python实际导入的OpenPI源码，且和served_metadata现有provenance校验。用最小CPU探针解析模块根/commit及解释器；复用现有git检查与served字段，不另造依赖快照或provenance框架。探针不加载模型/不占GPU。任意实际源码dirty或握手不符必须在episode执行前拒绝并正确回收服务。
接受P2：dataset与expected_policy_metadata/expected_execution_rows同时出现时，冲突明确报错；新wash manifest删除重复时间字段，只保留一个来源。支持旧drawer现有manifest，不改变其有效参数。
范围收敛：删除当前输入未用的--replay任意选节；保留必要的OpenPI/RMBench root映射及旧格式适配，不为了删行数重写整个launcher。不要增加新的通用配置格式。已有memory指标算法CPU review通过，除具体错误外不改controller/scheduler。
更正报告计数：5525是逻辑执行行/模型，K30对应各集41/51/24/38/33次infer，共187次/模型；此前报告的5525 query不可当成实际infer次数。正式GPU最终按实际日志验证。
提交小修并发布report，给出新增失败保护的定向CPU测试及新commit。目标20分钟，若需要扩大范围先说明。仍不占GPU；Manager交原独立reviewer复查后分配wash offline。本任务实现完成后允许继续负责本代码的GPU offline，但必须等Manager明确授权与checkpoint通过。
