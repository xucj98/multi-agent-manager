#!/usr/bin/env bash
# Local three-argument wrapper supplies the persistent Python as argument four.
set -euo pipefail
fail() {
  printf '%s\n' "$1" >&2
  exit 2
}
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
[[ "$workspace" = /* && "$workspace" != / && "$workspace" != *'/../'* ]] || fail "workspace must be a normalized non-root absolute path: $workspace"
[[ "$(realpath -m -- "$workspace")" = "$workspace" ]] || fail "workspace must not contain path aliases: $workspace"
[[ "$branch" == task/* ]] || fail "branch must start with task/: $branch"
[[ "$python" = /* && -x "$python" ]] || fail "shared Python must be an executable absolute path: $python"
if ! python_version=$("$python" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null); then
  fail "shared Python must be a runnable Python >= 3.10: $python"
fi
if [[ "$python_version" =~ ^([0-9]+)\.([0-9]+)$ ]]; then
  python_major=${BASH_REMATCH[1]}
  python_minor=${BASH_REMATCH[2]}
else
  fail "shared Python must be a runnable Python >= 3.10: $python"
fi
if (( python_major < 3 || (python_major == 3 && python_minor < 10) )); then
  fail "shared Python must be a runnable Python >= 3.10: $python"
fi
base=$(git -C "$source_root" rev-parse --verify "$base^{commit}")
worktree="$workspace/multi-agent-manager"
mkdir -p -- "$workspace"
if [[ -e "$worktree" || -L "$worktree" ]]; then
  [[ ! -L "$worktree" && -f "$worktree/.git" && ! -L "$worktree/.git" ]] || fail "existing worktree must have a regular .git file: $worktree"
  [[ "$(git -C "$worktree" rev-parse --path-format=absolute --git-common-dir)" = "$source_root/.git" ]] || fail "existing worktree belongs to another source repository: $worktree"
  [[ "$(git -C "$worktree" symbolic-ref --short HEAD)" = "$branch" ]] || fail "existing worktree branch differs from requested branch: $worktree"
else
  git -C "$source_root" worktree add -b "$branch" "$worktree" "$base"
fi
source_readme="$source_root/.local/README.md"
local_directory="$worktree/.local"
local_readme="$local_directory/README.md"
if [[ -f "$source_readme" ]]; then
  if [[ ! -e "$local_directory" && ! -L "$local_directory" ]]; then
    mkdir -- "$local_directory"
  fi
  if [[ -d "$local_directory" && ! -L "$local_directory" && ! -e "$local_readme" && ! -L "$local_readme" ]]; then
    ln -s -- "$source_readme" "$local_readme"
  fi
fi
[[ ! -L "$worktree/.venv" ]] || fail "worktree virtual environment must not be a symlink: $worktree/.venv"
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
