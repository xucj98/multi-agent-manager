# 原生 multi-agent v2 fallback 隔离验收

本文是 `unsupported_multi_agent_v2_direct_input` fallback 的人工验收 runbook。配套的
[`scripts/native_v2_fallback_acceptance.py`](../scripts/native_v2_fallback_acceptance.py) 只创建带
ownership marker 的新 fixture 目录，读取 fixture state 并生成证据，同时仅以隔离环境只读核验待测 source；
它不会连接 App Server、创建 Codex thread、发送 follow-up、安装 MAM、修改 Codex DB/feature flag，或重启
任何服务。默认 `plan` 子命令
没有副作用；`prepare` 和最后的 `cleanup` 都需要明确的确认短语。

这不是安装器的普通 persistent-thread liveprobe。普通 liveprobe 通过只证明常规 scheduler delivery；这里
专门确认真实原生 child 的 direct input 被拒绝后，Manager 的 parent-native follow-up 能完成收尾，不能称为
child direct `turn/start` 已恢复。

## 固定边界

- 使用一个新的、原本不存在的绝对路径作为 `FIXTURE_ROOT`；脚本只在其中建立 `project`、Git `state`、
  `.mam/env.json`、service state、Git isolation 和 `receipts`。它不读取或写入生产项目的 task、job、
  service state 或 workspace。
- `prepare` 的每个 Git 子进程都会删除继承的全部 `GIT_*`，禁用 system config，使用 fixture-owned 的空
  global config、空 template 和 hooks 目录；commit 同时使用 `--no-verify`。随后它以同一环境核验
  `state` 的 top-level 和 absolute git-dir 都精确属于 fixture。它不修改用户 Git 配置、外部仓库、外部
  index 或 hook。
- 所有 fixture CLI 都固定为 `SOURCE_ROOT/.venv/bin/python -I -c 'from multi_agent_manager.cli import main;
  raise SystemExit(main())'`，不使用 console script 或 `-m multi_agent_manager.cli`。`prepare` 会在 `-I`
  下实际导入 `multi_agent_manager`、`.cli` 和 `.wake_runtime`，要求三个 resolved `__file__` 都在
  `SOURCE_ROOT/multi_agent_manager`；它也以净化 Git 环境核验 source worktree top-level、准确 `HEAD` 与
  `git status --porcelain=v1 --untracked-files=all --ignore-submodules=none` 的空输出，并把 source Python、
  受控 CLI、三个 module path、`source_clean: true`、空 `source_git_status` 与准确 `HEAD` 写入
  `receipts/prepare.json`。执行前将其中的 `source_commit` 与本任务报告的待测交付 commit 核对。
- 当前验收由 root Manager `01a09657-e0f3-7352-b726-aba5bbd5d498` 执行；仅在 root 已明确以
  `collaboration.followup_task` 委派后，才使用既有原生 child
  `01a096ab-e5f3-7672-8ff3-36328d3fcfb7` (`/root/u_training_owner`)。不创建、替换、archive 或中断该
  child 的 thread，也不触碰其已有 review task。
- fixture 只登记一个本地短 sleep 进程。child 负责登记和最终 `mam job archive`；root Manager 负责创建、
  绑定、启动/停止**fixture** scheduler、记录 receipt、task archive 和删除已确认 ownership 的 fixture
  目录。任何异常先停止 fixture scheduler，保留目录和 receipts 供核对；不要删除 child、生产 task/job 或
  App Server。

## 执行前准备

以下命令要求 Bash。只在 root 的 active turn 中执行准备；不要让 root 结束 turn，直到 `blocked` 和
restart checkpoint 都通过。`FIXTURE_ROOT` 必须是新目录：

