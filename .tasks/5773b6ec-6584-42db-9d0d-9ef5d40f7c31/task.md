# 集群C评估环境准备

## 目标
用户授权现在准备wuwen-4090-1:/mnt/public/xcj/Projects/state-vla，git clone robot-bridge、RMBench、openpi三库，配置每库gitignored .local/create_worktree.sh。暂不扩展MAM。你在本机作为唯一环境负责人；按MAM注册本task、本机独立workspace，需要修改/独立检查的仓库以mam workspace add创建本地worktree，阅读各AGENTS/环境指南。远端目录和所有临时worktree手工登记到task report，避免游离；不在集群C另启动agent或MAM。

## 集群与缓存
- wuwen-4090-1/2/3属于集群C，共享/mnt/public，与本集群同名路径并非同一文件系统。环境只需在-1构建，-2/-3必须能直接运行评估，不要求uv或安装能力。
- 用户明确-1只能用uv symlink，不能hardlink。uv包缓存固定/mnt/public/xcj/cache/uv；Python可参考本集群/mnt/public/xcj/cache/shared-python，在C上使用共享、持久、三机可执行的真实解释器路径，禁止依赖-1私人/root里的解释器或旧site-packages手工PYTHONPATH。
- wheel、cuRobo等其他缓存放C:/mnt/public/xcj/Projects/state-vla/.cache。仓库源/环境/资产软链不能指向将清理的临时workspace。
- 跨集群传输优先SSH本集群wuwen-nx-aic，从wuwen-4090-aic传输（按实际源/目标方向使用rsync）；最多两条并发10MB/s链路且启动间隔至少1分钟。先检查C已有缓存/资源，避免重复大文件传输，报告需要同步的内容/大小。不要拷整个训练数据/全部模型库。必要传输超1小时登记本机mam job。

## 实施范围
1. 只读确认-1/-2/-3 hostname、共享根、Python/驱动/GPU可见性、SSH和缓存真实状态。复用现有可用uv，仅-1需要。不要动其他同学环境/进程。
2. 在上述state-vla根clone三库（origin保持各GitHub，代码固定本任务最新指定commit；robot-bridge codex/unified-sim-real-runtime最新已推f0f585a2b5974c60b51cac65277f94d1097591a3，OpenPI a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4；RMBench用本机当前xcj-dev HEAD并记录）。GitHub缺commit时通过已授权本机代码bundle补足，避免假称origin已有。不要覆盖已存在未知目录，先检查来源。
3. 三库分别维护自己的.local/create_worktree.sh，接口沿本机base commit/new branch/workspace dir，机器路径写在.local，脚本无需进git。不新增environment.yaml或provenance体系。代码受版本管理的创建脚本若硬编码hardlink/校验仅接受hardlink，做必要小改支持symlink模式及验证其语义，不全局改变本机现有hardlink行为；此类改动在本机独立worktree提交供Manager验收，不修改活跃实验源树。
4. 软链按各库需求创建：RMBench data/assets/eval_result、policy checkpoint等；OpenPI data/assets/checkpoints及实际规范需要的项；bridge按其规范。共享根必须是C稳定目录，eval产物未来仍RMBench/eval_result/<exp-group>/<run>。避免重新引入robot-bridge/eval_result或openpi/user_checkpoints。
5. 用这些入口实际创建新环境验证，在-1安装、-2/-3直接运行同一环境：Python/核心依赖导入、torch/CUDA、渲染/仿真与cuRobo运行必要短smoke；先读GPU空闲情况，只用空闲资源，短验证不启动正式训练/100rollout，不停止他人进程。确保symlink site-packages解析到C共享cache且缓存未来不得随意清理，二进制与共享Python在三机有效。不能只用--help/import宣称完整eval通过；分别注明环境检查与真实sim/policy短测试覆盖及缺失数据/模型等实际阻塞。
6. robot-bridge最新memory_config已本库自带，不为scheduler安装openpi-client wheel。OpenPI保留自身客户端正常模型依赖，不互相新增包依赖。

