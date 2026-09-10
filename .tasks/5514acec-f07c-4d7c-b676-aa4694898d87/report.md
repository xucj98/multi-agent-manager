# 环境入口测试诊断与修复验证

## 结论

`test_real_stdlib_environment_entry_and_linked_defaults` 的直接根因是本机缺少 MAM 环境入口硬编码的真实 CPython 3.10.19；不是网络或 `pip` 安装失败，也不是本次合并 `origin/main` 的代码回归。

`scripts/local_create_worktree.sh` 指定：

```text
/mnt/public/xcj/cache/shared-python/cpython-3.10.19-linux-x86_64-gnu/bin/python3.10
```

诊断时 `/mnt/public/xcj/cache` 不存在。该入口从 base commit 读取 `scripts/create_worktree.sh`；脚本在创建 worktree 或执行 `pip` 前检查该路径是否可执行，失败即静默 `exit 2`。因此 MAM 只能包装为 `environment entry failed`。

`351c3a3` 仅修改安装文档，且其中两份入口脚本与当前工作树的 SHA-256 一致；硬编码路径和测试均已在它的祖先提交中存在。故本次失败是该机器的共享解释器环境未准备好，而非 merge 引入的上游行为变化。

## 环境修复

按已发布授权执行：

```bash
uv python install 3.10.19 --install-dir /mnt/public/xcj/cache/shared-python
```

结果路径为上述精确路径。已用 `stat` 确认 `bin/python3.10` 是常规可执行文件（非软链接），并确认版本为 CPython 3.10.19。

未修改 MAM 源码、测试或管理分支；没有代码交付 commit。只读诊断直接在生产 checkout 执行，相关测试自行创建隔离的临时 Git 仓库，因此未创建本任务的代码 worktree。

## 验证

```bash
.venv/bin/python -B -m unittest discover -s tests -v
```

结果：`Ran 41 tests in 42.424s`，`OK`。原先失败的 `test_real_stdlib_environment_entry_and_linked_defaults` 已通过。

建议保留该共享解释器目录作为本集群 MAM 的前置环境；若未来需要提升可诊断性，可单独改进入口脚本，在解释器缺失时输出明确路径，但本任务未做代码修改。
