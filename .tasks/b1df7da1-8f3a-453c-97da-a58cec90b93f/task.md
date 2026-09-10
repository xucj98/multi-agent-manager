# 独立review要求
审查源任务已发布commit fbfdedcebfeb78046ec2b15902dc54ed2b43a52b 相对base351c3a3的最小可迁移性修复。先回报CODEX_THREAD_ID，阅读MAM规范，mam workspace add本TASK --repo multi-agent-manager --base fbfdedce... 创建独立review worktree。检查通用脚本是否真正摆脱站点路径/Python3.10.19依赖，local模板实际部署可用，错误和失败副作用合理，测试保留独立venv/README链接/linked MAM状态语义。验证必要针对性或完整测试，不重复无关测试。只给可复现有影响的问题和级别，不做风格扩scope。禁止修改实施或合并分支；发布report。不要派发agent。

# 独立 review MAM worktree Python 可迁移性修复

Review source delivery (source TASK-ID: 5514acec-f07c-4d7c-b676-aa4694898d87):
{
  "task": "5514acec-f07c-4d7c-b676-aa4694898d87",
  "commits": {
    "multi-agent-manager": "fbfdedcebfeb78046ec2b15902dc54ed2b43a52b"
  }
}

Source task requirements:

# 目标
诊断 MAM 更新后的唯一测试失败，优先确认是环境/网络问题还是上游回归；不要修改共享生产代码。
# 背景
manager 已 git fetch origin main (351c3a3) 并成功 merge 到 project/table-1000（b366dca）。创建 .venv 后 uv pip install -e .，执行 .venv/bin/python -B -m unittest discover -s tests -v：41 tests 中40 pass，test_real_stdlib_environment_entry_and_linked_defaults 在 tests/test_task.py:539 missing_path = Path(self.add(missing)["path"]) 失败，CLI stderr 仅 environment entry failed。最初系统 python 测试缺 /usr/bin/mam，该问题已通过正确 venv 解决，不需再查。
# 操作
阅读 MAM 入口与本地说明，回报 CODEX_THREAD_ID。只读诊断可在生产 checkout 跑单测（测试生成独立 temp repo）；若需修改代码，先报告 manager 证据，再按开发验证从 main 独立 worktree 实施。定位底层 entry stderr，复现后给出最小原因和处理建议。注意其他 agent 正在发布 MAM reports，不能变更管理分支。发布本任务 report。不要派发下级 agent。

# 裁决与环境修复授权
已定位该机缺少 scripts/local_create_worktree.sh 指定的真实 Python 3.10.19。优先用 uv python install 3.10.19 --install-dir /mnt/public/xcj/cache/shared-python 安装真实解释器满足既有路径，不修改上游脚本、不伪造版本软链。完成后以 MAM .venv/bin/python -B -m unittest discover -s tests -v 验证全部测试，发布根因、环境修复及结果。若发现其他代价或根因，报告 manager。

# 用户最新要求：分析 MAM 可迁移性，不能为不合理测试迎合旧机配置
用户质疑为何需要3.10.19，并指出MAM仅在wuwen-2验证过，其他环境考虑可能不足。请继续原任务做针对性分析：区分 pyproject Python>=3.10 的真实要求、本机 .local 配置和被版本化脚本/测试不合理固化的约束；核查硬编码 Python路径、/mnt/public前缀、测试是否依赖网络/主机用户目录、错误输出是否足够。给 manager 一个最小修复方案和真实应保留的测试语义，避免过度跨平台抽象。此前装Python只是复现证明，不应作为可迁移性的修复结论。
先提交分析/方案给manager，不直接改共享源码。若后续实施需独立MAM worktree，从同步后的main创建，按开发验证合并main再带入project分支。保留之前事实，报告结论需修正为测试通过仅适配了原主机假设。

