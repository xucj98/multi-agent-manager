#!/usr/bin/env bash
# Copy this entry to the primary checkout's ignored .local/create_worktree.sh.
# Set its Python there (or MAM_SHARED_PYTHON in that deployment); this template
# intentionally has no host-specific interpreter path.
set -euo pipefail
if [[ $# != 3 ]]; then
  echo 'usage: .local/create_worktree.sh BASE_COMMIT BRANCH WORKSPACE_ROOT' >&2
  exit 2
fi
source_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$source_root"
base=$(git rev-parse --verify "$1^{commit}")
python=${MAM_SHARED_PYTHON:-}
if [[ -z "$python" ]]; then
  echo 'configure a local Python >=3.10 in .local/create_worktree.sh or MAM_SHARED_PYTHON' >&2
  exit 2
fi
git show "$base:scripts/create_worktree.sh" | bash -s -- "$base" "$2" "$3" "$python"
