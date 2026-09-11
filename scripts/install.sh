#!/usr/bin/env bash
# Install this checkout, prepare App Server trace logging, and test it.
set -euo pipefail

readonly TRACE_BEGIN='# >>> MAM Codex App Server trace >>>'
readonly TRACE_END='# <<< MAM Codex App Server trace <<<'
readonly RUST_LOG_VALUE='off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info'
readonly LOG_FORMAT_VALUE='json'
readonly RESTART_WAIT_SECONDS=20
readonly STOP_WAIT_SECONDS=10

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

incomplete() {
    printf 'Installation/verification incomplete: %s\n' "$*" >&2
    return 1
}

repository_root() {
    local scripts
    scripts="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || return 1
    cd -- "$scripts/.." && pwd -P
}

find_project_config() {
    local directory="$1"
    while [[ "$directory" != / ]]; do
        if [[ -f "$directory/.mam/env.json" ]]; then
            printf '%s\n' "$directory/.mam/env.json"
            return 0
        fi
        directory="$(dirname -- "$directory")"
    done
    [[ -f "/.mam/env.json" ]] && printf '%s\n' '/.mam/env.json'
}

validate_project_config() {
    python3 - "$1" <<'PY'
import json
import os
import sys

path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
except (OSError, ValueError) as exc:
    print(f"invalid project configuration {path}: {exc}", file=sys.stderr)
    raise SystemExit(1)
if not isinstance(data, dict):
    print(f"invalid project configuration {path}: expected a JSON object", file=sys.stderr)
    raise SystemExit(1)
for key in ("MAM_ROOT", "PROJECT_ROOT"):
    if not isinstance(data.get(key), str) or not os.path.isabs(data[key]):
        print(f"invalid project configuration {path}: {key} must be an absolute path", file=sys.stderr)
        raise SystemExit(1)
if not isinstance(data.get("MAM_BRANCH"), str) or not data["MAM_BRANCH"]:
    print(f"invalid project configuration {path}: MAM_BRANCH must be a non-empty string", file=sys.stderr)
    raise SystemExit(1)
PY
}

