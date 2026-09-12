# C1/C2/C3 NVIDIA PID 显示：在线修复候选验证报告

## 结论

本轮没有找到可在用户态在线部署、且能把 NVML PID 真实映射为当前开发机
PID 的方案。因此没有修复或替换 C1/C2 的默认 `nvidia-smi` / `nvitop`，也
没有修改驱动、容器、服务、评估、全局 Python/NVML、shell 入口或 MAM 代码。

C1/C2 已复现的显示根因是：驱动/NVML 返回的 PID 在当前开发机的 PID
namespace 中无法解析，`nvidia-smi` 因而显示 `[Not Found]`，nvitop 用相同
numeric PID 创建 psutil `HostProcess` 后回退到 `No Such Process` / `N/A`。
这是**显示路径**的确定事实；NVML PID 与任何本地 worker 的一一归属仍未经
授权映射证实，不能靠显存、GPU 编号、PID 数字或命令参数猜测。

C3 不能直接套用 C1/C2 结论：本轮首个 C3 快照没有活跃 NVML process row，
随后一个短暂 GPU0 workload 的 `nvidia-smi` 同时显示本地 PID、进程可执行
路径和 `C+G` 行。C3 当前 `nvidia-smi` 路径可正确显示；没有由本任务施加
“修复”。C3 默认也没有 nvitop，且临时 nvitop 采样时该 workload 已结束，
不能声称已完成 C3 的 live nvitop 渲染验收。

## 三机对照和证据

| 节点 | hostname / driver | 现场结果 | 原命令是否修复 |
| --- | --- | --- | --- |
| C1 `wuwen-4090-1` | `is-ddfwxekq6usner7v-devmachine-0`, R550 `550.127.08`, PID ns `4026541571` | `nvidia-smi` active rows 全为 `[Not Found]`；`-q -d PIDS` 有 compute、`C+G` 和独立 graphics `G` 行，NVML PID 在当前 `/proc` 中均不可解析。系统 nvitop 1.7.1 对 compute 与 graphics 示例均给出 `No Such Process` / `N/A`。 | 否 |
| C2 `wuwen-4090-2` | `is-ddj72hiexddjfwo6-devmachine-0`, R550 `550.127.08`, PID ns `4026541748` | GPU6 gate launcher `1970635`、worker `1970705` 在 probe 前后存活；同窗 GPU6 driver rows 含 `C+G` PID `4010425` 和其他 compute PID，均不在当前 `/proc`。临时 nvitop 1.7.1 对该 graphics PID 也为 `No Such Process` / `N/A`。 | 否 |
| C3 `wuwen-4090-3` | `is-ddj72jhhjdy7hiyj-devmachine-0`, R580 `580.82.07`, PID ns `4026541020` | 初始无活跃 process/gate；后续 GPU0 transient workload 的 `nvidia-smi` 显示 local PID、解释器路径和 `C+G`，相应 PID 在本地存在。 | 不需要本任务修复 `nvidia-smi`；live nvitop 未验收 |

C1 七路正式评估在 probe 前后仍可见；例如 launcher `2130358` 与 worker
`2130887` 的 elapsed time 继续增加。前置报告中 C1 seed1/eval1 记录为 56，
本轮为 69，确认读取/候选运行没有中断评估。C2 gate 的 launcher/worker 也
在 probe 前后存在且 elapsed time 增加。C3 之后回到 GPU0 1 MiB、无 active
process 的空闲快照；没有等待或重启它以制造测试负载。

## 来源、版本与排除项

- 三机均从 `/usr/bin/nvidia-smi` 调用当前宿主机注入的 NVML。C1/C2 的
  `libnvidia-ml.so.1` 指向 550.127.08；C3 指向 580.82.07。
- C1 的 `/usr/local/bin/nvitop` 是 `nvitop==1.7.1`、`nvidia-ml-py==13.595.45`
  和 `psutil==7.2.2`；`pip index versions nvitop` 显示 1.7.1 已是 latest，
  因此没有盲目升级。C2/C3 默认未安装 nvitop；在各自 `/tmp` 独立 venv 固定
  安装相同 1.7.1 复现/比较，不触碰全局 site-packages。