```bash
SOURCE_ROOT=/mnt/public/xcj/Projects/workspace/b49a5b40-1d18-40e6-bc28-c5c57dc011f3/multi-agent-manager
SOURCE_PYTHON="$SOURCE_ROOT/.venv/bin/python"
MAM=(
  "$SOURCE_PYTHON" -I -c
  'from multi_agent_manager.cli import main; raise SystemExit(main())'
)
FIXTURE_ROOT=/mnt/public/xcj/Projects/.native-v2-fallback-fixture-$(date -u +%Y%m%dT%H%M%SZ)
ROOT_MANAGER=01a09657-e0f3-7352-b726-aba5bbd5d498
NATIVE_CHILD=01a096ab-e5f3-7672-8ff3-36328d3fcfb7
EXACT_REJECTION='App Server request turn/start failed: direct app-server input is not allowed for multi-agent v2 sub-agents'
CHILD_ARCHIVE_NOTE='native-v2 fallback fixture handled'

"$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" prepare \
  --root "$FIXTURE_ROOT" --source-root "$SOURCE_ROOT" \
  --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
  --confirm CREATE_NATIVE_V2_FIXTURE
```

在继续前读取 `FIXTURE_ROOT/receipts/prepare.json`：`source_cli` 必须是上面的 `MAM` 命令，三个
`source_modules` 必须都在 `SOURCE_ROOT/multi_agent_manager`，`source_git_toplevel` 必须精确等于
`SOURCE_ROOT`，`source_clean` 必须为 `true`、`source_git_status` 必须为空，且 `source_commit` 是待验收的
交付 commit。`fixture_git_toplevel` 和
`fixture_git_dir` 分别必须精确为 `FIXTURE_ROOT/state` 与 `FIXTURE_ROOT/state/.git`。

下面的本地函数只查询当前 fixture project 的 service state；它会在 60 秒后明确失败。每次 `service stop`
之后、`service start` 或删除 fixture 之前都要调用它：

```bash
FIXTURE_STOP_STATUS=''
wait_fixture_service_stopped() {
  local deadline=$((SECONDS + 60))
  local running
  while true; do
    if ! FIXTURE_STOP_STATUS="$("${MAM[@]}" service status)"; then
      printf '%s\n' 'fixture service status failed while waiting for stop' >&2
      return 1
    fi
    if ! running="$("$SOURCE_PYTHON" -I -c \
      'import json,sys; print("false" if json.load(sys.stdin).get("running") is False else "other")' \
      <<<"$FIXTURE_STOP_STATUS")"; then
      printf '%s\n' 'fixture service status was not valid JSON' >&2
      return 1
    fi
    if [[ "$running" == false ]]; then
      return 0
    fi
    if (( SECONDS >= deadline )); then
      printf '%s\n' 'fixture scheduler remained running for 60 seconds after service stop' >&2
      return 1
    fi
    sleep 1
  done
}
```

`prepare` 仅初始化 fixture Git state、project config 和 marker，尚未创建 task、启动 scheduler 或联系 App
Server。root 在 fixture project 中用受控 CLI 创建并发布 task，再绑定 child：

```bash
cd "$FIXTURE_ROOT/project"
TASK_ID="$("${MAM[@]}" task create --title 'native-v2 fallback isolated acceptance' |
  "$SOURCE_PYTHON" -I -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
printf '# native-v2 fallback isolated acceptance\n\nOnly register the owned short fixture job; do not archive it until the root Manager follows up after the fallback notification.\n' \
  > "$FIXTURE_ROOT/state/.tasks/$TASK_ID/task.md"
"${MAM[@]}" task publish "$TASK_ID" --file task
"${MAM[@]}" task bind "$TASK_ID" --agent "$NATIVE_CHILD"
```

root 接着以自身的 parent-native `collaboration.followup_task` 明确委派 child：先以受控 CLI 运行
`task show "$TASK_ID"`，再在 `FIXTURE_ROOT/project` 启动一个约 90 秒的本地 `sleep`、以受控 CLI 的
`job add` 绑定它，并把返回的 `JOB_ID` 写到 `FIXTURE_ROOT/receipts/child-registration.json`。child
不启动 service、不 archive job，也不操作任何非 fixture 路径。root 成功发送该原生委派后记录声明：

