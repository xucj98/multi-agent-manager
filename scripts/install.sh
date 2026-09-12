#!/usr/bin/env bash
# Install this checkout and manage its project-local proactive wake scheduler.
# The detached daemon is owned by ``mam service``.  Optional mam wait retains
# its App Server trace setup; a verified listener is restarted only after an
# exact interactive confirmation.
set -euo pipefail

readonly PATH_BEGIN='# >>> MAM PATH >>>'
readonly PATH_END='# <<< MAM PATH <<<'
readonly LEGACY_TRACE_BEGIN='# >>> MAM Codex App Server trace >>>'
readonly LEGACY_TRACE_END='# <<< MAM Codex App Server trace <<<'
readonly STARTUP_WAIT_ATTEMPTS=40
readonly STARTUP_WAIT_SECONDS=0.5
readonly TRACE_BEGIN="$LEGACY_TRACE_BEGIN"
readonly TRACE_END="$LEGACY_TRACE_END"
readonly RUST_LOG_VALUE='off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info'
readonly LOG_FORMAT_VALUE='json'
readonly RESTART_WAIT_SECONDS=20
readonly STOP_WAIT_SECONDS=10

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
WAIT_SOCKET=''
WAIT_LOG_PATH=''
TARGET_RECORD=''
TARGET_PID=''
TARGET_START_TICKS=''
TARGET_EXECUTABLE=''
TARGET_SOCKET=''
TARGET_PARENT_PID=''
TARGET_PARENT_START_TICKS=''
TARGET_PARENT_EXECUTABLE=''
TARGET_LOG_PATH=''
TARGET_LAUNCH_PLAN=''
DISCOVERY_ERROR=''
RUNTIME_ENV_ERROR=''
RESTART_ERROR=''
LAUNCH_ERROR=''
LAUNCHED_WRAPPER_PID=''
LAUNCHED_WRAPPER_START_TICKS=''
STARTUP_LOCK_FD=''
LOG_ERROR=''
LISTENER_ERROR=''
PROCESS_ERROR=''
TERMINATION_ERROR=''
MATCH_ERROR=''
RESTART_OUTCOME=''
RECOVERY_DIR=''
RECOVERY_PLAN_PATH=''
RECOVERY_SCRIPT_PATH=''
RECOVERY_ERROR=''
POST_TERM_GUARD=''

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

wait_incomplete() {
    printf 'Installation/verification incomplete: %s\n' "$*" >&2
    return 1
}

# Optional mam wait retains the stable trace setup and restart recovery path.
# These helpers only ever inspect or restart the verified app-managed listener
# after an exact interactive confirmation; the proactive service remains owned
# by mam service below.
update_bashrc() {
    local bashrc="${MAM_INSTALL_BASHRC:-$HOME/.bashrc}" directory temporary backup
    if [[ "$bashrc" != /* || ! -d "$(dirname -- "$bashrc")" ]]; then
        wait_incomplete "the .bashrc path must be in an existing absolute directory: $bashrc"
        return 1
    fi
    if [[ ! -e "$bashrc" ]]; then
        (umask 077; : > "$bashrc")
    elif [[ ! -f "$bashrc" || -L "$bashrc" ]]; then
        wait_incomplete "refusing to replace a non-regular .bashrc: $bashrc"
        return 1
    fi
    directory="$(dirname -- "$bashrc")"
    if ! temporary="$(mktemp -- "$directory/.${bashrc##*/}.mam-install.XXXXXX")"; then
        wait_incomplete 'could not create a temporary .bashrc update'
        return 1
    fi
    if ! python3 - "$bashrc" "$temporary" "$TRACE_BEGIN" "$TRACE_END" "$RUST_LOG_VALUE" <<'PY'
import os
from pathlib import Path
import stat
import sys

source, destination = map(Path, sys.argv[1:3])
begin, end, rust_log = sys.argv[3:]
try:
    raw = source.read_bytes()
    text = raw.decode("utf-8")
except (OSError, UnicodeDecodeError) as exc:
    print(f"cannot read {source}: {exc}", file=sys.stderr)
    raise SystemExit(1)

newline = "\r\n" if b"\r\n" in raw else "\n"
lines = text.splitlines(keepends=True)
starts = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == begin]
ends = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == end]
# Unmarked exports may belong to user shell logic.  Only this exact marker
# block proves installer ownership and may be replaced.
if starts or ends:
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        print("refusing incomplete or multiple MAM trace markers in .bashrc; it was left unchanged", file=sys.stderr)
        raise SystemExit(1)
    expected = [
        begin,
        'if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then',
        '    export PATH="$HOME/.local/bin:$PATH"',
        'fi',
        f'export RUST_LOG="{rust_log}"',
        'export LOG_FORMAT=json',
        end,
    ]
    observed = [line.rstrip("\r\n") for line in lines[starts[0] : ends[0] + 1]]
    if observed != expected:
        print("refusing an unrecognized MAM trace block in .bashrc; it was left unchanged", file=sys.stderr)
        raise SystemExit(1)
    kept = lines[: starts[0]] + lines[ends[0] + 1 :]
else:
    kept = list(lines)

block = [
    begin + newline,
    'if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then' + newline,
    '    export PATH="$HOME/.local/bin:$PATH"' + newline,
    'fi' + newline,
    f'export RUST_LOG="{rust_log}"' + newline,
    'export LOG_FORMAT=json' + newline,
    end + newline,
]
insert_at = len(kept)
for index, line in enumerate(kept):
    value = line.strip()
    if (
        value in {
            '[ -z "$PS1" ] && return',
            '[[ -z "$PS1" ]] && return',
            '[[ $- != *i* ]] && return',
            '[ "$-" != "${-#*i}" ] || return',
        }
        or value.startswith(('case $- in', 'case "$-" in'))
    ):
        insert_at = index
        break
if insert_at and not kept[insert_at - 1].endswith(("\n", "\r")):
    kept[insert_at - 1] += newline
try:
    metadata = source.stat()
    with destination.open("w", encoding="utf-8", newline="") as handle:
        handle.write("".join(kept[:insert_at] + block + kept[insert_at:]))
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(destination, stat.S_IMODE(metadata.st_mode))
    try:
        os.chown(destination, metadata.st_uid, metadata.st_gid)
    except PermissionError:
        pass
except OSError as exc:
    print(f"cannot prepare .bashrc update: {exc}", file=sys.stderr)
    raise SystemExit(1)
