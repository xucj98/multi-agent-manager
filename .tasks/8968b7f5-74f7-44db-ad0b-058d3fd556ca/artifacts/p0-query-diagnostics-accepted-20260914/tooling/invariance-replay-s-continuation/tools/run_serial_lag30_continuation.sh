#!/usr/bin/env bash
# Frozen S-only continuation. Invoke only after an explicit Manager approval.
set -euo pipefail

TASK_ID=8968b7f5-74f7-44db-ad0b-058d3fd556ca
C_ROOT=/mnt/public/xcj/Projects/state-vla
RUN="$C_ROOT/workspace/$TASK_ID/c2-query-diagnostic"
RECORDS="$C_ROOT/workspace/$TASK_ID/records"
TOOLS="$RECORDS/tools/query-diagnostic-c2-timeout90-v2-invariance-replay-s-continuation"
ORIGINAL_TOOLS="$RECORDS/tools/query-diagnostic-c2-timeout90-v2-preflight-selfpid-attempt2"
RESULT_RUN=query_diagnostic_serial_lag30_smoke_20260914_timeout90_v2
RESULT_DIR="$RUN/RMBench/eval_result/query_diagnostic_c2_20260914_timeout90_v2/$RESULT_RUN"
DIAGNOSTIC_DIR="$RECORDS/diagnostics-timeout90-v2/serial_lag30"
STATUS="$RECORDS/c2-query-diagnostic-timeout90-v2-invariance-replay-s-pipeline-status.json"
OUTER_LOG="$RECORDS/c2-query-diagnostic-timeout90-v2-invariance-replay-s-pipeline.log"
STARTED_AT="$(date -u --iso-8601=seconds)"
PHASE=serial_lag30_preflight

[[ ! -e "$STATUS" ]] || { echo "refusing to reuse S continuation pipeline status: $STATUS" >&2; exit 73; }
[[ ! -e "$OUTER_LOG" ]] || { echo "refusing to reuse S continuation outer log: $OUTER_LOG" >&2; exit 73; }
exec > >(tee "$OUTER_LOG") 2>&1
finish() {
  code=$?
  "$RUN/robot-bridge/.venv/bin/python" "$ORIGINAL_TOOLS/write_timeout90_pipeline_status.py" --output "$STATUS" --phase "$PHASE" --exit-code "$code" --started-at "$STARTED_AT" --log "$OUTER_LOG" || true
  trap - EXIT
  exit "$code"
}
trap finish EXIT

"$RUN/robot-bridge/.venv/bin/python" "$TOOLS/c2_serial_lag30_continuation_preflight.py" --output "$RECORDS/c2-query-diagnostic-timeout90-v2-invariance-replay-s-preflight.json"
PHASE=serial_lag30_smoke
"$ORIGINAL_TOOLS/launch_query_diagnostic_smoke_timeout90_v2.sh" serial_lag30 "$RESULT_RUN"
PHASE=serial_lag30_acceptance
"$RUN/robot-bridge/.venv/bin/python" "$ORIGINAL_TOOLS/validate_completed_diagnostic_smoke.py" --variant serial_lag30 --config "$RECORDS/manifests-timeout90-v2/serial_lag30/scheduler_config.yaml" --diagnostic-dir "$DIAGNOSTIC_DIR" --result-dir "$RESULT_DIR" --validator "$RUN/robot-bridge/scripts/validate_query_diagnostic.py" --output "$RECORDS/timeout90-v2-invariance-replay-s-smoke-acceptance-serial_lag30.json"
PHASE=serial_lag30_logging_invariance_and_saved_replay_pair
"$TOOLS/run_serial_lag30_pair_invariance_replay.sh"
PHASE=completed
