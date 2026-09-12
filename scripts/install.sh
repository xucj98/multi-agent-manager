#!/usr/bin/env bash
# Install this checkout and manage its project-local proactive wake scheduler.
# The detached daemon is owned by ``mam service``; this script never launches
# a shell supervisor or restarts Codex.
set -euo pipefail

readonly PATH_BEGIN='# >>> MAM PATH >>>'
readonly PATH_END='# <<< MAM PATH <<<'
readonly LEGACY_TRACE_BEGIN='# >>> MAM Codex App Server trace >>>'
readonly LEGACY_TRACE_END='# <<< MAM Codex App Server trace <<<'
readonly STARTUP_WAIT_ATTEMPTS=40
readonly STARTUP_WAIT_SECONDS=0.5

CHECKOUT_ROOT=''
MAM_ROOT=''
PROJECT_ROOT=''
LOCAL_BIN=''
MAM_BIN=''
SOURCE_PYTHON=''
INSTALLED_PYTHON=''
INSTALL_TMP=''
COMPATIBILITY_JSON=''
SERVICE_ERROR=''
SERVICE_STATE=''
SERVICE_MANAGER_ARGS=()

incomplete() {
    # Keep an unattended install transcript self-contained.  Individual tools
    # have already bounded/redacted external diagnostics before reaching here.
    printf 'MAM proactive wakeup installation: FAIL\n%s\n' "$*"
    return 1
}

repository_root() {
    local scripts
    scripts="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1
    cd -- "$scripts/.." && pwd -P
}

find_project_config() {
    local directory="$1"
    while :; do
        if [[ -f "$directory/.mam/env.json" ]]; then
            printf '%s\n' "$directory/.mam/env.json"
            return 0
        fi
        [[ "$directory" == / ]] && return 1
        directory="$(dirname -- "$directory")"
    done
}

