#!/usr/bin/env bash
# Run exactly one authorized logging-off/on pair from the completed v2 episode-0 record.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 {full_t_plus_1|serial_lag30}" >&2
  exit 64
fi

VARIANT=$1
TASK_ID=8968b7f5-74f7-44db-ad0b-058d3fd556ca
C_ROOT=/mnt/public/xcj/Projects/state-vla
RUN="$C_ROOT/workspace/$TASK_ID/c2-query-diagnostic"
RECORDS="$C_ROOT/workspace/$TASK_ID/records"
TOOLS="$RECORDS/tools/query-diagnostic-c2-timeout90-v2"
GPU=6

case "$VARIANT" in
  full_t_plus_1)
    CHECKPOINT_PARENT="/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/pi05_rmbench_put_back_block_full_t_plus_1/memory20k_e7e5ac54_put_back_full_t_plus_1_s0"
    RECORD="$RECORDS/diagnostics-timeout90-v2/full_t_plus_1/records/episode-000000-query-000001-seq-000001.json"
    OUTPUT="$RECORDS/pairs-timeout90-v2/full_t_plus_1/episode-000000-query-000001-seq-000001.json"
    ;;
  serial_lag30)
    CHECKPOINT_PARENT="/mnt/public/xcj/Projects/state-vla/openpi/checkpoints/pi05_rmbench_put_back_block_serial_lag30/memory20k_695bc51f_put_back_serial_lag30_s0"
    RECORD="$RECORDS/diagnostics-timeout90-v2/serial_lag30/records/episode-000000-query-000001-seq-000001.json"
    OUTPUT="$RECORDS/pairs-timeout90-v2/serial_lag30/episode-000000-query-000001-seq-000001.json"
    ;;
  *)
    echo "unsupported variant: $VARIANT" >&2
    exit 64
    ;;
esac

[[ -f "$RECORD" ]] || { echo "missing accepted v2 record: $RECORD" >&2; exit 66; }
[[ ! -e "$OUTPUT" ]] || { echo "refusing to overwrite pair receipt: $OUTPUT" >&2; exit 73; }
for spec in   "$RUN/RMBench:f401f5279c95451eb424ac98b831bab5552b2120"   "$RUN/robot-bridge:e147f600dc4329f330a6e2eb0335150b5b3093a3"   "$RUN/openpi:bc7603c5b2d3b9a58675f3cc351b49afcbf35bd6"; do
  root=${spec%%:*}
  commit=${spec##*:}
  [[ "$(git -C "$root" rev-parse HEAD)" == "$commit" ]] || { echo "unexpected source commit: $root" >&2; exit 65; }
  [[ -z "$(git -C "$root" status --porcelain)" ]] || { echo "source worktree is dirty: $root" >&2; exit 65; }
done
if ss -ltn 2>/dev/null | grep -Eq ':(19460|19462)\b'; then
  echo "C2 server port is unexpectedly listening before direct pair" >&2
  exit 75
fi

mkdir -p "$(dirname "$OUTPUT")"
export CUDA_VISIBLE_DEVICES=$GPU
export SAPIEN_RENDER_DEVICE=cuda:0
export VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.4
export PYTHONPATH="$RUN/robot-bridge:$RUN/openpi/packages/openpi-client/src${PYTHONPATH:+:$PYTHONPATH}"

exec "$RUN/openpi/.venv/bin/python" "$TOOLS/pair_query_diagnostic_logging.py"   --record "$RECORD"   --checkpoint "$CHECKPOINT_PARENT/20000"   --output "$OUTPUT"
