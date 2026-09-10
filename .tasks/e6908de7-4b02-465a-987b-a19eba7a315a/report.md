task_revision: 91a1667e8585e473d4e6df9009c06b509e4973a4

12:11 文档修正已完成：

- RMBench 文档 commit：f414eda7cfc9fb18fa3ccdfd902accdb9908b2e6。仅修改 experiments/memory_chunk_20260910/README_memory_schema.zh-CN.md；入口和配置保持已验收的 7378904 实现。
- 按训练 owner 已发布 report 1df8b8255d6967eb9858c3d3365ce06a65eb1f3c，将新 20k checkpoint 根改为 /mnt/public/xcj/Projects/openpi/checkpoints，修正 put-back exp_name 中误加的 block，补齐 rearrange full seed0/1/2、put-back seed0/1。旧 drawer 仍引用原 RMBench checkpoint 目录。
- 技术、正式与 drawer 模板采用本任务实际 worktree 解释器、具体 checkpoint 路径及 GPU0；删除 CHECKPOINT、$PWD、继承式 PYTHONPATH 和端口/GPU 占位符。去掉临时授权/旧 review 状态及冗余准备说明，保留必要 prepare-audit、checkpoint 自身 smoke→formal、只读 checkpoint、metadata 继承与清理规则。

验证：

- 只提取现有 CLI 的 argparse 声明核对文档中的 8 条命令；3 个 bash 块通过 bash -n，未调用模型或运行入口。
- 表格展开后的 12 个输出路径与训练 report 一致，实际 exp_name 父目录均存在；本次核对时 20000 尚未生成，README 明确保存完成后才能执行。
- 实际解释器、保留的两个 50-step 路径、旧 drawer 两模型路径、原始数据路径和 manifest 均存在；git diff --check 通过。
- 本轮没有启动 CPU 模型、GPU 程序或 MAM job，没有搬移 checkpoint、添加软链接或重建环境。

复用工作区：/mnt/public/xcj/Projects/workspace/e6908de7-4b02-465a-987b-a19eba7a315a

- RMBench：上述工作区 /RMBench，f414eda7cfc9fb18fa3ccdfd902accdb9908b2e6。
- robot-bridge：上述工作区 /robot-bridge，8ea6078543a875b5ae223df16891cdc1fe975c66。
- openpi：上述工作区 /openpi，a869498f01a246752d7e5c6ed5ccd5dfdd9b3ff4。

文档交付完成；GPU 技术 sim 与 drawer offline 等 Manager 在 F0 row1 完成后另行安排。
