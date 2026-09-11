# 重规划 Table-1000 项目 roadmap 与近期并行任务文档
# 目标
为用户编写整个Table-1000项目的新roadmap和近期可并行task文档；不是实施这些任务。用户倾向从头开始，对旧路线不满意，仅验收过probe-0001一个场景/一条轨迹且仍认为杂乱不足、整理效果差、抓取单一。旧工程代码/测试不得作为科研完成度；保留研究问题，技术路线重新开放，优先试点SimFoundry+OmniGibson原生流程，不要求先适配ManiSkill。
# 操作
读MAM规范和任务，回报CODEX_THREAD_ID供绑定。使用canonical table-1000/scripts/worktree_env/mam_workspace_add.sh TASK-ID f8340d5de7ac5452a6a8d726c1fc11047c0ae6b1 建独立worktree并读AGENTS。只改文档、不安装SimFoundry/下载模型/执行训练。不要重新做全库或全网研究。先尽快给manager章节骨架/关键决策，然后写作。
# 输入（已有证据，无需重复研究）
docs/proposal/research-proposal.md 科学主张；旧docs/roadmap.md仅历史。
MAM已发布报告：.tasks/ea051960-7287-4723-b156-462e3f1e5d17/report.md（现状），.tasks/d05ee593-fc5f-4beb-bf76-b7dca11502ac/report.md（SimFoundry），.tasks/a965dae3-b821-4f61-b579-194fe9906b3a/report.md（真实渲染），.tasks/79b4b3be-4297-40a8-884b-ff6580302897/report.md（附件/真实replay）。这些路径在MAM仓库。
Manager已亲看0001/0006/0007图及用户视频每2秒抽帧与原分辨率末帧：物体大多分离平铺、依赖弱；历史视频末态绿杯倾斜、篮内混堆/线圈伸出；留桌蓝物/小线可能keep不能判错。0006双终态位姿相同，0007餐具长直线排布不说明餐饮功能。当前main tidy-video真replay13技能通过，随后剪刀grasp_failed；不能称用户历史视频成功复现。历史附件hash不同于worklog，不能将7/14强套附件。
SimFoundry官方pinned 9e34ebefcd020583fbb755a8b57268dce78eca26：已发布A重建/B变体/C OG加载辅助；论文完整data generation/policy training未发布；24GiB stage7需low_vram，完整安装约250GB，多conda env、HF gated模型、Gemini可用API key替代GCP。新环境与现有ManiSkill隔离，缓存沿集群共享习惯，不随意清理uv store。首试刚体场景；OmniGibson优先候选未定案，不将换引擎视为抓取已解决。
# 交付文件
1. 将旧docs/roadmap.md完整保留为同目录docs/roadmap-legacy-2026-09-11.md，并明显标记历史记录。
2. 重写docs/roadmap.md，中文新项目总路线，包含问题/贡献与待检验假设、诚实起点、保留/重做取舍、阶段里程碑到论文与公开release、并行依赖、资源与人员假设、主要风险/决策点。指向近期任务及旧历史。不要改写research proposal科研正文；说明当前实施排期以新roadmap为准，旧project-plan/roadmap是参考。
3. docs/planning/near-term-tasks.md，中文近期任务卡，约6–8个有边界任务（小而可交付）分3条核心并行线：场景重建与生成、目标/多人终态与评价、抓取操作与执行。每卡含优先级、输入、输出文件/产物、验收、依赖、探索时间盒、失败时交付/降级、所需能力（不指定人选），标清可立即开始与依赖真实场景的部分。任务ID用计划编号如N01，不伪造已派发MAM任务。
4. 最小更新README链接与开头状态，确保用户能发现新路线，旧ManiSkill进展明确仅历史工程范围；已有开发文档不动。
5. 最小同步docs/README.md文档入口：新roadmap+near-term为当前执行入口；旧project-plan、R/P/A简报、spec/ADR为历史/实现参考，新实现按选型决策采纳；表格增加近期任务和历史roadmap，旧双轨描述改新阶段/三线。不改既有代码合同的当前有效性。
# Manager方向约束
- 先一个端到端高质量样例（初态、多种合理终态、实际可执行轨迹，用户看图/视频验收），再10–20科学pilot，再100/200级论文集，最终1000是通过质量和成本门后的扩展选项。不要把旧验收状态继承到新数据。
- 阶段交付不是只有工程量：验证多解且非任意解、人类评价可判定、open/explicit目标形成差异和planner/executor失败分离；真正模型实验、split冻结/scene-family+cousin隔离、reliability与偏差/泄漏检查、训练数据生产、论文与release均有位置。MVP规模/阈值是建议，不能冒充实验结论。
- 自然杂乱是遮挡/堆叠/功能占用/访问阻塞/先后依赖，而非简单加物体或随机密铺；操作多样由任务需求引出，别为凑技能清单要求所有scene都复杂。首样例控制刚体范围，柔性线缆/关节复杂物延期。
- 多人终态/静态偏好可以在真实桌面照片或现有合格场景上并行启动，不被完整机器人轨迹或SimFoundry安装阻塞。模型诊断也不等VLA训练。人评候选来自独立整理；不向人泄漏唯一整洁原型，生成器task YAML不能作主榜真值。
- 时间是2–3个新硕士、技能/投入未确认下的相对周窗口/时间盒；下周二见面再定人员与日历。不要许诺几周完成论文。资源问题写成待核验事项，非本轮索要权限。
- 建议每周短视频/图+证据验收，manager/用户职责明确，不以测试通过替代研究/视觉质量。
# 验证与交付
读者可从README进入roadmap和任务卡，历史保留；检查相对链接、任务依赖无循环、阶段与task交付一致、git diff --check。纯文档不跑pytest/GPU测试。提交独立commit，publish report记录commit/文件/验证/未决项，cleanup按AGENTS。禁止自行派发agent。报告简短即可。
