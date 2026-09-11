# 目标
核查SimFoundry官方开源状态及作为table-1000场景生成工具的实际适配成本，为研究分工提供依据，不安装或下载大模型。
# 输入与操作
官方入口 https://research.nvidia.com/labs/gear/simfoundry/ 。从官方GitHub、论文、INSTALL/管线文档查证，只用一手来源，保留URL与当前commit（能查则查）。已初查项目确实有代码：A重建/B cousin增强/C OmniGibson应用；README标记训练/数据生成未发布；24GB显卡mesh stage默认约29GB需low_vram。请独立确认，不把网页demo等同开源功能。
读MAM规范、回报CODEX_THREAD_ID。可只读canonical proposal和scene/asset schema了解目标（不改repo无需完整worktree）；web研究产物放本TASK workspace/report即可。关注：输入视频/图像、输出mesh/collision/pose/scale/metadata/USD/OG，ManiSkill可移植层与缺口；24GB4090、系统/多环境/模型下载/API key及依赖许可中对实际研究有影响的限制；可复现example作为第一里程碑。SimFoundry的task generation是否是显式单目标，不能替代Table1000多解语义和偏好评价。
# 交付
简明报告：确实已开源与未发布项，环境开销实际官方数字，推荐最小接入路径/不应先做什么，给场景同学2周pilot和量化go/no-go门槛（将建议与事实区分）。引用直达官方文档，避免营销指标泛化。不做安装、不下载模型、不改现有venv、不派发agent。发布MAM report。
