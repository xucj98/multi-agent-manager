# 空白使用者实操验收报告

## 结论

截至 2026-09-15 的 B 复验，文档已足以完成 5 个独立的新环境及真实 CPU 检查：B/openpi、B/RMBench、B/robot-bridge、C/RMBench、C/robot-bridge 均创建、安装并自检通过。B 的两个仓库在首次尝试时确实不存在，后续沿更新后的原文档重试成功；首次失败证据仍保留在本报告。C/openpi 的任务指定 BASE_COMMIT 在首次尝试时不在稳定仓库中，按 Manager 指示暂缓复验，等待明确的复验 base。未修改任何稳定脚本、代码、共享配置或他人环境。

执行者从 MAM 库的 `.local/README.md` 开始，仅沿其链接阅读 `.local/wuwen-11.md`、`.local/wuwen-4090.md`、存在仓库的 `AGENTS.md` 与其明确引用的 `docs/worktree_env/README.zh-CN.md`。未读取实现、安装脚本、其他 task 报告或私有 launcher。

## 结果矩阵

| 集群 / 仓库 | 创建与安装 | 文档环境检查 | 真实 CPU 功能检查 | 结果与位置 |
| --- | --- | --- | --- | --- |
| B / openpi | 通过，入口 exit 0 | 通过，exit 0 | 通过，`worktree_env_smoke.py` | `/mnt/public3/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5/openpi` |
| B / RMBench | 复验通过，入口 exit 0 | 通过 | 通过，CPU import exit 0 | `/mnt/public3/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5/RMBench` |
| B / robot-bridge | 复验通过，入口 exit 0 | 通过，exit 0 | 通过，`worktree_env_smoke.py` | `/mnt/public3/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5/robot-bridge` |
| C / openpi | 暂缓复验 | 未运行 | 未运行 | 保留首次指定 BASE_COMMIT 不可用的证据，等待 Manager 提供明确复验 base |
| C / RMBench | 通过，入口 exit 0 | 通过 | 通过，CPU import exit 0 | `/mnt/public/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5/RMBench` |
| C / robot-bridge | 通过，入口 exit 0 | 通过，exit 0 | 通过，`worktree_env_smoke.py` | `/mnt/public/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5/robot-bridge` |

所有已创建 worktree 使用 `task/bed9952b-c1a2-40ec-9f6d-34feeba91aa5`：B/openpi 为 `34002dce65962734c59725a0f6d982ae2c438a2d`；B/RMBench 与 C/RMBench 均为 `f401f5279c95451eb424ac98b831bab5552b2120`；B/robot-bridge 与 C/robot-bridge 均为 `f9626636c4776d8eb15f9c556775cb2d12c000e5`。B/openpi、B/RMBench、B/robot-bridge 和 C/RMBench 均以 `git branch --show-current` 与 `git rev-parse HEAD` 复核。

## 文档命令及证据

集群 B 的 `.local/wuwen-11.md` 和集群 C 的 `.local/wuwen-4090.md` 都给出三参数入口：

```text
bash <项目根>/<repo>/.local/create_worktree.sh BASE_COMMIT NEW_BRANCH <项目根>/workspace/TASK-ID
```

实际执行的成功创建命令如下，均以 exit 0 返回：

```text
ssh wuwen-11 'bash /mnt/public3/xcj/Projects/state-vla/openpi/.local/create_worktree.sh 34002dce65962734c59725a0f6d982ae2c438a2d task/bed9952b-c1a2-40ec-9f6d-34feeba91aa5 /mnt/public3/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5'
ssh wuwen-4090-1 'bash /mnt/public/xcj/Projects/state-vla/RMBench/.local/create_worktree.sh f401f5279c95451eb424ac98b831bab5552b2120 task/bed9952b-c1a2-40ec-9f6d-34feeba91aa5 /mnt/public/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5'
ssh wuwen-4090-1 'bash /mnt/public/xcj/Projects/state-vla/robot-bridge/.local/create_worktree.sh f9626636c4776d8eb15f9c556775cb2d12c000e5 task/bed9952b-c1a2-40ec-9f6d-34feeba91aa5 /mnt/public/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5'
```