## 交付
尽快先报告三机连通性、现有缓存复用与关键风险，然后实施并给三库精确clone路径/commit、.local入口、实际worktree/venv/软链目标及三机验证结果。必要本地代码改动提交commit；有用环境信息写远端state-vla/.local/README.md或各库.local README并在report链接，别散落重复长说明。报告列已完成和待完成，不把安装成功当评估通过。清理自己的smoke/临时下载/测试树，保留稳定缓存及待验收环境；远端临时workspace需要逐项登记和清理。发布MAM报告供Manager独立验收，不自行推送/合并业务代码，不改变正在运行的本机实验，默认不进行正式评估。

## 用户追加正式验收（覆盖此前不跑正式评估）
必须交付以下验收：
1. 三库.local/create_worktree.sh分别实际测量创建耗时与磁盘占用。记录命令/start/end/exit、环境建前后du/文件系统差异，分别报告新worktree和.venv自身实际占用、共享缓存新增占用；symlink不能通过du -L重复统计成独占，也不能仅看链接大小声称整个环境零占用。区分首次缺包缓存构建与缓存已命中，不用假设代替实测；包括源码/venv/稳定缓存的空间解释。
2. wuwen-4090-1/-2/-3都必须实际跑eval，不能只import/--help。每台先用同一模型/同一配置跑一个含2rollout的smoke（一有video、一无video），检查正常退出、视频和完整产物；使用各机空闲GPU，一run在一卡串行，不要求-2/-3可安装或有uv。
3. 一个模型在C完整跑100 rollout，需与本机完整100 rollout基线成功率差<=5个百分点（100次下<=5次成功差）。复用已完成本机模型/训练seed/ckpt哈希，固定任务/数据/环境seed序列/H/K/memory协议、仿真器和policy代码commit。优先与本机eval负责人e6908de7确认一个完整已收尾的对照结果、具体冻结三库commit/命令。环境搭建可以最新代码；正式对照需相同代码状态，若需要旧commit环境确保依赖仍可正常安装而不是路径猜测。对照选定和额外传输/代码差异先报告Manager裁定，不能默默变配置。若没有可直接使用的严格同版本基线，提出最小本机补跑计划，不拿不同版本直接归因GPU硬件。
4. 正式100在三机smoke通过、代码干净/提交及产物门禁通过后启动，本机mam job add登记C进程，说明host/GPU/用途；只同步所需一个ckpt和eval资源。C输出RMBench/eval_result/<exp-group>/<run>，本机最终同结构回传并校验。50rollout时先检查趋势与协议，不提前以50样本验收；完整100若差>5pp，保留原结果并分析，不靠重跑挑结果通过。
5. 报告表列三脚本耗时/独占与缓存磁盘、三机smoke、C100和本机100成功计数/差值、固定版本/模型/数据和结果路径。实验说明最终RMBench/experiments/<exp-group>，必要Git代码改动仍本机独立worktree提交复核；不要扩MAM功能。

## 用户确认后续C集群eval与手工workspace管理
用户要求Manager继续推进，C验收通过后后续新eval迁至C，当前已启动本机eval不搬迁。暂不扩MAM；负责eval的subagent在C:/mnt/public/xcj/Projects/state-vla/workspace/TASK-ID手动创建workspace及各库worktree，使用本task提供的.local/create_worktree.sh。本机MAM task/agent仍一一绑定，远端worktree登记到其report，不在C启动agent或另装MAM。
请在本task稳定state-vla根交付README.md，供后续eval执行者开工前阅读；内容只写可执行的当前环境操作手册：三台机器/共享路径、-1安装与-2/-3运行、uv symlink共享缓存不可随意删除、创建workspace/TASK-ID和所需worktree的准确命令、各库.local脚本3参数接口、GPU检查/占用登记、smoke2一有video一无video→commit→单GPU串行100/50检查、输出RMBench/eval_result/<exp-group>/<run>及本机回传与实验说明、完成后由执行者清理smoke/临时文件和自己的remote worktree/branch/workspace、保留共享模型/数据/缓存。只删除任务自己创建的分支，不删仓库工作分支或他人目录；清理不跟随共享软链。
README不写MAM新接口、复杂后端或猜测尚未验证的命令。先随环境实现起草，三机/100eval验收完成后更新为实测可用版本。路径稳定、简洁清楚，Manager验收后将其路径写进每个后续eval任务要求，作为必读。源文档副本可随本task报告留在本机MAM，避免只有临时目录有价值说明。
