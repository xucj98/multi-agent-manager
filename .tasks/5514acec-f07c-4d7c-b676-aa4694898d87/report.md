# MAM 环境入口可迁移性修复

## 交付

- Worktree：`/mnt/public/xcj/Projects/table-1000/workspace/5514acec-f07c-4d7c-b676-aa4694898d87/multi-agent-manager`
- 分支：`task/5514acec-f07c-4d7c-b676-aa4694898d87`
- 当前交付 commit：`fd28c23e72d49951ef508aea7d80361365598ec2`（base `351c3a3`；包含此前的可迁移性修复 `fbfdedc`）

该提交移除了版本化 local 模板中的 CPython 3.10.19 和 `/mnt/public/xcj` 路径；实际、被忽略的 `.local/create_worktree.sh` 保留部署者的解释器选择。通用脚本现在只接受绝对、可执行、可运行的 Python >=3.10，不再要求 `/mnt/public` 前缀，并为无效 workspace、branch、解释器、已有 worktree 与 `.venv` 软链接提供具体 stderr。

真实入口测试改为在临时仓库的 `.local/create_worktree.sh` 中传入测试自身解释器，并将传入路径放在 `/tmp`（显式断言其不在 `/mnt/public`）。它继续覆盖独立 venv、README 单文件链接及冲突保护、子 venv 的 `mam task status`、linked MAM root/config 与 archive 语义。新增测试确认伪解释器会得到明确的 Python >=3.10 错误且不创建 workspace。

## 文档重组

`docs/install.md` 现只说明安装、命令使用与 `.mam/env.json` 配置。新增自包含的 `docs/development.md` 说明 MAM 自身的开发 worktree、MAM 专属的 Python >=3.10 选择、editable/PEP 517 `flit_core` 前提、测试与 review/合并流程；它明确这些要求不属于 MAM 管理的其他仓库。README 的“开发验证”仅保留对此说明的一句引用，AGENTS.md 已删除日常 agent 的 MAM 开发指引。

本次文档提交未运行测试，也没有执行 uv 或 pip；已检查 Markdown 围栏、相对文档目标与 `git diff --check`。

## 修正后的诊断结论

最初的失败直接由版本化 `scripts/local_create_worktree.sh` 对单一主机路径的硬编码造成。临时执行 `uv python install 3.10.19 --install-dir /mnt/public/xcj/cache/shared-python` 后的 41/41 通过，只是恢复了旧 wuwen-2 风格环境，不能证明 MAM 已具可迁移性；该真实解释器仍可作为本机 `.local` 配置，而不是 MAM 的全局前置条件。

`pyproject.toml` 的真实要求是 `requires-python = ">=3.10"`。此前通用脚本还把解释器限制为 `/mnt/public/*`，与此要求和 `.local` 的部署边界不一致。`351c3a3` 仅修改安装文档，不是该耦合的引入者。

清洁 `$HOME` 与禁用 pip cache 后，真实入口测试仍通过，故不依赖当前用户目录；加入 `PIP_NO_INDEX=1` 后，它和 `test_regular_install_runs_without_source_or_git_cwd` 都因 PEP 517 build isolation 找不到 `flit_core>=3.11,<5` 而失败。这是已在文档记录的打包集成前提。

## 验证

```bash
bash -n scripts/create_worktree.sh scripts/local_create_worktree.sh
git diff --check
.venv/bin/python -B -m unittest discover -s tests -v
```

结果：完整测试 `Ran 42 tests in 64.079s`，`OK`。针对真实入口和非 Python 诊断的两项测试也单独通过；未配置的版本化 local 模板会明确提示在 `.local/create_worktree.sh` 或 `MAM_SHARED_PYTHON` 中选择 Python，且不会创建 workspace。

上述测试结果适用于此前的代码提交；本次文档重组只进行了文档检查。
