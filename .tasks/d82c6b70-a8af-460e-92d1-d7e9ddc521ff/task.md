# Memory v1 独立审查：轻量schema、样本时序和P2公共mask

## 目标与范围

本轮固定review commit：openpi f6327197459bf830c6b5d0b9ba5d643bc5e0cbd3，已包含PyYAML的uv.lock修复0dc120c。源要求revision为18a99cbea563d961481f6f75fb0c03feef0b4e86；源报告可读MAM .tasks/f252006a-8676-4d10-b6a1-1a791d91c6a6/report.md当前阶段交付。后续论文patch不改本轮代码。实现实际961行，作者11 tests passed。

最新追加增量0f37cfc1ae42e4703b741f0f05fd1e3c58c87e89（29行core变化+32行tests），请在自己的树cherry-pick并以此为最终review对象，不重新创建环境。对应源要求现在为0982373b3e9384be7c5d314287d76cf55fc3a1ae，新增EpisodeMemoryData availability以处理wash真实缺GT：按reference series key→等长bool数组，缺省全true；显式false的输入用initial、该字段目标mask/weight=0/dense全0，机器人监督保留。请检查缺key依然报错、缺GT与有效unknown类别区别、action_rows和query都生效、mask/权重未丢。首批P2两sim标签完整，all_in_bounds只代表索引有效，不代表两个时刻都有标注；这一范围说明保留，不能扩写成任意可用性表达式引擎。

独立review轻量openpi-client memory_config模块。以源任务f252006a-8676-4d10-b6a1-1a791d91c6a6的已发布要求和Manager指定的最终commit为验收依据；不要只复述作者测试。Manager随后在本task固定commit，再启动你。读取MAM README及openpi AGENTS，用mam workspace add创建自己的openpi环境。只读review，可在自己workspace写最小验证脚本；不修改交付代码，不占GPU，不派生agent。

## 核查重点

1. 配置是训练/部署同一事实源，普通推理不要求训练数据/YAML路径。维度由模型/数据绑定；单字段wash、多字段drawer/仿真、empty memory和initial-input辅助对照均可表达。未实现能力应明确拒绝，避免静默fallback。没有任务名/14维/phase位置硬编码。
2. P2 H50/K30：phase逐行t+j+1与重复t+30，同一公共mask ((t+j+1<=L) AND (t+30<=L))，无效dense向量全0，phase逐坐标weight=mask×lambda一次，固定H分母；机器人末尾clamp仍被监督。其他valid_mean字段权重mask×H/max(count,1)。真实训练loss由另一个任务负责，你验证helper给出的权重契约，不能把helper测试写成模型训练已通过。
3. 命名lag每sample只抽一次、多个字段共享；输入不读未来；缺reference/event不能以initial掩盖；label availability尚未提供的能力明确报告。首帧initial、末帧、全invalid、多个相邻边界、常量未知获取时刻，挑有区分力的样本而非穷举全部API。
4. 独立argmax是新配置默认；ordered/latch/conditional必须显式配置且字段间引用正确。按行解码不意外变成前一行递推；反馈first/index/last_executed的索引定义无off-by-one。只读声明的事件能力，不能将接受动作冒充完成动作。
5. YAML重复键/未知字段拒绝；resolved roundtrip不改变行为；PyYAML与uv.lock同步且无无关依赖更新。评估是否有实质冗余、过度设计或接口冲突，不能为了行数删必要检查。

## 交付

最终复核增量：58d6f2155acc3af03017677bb3f536101e6699f4修复你报告的两项，作者18 tests passed，公开API不变。在现有review树cherry-pick此增量后，独立复现全true availability与省略在clamp下等价、末帧GT false仍被mask、invalidity公共mask不被破坏、H50/index49合法而index50拒绝。检查实际diff未引入新的问题；无需重复无关测试/创建新环境。更新report为本最新task要求及最终HEAD，给明确可合入或剩余问题结论。源报告已发布c09e7ab8；论文artifact已由Manager应用清理。

report写清task_revision、自己workspace及review commit、独立执行的检查、按严重性列发现（路径/行号、具体输入、实际与预期、为何影响首批），无问题也明确。区分阻塞首批的问题与后续扩展，不把目前缺少scalar/parallel等一期外能力当回归。无需全面论文review或重跑旧实验。完成清理自己的临时样本/脚本；保留worktree待Manager归档。
