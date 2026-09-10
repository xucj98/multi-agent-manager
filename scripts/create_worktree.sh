#!/usr/bin/env bash
# Local three-argument wrapper supplies the persistent Python as argument four.
set -euo pipefail
if [[ $# != 4 ]]; then
  echo 'usage: create_worktree.sh BASE_COMMIT BRANCH WORKSPACE_ROOT SHARED_PYTHON' >&2
  exit 2
fi
base=$1
branch=$2
workspace=$3
python=$4
source_root=$(git rev-parse --path-format=absolute --git-common-dir)
source_root=${source_root%/.git}
[[ "$workspace" = /* && "$workspace" != / && "$workspace" != *'/../'* ]] || exit 2
[[ "$(realpath -m -- "$workspace")" = "$workspace" ]] || exit 2
[[ "$branch" == task/* && -x "$python" && "$python" == /mnt/public/* ]] || exit 2
base=$(git -C "$source_root" rev-parse --verify "$base^{commit}")
worktree="$workspace/multi-agent-manager"
mkdir -p -- "$workspace"
if [[ -e "$worktree" || -L "$worktree" ]]; then
  [[ ! -L "$worktree" && -f "$worktree/.git" && ! -L "$worktree/.git" ]] || exit 2
  [[ "$(git -C "$worktree" rev-parse --path-format=absolute --git-common-dir)" = "$source_root/.git" ]] || exit 2
  [[ "$(git -C "$worktree" symbolic-ref --short HEAD)" = "$branch" ]] || exit 2
else
  git -C "$source_root" worktree add -b "$branch" "$worktree" "$base"
fi
[[ ! -L "$worktree/.venv" ]] || exit 2
# Ignore the independent environment even when the selected base predates it.
git -C "$worktree" check-ignore -q .venv/ || {
  echo 'base must ignore .venv/; worktree retained for diagnosis' >&2
  exit 2
}
"$python" -m venv "$worktree/.venv"
"$worktree/.venv/bin/python" -m pip install --no-deps --editable "$worktree"
(
  cd "$worktree"
  "$worktree/.venv/bin/python" -B "$worktree/.venv/bin/mam" task list
)
