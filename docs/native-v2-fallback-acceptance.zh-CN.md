# 原生 multi-agent v2 fallback 隔离验收

本文是 `unsupported_multi_agent_v2_direct_input` fallback 的人工验收 runbook。配套的
[`scripts/native_v2_fallback_acceptance.py`](../scripts/native_v2_fallback_acceptance.py) 只创建带
ownership marker 的新 fixture 目录，或读取该 fixture 的状态并生成证据；它不会连接 App Server、创建
Codex thread、发送 follow-up、安装 MAM、修改 Codex DB/feature flag，或重启任何服务。默认 `plan` 子命令
没有副作用；`prepare` 和最后的 `cleanup` 都需要明确的确认短语。

这不是安装器的普通 persistent-thread liveprobe。普通 liveprobe 通过只证明常规 scheduler delivery；这里
专门确认真实原生 child 的 direct input 被拒绝后，Manager 的 parent-native follow-up 能完成收尾，不能称为
child direct `turn/start` 已恢复。

## 固定边界

- 使用一个新的、原本不存在的绝对路径作为 `FIXTURE_ROOT`；脚本在其中建立独立的 `project`、Git `state`、
  `.mam/env.json`、service state 和 `receipts`。它不读取或写入生产项目的 task、job、service state 或
  workspace。
- 当前验收由 root Manager `01a09657-e0f3-7352-b726-aba5bbd5d498` 执行；仅在 root 已明确以
  `collaboration.followup_task` 委派后，才使用既有原生 child
  `01a096ab-e5f3-7672-8ff3-36328d3fcfb7`（`/root/u_training_owner`）。不创建、替换、archive 或中断该
  child 的 thread，也不触碰其已有 review task。
- fixture 只登记一个本地短 sleep 进程。child 负责登记和最终 `mam job archive`；root Manager 负责创建、
  绑定、启动/停止**fixture** scheduler、记录 receipt、task archive 和删除已确认 ownership 的 fixture
  目录。任何异常先停止 fixture scheduler，保留目录和 receipts 供核对；不要删除 child、生产 task/job 或
  App Server。
- 运行必须使用待验收 source worktree 的 `.venv/bin/mam`，而不是已安装的 pipx launcher。这样 fixture
  daemon 由该 source 的 `wake_runtime` 启动，且无需执行安装。

## 执行前准备

先只在 root 的 active turn 中执行以下准备；不要让 root 结束 turn，直到 `blocked` 和 restart checkpoint 都
通过。这里的 `FIXTURE_ROOT` 必须是新目录，示例路径仅供替换：

```bash
SOURCE_ROOT=/mnt/public/xcj/Projects/workspace/b49a5b40-1d18-40e6-bc28-c5c57dc011f3/multi-agent-manager
FIXTURE_ROOT=/mnt/public/xcj/Projects/.native-v2-fallback-fixture-$(date -u +%Y%m%dT%H%M%SZ)
ROOT_MANAGER=01a09657-e0f3-7352-b726-aba5bbd5d498
NATIVE_CHILD=01a096ab-e5f3-7672-8ff3-36328d3fcfb7

"$SOURCE_ROOT/.venv/bin/python" "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" prepare \
  --root "$FIXTURE_ROOT" --source-root "$SOURCE_ROOT" \
  --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
  --confirm CREATE_NATIVE_V2_FIXTURE
```

`prepare` 仅初始化 fixture Git state、project config 和 marker，尚未创建 task、启动 scheduler 或联系 App
Server。root 在 fixture project 中用 source CLI 创建并发布 task，再绑定 child：

```bash
MAM="$SOURCE_ROOT/.venv/bin/mam"
cd "$FIXTURE_ROOT/project"
TASK_ID="$("$MAM" task create --title 'native-v2 fallback isolated acceptance' | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
printf '# native-v2 fallback isolated acceptance\n\nOnly register the owned short fixture job; do not archive it until the root Manager follows up after the fallback notification.\n' > "$FIXTURE_ROOT/state/.tasks/$TASK_ID/task.md"
"$MAM" task publish "$TASK_ID" --file task
"$MAM" task bind "$TASK_ID" --agent "$NATIVE_CHILD"
```

root 接着以自身的 parent-native `collaboration.followup_task` 明确委派 child：先 `mam task show "$TASK_ID"`，
再在 `$FIXTURE_ROOT/project` 启动一个约 90 秒的本地 `sleep`、以 `mam job add` 绑定它，并把返回的 `JOB_ID`
写到 `$FIXTURE_ROOT/receipts/child-registration.json`。child 不启动 service、不 archive job，也不操作任何非
fixture 路径。root 在成功发送该原生委派后记录声明：

```bash
"$SOURCE_ROOT/.venv/bin/python" "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" record-delegation \
  --root "$FIXTURE_ROOT" --task "$TASK_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
  --attestation 'root used collaboration.followup_task to delegate only the fixture job' \
  --receipt "$FIXTURE_ROOT/receipts/delegation.json"
```

