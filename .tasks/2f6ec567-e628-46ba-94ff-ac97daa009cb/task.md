# C1 nvidia-smi / nvitop PID 显示修复

用户明确要求尝试修复 wuwen-4090-1 的 nvidia-smi 进程列表缺失、nvitop No Such Process/N/A。具体执行由 terra/max 完成，Manager 核对事实与方案后裁决。前置诊断 TASK-ID 82bbbd0b-ee27-4a34-92c6-3d8e1cccdd8b，先 mam task show --file report 读取；不重复基础诊断。

## 执行边界
先读 AGENTS/README/.local/README。先回 CODEX_THREAD_ID 绑定。任务工作空间用于诊断与候选文件；若修改项目仓库，用独立 worktree 并阅读其AGENTS。不要为纯系统工具修复修改MAM代码。

正在跑的 C1 七路正式评估必须继续；禁止 GPU reset、驱动卸载/重载/升级、容器重建、服务/评估重启、全局 /proc 或 PID namespace 改动、kill 他人进程。不读取 /proc/*/fd/0、不输出凭据/整份environ。不尝试越过集群隔离或访问未授权的其他租户环境。

用户授权了可逆的修复尝试。可用独立临时目录/用户态独立环境验证候选；不直接覆盖系统 nvidia-smi/nvitop 或全局Python/NVML库，不改shell默认入口，先交具体diff、复现结果和rollback给Manager审阅。避免盲目pip升级，先找版本行为或机制证据。

## 排查与候选要求
1. 核查驱动/NVML与nvitop来源、版本和当前调用路径；检查是否存在本平台提供的容器PID适配、受支持监控入口、错误的库选择/包装或环境差异。只读必要且非敏感字段。
2. 查官方nvitop/NVIDIA/平台可用文档与上游issue，确定当前版本是否有现成namespace映射支持。不要把通用“用host PID namespace重建容器”当作可在线应用的修复。
3. 只有具备可验证映射证据时，才能显示NVML PID对应的本地命令、CPU、用户名；compute/graphics分别核对，不能用显存相近、PID偏移、GPU编号或CUDA_VISIBLE_DEVICES推测一一映射。单个renderer不出现在compute列表本身也不证明其NVML PID不一致（需检查graphics）。
4. 优先验证能使用户原有两个命令恢复真实进程信息的最小方案。若只能提供独立监控命令/补充视图，要明确是替代查看方式而非原命令已修复。未映射行保留未知，不隐藏占用或伪造归属。
5. 任一候选先在独立进程/环境运行，核验GPU总显存/占用和可见本地进程真实一致、无PID误映射，运行前后评估进程身份与结果增量正常。不要新启GPU负载作测试。
6. 有可信方案尽早发给Manager；没有可在线修复入口时，给出已排除路径、具体缺少的能力和最小后续措施，不无限探索，也不将“尚未找到”写成绝对不可修。

## 交付
发布report：根因证据、尝试及实际输出、候选文件/diff/准确命令、适用范围、风险/回滚、是否真正修复nvidia-smi和nvitop各自显示；保存最小必要证据。未验收不部署默认命令。当前可执行事项结束正常结束turn，由MAM唤醒，不轮询。

## 用户追加范围：C2 / C3 同样异常
用户确认 wuwen-4090-2 和 wuwen-4090-3 也存在相同 nvidia-smi/nvitop 显示问题。修复范围扩展为 C1/C2/C3，分别验证hostname、驱动/NVML/nvitop来源与PID可见性、可用映射入口，不把C1结论直接当作三台同根因。C1已有正式评估、C2 GPU6和C3 GPU0已有40-reset gate，所有活跃进程保持。先在一台独立用户态环境验证，再提出适用另外两台的具体方案；共享/mnt/public意味着不能以不同SSH主机当作不同文件树。报告提供三台的对照及各自是否修复/限制。其余约束不变。

## Manager复核与C3可执行收尾
Manager已读9de0262报告/源码/证据，接受C1/C2暂无可靠在线映射候选；不把补充探针当修复部署。C3 Manager独立SSH复核当前GPU0约16142MiB，nvidia-smi正确显示PID1032416/1032527等及完整评估runtime路径，command -v nvitop为空。现在有真实活跃负载，可完成此前缺失的live nvitop验证。

请在C3独立用户态venv固定nvitop1.7.1及已验证依赖，核验compute和graphics的nvitop command/user/CPU字段可读且与/proc真实进程一致。不要新启GPU负载或干扰评估。若通过，授权提供持久独立工具入口：优先使用C3本机 /root/.local/share/venvs/nvitop-c3 及 /root/.local/bin/nvitop（仅在该路径不存在、无用户现有命令被覆盖时创建链接；否则用独立明确命名入口）。不要改全局site-packages、shell profile、驱动或C共享runtime。确认SSH login shell能找到命令，否则报告已验证的绝对入口即可。

C1/C2暂不部署猜测性wrapper；将最小平台支持复现说明准备为简短文本，含主机名/driver版本、默认命令、实测异常和C3对照、希望平台提供的实例内PID可见性支持，不发送给平台（用户尚未授权对外联系）。如果平台官方文档无法直接核实，不把该平台架构限制写成绝对事实。

发布增量report：C3真实nvitop显示样本/入口/版本/卸载方式、C1/C2未修复边界、平台复现文本位置。删除无部署用途的重复临时probe/cache，保留最小证据即可。当前任务在这一步后再由Manager收尾。