成功入口的最小 stdout 证据：B/openpi 输出 `All installed packages are compatible`、`created openpi worktree` 和对应 source commit；C/RMBench 输出 `created RMBench worktree` 和对应 commit；C/robot-bridge 输出 `All installed packages are compatible`、`created robot-bridge worktree`。三者都将 editable source 指向各自上述任务 worktree。

环境说明中的 CPU 检查及实际结果：

```text
# B/openpi docs/worktree_env/README.zh-CN.md: “安装成功后”
ssh wuwen-11 'cd .../openpi && .venv/bin/python scripts/worktree_env_smoke.py'
# exit 0; stdout: {"numpy":"1.26.4", "openpi":".../workspace/.../openpi/src/openpi/__init__.py", "openpi_client":".../workspace/.../openpi/packages/openpi-client/src/openpi_client/__init__.py", ...}

# C/RMBench docs/worktree_env/README.zh-CN.md: “CPU 基础检查”
ssh wuwen-4090-1 'cd .../RMBench && .venv/bin/python -c '\''import curobo, pytorch3d, sapien.core; print("simulator imports ok")'\'''
# exit 0; stdout: simulator imports ok
# stderr: SAPIEN reported a Vulkan ICD warning during import, then the command completed successfully.

# C/robot-bridge docs/worktree_env/README.zh-CN.md: “安装成功后”
ssh wuwen-4090-1 'cd .../robot-bridge && .venv/bin/python scripts/worktree_env_smoke.py'
# exit 0; stdout includes "robot_bridge":".../workspace/.../robot-bridge/robot_bridge/__init__.py" plus cv2, mcap, msgpack, scipy and transport dependencies.
```

RMBench 的 CPU import 曾在共享盘页读取 (`wait_on_page_bit_common`) 等待约数分钟，随后正常返回；这不是 GPU 运行。未执行其文档保留给已分配设备的 GPU/render 检查：

```text
CUDA_VISIBLE_DEVICES=<assigned> .venv/bin/python script/worktree_env_smoke.py
```

## 首次失败、缺失信息与分类

### B / RMBench、robot-bridge：文档路径与实际稳定根不一致

文档位置：`.local/wuwen-11.md` 的“使用库前阅读 `<项目根>/<repo>/AGENTS.md`”及随后三参数入口；该文档定义 B 项目根为 `/mnt/public3/xcj/Projects/state-vla`。

按说明首先读取以下入口，原输出为：

```text
sed -n '1,360p' /mnt/public3/xcj/Projects/state-vla/RMBench/AGENTS.md
sed: can't read /mnt/public3/xcj/Projects/state-vla/RMBench/AGENTS.md: No such file or directory

sed -n '1,360p' /mnt/public3/xcj/Projects/state-vla/robot-bridge/AGENTS.md
sed: can't read /mnt/public3/xcj/Projects/state-vla/robot-bridge/AGENTS.md: No such file or directory
```

随后只读目录检查确认两个仓库目录均 `absent`，而 `openpi` 为 `present`。这是该两分支的首次失败；没有 repo 就不能遵守“先读 AGENTS.md”或调用其中的安装入口。需要补充的信息是 B 上 RMBench 和 robot-bridge 的正确稳定仓库位置，或将它们同步到文档所声明的根；现有 B 文档没有恢复办法。分类：文档/部署路径缺失。

### C / openpi：任务指定 base object 缺失

文档位置：`.local/wuwen-4090.md` 的三参数入口；`openpi/docs/worktree_env/README.zh-CN.md` 说明 `BASE_COMMIT` 同时选择源码与受管安装逻辑，早于入口合约会被拒绝。

按说明执行的原命令与完整失败输出：

```text
ssh wuwen-4090-1 'bash /mnt/public/xcj/Projects/state-vla/openpi/.local/create_worktree.sh 34002dce65962734c59725a0f6d982ae2c438a2d task/bed9952b-c1a2-40ec-9f6d-34feeba91aa5 /mnt/public/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5'
fatal: Needed a single revision
error: BASE_COMMIT is not available in /mnt/public/xcj/Projects/state-vla/openpi: 34002dce65962734c59725a0f6d982ae2c438a2d
# exit 2
```

