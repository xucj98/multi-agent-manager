# 清理用户确认废弃的 RMBench pi05 虚拟环境
# Remove explicitly retired pi05 virtual environment

User explicitly authorized deleting /mnt/public/xcj/Projects/RMBench/policy/pi05/.venv (same as /root/Projects/RMBench/policy/pi05/.venv). Only this legacy environment is in scope. This is an operation on an ignored stable resource, no source-code edits or new code worktrees/environment are needed. Your previous reviewa8946c75 is archived; use this task's registered workspace if a temporary file is necessary.

Read RMBench AGENTS and relevant cleanup constraints. Verify exact target is the expected directory beneath stable RMBench, check local and wuwen-1 processes for direct references to this exact retired environment before deletion (do not dump unrelated commands/environment). If no user jobs depend on it, remove only the .venv directory without following contained symlinks; preserve checkpoints, shared Python/uv cache and adjacent files. Do not change evaluation/training code, manifests, other environments or docs; no GPU jobs. A direct active dependency is a blocker to report, not permission to stop the job.

Record target, pre-removal size if inexpensive (do not equate hardlink du with bytes freed), checks, deletion result and preserved neighbours in concise .tasks/TASK-ID/report.md; publish. Remove owned temporary files and end turn. No code commit expected. Model gpt-5.6-terra/max.
