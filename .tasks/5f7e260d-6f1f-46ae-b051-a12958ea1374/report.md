# robot-bridge 本地环境与结果入口

已在独立 worktree `/mnt/public/xcj/Projects/workspace/5f7e260d-6f1f-46ae-b051-a12958ea1374/robot-bridge`（基线 `ae8829658644450181e6201bdef16fea2bf4daef`）完成并提交 tracked 修改：`1e5f3aca04359420842338349708f2631e910e55` (`fix worktree result ownership`)。安装器现在只共享 `logs`，不再创建或链接 `eval_result`；环境说明改为面向使用者地说明结果由实际评测器写入其指定位置，创建 worktree 不提供或迁移结果目录。没有新增选项、环境管理器或结果元数据。

稳定忽略入口 `/mnt/public/xcj/Projects/robot-bridge/.local/create_worktree.sh` 已原子更新。其三参数接口 `BASE_COMMIT NEW_BRANCH WORKSPACE_ROOT` 和按基线取受管脚本的行为保持不变；它会把旧版 `(logs eval_result)` 或新版 `(logs)` 的共享项声明规范为仅 `logs`，再执行，因此历史基线也不会重建稳定 `eval_result` 或 worktree 链接。实际历史基线与规范化脚本流均通过 CPU 门禁、shell 语法和参数传递检查；未创建额外未登记 worktree。

替换前本机和 `wuwen-1` 的只读 `/proc` 检查均未发现稳定 `.venv` 的直接依赖（检查 cwd、exe、root、fd、cmdline、environment、maps、mountinfo，且排除扫描器及祖先进程），未停止任何进程。稳定环境现为 `/mnt/public/xcj/Projects/robot-bridge/.venv`，`/root` 别名仍指向同一目录；`bin/python` realpath 为 shared CPython `3.11.14`：`/mnt/public/xcj/cache/shared-python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11`。以同目录可回滚备份重建，使用冻结锁、dev extra、uv cache 和 hardlink 模式；从 3.13.13 切换完成，创建 0.038s、sync 0.577s、完整事务 4.261s，备份已删除。锁文件 SHA-256 为 `d0b8ab334df0387d2d53dcf7c6acc29a48252b733b0d6c187e46e19136180b58`。

验证通过：`uv lock --check`、稳定和独立 worktree 的 `uv pip check`（74 packages）、稳定和独立 worktree 的 CPU `scripts/worktree_env_smoke.py`、editable 源路径/解释器 realpath、以及 cache-to-venv hardlink probe。未运行 GPU、机器人或评测服务。

最终清理完成：本任务 worktree 的旧 `eval_result` 链接已删除，回滚备份和入口门禁临时目录均不存在。最终检查时稳定 `eval_result` 为空目录，已用 `rmdir` 移除；`/mnt/public/xcj/Projects/robot-bridge/eval_result` 和 `/root/Projects/robot-bridge/eval_result` 均不存在。另有两个现存 worktree 的旧链接按用户要求保持未触碰，未删除任何结果文件。稳定源中既有未跟踪文件 `docs/design/low-dimensional-memory-design-space.zh-CN.md` 保持不变。没有远端写入、推送或其他活跃树改动；此前环境范围无 blocker。

## 最终文档、夹具修复与 CPU 测试

文档 refinement 已单独提交为 `8b1ba04e61b51051b9d418e8af4b6ffbffbcfaa4` (`docs: simplify worktree environment guide`)。`docs/worktree_env/README.zh-CN.md` 现只保留三参数创建命令、参数含义、worktree/.venv 位置、CPU smoke 命令和开发指南链接；已移除共享实体表、稳定源提取、路径检查以及结果目录等维护实现说明。

先完成基线等价验证：在修复前，`RMBenchSimulationController`、目标测试和 `pyproject.toml` 的 Git blob 与 `ae8829658644450181e6201bdef16fea2bf4daef` 完全一致；目标用例复现退出码 1 的 `AttributeError`。实际构造器在未提供 `worker_trace_path` 时设置 `_trace_enabled = False`，而该测试用 `object.__new__` 绕过构造器。

已单独提交最小 test-only 修复 `f45c6a472d51365e60847cd028502395c47f1575` (`test: initialize bypassed controller trace default`)：仅在该测试夹具补入 `_trace_enabled = False`，未修改生产控制器、图像路径或原有调度断言。目标用例通过：`1 passed in 2.44s`。

按仓库约定，在独立 worktree 的 CPython 3.11.14 环境运行 `.venv/bin/python -m pytest tests/`：`542 passed, 2 skipped in 71.39s`（退出码 0；外层记录 72 秒）。未使用 GPU、真实机器人或服务。pytest cache、29 个本任务生成的 `__pycache__` 目录和临时日志已清除。按最新要求未重复环境重建或进程扫描。