```bash
"$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" record-delegation \
  --root "$FIXTURE_ROOT" --task "$TASK_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
  --attestation 'root used collaboration.followup_task to delegate only the fixture job' \
  --receipt "$FIXTURE_ROOT/receipts/delegation.json"
```

确认 child 已登记 job 且还在运行后，root 启动唯一的 fixture scheduler；`wake_compat` 会对随机未知 ID 做
拒绝检查，但不会创建任何 thread：

```bash
cd "$FIXTURE_ROOT/project"
"$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" verify-source \
  --root "$FIXTURE_ROOT" --phase before-start \
  --receipt "$FIXTURE_ROOT/receipts/source-before-start.json"
"${MAM[@]}" service start --manager "$ROOT_MANAGER"
```

`verify-source` 会以 prepare 时相同的隔离 Git 和 `-I` import 检查 source 的完整 identity；任何 HEAD、
clean 状态、module path 或受控 CLI 漂移都会失败并保留 fixture，不能继续启动 scheduler。

## 必须按顺序留下的证据

1. root 保持 active，等待短 job 停止，并让 fixture scheduler 至少完成一个 `JOB_PROBE_SECONDS`（30 秒）
   和一个 scheduler cycle（10 秒）。预期 child direct `turn/start` 恰好一次并得到已知精确拒绝。
   `assert --phase blocked` 要求 source `delivery: blocked`、精确 failure/block kind、精确 error、
   `next_attempt_at: null`、`attempts == 1`，以及同 TASK/JOB 的唯一 pending Manager escalation
   `attempts == 0`、相同 source signature、精确 error 和 `use_native_followup_task` action。receipt 会持久化
   source/escalation 的 signature、delivery、attempts、error、source_event、action 和 `accepted_at`。

   ```bash
   "$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" assert \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --phase blocked --receipt "$FIXTURE_ROOT/receipts/blocked.json"
   ```

2. root 仍保持 active。停止**fixture** scheduler，等待其 `service status` 的 `running: false` 后，先记录
   stopped receipt，再启动它；这不是 App Server restart。stopped receipt 将 `blocked.json` 的 TASK/JOB、
   Manager/child、source/escalation signature、精确 payload、attempts 与旧 daemon PID/identity 绑定到
   `enabled: false`、`mode: disabled` 的实际 service-status observation 和冻结 cycle。启动后等待至少两个
   **post-restart** scheduler cycles。`assert --phase restarted` 同时读取 blocked 与 stopped receipt，要求
   新 PID 不同，并以 stopped 的冻结计数为基准要求至少 `+2`；它不从 stop 前的旧 daemon cycle
   推断 post-restart 证据。

   ```bash
   "${MAM[@]}" service stop
   wait_fixture_service_stopped
   "$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" record-stopped \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --baseline "$FIXTURE_ROOT/receipts/blocked.json" --service-status "$FIXTURE_STOP_STATUS" \
     --receipt "$FIXTURE_ROOT/receipts/stopped.json"
   "${MAM[@]}" service start --manager "$ROOT_MANAGER"
   # Root remains active. Wait until at least two post-restart scheduler cycles have run.
   "$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" assert \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --phase restarted --baseline "$FIXTURE_ROOT/receipts/blocked.json" \
     --stopped-baseline "$FIXTURE_ROOT/receipts/stopped.json" \
     --receipt "$FIXTURE_ROOT/receipts/restarted.json"
   ```

3. root 正常结束当前 turn。fixture daemon 只在 root 确为 idle 后发送一次带 fixture TASK-ID/JOB-ID 和精确错误
   的 `[MAM Message]`。收到该消息的新 root turn 先目视确认 marker，随后运行 `assert --phase delivered`；
   它把 `restarted.json` 的 TASK-ID、JOB-ID、Manager、child、source signature 和 escalation signature 与
   当前 state 精确比对，并要求唯一 Manager escalation `accepted`、`attempts == 1`，source 仍为
   `blocked`、`attempts == 1`。人类 attestation 必须包含 `[MAM Message]`、两个 ID 和精确 rejection。

   ```bash
   "$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" assert \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --phase delivered --baseline "$FIXTURE_ROOT/receipts/restarted.json" \
     --manager-attestation "[MAM Message] TASK-ID $TASK_ID JOB-ID $JOB_ID ERROR: $EXACT_REJECTION received in the new idle-root turn" \
     --receipt "$FIXTURE_ROOT/receipts/delivered.json"
   ```

