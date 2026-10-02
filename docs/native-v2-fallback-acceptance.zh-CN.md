# 原生子 agent 唤醒转发验收

验证原生子 agent 拒绝直接唤醒后，Manager 能收到简短通知，通过 `followup_task` 让执行者处理并归档 job。

使用专门用于验收的 root Manager 及其空闲原生子 agent，在独立 fixture 中运行。准备一个干净的源码 worktree 和已安装该源码的 `.venv`。辅助脚本负责创建 fixture、核对状态、保存证据和清理；原生协作动作由 Manager 执行。

## 准备

下面使用 Bash。替换源码目录、临时目录和 agent ID；fixture 必须是尚不存在的目录，放在本次验收任务的 `tmp` 下。

```bash
SOURCE_ROOT=/absolute/path/to/source-worktree
SOURCE_PYTHON="$SOURCE_ROOT/.venv/bin/python"
FIXTURE_ROOT=/absolute/path/to/workspace/TASK-ID/tmp/native-v2-fixture
ROOT_MANAGER=ROOT-AGENT-ID
NATIVE_CHILD=CHILD-AGENT-ID
CHILD_ARCHIVE_NOTE='native-v2 fallback fixture handled'
MAM=("$SOURCE_PYTHON" -I -c 'from multi_agent_manager.cli import main; raise SystemExit(main())')
CHECK=("$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py")

"${CHECK[@]}" prepare --root "$FIXTURE_ROOT" --source-root "$SOURCE_ROOT" \
  --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" --confirm CREATE_NATIVE_V2_FIXTURE
```

核对 `receipts/prepare.json` 中的源码 commit、模块路径和 fixture 路径。后续所有 MAM 命令都在 fixture project 中使用上述 `MAM` 入口；准备完成后保持 Manager 当前 turn，直到重启检查通过。

```bash
cd "$FIXTURE_ROOT/project"
TASK_ID="$("${MAM[@]}" task create --title 'native-v2 fallback acceptance' |
  "$SOURCE_PYTHON" -I -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
printf '# 验收任务\n登记短 sleep 进程；收到 Manager 后续通知后再归档 job 并发布简报。\n' \
  > "$FIXTURE_ROOT/state/.tasks/$TASK_ID/task.md"
"${MAM[@]}" task publish "$TASK_ID"
```

Manager 用 `collaboration.followup_task` 将 fixture 路径、受控 `MAM` 命令和 TASK-ID 交给指定 child。child 在自己的 turn 中执行：

```bash
cd "$FIXTURE_ROOT/project"
"${MAM[@]}" task start "$TASK_ID"
"${MAM[@]}" task show
sleep 90 >/dev/null 2>&1 &
fixture_pid=$!
"${MAM[@]}" job add --host local --pid "$fixture_pid" --note 'native-v2 fixture sleep' \
  > "$FIXTURE_ROOT/receipts/child-registration.json"
```

child 登记后结束 turn。Manager 记录已执行的原生委派，取得 JOB-ID，再启动 fixture service：

```bash
"${CHECK[@]}" record-delegation --root "$FIXTURE_ROOT" --task "$TASK_ID" \
  --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
  --attestation 'root used collaboration.followup_task to delegate the fixture job' \
  --receipt "$FIXTURE_ROOT/receipts/delegation.json"
JOB_ID="$("$SOURCE_PYTHON" -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' \
  "$FIXTURE_ROOT/receipts/child-registration.json")"
IDS=(--root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD")
"${CHECK[@]}" verify-source --root "$FIXTURE_ROOT" --phase before-start \
  --receipt "$FIXTURE_ROOT/receipts/source-before-start.json"
"${MAM[@]}" service start --manager "$ROOT_MANAGER"
```

全部通知使用用户消息渠道，Manager 在客户端核对收到的 MAM 消息。

## 拒绝与重启

Manager 保持 active。进程退出且 child 空闲后，等待 job 探测和一次调度周期，检查：直接投递被拒绝并停止重试，Manager 转发通知尚未发送。

```bash
"${CHECK[@]}" assert "${IDS[@]}" --phase blocked \
  --receipt "$FIXTURE_ROOT/receipts/blocked.json"
```

停止 fixture service 后，先确认进程退出，再记录和重启。以下函数最多检查 30 次，每次间隔一秒：