PY
    then
        rm -f -- "$temporary"
        wait_incomplete 'the .bashrc contains an incomplete, multiple, or unrecognized MAM trace block; it was left unchanged'
        return 1
    fi
    if cmp -s -- "$bashrc" "$temporary"; then
        rm -f -- "$temporary"
        printf 'MAM trace configuration in %s is already up to date.\n' "$bashrc"
        return 0
    fi
    backup="${bashrc}.mam-install.$(date -u +%Y%m%dT%H%M%SZ).$$.bak"
    if ! cp -p -- "$bashrc" "$backup"; then
        rm -f -- "$temporary"
        wait_incomplete 'could not create a reversible .bashrc backup'
        return 1
    fi
    if ! mv -f -- "$temporary" "$bashrc"; then
        rm -f -- "$temporary"
        wait_incomplete "could not update .bashrc; restore it with: cp -p -- $backup $bashrc"
        return 1
    fi
    printf 'Updated %s; backup: %s\nRollback: cp -p -- %q %q\n' "$bashrc" "$backup" "$backup" "$bashrc"
}

discover_app_server() {
    local socket="$1" result status
    local -a fields=()
    TARGET_RECORD=''
    TARGET_PID=''
    TARGET_START_TICKS=''
    TARGET_EXECUTABLE=''
    TARGET_SOCKET=''
    TARGET_PARENT_PID=''
    TARGET_PARENT_START_TICKS=''
    TARGET_PARENT_EXECUTABLE=''
    TARGET_LOG_PATH=''
    TARGET_LAUNCH_PLAN=''
    DISCOVERY_ERROR=''
    if result="$(python3 - "$socket" 2>&1 <<'PY'
import base64
import json
import os
from pathlib import Path
import stat
import sys

socket = sys.argv[1]


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def encoded(value):
    return base64.b64encode(canonical(value).encode("ascii")).decode("ascii")


def proc_fields(pid):
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    close = raw.rfind(")")
    tail = raw[close + 2 :].split() if close >= 0 else []
    if len(tail) <= 19 or not tail[1].isdecimal() or not tail[19].isdecimal():
        raise ValueError("invalid process stat")
    return tail[0], int(tail[1]), int(tail[19])


def arguments(pid):
    values = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    return [os.fsdecode(value) for value in values if value]


def environment(pid):
    entries = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
    result = {}
    for entry in entries:
        key, separator, value = entry.partition(b"=")
        if not separator:
            continue
        name = os.fsdecode(key)
        if not name or "=" in name or name in result:
            raise ValueError("invalid wrapper environment")
        result[name] = os.fsdecode(value)
    return result


def app_server_arguments(values):
    if "app-server" not in values:
        return False
    return any(
        value == "--listen=unix://" or (value == "--listen" and index + 1 < len(values) and values[index + 1] == "unix://")
        for index, value in enumerate(values)
    )


if not os.path.isabs(socket):
    fail(f"the App Server socket path must be absolute: {socket}")
try:
    socket_stat = os.stat(socket)
except OSError as exc:
    fail(f"cannot inspect the control socket at {socket}: {exc}")
if not stat.S_ISSOCK(socket_stat.st_mode):
    fail(f"the configured App Server path is not a socket: {socket}")

kernel_inode = None
try:
    with open("/proc/net/unix", encoding="ascii") as handle:
        for line in handle:
            values = line.rstrip("\n").split(maxsplit=7)
            if len(values) == 8 and values[5] == "01" and values[7] == socket:
                kernel_inode = values[6]
                break
except OSError as exc:
    fail(f"cannot inspect Unix listeners: {exc}")
if not kernel_inode or not kernel_inode.isdecimal():
    fail(f"no listening Unix socket at {socket}")

owners = []
for proc in Path("/proc").iterdir():
    if not proc.name.isdecimal():
        continue
    try:
        for fd in (proc / "fd").iterdir():
            if os.readlink(fd) == f"socket:[{kernel_inode}]":
                owners.append(int(proc.name))
                break
    except OSError:
        continue

candidates = []
expected_log = os.path.join(os.path.dirname(socket), "app-server.log")
for pid in owners:
    try:
        state, parent, start_ticks = proc_fields(pid)
        child_arguments = arguments(pid)
        executable = os.path.realpath(f"/proc/{pid}/exe")
        parent_state, _, parent_start_ticks = proc_fields(parent)
        parent_arguments = arguments(parent)
        parent_executable = os.path.realpath(f"/proc/{parent}/exe")
        parent_cwd = os.path.realpath(os.readlink(f"/proc/{parent}/cwd"))
        parent_environment = environment(parent)
        stdin = os.readlink(f"/proc/{parent}/fd/0")
        stdout = os.readlink(f"/proc/{parent}/fd/1")
        stderr = os.readlink(f"/proc/{parent}/fd/2")
        log_stat = os.lstat(stdout)
    except (OSError, ValueError):
        continue
    wrapper_arguments = [value for value in parent_arguments[1:] if os.path.basename(value) == "codex"]
    if state == "Z" or parent <= 1 or parent_state == "Z" or not app_server_arguments(child_arguments):
        continue
    if not app_server_arguments(parent_arguments) or os.path.basename(parent_arguments[0]) not in {"node", "nodejs"}:
        continue
    if len(wrapper_arguments) != 1 or not os.path.isabs(wrapper_arguments[0]):
        continue
    if not os.path.isfile(wrapper_arguments[0]) or not os.access(wrapper_arguments[0], os.X_OK):
        continue
    if os.path.basename(parent_executable) not in {"node", "nodejs"} or not os.access(parent_executable, os.X_OK):
        continue
    if not os.access(executable, os.X_OK) or not os.path.isdir(parent_cwd):
        continue
    if stdin != "/dev/null" or stdout != stderr or stdout != expected_log:
        continue
    if os.path.islink(stdout) or not stat.S_ISREG(log_stat.st_mode):
        continue
    candidates.append(
        {
            "listener": {
                "pid": pid,
                "start_ticks": start_ticks,
                "executable": executable,
                "argv": child_arguments,
                "parent_pid": parent,
                "socket": socket,
                "socket_device": socket_stat.st_dev,
                "socket_inode": socket_stat.st_ino,
                "kernel_inode": int(kernel_inode),
            },
            "launch": {
                "socket": socket,
                "log_path": stdout,
                "parent": {
                    "pid": parent,
                    "start_ticks": parent_start_ticks,
                    "executable": parent_executable,
                    "argv": parent_arguments,
                    "cwd": parent_cwd,
                    "environment": parent_environment,
                    "stdin": stdin,
                    "stdout": stdout,
                    "stderr": stderr,
                    "log_identity": {"device": log_stat.st_dev, "inode": log_stat.st_ino},
                },
            },
        }
    )

if len(candidates) != 1:
    if not candidates:
        fail("the socket owner is not the expected app-managed npm Codex App Server listener with its standard log")
    fail(f"more than one validated app-managed Codex App Server listener owns {socket}")

record = candidates[0]
listener = record["listener"]
launch = record["launch"]
visible = (
    listener["pid"],
    listener["start_ticks"],
    listener["executable"],
    socket,
    launch["parent"]["pid"],
    launch["parent"]["start_ticks"],
    launch["parent"]["executable"],
    launch["log_path"],
)
if any("\n" in str(value) or "\r" in str(value) for value in visible):
    fail("the App Server target contains an unsafe line break")
print(
    listener["pid"],
    listener["start_ticks"],
    listener["executable"],
    socket,
    launch["parent"]["pid"],
    launch["parent"]["start_ticks"],
    launch["parent"]["executable"],
    launch["log_path"],
    encoded(launch),
    encoded(record),
    sep="\n",
)
PY
)"; then
        :
    else
        status=$?
        DISCOVERY_ERROR="${result:-unable to inspect the App Server listener}"
        return "$status"
    fi
    mapfile -t fields <<< "$result"
    if ((${#fields[@]} != 10)); then
        DISCOVERY_ERROR='invalid App Server listener identity'
        return 1
    fi
    TARGET_PID="${fields[0]}"
    TARGET_START_TICKS="${fields[1]}"
    TARGET_EXECUTABLE="${fields[2]}"
    TARGET_SOCKET="${fields[3]}"
    TARGET_PARENT_PID="${fields[4]}"
    TARGET_PARENT_START_TICKS="${fields[5]}"
    TARGET_PARENT_EXECUTABLE="${fields[6]}"
    TARGET_LOG_PATH="${fields[7]}"
    TARGET_LAUNCH_PLAN="${fields[8]}"
    TARGET_RECORD="${fields[9]}"
}

runtime_logging_ready() {
    local pid="$1" result status
    RUNTIME_ENV_ERROR=''
    if result="$(python3 - "$pid" "$RUST_LOG_VALUE" "$LOG_FORMAT_VALUE" 2>&1 <<'PY'
import os
from pathlib import Path
import sys

pid, required_rust, required_format = sys.argv[1:]
try:
    entries = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
except OSError as exc:
    print(f"cannot inspect the listener environment for PID {pid}: {exc}", file=sys.stderr)
    raise SystemExit(2)
environment = {}
for entry in entries:
    key, separator, value = entry.partition(b"=")
    if separator:
        environment[os.fsdecode(key)] = os.fsdecode(value)
if environment.get("RUST_LOG") != required_rust or environment.get("LOG_FORMAT") != required_format:
    print(f"PID {pid} does not have the required JSON trace logging environment", file=sys.stderr)
    raise SystemExit(1)
PY
)"; then
        return 0
    else
        status=$?
    fi
    RUNTIME_ENV_ERROR="${result:-unable to inspect the listener environment}"
    return "$status"
}

log_is_regular() {
    local path="$1" result status
    LOG_ERROR=''
    if result="$(python3 - "$path" 2>&1 <<'PY'
import os
import stat
import sys

path = sys.argv[1]
try:
    current = os.lstat(path)
except OSError as exc:
    print(f"cannot inspect the App Server trace log at {path}: {exc}", file=sys.stderr)
    raise SystemExit(2)
if not stat.S_ISREG(current.st_mode):
    print(f"the App Server trace log is not a regular file: {path}", file=sys.stderr)
    raise SystemExit(1)
PY
)"; then
        return 0
    else
        status=$?
    fi
    LOG_ERROR="${result:-unable to inspect the App Server trace log}"
    return "$status"
}