4. root 在该新 turn 先恢复上面记录的 `SOURCE_ROOT`、`SOURCE_PYTHON`、`MAM`、`FIXTURE_ROOT` 和 ID 值，
   再核对 child 状态/报告，随后用 parent-native `collaboration.followup_task` 让同一 child **只**在
   `FIXTURE_ROOT/project` 中运行下面两条受控命令。root 的消息要包含同一组 source 路径和 `MAM` array；
   第一条是真实 `mam job archive`；第二条不执行
   archive 或发送消息，只读取 fixture task/job record，核对 archive state 和固定 note，并写入明确 child
   attestation。不得以非空 report 推断 child 做过 archive。

   ```bash
   "${MAM[@]}" job archive "$JOB_ID" --note "$CHILD_ARCHIVE_NOTE"
   "$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" record-child-archive \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --attestation "child received collaboration.followup_task and ran mam job archive $JOB_ID --note '$CHILD_ARCHIVE_NOTE' for TASK-ID $TASK_ID" \
     --receipt "$FIXTURE_ROOT/receipts/child-archive.json"
   ```

   root 等待一个 fixture cycle 后运行 `assert-archived`。它强制绑定 `delivered.json`：按两条 signature 精确
   定位 history source/escalation，重验 blocked source 的 error/attempts 与 escalation 的 source_event、
   error、action、accepted/attempts/accepted_at，要求实际 runtime 写出的
   `condition changed or resolved` resolution，并拒绝仍含 baseline 两条 signature 的 active event。它还读取
   `child-archive.json`，将 child/TASK-ID/JOB-ID/`mam job archive` attestation 与 job archive note/state
   精确比对。

   ```bash
   "$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" assert-archived \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" --manager "$ROOT_MANAGER" --child "$NATIVE_CHILD" \
     --baseline "$FIXTURE_ROOT/receipts/delivered.json" \
     --child-archive-receipt "$FIXTURE_ROOT/receipts/child-archive.json" \
     --receipt "$FIXTURE_ROOT/receipts/archived.json"
   ```

   root 在 archive fixture task 前保持当前 turn active。job 已 archive 且 child 转 idle 后可能形成普通
   `task_ready`，应由紧随其后的 task archive 清除，不能让它在这次验收中成为第二条 idle-time 通知。

5. root 将 receipts 复制或汇编到 fixture 外的 evidence 文件，停止 fixture service、等待其实际退出、archive
   fixture task，最后才运行 guarded `cleanup`。`cleanup` 要求 service disabled、fixture task/job 已
   archived、外部 evidence 文件存在且不在 fixture root 内；它只删除 marker 所有的 fixture root。若任一点
   失败，保留 fixture 并由 root 处理。

   ```bash
   cd "$FIXTURE_ROOT/project"
   "${MAM[@]}" service stop
   wait_fixture_service_stopped
   "$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" verify-source \
     --root "$FIXTURE_ROOT" --phase after-stop \
     --receipt "$FIXTURE_ROOT/receipts/source-after-stop.json"
   "${MAM[@]}" task archive "$TASK_ID" --note 'native-v2 fallback fixture completed and receipts retained'
   "$SOURCE_PYTHON" -I "$SOURCE_ROOT/scripts/native_v2_fallback_acceptance.py" cleanup \
     --root "$FIXTURE_ROOT" --task "$TASK_ID" --job "$JOB_ID" \
     --external-evidence /absolute/path/outside-fixture/native-v2-fallback-evidence.json \
     --confirm REMOVE_NATIVE_V2_FIXTURE
   ```

整个验收不运行 `scripts/install.sh`，不安装任何内容，不重启 App Server 或生产 daemon，也不声称 direct
native-v2 input 已恢复。
