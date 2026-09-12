# C1/C2/C3 NVIDIA PID 显示：最终核验报告

## 结论

C1、C2 仍没有可安全在线部署的 PID 映射修复。两机的驱动/NVML GPU 行 PID
无法在调用者 PID namespace 中解析：`nvidia-smi` 显示 `[Not Found]`，nvitop
1.7.1 对同一 PID 回退为 `No Such Process` / `N/A`。这证明当前实例缺少可用的
进程身份解析，不能据此把任何本地 worker 归属给某个 NVML PID；没有依据显存、
GPU 编号、数值 PID 或命令参数推测归属，也没有部署 wrapper 或改动默认命令。

C3 原有的登录 shell `nvitop` 已确认正常。本任务没有修复 C3 底层显示：它原本
就通过 `/root/.local/bin/nvitop` 指向 pipx 的 nvitop 1.7.1，并在真实 GPU0
负载下显示本地 PID、用户、CPU 和命令字段。此前非登录 SSH shell 中
`command -v nvitop` 的空结果不足以证明未安装，现已纠正。为避免重复安装，
本任务新建的 `nvitop-c3` 链接和 venv 均已删除；原 pipx 入口保持不变。

## 三机现场结果

| 节点 | driver / PID namespace | 现场结果 | 交付状态 |
| --- | --- | --- | --- |
| C1 `wuwen-4090-1` (`is-ddfwxekq6usner7v-devmachine-0`) | R550 `550.127.08`; `pid:[4026541571]` | `nvidia-smi` active rows 为 `[Not Found]`；`-q -d PIDS` 包含 compute、`C+G`、graphics `G`，所报 PID 不在当前实例 `/proc`。nvitop 1.7.1 对 compute/graphics 显示 `No Such Process` / `N/A`。 | 未修复；不部署猜测性 wrapper。 |
| C2 `wuwen-4090-2` (`is-ddj72hiexddjfwo6-devmachine-0`) | R550 `550.127.08`; `pid:[4026541748]` | GPU6 gate 存活期间，driver-visible compute/`C+G` PID（含 `4010425`）不在当前实例 `/proc`；隔离 nvitop 1.7.1 同样回退。 | 未修复；不部署猜测性 wrapper。 |
| C3 `wuwen-4090-3` (`is-ddj72jhhjdy7hiyj-devmachine-0`) | R580 `580.82.07`; `pid:[4026541020]` | 原 pipx nvitop 1.7.1 和 `nvidia-smi` 均可解析本地 PID/进程字段。 | 原入口正常；本任务未部署 C3 修复。 |

C1 七路正式评估以及 C2/C3 gate/评估均未重启、终止或改动。C3 与 C1/C2 的差异
只构成现场对照，不能据此断言 R580 驱动版本是原因，也不能把升级作为在线修复。

## C3 原入口复验

C3 的既有入口保持为：

```text
/root/.local/bin/nvitop
-> /root/.local/share/pipx/venvs/nvitop/bin/nvitop
```

在 SSH 登录 shell 中，它解析为 `/root/.local/bin/nvitop`，版本为 `nvitop 1.7.1`。
使用以下只读命令在真实 GPU0 负载上复验：

```bash
nvitop --once --readonly --compute --only 0
nvitop --once --readonly --graphics --only 0
```

01:42:20/21 CST 的 compute 视图显示 PID `1032416`、`1032527`、`1050583`、
`1050584`，均有 `root`、数值 CPU 和命令字段；graphics 视图显示 PID `1032527`
的 graphics 行，同样有 `root`、数值 CPU 和命令字段。同窗 `nvidia-smi` 显示
GPU0 使用 `14173MiB / 24564MiB`，并列出同一组 PID；随后 `ps` 也确认这四个
PID 在该实例内存在且用户为 `root`。

清理前已精确核对本任务新增项：

```text
/root/.local/bin/nvitop-c3
-> /root/.local/share/venvs/nvitop-c3/bin/nvitop
/root/.local/share/venvs/nvitop-c3
```

两者均为 root-owned 的 task-created 对象，已删除。原 pipx link 与其 venv 未被
修改，且删除后再次确认原登录-shell `nvitop --version` 为 `nvitop 1.7.1`。

## 证据与平台支持材料

- 最小只读证据：[evidence.md](./evidence.md)
- 平台支持复现草稿（**未发送**）：[platform_support_repro.md](./platform_support_repro.md)

平台草稿请求确认是否有受支持的实例内 PID translation 或 tenant-scoped 监控入口，
并要求 compute/graphics 行给出权威 local PID 与抗 PID-reuse identity。它不请求
host `/proc`、host PID namespace、容器重建、驱动改动或服务重启。

## 清理与交付

- 已删除无部署用途的旧 probe、README、空 `candidate/` 目录、C3 disposable
  venv 以及重复 `nvitop-c3` 安装。
- Task workspace 已清空；证据和平台草稿已移入本任务的 MAM `.tasks` 目录，并以
  单独提交 `30eca5e` 保存。
- 未修改项目代码仓库；未触碰现有用户 dirty 文档。