listener_is_present() {
    local socket="$1" result status
    LISTENER_ERROR=''
    if result="$(python3 - "$socket" 2>&1 <<'PY'
import os
import stat
import sys

socket = sys.argv[1]
if not os.path.isabs(socket):
    print(f"the App Server socket path must be absolute: {socket}", file=sys.stderr)
    raise SystemExit(2)
try:
    current = os.lstat(socket)
except FileNotFoundError:
    raise SystemExit(1)
except OSError as exc:
    print(f"cannot inspect the control socket at {socket}: {exc}", file=sys.stderr)
    raise SystemExit(2)
if not stat.S_ISSOCK(current.st_mode):
    print(f"the configured App Server path is not a socket: {socket}", file=sys.stderr)
    raise SystemExit(2)
try:
    with open("/proc/net/unix", encoding="ascii") as handle:
        for line in handle:
            values = line.rstrip("\n").split(maxsplit=7)
            if len(values) == 8 and values[5] == "01" and values[7] == socket:
                raise SystemExit(0)
except OSError as exc:
    print(f"cannot inspect Unix listeners: {exc}", file=sys.stderr)
    raise SystemExit(2)
raise SystemExit(1)
PY
)"; then
        return 0
    else
        status=$?
    fi
    if ((status != 1)); then
        LISTENER_ERROR="${result:-unable to inspect the App Server socket listener}"
    fi
    return "$status"
}

process_identity_present() {
    local pid="$1" start_ticks="$2" executable="$3" result status
    PROCESS_ERROR=''
    if result="$(python3 - "$pid" "$start_ticks" "$executable" 2>&1 <<'PY'
import os
from pathlib import Path
import sys

pid, expected_start, expected_executable = sys.argv[1:]
try:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    close = raw.rfind(")")
    tail = raw[close + 2 :].split() if close >= 0 else []
    if len(tail) <= 19 or not tail[19].isdecimal():
        raise ValueError("invalid process stat")
    if tail[0] == "Z" or int(tail[19]) != int(expected_start):
        raise SystemExit(1)
    if os.path.realpath(f"/proc/{pid}/exe") != expected_executable:
        raise SystemExit(1)
except FileNotFoundError:
    raise SystemExit(1)
except (OSError, ValueError) as exc:
    print(f"cannot inspect process identity for PID {pid}: {exc}", file=sys.stderr)
    raise SystemExit(2)
PY
)"; then
        return 0
    else
        status=$?
    fi
    if ((status != 1)); then
        PROCESS_ERROR="${result:-unable to inspect process identity}"
    fi
    return "$status"
}

acquire_startup_lock() {
    local socket="$1" lock
    STARTUP_LOCK_FD=''
    lock="$(dirname -- "$socket")/app-server-startup.lock"
    if [[ ! -f "$lock" || -L "$lock" ]]; then
        RESTART_ERROR="the existing App Server startup lock is unavailable at $lock"
        return 1
    fi
    if ! command -v flock >/dev/null 2>&1; then
        RESTART_ERROR='flock is required to coordinate the existing App Server startup lock'
        return 1
    fi
    if exec {STARTUP_LOCK_FD}>>"$lock"; then
        :
    else
        RESTART_ERROR="cannot open the existing App Server startup lock at $lock"
        return 1
    fi
    if flock -n "$STARTUP_LOCK_FD"; then
        return 0
    fi
    RESTART_ERROR='the App Server startup lock is busy; no process was stopped'
    exec {STARTUP_LOCK_FD}>&-
    STARTUP_LOCK_FD=''
    return 1
}

