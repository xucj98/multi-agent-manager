task_revision: 0013b2aee851a1b2fee75cd151d3bd3482a20435
完成与未完成：已完成 task list 五列单行输出、show 原生正文与 --json、status 不刷新 job、job list 先过滤后探测；无未完成项。
workspace、各库交付 commit：/mnt/public/xcj/Projects/workspace/b2646623-9cef-4e0f-8695-06baa8b930f7/multi-agent-manager @ 23288c32a37af56b20e770ae07ff4045b2448f73。
验证结果与成果位置：在该 worktree 运行 `.venv/bin/python -B -m unittest discover -s tests -v`，26 项通过；`git diff --check` 通过；新增测试使用临时 root 的 mam CLI 验收默认 list/show 与 --json。
已知行为变化：task list/show 默认改为文本，脚本应使用 --json；status 展示已保存的 job 检查结果，实时检查由 job list 执行。
