# 通用 memory offline 独立 review

## 目标与输入
独立审阅b86b3d02-29f2-437a-a5e7-db427a7df96c最新已发布task与report，判断wash单字段和旧drawer多字段共用offline实现是否正确、范围是否合理，可否进入新20k GPU offline验收。作者robot-bridge提交3a364a6dd87c08753a804e5598ddc85ef832d9b1，对照base bd30069ffc0b773de13f98f53753566711960858；openpi a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。
通过mam workspace add在自己的workspace建立两库独立worktree，阅读两库AGENTS和bridge docs/design/conventions.md。不要修改作者树、主树或训练树。不占GPU、不启动模型训练/推理。不派其他agent。

## 重点
1. 使用make_training_sample的真实训练时序、availability mask、机器人offset0；full per-frame/repeated endpoint与serial语义一致，多字段可用。GT只用于指标，不进入policy观测、MemoryContext反馈或未来信息。检查实际execute行与memory反馈/记录时刻一致，reset与wait-condition不回归。
2. CPU实际测试关键边界及旧drawer回归，不只复述作者49 passed；选有意义的独立反例（episode末尾、缺失mask、多字段、非默认H/K等）。确认wash五集确为转换索引0–4、raw/source-frame对齐。报告中的5525 query究竟是实际policy调用数还是数据行数，需要辨清。
3. launcher增加约520行，有root alias registry、string/mapping双路径、可选replay section、metadata重复字段。明确哪些是当前两套manifest实际所需，哪些属于可以删除的泛化；核对冲突字段会否默默优先覆盖。以具体风险和最小修复建议为主，不用行数本身判错。
4. 留痕必须是实际运行的bridge/openpi源码commit与解释器，不能用checkpoint数据根目录的Git HEAD冒充policy源码版本。检查clean门禁、退出清理、metadata传递与真实恢复参数。
5. 旧drawer沿同一通用机制；遗留格式适配可以存在，不应另写wash专用算法。报告声明不超过已测边界。

## 交付
先给阻塞级问题及证据（文件/行、复现、影响、最小修改），区分正确性阻塞、建议简化和非问题；Manager裁定，review意见不是自动修改指令。不改业务实现，可临时编写必要独立测试并清理。报告含测试命令/结果、两库commit、剩余GPU验收，写report并mam发布。保留worktree供Manager验收。目标约30分钟首轮结论，若遇环境阻塞及时报告实际错误，不凭路径猜测另建框架。

## 07:27 修复增量复查
作者新commit fda269c1f333dabdb5628c083a4dba3db0938333，report已发布。将自己bridge worktree在自己的task分支推进到该commit，独立核对P1实际policy源码/clean/served握手、P2冲突拒绝及--replay删除，无需重复已通过全部controller时序验证。定向反例至少覆盖dirty实际OpenPI与干净checkpoint根不混淆、握手源码不符/解释器不符拒绝、重复时序冲突拒绝及两有效manifest。若通过明确可进入GPU offline，剩余实际权重验收如实标出。不占GPU，报告新commit与检查结果；目标10–15分钟。
