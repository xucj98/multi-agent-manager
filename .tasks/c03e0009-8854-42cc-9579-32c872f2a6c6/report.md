# OpenPI symlink transformers 覆盖定向复核

结论：**PASS**。新提交 `5f6ca06436c7b33905b442c769c7800d3f4a17e2` 已修复前次报告的优化模式问题。本轮仅复核其相对 `958eeaedc4c841e2f1b31c51572ddecc449ba5cb` 的两文件增量，未发现本范围内待修问题。

## 修复与验证

安装器的两处路径边界，以及 smoke 的 venv 路径、内容、非 symlink 和私有 inode 检查，均改为显式条件与 RuntimeError，不再受 Python 优化模式移除 assert 的影响。临时文件加 os.replace 的覆盖方式保持不变。

直接提取新提交安装器的 Python heredoc 和 smoke 的 transformers 核心代码执行；本机 CPython 3.13.9、独立临时文件级 symlink/hardlink fixture，普通模式与同时设置 PYTHONOPTIMIZE=1、python -O 的模式各运行以下 7 项，**14/14 PASS**：

- 正常 symlink 覆盖：5 个目标内容正确、非 symlink、st_nlink=1，smoke 核心通过。
- 正常 hardlink 覆盖：5 个目标内容正确、非 symlink、st_nlink=1，smoke 核心通过。
- models 目录链接到 cache：安装器拒绝越界。
- transformers 位于 venv 外：安装器与 smoke 核心均拒绝。
- 覆盖内容错误：smoke 核心拒绝。
- 内容完全相同但仍为 symlink：smoke 核心拒绝，独立验证新增非 symlink 检查有效。
- 内容正确但 inode 被另一硬链接共享：smoke 核心拒绝。

每项均核对 fixture cache 的 5 个原文件及 __init__.py 字节、inode 保持不变。git diff --check 与 bash -n 通过。本轮没有重复 uv 安装或完整依赖 smoke；真实 uv 布局证据沿用上一轮。

## 交付与范围

- 复用并快进审阅树：`/mnt/public/xcj/Projects/workspace/c03e0009-8854-42cc-9579-32c872f2a6c6/openpi`
- HEAD：`5f6ca06436c7b33905b442c769c7800d3f4a17e2`
- 分支：`task/c03e0009-8854-42cc-9579-32c872f2a6c6`
- 无业务代码修改，无新增代码 commit。审阅树保留供 Manager 验收归档。
- 本轮 TemporaryDirectory fixture/cache 已自动删除并检查不存在；使用 -B 禁止生成 bytecode。
- 未访问 C、未做远端写入或 GPU 测试；不宣称三机 smoke/C100 或完整环境已验收。
- 前次问题报告 revision：`2ce3e0b49c29b50fdad60c4cca65fa1ec4835872`；其中 -O 问题现已关闭。
