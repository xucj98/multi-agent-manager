# 本集群 state-vla 资源位置与 worktree 创建审计

## 目标与只读边界
用户要求与集群C并行另一个独立审计。本任务审计当前训练服务器、wuwen-1及wuwen-nx-aic（仅有相关引用时）的state-vla资源位置，识别不合理布局。只读，不修复、不删除、不安装、不重建worktree/venv、不跑GPU、不停止或修改活跃训练/评估。不要输出密钥、认证令牌或完整私密环境。
读MAM AGENTS/README/.local说明。项目共享根/mnt/public/xcj/Projects；/root/Projects是本机访问别名，必须分别确认真实路径，wuwen-1各自/root和/home非共享。C资源由另一执行者71e53073审计，你不重复查C。

## 范围与资源表
核心三库RMBench、robot-bridge、openpi；mem-0、opendm、MAM及其他state-vla组件的相关资源也纳入资源总览（存在则实查，不猜路径）。以真实repo/.local/create_worktree.sh、所调用脚本、当前worktree/运行入口/软链接/解释器为线索，追踪所有项目相关外部资源。不是对整个/mnt/public或用户主目录无目的遍历。
清单覆盖：
- 主checkout、git common dir、已登记与遗留workspace/worktree/branch，/root/Projects及shared Projects映射、.local各入口/固定路径；
- raw/converted数据、RMBench data/assets/meshes和模拟器资源、wash/drawer数据与metadata/norm；
- checkpoints/base/训练模型、mem-0模型资源、eval_result/experiments、训练log、临时输出和重复目录（包括是否还存在user_checkpoints等，不以存在即判垃圾）；
- 各venv与最终python目标、shared-python、uv cache/可执行、hardlink/symlink模式、pip缓存、cuRobo/PyTorch3D wheel、offline lock/patch/shim；
- HuggingFace/torch/JAX/XLA/Warp/renderer运行缓存、相关传输/暂存目录；
- MAM_ROOT/.tasks/.local登记及PROJECT_ROOT/workspace的归属关系，只记录任务ID/路径，不泄露无关对话或敏感信息；
- 本机能运行但wuwen-1可能找不到的/root或/home依赖、shared-python真实链接、运行和安装入口要求。
每项表列用途、逻辑路径、realpath、共享/主机私有、创建与使用入口、确认状态/证据。容量不跟随软链接重复计数；hardlink占用说明去重口径。复用已有测量，局部必要du即可，不全量扫描巨型cache/data。

## 独立章节：worktree创建审计
三个核心库各写独立小节；如果opendm/mem-0另有创建入口，再单列补充。
逐库从本集群真实.local/create_worktree.sh到受版本控制脚本，写参数合同（base/branch/workspace）、执行步骤、固定cache/python/wheel路径、环境创建/共享方式、实际创建/复制/软链接清单（link→目标、类型、目标可达性）、数据/资产/ckpt/eval_result映射、.local与运行cache是否私有。抽查现有活跃worktree的实际链接和源码声明一致性，不只总结脚本意图。说明清理workspace影响哪些资源、哪些共享目标保留。区分历史测量和当前未实测，不为补耗时重跑创建。

## 判断与交付
确认问题、维护成本、待核实项分开。重点查：悬空/跨节点私有依赖、旧已删task/临时目录依赖、结果保存错库或目录层级混乱、重复大模型/资产、共享可写cache冲突、未登记的遗留workspace、入口/README与实际不一致。集群固定绝对路径本身不是问题，不提出可迁移性大改造或新provenance系统。每个问题给实际路径/触发条件/影响与最小建议，不凭目录名推断可删除。
完整报告写本任务MAM .tasks/<TASK-ID>/report.md，章节为资源总览、worktree创建审计（逐库）、发现与建议、未覆盖/未确认。精简证据放.tasks下或本task workspace，最终有价值证据留.tasks；清理自有临时查询文件，无代码修改无需建业务库worktree。报告mam task publish后结束turn，交Manager裁定，不自动实施任何建议。
