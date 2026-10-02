# install.sh

本文描述系统程序安装与升级。操作步骤见[安装说明](../install.md)，发版与验收要求见[开发指南](../development.md#版本与发版)。

## 接口

```text
install.sh [--version VERSION]
```

同一入口负责系统 `mam` 的首次安装和升级，作用于共用该安装的所有实例。默认使用最新正式发布版本，`--version` 指定目标版本。

安装独立于源码 checkout 和实例配置，新实例在安装后 clone 对应的发布版本。

## 指定版本

`VERSION` 为发布版本号，例如 `0.2.3`。需要固定安装或升级的目标版本时，在 Bash 中执行：

```bash
set -o pipefail
curl -fsSL "https://raw.githubusercontent.com/xucj98/multi-agent-manager/main/scripts/install.sh" \
  | bash -s -- --version 0.2.3
echo $?
```

`set -o pipefail` 使下载失败也反映在整条命令的退出码中；最后一行显示本次命令的退出码。不指定版本时使用最新正式发布版本，命令见[安装说明](../install.md#安装)。

## 安装与测试

脚本下载选定版本的源码发布包并解压，运行必要的包和关键文件 smoke，通过 pipx 安装或更新 `mam`，再调用 `mam-codex-check` 完成分层兼容性验收。版本、提交、阶段耗时、测试摘要和原始证据会保留在用户数据目录；临时工作目录仍在结束时清理。完整的旧版升级场景在[发版集成测试](../development.md#发版集成测试)中验收。

## 结果与重试

成功时输出安装版本和测试摘要，退出码为 `0`；失败时输出失败环节与原因，退出码非 `0`。安装后可用 `mam --version` 查看当前程序版本。

失败后按报错处理，再运行同一安装命令。若程序已更新、后续兼容性或投递测试失败，保持各实例的 daemon 停止，修复后重试；安装通过后继续实例升级。

## 与实例升级的衔接

更新系统程序前，暂停 agent、结束现有 MAM 命令，并停止共用该安装的所有 daemon。程序更新后，通过 [mam service upgrade](service.md#实例升级) 分别升级各实例，再按需启动。
