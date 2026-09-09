task_revision: cfb25bc263702ff75a981adec3f68260257c6252

# d10cc01 组合审查：rearrange firstfull CPU GO，R1/R2关闭

完成与未完成：

- 原worktree已合入5e3bfd6d46f13643c53271c1e3e1bc116dd4ff06及d10cc01d44c10e5ed0cd8c228d9409dd6cabac50；真实review HEAD为c3be18c613af048a488fe83d43dd6b132c2f0f00，git diff d10cc01 HEAD为空。R1/R2增量独立复核通过，均关闭。未修改交付实现、未重建环境、未使用GPU。
- **rearrange firstfull（t+1/t+30、默认argmax）CPU GO。** 既有真实条件/loss/数据窗口/计数证据继续有效，新的CLI与自包含factory/YAML阻塞已消除。Pascal发布的7项真实MemoryContext跨库联通已纳入证据。因此CPU侧无剩余firstfull blocker；正式20k仍待owner的full GPU50更新/真实BF16保存恢复证据与Manager开跑通知，不把CPU GO扩大成GPU GO。
- serial默认argmax与no-memory的R1/R2共用恢复边界也通过。serial仍需其独立GPU50路径；no-memory不额外50step。put-back使用自身14维norm，实际norm loader证据另待交付，不因此阻塞rearrange firstfull。aux R3、显式conditional R4以及wash/live单列，均不捆绑firstfull。
- 保存与恢复可使用不同固定commit：如修复只涉及factory/YAML恢复，不要求重复已完成50次update，分别记录训练保存commit、恢复commit、原checkpoint与实际keys/shapes。full通过可单独放行；serial、aux、wash和live的未完成项不捆绑阻塞firstfull。no-memory不另加50step。

发现状态：

4. **R4 / P2 / 仅显式conditional decoder：Pi0与公共schema的case优先级相反。** models/pi0.py:297-310逐case用jnp.where覆盖allowed，所以最后一个匹配分支获胜；公共memory_config.py:866-870命中首个立即返回。实际serial配置加入合法重叠case（previous.phase=unknown允许left；后续selected.phase=unknown允许right）后，相同logits/previous在公共spec得[0,1,0]，Pi0得[0,2,0]。会让serial动作条件与保存schema定义不同；当前默认argmax的full/serial均不走此分支，不阻塞firstfull。remaining_review_test.py::test_explicit_conditional_decoder_agrees_with_public_spec可独立复现；仅复核consumer一致性，未重审parser。

1. **R1 / 已关闭于d10cc01。** training/config.py:206-214增加create_for_inference并显式load_norm_stats=False，create_base_config:230据此不读源统计；TrainConfig:1107使用该入口。所有现有factory透传同一开关，训练入口默认仍加载统计。原独立fresh-process拒读测试通过；未增加第二份schema或norm来源。
2. **R2 / 已关闭于d10cc01。** models/pi0_config.py:92-113将nested decoder mapping验证移到完整构造后的validate_key_state_decoder_rules，model.create:123与TrainConfig.create_data_config:1103在使用前调用。真实serial tagged YAML保存/恢复与model_spec相等；空rule仍在两个使用入口抛ValueError，不是删除校验。full/no-memory真实metadata roundtrip同时通过。
3. **R3 / P1 / aux：合法source: initial无法构造adapter。** training/memory_data.py:195-198 为所有 train input 无条件索引 input_spec["mask"]；core对source: initial的合法resolved项只有source。将实际full配置各字段train/infer改initial、feedback updates清空，TrainConfig成功但create_data_config报KeyError: mask。须先按source区分；修复后还要验证policy遵守infer initial而不消费传入的非initial cache（当前AttachMemory只使用IDs/model_spec，尚未证明该协议约束）。

已通过的独立证据：

