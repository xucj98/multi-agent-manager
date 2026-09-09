task_revision: eab68403016a134e3e99f012e3155d795663b814

# ffa308d 组合审查：本轮CPU范围完成，待修复与GPU增量验收

完成与未完成：

- 审查树已合入固定训练提交 ffa308d5485a2c8222d3e7735b08723c6e93a237；真实 review HEAD 为 63be08cace87282eb560496b760455c07be8dbb4，git diff ffa308d HEAD 为空。原489阶段的缺失接口已由本次组合接入，不再作为当前发现。
- 按 full / serial / no-memory / aux 分路验收。full已通过独立真实PaligemmaTokenizer条件检查、训练/推理token一致性、P2 batch数值loss及梯度检查；但下列R1影响其自包含恢复，当前待修复及作者full GPU证据。serial另有R2。R3只阻塞aux，不阻塞首批full。no-memory沿共用模型路径，无额外50step要求。wash/live不作为full开跑依赖。
- 本轮剩余CPU范围已完成：真实数据adapter索引、serial模型实际动作条件与wire、最终update计数；没有新增firstfull计算/数据阻塞。R1/R2已由Manager裁定交Bernoulli修复，收到固定小commit后只增量复核。GPU1 full和serial各50step及实际保存/恢复产物尚无新发布报告，runtime真实联通也尚未收到已完成证据；因此本报告不是最终GPU/闭环放行。
- 保存与恢复可使用不同固定commit：如修复只涉及factory/YAML恢复，不要求重复已完成50次update，分别记录训练保存commit、恢复commit、原checkpoint与实际keys/shapes。full通过可单独放行；serial、aux、wash和live的未完成项不捆绑阻塞firstfull。no-memory不另加50step。

新增可定位问题：

4. **R4 / P2 / 仅显式conditional decoder：Pi0与公共schema的case优先级相反。** models/pi0.py:297-310逐case用jnp.where覆盖allowed，所以最后一个匹配分支获胜；公共memory_config.py:866-870命中首个立即返回。实际serial配置加入合法重叠case（previous.phase=unknown允许left；后续selected.phase=unknown允许right）后，相同logits/previous在公共spec得[0,1,0]，Pi0得[0,2,0]。会让serial动作条件与保存schema定义不同；当前默认argmax的full/serial均不走此分支，不阻塞firstfull。remaining_review_test.py::test_explicit_conditional_decoder_agrees_with_public_spec可独立复现；仅复核consumer一致性，未重审parser。

1. **R1 / P1 / full、serial、no-memory共用：推理factory仍打开训练norm。** training/config.py:1004-1015 的 training=False 分支仍调用 data.create → create_base_config:208 → _load_norm_stats:230，读取原 data.assets.assets_dir 下的 norm_stats.json。policy_config.py:59 在加载 checkpoint assets:65 之前执行该factory。独立测试使用实际full配置、有效checkpoint/assets，并在全新进程禁止训练norm/data/sidecar/YAML访问，得到 TRAINING_SOURCE_READ（源 norm_stats.json）。原norm目录不可读、格式变化或维度变化仍可使有完整checkpoint assets的加载失败；URI资产还会触发不必要下载。需让普通推理构造transforms时不读取训练norm，使用checkpoint携带的统计。
2. **R2 / P1 / serial：真实TrainConfig不能从保存的YAML恢复。** models/pi0_config.py:92-98 在 __post_init__ 校验 tuple[Mapping] decoder_rules，而tyro/PyYAML此刻还只构造出 ({}, {}, {})；load_train_config直接抛 ValueError: each key_state_decoder_rules entry must be a mapping with a string kind。用真实 pi05_rmbench_rearrange_blocks_serial_lag30 和真实 checkpoint_metadata.save/load 即可复现，无stub、无GPU。full/no-memory相同roundtrip通过。需在嵌套mapping完成构造后验证，且保持唯一resolved schema。
3. **R3 / P1 / aux：合法source: initial无法构造adapter。** training/memory_data.py:195-198 为所有 train input 无条件索引 input_spec["mask"]；core对source: initial的合法resolved项只有source。将实际full配置各字段train/infer改initial、feedback updates清空，TrainConfig成功但create_data_config报KeyError: mask。须先按source区分；修复后还要验证policy遵守infer initial而不消费传入的非initial cache（当前AttachMemory只使用IDs/model_spec，尚未证明该协议约束）。

已通过的独立证据：

