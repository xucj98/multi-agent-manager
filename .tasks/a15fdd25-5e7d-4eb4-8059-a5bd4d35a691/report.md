task_revision: 8d5b4d5e8f11f180ab90a262da0fdf71ee005c35

完成与未完成：

F0 的四份 H50/K30 固定配置、row30 优先的 smoke 入口与诊断核查说明已准备并提交。原独立 workspace 已合入发布的 runtime；本轮只有 CPU/静态验证，没有启动新 GPU smoke、正式100或训练。准备阶段已完成，按 Manager 通知发布报告后结束本阶段，不空等 review；workspace 保留，GPU0仍预留。

已读取最新裁定：保留 recorder 完整配置匹配，四个 row 各自在自己的100ep前运行一次2-rollout smoke（一video、一no-video），仅GPU0按row30/20/1/50依次执行，不加selector白名单、不放宽门禁。terminal额外infer交runtime owner Einstein在OpenPISimulationScheduler现有路径中最小修复并独立review，不改SchedulerBase或真机循环。恢复后先取得明确修复commit、更新入口固定版本，再按Manager放行运行smoke；formal仍另行通知。当前fd38513仅作为准备阶段版本，不据此启动正式评测。

workspace、各库交付 commit：

- workspace：/mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691，复用原 MAM 登记的三个 worktree，没有创建新任务或修改主 checkout。
- RMBench：9e8fccbd2fa004f18a3cbcc301e7387b02edaccf（实验：准备旧 full 的 F0 固定选行配置与 smoke 入口），8文件、修改仅在 experiments/memory_chunk_20260910/。此前中文文档反馈提交 d1a64cb2468d409411bbcfd3f23ae59d2ec8db6e 已保留。
- robot-bridge：fd38513adb5ba171327358f70f55f88059de49d2，本任务独立分支已 fast-forward 合入，无本地核心修改。
- openpi：58d6f2155acc3af03017677bb3f536101e6699f4，本任务独立分支已 fast-forward 合入，无本地模型修改。
- OpenPI 使用自己的 editable 环境；bridge 自己的 .venv 已 editable 安装同任务 ../openpi/packages/openpi-client，实际 openpi_client.memory_config.__file__ 指向本任务 OpenPI worktree。
- 提交后核对 message、文件摘要与状态，三个 worktree 均干净。

固定协议与入口：

- 四份真实 scheduler YAML 位于 experiments/memory_chunk_20260910/configs/：f0_row1.yaml、f0_row20.yaml、f0_row30.yaml、f0_row50.yaml。共同为 scheduler=openpi_simulation、move_steps=30、debug_iterations=0；legacy_full_feedback_selector 均为 kind=index，value分别0/19/29/49，所有 legacy memory 字段共同选行。
- H50 从同一旧30k checkpoint metadata 恢复；保留原模型、字段、归一化、编码与解码，不注入新 memory_config。旧字段为 phase、empty_mat_side、button_press_status。
- 旧 P1 场景固定 demo_clean_eval；eval seed=0、起始候选seed=100000、instruction generation=100。四组正式 run 计划各单GPU串行100条，顺序row30/20/1/50，成对初始条件一致。
- 训练/转换数据约束仍为 demo_clean_state；旧 metadata 记录 rearrange_blocks_demo_clean_state_shared_memory。新 checkpoint 必须提供同来源证据，不能以缺metadata/详细子任务标注的 demo_clean 替代。没有因此改变旧 P1 评测场景。
- 新入口自动定位三库，检查固定 runtime HEAD/干净状态、scheduler配置与H50。仅GPU0，policy显存比例0.40，启动前查询GPU0显存/利用率/计算进程；已有计算进程时拒绝启动。F0共用编译缓存，结果leaf独立。
- --dry-run只校验并展开命令，不启动GPU、不创建结果或缓存。旧shell默认入口保留，F0 wrapper显式传入新scheduler配置与结果名。

现在可执行的核对命令（无需export根目录变量）：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0_smoke.py --row 30 --dry-run
```

Manager恢复本任务、拿到terminal修复commit并更新入口固定版本、确认runtime review无阻塞后，首个row30的实际smoke命令如下；当前尚未执行，其余row后续各自按同一入口指定--row：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/RMBench
../robot-bridge/.venv/bin/python experiments/memory_chunk_20260910/commands/run_f0_smoke.py --row 30
```

验证结果：

- 在bridge独立环境仅用CPU完成以下定向集合：57 passed in 3.40s。

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/robot-bridge
CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python -m pytest -q tests/scheduler/test_openpi_simulation.py tests/benchmark tests/policy/test_openpi_metadata.py tests/robot/controllers/test_execution_progress.py
```

- 四臂dry-run均通过；展开参数为smoke、GPU0、各自selector YAML和独立结果名，未启动GPU。
- 用既有真实smoke的policy_metadata初始化实际scheduler的四份配置均通过，确认H50/model_action_dim32、legacy full_state、无新memory_config与原字段。K30覆盖checkpoint保存的query_stride20的警告符合原P1协议。
- 已有CPU用例覆盖完整K30时last_executed与index29反馈等价；这不等于GPU真实闭环smoke已通过。partial terminal时二者不保证同一选行。
- 新Python文件ruff、shell的bash -n、git diff --check均通过；没有重复已验收的旧GPU smoke。
- 诊断说明覆盖query_id、source/observed logical step、planned/actual K、selector、selected row、fields before/selected/after、next_query。完整日志在run的processes/；status仅保留最近64条trace。同query的多次状态日志应合并核查，不能计为多次query。row50只读模型预测，完整K30后应为was_executed=false。

问题1与最新处理：终止观测的实际infer与trace不一致，已交runtime owner修复。

bridge robot_bridge/scheduler/openpi_simulation.py:606在terminal观测标记next_query=false，但robot_bridge/scheduler/base.py:507构建policy输入后，:512仍无条件调用infer，直到build_act_request才跳过action。CPU fake clients已复现如下，未修改runtime，也没有启动模型/GPU：

```bash
cd /mnt/public/xcj/Projects/workspace/a15fdd25-5e7d-4eb4-8059-a5bd4d35a691/robot-bridge
CUDA_VISIBLE_DEVICES='' JAX_PLATFORMS=cpu .venv/bin/python - <<'PY'
import json
from types import SimpleNamespace
from tests.scheduler.test_openpi_simulation import _f0_scheduler, _f0_actions, _obs

