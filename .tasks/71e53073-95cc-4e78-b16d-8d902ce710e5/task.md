# 集群C state-vla资源位置及worktree创建审计

## 用户目标
只读审计wuwen-4090-1/2/3上与state-vla相关资源的位置，重点独立成章审计三个库的worktree创建。要回答资源在哪里、谁创建/使用、是否共享、为什么这样放、是否不合理。实查当前状态而非复制旧结论。审计不包含修复、清理、重新安装或GPU评估。

## 范围与依据
读MAM AGENTS/README/.local说明。C共享/mnt/public，项目根/mnt/public/xcj/Projects/state-vla，三库robot-bridge、RMBench、openpi；wuwen-4090-aic是传输入口，优先nx-aic↔4090-aic。三机只读SSH，严禁输出认证密钥/令牌/完整环境秘密。当前有活跃eval，由e690任务负责，其workspace和进程都不能改。
读取C稳定README、各repo AGENTS（存在才读）和真实.local/create_worktree.sh及其调用脚本；脚本和软链接以C实际部署版本为准，标明SHA/内容摘要，不能只审本机模板。对照本机RMBench/experiments/cluster_c_eval_acceptance_20260911/README.md的既有测量和验收，但当前事实与历史测量分列。全程只读，不为审计创建新C环境或重复smoke/100rollout；本MAM task workspace仅存审计证据，无代码修改不强制新repo worktree。

## 完整资源清单
先列项目相关根和所有引用到的外部路径，再沿入口/软链接/解释器引用追踪。包括但不限于：
- 三库主checkout、git common dir、各工作树/分支、实际.local、共享shim路径（如/mnt/public/xcj/Projects/RMBench）及canonical目标；
- datasets/raw/converted、RMBench data/assets/meshes、模拟器资源、eval_result/experiments、训练checkpoint和模型资产/norm/metadata；
- 各venv路径和python可执行文件的最终目标、shared-python位置、uv可执行与共享uv缓存/mode、pip/cache/temp、PyTorch3D/cuRobo预编译wheel及离线lock/shim/patch；
- HuggingFace/torch/JAX/XLA/Warp/renderer caches、运行logs/temporary/result leaf、e690任务独立资源；
- 安装期依赖与运行期依赖分开，确认C2/C3无需uv也可运行的实际依据，检查venv是否意外指向C1专属/root或/home、旧已删task/临时目录、传输节点本地路径。
按资源表列用途、逻辑路径、realpath、共享/节点私有、创建入口/使用者、已确认状态与证据。软链接不重复统计共享目标；容量优先已有记录与局部du，不对整个共享cache/data做全量昂贵扫描，不把逻辑大小当物理占用。

## 独立章节：创建worktree审计（三库分别写）
每库至少说明：调用入口及base/branch/workspace三个参数；脚本执行步骤与固定环境路径；实际新建/复制/链接的完整资源清单；每条软链接源/目标/相对或绝对/是否存在；venv如何创建以及依赖从哪个cache/wheel/python取；是否离线、是否symlink；哪些必须在C1安装，哪些在C2/C3运行时仍依赖；workspace删除影响哪些资源。用当前e690或其他活跃树只读抽查脚本声明与实际对应，不只写脚本意图。现有实测耗时/空间注明测量日期/commit/口径，不能把本次未实跑的创建称为已测。

## 判断与交付
发现项按实际影响排序，区分确认问题、维护成本、尚缺证据；给具体路径和触发条件、最小改进建议。重点检查重复大资源、不可移除的临时worktree依赖、主机私有路径破坏三机运行、软链接悬空、共享可写运行cache冲突、资产/结果归属混乱、安装脚本与README不符。不能因为绝对集群路径本身就判为问题（这个环境就是服务本集群）；不要求额外provenance系统或可移植性大改造。
完整审计正文写MAM .tasks/<TASK-ID>/report.md，包含资源总览、三库独立worktree章节、发现与建议、未确认项/范围边界。原始精简证据放本task workspace或.tasks下合理目录，报告能追到来源；有价值证据最终留.tasks，不留无归属垃圾。通过mam task publish发布report，清理自有临时查询文件后结束turn。向Manager给最重要发现和报告路径。不要自动修复任何问题或调整活跃服务。
