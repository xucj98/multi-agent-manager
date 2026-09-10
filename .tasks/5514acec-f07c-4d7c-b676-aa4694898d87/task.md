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

# 用户最新文档重组要求
用户明确要求：docs/install.md仅讲如何安装/使用MAM及配置；新增docs/development.md讲开发MAM自身（开发worktree、Python选择、editable/build后端、测试与合并等）；README中“开发验证”仅保留一句引用development.md；AGENTS.md最后关于修改MAM实现/开发验证的那句删除，日常AGENTS不指挥MAM开发。请在原任务独立worktree继续实现。manager已先提交798bb01澄清两段作用域并合入main/project，你的原worktree HEAD也为798bb01，从这里继续。docs/development要自包含且不把Python>=3.10当其他repo要求；正确链接，简洁，不新增流程。纯文档无需再跑完整单测，检查链接与diff即可。完成commit并发布report后给manager合并，后续独立文档review。cache迁移仍在进行，不运行uv/pip写cache。
