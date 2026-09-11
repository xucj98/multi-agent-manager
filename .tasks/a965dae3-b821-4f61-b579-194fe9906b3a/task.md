# 复现现有场景渲染并核验视觉质量
# 目标
用户说明只有一个场景和一条轨迹获本人验收，其余几乎不满意。先复现和看图，不能把工程pass当人类验收。复现3个代表场景的初态/终态多视角渲染：probe-0001，以及后续0006和另一个密集probe（建议0007）。
# 操作
阅读MAM规范，回报CODEX_THREAD_ID。用canonical table-1000/scripts/worktree_env/mam_workspace_add.sh TASK-ID f8340d5de7ac5452a6a8d726c1fc11047c0ae6b1 创建独立worktree，读AGENTS。查既有命令，使用实际ManiSkill渲染，不造示意图。限定单张空闲GPU并与轨迹agent协调。先尽快交付0001一张初态和终态图供manager看，不等待整批完成。不要全套测试、改场景或替换资产。缺少缓存时报告具体缺口，避免大规模下载。输出到任务outputs，保留每张图scene/terminal ID、camera、命令、commit、配置，区分handwritten terminal与实际执行终态。
# 验收
3个场景初态和至少一个终态的俯视/斜视图，必要时拼成标注清晰contact sheet；检查资产像不像对象/容器、穿透/漂浮、密度、任务合理性和真实多解。所有人工验收状态标待用户确认。报告具体视觉问题，不以schema或物理稳定替代视觉质量；自行查看图，向manager返回绝对图片路径。短smoke不用job；预计>1h需登记，优先短复现。收尾cleanup并publish report。不得派发subagent。