release_startup_lock() {
    if [[ -n "$STARTUP_LOCK_FD" ]]; then
        flock -u "$STARTUP_LOCK_FD" >/dev/null 2>&1 || true
        exec {STARTUP_LOCK_FD}>&-
        STARTUP_LOCK_FD=''
    fi
}

clear_post_term_guard() {
    POST_TERM_GUARD=''
    trap - EXIT HUP INT TERM
}

print_recovery_command() {
    if [[ -z "$RECOVERY_SCRIPT_PATH" ]]; then
        return 1
    fi
    printf 'Recovery command: bash %q\n' "$RECOVERY_SCRIPT_PATH" >&2
}

discard_recovery_artifacts() {
    local directory="$RECOVERY_DIR"
    RECOVERY_ERROR=''
    if [[ -z "$directory" ]]; then
        return 0
    fi
    if ! rm -rf -- "$directory"; then
        RECOVERY_ERROR="could not remove protected recovery artifacts at $directory"
        return 1
    fi
    RECOVERY_DIR=''
    RECOVERY_PLAN_PATH=''
    RECOVERY_SCRIPT_PATH=''
}

write_recovery_script() {
    local installer="$1" plan_path="$2" socket="$3" destination="$4"
    (
        umask 077
        {
            printf '%s\n' '#!/usr/bin/env bash'
            printf '%s\n' 'set -euo pipefail'
            printf 'readonly MAM_RECOVERY_INSTALLER=%q\n' "$installer"
            printf 'readonly MAM_RECOVERY_PLAN=%q\n' "$plan_path"
            printf 'readonly MAM_RECOVERY_SOCKET=%q\n' "$socket"
            cat <<'SH'
if [[ ! -f "$MAM_RECOVERY_PLAN" || -L "$MAM_RECOVERY_PLAN" ]]; then
    printf 'Recovery failed: protected launch plan is unavailable at %s\n' "$MAM_RECOVERY_PLAN" >&2
    exit 1
fi
if [[ "$(stat -c '%a' -- "$MAM_RECOVERY_PLAN" 2>/dev/null || true)" != 600 ]]; then
    printf 'Recovery failed: protected launch plan must have mode 600 at %s\n' "$MAM_RECOVERY_PLAN" >&2
    exit 1
fi
if [[ ! -f "$MAM_RECOVERY_INSTALLER" || -L "$MAM_RECOVERY_INSTALLER" ]]; then
    printf 'Recovery failed: installer source is unavailable at %s\n' "$MAM_RECOVERY_INSTALLER" >&2
    exit 1
fi
source "$MAM_RECOVERY_INSTALLER"
if ! launch_plan="$(<"$MAM_RECOVERY_PLAN")"; then
    printf 'Recovery failed: could not read the protected launch plan\n' >&2
    exit 1
fi
if ! acquire_startup_lock "$MAM_RECOVERY_SOCKET"; then
    printf 'Recovery failed: %s\n' "${RESTART_ERROR:-could not acquire the App Server startup lock}" >&2
    exit 1
fi
trap 'release_startup_lock' EXIT
if launch_same_style "$launch_plan"; then
    release_startup_lock
    trap - EXIT
    printf 'Recovery launch started from the protected captured plan (wrapper PID %s). Re-run bash scripts/install.sh to verify it.\n' "$LAUNCHED_WRAPPER_PID"
    exit 0
else
    launch_status=$?
fi
release_startup_lock
trap - EXIT
printf 'Recovery failed: %s\n' "${LAUNCH_ERROR:-the captured app-managed npm wrapper could not be started}" >&2
exit "$launch_status"
SH
        } > "$destination"
    )
}

