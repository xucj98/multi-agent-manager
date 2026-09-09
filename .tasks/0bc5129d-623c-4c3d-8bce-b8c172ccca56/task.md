## Eval入口补充

Eval准备commit RMBench9e8fccbd2fa004f18a3cbcc301e7387b02edaccf发现terminal trace next_query=false仍额外policy infer。Manager已要求作者在simulation scheduler局部跳过terminal infer并单独提交，保留base/live循环；请复核此增量与F0实际调用/trace一致。另正式recorder原完整配置smoke检查保留，四种row各自先2rollout smoke，不写新的白名单兼容机制。

## 已提交的完整runtime增量

作者已交付robot-bridge fd38513adb5ba171327358f70f55f88059de49d2（含22a5c6c/bb908c6前置），请在本任务独立分支合入并完成上述全范围review；openpi helper使用主库58d6f2155acc3af03017677bb3f536101e6699f4的等价API。作者报告445 passed/1skipped不是独立验收结论。F0是旧full固定权重评测的直接阻塞：先给selector/legacy/progress部分是否阻塞的明确结论，剩余新schema路径继续检查。报告实现与测试的代码规模，以及必要性/重复逻辑方面的实质问题，不为凑行数删必要验证。

# Memory runtime独立review：执行进度、反馈时刻与takeover

## 范围与工作区

独立审查runtime任务9f5a3889-49a6-4f00-af84-096d8042c3bc的已发布要求与交付代码。先创建本task robot-bridge worktree at22a5c6cc54f46daf0e025fa3f7fdbd1f07a2f6a8，并读AGENTS与docs/design/conventions.md；需要新client API时创建本task openpi at58d6f2155acc3af03017677bb3f536101e6699f4，使用独立editable，不能引用作者临时树。起始commit含bb908c6执行进度及22a5c6c metadata透传，可先审这两项。作者正在补scheduler/MemoryContext/UI集成，Manager随后给增量commit；不要空等，不改交付实现，不占GPU，不派agent。

## 核查要点

- 保留SchedulerBase原execute→带wait_condition的get_obs循环及真机WS action chunk/UDP takeover机制；没有get_progress RPC或session概念。模型可以原有内部cache/reset，scheduler负责显式memory context，单scheduler一robot一policy。
- execute接受chunk与实际处理多少policy动作行明确区分；新controller计数与相应chunk/观察对应，部分执行、取消、episode中止、接管、异常和reset均不会消费旧proposal。动作行计数不冒充物理到位检测，不把渲染帧/仿真积分substep当policy row。看锁/线程/队列路径，独立构造最小复现，不能只相信作者mock。
- 新memory单/多字段共用：语义初值、当前selected与prior snapshot、query_selected/chunk_completed反馈、row.first/index/last_executed、actual k与一基/零基索引一致。full逐行预测不是强制每行相同；首批P2在K30完成后读row30。缺GT属于训练数据，不应让普通runtime读GT或训练dataset；one-hot identity新输出与legacy归一化各按真实路径解码。
- F0旧full30k固定H50/K30，需要rows1/20/30/50（index0/19/29/49）诊断，所有memory字段同一选行规则；原模型/词表/归一化/解码路径保持可比。新selector/trace不能顺手更改旧模型条件；老checkpoint未含memory_config仍可走原已验证路径。每query trace记录请求/实际执行k、消费行、before/after语义；episode已结束不伪造下一query。
- 真机/offline/sim/takeover共享context处理；UI从相同字段定义显示，无phase/attribute字段数量硬编码。reset/接管清pending，异常收尾不泄漏子进程/端口/视频。仿真结果归RMBench recorder，代码不新建robot-bridge/eval_result。
- 审实现冗余与概念边界，避免同一逻辑在三scheduler复制三份或新建通用plugin bus；也不要为精简破坏已经验证的真机循环。

## 验证与交付

CPU测试适用于controller进度、并发/中断、MemoryContext时序、legacy分支和UI字段传递。GPU的2rollout video/no-video及正式100由独立eval任务执行，你不启动。起始阶段只报告已审查commit的范围；新scheduler增量到后再给完整结论。报告须有task_revision、审查HEAD/工作区、独立验证及发现的具体输入/路径/后果，区分阻塞首批与扩展事项；记录未能验证的真机硬件部分，不能用mock成功冒称真机通过。发布report后清理自己的临时脚本/cache，保留工作树待Manager归档。