```bash
wait_fixture_stopped() {
  local attempt
  for attempt in {1..30}; do
    FIXTURE_STOP_STATUS="$("${MAM[@]}" service status)" || return 1
    if "$SOURCE_PYTHON" -I -c 'import json,sys; sys.exit(json.load(sys.stdin).get("running") is not False)' \
      <<<"$FIXTURE_STOP_STATUS"; then return 0; fi
    sleep 1
  done
  return 1
}

"${MAM[@]}" service stop
wait_fixture_stopped || exit 1
"${CHECK[@]}" record-stopped "${IDS[@]}" \
  --baseline "$FIXTURE_ROOT/receipts/blocked.json" --service-status "$FIXTURE_STOP_STATUS" \
  --receipt "$FIXTURE_ROOT/receipts/stopped.json"
"${MAM[@]}" service start --manager "$ROOT_MANAGER"
```

Manager 保持 active，待重启后的 service 完成至少两个调度周期，再检查原待办得到保留、子 agent 未被重复直投：

```bash
"${CHECK[@]}" assert "${IDS[@]}" --phase restarted \
  --baseline "$FIXTURE_ROOT/receipts/blocked.json" --stopped-baseline "$FIXTURE_ROOT/receipts/stopped.json" \
  --receipt "$FIXTURE_ROOT/receipts/restarted.json"
```

## 收到通知与收尾

Manager 正常结束 turn。收到通知后，在新 turn 恢复上述路径、ID 和命令数组。消息包含执行者路径或 TASK-ID、JOB-ID，以及用 `followup_task` 通知执行者检查结果并归档 job 的动作；精确 RPC 错误保存在 service 诊断中。待办仍存在时，Manager 再次空闲会收到后续提醒。

将实际收到的完整消息赋给 `MANAGER_ATTESTATION`，保存投递证据：

```bash
MANAGER_ATTESTATION='粘贴实际收到的完整 [MAM Message] 消息'
"${CHECK[@]}" assert "${IDS[@]}" --phase delivered \
  --baseline "$FIXTURE_ROOT/receipts/restarted.json" --manager-attestation "$MANAGER_ATTESTATION" \
  --receipt "$FIXTURE_ROOT/receipts/delivered.json"
```

Manager 核对 child 状态后，用 `collaboration.followup_task` 通知同一 child 在 fixture 中收尾，同时传入路径、ID 和 `MAM`、`CHECK`、`IDS` 数组。child 执行：

```bash
"${MAM[@]}" job archive "$JOB_ID" --note "$CHILD_ARCHIVE_NOTE"
"${CHECK[@]}" record-child-archive "${IDS[@]}" \
  --attestation "child received collaboration.followup_task and ran mam job archive $JOB_ID --note '$CHILD_ARCHIVE_NOTE' for TASK-ID $TASK_ID" \
  --receipt "$FIXTURE_ROOT/receipts/child-archive.json"
printf '已收到原生 follow-up，检查并归档 fixture job。\n' \
  > "$FIXTURE_ROOT/state/.tasks/$TASK_ID/report.md"
"${MAM[@]}" task report
```

Manager 等待一个调度周期，确认旧 job 待办消失，然后停止 fixture service 并归档任务：

```bash
"${CHECK[@]}" assert-archived "${IDS[@]}" \
  --baseline "$FIXTURE_ROOT/receipts/delivered.json" \
  --child-archive-receipt "$FIXTURE_ROOT/receipts/child-archive.json" \
  --receipt "$FIXTURE_ROOT/receipts/archived.json"
"${MAM[@]}" service stop
wait_fixture_stopped || exit 1
"${CHECK[@]}" verify-source --root "$FIXTURE_ROOT" --phase after-stop \
  --receipt "$FIXTURE_ROOT/receipts/source-after-stop.json"
"${MAM[@]}" task archive "$TASK_ID" --note 'fixture completed; receipts retained'
```

将 receipts 汇总到本次验收任务的 `.task/files/` 并发布，之后清理 fixture。`--external-evidence` 指向已经保存、位于 fixture 外的证据文件。

```bash
"${CHECK[@]}" cleanup --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" \
  --external-evidence /absolute/path/to/retained-evidence.json --confirm REMOVE_NATIVE_V2_FIXTURE
```

遇到异常先停止 fixture service，保留目录和证据供检查。
