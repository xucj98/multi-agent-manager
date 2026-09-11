# Table-1000 重规划文档交付

- 执行线程：01a08e2e-1a7d-7d90-a78a-56c2ca388b94。
- Worktree：workspace/220a4ee4-9a6b-420c-b3a9-77f106817a85/table-1000；提交：a616f47。
- 新路线：docs/roadmap.md；近期三线任务卡：docs/planning/near-term-tasks.md；旧 roadmap 已完整存档为 docs/roadmap-legacy-2026-09-11.md。
- README 与 docs 文档入口已指向新路线，并将现有 ManiSkill 实现明确为历史工程范围；既有 spec/ADR 对当前代码仍有效。
- 验证：新入口链接存在；历史 roadmap 正文与基线逐字一致；git diff --check 通过；cleanup.sh=PASS。纯文档任务，未运行 pytest/GPU。
- 未决：下周二确认人员、场景/人评安排及 SimFoundry pilot 资源/许可证；建议 manager 发起独立 review 后集成。