- **d10本轮增量（所有Python显式CPU）：** 原独立combined_review_test.py仅选择real_train_config_metadata_roundtrip / fresh_process_inference_factory_never_reads_training_norm，**4 passed, 4 deselected**（27.35s）。未重复其tokenizer/P2/loss部分。作者config_memory_test/config_test/memory_data_test中仅选择CLI和新factory/YAML用例，**4 passed, 12 deselected**（71.23s），含实际scripts/train.py --help。
- 新独立d10_review_test.py：真实config.cli在新进程解析`scripts/train.py pi05_rmbench_rearrange_blocks_full_t_plus_1 --exp-name=review-cli-no-training --num-train-steps=50 --save-interval=50 --batch-size=32 --no-wandb-enabled`，断言实际选中模板、resolved schema/bindings、save_dtype=bfloat16/save_full_state=False。没有进入train.main。另以坏的({}, {}, {})规则证明Pi0Config.create及恢复后的TrainConfig.create_data_config都会在使用前拒绝。
- 新fresh-process policy factory检查覆盖full/serial/no-memory共**3 passed, 2 deselected**（62.26s），从/tmp启动，audit hook在首次OpenPI import前安装，禁止open/listdir/scandir访问训练norm、dataset、sidecar与examples原YAML；源norm特意写坏。实际create_trained_policy_from_checkpoint→tagged配置反序列化→create_data_config(False)→checkpoint/assets统计→Policy.infer通过，真实Normalize/Unnormalize对象内统计精确等于checkpoint保存值，输出actions(50,14)、full IDs(50,3)/serial IDs(1,3)。本测试仅替换昂贵的restore_params、Pi0Config.load以及module_jit，用轻量模型输出隔离此次改动边界；未声称实际3.35B参数IO/JIT或最终BF16产物已恢复。首次harness将ALOHA输出误假定全0，修正为检查实际统计及既有机器人/夹爪转换后通过；不是实现发现。该文件按增量分次执行总计5项通过，未重复CLI/坏rule已过项。
- Pascal最新发布报告**05ba1a0a312c665e5d00b61aba7f9ebff3f61135**纳入组合证据：其OpenPI f3f6459文件树等价ffa308d，bridge87fbc9c；7项真实SimulationScheduler/MemoryContext/Policy/transforms/tokenizer跨库CPU检查通过。覆盖full/serial单多字段、no-memory、K30 index29、request previous与实际serial condition一致。d10及CLI增量未修改这些wire/model/data实现；沿用该证据，不复制第三bridge环境。完整权重/JIT和live进度不在该7项结论内。

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
- ffa308d历史本任务独立combined_review_test.py：5 passed, 3 failed；当时三个失败为R1/R2/R3，其中R1/R2已由上述d10增量关闭，R3仍单列。按Manager要求本轮未重复已通过tokenizer/P2梯度或旧tiny cast。
- 本轮remaining_review_test.py的8项按增量选择执行：7项通过、1项复现R4（不是一次整套pytest的总数）。具体为真实数据两路各1、serial多字段1/单字段1、真实main计数2、full当前truth1通过；显式conditional consumer对照1失败。构建review harness时修正过FPS读取、公共decoder输入rank以及实际prompt wrapper，不把这些测试构建问题算作实现发现。

workspace、各库交付 commit：

- openpi: /mnt/public/xcj/Projects/workspace/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/openpi；复用原独立.venv。
- 当前review HEAD: c3be18c613af048a488fe83d43dd6b132c2f0f00（与d10cc01d44c10e5ed0cd8c228d9409dd6cabac50文件树一致）。历史数值审查HEAD为63be08cace87282eb560496b760455c07be8dbb4，文件树等价ffa308d。
- 未修改openpi实现、未派agent、所有测试显式CUDA_VISIBLE_DEVICES='' / JAX_PLATFORMS=cpu。
- 用户收窄跨库分工的通知前，上一轮已登记robot-bridge f84edbd6eea81104a00fd85409046eaaa8712e9b工作树；本轮不使用、不测试它，交Manager归档时处理。

验证结果与成果位置：

- 独立复现脚本在本report同目录：metadata_review_probe.py、combined_review_test.py、remaining_review_test.py、d10_review_test.py。
- 复跑（从上述openpi根）：
  env CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu PYTHONDONTWRITEBYTECODE=1 OPENPI_DATA_HOME=/mnt/public/cache/openpi HF_HUB_OFFLINE=1 HF_LEROBOT_HOME=/mnt/public/xcj/cache/huggingface/lerobot .venv/bin/python -B -m pytest -q -p no:cacheprovider /mnt/public/xcj/Projects/multi-agent-manager/.tasks/9b73b590-f7bf-4f46-b2e4-4fa5882d9db3/combined_review_test.py
- remaining_review_test.py使用同一CPU环境命令，将末尾文件名替换即可；真实LeRobot检查另设HF_DATASETS_CACHE=/tmp/review-9b73-remaining-20260910/datasets。单项可用-k选择，不需要重复已过项。
- 本任务四个/tmp/review-9b73-{metadata-tests,combined-tests,independent,remaining}-20260910目录已清理；无本任务运行中的测试进程。业务库git status为空，git diff --check通过，保留原worktree/.venv与MAM复现脚本供增量验收。
- d10本轮四个/tmp/review-9b73-d10-{existing,author,new,policy}-20260910也已清理。原worktree/.venv继续复用，git diff d10cc01 HEAD为空。
- 最新training report为09f1d34e2f426fec448299a60534b0bb41988d2d，交付d10cc01并列明GPU50尚待执行。Pascal跨库7项证据已由05ba1a0a关闭CPU wire项。GPU阶段后续只审实际命令/固定保存与加载commit、最终50目录/完整参数树shape与dtype、恢复keys/shapes，不要求因纯恢复修复重跑已有50update。put-back实际norm loader证据仍待提供。