update_bashrc() {
    local bashrc="${MAM_INSTALL_BASHRC:-$HOME/.bashrc}" directory temporary backup
    if [[ "$bashrc" != /* || ! -d "$(dirname -- "$bashrc")" ]]; then
        incomplete "the .bashrc path must be in an existing absolute directory: $bashrc"
        return 1
    fi
    if [[ ! -e "$bashrc" ]]; then
        (umask 077; : > "$bashrc")
    elif [[ ! -f "$bashrc" || -L "$bashrc" ]]; then
        incomplete "refusing to replace a non-regular .bashrc: $bashrc"
        return 1
    fi
    directory="$(dirname -- "$bashrc")"
    if ! temporary="$(mktemp -- "$directory/.${bashrc##*/}.mam-install.XXXXXX")"; then
        incomplete 'could not create a temporary .bashrc update'
        return 1
    fi
    if ! python3 - "$bashrc" "$temporary" "$TRACE_BEGIN" "$TRACE_END" "$RUST_LOG_VALUE" <<'PY'
import os
from pathlib import Path
import stat
import sys

source, destination = map(Path, sys.argv[1:3])
begin, end, rust_log = sys.argv[3:]
legacy = {
    'export RUST_LOG="off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info"',
    "export LOG_FORMAT=json",
}
try:
    raw = source.read_bytes()
    text = raw.decode("utf-8")
except (OSError, UnicodeDecodeError) as exc:
    print(f"cannot read {source}: {exc}", file=sys.stderr)
    raise SystemExit(1)

newline = "\r\n" if b"\r\n" in raw else "\n"
kept, inside = [], False
for line in text.splitlines(keepends=True):
    value = line.rstrip("\r\n")
    if value == begin:
        if inside:
            print("refusing nested MAM trace markers in .bashrc", file=sys.stderr)
            raise SystemExit(1)
        inside = True
    elif value == end:
        if not inside:
            print("refusing an unmatched MAM trace end marker in .bashrc", file=sys.stderr)
            raise SystemExit(1)
        inside = False
    elif not inside and value not in legacy:
        kept.append(line)
if inside:
    print("refusing an unmatched MAM trace start marker in .bashrc", file=sys.stderr)
    raise SystemExit(1)

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
        incomplete 'the .bashrc contains incomplete MAM trace markers; it was left unchanged'
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
        incomplete 'could not create a reversible .bashrc backup'
        return 1
    fi
    if ! mv -f -- "$temporary" "$bashrc"; then
        rm -f -- "$temporary"
        incomplete "could not update .bashrc; restore it with: cp -p -- $backup $bashrc"
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
    local launch_plan="$1" result status
    LAUNCH_ERROR=''
    LAUNCHED_WRAPPER_PID=''
    LAUNCHED_WRAPPER_START_TICKS=''
    if result="$(python3 - "$RUST_LOG_VALUE" "$LOG_FORMAT_VALUE" 3<<< "$launch_plan" 2>&1 <<'PY'
import base64
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

required_rust, required_format = sys.argv[1:]


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
if socket_stat is not None:
    fail("the original control socket path remains; refusing to overwrite it")
try:
    with open("/proc/net/unix", encoding="ascii") as handle:
        for line in handle:
            values = line.rstrip("\n").split(maxsplit=7)
            if len(values) == 8 and values[5] == "01" and values[7] == socket:
                fail("an App Server listener appeared before the captured wrapper could be launched")
except OSError:
    fail("cannot inspect Unix listeners before restart")
if any(not key or "=" in key for key in environment):
    fail("the captured npm environment is invalid")
environment["RUST_LOG"] = required_rust
environment["LOG_FORMAT"] = required_format
try:
    with open("/dev/null", "rb", buffering=0) as stdin_handle, open(log_path, "ab", buffering=0) as log_handle:
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
        incomplete "$DISCOVERY_ERROR; no standalone fallback was launched"
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
        incomplete 'could not retain the verified npm wrapper identity; no process was stopped'
        return 1
    fi
    if confirm_restart "$old_pid" "$old_executable" "$TARGET_SOCKET"; then
        :
    else
        incomplete 'the current App Server needs a restart before behavioral verification; no process was stopped'
        return 1
    fi
    if acquire_startup_lock "$socket"; then
        :
    else
        incomplete "$RESTART_ERROR"
        return 1
    fi
    if discover_app_server "$socket"; then
        if [[ "$TARGET_RECORD" != "$old_record" ]]; then
            if validate_discovered_runtime; then
                printf 'A concurrent verified App Server replacement appeared before restart; leaving it running.\n'
                release_startup_lock
                return 0
            fi
            incomplete "$RESTART_ERROR; no process was stopped"
            release_startup_lock
            return 1
        fi
    else
        incomplete "the confirmed App Server target disappeared before restart: $DISCOVERY_ERROR; no process was stopped"
        release_startup_lock
        return 1
    fi
    if send_term "$old_pid" "$old_start_ticks" "$old_executable" "$socket"; then
        :
    else
        incomplete "${TERMINATION_ERROR:-could not terminate the verified listener}; no other process was targeted"
        release_startup_lock
        return 1
    fi
    printf 'Stopped only verified listener PID %s; restoring its captured app-managed npm wrapper.\n' "$old_pid"
    if wait_for_target_departure "$socket" "$old_record" "$old_parent_pid" "$old_parent_start_ticks" "$old_parent_executable"; then
        :
    else
        incomplete "$RESTART_ERROR; no standalone fallback was launched"
        release_startup_lock
        return 1
    fi
    if [[ "$RESTART_OUTCOME" == concurrent-replacement ]]; then
        release_startup_lock
        return 0
    fi
    if launch_same_style "$old_launch_plan"; then
        :
    else
        incomplete "$LAUNCH_ERROR; no standalone fallback was launched"
        release_startup_lock
        return 1
    fi
    if wait_for_replacement "$socket" "$old_record" "$LAUNCHED_WRAPPER_PID" "$LAUNCHED_WRAPPER_START_TICKS" "$old_parent_executable"; then
        :
    else
        incomplete "$RESTART_ERROR; no standalone fallback was launched"
        release_startup_lock
        return 1
    fi
    release_startup_lock
    printf 'Verified replacement listener PID %s at %s with its socket, log, and trace environment.\n' "$TARGET_PID" "$TARGET_SOCKET"
}

ensure_runtime_logging() {
    local socket="$1" status
    if discover_app_server "$socket"; then
        :
    else
        incomplete "$DISCOVERY_ERROR; no standalone fallback was launched"
        return 1
    fi
    if log_is_regular "$TARGET_LOG_PATH"; then
        :
    else
        incomplete "$LOG_ERROR; no process was stopped"
        return 1
    fi
    if runtime_logging_ready "$TARGET_PID"; then
        printf 'The current verified listener already has JSON trace logging.\n'
        return 0
    else
        status=$?
    fi
    if ((status == 2)); then
        incomplete "$RUNTIME_ENV_ERROR; no process was stopped"
        return 1
    fi
    if ((status != 1)); then
        incomplete "${RUNTIME_ENV_ERROR:-could not inspect the listener environment}; no process was stopped"
        return 1
    fi
    printf 'The current verified listener needs a restart to receive the .bashrc trace settings.\n'
    restart_app_server "$socket"
}

install_mam() {
    local checkout="$1" bin_dir mam_bin mam_python
    if ! command -v pipx >/dev/null 2>&1; then
        incomplete 'pipx is required; run sudo apt install pipx before bash scripts/install.sh'
        return 1
    fi
    printf 'Installing MAM from %s\n' "$checkout"
    if ! pipx install --force "$checkout"; then
        incomplete 'pipx could not install MAM from this checkout'
        return 1
    fi
    bin_dir="$(pipx environment --value PIPX_BIN_DIR 2>/dev/null || true)"
    bin_dir="${bin_dir:-${PIPX_BIN_DIR:-$HOME/.local/bin}}"
    mam_bin="$bin_dir/mam"
    mam_python="$(sed -n '1{s/^#!//;p;}' "$mam_bin" 2>/dev/null || true)"
    if [[ ! -x "$mam_bin" || ! -x "$mam_python" ]] || ! "$mam_bin" --help >/dev/null; then
        incomplete "pipx did not produce a working mam entry point at $mam_bin"
        return 1
    fi
    export PATH="$bin_dir:$PATH"
    INSTALLED_MAM_PYTHON="$mam_python"
}

run_checks() {
    local checkout="$1" python="$2" socket="$3" log_path="$4"
    printf 'Running MAM unit tests from the installed environment.\n'
    if ! "$python" -B -m unittest discover -s "$checkout/tests" -v; then
        incomplete 'MAM unit tests failed'
        return 1
    fi
    printf 'Running live behavioral App Server compatibility checks.\n'
    if ! MAM_APP_SERVER_SOCKET="$socket" MAM_APP_SERVER_LOG="$log_path" "$python" -m multi_agent_manager.wait_compat; then
        incomplete 'behavioral App Server compatibility tests failed'
        return 1
    fi
}

main() {
    local checkout config socket
    if (($#)); then
        printf 'usage: bash scripts/install.sh\n' >&2
        return 64
    fi
    if ! checkout="$(repository_root)" || [[ ! -f "$checkout/pyproject.toml" || ! -d "$checkout/tests" ]]; then
        incomplete 'scripts/install.sh must be run from a multi-agent-manager checkout'
        return 1
    fi
    if ! config="$(find_project_config "$checkout")" || ! validate_project_config "$config"; then
        incomplete 'create a valid .mam/env.json above this checkout before installing'
        return 1
    fi
    printf 'Using project configuration %s\n' "$config"
    update_bashrc || return 1
    export PATH="$HOME/.local/bin:$PATH"
    install_mam "$checkout" || return 1

    socket="${MAM_APP_SERVER_SOCKET:-$HOME/.codex/app-server-control/app-server-control.sock}"
    ensure_runtime_logging "$socket" || return 1
    run_checks "$checkout" "$INSTALLED_MAM_PYTHON" "$socket" "$TARGET_LOG_PATH"
    printf 'MAM installation and behavioral compatibility: PASS\n'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
