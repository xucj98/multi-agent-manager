# MAM Python 可迁移性修复独立审查

## 结论

通过。对源任务交付 commit `fbfdedcebfeb78046ec2b15902dc54ed2b43a52b`（base `351c3a3e6dc807cae280a99d5f3c824f8d5750ff`）未发现可复现、有影响的缺陷；没有修改实施或合并分支。

## 审查证据

- `scripts/create_worktree.sh` 已不含 `/mnt/public` 或 `3.10.19` 约束：它接受绝对、可执行且可运行的 Python，并按 `pyproject.toml` 的真实下限验证 Python >=3.10。无效 workspace、branch、解释器、已有 worktree 和 `.venv` 软链接都有明确 stderr；解释器诊断发生在创建 workspace 前。
- 版本化 local 模板不再固化站点解释器。将其复制到全新的临时 Git 项目的被忽略 `.local/create_worktree.sh` 后，以 `MAM_SHARED_PYTHON=/tmp/.../python`（不在 `/mnt/public`）实际执行成功：创建 task worktree、独立 `.venv`，并成功运行新环境的 `mam task list`。临时 fixture 已清理。
- 未设置 `MAM_SHARED_PYTHON` 时，模板以退出码 2 报出 `configure a local Python >=3.10 in .local/create_worktree.sh or MAM_SHARED_PYTHON`，且目标 workspace 不存在。
- `test_real_stdlib_environment_entry_and_linked_defaults` 仍覆盖独立环境入口、单文件 `.local/README.md` 链接、冲突保护、linked MAM root/config 与 archive 语义；测试解释器通过 `/tmp` 路径传入。新增非 Python 诊断测试确认退出码 2 且不创建 workspace。

## 验证

```text
bash -n scripts/create_worktree.sh scripts/local_create_worktree.sh
git diff --check 351c3a3..fbfdedc
.venv/bin/python -B -m unittest discover -s tests -v
```

前两项通过；完整单测结果为 `Ran 42 tests in 65.254s`、`OK`。

## 审查 workspace

- `/mnt/public/xcj/Projects/table-1000/workspace/b1df7da1-8f3a-453c-97da-a58cec90b93f/multi-agent-manager`
- 分支：`task/b1df7da1-8f3a-453c-97da-a58cec90b93f`
- 无实施改动。

## 用户文档拆分增量审查

通过。只读审查了 `fbfdedcebfeb78046ec2b15902dc54ed2b43a52b..fd28c23e72d49951ef508aea7d80361365598ec2`（包含 manager 澄清 commit `798bb012dfe578e45f58f04eb89a1d7889970a2b`），未发现信息丢失、范围混淆或失效链接。

- `docs/install.md` 现在只保留安装、PATH 与项目 `.mam/env.json` 配置；MAM 自身的解释器、editable 安装、构建后端前提、验证和合并流程都已迁入 `docs/development.md`。
- `docs/development.md` 明确只适用于 MAM 自身，保留从 `main` 建立独立 worktree、Python >=3.10、被忽略的 local 配置、`flit_core` 前提、完整单测和独立 review/合并语义；不会把这些要求错误施加给被管理仓库。
- `README.md` 的“开发验证”仅保留到开发说明的一句引用；`AGENTS.md` 最后的开发指引已按要求删除。`README -> docs/development.md`、`docs/development.md -> ../README.md` 和 `install.md` 的相对目标均存在，相关标题与锚点一致。
- 执行了 `git diff --check` 和 Git 对链接目标文件的静态存在性检查；这是纯文档增量，按要求没有运行安装或测试。