确认 child 已登记 job 且还在运行后，root 启动唯一的 fixture scheduler；`wake_compat` 会对随机未知 ID 做
拒绝检查，但不会创建任何 thread：

```bash
cd "$FIXTURE_ROOT/project"
"$MAM" service start --manager "$ROOT_MANAGER"
```

## 必须按顺序留下的证据

1. root 保持 active，等待该短 job 停止并让 fixture scheduler 至少完成一个 `JOB_PROBE_SECONDS`（30 秒）
   和一个 scheduler cycle（10 秒）。预期 child direct `turn/start` 恰好一次并得到已知精确拒绝。
   `assert --phase blocked` 要求 source `delivery: blocked`、精确 failure/block kind、`next_attempt_at: null`、
   source `attempts == 1`，以及同 TASK/JOB 的唯一 pending Manager escalation `attempts == 0`。它还拒绝同
   task 的 `task_ready`/额外 Manager event，防止设置顺序产生混杂通知。

   ```bash
   "$SOURCE_ROOT/.venv/bin/python" "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" assert \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --phase blocked --receipt "$FIXTURE_ROOT/receipts/blocked.json"
   ```

2. root 仍保持 active，至少再等两个 scheduler cycle 后停止并重新启动**fixture** scheduler；这不是 App
   Server restart。`assert --phase restarted` 将当前 state 与 `blocked.json` 比较：service PID 必须变化、cycle
   数增加，child source 和 Manager escalation 的 attempts 都不能增加，且 Manager escalation 仍未 accepted。

   ```bash
   "$MAM" service stop
   "$MAM" service start --manager "$ROOT_MANAGER"
   # wait at least 20 seconds while root is still active
   "$SOURCE_ROOT/.venv/bin/python" "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" assert \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --phase restarted --baseline "$FIXTURE_ROOT/receipts/blocked.json" \
     --receipt "$FIXTURE_ROOT/receipts/restarted.json"
   ```

3. root 正常结束当前 turn。fixture daemon 只在 root 确为 idle 后发送一次带 fixture TASK-ID/JOB-ID 和精确错误
   的 `[MAM Message]`。收到该消息的新 root turn 先目视确认其 marker，随后运行 `assert --phase delivered`；
   它要求唯一 Manager escalation 为 `accepted`、`attempts == 1`，source 仍为 `blocked`、`attempts == 1`。
   `--manager-attestation` 记录这次人类可见的单条通知，持久 state 的 exactly-one attempts 是机器可复核部分。

   ```bash
   "$SOURCE_ROOT/.venv/bin/python" "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" assert \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --phase delivered --baseline "$FIXTURE_ROOT/receipts/restarted.json" \
     --manager-attestation "[MAM Message] TASK-ID $TASK_ID JOB-ID $JOB_ID received in the new idle-root turn" \
     --receipt "$FIXTURE_ROOT/receipts/delivered.json"
   ```

4. root 在该新 turn 使用 parent-native `collaboration.followup_task` 让同一 child **只**运行
   `mam job archive "$JOB_ID" --note 'native-v2 fallback fixture handled'` 并写 fixture report。root 不应因为
   child 已显示 `active` 就再发一次 follow-up：先查 child 的状态/报告。等待一个 fixture cycle 后，
   `assert --phase archived` 要求 job 已 archive，active events 已没有该 source/escalation，history 有二者的
   stale 记录。root 在 archive fixture task 前保持当前 turn active；job 已 archive 且 child 转 idle 后可能形成
   普通 `task_ready`，应由紧随其后的 task archive 清除，不能让它在这次验收中成为第二条 idle-time 通知。

   ```bash
   "$SOURCE_ROOT/.venv/bin/python" "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" assert-archived \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --receipt "$FIXTURE_ROOT/receipts/archived.json"
   ```

5. root 保存 receipts 到任务报告可引用的位置，停止 fixture service，archive fixture task，最后才运行 guarded
   `cleanup`。`cleanup` 要求 service 已 disabled、fixture task/job 已 archived、外部 evidence 文件存在且不在
   fixture root 内；它只删除 marker 所有的 fixture root。若任一点失败，保留 fixture 并由 root 处理。

   ```bash
   # Copy or assemble the evidence outside FIXTURE_ROOT first, then run these as root.
   cd "$FIXTURE_ROOT/project"
   MAM="$SOURCE_ROOT/.venv/bin/mam"
   "$MAM" service stop
   "$MAM" task archive "$TASK_ID" --note 'native-v2 fallback fixture completed and receipts retained'
   "$SOURCE_ROOT/.venv/bin/python" "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" cleanup \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" \
     --external-evidence /absolute/path/outside-fixture/native-v2-fallback-evidence.json \
     --confirm REMOVE_NATIVE_V2_FIXTURE
   ```

整个验收不运行 `scripts/install.sh`，不安装任何内容，不重启 App Server 或生产 daemon，也不声称 direct
native-v2 input 已恢复。
