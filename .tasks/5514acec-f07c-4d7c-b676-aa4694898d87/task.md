# 目标
诊断 MAM 更新后的唯一测试失败，优先确认是环境/网络问题还是上游回归；不要修改共享生产代码。
# 背景
manager 已 git fetch origin main (351c3a3) 并成功 merge 到 project/table-1000（b366dca）。创建 .venv 后 uv pip install -e .，执行 .venv/bin/python -B -m unittest discover -s tests -v：41 tests 中40 pass，test_real_stdlib_environment_entry_and_linked_defaults 在 tests/test_task.py:539 missing_path = Path(self.add(missing)["path"]) 失败，CLI stderr 仅 environment entry failed。最初系统 python 测试缺 /usr/bin/mam，该问题已通过正确 venv 解决，不需再查。
# 操作
阅读 MAM 入口与本地说明，回报 CODEX_THREAD_ID。只读诊断可在生产 checkout 跑单测（测试生成独立 temp repo）；若需修改代码，先报告 manager 证据，再按开发验证从 main 独立 worktree 实施。定位底层 entry stderr，复现后给出最小原因和处理建议。注意其他 agent 正在发布 MAM reports，不能变更管理分支。发布本任务 report。不要派发下级 agent。