该入口在创建前失败，C 任务目录下 `openpi` 不存在。文档没有说明缺失 base 的获取、同步或替代提交策略；需要发布方提供可达对象或文档化恢复步骤。分类：外部 git 对象/发布输入问题（文档无恢复办法）。

## 额外步骤与边界

- `mam workspace add --help` 与 `mam task publish --help` 仅用于核对 MAM 子命令语法；集群创建参数、主机和根路径均由原文档给出，帮助没有补足任何安装步骤。
- 为防止把预存环境算作验收，在调用入口前只读检查了两个任务根，均为 `absent`。完成后只读检查了分支和提交。
- C1 上用于只读进程观察的 `rg` 不存在，改用 `grep`；这不参与环境创建或 CPU 检查。
- 未运行训练、rollout、评测、传输或任何 GPU 命令，未修改稳定脚本、代码、共享配置或他人环境。环境和最小输出保留在上述 task workspace，供 Manager 裁决。

## 2026-09-15 B / RMBench、robot-bridge 增量复验

Manager 通知 B 稳定仓库与文档已修复后，按原合同仅重试此前 B/RMBench、B/robot-bridge 两个失败分支；没有读取修复者的代码或报告来猜测步骤，也没有触碰 C/openpi 或已通过的三个环境。重新从本机 `.local/README.md` 沿 `.local/wuwen-11.md` 导航，读取两个现在可达仓库的 `AGENTS.md`，再读取其明确引用的 `docs/worktree_env/README.zh-CN.md`。

两个新目标目录在创建前都不存在。按 B 集群文档原三参数入口执行：

```text
ssh wuwen-11 'bash /mnt/public3/xcj/Projects/state-vla/RMBench/.local/create_worktree.sh f401f5279c95451eb424ac98b831bab5552b2120 task/bed9952b-c1a2-40ec-9f6d-34feeba91aa5 /mnt/public3/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5'
# exit 0; stdout includes: created RMBench worktree: .../workspace/.../RMBench; f401f5279c95451eb424ac98b831bab5552b2120

ssh wuwen-11 'bash /mnt/public3/xcj/Projects/state-vla/robot-bridge/.local/create_worktree.sh f9626636c4776d8eb15f9c556775cb2d12c000e5 task/bed9952b-c1a2-40ec-9f6d-34feeba91aa5 /mnt/public3/xcj/Projects/state-vla/workspace/bed9952b-c1a2-40ec-9f6d-34feeba91aa5'
# exit 0; stdout includes: All installed packages are compatible; created robot-bridge worktree: .../workspace/.../robot-bridge; editable source: .../workspace/.../robot-bridge
```

按两个环境说明的“安装后检查与实验”段落，实际运行且均 exit 0：

```text
# RMBench：CPU 基础检查
ssh wuwen-11 'cd .../RMBench && .venv/bin/python -c '\''import curobo, pytorch3d, sapien.core; print("simulator imports ok")'\'''
# stdout: simulator imports ok
# stderr: pkg_resources deprecated warning; SAPIEN Vulkan ICD warning; command仍成功完成。

# robot-bridge：CPU basic check
ssh wuwen-11 'cd .../robot-bridge && .venv/bin/python scripts/worktree_env_smoke.py'
# stdout: {"cv2":"4.11.0", ..., "robot_bridge":".../workspace/.../robot-bridge/robot_bridge/__init__.py", ...}
```

两项均未执行文档中要求已分配设备的 GPU/render smoke。最后的只读复核显示两个仓库均在 `task/bed9952b-c1a2-40ec-9f6d-34feeba91aa5`，HEAD 分别为 `f401f5279c95451eb424ac98b831bab5552b2120` 和 `f9626636c4776d8eb15f9c556775cb2d12c000e5`，`git status --porcelain` 均无输出。

此前“B / RMBench、robot-bridge：文档路径与实际稳定根不一致”一节保留原始 `No such file or directory` 输出，作为首个失败证据；本次不覆盖该事实，而是记录修复后同一文档导航与同一三参数合同已能完成复验。
