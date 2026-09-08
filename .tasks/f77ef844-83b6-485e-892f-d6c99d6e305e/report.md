task_revision: e8df35f74df2df27e3a6f2c5814fedc71031839e

# 任务管理 CLI 交付简报

已完成核心 CLI、标准库测试、agent-workflow 简易环境入口，以及本次“发布暂存区修订”。workspace：`/mnt/public/xcj/Projects/workspace/f77ef844-83b6-485e-892f-d6c99d6e305e`；唯一代码 worktree：其下 `agent-workflow`；分支：`task/f77ef844-83b6-485e-892f-d6c99d6e305e`。

完整交付 commit：`72c05473542ddb15a7c101c70e417f0bf8028d1f`。本次修复只修改 `scripts/task.py` 和 `tests/test_task.py`，基于此前交付 `5c460b1ab3a3e6c885b76560f8de234ee10a3fd6`。公共文档、其他任务及业务库未修改。

## 本次修复

`publish` 继续用临时 index 创建指定任务文件的提交，并通过比较旧 SHA 的 update-ref 更新 main。正常发布完成后，仅把本次文件的共享 index entry 更新为实际发布的 blob；`unchanged` 路径执行相同的定向同步，恢复 staged 删除或旧 blob 的异常状态。

其他文件的 staged 内容保持原样。所有工作目录草稿保持原样；发布过程中对本次文件产生的新编辑仍为未暂存草稿，不会被误发布或覆盖。修订后的约束是“保留其他文件的 index entry”，不再要求整个 index 文件字节不变。

新增回归先在旧实现上复现缺失/过期 index entry，修复后通过。测试覆盖 task/report 两种文件、删除/旧内容两类异常、unchanged 不产生新发布 commit、其他 staged 内容与草稿保留、并发发布，以及后续普通代码提交不会删除或回退已发布文件。

## 整体接口与行为

- `create --title TITLE [--review UUID]`；`bind UUID --agent ID`；`workspace add UUID --repo REPO --base COMMIT`。
- `show UUID [--file task|report] [--revision COMMIT]`；`publish UUID --file task|report`；`list [--archived|--all]`；`status UUID`。
- `archive UUID --note TEXT`；`job add UUID --note TEXT --host HOST --pid PID`；`job list [--task UUID] [--status running|stopped|archived|all] [--attention]`；`job archive JOB_UUID --note TEXT`。

统一入口为 `python scripts/task.py`，可用全局 `--root ROOT` 注入测试管理根。UUID 自动生成，linked worktree 与稳定主库使用相同状态目录。创建前记录资源意图，部分失败可查询与重试，review 固定源任务、报告和交付 commits，报告必须明确 task_revision。

统一 archive 包含取消任务：无报告、绑定、验收或合入状态 gate。全库预检保护 dirty/untracked、未知 ignored 实体和外层目录，允许独立 .venv 和 gitignored 共享软链接；移除登记 worktree 及对应任务分支，保留任务和 job 历史。进程查询以 status 为准，stopped 携带诊断仍可归档，unknown 保留上次确认状态和时间。

环境入口为 `scripts/create_worktree.sh`，三参数 wrapper 模板为 `scripts/local_create_worktree.sh`，已安装到稳定库 `.local/create_worktree.sh`；使用共享持久 CPython 3.10.19 创建私有 venv，不安装业务依赖。旧 ws 接口已删除。

## 本次验证

在上述代码 worktree 根目录执行：

```bash
python3 -B -m unittest discover -s tests -p test_task.py -k 'publish' -v
python3 -B -m unittest discover -s tests -p test_task.py -k 'parallel' -v
git diff --check
```

两项定向测试通过（随后又新增了发布期间编辑草稿的回归），空白检查通过。最终完整核心套件运行命令为：

```bash
python3 -B - <<'PY'
import sys
import unittest
sys.path.insert(0, '/mnt/public/xcj/Projects/agent-workflow/scripts')
suite = unittest.defaultTestLoader.discover('tests', pattern='test_task.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
PY
```

结果：12 项，11 项通过、1 项跳过，耗时 7.309 秒。跳过项为真实进程契约测试：运行时稳定库尚未集成并行交付的 `job_runtime.py`。发布相关三个测试及原有版本/review、多库/部分失败重试、归档安全、真实私有 venv smoke 等测试全部通过。此前已只读对接 Erdos 工作树，验证两个自建进程 running → stopped → archived，现有 App Server 查询返回 active；本次未扩展进程模块验证。

实现 582 行，核心测试 337 行。测试数据由 TemporaryDirectory 清理；本次未留下测试进程、临时文件或环境。代码工作树在提交后干净，保留待 Manager review 和归档。

## 发布与剩余事项

已通过本 worktree CLI 执行 `publish f77ef844-83b6-485e-892f-d6c99d6e305e --file task`，返回 `unchanged: true`，版本仍为 `e8df35f74df2df27e3a6f2c5814fedc71031839e`，只恢复本任务说明的 index entry。本报告随后通过同一入口发布。

本次修复无未完成项。`job_runtime.py` 的代码集成、其他任务历史报告的定向 index 同步由 Manager 负责；本分支未复制或修改该模块。部分环境恢复仍由各库本地入口负责，未知临时产物由执行者处理。任务分支归档后仅保存 SHA，不建立备份引用，成果保留与集成由 Manager 决定。
