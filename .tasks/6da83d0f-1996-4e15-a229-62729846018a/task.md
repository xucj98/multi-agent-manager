# Manager wait 快捷停止

从 MAM main 9f2ebe1b489054886e7bcfdb22dcf39703d5eb06 创建独立worktree。当前生产MAM根 /mnt/public/xcj/Projects/multi-agent-manager，项目发布分支project/state-vla，任务/报告在生产根编辑发布。实现提交只基于main；不要把项目分支合回main。

## 实施
1. 增加 `mam wait stop manager`，保留 `mam wait stop --agent AGENT-ID`。二者互斥且必须选一种。按当前MAM中有效wait记录及当前未归档task绑定，识别未绑定task的等待agent，恰好一个则停止该等待。无候选或多个均明确报错，不需要用户先wait list。不能把wait的--task过滤参数误当成agent绑定。若身份无法确认不能默默选另一个。复用现有PID/identity/token/锁保护，处理检查后wait已结束的正常竞争，不误停替换后的新等待。不引入manager注册表/daemon或外部agent查询；不停止任何被监控job。
2. scripts/create_worktree.sh 为新MAM worktree可选地建立 .local/README.md 单文件软链接，指向源MAM根的本地README（存在时）；不共享整个.local。缺失时允许创建，不覆盖已有冲突文件。保持MAM上下文隔离及归档安全：验证这个受控软链不会让正常mam task archive失败；必要时最小调整认可方式，不放宽未知文件/任务数据保护。

## 范围与验收
实现/脚本/测试/设计文档由你负责，README/AGENTS由Manager负责（用户刚修改了生产README，不碰它）。完整测试，覆盖唯一manager、零/多候选、绑定执行者排除、身份不明/结束竞争、只停止等待不停止jobs、两项目隔离，及本地README链接/缺失/冲突与归档。实际短进程验证stop manager快速返回且job仍运行，不用GPU。不增加大量镜像测试或重复验证。

## 交付
提交代码，发布报告记录commit、改动文件、验证与限制。清理短测试产物/缓存，保留worktree待review。不要自行合并安装。
