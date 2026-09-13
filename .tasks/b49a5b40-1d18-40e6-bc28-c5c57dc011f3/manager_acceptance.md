# Manager 验收与降级方案裁决

用户于 2026-09-13 明确选择：“先作降级处理，把信息转到你这里，这个问题先close。”采用已验收的 native-v2 拒绝转 Manager 路由，停止直达接口/预挂起等待等替代路线的调查。

源码交付为 3f2738abcfc9cbe50b25222562fc58b2bac0a7ff，已进入 main 与项目分支。独立 review 052c3051 的最终报告为 4580953c243b45b5c1d688bf3261aa990801d34a，核心 215 项测试通过。Manager 已直接核对精确错误匹配、停止重试、按源事件签名去重、有效且不同的 Manager 路由和旧拒绝状态迁移。

真实原生 fixture 已完整验收；本目录 native-v2-fallback-evidence.json 的 SHA-256 为 b87e37cbb0214f53f447f23d13c297863fdf14d753869756c895aead699858bf。9 项通过检查及14项回执覆盖真实拒绝一次、Manager active 不打断、重启去重、root 空闲实际收到一次消息、同一子 agent 原生接续并归档、事件进入历史和 fixture 清理。Manager 再次核对汇总哈希、状态与上述检查，未重跑实验。

代码任务可归档；实际生产切换和安装验收由任务 a0c09804-1b5b-4df3-abf0-986ff19381af 继续跟踪，不能以本代码验收代替其成功安装结论。独立 pipx 包是非 editable 安装，不依赖作者 worktree。

关闭口径为“通过 Manager 转发的降级处理完成”。原生 v2 child 直接 turn/start 的限制仍存在，不宣称 Codex 直达能力已恢复。
