#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
    echo "usage: $0 /absolute/path/to/multi-agent-manager" >&2
    exit 64
fi

checkout="$1"
if [[ "$checkout" != /* || ! -d "$checkout" ]]; then
    echo "checkout must be an existing absolute directory" >&2
    exit 64
fi
checkout="$(cd "$checkout" && pwd -P)"
if [[ ! -f "$checkout/pyproject.toml" || ! -d "$checkout/tests" ]]; then
    echo "checkout is not a multi-agent-manager source checkout: $checkout" >&2
    exit 64
fi

if ! command -v pipx >/dev/null; then
    echo "pipx is required; install it before running this script" >&2
    exit 127
fi

echo "Installing MAM from $checkout"
pipx install --force "$checkout"

pipx_bin_dir="$(pipx environment --value PIPX_BIN_DIR 2>/dev/null || true)"
if [[ -z "$pipx_bin_dir" ]]; then
    pipx_bin_dir="${PIPX_BIN_DIR:-$HOME/.local/bin}"
fi
mam_bin="$pipx_bin_dir/mam"
if [[ ! -x "$mam_bin" ]]; then
    echo "pipx installed MAM but its mam entrypoint was not found at $mam_bin" >&2
    exit 1
fi

mam_python="$(sed -n '1{s/^#!//;p;}' "$mam_bin")"
if [[ ! -x "$mam_python" ]]; then
    echo "the installed mam entrypoint does not reference an executable Python interpreter" >&2
    exit 1
fi

"$mam_bin" --help >/dev/null
"$mam_python" -B -m unittest discover -s "$checkout/tests" -v
"$mam_python" -m multi_agent_manager.wait_compat