- 真实LeRobot→PromptFromLeRobotTask→MemoryLeRobotDataset：两库各选episode0/7，rearrange共805物理query、put-back709，所有sidecar series为M+1但dataset长度仍M。full两臂/serial/no-memory在q=0、30、M-30、M-29、M-1共60个窗口，sidecar前M机器人actions逐值等于Parquet action[:14]；窗口等于原action[q+j]并在末行clamp，无二次移位。rearrange40个窗口进一步经过真实已有14维norm与完整training transforms，state/actions有限、输出(50,32)、robot weight全1。put-back20个窗口通过adapter数值检查，但其专用norm资产当前不存在，未将该路标为实际归一化通过。
- 对真实episode缓存只在本进程将phase availability置false，实际dataset.__getitem__仍返回完整机器人sample/50x14动作，robot weights=1且仅phase weights/mask归零。serial真实输入为q-30（q<30用initial），target为当前q；额外低维adapter检查full q0初始、其余读取当前truth并忽略故意放入的旧key_state_input_ids列。未重跑数据reviewer全100集原始GT审查。
- 本轮新增实际serial sampler检查通过：使用真实Pi0.embed_prefix、value/query embeddings、logit head、selector、sample_actions_with_key_state和JAX while_loop，仅用可观测小trunk替换Gemma/SigLIP。相同输入previous=[3,1,0]选[0,2,2]；选中IDs及显式override=[1,1,1]分别进入segment1 current tokens并改变动作。实际Policy.infer经真实输入/输出transforms返回robot actions(50,14)、memory_prediction_ids(1,3)，与真正动作条件一致。真实compute_loss训练分支追加reference ID的同一embedding，query head不能看teacher target、action suffix可看全部current tokens。此为CPU算法/接口检查，不替代实际base GPU JIT。
- 单字段serial另独立执行相同真实sampler/Policy路径：previous=[3]回退选[0]，segment1 tokens一致，actions(50,14)、wire(1,1)。无旧单字段单调递增规则。
- 本轮新增实际scripts/train.py::main计数检查：分别执行50和20000次受控update，只有最终一次save_state调用，其state.step和目录step严格为50/20000，save_full_state=False，最后wait_until_finished。使用真实main、受控CPU update/save替身，不创建Orbax checkpoint；真实train_step静态核对每次optax.update后step+1，原作者实际train_test的2/4保存证据沿用。正式配置num_train_steps=save_interval=20000、batch32、BF16/model-only。

- checkpoint metadata 3d4fe31→cc706e37：新增3测试通过；未重复tiny cast。独立metadata_review_probe.py使用真实rearrange/put-back目录：dataset meta各8文件（304571 / 277972字节），sidecar metadata各17文件（741466 / 890008字节），SHA256逐文件完全一致；root episode_memory/视频/Parquet/源码未复制。真实command argv/env/cwd可还原。全新进程禁止训练来源后metadata加载通过（不等同于policy全链路通过）。
- 实际full transforms使用真实SentencePiece/PaligemmaTokenizer、同robot/images/prompt、memory [0,0,0]与[2,1,2]：token条件不同；memory one-hot维持identity、机器人部分相同，真实data_loader.transform_dataset与推理token一致。原始50x32输出解码后actions为50x14，memory_prediction_ids为50x3且保留第30行。
- 真实Pi0.compute_loss（只控制velocity/trunk输出，保留原preprocess/loss/autodiff）独立B=2/H=50/D=32测试：lambda=.25、valid_mean非单位系数、M-30与M-29末尾、P2两臂公共mask与robot targets一致；解析梯度=2w/(BHD)，phase全invalid不清机器人loss，padding梯度严格0。
- 实际Pi0默认serial decoder：previous=[3,1,0]可选[0,2,2]，与公共spec decoder独立argmax一致，无旧phase递增/button约束。
- 作者新增pipeline/model/config/policy测试以 -m 'not manual' 执行：14 passed, 2 deselected。覆盖被作者 -k 'not infer and not broker' 漏掉的 test_policy_uses_inference_data_config_and_runtime_memory_metadata；其余作者总数仅作输入证据。
- 前轮本任务独立combined_review_test.py：5 passed, 3 failed；三个失败即R1/R2/R3，不是测试环境失败。按Manager要求本轮未重复已通过tokenizer/P2梯度或旧tiny cast。
- 本轮remaining_review_test.py的8项按增量选择执行：7项通过、1项复现R4（不是一次整套pytest的总数）。具体为真实数据两路各1、serial多字段1/单字段1、真实main计数2、full当前truth1通过；显式conditional consumer对照1失败。构建review harness时修正过FPS读取、公共decoder输入rank以及实际prompt wrapper，不把这些测试构建问题算作实现发现。

workspace、各库交付 commit：

- openpi: /mnt/public/xcj/Projects/workspace/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/openpi；复用原独立.venv。
- review HEAD: 63be08cace87282eb560496b760455c07be8dbb4（与ffa308d5485a2c8222d3e7735b08723c6e93a237文件树一致）。
- 未修改openpi实现、未派agent、所有测试显式CUDA_VISIBLE_DEVICES='' / JAX_PLATFORMS=cpu。
- 用户收窄跨库分工的通知前，上一轮已登记robot-bridge f84edbd6eea81104a00fd85409046eaaa8712e9b工作树；本轮不使用、不测试它，交Manager归档时处理。

验证结果与成果位置：

- 独立复现脚本在本report同目录：metadata_review_probe.py、combined_review_test.py、remaining_review_test.py。
- 复跑（从上述openpi根）：
  env CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 OPENPI_DATA_HOME=/mnt/public/cache/openpi HF_HUB_OFFLINE=1 HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot .venv/bin/python -B -m pytest -q -p no:cacheprovider /mnt/public/xcj/Projects/multi-agent-manager/.tasks/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/combined_review_test.py
- remaining_review_test.py使用同一CPU环境命令，将末尾文件名替换即可；真实LeRobot检查另设HF_DATASETS_CACHE=/tmp/review-9b73-remaining-20260910/datasets。单项可用-k选择，不需要重复已过项。
- 本任务四个/tmp/review-9b73-{metadata-tests,combined-tests,independent,remaining}-20260910目录已清理；无本任务运行中的测试进程。业务库git status为空，git diff --check通过，保留原worktree/.venv与MAM复现脚本供增量验收。
- 截止本轮读取，training report仍为56649e2，Pascal report为ebd21bb、Einstein为bb4a200，后两者尚未宣称完成真实新wire跨库联通。live问题另属其范围，不纳入firstfull阻塞；后续只需追加该CPU边界证据，不创建第三bridge环境。
