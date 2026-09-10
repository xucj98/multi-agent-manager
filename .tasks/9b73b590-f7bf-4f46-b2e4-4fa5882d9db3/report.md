task_revision: cd4af5bb686e9e0c54962a07cab81dd597aea4c5

完成与结论：**d49c1a1 的 R3、R4 均通过定向 CPU 复核，可以关闭。本阶段完成，无新增阻塞。**

历史 CPU 结论引用本任务 publication 6a328471cd1493e21c3bc617b0f697b445a17a96。按最新 task，Manager 后续已验收 full/serial 实际 GPU50、BF16 保存/恢复及 put-back norm/loader，首批八路固定 d10 的正式训练保持既有放行。本轮未重测、未修改它们；尚未交付的 wash 训练注册另待确切增量。

workspace、审查版本：

- 复用 /mnt/public/xcj/Projects/workspace/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/openpi 及原 .venv。
- 候选 d49c1a1c5cb141283cb10634cfb31903624ed761；真实 review HEAD beb1741ac7f121d8b82f379444860fa8875bb1ee，git diff d49c1a1 HEAD 为空。候选父级含已交付的 42011a3 数据/文档，此次只判断 R3/R4。
- 未修改交付实现、未用 GPU、未派 agent、未创建环境。已登记的 robot-bridge 树未用于重复跨库验证。

R3 证据：

- 原全 initial 复现通过。新独立检查将字段 initial 特意设为非零 [3,2,1]，覆盖 full/serial 各自的全 initial、部分 initial/其余 cache，以及仅 infer initial、train 保持 reference，共 6 项。
- 实际 TrainConfig.create_data_config、MemoryDataAdapter.make_row、data_loader.transform_dataset 与推理 input transforms 均执行；使用已有 robot norm 和真实 tokenizer。全 initial 忽略两组合法非initial请求，full tokens相同；部分 initial 仅覆盖声明字段，其余 cache 仍改变 full tokens。serial 消费的 key_state_input_ids 与声明逐字段一致。
- 真实采样和训练 transforms 保持 train source 独立于 infer source；无 mask 的 initial 可以采样。对构造的81行 episode 在 q31 取样，再把 phase availability 全置 false，机器人50x14 target、归一化结果及全1 robot weights均保留；仅 phase监督被屏蔽。没有重跑原数据窗口/P2数值验收。

R4 证据：

- 原重叠 case 复现现与公共 spec 同得 [0,1,0]。新 batched JIT selector 在同一 batch 覆盖首个匹配、仅第二个匹配、无匹配 otherwise，并让第三字段读取第二字段已选结果；公共 decoder 与 Pi0 逐值同得 [0,1,1] / [0,2,2] / [2,0,0]。默认 argmax 对照仍等于独立 argmax。
- 复用原 SerialProbe，实际 Pi0.sample_actions_with_key_state、选择、current segment embedding 和 JAX sampling loop接真实 Policy.infer/transforms。上述三种条件均满足：统一 wire IDs = 公共 decoder 结果 = 真正传入 segment1 的动作条件；actions 为50x14且有限。
- 该 sampler 检查沿原 CPU 小trunk替身替代昂贵 Gemma/SigLIP/投影，并将 module_jit 包装设为 identity；没有冒称新的完整模型/GPU或硬件验证。

实际定向命令与结果：从上述 openpi 根执行，统一前缀为：

    env CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 OPENPI_DATA_HOME=/mnt/public/cache/openpi HF_HUB_OFFLINE=1 HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot .venv/bin/python -B -m pytest -q -p no:cacheprovider

其后参数及实际输出（临时脚本当时均位于本 report 同目录）：

| 检查 | pytest 参数 | 输出 |
| --- | --- | --- |
| 原独立复现 | combined_review_test.py remaining_review_test.py -k 'aux_initial_ignores_external_cached_ids or explicit_conditional_decoder_agrees_with_public_spec'（脚本传绝对路径） | 2 passed, 14 deselected，14.85s |
| 新独立边界 | d49_review_test.py（脚本传绝对路径） | 8 passed，21.21s |
| 作者新增回归 | src/openpi/training/config_memory_test.py src/openpi/training/memory_data_test.py -k 'conditional_decoder_uses_first_matching_schema_case or auxiliary_initial_input_needs_no_mask_and_ignores_inference_cache' | 2 passed, 11 deselected，13.97s |

收尾：5个本任务临时review脚本已在执行后清理，以上为实际执行记录。未跟随共享软链接，检查两worktree的非tracked源码cache：openpi仅有1个 .ruff_cache，已清理；robot-bridge为0个。共享数据/资产和原环境保留，两库实现工作树干净；环境/分支由Manager后续归档。本阶段可结束，wash候选到达时继续同一任务。
