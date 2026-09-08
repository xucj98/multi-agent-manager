# MAM 三组命令与文档空白 review

独立只读验收，使用自己的 MAM worktree 和环境；不修改实现、文档、全局安装或其他任务，不使用 GPU。任务 UUID 与 workspace 路径由 CLI 登记提供。

## 固定依据

- 源任务：cb5e5ca6-1562-4355-b815-891b479eab8c，要求版本 d6afa84cfe80604733fb5d22b6a74e2a120b28f1，简报版本 db9aa792377fbeb0dba1db7540f05aebcf353d86；用 `mam task show` 的 `--revision`、`--file` 读取。
- 代码：fa79410c72469974f6462f12adf2467eb9b5b744。
- 最终 AGENTS/README：d8a251d592512e76028f4d3fe6b1b435b916a04e（包含 7f374ff 的按需阅读整理，并补齐启动时 status 查询工作区、show 查询发布要求）；安装与设计说明延续 043861a 的内容。

## 验收

1. 原代码验收已完成：独立环境完整 22 项测试、顶层 task/job/workspace、原参数与 --root 语义、旧嵌套入口拒绝、从 /tmp 调用私有新 mam、复用本任务已登记的 worktree。保留原结果，不重复回归。
2. 增量只读审阅最终文档。用户决定统一从 MAM 仓库启动 agent；AGENTS 应按操作给出阅读入口，详细流程在 README，参数在 CLI help，安装独立。Manager 自己的工作无需 task，task 正文不重复自己的 UUID/workspace，超过一小时的程序登记 job。核对各链接、命令、规则完整性及是否仍有歧义、重复。无需安装 skill 或跨库发现机制，不扩大代码范围。
3. 简报首行写最新任务 revision，分别列代码/最终文档版本、已有验证和增量阅读结论、具体问题及未完成项。通过稳定 `mam task publish` 发布，清理自己的临时产物，保留 clean worktree 待 Manager 归档。
