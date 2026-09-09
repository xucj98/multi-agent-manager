task_revision: eab68403016a134e3e99f012e3155d795663b814

# ffa308d 组合审查：CPU阶段新增发现（继续审查中）

完成与未完成：

- 审查树已合入固定训练提交 ffa308d5485a2c8222d3e7735b08723c6e93a237；真实 review HEAD 为 63be08cace87282eb560496b760455c07be8dbb4，git diff ffa308d HEAD 为空。原489阶段的缺失接口已由本次组合接入，不再作为当前发现。
- 按 full / serial / no-memory / aux 分路验收。full已通过独立真实PaligemmaTokenizer条件检查、训练/推理token一致性、P2 batch数值loss及梯度检查；但下列R1影响其自包含恢复，当前待修复及作者full GPU证据。serial另有R2。R3只阻塞aux，不阻塞首批full。no-memory沿共用模型路径，无额外50step要求。wash/live不作为full开跑依赖。
- 尚在继续：真实数据adapter索引、serial模型实际动作条件与wire、最终update计数/保存证据；GPU1 full和serial各50step由作者顺序提供，runtime联通由Einstein/Pascal提供。此报告先发布可复现问题，非最终完整放行。

新增可定位问题：

1. **R1 / P1 / full、serial、no-memory共用：推理factory仍打开训练norm。** training/config.py:1004-1015 的 training=False 分支仍调用 data.create → create_base_config:208 → _load_norm_stats:230，读取原 data.assets.assets_dir 下的 norm_stats.json。policy_config.py:59 在加载 checkpoint assets:65 之前执行该factory。独立测试使用实际full配置、有效checkpoint/assets，并在全新进程禁止训练norm/data/sidecar/YAML访问，得到 TRAINING_SOURCE_READ（源 norm_stats.json）。原norm目录不可读、格式变化或维度变化仍可使有完整checkpoint assets的加载失败；URI资产还会触发不必要下载。需让普通推理构造transforms时不读取训练norm，使用checkpoint携带的统计。
2. **R2 / P1 / serial：真实TrainConfig不能从保存的YAML恢复。** models/pi0_config.py:92-98 在 __post_init__ 校验 tuple[Mapping] decoder_rules，而tyro/PyYAML此刻还只构造出 ({}, {}, {})；load_train_config直接抛 ValueError: each key_state_decoder_rules entry must be a mapping with a string kind。用真实 pi05_rmbench_rearrange_blocks_serial_lag30 和真实 checkpoint_metadata.save/load 即可复现，无stub、无GPU。full/no-memory相同roundtrip通过。需在嵌套mapping完成构造后验证，且保持唯一resolved schema。
3. **R3 / P1 / aux：合法source: initial无法构造adapter。** training/memory_data.py:195-198 为所有 train input 无条件索引 input_spec["mask"]；core对source: initial的合法resolved项只有source。将实际full配置各字段train/infer改initial、feedback updates清空，TrainConfig成功但create_data_config报KeyError: mask。须先按source区分；修复后还要验证policy遵守infer initial而不消费传入的非initial cache（当前AttachMemory只使用IDs/model_spec，尚未证明该协议约束）。

已通过的独立证据：

- checkpoint metadata 3d4fe31→cc706e37：新增3测试通过；未重复tiny cast。独立metadata_review_probe.py使用真实rearrange/put-back目录：dataset meta各8文件（304571 / 277972字节），sidecar metadata各17文件（741466 / 890008字节），SHA256逐文件完全一致；root episode_memory/视频/Parquet/源码未复制。真实command argv/env/cwd可还原。全新进程禁止训练来源后metadata加载通过（不等同于policy全链路通过）。
- 实际full transforms使用真实SentencePiece/PaligemmaTokenizer、同robot/images/prompt、memory [0,0,0]与[2,1,2]：token条件不同；memory one-hot维持identity、机器人部分相同，真实data_loader.transform_dataset与推理token一致。原始50x32输出解码后actions为50x14，memory_prediction_ids为50x3且保留第30行。
- 真实Pi0.compute_loss（只控制velocity/trunk输出，保留原preprocess/loss/autodiff）独立B=2/H=50/D=32测试：lambda=.25、valid_mean非单位系数、M-30与M-29末尾、P2两臂公共mask与robot targets一致；解析梯度=2w/(BHD)，phase全invalid不清机器人loss，padding梯度严格0。
- 实际Pi0默认serial decoder：previous=[3,1,0]可选[0,2,2]，与公共spec decoder独立argmax一致，无旧phase递增/button约束。
- 作者新增pipeline/model/config/policy测试以 -m 'not manual' 执行：14 passed, 2 deselected。覆盖被作者 -k 'not infer and not broker' 漏掉的 test_policy_uses_inference_data_config_and_runtime_memory_metadata；其余作者总数仅作输入证据。
- 本任务独立combined_review_test.py：5 passed, 3 failed；三个失败即R1/R2/R3，不是测试环境失败。

workspace、各库交付 commit：

- openpi: /mnt/public/xcj/Projects/workspace/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/openpi；复用原独立.venv。
- review HEAD: 63be08cace87282eb560496b760455c07be8dbb4（与ffa308d5485a2c8222d3e7735b08723c6e93a237文件树一致）。
- 未修改openpi实现、未派agent、所有测试显式CUDA_VISIBLE_DEVICES='' / JAX_PLATFORMS=cpu。
- 用户收窄跨库分工的通知前，上一轮已登记robot-bridge f84edbd6eea81104a00fd85409046eaaa8712e9b工作树；本轮不使用、不测试它，交Manager归档时处理。

验证结果与成果位置：

- 独立复现脚本在本report同目录：metadata_review_probe.py、combined_review_test.py。
- 复跑（从上述openpi根）：
  env CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 OPENPI_DATA_HOME=/mnt/public/cache/openpi HF_HUB_OFFLINE=1 HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot .venv/bin/python -B -m pytest -q -p no:cacheprovider /mnt/public/xcj/Projects/multi-agent-manager/.tasks/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/combined_review_test.py
- 测试cache仅在reviewer /tmp/review-9b73-*，结束统一清理；业务库无实现修改。
