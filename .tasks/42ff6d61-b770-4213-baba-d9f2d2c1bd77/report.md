# uv symlink 独立环境实测

## 结论

`uv --link-mode symlink` 在本机可作为 yrfs 不能跨目录 hardlink/reflink 时的空间替代：每个 worktree 保持自己的 venv，A 中升级或卸载第三方包不会影响 B；已缓存的包文件只保留一份，第二个环境安装显著更快、更省空间。

但它不是自包含环境：venv 内的第三方文件逐个以**绝对 symlink**指向 cache。cache 必须被当作稳定、持久的包仓库；删除、迁移或不可访问都会损坏所有引用它的环境。故适合用户现已决定的 canonical `/mnt/public/xcj/cache/uv`，前提是路径稳定、所有运行节点可见，并禁止把它当作可随意清理的临时缓存。

## 实测范围与结果

- 环境：`uv 0.12.5`、Python `3.12.3`；全部操作位于本任务独立目录，使用 `UV_CACHE_DIR=.../uv-symlink-study/cache-run2`，未读写 canonical cache 或业务 venv。
- 建立两个真实 venv，分别以 `uv pip install --link-mode symlink idna==3.7` 安装。
  - A（冷 cache）总耗时 `963 ms`；B（已热 cache）`175 ms`。
  - 每个 venv 的表观增量均为 `2,977 B`；共享的 cache 中 `idna` 目标树为 `303,984 B`，`core.py` 的每个 venv link 字符串仅 `151 B`。
  - cache 从 `340,414 B`（A 后）到 `342,643 B`（B 后），B 只增加索引/元数据约 `2,229 B`，未复制包内容。
  - uv 0.12.5 的实现是**文件级** symlink，不是整个 `idna/` 目录 link：A 与 B 的 `site-packages/idna/core.py` 都指向同一 `cache-run2/archive-v0/.../idna/core.py`。
- A 升级到 `idna==3.10`（`617 ms`），B 仍为 `3.7`，且 B 的 `3.7` cache 目标仍存在；随后从 A 卸载 `idna`，B 仍为 `3.7`，`uv pip check` 通过。由此确认版本升级、卸载的文件系统效果限定在目标 venv，不会删除其他 venv 使用的 cache 版本。
- Editable 验证：A、B 安装同名同版本 `editable-probe==0.1.0`，但源目录各自为 `editable-a/src` 与 `editable-b/src`。初始导入分别返回 `editable-a` / `editable-b` 且 `__file__` 分别在各自源码路径。仅修改隔离测试夹具 A 的源码后，A 返回 `editable-a-mutated`，B 仍为 `editable-b`；未修改第三方包或 cache 内容。
  - 需要注意：symlink 模式下 editable 的 `__editable__.editable_probe-0.1.0.pth` 也是指向 cache 的 symlink，但两份 PTH 内容分别指向 A/B 的专有源码。因此源码所有权隔离成立，但 editable 元数据仍会依赖 cache。

## cache 生命周期边界

- 受控实验 cache 执行 `uv cache clean idna`，普通命令成功删除 `33` 个文件（`672.5 KiB`）；B 的 `idna/core.py` 目标消失，随后 `from idna import encode` 以 `ImportError` 失败。单纯 `import idna` 会退化为一个空 namespace 而返回成功，故健康检查要调用实际 API，不能只检查 import 返回码。
- 另做独立 prune probe：普通 `uv cache prune` 输出 `No unused entries found`，目标仍在、功能调用成功；`uv cache prune --ci` 删除 `16` 个文件（`310.2 KiB`），目标消失且同一调用失败。
- 官方明确警告 `symlink` 与 cache/环境强耦合，`uv cache clean` 会破坏已安装包；官方当前文档将普通 `uv cache prune` 说明为可周期运行，但 `--ci` 会移除预构建 wheel 和解压内容。对于本项目追求的长期可用独立 venv，建议安装/清理脚本一律不执行 `cache clean`、按包 `cache clean`、`cache prune --ci` 或手工删除 canonical cache；若未来要采用普通 prune，应仅由管理员在版本确认和环境健康检查后受控执行。

参考：[uv link-mode settings](https://docs.astral.sh/uv/reference/settings/#link-mode)、[uv cache](https://docs.astral.sh/uv/concepts/cache/)、[uv CLI](https://docs.astral.sh/uv/reference/cli/)。

## 建议的最小脚本改动

1. 第三方依赖安装/同步阶段显式使用 `--link-mode symlink`（或等价的 `UV_LINK_MODE=symlink`）并固定 `UV_CACHE_DIR=/mnt/public/xcj/cache/uv`；venv 路径仍保持每个 worktree 独立，绝不共享或 symlink 整个 venv。
2. 本地 editable 项目单独以其自身 worktree 安装，例如 `uv pip install --no-deps --link-mode copy --editable "$WORKTREE"`。这样仅本地 editable 元数据采用 copy，避免它也成为 cache symlink；第三方大包仍从 shared cache symlink，空间收益不变。
3. 给 cache 加运行约定：不移动其绝对路径，不执行上述清理命令，不手删其中内容；cache 不可用时把所有依赖 venv 视为需要重建，而不是可正常运行的独立环境。

## 交付与验证材料

- workspace：`/mnt/public/xcj/Projects/table-1000/workspace/42ff6d61-b770-4213-baba-d9f2d2c1bd77`；本任务不改业务仓库，因此无 worktree/commit。
- 简短证据摘要保留在 workspace 的 `SYMLINK_EVIDENCE.md`；临时 venv、cache、脚本和完整日志已在发布后清理，避免占用共享空间。
- 验证已执行：两个 venv 的 install/upgrade/uninstall、`uv pip check`、两个独立 editable 导入及 A 源变更、按包 clean、普通 prune 与 `prune --ci` 的功能 API 检查。
