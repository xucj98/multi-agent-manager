#!/usr/bin/env bash
# Install this small entry at the primary checkout's .local/create_worktree.sh.
set -euo pipefail
if [[ $# != 3 ]]; then
  echo 'usage: .local/create_worktree.sh BASE_COMMIT BRANCH WORKSPACE_ROOT' >&2
  exit 2
fi
source_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
cd "$source_root"
base=$(git rev-parse --verify "$1^{commit}")
python=/mnt/public/xcj/cache/shared-python/cpython-3.10.19-linux-x86_64-gnu/bin/python3.10
git show "$base:scripts/create_worktree.sh" | bash -s -- "$base" "$2" "$3" "$python"
