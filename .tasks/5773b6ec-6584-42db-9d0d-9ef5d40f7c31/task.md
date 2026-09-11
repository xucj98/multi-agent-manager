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
