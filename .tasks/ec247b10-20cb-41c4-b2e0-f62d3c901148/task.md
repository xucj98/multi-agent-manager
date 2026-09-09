# 论文实验设计：问题、受控矩阵与文献核查
# 目标

为论文首批实验与两周计划做独立的实验设计/文献评议，帮助Manager裁定；不写代码、不运行实验。重点是提出少量能被数据支持或否定的研究问题，以及可直接运行的有限比较。最终只编辑本任务report.md，Manager整合进论文库。

# 背景与必读

论文 /root/Documents/task-state-vla-paper，读 ROADMAP.zh-CN.md、docs/MEMORY_DESIGN_FRAMEWORK.zh-CN.md、docs/MEMORY_CONFIG.zh-CN.md；历史证据已在 /mnt/public/xcj/Projects/RMBench/experiments/history_audit_20260909，不重做历史全量审计。研究主线：给定相同低维任务记忆内容，action chunk下监督与递推反馈的选择如何影响闭环可靠性。schema是分析和控制变量的工具，不能本身充当贡献。已有full/serial差异是多因素差异；Oracle不是自动上界；offline回放不是闭环成功率。

# 具体交付

1. 评议P1反馈位置、P2逐帧/重复终点、P3按钮语义×K是否回答中心问题；尤其P2公共mask+固定H分母是否是有效控制、是否无意引入新混杂。指出真正需要修改的地方，不展开全笛卡尔积。
2. 推荐最多3个核心研究问题，每项写：已知现象、尚未知、最小比较、固定项、正/负结果分别支持什么。给一个两周分层矩阵，分清训练run数、checkpoint数、100ep评测run数，首波8个单GPU训练名额（另2卡eval），之后补3个train seeds。含无记忆和辅助监督无递推对照的必要性判断；full/serial能力比较不能称纯编码效应。
3. 新训练统一单卡bs32、20k steps、只留最终BF16模型权重与metadata，估算18GPU小时/run。十卡两周3360GPU小时，需扣eval/开发，不能许诺200个18h训练均完成。给基础预算与扩展预算；wuwen-11仅追加候选、不访问。
4. 真机：wash-cup单phase，drawer phase+attribute，full/serial；wash所有有效数据训练、5个训练ep做offline。label6、缺标注、不是1..5各一次过滤，顺序可变；S2M。人类安排真机闭环，不假称offline已证明成功。
5. 浏览并只引用原论文/作者代码核查SAGE（2509.19853）、Why Does Action Chunking Improve Behavioral Cloning Performance in Robotic Control?（2608.02547）以及最多2篇直接相关工作。每篇给可核验URL、它实际研究了什么、我们的设计空间与其是否重合；不宣称未经查证的新颖性。若具体网页不可访问明确未知。引用内容遵守摘要/引用限制。

# 边界与交付

只读调查与方案评议，不创建代码环境/worktree，不修改论文原文件、不使用GPU。报告力求150行以内、有数据/来源的结论优先，不写冗长预防性清单。读MAM发布任务，最终report包含task_revision、完成/未知、workspace与无代码commit、结果与来源，发布report，清理临时文件等待归档。你不能继续派subagent。
