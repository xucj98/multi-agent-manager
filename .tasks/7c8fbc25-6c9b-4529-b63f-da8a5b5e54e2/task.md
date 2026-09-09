# Memory v1：数据适配与wash-cup转换
# 目标

# 用户最新数据约束

用户明确指定RMBench训练/转换只用demo_clean_state；demo_clean没有metadata及详细子任务划分，不允许用作fallback。wash-cup原始数据不受此命名约束。已转换仿真数据须沿metadata确认来自demo_clean_state，并核实所需真值/事件完整；来源不明先不训练，不从评测rollout重建标注。

资产owner已定位旧converted源：/mnt/public3/xcj/cache/huggingface/lerobot/{rearrange_blocks,put_back_block}_demo_clean_state_shared_memory，分别50ep/20103frames、50ep/17588frames，正恢复到本集群/mnt/public/xcj/cache/huggingface/lerobot/同名目录。包含action、observation.state、key_state_input/target/mask、index/timestamp；rearrange还有key_state_guard_offset，meta/rmbench保留转换与source/key-state metadata。尚需你检查是否足够绑定series/constants/events和P2当前真值（不能将lagged input误作当前truth），若原始详细边界缺失则精确列出所需raw文件让Manager安排恢复。不要依靠目录名自行宣布来源已核验，也不要为了框架接口重转全部图像。此事与wash-cup转换可并行。

# 已确定共享接口（API owner的先行契约）

openpi-client模块为 openpi_client.memory_config，load_memory_config(path_or_mapping) -> ResolvedMemoryConfig；to_dict()为metadata.memory_config。训练入口 make_training_sample(EpisodeMemoryData(series, constants, events, tail=None), query_index, rng) 返回input_ids/target_ids/逐行target_mask、robot目标索引/有效位和lag_draws；字段顺序为memory列表。model_spec()提供representation、词表/initial IDs、dense offsets或token sizes、loss和显式decoder/反馈。validate_model_dimensions(robot_dim, padded_dim)检查已有模型维度。具体可调用属性以owner首个commit为准，先通过该helper复用契约，不复制parser。

input train/infer显式source=initial可作为辅助监督无递推对照；memory=[]为标准无记忆。正常新schema默认独立argmax，历史规则仅显式配置生效。首批H50/K30；P2两full配置仅phase目标时刻不同，共享mask和固定H分母。跨agent的工作树代码需通过明确commit集成，不能把对方临时workspace长期加入PYTHONPATH。需要伴随openpi代码时在自己MAM任务下增加openpi worktree并接owner提交，或用自身venv安装该commit构建的轻量包，勿改共享环境。


在独立openpi中准备统一schema的数据适配与首批wash-cup转换，支持同一memory字段定义供full/serial训练使用。后续RMBench新训练复用现有真实标注，不新增另一套任务语义。可实施转换，暂不启动正式模型训练。

# 工作区与分工

用mam workspace add --repo openpi --base 71c80db723a242c61cfe429dd6794e9ece3cbcf1创建环境/worktree；读openpi AGENTS.md。写入范围openpi/examples的数据转换器、新数据适配模块/配置和对应定向测试。不要改src/openpi或packages/openpi-client（任务 f252006a-8676-4d10-b6a1-1a791d91c6a6 owner负责）。若需RMBench薄转换入口，用其worktree e31d14fe0818235d471b371924ea30c273e75c7a且先报Manager；不改legacy policy/pi05的算法/转换实现。不要写robot-bridge。

# 数据与语义

1. 原始wash-cup /mnt/public/datasets/x1pro/wash-cup，annotation_layers.json给子任务标注位置。扫描并给确定筛选清单：任何label6、缺标注文件、labels1..5不是各恰好一次都剔除；次序允许变化。其余全部训练，不划分holdout；固定5个合格训练episode做offline并记录IDs。phase是当前子任务，不是已完成到哪步。沿用drawer S2M输入/动作定义、真实时间戳/频率与相机映射，不猜SM2SM。
2. 首轮只一个phase，full与serial使用同一有序domain/标注；顺序可变，不能默认按1到5推进。初始值如何在未知顺序下合法：若第一label并不恒为1，报告事实并设置显式unknown或由可观测的初始化定义，不能在推理偷用训练episode首标签。不要把domain ID和原始label ID混用。
3. 抽取现有drawer/rearrange多字段转换中可复用的sample/time绑定，明确normalized series/constants/events映射。原始数据转换只保存真实标签和可用性，不把每次实验的phase目标策略写死进数据导致重复转换。P2在训练sample阶段从同份标签生成目标/mask，保留t+1 vs t+30和采样边界。
4. 配置唯一解析器由f252任务提供，checkpoint metadata键memory_config；先整理标注适配/读写入口，接口到达再接，不抄第二套schema。无需扫描所有历史实验或另造统一data framework。新数据结果放共享主openpi的gitignored data目录，按明确dataset/run命名，不指向你临时workspace。
5. raw数据只读。转换数据保存命令+commit+resolved配置+源标注路径及筛选统计/IDs等既有metadata链。先小规模转换验证schema/标签/视频同步，再提交代码再正式全量转换；预计超过1小时进程登记mam job。清理成功正式转换替代的临时smoke，不让结果根混乱。

# 验收与交付

报告有效/过滤数和原因、phase次序统计、数据/5ep输出位置、必要空间估算。测试label6/缺标注/重复/缺类/任意顺序、标签边界、S2M shape/时间对齐；读回生成数据验证。代码量先预估，复用优先；新文件名/接口尽早发Manager。未获分配不占GPU，CPU解码可用；不运行模型训练或真机。最终report含task_revision/workspace/commit与验证，发布等待归档，不自行派agent。
