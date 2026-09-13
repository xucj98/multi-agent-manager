# Manager 生产验收：降级转发已上线，问题关闭

接受安装报告 95a7e6d87719f159734740333baf89e3819a0e1e。用户已明确选择将 native-v2 拒绝转到 Manager，不再继续直达接口调查。

Manager 独立核验：

- 标准 installer transcript 的实际215项测试通过、wait/API检查通过、普通持久线程6-turn真实投递通过和生产healthy通过标记；installer_exit=0。6份报告引用的主要artifact哈希全部匹配。
- 直接读取生产进程1074834的 /proc 身份：boot_id 和 start_ticks=55016755 与 service登记一致，隔离bootstrap选中 pipx site-packages，不引用 task worktree。实际进程identity.started_at为2026-09-13T12:09:03Z；service ready_at为12:09:04Z，以这两种不同含义区分报告中的近似启动时间。
- 从实际bootstrap指定路径读取 wake_runtime.py，逐字节等于 Git 3f2738abcfc9cbe50b25222562fc58b2bac0a7ff 对应源码，SHA-256为c926e9d9d9d916ad80bbb37219be8e26f52f0700fe6a88171669390691f55de2。pipx direct_url 的 dir_info 没有 editable 标记；安装不依赖该 task 树。
- mam service status确认running/healthy，Manager仍为01a09657-e0f3-7352-b726-aba5bbd5d498；验收时pending为0。训练8项job ID在安装前后快照相同。App Server无需重启由标准installer的实际listener检查和成功路径确认，未安排额外重启。

验证边界：普通liveprobe的原始临时JSON已被标准installer清理。保留的是明确标注的derived receipt、原始安装transcript及固定源码中的八项check/6-turn校验路径；不宣称Manager重新逐一读取了该次已删除的thread/turn receipt，也不为留存缺口重跑模型测试。原生拒绝→root实际收到→同child原生接续→归档的完整14份原始回执此前已另行保存在源任务b49a5b40并验收。

本次可按“降级处理完成”关闭：源码、独立代码review、原生集成fixture、安装与生产服务身份已通过对应验收，源任务已归档。后续遇精确v2拒绝时由MAM停止盲重试并转Manager，Manager核对真实执行状态后使用原生followup接续。不宣称Codex已支持外部直达v2子agent。
