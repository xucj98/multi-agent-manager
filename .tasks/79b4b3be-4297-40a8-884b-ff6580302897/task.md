# 定位已验收轨迹并复现物理执行视频
# 目标
用户明确只验收过一个场景和一条轨迹，后续几乎都没通过，需要真正复现轨迹视频并查看。定位已验收候选（先查probe-0001历史记录，用户正补充），复现一条有依据的轨迹；再选一条后续有代表性的轨迹/失败尝试供比较，若只有partial务必明确。
# 操作
阅读MAM规范、回报CODEX_THREAD_ID，用canonical table-1000/scripts/worktree_env/mam_workspace_add.sh TASK-ID f8340d5de7ac5452a6a8d726c1fc11047c0ae6b1 创建独立worktree，读AGENTS。只读检查canonical outputs和旧库/mnt/public/xcj/table-1000及迁移备份里的视频/计划索引，别读参与者令牌。优先找到历史验收证据，不能将20/20参考计划等同用户验收。用真实物理执行渲染，不能用终态插值视频冒充。与scene agent协调不同空闲GPU，不全套测试/改参数求通过/长程搜索。
# 交付
先尽快返回已有视频候选绝对路径和依据，再复现。输出任务outputs下MP4及6-12关键帧contact sheet（初态、抓取、放置、关键失败、终态），记录来源commit、场景/plan、命令、完整/partial、运行约束。至少1条真实回放，第二条短比较尽力；若复现失败保留失败视频日志，不美化。自行查看关键帧并给manager视觉问题。不宣称用户接受未确认结果。>1h程序登记job，优先短复现。收尾cleanup和publish report，不派发subagent。