# Manager 实施裁决
接受分析的最小可迁移性修复：版本化模板移除站点专属Python3.10.19绝对路径，真正.local配置保留本地选择；通用脚本移除/mnt/public前缀限制并验证解释器>=3.10，错误清楚；真实worktree测试使用测试解释器而保留原业务断言。可把现有静默校验改清楚，避免其他重构。不把打包网络依赖混入本修复，文档声明其前提即可。请从main（manager已快进到origin/main 351c3a3）建立独立MAM worktree实施，可先创建ignored .local bootstrap选择现已安装的3.10.19以通过旧base建树，正式代码/test不应依赖此精确路径。跑完整单测并特别验证不在/mnt/public的测试解释器/路径可用。提交并发布report；manager安排独立review后合并main及project分支。

Source report:

# MAM 环境入口可迁移性修复

## 交付

- Worktree：`/mnt/public/xcj/Projects/table-1000/workspace/5514acec-f07c-4d7c-b676-aa4694898d87/multi-agent-manager`
- 分支：`task/5514acec-f07c-4d7c-b676-aa4694898d87`
- 交付 commit：`fbfdedcebfeb78046ec2b15902dc54ed2b43a52b`（base `351c3a3`）

该提交移除了版本化 local 模板中的 CPython 3.10.19 和 `/mnt/public/xcj` 路径；实际、被忽略的 `.local/create_worktree.sh` 保留部署者的解释器选择。通用脚本现在只接受绝对、可执行、可运行的 Python >=3.10，不再要求 `/mnt/public` 前缀，并为无效 workspace、branch、解释器、已有 worktree 与 `.venv` 软链接提供具体 stderr。

真实入口测试改为在临时仓库的 `.local/create_worktree.sh` 中传入测试自身解释器，并将传入路径放在 `/tmp`（显式断言其不在 `/mnt/public`）。它继续覆盖独立 venv、README 单文件链接及冲突保护、子 venv 的 `mam task status`、linked MAM root/config 与 archive 语义。新增测试确认伪解释器会得到明确的 Python >=3.10 错误且不创建 workspace。

安装文档说明了 PEP 517 `flit_core` 构建后端的包索引或预置缓存前提，没有把该打包网络问题混入本修复。

## 修正后的诊断结论

最初的失败直接由版本化 `scripts/local_create_worktree.sh` 对单一主机路径的硬编码造成。临时执行 `uv python install 3.10.19 --install-dir /mnt/public/xcj/cache/shared-python` 后的 41/41 通过，只是恢复了旧 wuwen-2 风格环境，不能证明 MAM 已具可迁移性；该真实解释器仍可作为本机 `.local` 配置，而不是 MAM 的全局前置条件。

`pyproject.toml` 的真实要求是 `requires-python = ">=3.10"`。此前通用脚本还把解释器限制为 `/mnt/public/*`，与此要求和 `.local` 的部署边界不一致。`351c3a3` 仅修改安装文档，不是该耦合的引入者。

清洁 `$HOME` 与禁用 pip cache 后，真实入口测试仍通过，故不依赖当前用户目录；加入 `PIP_NO_INDEX=1` 后，它和 `test_regular_install_runs_without_source_or_git_cwd` 都因 PEP 517 build isolation 找不到 `flit_core>=3.11,<5` 而失败。这是已在文档记录的打包集成前提。

## 验证

```bash
bash -n scripts/create_worktree.sh scripts/local_create_worktree.sh
git diff --check
.venv/bin/python -B -m unittest discover -s tests -v
```

结果：完整测试 `Ran 42 tests in 64.079s`，`OK`。针对真实入口和非 Python 诊断的两项测试也单独通过；未配置的版本化 local 模板会明确提示在 `.local/create_worktree.sh` 或 `MAM_SHARED_PYTHON` 中选择 Python，且不会创建 workspace。

# 用户文档拆分增量review
源任务新增文档commit 798bb01 与 fd28c23e72d49951ef508aea7d80361365598ec2（已发布report d15a026）。用户要求install.md仅讲使用安装，development.md讲MAM自身开发，README开发验证仅一句引用，AGENTS最后开发指引删除。请在已有独立review worktree只读审查git diff fbfded..fd28或ff到fd28，核对以上意图与信息无丢失/误导、相对链接正确。纯文档无需重跑tests或安装，禁止cache写入。尽快发布增量结论，manager合main/project并push main已获用户授权。
