#!/usr/bin/env bash
# Frozen task-owned C2 launcher. It creates no source-tree configuration.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 {full_t_plus_1|serial_lag30} RESULT_RUN" >&2
  exit 64
fi

VARIANT=$1
RESULT_RUN=$2
TASK_ID=8968b7f5-74f7-44db-ad0b-058d3fd556ca
C_ROOT=/mnt/public/xcj/Projects/state-vla
RUN="$C_ROOT/workspace/$TASK_ID/c2-query-diagnostic"
RECORDS="$C_ROOT/workspace/$TASK_ID/records"
TOOLS="$RECORDS/tools/query-diagnostic-c2-timeout90-v2"
EXPERIMENT_GROUP=query_diagnostic_c2_20260914_timeout90_v2
GPU=6

case "$VARIANT" in
  full_t_plus_1)
    RUN_ID=query_diagnostic_full_t_plus_1
    EXPECTED_RESULT_RUN=query_diagnostic_full_t_plus_1_smoke_20260914_timeout90_v2
    CHECKPOINT_PARENT="$C_ROOT/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0"
    CHECKPOINT_ALIAS=CheckpointFull
    ;;
  serial_lag30)
    RUN_ID=query_diagnostic_serial_lag30
    EXPECTED_RESULT_RUN=query_diagnostic_serial_lag30_smoke_20260914_timeout90_v2
    CHECKPOINT_PARENT="$C_ROOT/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0"
    CHECKPOINT_ALIAS=CheckpointSerial
    ;;
  *)
    echo "unsupported variant: $VARIANT" >&2
    exit 64
    ;;
esac

if [[ "$RESULT_RUN" != "$EXPECTED_RESULT_RUN" ]]; then
  echo "result run must be the frozen fresh leaf: $EXPECTED_RESULT_RUN" >&2
  exit 64
fi

RESULT_DIR="$RUN/RMBench/eval_result/$EXPERIMENT_GROUP/$RESULT_RUN"
DIAGNOSTIC_DIR="$RECORDS/diagnostics-timeout90-v2/$VARIANT"
MANIFEST="$RECORDS/manifests-timeout90-v2/$VARIANT/runner_input_manifest.json"
SCHEDULER_CONFIG="$RECORDS/manifests-timeout90-v2/$VARIANT/scheduler_config.yaml"

for item in "$MANIFEST" "$SCHEDULER_CONFIG" "$CHECKPOINT_PARENT/20000"; do
  [[ -e "$item" ]] || { echo "required input missing: $item" >&2; exit 66; }
done
for spec in \
  "$RUN/RMBench:f401f5279c95451eb424ac98b831bab5552b2120" \
  "$RUN/robot-bridge:e147f600dc4329f330a6e2eb0335150b5b3093a3" \
  "$RUN/openpi:bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6"; do
  root=${spec%%:*}
  commit=${spec##*:}
  [[ "$(git -C "$root" rev-parse HEAD)" == "$commit" ]] || { echo "unexpected source commit: $root" >&2; exit 65; }
  [[ -z "$(git -C "$root" status --porcelain)" ]] || { echo "source worktree is dirty: $root" >&2; exit 65; }
done
if [[ -e "$RESULT_DIR" ]] || [[ -e "$DIAGNOSTIC_DIR" ]]; then
  echo "refusing to reuse a result or diagnostic leaf" >&2
  exit 73
fi
if ss -ltn 2>/dev/null | grep -Eq ':(19460|19462)\b'; then
  echo "required C2 ports 19460 or 19462 are already listening" >&2
  exit 75
fi

export CUDA_VISIBLE_DEVICES=$GPU
export SAPIEN_RENDER_DEVICE=cuda:0
export VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json
export PYTHONPATH="$RUN/robot-bridge:$RUN/openpi/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"
export RB_RMBENCH_ROOT="$RUN/RMBench"
export RB_RMBENCH_PY="$RUN/RMBench/.venv/bin/python"
export RB_OPENPI_POLICY_DIR="$CHECKPOINT_PARENT/20000"
"$RUN/robot-bridge/.venv/bin/python" "$TOOLS/validate_timeout90_config.py" \
  --config "$SCHEDULER_CONFIG" \
  --expected-directory "$DIAGNOSTIC_DIR" \
  --output "$RECORDS/timeout90-v2-config-validation-${VARIANT}.json"

ROBOT_COMMAND="env VK_ICD_FILENAMES=$VK_ICD_FILENAMES WARP_CACHE_PATH=$RUN/RMBench/.local/warp-cache/$EXPERIMENT_GROUP/runs/{result_run}/robot $RUN/robot-bridge/.venv/bin/python $RUN/robot-bridge/scripts/run_robot_server.py --port 19460 --config configs/robot_controllers/rmbench_sim.yaml --host 127.0.0.1 --overrides params.rpc_timeout=600 params.startup_timeout=120 params.worker_log_path={run_dir}/processes/rmbench_sim_worker.stderr.log"
POLICY_COMMAND="env VK_ICD_FILENAMES=$VK_ICD_FILENAMES WARP_CACHE_PATH=$RUN/RMBench/.local/warp-cache/$EXPERIMENT_GROUP/runs/{result_run}/policy XLA_PYTHON_CLIENT_MEM_FRACTION=0.4 PYTHONPATH=$RUN/robot-bridge:$RUN/openpi/packages/openpi-client/src RB_OPENPI_POLICY_DIR=$CHECKPOINT_PARENT/20000 $RUN/openpi/.venv/bin/python $RUN/robot-bridge/scripts/run_policy_server.py --port 19462 --config configs/policy_backends/openpi.yaml --host 127.0.0.1"

printf 'launch variant=%s result_run=%s gpu=%s\n' "$VARIANT" "$RESULT_RUN" "$GPU"
printf 'manifest_sha256=%s\n' "$(sha256sum "$MANIFEST" | awk '{print $1}')"
printf 'scheduler_config_sha256=%s\n' "$(sha256sum "$SCHEDULER_CONFIG" | awk '{print $1}')"
printf 'policy_first_infer_timeout=90.0\n'
printf 'policy_subsequent_infer_timeout=30.0\n'

cd "$RUN/robot-bridge"
exec "$RUN/robot-bridge/.venv/bin/python" \
  "$RUN/robot-bridge/scripts/launch/rmbench_benchmark.py" \
  --manifest "$MANIFEST" \
  --run-id "$RUN_ID" \
  --result-run "$RESULT_RUN" \
  --experiment-group "$EXPERIMENT_GROUP" \
  --result-recorder "$RUN/RMBench/script/eval_diagnostics.py" \
  --mode smoke \
  --scheduler-config "$SCHEDULER_CONFIG" \
  --robot-url ws://127.0.0.1:19460 \
  --policy-url ws://127.0.0.1:19462 \
  --robot-command "$ROBOT_COMMAND" \
  --policy-command "$POLICY_COMMAND" \
  --gpu "$GPU" \
  --startup-timeout 660 \
  --reset-timeout 660 \
  --episode-timeout 3600 \
  --source-root "RMBench=$RUN/RMBench" \
  --source-root "$CHECKPOINT_ALIAS=$CHECKPOINT_PARENT" \
  --source-root "TaskRecords=$RECORDS"
