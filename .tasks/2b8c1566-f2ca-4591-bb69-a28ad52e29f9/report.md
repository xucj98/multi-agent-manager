task_revision: f1b0341043261ad74bfdbc3474d5bd60028ee853

# B/C 稳定入口与指定提交修复

## 交付结果

B 的稳定根 `/mnt/public3/xcj/Projects/state-vla` 已补齐独立的 `RMBench` 和 `robot-bridge` 主仓库，分别固定为 `f401f5279c95451eb424ac98b831bab5552b2120`（`frozen-f401f527`）和 `f9626636c4776d8eb15f9c556775cb2d12c000e5`（`frozen-f9626636`）。两仓库的稳定 `.local/create_worktree.sh` 均可执行，tracked 源树 clean；B 的跨设备 cache/worktree 安装使用经实际验证的 copy-mode 入口。

C 的稳定 OpenPI 根 `/mnt/public/xcj/Projects/state-vla/openpi` 已可解析指定的 `34002dce65962734c59725a0f6d982ae2c438a2d`，并有 `frozen-34002dce` ref；三参数稳定入口可创建该提交的独立 worktree。C 的兼容路径 `/mnt/public/xcj/Projects/RMBench` 仍指向稳定 `state-vla/RMBench`，未改向任务 worktree。

没有重置稳定分支、改动活跃 worktree、修改模型/数据或启动 GPU 工作。MAM 代码 worktree 为 `/mnt/public/xcj/Projects/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/multi-agent-manager`，HEAD `c8c76ca85052cae218fa2d9924e042b2db09307d`，无业务代码提交；本次交付是稳定部署前置和本地集群说明。

## CPU 环境复验

| 集群 / 仓库 | 隔离 worktree 与分支 | 验证结果 |
| --- | --- | --- |
| B / robot-bridge | `workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/cpu-robot-bridge/robot-bridge`；`task/2b8c1566-f2ca-4591-bb69-a28ad52e29f9-cpu-robot-bridge`；`f9626636…` | 稳定入口安装成功并输出 `copy-mode=PASS`；`scripts/worktree_env_smoke.py` 成功，editable `robot_bridge` 与基础依赖均来自该 worktree。 |
| B / RMBench | `workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/cpu-rmbench/RMBench`；`task/2b8c1566-f2ca-4591-bb69-a28ad52e29f9-cpu-rmbench`；`f401f527…` | 稳定入口安装成功并输出 `copy-mode=PASS`；文档 CPU 命令 `import curobo, pytorch3d, sapien.core` 输出 `simulator imports ok`。SAPIEN 仅提示当前无 Vulkan ICD，未执行 GPU/render 检查。 |
| C / openpi | `workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/cpu-openpi/openpi`；`task/2b8c1566-f2ca-4591-bb69-a28ad52e29f9-cpu-openpi`；`34002dce…` | 入口安装完成：242 packages 一致性检查通过、`uv_symlink=PASS`、editable source 正确。旧源码的未优化 smoke 在其 `Path.resolve()` 路径断言处失败，因为 C 软链接模式会把 package 实体解析到共享 cache；同一脚本用恢复命令完成并输出 worktree 内 `openpi`/`openpi_client` 路径及 `numpy=1.26.4`。 |

C 的恢复命令已写入本机集群入口 `.local/wuwen-4090.md`，SHA-256 为 `a4b6a1c75d3d11ab890d25dc7662f6768b21c115fec764c2a029b4ed8092241d`：

```text
PYTHONOPTIMIZE=1 .venv/bin/python scripts/worktree_env_smoke.py
```

它只适用于上述冻结 OpenPI 提交在 C 的共享 uv cache 软链接布局；保留精确源码提交，不以其他提交替代，也不使用 GPU。C 的原始失败与成功输出分别保留为 `cpu-openpi-install-and-smoke.log`、`cpu-openpi-optimized-smoke-continued.log`。这不是依赖缺失：入口已完成 package consistency、私有 transformers patch 及 symlink 证据检查。

## 复验入口

```text
# B
ssh wuwen-11 'bash /mnt/public3/xcj/Projects/state-vla/RMBench/.local/create_worktree.sh f401f5279c95451eb424ac98b831bab5552b2120 task/<TASK-ID> /mnt/public3/xcj/Projects/state-vla/workspace/<TASK-ID>'
ssh wuwen-11 'bash /mnt/public3/xcj/Projects/state-vla/robot-bridge/.local/create_worktree.sh f9626636c4776d8eb15f9c556775cb2d12c000e5 task/<TASK-ID> /mnt/public3/xcj/Projects/state-vla/workspace/<TASK-ID>'

# C
ssh wuwen-4090-1 'bash /mnt/public/xcj/Projects/state-vla/openpi/.local/create_worktree.sh 34002dce65962734c59725a0f6d982ae2c438a2d task/<TASK-ID> /mnt/public/xcj/Projects/state-vla/workspace/<TASK-ID>'
```

B 的两份安装/CPU 日志位于 `/mnt/public3/xcj/Projects/state-vla/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/`；C 的证据位于对应 `/mnt/public/xcj/Projects/state-vla/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/`。三个 worktree 均已复核为指定 HEAD 且 tracked clean。

耗时超过预期的三个 CPU 安装/检查均已登记、核验并归档：`96d3f5cb-64ff-4a0d-8f9a-27f71eb413a7`、`1c84ec4b-be45-4f86-9328-a05cf39755b0`、`db8b6dd2-845a-45d2-8fbf-35658fa0346e`。没有仍在运行的本任务 job。
