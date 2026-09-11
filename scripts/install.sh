#!/usr/bin/env bash
# Install this checkout, prepare App Server trace logging, and test it.
set -euo pipefail

readonly TRACE_BEGIN='# >>> MAM Codex App Server trace >>>'
readonly TRACE_END='# <<< MAM Codex App Server trace <<<'
readonly RUST_LOG_VALUE='off,codex_app_server::message_processor=trace,codex_app_server::app_server_tracing=info'
readonly LOG_FORMAT_VALUE='json'
readonly RESTART_WAIT_SECONDS=20

TARGET_RECORD=''
TARGET_PID=''
TARGET_START_TICKS=''
TARGET_EXECUTABLE=''
TARGET_SOCKET=''
DISCOVERY_ERROR=''
RUNTIME_ENV_ERROR=''
RESTART_ERROR=''

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
    local socket="$1" result
    local -a fields=()
    DISCOVERY_ERROR=''
    if ! result="$(python3 - "$socket" 2>&1 <<'PY'
import os
from pathlib import Path
import stat
import sys

socket = sys.argv[1]

def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)

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
            fields = line.rstrip("\n").split(maxsplit=7)
            if len(fields) == 8 and fields[5] == "01" and fields[7] == socket:
                kernel_inode = fields[6]
                break
except OSError as exc:
    fail(f"cannot inspect Unix listeners: {exc}")
if not kernel_inode or not kernel_inode.isdecimal():
    fail(f"no listening Unix socket at {socket}")

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

def app_server_arguments(values):
    if "app-server" not in values:
        return False
    return any(
        value == "--listen=unix://" or (value == "--listen" and index + 1 < len(values) and values[index + 1] == "unix://")
        for index, value in enumerate(values)
    )

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
for pid in owners:
    try:
        state, parent, start_ticks = proc_fields(pid)
        child_arguments = arguments(pid)
        executable = os.path.realpath(f"/proc/{pid}/exe")
        parent_state, _, _ = proc_fields(parent)
        parent_arguments = arguments(parent)
        parent_executable = os.path.realpath(f"/proc/{parent}/exe")
    except (OSError, ValueError):
        continue
    if state == "Z" or parent <= 1 or parent_state == "Z" or not app_server_arguments(child_arguments):
        continue
    if not app_server_arguments(parent_arguments) or not any(os.path.basename(arg) == "codex" for arg in parent_arguments):
        continue
    if os.path.basename(parent_executable) not in {"node", "nodejs"} or not os.access(executable, os.X_OK):
        continue
    candidates.append((pid, start_ticks, executable, parent, parent_executable))

if len(candidates) != 1:
    if not candidates:
        fail("the socket owner is not the expected app-managed npm Codex App Server listener")
    fail(f"more than one validated app-managed Codex App Server listener owns {socket}")

pid, start_ticks, executable, parent, parent_executable = candidates[0]
values = (pid, start_ticks, executable, socket, socket_stat.st_ino, kernel_inode, parent, parent_executable)
if any("\n" in str(value) or "\r" in str(value) for value in values):
    fail("the App Server target contains an unsafe line break")
print(*values, sep="\n")
PY
)"; then
        DISCOVERY_ERROR="${result:-unable to inspect the App Server listener}"
        return 1
    fi
    mapfile -t fields <<< "$result"
    if ((${#fields[@]} != 8)); then
        DISCOVERY_ERROR='invalid App Server listener identity'
        return 1
    fi
    TARGET_RECORD="$result"
    TARGET_PID="${fields[0]}"
    TARGET_START_TICKS="${fields[1]}"
    TARGET_EXECUTABLE="${fields[2]}"
    TARGET_SOCKET="${fields[3]}"
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
    fi
    status=$?
    RUNTIME_ENV_ERROR="$result"
    return "$status"
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

wait_for_replacement() {
    local socket="$1" old_record="$2" deadline=$((SECONDS + RESTART_WAIT_SECONDS)) status
    RESTART_ERROR=''
    while ((SECONDS < deadline)); do
        if discover_app_server "$socket" && [[ "$TARGET_RECORD" != "$old_record" ]]; then
            if runtime_logging_ready "$TARGET_PID"; then
                return 0
            fi
            status=$?
            if ((status == 2)); then
                RESTART_ERROR="$RUNTIME_ENV_ERROR"
            else
                RESTART_ERROR='the replacement listener appeared without the required trace logging environment'
            fi
            return 1
        fi
        sleep 0.2
    done
    RESTART_ERROR="no verified app-managed replacement listener appeared within ${RESTART_WAIT_SECONDS}s"
    return 1
}

restart_app_server() {
    local socket="$1" old_record old_pid old_executable
    if ! discover_app_server "$socket"; then
        incomplete "$DISCOVERY_ERROR; no standalone fallback was launched"
        return 1
    fi
    old_record="$TARGET_RECORD"
    old_pid="$TARGET_PID"
    old_executable="$TARGET_EXECUTABLE"
    if ! confirm_restart "$old_pid" "$old_executable" "$TARGET_SOCKET"; then
        incomplete 'the current App Server needs a restart before behavioral verification; no process was stopped'
        return 1
    fi
    if ! discover_app_server "$socket" || [[ "$TARGET_RECORD" != "$old_record" ]]; then
        incomplete 'the confirmed App Server target changed before restart; no process was stopped'
        return 1
    fi
    if ! send_term "$old_pid"; then
        incomplete "could not terminate verified listener PID $old_pid; no other process was targeted"
        return 1
    fi
    printf 'Stopped only verified listener PID %s; waiting for its app-managed replacement.\n' "$old_pid"
    if ! wait_for_replacement "$socket" "$old_record"; then
        incomplete "$RESTART_ERROR; no standalone fallback was launched"
        return 1
    fi
    printf 'Verified replacement listener PID %s at %s.\n' "$TARGET_PID" "$TARGET_SOCKET"
}

send_term() {
    command kill -TERM -- "$1"
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
    local checkout="$1" python="$2"
    printf 'Running MAM unit tests from the installed environment.\n'
    if ! "$python" -B -m unittest discover -s "$checkout/tests" -v; then
        incomplete 'MAM unit tests failed'
        return 1
    fi
    printf 'Running live behavioral App Server compatibility checks.\n'
    if ! "$python" -m multi_agent_manager.wait_compat; then
        incomplete 'behavioral App Server compatibility tests failed'
        return 1
    fi
}

main() {
    local checkout config socket status
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
    if ! discover_app_server "$socket"; then
        incomplete "$DISCOVERY_ERROR; no standalone fallback was launched"
        return 1
    fi
    if ! runtime_logging_ready "$TARGET_PID"; then
        status=$?
        if ((status == 2)); then
            incomplete "$RUNTIME_ENV_ERROR; no process was stopped"
            return 1
        fi
        printf 'The current verified listener needs a restart to receive the .bashrc trace settings.\n'
        restart_app_server "$socket" || return 1
    else
        printf 'The current verified listener already has JSON trace logging.\n'
    fi
    run_checks "$checkout" "$INSTALLED_MAM_PYTHON"
    printf 'MAM installation and behavioral compatibility: PASS\n'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