s = _f0_scheduler({"kind": "index", "value": 29})
obs = _obs(100)
s.build_policy_obs(obs)
s.after_execute(s.build_act_request({"actions": _f0_actions()}, obs))
calls = []
s._policy_reset_pending = False
s._robot_client = SimpleNamespace(
    call=lambda request: {"status": "ok", "obs": _obs(110, terminal=True)}
)
def infer(request):
    calls.append(request["cmd"])
    return {"status": "ok", "actions": _f0_actions()}
s._policy_client = SimpleNamespace(call=infer)
result = s.run_iteration()
trace = s.get_status()["memory_diagnostics"]["traces"][-1]
print(json.dumps({
    "iteration_return": result,
    "post_terminal_policy_calls": calls,
    "trace_actual_k": trace["actual_k"],
    "trace_next_query": trace["next_query"],
}))
PY
```

实测输出：{"iteration_return": "skip", "post_terminal_policy_calls": ["infer"], "trace_actual_k": 10, "trace_next_query": false}。现有terminal用例直接分别调用build_policy_obs/build_act_request，未覆盖完整run_iteration的实际infer。Manager已交Einstein做最小sim修复并交reviewer复核；本任务不改scheduler核心，恢复后合入明确修复commit并更新固定版本。

问题2与最新裁定：四个row各自完成匹配配置的smoke，保留现有门禁。

RMBench script/eval_diagnostics.py:702的assert_smoke_compatible对launch做完整_content_identity比较，而bridge robot_bridge/benchmark/runner.py:593将解析后的scheduler_config放在launch中。实际四份YAML经身份比较，row30与row20等均不相等，正式复用会触发“smoke launch differs from actual formal run”。Manager已裁定每个row在自己的100之前完成一次2-rollout smoke；完整配置检查保留，不增加selector白名单或放宽门禁。此项已有执行方案，不再待裁定；本阶段没有运行这些GPU smoke。

此外，runner的source_content_hash包含Git可见内容；smoke后新增正式入口或修改experiments文档/配置会影响源身份。交付完整正式入口时必须同时核对provenance，不能假定提交后自然可复用已有smoke。本轮只准备配置与smoke入口，完整正式入口及最终验收仍未完成。9e8fccb中的README/固定版本反映准备时状态；恢复后随明确runtime修复commit同步更新到本次裁定。

成果位置与旧smoke锚点：

- worktree的eval_result经readlink解析为 /mnt/public/xcj/Projects/RMBench/eval_result，产物在共享主RMBench，不依赖临时workspace留存。
- 新row30 smoke计划目录：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/f0_rearrange_full_h50_k30_row30_smoke_20260910/。当前尚未创建，不是已完成产物。
- 四个正式目录计划为主RMBench同实验组下的f0_rearrange_full_h50_k30_row{1|20|30|50}_100ep_seed0，尚未运行。
- Manager已验收的旧加载锚点：/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/pi05_rearrange_full_k30_oldfull_smoke_20260910/。旧bridge为b17f6c53ffbc1030972a9820cf592f28b937d501、OpenPI为71c80db723a242c61cfe429dd6794e9ece3cbcf1；不能替代新F0 smoke。
- 旧smoke于2026-09-10 03:35:11—03:41:57 +08:00完成，exit0；seed100000为Fail（button_press_insufficient）、100001为Success，结果1/2。episode0.mp4为700帧、521128 bytes且可读；episode1视频关闭且不存在。两个scheduler child exit0，robot/policy正常shutdown；当时官方validate_smoke_run通过。
- 旧目录留存config.yaml、command.txt、checkpoint_metadata/、episode context、诊断、video_checks.jsonl、processes.jsonl。config SHA-256为2dbaa989b3703e3aeb0fd342528ddfa6e5b519e48783d8ce180296b734814a89。
- 旧restore日志为7.95秒，包含冷启动/XLA编译的两条smoke共406秒（粗算17.7条/小时）；两条长度700/406 logical steps。这些仅是旧环境吞吐锚点，不能承诺新F0正式100耗时。

运行状态：

本阶段发布后结束，释放agent并发名额供Manager安排sim数据独立复核，不做轮询等待。workspace不删除，GPU0继续预留；GPU1与远端训练资源不使用。Manager在F0审查结论到达后恢复本任务；届时先合入terminal修复并更新固定版本，逐row检查两条smoke的一次video、一次no-video、metadata与逐query时序，正式100各自仍须通知。第50条由实验负责人手动检查相对固定基线偏差，超过10个百分点时调查并记录协议/基础设施结论，保留全部不利episode；不宣称runner自动实现该人工检查。本轮无新运行进程或MAM job，不归档任务或workspace。