- nvitop upstream 当前代码的 `Device.processes()` 明确轮询
  `nvmlDeviceGetComputeRunningProcesses` **和**
  `nvmlDeviceGetGraphicsRunningProcesses`，再以 NVML 的 `p.pid` 构造
  `HostProcess(pid)`；其 `cmdline`/username/CPU 回退与现场一致。见
  [nvitop device source](https://raw.githubusercontent.com/XuehaiPan/nvitop/main/nvitop/api/device.py)
  和 [process source](https://raw.githubusercontent.com/XuehaiPan/nvitop/main/nvitop/api/process.py)。
- NVIDIA 的文档也将 compute 与 graphics 列为独立 NVML 查询，且 `nvidia-smi`
  Processes 输出的 PID/Type/Name 由该层提供：
  [NVML Device Queries](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlDeviceQueries.html)，
  [nvidia-smi process semantics](https://docs.nvidia.com/deploy/nvidia-smi/)。
- nvitop 的 Docker 文档要求 `--pid=host` 才能从容器看到 host processes；这
  佐证了 PID-namespace 前提，但不适用于本任务的在线边界，故未尝试：
  [upstream Docker guidance](https://github.com/XuehaiPan/nvitop#for-docker-users)。
- 平台公开文档确认开发机是容器、驱动由宿主机约束且用户不能自行更换；公开
  resource-monitor 只提供 GPU 使用率/显存等聚合指标，没有发现受支持的
  tenant-scoped host-PID 映射 API 或监控入口：
  [driver boundary](https://docs.neogpu.com/compute/dev-instance-rerun.html)，
  [resource monitor](https://docs.neogpu.com/ai-studio/dev-instance/resource-monitor.html)。

R550 C1/C2 与当前 R580 C3 的差异是有价值的平台对照，但尚无证据能把它定性为
单纯驱动版本 bug；按平台边界，用户也不能将 C1/C2 升级到 R580。没有发现可用
的 `nvidia-container-cli`、`nvidia-ctk`、平台 PID adapter 或 host `/proc`
映射文件；`/proc/driver/nvidia/clients` 在三机均不可用。

## 已验证的最小用户态候选

交付文件：

- `/mnt/public/xcj/Projects/workspace/2f6ec567-e628-46ba-94ff-ac97daa009cb/candidate/gpu_pid_visibility_probe.py`
- `/mnt/public/xcj/Projects/workspace/2f6ec567-e628-46ba-94ff-ac97daa009cb/candidate/README.md`
- 最小证据：`/mnt/public/xcj/Projects/workspace/2f6ec567-e628-46ba-94ff-ac97daa009cb/evidence.md`

该 probe 以 `nvidia-smi -q -d PIDS` 读取所有 driver 报告的行，故不会遗漏
graphics/`C+G`；只标记一个 numeric PID 是否碰巧出现在当前 `/proc`。即使
numeric PID 存在，也输出 `numeric-pid-present-but-unverified` 并拒绝读取或
显示该进程的 command、user、CPU、NSpid，避免 PID 重用/跨 namespace 碰撞
造成伪归属。它不读取 `/proc/*/fd/0` 或 environ，不启动 GPU workload，也不
修改任何状态。

```bash
python3 /mnt/public/xcj/Projects/workspace/2f6ec567-e628-46ba-94ff-ac97daa009cb/candidate/gpu_pid_visibility_probe.py
```

源码 SHA-256：
`42e544cca16d68c4cd6a3f6d41e7a412fbc82f14c57db3bbad140b93c77511a9`。
`python3 -m py_compile` 通过；源码以相同 hash 复制到三台 C 节点的独立
`/tmp/mam-2f6ec567/` 后运行。C1/C2 输出均保留所有行而标为 unresolved；C3
有 locally-present 的数字但仍标 unverified，真正的 C3 mapping 只依据
`nvidia-smi` 同窗显示的可执行路径和本地 PID 核对。

这只是**补充诊断视图**，不修复原命令，也不是可用于进程归属/终止的工具。它
不应替换用户原有命令或写入 shell profile。新文件相对空基线的可审阅 diff：

```bash
git diff --no-index -- /dev/null \
  /mnt/public/xcj/Projects/workspace/2f6ec567-e628-46ba-94ff-ac97daa009cb/candidate/gpu_pid_visibility_probe.py
```

该命令对新增文件预期返回 exit 1；不代表失败。

## 适用范围、风险、回滚与最小后续措施

- **C1/C2 原命令修复：未完成。** nvidia-smi 的 process-name 解析和 nvitop
  的 psutil 解析都缺少权威 host→container PID translation；用户态 wrapper
  不能凭猜测补齐它。安装新版 nvitop 也不能改变底层 PID identity。
- **C3：** 当前 `nvidia-smi` 已可显示真实 local PID；无默认 nvitop 可改，且
  本任务不在 C3 部署任何默认工具。
- **已清理的验证环境：** 三机 `/tmp/mam-2f6ec567/`（脚本和 C2/C3 venv）已
  删除。没有持久化 package/config/alias，故无系统 rollback；
  如 Manager 以后复测，删除该指定 `/tmp` 目录即可回滚临时副本。
- **需要的平台能力：** 平台应提供 tenant-scoped、权限受限的监控入口，或在
  开发机注入官方 PID-namespace-aware NVML/SMI 适配。若返回 mapping，至少应
  为每条 compute/graphics row 同时给出 namespace identity、host PID、local
  PID 和抗 PID-reuse 的启动身份，且只允许该实例的可见对象。不能用 host PID
  namespace 或可浏览 host `/proc` 作为当前线上 workaround。
- **给平台支持的最小复现材料：** C1/C2 R550、当前 PID namespace inode、
  `nvidia-smi -q -d PIDS` 的 `[Not Found]`/空 Name，以及同一 PID 在当前
  `/proc` 不存在；C3 R580 的成功同窗可作为对照。请平台在不暴露其他租户
  process metadata 的条件下确认其 runtime 是否提供 PID translation。

## 交付

- Workspace：`/mnt/public/xcj/Projects/workspace/2f6ec567-e628-46ba-94ff-ac97daa009cb`
- 项目仓库/worktree/commit：无。任务没有修改项目仓库；候选和证据仅位于本
  task workspace。
- 验证：C1/C2/C3 SSH 只读采样，C1 current nvitop，C2/C3 disposable nvitop
  1.7.1，候选 script hash/compile/三机 one-shot，C1 eval 与 C2 gate pre/post
  identity 检查，官方 NVIDIA/nvitop/平台文档核查。
