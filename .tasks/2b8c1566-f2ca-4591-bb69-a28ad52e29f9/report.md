task_revision: 0c4b89e4b933878fa8da57bee33096cb4d8fd355

# B/C 稳定入口与 OpenPI symlink smoke 修复

## 已交付

B 的稳定根 `/mnt/public3/xcj/Projects/state-vla` 已补齐独立的 `RMBench` 和 `robot-bridge` 主仓库，分别固定为 `f401f5279c95451eb424ac98b831bab5552b2120`（`frozen-f401f527`）和 `f9626636c4776d8eb15f9c556775cb2d12c000e5`（`frozen-f9626636`）。两仓库的稳定 `.local/create_worktree.sh` 可用，tracked 源树 clean。

C 的稳定 OpenPI 根 `/mnt/public/xcj/Projects/state-vla/openpi` 已可解析冻结提交 `34002dce65962734c59725a0f6d982ae2c438a2d`，并有 `frozen-34002dce` ref；三参数稳定入口可为该提交创建独立 worktree。兼容路径 `/mnt/public/xcj/Projects/RMBench` 仍指向稳定 `state-vla/RMBench`。

OpenPI 环境修复在本任务独立 worktree 中提交：

- worktree：`/mnt/public/xcj/Projects/workspace/2b8c1566-f2ca-4591-bb69-a28ad52e29f9/openpi`
- branch：`task/2b8c1566-f2ca-4591-bb69-a28ad52e29f9`
- base：`34002dce65962734c59725a0f6d982ae2c438a2d`
- delivery：`c03898f5a76f4ac208f7d23ae14e2cc759be8853` (`fix(worktree): validate symlink-mode transformer overrides`)

该提交是冻结 base 的直接子提交，没有改写 `34002dce`。它原生增加受控 `--link-mode hardlink|symlink`（默认 hardlink），并让 symlink 模式的安装器按未解析的 worktree site-packages 路径定位 transformers。安装器和 smoke 的关键路径均改为显式 `RuntimeError`，不会被 `-O` 移除。

普通 CPU smoke 现在先校验当前解释器、`sys.prefix`、`purelib`/`platlib` 和 transformers 的词法 site-packages 路径都在该 worktree venv。它允许未受管 transformers 文件链接到共享 uv cache，但会逐一校验五个受管覆盖文件：补丁源和目标没有链接逃逸、目标是常规非 symlink 文件、`st_nlink == 1`，且字节内容一致；`openpi` 与 `openpi_client` 也必须解析回该 worktree。通用说明已写入 `openpi/docs/worktree_env/README.zh-CN.md`，没有向集群入口增加优化模式或提交专属恢复命令。

## 验证

| 范围 | 结果 |
| --- | --- |
| OpenPI smoke 回归 | `.venv/bin/python -m pytest -q scripts/worktree_env_smoke_test.py`：9 passed。夹具覆盖共享 cache 中的 symlink 模块与私有补丁共存、解释器/来源逃逸、补丁源 symlink、补丁目标父目录逃逸、目标 symlink、hardlink 和内容错误。内容错误在 `python -O` 子进程中仍明确失败。 |
| OpenPI lint | `.venv/bin/python -m ruff check ...` 与 `ruff format --check ...` 均通过。 |
| 本任务 worktree 的普通 CPU 命令 | `.venv/bin/python scripts/worktree_env_smoke.py` 成功，输出该 worktree 的 Python、openpi、openpi-client 和 `numpy=1.26.4`。同一完整检查在 `-O` 下也通过；这只是鲁棒性验证，用户入口仍是普通命令。 |
| 安装器 | `bash -n scripts/worktree_env/create_worktree_env.sh` 通过；帮助文本和非法 `--link-mode` 拒绝路径已核验。 |
| B / robot-bridge | 稳定入口安装成功并输出 `copy-mode=PASS`；`scripts/worktree_env_smoke.py` 成功，editable `robot_bridge` 与基础依赖都来自任务 worktree。 |
| B / RMBench | 稳定入口安装成功并输出 `copy-mode=PASS`；文档 CPU 命令导入 `curobo`、`pytorch3d`、`sapien.core` 成功。SAPIEN 仅提示无 Vulkan ICD，未执行 GPU/render 检查。 |

为避免改动 C 的稳定或生产 worktree，仅对已有的本任务 C CPU worktree 做了不落盘的内存加载尝试。当前 C 的共享 Python 在标准库 `importlib` 导入阶段超过 55 秒，命令由 `timeout` 以 124 退出；没有 GPU、模型、数据、稳定 worktree 或残留进程被改动。因此 C 上的正式新 base smoke 和空白用户复验仍待部署后执行，不能由此尝试替代。

## 后续部署边界

C 的现有稳定入口会对 `34002dce` 提取的安装器应用 `.local/patches/openpi-uv-symlink.patch`。该外部补丁与 `c03898f` 已原生包含的 link-mode/私有补丁逻辑重叠，不能直接继续叠加到新提交；Manager 部署新 base 前应复核并移除或更新该外部补丁，然后在新的独立 C worktree 用普通命令复验。此任务没有部署 `c03898f` 到 C，也没有改动 C 稳定根、生产 worktree、B 环境、GPU、模型或数据。

此前三个预计较长的 CPU 安装/检查 job 均已核验并归档：`96d3f5cb-64ff-4a0d-8f9a-27f71eb413a7`、`1c84ec4b-be45-4f86-9328-a05cf39755b0`、`db8b6dd2-845a-45d2-8fbf-35658fa0346e`。本任务没有未归档 job。
