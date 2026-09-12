# 九任务覆盖与seed差异证据审计
用户要求重排论文核心主张/实验，优先完整RMBench九任务覆盖，不接受默认所有配置3训练seed。新增预算12卡A100×7天=2016 GPUh，20h/训练理论约100次；要有验证/故障预留，不能无依据全用满。现在已暂停新开跑，现有job仅自然收尾。

先读MAM AGENTS/README/.local/README，回CODEX_THREAD_ID。只读审计，结果存本task workspace并发布report；不改代码/台账、不新训练或评测，不创建无必要worktree。
1. 核验RMBench官方论文/仓库及本地实际任务注册，明确用户所指9任务的准确名字、难点/记忆信息类型。核对当前数据demo_clean_state及标注/转换/schema/历史模型/新20k资产可复用情况。不要仅查有目录就判就绪；给逐任务ready/缺项及证据路径。可读 /root/Documents/task-state-vla-paper 与 /mnt/public/xcj/Projects/RMBench/openpi（openpi实际同级Projects/openpi）。优先现有history_audit、任务e248b5a1材料；只能官方文献primary source，需上网核实确切9任务。
2. 现有新模型同一任务/config的训练seed0/1/2差异：必须固定同eval seed比较，输出成功数/100、范围、均值、样本标准差，最好由paired episode结果算差异不确定性（必要且容易时）；明示100rollout观测噪声、训练随机性和评估初始条件不可混淆。当前Q2四组分别87/99/96，90/92/93，69/47/67，70/63/74；独立核验原始结果。no-memory三trainseed的eval0为23/24/37可核对；不能拿train1/2的300均值和train0的100比较。结果还不能证明差异小或等价。
3. 给覆盖九任务的单seed训练matrix候选，区分已有20k可直接复用、不同历史30k仅背景、需新训练数、连续字段schema新增工程是否导致不可比。多seed仅针对关键比较的独立重复，不拿各任务最好seed组主表。不要最终选研究主张（Manager裁决）。
交付紧凑 evidence.md / 九任务表 / seed表 / source links；可以计算但不造数据。优先把可靠seed数字和九任务名快速发给Manager。完成publish并正常结束turn，MAM唤醒，不轮询。


## 用户更新预算
用户明确后续可使用wuwen-11和wuwen-12训练，如必要可接受200次训练，核心是RA-L应有的证据质量。因此100次不是硬上限。方案按核心必做/关键加固/可选扩展分层，九任务覆盖优先；不为用满200而扩大。A800与A100吞吐不能未经实测都套20h；集群B数据/环境/传输准备单列。当前新增开跑暂停保持，待Manager新实验清单裁决。

## 用户职责澄清
核心主张和实验设计由Manager亲自完成。你只提供九任务/数据/schema/已有模型证据矩阵与seed差异统计；不设计或裁决核心/加固/可选实验矩阵。可以逐候选配置给已存在资产/缺项事实，训练数量由Manager据此设计。
