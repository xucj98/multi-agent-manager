# C1/C2/C3 NVIDIA PID 显示：C3 现场验证与交付报告

## 结论

C1、C2 仍没有可安全在线部署的 PID 映射修复。两机的驱动/NVML 返回的
GPU 行 PID 在调用者 PID namespace 中不可解析：`nvidia-smi` 显示
`[Not Found]`，nvitop 1.7.1 对同一 PID 回退为 `No Such Process` / `N/A`。
这证明当前实例缺少可用的进程身份解析，不证明任何本地 worker 对应某个
NVML PID；没有依据显存、GPU 编号、数值 PID 或命令参数推测归属，也没有部署
wrapper、改动默认命令或干扰评估。

C3 的实时 GPU0 评估证明其当前环境可以正确解析本地 PID。已在 C3 安装并验证
一个**明确命名的独立入口** `nvitop-c3`，用于查看真实 compute/graphics 进程。
它不替换原有 `nvitop`，不修改 shell profile、全局 site-packages、驱动、
容器或共享运行时。

## 三机证据与适用范围

| 节点 | driver / PID namespace | 现场结果 | 交付状态 |
| --- | --- | --- | --- |
| C1 `wuwen-4090-1` (`is-ddfwxekq6usner7v-devmachine-0`) | R550 `550.127.08`; `pid:[4026541571]` | `nvidia-smi` 的 active rows 为 `[Not Found]`；`-q -d PIDS` 同时包含 compute、`C+G`、graphics `G` 行，所报 PID 不在该实例 `/proc`。系统 nvitop 1.7.1 对 compute/graphics 均显示 `No Such Process` / `N/A`。 | 未修复；不部署猜测性 wrapper。 |
| C2 `wuwen-4090-2` (`is-ddj72hiexddjfwo6-devmachine-0`) | R550 `550.127.08`; `pid:[4026541748]` | GPU6 gate 存活期间，driver-visible compute/`C+G` PID（含 `4010425`）不在该实例 `/proc`；隔离 nvitop 1.7.1 同样回退为 `No Such Process` / `N/A`。 | 未修复；不部署猜测性 wrapper。 |
| C3 `wuwen-4090-3` (`is-ddj72jhhjdy7hiyj-devmachine-0`) | R580 `580.82.07`; `pid:[4026541020]` | 实时 GPU0 评估期间，`nvidia-smi` 显示本地 compute PID `1032416` 和 `C+G` PID `1032527`，并显示真实 Python 路径。两 PID 在 nvitop 前后均存活。 | 已交付独立 `nvitop-c3` 入口。 |

C1 七路正式评估及 C2/C3 gate/评估均未重启、终止或改动。C3 与 C1/C2 的差异是
现场对照，不能据此断言 R580 驱动版本是原因或把升级当作在线修复方案。

完整的最小只读证据位于
`/mnt/public/xcj/Projects/workspace/2f6ec567-e628-46ba-94ff-ac97daa009cb/evidence.md`。

## C3 实时 nvitop 验证

在 C3 的真实 GPU0 评估窗口内，先以 disposable nvitop 1.7.1 venv 将稳定行的
`command`、`user`、`CPU` 与 `psutil.Process(同一 PID)` 比较；命令行和用户一致，
CPU 为可读数值。随后实际 CLI 结果为：

```bash
nvitop --once --readonly --compute --only 0
nvitop --once --readonly --graphics --only 0
```

- compute 视图显示真实 command/user/CPU；GPU0 当时约为 `16121MiB / 23.99GiB`。
- graphics 视图显示 PID `1032527` 的 `C+G` 行，并显示同一真实
  command/user/CPU。
- 上述行与同窗 `nvidia-smi` 本地 PID 一致；验证前后评估 PID 均存活。

因此 C3 的独立入口可提供经验证的真实进程字段；这不是对 C1/C2 的 PID 映射
修复，也不表示 C3 对任意未来 workload 均已重新验收。

## C3 安装、使用与回滚

C3 上已存在的 `nvitop` pipx 链接已保留：

```text
/root/.local/bin/nvitop
-> /root/.local/share/pipx/venvs/nvitop/bin/nvitop
```

新入口与隔离 venv 为：

```text
/root/.local/bin/nvitop-c3
-> /root/.local/share/venvs/nvitop-c3/bin/nvitop
```

固定版本：

```text
nvitop==1.7.1
nvidia-ml-py==13.595.45
psutil==7.2.2
```

推荐使用方式：

```bash
nvitop-c3 --readonly --only 0
nvitop-c3 --once --readonly --compute --only 0
nvitop-c3 --once --readonly --graphics --only 0
```

清理 disposable 验证环境 `/tmp/mam-2f6ec567-c3-nvitop` 后，已用 SSH login shell
复验：`command -v nvitop-c3` 返回 `/root/.local/bin/nvitop-c3`，
`nvitop-c3 --version` 返回 `nvitop 1.7.1`。如需撤销这次 C3 专用安装，仅删除
这两个新对象，勿触碰已有的 `nvitop` pipx 链接：

```bash
unlink /root/.local/bin/nvitop-c3
find /root/.local/share/venvs/nvitop-c3 -depth -delete
```

## 平台支持复现材料

已准备、但**未发送**给平台的最小复现草稿：
`/mnt/public/xcj/Projects/workspace/2f6ec567-e628-46ba-94ff-ac97daa009cb/platform_support_repro.md`。
它请求平台确认是否有受支持的实例内 PID translation 或 tenant-scoped 监控入口，
要求 compute/graphics 行给出权威 local PID 与抗 PID-reuse identity；不请求 host
`/proc`、host PID namespace、容器重建、驱动改动或服务重启。

## 清理与交付

- 已删除没有部署用途的旧候选 probe、README、空 `candidate/` 目录及 C3 的
  disposable venv；没有保留可被误当作 C1/C2 修复工具的文件。
- Workspace：`/mnt/public/xcj/Projects/workspace/2f6ec567-e628-46ba-94ff-ac97daa009cb`
- 项目仓库/worktree/commit：无；本任务未修改项目代码仓库。
- 验证：三机只读 NVML/PID 采样；C3 实时 compute 与 graphics nvitop/psutil
  同 PID 核对；C3 持久入口的 SSH login-shell 解析与版本复验。
