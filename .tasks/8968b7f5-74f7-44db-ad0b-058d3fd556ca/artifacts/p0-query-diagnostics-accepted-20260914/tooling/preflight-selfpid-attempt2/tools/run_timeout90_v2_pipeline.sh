#!/usr/bin/env bash
# One bounded C2 recovery: preflight, J smoke/acceptance/pair, then S smoke/acceptance/pair.
set -euo pipefail

TASK_ID=8968b7f5-74f7-44db-ad0b-058d3fd556ca
C_ROOT=/mnt/public/xcj/Projects/state-vla
RUN="$C_ROOT/workspace/$TASK_ID/c2-query-diagnostic"
RECORDS="$C_ROOT/workspace/$TASK_ID/records"
TOOLS="$RECORDS/tools/query-diagnostic-c2-timeout90-v2-preflight-selfpid-attempt2"
STATUS="$RECORDS/c2-query-diagnostic-timeout90-v2-preflight-selfpid-attempt2-pipeline-status.json"
OUTER_LOG="$RECORDS/c2-query-diagnostic-timeout90-v2-preflight-selfpid-attempt2-pipeline.log"
STARTED_AT="$(date -u --iso-8601=seconds)"
PHASE="preflight"

[[ ! -e "$STATUS" ]] || { echo "refusing to reuse timeout90 pipeline status: $STATUS" >&2; exit 73; }
finish() {
  code=$?
  "$RUN/robot-bridge/.venv/bin/python" "$TOOLS/write_timeout90_pipeline_status.py" \
    --output "$STATUS" --phase "$PHASE" --exit-code "$code" --started-at "$STARTED_AT" --log "$OUTER_LOG" || true
  trap - EXIT
  exit "$code"
}
trap finish EXIT

"$RUN/robot-bridge/.venv/bin/python" "$TOOLS/c2_timeout90_v2_preflight.py" \
  --output "$RECORDS/c2-query-diagnostic-timeout90-v2-preflight-selfpid-attempt2-preflight.json"

PHASE="full_t_plus_1_smoke"

"$TOOLS/launch_query_diagnostic_smoke_timeout90_v2.sh" "full_t_plus_1" "query_diagnostic_full_t_plus_1_smoke_20260914_timeout90_v2"

PHASE="full_t_plus_1_acceptance"

"$RUN/robot-bridge/.venv/bin/python" "$TOOLS/validate_completed_diagnostic_smoke.py" \
  --variant "full_t_plus_1" \
  --config "$RECORDS/manifests-timeout90-v2/full_t_plus_1/scheduler_config.yaml" \
  --diagnostic-dir "$RECORDS/diagnostics-timeout90-v2/full_t_plus_1" \
  --result-dir "$RUN/RMBench/eval_result/query_diagnostic_c2_20260914_timeout90_v2/query_diagnostic_full_t_plus_1_smoke_20260914_timeout90_v2" \
  --validator "$RUN/robot-bridge/scripts/validate_query_diagnostic.py" \
  --output "$RECORDS/timeout90-v2-preflight-selfpid-attempt2-smoke-acceptance-full_t_plus_1.json"

PHASE="full_t_plus_1_logging_off_on_pair"

"$TOOLS/run_query_diagnostic_pair_timeout90_v2.sh" "full_t_plus_1"

PHASE="serial_lag30_smoke"

"$TOOLS/launch_query_diagnostic_smoke_timeout90_v2.sh" "serial_lag30" "query_diagnostic_serial_lag30_smoke_20260914_timeout90_v2"

PHASE="serial_lag30_acceptance"

"$RUN/robot-bridge/.venv/bin/python" "$TOOLS/validate_completed_diagnostic_smoke.py" \
  --variant "serial_lag30" \
  --config "$RECORDS/manifests-timeout90-v2/serial_lag30/scheduler_config.yaml" \
  --diagnostic-dir "$RECORDS/diagnostics-timeout90-v2/serial_lag30" \
  --result-dir "$RUN/RMBench/eval_result/query_diagnostic_c2_20260914_timeout90_v2/query_diagnostic_serial_lag30_smoke_20260914_timeout90_v2" \
  --validator "$RUN/robot-bridge/scripts/validate_query_diagnostic.py" \
  --output "$RECORDS/timeout90-v2-preflight-selfpid-attempt2-smoke-acceptance-serial_lag30.json"

PHASE="serial_lag30_logging_off_on_pair"

"$TOOLS/run_query_diagnostic_pair_timeout90_v2.sh" "serial_lag30"

PHASE="completed"
