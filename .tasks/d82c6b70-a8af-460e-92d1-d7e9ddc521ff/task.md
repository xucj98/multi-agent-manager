# Memory v1 独立审查：轻量schema、样本时序和P2公共mask

## 目标与范围

本轮固定review commit：openpi f6327197459bf830c6b5d0b9ba5d643bc5e0cbd3，已包含PyYAML的uv.lock修复0dc120c。源要求revision为18a99cbea563d961481f6f75fb0c03feef0b4e86；源报告可读MAM .tasks/f252006a-8676-4d10-b6a1-1a791d91c6a6/report.md当前阶段交付。后续论文patch不改本轮代码。实现实际961行，作者11 tests passed。

独立review轻量openpi-client memory_config模块。以源任务f252006a-8676-4d10-b6a1-1a791d91c6a6的已发布要求和Manager指定的最终commit为验收依据；不要只复述作者测试。Manager随后在本task固定commit，再启动你。读取MAM README及openpi AGENTS，用mam workspace add创建自己的openpi环境。只读review，可在自己workspace写最小验证脚本；不修改交付代码，不占GPU，不派生agent。

## 核查重点

1. 配置是训练/部署同一事实源，普通推理不要求训练数据/YAML路径。维度由模型/数据绑定；单字段wash、多字段drawer/仿真、empty memory和initial-input辅助对照均可表达。未实现能力应明确拒绝，避免静默fallback。没有任务名/14维/phase位置硬编码。
2. P2 H50/K30：phase逐行t+j+1与重复t+30，同一公共mask ((t+j+1<=L) AND (t+30<=L))，无效dense向量全0，phase逐坐标weight=mask×lambda一次，固定H分母；机器人末尾clamp仍被监督。其他valid_mean字段权重mask×H/max(count,1)。真实训练loss由另一个任务负责，你验证helper给出的权重契约，不能把helper测试写成模型训练已通过。
3. 命名lag每sample只抽一次、多个字段共享；输入不读未来；缺reference/event不能以initial掩盖；label availability尚未提供的能力明确报告。首帧initial、末帧、全invalid、多个相邻边界、常量未知获取时刻，挑有区分力的样本而非穷举全部API。
4. 独立argmax是新配置默认；ordered/latch/conditional必须显式配置且字段间引用正确。按行解码不意外变成前一行递推；反馈first/index/last_executed的索引定义无off-by-one。只读声明的事件能力，不能将接受动作冒充完成动作。
5. YAML重复键/未知字段拒绝；resolved roundtrip不改变行为；PyYAML与uv.lock同步且无无关依赖更新。评估是否有实质冗余、过度设计或接口冲突，不能为了行数删必要检查。

## 交付

report写清task_revision、自己workspace及review commit、独立执行的检查、按严重性列发现（路径/行号、具体输入、实际与预期、为何影响首批），无问题也明确。区分阻塞首批的问题与后续扩展，不把目前缺少scalar/parallel等一期外能力当回归。无需全面论文review或重跑旧实验。完成清理自己的临时样本/脚本；保留worktree待Manager归档。
