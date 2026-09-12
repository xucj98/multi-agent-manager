# Windows App subagent 可见性实验

## 目标

验证用户能否在 Windows App 中看到当前对话创建的 subagent 及其回报。

## 执行要求

1. 阅读仓库根目录的 `AGENTS.md`。
2. 使用 `mam task show 2400a341-5cd7-47f5-867c-e06853e21c8b` 查看已发布任务。
3. 不修改任何项目文件，不启动长进程。
4. 向 manager 回报一句：`SUBAGENT_VISIBLE_TEST_OK`，并注明自己已成功启动。

## 交付与验收

在 `report.md` 写入简短结果并发布；manager 能收到上述识别文本即通过。