validate_project_config() {
    local config_path="$1"
    python3 - "$config_path" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
    print(f"invalid project configuration: {exc}", file=sys.stderr)
    raise SystemExit(1)
if not isinstance(data, dict):
    print("invalid project configuration: expected a JSON object", file=sys.stderr)
    raise SystemExit(1)
for key in ("MAM_ROOT", "PROJECT_ROOT", "MAM_BRANCH"):
    if key not in data:
        print(f"invalid project configuration: missing {key}", file=sys.stderr)
        raise SystemExit(1)
if not isinstance(data["MAM_BRANCH"], str) or not data["MAM_BRANCH"]:
    print("invalid project configuration: MAM_BRANCH must be a non-empty string", file=sys.stderr)
    raise SystemExit(1)
resolved = {}
for key in ("MAM_ROOT", "PROJECT_ROOT"):
    raw = data[key]
    if not isinstance(raw, str) or not raw or "\x00" in raw or "\r" in raw or "\n" in raw:
        print(f"invalid project configuration: {key} must be a single-line absolute path", file=sys.stderr)
        raise SystemExit(1)
    candidate = Path(raw)
    if not candidate.is_absolute():
        print(f"invalid project configuration: {key} must be an absolute path", file=sys.stderr)
        raise SystemExit(1)
    try:
        candidate = candidate.resolve(strict=True)
    except OSError as exc:
        print(f"invalid project configuration: cannot resolve {key}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    if not candidate.is_dir():
        print(f"invalid project configuration: {key} must name a directory", file=sys.stderr)
        raise SystemExit(1)
    resolved[key] = candidate
try:
    resolved["MAM_ROOT"].relative_to(resolved["PROJECT_ROOT"])
except ValueError:
    print("invalid project configuration: MAM_ROOT must be inside PROJECT_ROOT", file=sys.stderr)
    raise SystemExit(1)
print(resolved["MAM_ROOT"])
print(resolved["PROJECT_ROOT"])
PY
}

same_git_repository() {
    local checkout_common state_common
    if ! checkout_common="$(git -C "$CHECKOUT_ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"; then
        incomplete 'the installation checkout is not a Git worktree'
        return 1
    fi
    if ! state_common="$(git -C "$MAM_ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"; then
        incomplete 'the configured MAM_ROOT is not a Git worktree'
        return 1
    fi
    if ! python3 - "$checkout_common" "$state_common" <<'PY'
from pathlib import Path
import sys
try:
    left = Path(sys.argv[1]).resolve(strict=True)
    right = Path(sys.argv[2]).resolve(strict=True)
except OSError:
    raise SystemExit(1)
raise SystemExit(0 if left == right else 1)
PY
    then
        incomplete 'the installation checkout and configured MAM_ROOT are not worktrees of the same Git repository'
        return 1
    fi
}

choose_source_python() {
    if [[ -x "$CHECKOUT_ROOT/.venv/bin/python" ]]; then
        SOURCE_PYTHON="$CHECKOUT_ROOT/.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        SOURCE_PYTHON="$(command -v python3)"
    else
        incomplete 'Python 3 is required to run the MAM test suite'
        return 1
    fi
    if ! "$SOURCE_PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
        incomplete 'MAM requires Python 3.10 or newer'
        return 1
    fi
}

run_tests() {
    # A clean checkout is tested before pipx has installed it.  Test code can
    # start a detached service from MAM_ROOT, where cwd no longer identifies
    # this checkout, so keep the checkout first in every test subprocess.
    local checkout_pythonpath="$CHECKOUT_ROOT"
    if [[ -n "${PYTHONPATH:-}" ]]; then
        checkout_pythonpath+=":$PYTHONPATH"
    fi
    printf 'MAM proactive wakeup: running checkout tests with %s\n' "$SOURCE_PYTHON"
    if ! (
        cd -- "$CHECKOUT_ROOT"
        export PYTHONPATH="$checkout_pythonpath"
        "$SOURCE_PYTHON" -B -m unittest discover -s tests -v
    ); then
        incomplete 'checkout tests failed; pipx and the existing scheduler were left untouched'
        return 1
    fi
}

prepare_local_bin() {
    if [[ -z "${HOME:-}" || "$HOME" != /* || "$HOME" == *$'\n'* || "$HOME" == *$'\r'* ]]; then
        incomplete 'HOME must be a single-line absolute path'
        return 1
    fi
    LOCAL_BIN="$HOME/.local/bin"
    if ! mkdir -p -- "$LOCAL_BIN"; then
        incomplete 'cannot create ~/.local/bin for the pipx launcher'
        return 1
    fi
    export PATH="$LOCAL_BIN:$PATH"
    MAM_BIN="$LOCAL_BIN/mam"
}

install_with_pipx() {
    if ! command -v pipx >/dev/null 2>&1; then
        incomplete 'pipx is required; install it first with: sudo apt install -y pipx'
        return 1
    fi
    printf 'MAM proactive wakeup: installing current checkout through pipx\n'
    if ! PIPX_BIN_DIR="$LOCAL_BIN" pipx install --force "$CHECKOUT_ROOT"; then
        incomplete 'pipx could not install the current checkout; the existing scheduler was not stopped'
        return 1
    fi
    if [[ ! -x "$MAM_BIN" ]]; then
        incomplete 'pipx completed without creating ~/.local/bin/mam'
        return 1
    fi
    if ! env -u CODEX_THREAD_ID "$MAM_BIN" --help >/dev/null 2>&1; then
        incomplete '~/.local/bin/mam is not runnable after the pipx installation'
        return 1
    fi
}

update_startup_file() {
    local target="$1" kind="$2" directory temporary backup changed
    if [[ -e "$target" && (! -f "$target" || -L "$target") ]]; then
        incomplete "refusing to modify non-regular shell startup file: $target"
        return 1
    fi
    directory="$(dirname -- "$target")"
    if ! mkdir -p -- "$directory"; then
        incomplete "cannot create shell startup directory: $directory"
        return 1
    fi
    if [[ ! -e "$target" ]]; then
        (umask 077; : > "$target") || {
            incomplete "cannot create shell startup file: $target"
            return 1
        }
    fi
    if ! temporary="$(mktemp -- "$directory/.${target##*/}.mam-path.XXXXXX")"; then
        incomplete "cannot prepare a PATH update for $target"
        return 1
    fi
    if ! changed="$(python3 - "$target" "$temporary" "$kind" "$PATH_BEGIN" "$PATH_END" "$LEGACY_TRACE_BEGIN" "$LEGACY_TRACE_END" <<'PY'
from pathlib import Path
import os
import stat
import sys

source, destination = map(Path, sys.argv[1:3])
kind, path_begin, path_end, trace_begin, trace_end = sys.argv[3:]
legacy_trace = [
    trace_begin,
    'if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then',
    '    export PATH="$HOME/.local/bin:$PATH"',
    'fi',
    'export RUST_LOG="off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info"',
    'export LOG_FORMAT=json',
    trace_end,
]
path_block = (
    [
        path_begin,
        'if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then',
        '    export PATH="$HOME/.local/bin:$PATH"',
        'fi',
        path_end,
    ]
    if kind == "bash"
    else [
        path_begin,
        'case ":$PATH:" in',
        '    *":$HOME/.local/bin:"*) ;;',
        '    *) export PATH="$HOME/.local/bin:$PATH" ;;',
        'esac',
        path_end,
    ]
)
try:
    raw = source.read_bytes()
    text = raw.decode("utf-8")
except (OSError, UnicodeDecodeError) as exc:
    print(f"cannot read {source}: {exc}", file=sys.stderr)
    raise SystemExit(1)
newline = "\r\n" if b"\r\n" in raw else "\n"
lines = text.splitlines(keepends=True)

def value(line):
    return line.rstrip("\r\n")

def remove_exact(items, begin, end, expected, label):
    starts = [index for index, line in enumerate(items) if value(line) == begin]
    ends = [index for index, line in enumerate(items) if value(line) == end]
    if not starts and not ends:
        return items
    if len(starts) != 1 or len(ends) != 1 or starts[0] > ends[0]:
        raise ValueError(f"incomplete or duplicate MAM {label} marker block in {source}")
    start, finish = starts[0], ends[0]
    actual = [value(line) for line in items[start : finish + 1]]
    if actual != expected:
        raise ValueError(f"refusing to replace a non-exact MAM-owned {label} block in {source}")
    return items[:start] + items[finish + 1 :]

try:
    # This is the exact block emitted by the previous trace-based installer.
    # It is the only obsolete trace content this installer may remove.
    lines = remove_exact(lines, trace_begin, trace_end, legacy_trace, "trace")
    lines = remove_exact(lines, path_begin, path_end, path_block, "PATH")
except ValueError as exc:
    print(str(exc), file=sys.stderr)
    raise SystemExit(1)

insert_at = len(lines)
if kind == "bash":
    for index, line in enumerate(lines):
        stripped = value(line).strip()
        if stripped in {
            '[ -z "$PS1" ] && return',
            '[[ -z "$PS1" ]] && return',
            '[[ $- != *i* ]] && return',
            '[ "$-" != "${-#*i}" ] || return',
        } or stripped.startswith(("case $- in", 'case "$-" in')):
            insert_at = index
            break
block = [line + newline for line in path_block]
if insert_at and not lines[insert_at - 1].endswith(("\n", "\r")):
    lines[insert_at - 1] += newline
updated = "".join(lines[:insert_at] + block + lines[insert_at:])
try:
    metadata = source.stat()
    with destination.open("w", encoding="utf-8", newline="") as handle:
        handle.write(updated)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(destination, stat.S_IMODE(metadata.st_mode))
    try:
        os.chown(destination, metadata.st_uid, metadata.st_gid)
    except PermissionError:
        pass
except OSError as exc:
    print(f"cannot prepare {source}: {exc}", file=sys.stderr)
    raise SystemExit(1)
print("unchanged" if updated == text else "changed")
PY
)"; then
        rm -f -- "$temporary"
        incomplete "cannot safely update shell PATH setup in $target"
        return 1
    fi
    if [[ "$changed" == unchanged ]]; then
        rm -f -- "$temporary"
        return 0
    fi
    backup="${target}.mam-path.$(date -u +%Y%m%dT%H%M%SZ).$$.bak"
    if ! cp -p -- "$target" "$backup"; then
        rm -f -- "$temporary"
        incomplete "cannot create a backup before updating $target"
        return 1
    fi
    if ! mv -f -- "$temporary" "$target"; then
        rm -f -- "$temporary"
        incomplete "cannot update $target; restore with: cp -p -- $backup $target"
        return 1
    fi
    printf 'MAM proactive wakeup: persistent PATH updated in %s (backup: %s)\n' "$target" "$backup"
}

persist_local_bin_path() {
    local login_file
    update_startup_file "$HOME/.bashrc" bash || return 1
    if [[ -e "$HOME/.bash_profile" ]]; then
        login_file="$HOME/.bash_profile"
    elif [[ -e "$HOME/.bash_login" ]]; then
        login_file="$HOME/.bash_login"
    else
        login_file="$HOME/.profile"
    fi
    update_startup_file "$login_file" login
}

resolve_installed_python() {
    local pipx_home
    if ! pipx_home="$(pipx environment --value PIPX_HOME 2>/dev/null)"; then
        incomplete 'cannot identify the pipx environment for the installed MAM interpreter'
        return 1
    fi
    if [[ -z "$pipx_home" || "$pipx_home" != /* || "$pipx_home" == *$'\n'* || "$pipx_home" == *$'\r'* ]]; then
        incomplete 'pipx returned an invalid PIPX_HOME path'
        return 1
    fi
    INSTALLED_PYTHON="$pipx_home/venvs/multi-agent-manager/bin/python"
    if [[ ! -x "$INSTALLED_PYTHON" ]]; then
        incomplete 'pipx did not provide the MAM virtual-environment interpreter'
        return 1
    fi
}

validate_explicit_manager() {
    if [[ -z "${MAM_SERVICE_MANAGER:-}" ]]; then
        return 0
    fi
    if ! "$INSTALLED_PYTHON" - "$MAM_SERVICE_MANAGER" <<'PY'
import sys
import uuid
try:
    value = sys.argv[1]
    if str(uuid.UUID(value)) != value:
        raise ValueError
except (IndexError, ValueError):
    raise SystemExit(1)
PY
    then
        incomplete 'MAM_SERVICE_MANAGER must be a canonical AGENT-ID'
        return 1
    fi
    SERVICE_MANAGER_ARGS=(--manager "$MAM_SERVICE_MANAGER")
}

create_install_tmp() {
    if ! INSTALL_TMP="$(mktemp -d "${TMPDIR:-/tmp}/mam-install.XXXXXX")"; then
        incomplete 'cannot create a private directory for installation acceptance'
        return 1
    fi
    chmod 700 -- "$INSTALL_TMP" || true
    trap cleanup_install_tmp EXIT
}

cleanup_install_tmp() {
    if [[ -n "$INSTALL_TMP" && -d "$INSTALL_TMP" && ! -L "$INSTALL_TMP" ]]; then
        rm -rf -- "$INSTALL_TMP"
    fi
}

bounded_diagnostic() {
    python3 - "$@" <<'PY'
from pathlib import Path
import re
import sys

parts = []
for raw in sys.argv[1:]:
    path = Path(raw)
    try:
        if path.is_file() and not path.is_symlink():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        pass
text = " ".join(" ".join(parts).split())[:1400]
text = re.sub(r"(?i)\b(token|secret|password|api[_-]?key)\s*=\s*[^\s,;]+", r"\1=<redacted>", text)
print(text)
PY
}

validate_compatibility_json() {
    "$INSTALLED_PYTHON" - "$1" <<'PY'
import json
from pathlib import Path
import sys
try:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except (OSError, UnicodeDecodeError, ValueError):
    raise SystemExit(1)
if not isinstance(data, dict) or not isinstance(data.get("socket_path"), str):
    raise SystemExit(1)
if not Path(data["socket_path"]).is_absolute() or not isinstance(data.get("capabilities"), dict):
    raise SystemExit(1)
if data["capabilities"].get("model_requests") != 0:
    raise SystemExit(1)
PY
}

run_lightweight_probe() {
    local output="$INSTALL_TMP/compatibility.json" errors="$INSTALL_TMP/compatibility.stderr" detail
    printf 'MAM proactive wakeup: running non-model App Server API compatibility probe\n'
    if ! (cd -- "$PROJECT_ROOT" && env -u CODEX_THREAD_ID "$INSTALLED_PYTHON" -B -m multi_agent_manager.wake_compat --json >"$output" 2>"$errors"); then
        detail="$(bounded_diagnostic "$output" "$errors")"
        incomplete "the App Server API compatibility probe failed${detail:+: $detail}"
        return 1
    fi
    if ! validate_compatibility_json "$output"; then
        detail="$(bounded_diagnostic "$output" "$errors")"
        incomplete "the App Server API compatibility probe returned invalid evidence${detail:+: $detail}"
        return 1
    fi
    COMPATIBILITY_JSON="$output"
    printf 'MAM proactive wakeup: non-model App Server API compatibility PASS\n'
}

validate_liveprobe_evidence() {
    "$INSTALLED_PYTHON" - "$1" <<'PY'
import json
from pathlib import Path
import sys
try:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except (OSError, UnicodeDecodeError, ValueError):
    raise SystemExit(1)
checks = data.get("checks") if isinstance(data, dict) else None
if data.get("status") != "passed" or data.get("model_turns") != 6 or not isinstance(checks, dict):
    raise SystemExit(1)
if not all(checks.get(key) is True for key in ("all_roles_baselined_before_service", "baseline_history_read_after_idle", "job_delivery", "manager_delivery", "manager_is_fixture_only", "turn_budget", "quiet_window_no_duplicate_starts", "idle_executors_received_no_turn")):
    raise SystemExit(1)
PY
}

run_live_delivery_probe() {
    local output="$INSTALL_TMP/liveprobe.out" errors="$INSTALL_TMP/liveprobe.stderr"
    local evidence="$INSTALL_TMP/liveprobe-evidence.json" detail
    printf 'MAM proactive wakeup: running isolated real delivery acceptance\n'
    if ! (cd -- "$PROJECT_ROOT" && env -u CODEX_THREAD_ID "$INSTALLED_PYTHON" -B -m multi_agent_manager.liveprobe \
        --compatibility "$COMPATIBILITY_JSON" --root "$INSTALL_TMP/liveprobe" --evidence "$evidence" >"$output" 2>"$errors"); then
        detail="$(bounded_diagnostic "$output" "$errors" "$evidence")"
        incomplete "isolated real delivery acceptance failed${detail:+: $detail}"
        return 1
    fi
    if ! validate_liveprobe_evidence "$evidence"; then
        detail="$(bounded_diagnostic "$output" "$errors" "$evidence")"
        incomplete "isolated real delivery acceptance returned invalid evidence${detail:+: $detail}"
        return 1
    fi
    printf 'MAM proactive wakeup: isolated real delivery PASS (6 model turns)\n'
}

service_command() {
    local action="$1" output="$2" errors="$3"
    local -a command=("$MAM_BIN" service "$action")
    SERVICE_ERROR=''
    if [[ "$action" == start ]] && ((${#SERVICE_MANAGER_ARGS[@]})); then
        command+=("${SERVICE_MANAGER_ARGS[@]}")
    fi
    # The installer process is never implicitly selected as Manager.
    if ! (cd -- "$PROJECT_ROOT" && env -u CODEX_THREAD_ID "${command[@]}" >"$output" 2>"$errors"); then
        SERVICE_ERROR="$(bounded_diagnostic "$output" "$errors")"
        return 1
    fi
}

status_running() {
    "$INSTALLED_PYTHON" - "$1" <<'PY'
import json
from pathlib import Path
import sys
try:
    value = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except (OSError, UnicodeDecodeError, json.JSONDecodeError):
    raise SystemExit(2)
if not isinstance(value, dict) or not isinstance(value.get("running"), bool):
    raise SystemExit(2)
raise SystemExit(0 if value["running"] else 1)
PY
}

validated_service_state() {
    (cd -- "$PROJECT_ROOT" && "$INSTALLED_PYTHON" -B -m multi_agent_manager.wake_compat \
        --service-status "$1" --quiet)
}

readiness_may_arrive() {
    "$INSTALLED_PYTHON" - "$1" <<'PY'
import json
from pathlib import Path
import sys
try:
    status = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
except (OSError, UnicodeDecodeError, json.JSONDecodeError):
    raise SystemExit(2)
if not isinstance(status, dict):
    raise SystemExit(2)
if status.get("running") is True and status.get("status") in {"healthy", "pending"}:
    raise SystemExit(0)
raise SystemExit(1)
PY
}

wait_for_service_readiness() {
    local status_path="$1" errors="$2" attempt validation
    for ((attempt = 1; attempt <= STARTUP_WAIT_ATTEMPTS; attempt++)); do
        if ! service_command status "$status_path" "$errors"; then
            return 1
        fi
        if validation="$(validated_service_state "$status_path" 2>&1)"; then
            SERVICE_STATE="$validation"
            return 0
        fi
        if readiness_may_arrive "$status_path"; then
            sleep "$STARTUP_WAIT_SECONDS"
            continue
        fi
        SERVICE_ERROR="$validation"
        return 1
    done
    SERVICE_ERROR="scheduler did not become healthy within $((STARTUP_WAIT_ATTEMPTS / 2)) seconds"
    return 1
}

start_project_service() {
    local before="$INSTALL_TMP/status-before.json" after="$INSTALL_TMP/status-after.json" result
    if ! service_command status "$before" "$INSTALL_TMP/status-before.stderr"; then
        incomplete "mam service status failed before activation${SERVICE_ERROR:+: $SERVICE_ERROR}"
        return 1
    fi
    if status_running "$before"; then
        if ! service_command stop "$INSTALL_TMP/stop.json" "$INSTALL_TMP/stop.stderr"; then
            incomplete "the existing project scheduler could not be stopped safely${SERVICE_ERROR:+: $SERVICE_ERROR}"
            return 1
        fi
    else
        result=$?
        if ((result != 1)); then
            incomplete 'mam service status returned an invalid running flag'
            return 1
        fi
    fi
    if ! service_command start "$INSTALL_TMP/start.json" "$INSTALL_TMP/start.stderr"; then
        incomplete "mam service start failed${SERVICE_ERROR:+: $SERVICE_ERROR}"
        return 1
    fi
    if ! wait_for_service_readiness "$after" "$INSTALL_TMP/status-after.stderr"; then
        incomplete "mam service did not acknowledge readiness${SERVICE_ERROR:+: $SERVICE_ERROR}"
        return 1
    fi
    case "$SERVICE_STATE" in
        healthy)
            printf 'MAM proactive wakeup installation: PASS (scheduler healthy)\n'
            ;;
        pending)
            printf 'MAM proactive wakeup installation: PASS (scheduler healthy; pending delivery retained)\n'
            ;;
        awaiting_manager)
            printf 'MAM proactive wakeup installation: PASS (scheduler awaiting first Manager binding)\n'
            ;;
        *)
            incomplete 'mam service returned an unknown validated lifecycle status'
            return 1
            ;;
    esac
}

main() {
    if (($#)); then
        printf 'usage: bash scripts/install.sh\n' >&2
        return 64
    fi
    CHECKOUT_ROOT="$(repository_root)" || {
        incomplete 'cannot resolve the MAM checkout containing this installer'
        return 1
    }
    if [[ ! -f "$CHECKOUT_ROOT/pyproject.toml" || ! -d "$CHECKOUT_ROOT/tests" ]]; then
        incomplete 'scripts/install.sh must be run from a multi-agent-manager checkout'
        return 1
    fi
    local config_path
    if ! config_path="$(find_project_config "$CHECKOUT_ROOT")"; then
        incomplete 'no .mam/env.json was found above this MAM checkout'
        return 1
    fi
    local -a config_values=()
    if ! mapfile -t config_values < <(validate_project_config "$config_path"); then
        incomplete 'project configuration is invalid for this MAM checkout'
        return 1
    fi
    if ((${#config_values[@]} != 2)); then
        incomplete 'project configuration is invalid for this MAM checkout'
        return 1
    fi
    MAM_ROOT="${config_values[0]}"
    PROJECT_ROOT="${config_values[1]}"
    same_git_repository
    choose_source_python
    run_tests
    prepare_local_bin
    install_with_pipx
    persist_local_bin_path
    resolve_installed_python
    validate_explicit_manager
    create_install_tmp
    # Both checks are mandatory for every install, including a fresh project
    # that will later wait for its first Manager binding.  Neither reads or
    # stops the production scheduler.
    run_lightweight_probe
    run_live_delivery_probe
    start_project_service
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