prepare_recovery_artifacts() {
    local launch_plan="$1" socket="$2" control_directory root installer directory
    RECOVERY_ERROR=''
    if [[ -z "$launch_plan" || "$socket" != /* ]]; then
        RECOVERY_ERROR='cannot prepare recovery artifacts from an invalid captured launch plan'
        return 1
    fi
    control_directory="$(dirname -- "$socket")"
    if [[ ! -d "$control_directory" ]]; then
        RECOVERY_ERROR="the App Server control directory is unavailable at $control_directory"
        return 1
    fi
    if ! root="$(repository_root)" || [[ ! -f "$root/scripts/install.sh" || -L "$root/scripts/install.sh" ]]; then
        RECOVERY_ERROR='the current installer source is unavailable for recovery'
        return 1
    fi
    installer="$root/scripts/install.sh"
    if ! directory="$(mktemp -d -- "$control_directory/mam-app-server-recovery.XXXXXX")"; then
        RECOVERY_ERROR='could not create a private App Server recovery directory'
        return 1
    fi
    RECOVERY_DIR="$directory"
    RECOVERY_PLAN_PATH="$directory/launch-plan.b64"
    RECOVERY_SCRIPT_PATH="$directory/recover-app-server.sh"
    if ! chmod 700 -- "$RECOVERY_DIR"; then
        discard_recovery_artifacts >/dev/null 2>&1 || true
        RECOVERY_ERROR='could not protect the App Server recovery directory'
        return 1
    fi
    if ! (umask 077; printf '%s\n' "$launch_plan" > "$RECOVERY_PLAN_PATH"); then
        discard_recovery_artifacts >/dev/null 2>&1 || true
        RECOVERY_ERROR='could not write the protected App Server launch plan'
        return 1
    fi
    if ! chmod 600 -- "$RECOVERY_PLAN_PATH"; then
        discard_recovery_artifacts >/dev/null 2>&1 || true
        RECOVERY_ERROR='could not protect the App Server launch plan'
        return 1
    fi
    if ! write_recovery_script "$installer" "$RECOVERY_PLAN_PATH" "$socket" "$RECOVERY_SCRIPT_PATH"; then
        discard_recovery_artifacts >/dev/null 2>&1 || true
        RECOVERY_ERROR='could not write the App Server recovery command'
        return 1
    fi
    if ! chmod 700 -- "$RECOVERY_SCRIPT_PATH"; then
        discard_recovery_artifacts >/dev/null 2>&1 || true
        RECOVERY_ERROR='could not protect the App Server recovery command'
        return 1
    fi
}

post_term_failure() {
    local reason="$1"
    clear_post_term_guard
    release_startup_lock
    wait_incomplete "$reason" || true
    printf 'The captured app-managed npm launch plan remains in a protected recovery artifact.\n' >&2
    if print_recovery_command; then
        :
    else
        printf 'Recovery artifact was unexpectedly unavailable; do not assume the App Server was restored.\n' >&2
    fi
    return 1
}

handle_post_term_exit() {
    local status="$1"
    if [[ "$POST_TERM_GUARD" != 1 ]]; then
        return "$status"
    fi
    if ((status == 0)); then
        status=1
    fi
    post_term_failure 'App Server restart exited before replacement verification completed after recovery preparation.' || true
    return "$status"
}

handle_post_term_signal() {
    local signal_name="$1" status="$2"
    if [[ "$POST_TERM_GUARD" == 1 ]]; then
        post_term_failure "App Server restart was interrupted by SIG${signal_name} after recovery preparation; its stop/relaunch state may be incomplete." || true
    fi
    exit "$status"
}

recovery_artifacts_are_protected() {
    if [[ -z "$RECOVERY_DIR" || ! -d "$RECOVERY_DIR" || -L "$RECOVERY_DIR" ]] \
        || [[ -z "$RECOVERY_SCRIPT_PATH" || ! -f "$RECOVERY_SCRIPT_PATH" || -L "$RECOVERY_SCRIPT_PATH" || ! -x "$RECOVERY_SCRIPT_PATH" ]] \
        || [[ -z "$RECOVERY_PLAN_PATH" || ! -f "$RECOVERY_PLAN_PATH" || -L "$RECOVERY_PLAN_PATH" ]]; then
        return 1
    fi
    [[ "$(stat -c '%a' -- "$RECOVERY_DIR" 2>/dev/null || true)" == 700 ]] \
        && [[ "$(stat -c '%a' -- "$RECOVERY_SCRIPT_PATH" 2>/dev/null || true)" == 700 ]] \
        && [[ "$(stat -c '%a' -- "$RECOVERY_PLAN_PATH" 2>/dev/null || true)" == 600 ]]
}

arm_post_term_guard() {
    if ! recovery_artifacts_are_protected; then
        RECOVERY_ERROR='the protected App Server recovery command is unavailable'
        return 1
    fi
    POST_TERM_GUARD=1
    trap 'handle_post_term_exit "$?"' EXIT
    trap 'handle_post_term_signal HUP 129' HUP
    trap 'handle_post_term_signal INT 130' INT
    trap 'handle_post_term_signal TERM 143' TERM
}

finish_post_term_restart() {
    clear_post_term_guard
    release_startup_lock
    if discard_recovery_artifacts; then
        return 0
    fi
    wait_incomplete "the replacement listener was verified, but $RECOVERY_ERROR; remove them manually" || true
    if print_recovery_command; then
        :
    fi
    return 1
}

confirm_restart() {
    local pid="$1" executable="$2" socket="$3" response
    printf '\nCodex App Server restart required for trace logging.\nTarget PID: %s\nExecutable: %s\nSocket: %s\n' "$pid" "$executable" "$socket" >&2
    printf 'Run this from a separate terminal: restarting it can sever an App-managed connection.\n' >&2
    if [[ ! -t 0 || ! -t 1 ]]; then
        printf 'No terminal confirmation is available; no process was stopped.\n' >&2
        return 1
    fi
    printf 'Type exactly yes and press Enter to restart only this listener: ' >&2
    if ! IFS= read -r response; then
        printf 'Confirmation ended without yes; no process was stopped.\n' >&2
        return 1
    fi
    if [[ "$response" != yes ]]; then
        printf 'Restart declined; no process was stopped.\n' >&2
        return 1
    fi
}

validate_discovered_runtime() {
    local status
    if log_is_regular "$TARGET_LOG_PATH"; then
        :
    else
        status=$?
        RESTART_ERROR="${LOG_ERROR:-cannot inspect the App Server trace log}"
        return "$status"
    fi
    if runtime_logging_ready "$TARGET_PID"; then
        return 0
    else
        status=$?
    fi
    if ((status == 2)); then
        RESTART_ERROR="${RUNTIME_ENV_ERROR:-cannot inspect the listener environment}"
    else
        RESTART_ERROR='the verified App Server listener does not have the required JSON trace logging environment'
    fi
    return "$status"
}

wait_for_target_departure() {
    local socket="$1" old_record="$2" old_parent_pid="$3" old_parent_start_ticks="$4" old_parent_executable="$5"
    local deadline=$((SECONDS + STOP_WAIT_SECONDS)) status
    RESTART_OUTCOME=''
    RESTART_ERROR=''
    while ((SECONDS < deadline)); do
        if discover_app_server "$socket"; then
            if [[ "$TARGET_RECORD" != "$old_record" ]]; then
                if validate_discovered_runtime; then
                    RESTART_OUTCOME='concurrent-replacement'
                    printf 'A concurrent verified App Server replacement appeared; leaving it running.\n'
                    return 0
                fi
                return 1
            fi
        else
            if listener_is_present "$socket"; then
                RESTART_ERROR="a listener remains at $socket but could not be verified as the expected app-managed npm listener: ${DISCOVERY_ERROR:-unknown listener}"
                return 1
            else
                status=$?
            fi
            if ((status != 1)); then
                RESTART_ERROR="${LISTENER_ERROR:-cannot inspect whether the original listener stopped}"
                return "$status"
            fi
            if process_identity_present "$old_parent_pid" "$old_parent_start_ticks" "$old_parent_executable"; then
                :
            else
                status=$?
                if ((status != 1)); then
                    RESTART_ERROR="${PROCESS_ERROR:-cannot inspect the original npm wrapper after stopping its listener}"
                    return "$status"
                fi
                if [[ ! -e "$socket" && ! -L "$socket" ]]; then
                    RESTART_OUTCOME='departed'
                    return 0
                fi
            fi
        fi
        sleep 0.2
    done
    RESTART_ERROR="the original listener or npm wrapper did not leave the control socket within ${STOP_WAIT_SECONDS}s"
    return 1
}

launch_same_style() {
    local mode='launch' launch_plan result status
    case "$#" in
        1)
            launch_plan="$1"
            ;;
        2)
            if [[ "$1" != --preflight ]]; then
                LAUNCH_ERROR='usage: launch_same_style [--preflight] LAUNCH_PLAN'
                return 2
            fi
            mode='preflight'
            launch_plan="$2"
            ;;
        *)
            LAUNCH_ERROR='usage: launch_same_style [--preflight] LAUNCH_PLAN'
            return 2
            ;;
    esac
    LAUNCH_ERROR=''
    LAUNCHED_WRAPPER_PID=''
    LAUNCHED_WRAPPER_START_TICKS=''
    if result="$(python3 - "$mode" "$RUST_LOG_VALUE" "$LOG_FORMAT_VALUE" 3<<< "$launch_plan" 2>&1 <<'PY'
import base64
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

mode, required_rust, required_format = sys.argv[1:]


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def decode_plan():
    try:
        raw = os.fdopen(3, encoding="ascii").read().strip()
        value = json.loads(base64.b64decode(raw, validate=True).decode("ascii"))
        parent = value["parent"]
        if not isinstance(value["socket"], str) or not isinstance(value["log_path"], str):
            raise ValueError
        for key in ("executable", "cwd", "stdin", "stdout", "stderr"):
            if not isinstance(parent[key], str):
                raise ValueError
        if not isinstance(parent["argv"], list) or not parent["argv"] or not all(isinstance(arg, str) for arg in parent["argv"]):
            raise ValueError
        if not isinstance(parent["environment"], dict) or not all(
            isinstance(key, str) and isinstance(item, str) for key, item in parent["environment"].items()
        ):
            raise ValueError
        return value, parent
    except (KeyError, TypeError, ValueError, UnicodeError, OSError, json.JSONDecodeError) as exc:
        fail("the captured app-managed npm launch plan is invalid")


def app_server_arguments(values):
    return "app-server" in values and any(
        value == "--listen=unix://" or (value == "--listen" and index + 1 < len(values) and values[index + 1] == "unix://")
        for index, value in enumerate(values)
    )


def start_ticks(pid):
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    close = raw.rfind(")")
    tail = raw[close + 2 :].split() if close >= 0 else []
    if len(tail) <= 19 or not tail[19].isdecimal():
        raise ValueError("invalid process stat")
    return int(tail[19])


plan, parent = decode_plan()
if mode not in {"preflight", "launch"}:
    fail("the captured app-managed npm launch mode is invalid")
socket = plan["socket"]
log_path = plan["log_path"]
executable = parent["executable"]
argv = parent["argv"]
cwd = parent["cwd"]
environment = dict(parent["environment"])
if not os.path.isabs(socket) or not os.path.isabs(log_path) or not os.path.isabs(executable) or not os.path.isabs(cwd):
    fail("the captured app-managed npm launch plan contains a relative path")
if any("\0" in value for value in [socket, log_path, executable, cwd, *argv, *environment, *environment.values()]):
    fail("the captured app-managed npm launch plan contains an unsafe value")
if os.path.basename(executable) not in {"node", "nodejs"} or not os.access(executable, os.X_OK):
    fail("the captured npm wrapper executable is no longer runnable")
if os.path.basename(argv[0]) not in {"node", "nodejs"} or not app_server_arguments(argv):
    fail("the captured command is not an app-managed npm App Server start")
wrappers = [value for value in argv[1:] if os.path.basename(value) == "codex"]
if len(wrappers) != 1 or not os.path.isabs(wrappers[0]) or not os.path.isfile(wrappers[0]) or not os.access(wrappers[0], os.X_OK):
    fail("the captured Codex npm wrapper is no longer runnable")
if not os.path.isdir(cwd) or parent["stdin"] != "/dev/null" or parent["stdout"] != log_path or parent["stderr"] != log_path:
    fail("the captured app-managed npm stdio or working directory is no longer supported")
if log_path != os.path.join(os.path.dirname(socket), "app-server.log"):
    fail("the captured App Server log is not the standard control-directory log")
try:
    log_stat = os.lstat(log_path)
except OSError as exc:
    fail("the captured App Server log is unavailable")
if os.path.islink(log_path) or not stat.S_ISREG(log_stat.st_mode):
    fail("the captured App Server log is not a regular file")
identity = parent.get("log_identity")
if not isinstance(identity, dict) or identity.get("device") != log_stat.st_dev or identity.get("inode") != log_stat.st_ino:
    fail("the captured App Server log changed before restart")
try:
    socket_stat = os.lstat(socket)
except FileNotFoundError:
    socket_stat = None
except OSError:
    fail("cannot inspect the control socket before restart")
if mode == "preflight":
    if socket_stat is None or not stat.S_ISSOCK(socket_stat.st_mode):
        fail("the confirmed control socket is no longer present for the captured launch plan")
elif socket_stat is not None:
    fail("the original control socket path remains; refusing to overwrite it")
try:
    with open("/proc/net/unix", encoding="ascii") as handle:
        for line in handle:
            values = line.rstrip("\n").split(maxsplit=7)
            if mode == "launch" and len(values) == 8 and values[5] == "01" and values[7] == socket:
                fail("an App Server listener appeared before the captured wrapper could be launched")
except OSError:
    fail("cannot inspect Unix listeners before restart")
if any(not key or "=" in key for key in environment):
    fail("the captured npm environment is invalid")
environment["RUST_LOG"] = required_rust
environment["LOG_FORMAT"] = required_format
try:
    with open("/dev/null", "rb", buffering=0) as stdin_handle, open(log_path, "ab", buffering=0) as log_handle:
        if mode == "launch":
            process = subprocess.Popen(
                argv,
                executable=executable,
                cwd=cwd,
                env=environment,
                stdin=stdin_handle,
                stdout=log_handle,
                stderr=log_handle,
                close_fds=True,
                start_new_session=True,
                umask=0o077,
            )
    if mode == "preflight":
        raise SystemExit(0)
    try:
        launched_start_ticks = start_ticks(process.pid)
    except (OSError, ValueError):
        process.terminate()
        fail("the captured npm wrapper exited before its identity could be recorded")
except (OSError, subprocess.SubprocessError):
    fail("the captured app-managed npm wrapper could not be started")
print(process.pid, launched_start_ticks)
PY
)"; then
        :
    else
        status=$?
        LAUNCH_ERROR="${result:-the captured app-managed npm wrapper could not be started}"
        return "$status"
    fi
    if [[ "$mode" == preflight ]]; then
        return 0
    fi
    read -r LAUNCHED_WRAPPER_PID LAUNCHED_WRAPPER_START_TICKS <<< "$result"
    if [[ ! "$LAUNCHED_WRAPPER_PID" =~ ^[0-9]+$ || ! "$LAUNCHED_WRAPPER_START_TICKS" =~ ^[0-9]+$ ]]; then
        LAUNCH_ERROR='the captured app-managed npm wrapper returned an invalid process identity'
        return 1
    fi
}

replacement_matches_launch() {
    local old_record="$1" current_record="$2" wrapper_pid="$3" wrapper_start_ticks="$4" result status
    MATCH_ERROR=''
    if result="$(python3 - "$wrapper_pid" "$wrapper_start_ticks" "$RUST_LOG_VALUE" "$LOG_FORMAT_VALUE" 3<<< "$old_record" 4<<< "$current_record" 2>&1 <<'PY'
import base64
import json
import os
import sys

wrapper_pid, wrapper_start_ticks, required_rust, required_format = sys.argv[1:]


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def decode(fd):
    try:
        raw = os.fdopen(fd, encoding="ascii").read().strip()
        return json.loads(base64.b64decode(raw, validate=True).decode("ascii"))
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
        fail("the App Server identity record is invalid")


old = decode(3)
current = decode(4)
try:
    old_launch = old["launch"]
    old_parent = old_launch["parent"]
    current_listener = current["listener"]
    current_launch = current["launch"]
    current_parent = current_launch["parent"]
except (KeyError, TypeError):
    fail("the App Server identity record is incomplete")
if current_listener.get("parent_pid") != int(wrapper_pid):
    fail("the replacement listener is not owned by the wrapper launched by this installer")
if current_parent.get("pid") != int(wrapper_pid) or current_parent.get("start_ticks") != int(wrapper_start_ticks):
    fail("the replacement npm wrapper identity does not match the launched wrapper")
for key in ("socket", "log_path"):
    if current_launch.get(key) != old_launch.get(key):
        fail("the replacement changed the captured App Server socket or log")
for key in ("executable", "argv", "cwd", "stdin", "stdout", "stderr", "log_identity"):
    if current_parent.get(key) != old_parent.get(key):
        fail("the replacement changed the captured npm wrapper command or stdio")
expected_environment = dict(old_parent.get("environment", {}))
expected_environment["RUST_LOG"] = required_rust
expected_environment["LOG_FORMAT"] = required_format
if current_parent.get("environment") != expected_environment:
    fail("the replacement npm wrapper environment differs from the captured environment outside trace settings")
PY
)"; then
        return 0
    else
        status=$?
    fi
    MATCH_ERROR="${result:-the replacement did not match the captured app-managed npm launch}"
    return "$status"
}

wait_for_replacement() {
    local socket="$1" old_record="$2" wrapper_pid="$3" wrapper_start_ticks="$4" wrapper_executable="$5"
    local deadline=$((SECONDS + RESTART_WAIT_SECONDS)) status match_error
    RESTART_OUTCOME=''
    RESTART_ERROR=''
    while ((SECONDS < deadline)); do
        if discover_app_server "$socket"; then
            if [[ "$TARGET_RECORD" != "$old_record" ]]; then
                if replacement_matches_launch "$old_record" "$TARGET_RECORD" "$wrapper_pid" "$wrapper_start_ticks"; then
                    if validate_discovered_runtime; then
                        RESTART_OUTCOME='relaunched'
                        return 0
                    fi
                    return 1
                else
                    match_error="$MATCH_ERROR"
                fi
                if validate_discovered_runtime; then
                    RESTART_OUTCOME='concurrent-replacement'
                    printf 'A concurrent verified App Server replacement appeared during restart; leaving it running.\n'
                    return 0
                fi
                RESTART_ERROR="${RESTART_ERROR:-the replacement listener could not be validated}; ${match_error:-it did not match the captured npm wrapper}"
                return 1
            fi
        else
            if listener_is_present "$socket"; then
                RESTART_ERROR="a listener appeared at $socket but could not be verified as app-managed: ${DISCOVERY_ERROR:-unknown listener}"
                return 1
            else
                status=$?
            fi
            if ((status != 1)); then
                RESTART_ERROR="${LISTENER_ERROR:-cannot inspect the replacement listener}"
                return "$status"
            fi
            if process_identity_present "$wrapper_pid" "$wrapper_start_ticks" "$wrapper_executable"; then
                :
            else
                status=$?
                if ((status != 1)); then
                    RESTART_ERROR="${PROCESS_ERROR:-cannot inspect the launched npm wrapper}"
                else
                    RESTART_ERROR='the captured npm wrapper exited before it recreated the App Server listener'
                fi
                return "$status"
            fi
        fi
        sleep 0.2
    done
    RESTART_ERROR="no verified App Server replacement appeared within ${RESTART_WAIT_SECONDS}s"
    return 1
}

send_term() {
    local pid="$1" start_ticks="$2" executable="$3" socket="$4" result status
    TERMINATION_ERROR=''
    if result="$(python3 - "$pid" "$start_ticks" "$executable" "$socket" 2>&1 <<'PY'
import os
from pathlib import Path
import signal
import sys

pid, expected_start, expected_executable, socket = sys.argv[1:]


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)

try:
    raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    close = raw.rfind(")")
    tail = raw[close + 2 :].split() if close >= 0 else []
    if len(tail) <= 19 or tail[0] == "Z" or not tail[19].isdecimal() or int(tail[19]) != int(expected_start):
        fail("the confirmed listener identity changed before termination")
    if os.path.realpath(f"/proc/{pid}/exe") != expected_executable:
        fail("the confirmed listener executable changed before termination")
    kernel_inode = None
    with open("/proc/net/unix", encoding="ascii") as handle:
        for line in handle:
            values = line.rstrip("\n").split(maxsplit=7)
            if len(values) == 8 and values[5] == "01" and values[7] == socket:
                kernel_inode = values[6]
                break
    if not kernel_inode:
        fail("the confirmed listener no longer owns the control socket")
    if not any(os.readlink(fd) == f"socket:[{kernel_inode}]" for fd in Path(f"/proc/{pid}/fd").iterdir()):
        fail("the confirmed listener no longer owns the control socket")
    os.kill(int(pid), signal.SIGTERM)
except OSError as exc:
    fail(f"could not terminate the confirmed listener: {exc}")
PY
)"; then
        return 0
    else
        status=$?
    fi
    TERMINATION_ERROR="${result:-could not terminate the confirmed listener}"
    return "$status"
}

restart_app_server() {
    local socket="$1" old_record old_launch_plan old_pid old_start_ticks old_executable old_parent_pid old_parent_start_ticks old_parent_executable
    if discover_app_server "$socket"; then
        :
    else
        wait_incomplete "$DISCOVERY_ERROR; no standalone fallback was launched"
        return 1
    fi
    old_record="$TARGET_RECORD"
    old_launch_plan="$TARGET_LAUNCH_PLAN"
    old_pid="$TARGET_PID"
    old_start_ticks="$TARGET_START_TICKS"
    old_executable="$TARGET_EXECUTABLE"
    old_parent_pid="$TARGET_PARENT_PID"
    old_parent_start_ticks="$TARGET_PARENT_START_TICKS"
    old_parent_executable="$TARGET_PARENT_EXECUTABLE"
    if [[ -z "$old_parent_executable" ]]; then
        wait_incomplete 'could not retain the verified npm wrapper identity; no process was stopped'
        return 1
    fi
    if confirm_restart "$old_pid" "$old_executable" "$TARGET_SOCKET"; then
        :
    else
        wait_incomplete 'the current App Server needs a restart before behavioral verification; no process was stopped'
        return 1
    fi
    if acquire_startup_lock "$socket"; then
        :
    else
        wait_incomplete "$RESTART_ERROR"
        return 1
    fi
    if discover_app_server "$socket"; then
        if [[ "$TARGET_RECORD" != "$old_record" ]]; then
            if validate_discovered_runtime; then
                printf 'A concurrent verified App Server replacement appeared before restart; leaving it running.\n'
                release_startup_lock
                return 0
            fi
            wait_incomplete "$RESTART_ERROR; no process was stopped"
            release_startup_lock
            return 1
        fi
    else
        wait_incomplete "the confirmed App Server target disappeared before restart: $DISCOVERY_ERROR; no process was stopped"
        release_startup_lock
        return 1
    fi
    if launch_same_style --preflight "$old_launch_plan"; then
        :
    else
        wait_incomplete "${LAUNCH_ERROR:-the captured app-managed npm launch plan could not be preflighted}; no process was stopped"
        release_startup_lock
        return 1
    fi
    if prepare_recovery_artifacts "$old_launch_plan" "$socket"; then
        :
    else
        wait_incomplete "${RECOVERY_ERROR:-could not prepare the protected App Server recovery command}; no process was stopped"
        release_startup_lock
        return 1
    fi
    if arm_post_term_guard; then
        :
    else
        clear_post_term_guard
        discard_recovery_artifacts >/dev/null 2>&1 || true
        wait_incomplete "${RECOVERY_ERROR:-could not arm the protected App Server recovery command}; no process was stopped"
        release_startup_lock
        return 1
    fi
    if send_term "$old_pid" "$old_start_ticks" "$old_executable" "$socket"; then
        :
    else
        clear_post_term_guard
        discard_recovery_artifacts >/dev/null 2>&1 || true
        wait_incomplete "${TERMINATION_ERROR:-could not terminate the verified listener}; no other process was targeted"
        release_startup_lock
        return 1
    fi
    printf 'Stopped only verified listener PID %s; restoring its captured app-managed npm wrapper.\n' "$old_pid"
    if wait_for_target_departure "$socket" "$old_record" "$old_parent_pid" "$old_parent_start_ticks" "$old_parent_executable"; then
        :
    else
        post_term_failure "$RESTART_ERROR; no standalone fallback was launched" || true
        return 1
    fi
    if [[ "$RESTART_OUTCOME" == concurrent-replacement ]]; then
        finish_post_term_restart || return 1
        return 0
    fi
    if launch_same_style "$old_launch_plan"; then
        :
    else
        post_term_failure "$LAUNCH_ERROR; no standalone fallback was launched" || true
        return 1
    fi
    if wait_for_replacement "$socket" "$old_record" "$LAUNCHED_WRAPPER_PID" "$LAUNCHED_WRAPPER_START_TICKS" "$old_parent_executable"; then
        :
    else
        post_term_failure "$RESTART_ERROR; no standalone fallback was launched" || true
        return 1
    fi
    finish_post_term_restart || return 1
    printf 'Verified replacement listener PID %s at %s with its socket, log, and trace environment.\n' "$TARGET_PID" "$TARGET_SOCKET"
}

ensure_runtime_logging() {
    local socket="$1" status
    if discover_app_server "$socket"; then
        :
    else
        wait_incomplete "$DISCOVERY_ERROR; no standalone fallback was launched"
        return 1
    fi
    if log_is_regular "$TARGET_LOG_PATH"; then
        :
    else
        wait_incomplete "$LOG_ERROR; no process was stopped"
        return 1
    fi
    if runtime_logging_ready "$TARGET_PID"; then
        printf 'The current verified listener already has JSON trace logging.\n'
        return 0
    else
        status=$?
    fi
    if ((status == 2)); then
        wait_incomplete "$RUNTIME_ENV_ERROR; no process was stopped"
        return 1
    fi
    if ((status != 1)); then
        wait_incomplete "${RUNTIME_ENV_ERROR:-could not inspect the listener environment}; no process was stopped"
        return 1
    fi
    printf 'The current verified listener needs a restart to receive the .bashrc trace settings.\n'
    restart_app_server "$socket"
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
    if ! changed="$(python3 - "$target" "$temporary" "$kind" "$PATH_BEGIN" "$PATH_END" <<'PY'
from pathlib import Path
import os
import stat
import sys

source, destination = map(Path, sys.argv[1:3])
kind, path_begin, path_end = sys.argv[3:]
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

prepare_wait_trace() {
    local socket="${MAM_APP_SERVER_SOCKET:-$HOME/.codex/app-server-control/app-server-control.sock}"
    if ! update_bashrc; then
        return 1
    fi
    if ! ensure_runtime_logging "$socket"; then
        return 1
    fi
    WAIT_SOCKET="$TARGET_SOCKET"
    WAIT_LOG_PATH="$TARGET_LOG_PATH"
    if [[ -z "$WAIT_SOCKET" || -z "$WAIT_LOG_PATH" ]]; then
        wait_incomplete 'the verified App Server did not retain socket and trace-log paths'
        return 1
    fi
}

run_wait_compatibility() {
    local output="$INSTALL_TMP/wait-compat.out" errors="$INSTALL_TMP/wait-compat.stderr" detail
    printf 'MAM optional wait: running live App Server trace compatibility probe\n'
    if ! (
        cd -- "$PROJECT_ROOT"
        env -u CODEX_THREAD_ID MAM_APP_SERVER_SOCKET="$WAIT_SOCKET" MAM_APP_SERVER_LOG="$WAIT_LOG_PATH" \
            "$INSTALLED_PYTHON" -B -m multi_agent_manager.wait_compat >"$output" 2>"$errors"
    ); then
        detail="$(bounded_diagnostic "$output" "$errors")"
        incomplete "the optional wait compatibility probe failed${detail:+: $detail}"
        return 1
    fi
    printf 'MAM optional wait: live App Server trace compatibility PASS\n'
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
    prepare_wait_trace
    persist_local_bin_path
    resolve_installed_python
    validate_explicit_manager
    create_install_tmp
    # Both optional-wait and proactive compatibility paths must pass before
    # this installer can stop or replace the current project scheduler.
    run_wait_compatibility
    run_lightweight_probe
    run_live_delivery_probe
    start_project_service
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
