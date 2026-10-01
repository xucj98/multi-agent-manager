#!/usr/bin/env bash
# Install this checkout and manage its project-local proactive wake scheduler.
# The detached daemon is owned by ``mam service``.
set -euo pipefail

readonly PATH_BEGIN='# >>> MAM PATH >>>'
readonly PATH_END='# <<< MAM PATH <<<'
CHECKOUT_ROOT=''
REQUESTED_VERSION=''
INSTALL_ARCHIVE="${MAM_INSTALL_ARCHIVE:-}"
MAM_ROOT=''
PROJECT_ROOT=''
LOCAL_BIN=''
MAM_BIN=''
SOURCE_PYTHON=''
INSTALLED_PYTHON=''
INSTALLED_VERSION=''
INSTALLED_COMMIT=''
INSTALL_TMP=''
COMPATIBILITY_JSON=''
INSTALL_EVIDENCE_PATH=''
INSTALL_TEST_COUNT=1
INSTALL_STARTED_EPOCH=''
INSTALL_TEST_SECONDS=0
INSTALL_PIPX_SECONDS=0
INSTALL_COMPAT_SECONDS=0

parse_args() {
    while (($#)); do
        case "$1" in
            --version)
                if (($# < 2)) || [[ -z "$2" || "$2" == -* ]]; then
                    incomplete '--version requires a release version'
                    return 1
                fi
                REQUESTED_VERSION="$2"
                shift 2
                ;;
            --version=*)
                REQUESTED_VERSION="${1#*=}"
                [[ -n "$REQUESTED_VERSION" ]] || { incomplete '--version requires a release version'; return 1; }
                shift
                ;;
            --)
                shift
                (($# == 0)) || { incomplete 'unexpected installer arguments'; return 1; }
                ;;
            *)
                incomplete "unexpected installer argument: $1"
                return 1
                ;;
        esac
    done
}

version_is_valid() {
    [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]]
}

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

prepare_release_source() {
    local archive="$INSTALL_ARCHIVE" url="" source_dir="$INSTALL_TMP/source" first
    mkdir -p -- "$source_dir"
    if [[ -z "$archive" ]]; then
        url="https://github.com/xucj98/multi-agent-manager/archive/refs/tags/v${REQUESTED_VERSION}.tar.gz"
        archive="$INSTALL_TMP/source.tar.gz"
        if ! command -v curl >/dev/null 2>&1; then
            incomplete 'curl is required to download the selected MAM release'
            return 1
        fi
        printf 'MAM installation: downloading %s\n' "$url"
        if ! curl -fsSL --retry 2 -o "$archive" -- "$url"; then
            incomplete "download failed for release $REQUESTED_VERSION"
            return 1
        fi
    elif [[ "$archive" != /* || ! -f "$archive" || -L "$archive" ]]; then
        incomplete 'MAM_INSTALL_ARCHIVE must be an absolute regular file'
        return 1
    fi
    if ! tar -xf "$archive" -C "$source_dir"; then
        incomplete "cannot unpack source archive: $archive"
        return 1
    fi
    first="$(find "$source_dir" -mindepth 1 -maxdepth 1 -type d -print -quit)"
    if [[ -n "$first" && -f "$first/pyproject.toml" ]]; then
        CHECKOUT_ROOT="$first"
    elif [[ -f "$source_dir/pyproject.toml" ]]; then
        CHECKOUT_ROOT="$source_dir"
    else
        incomplete 'source archive does not contain a pyproject.toml checkout'
        return 1
    fi
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
    local candidate
    for candidate in "$CHECKOUT_ROOT/.venv/bin/python" "$CHECKOUT_ROOT/.venv/bin/python3"; do
        if [[ -x "$candidate" ]]; then
            SOURCE_PYTHON="$candidate"
            break
        fi
    done
    if [[ -z "$SOURCE_PYTHON" ]] && command -v python3 >/dev/null 2>&1; then
        SOURCE_PYTHON="$(command -v python3)"
    elif [[ -z "$SOURCE_PYTHON" ]] && command -v python >/dev/null 2>&1; then
        SOURCE_PYTHON="$(command -v python)"
    fi
    if [[ -z "$SOURCE_PYTHON" ]]; then
        incomplete 'Python 3 is required to run the MAM installation smoke checks'
        return 1
    fi
    if [[ ! -x "$SOURCE_PYTHON" ]]; then
        incomplete "selected Python interpreter is not executable: $SOURCE_PYTHON"
        return 1
    fi
    if ! "$SOURCE_PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
        incomplete 'MAM requires Python 3.10 or newer'
        return 1
    fi
}

validate_release_metadata() {
    local release_file="$CHECKOUT_ROOT/multi_agent_manager/release.py"
    if [[ ! -f "$release_file" ]]; then
        incomplete 'release archive has no multi_agent_manager/release.py metadata'
        return 1
    fi
    if ! "$SOURCE_PYTHON" - "$release_file" "$REQUESTED_VERSION" "$CHECKOUT_ROOT" <<'PY'
import ast
from pathlib import Path
import re
import sys

release_file = Path(sys.argv[1])
requested = sys.argv[2]
checkout = Path(sys.argv[3])
project_file = checkout / "pyproject.toml"
if not project_file.is_file():
    raise SystemExit(1)
project_version = None
try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None
if tomllib is not None:
    try:
        document = tomllib.loads(project_file.read_text(encoding="utf-8"))
        project = document.get("project")
        project_version = project.get("version") if isinstance(project, dict) else None
    except (OSError, UnicodeDecodeError, ValueError):
        project_version = None
else:
    try:
        section = None
        for raw_line in project_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1]
            elif section == "project" and line.startswith("version") and "=" in line:
                project_version = ast.literal_eval(line.split("=", 1)[1].strip())
                break
    except (OSError, UnicodeDecodeError, ValueError, SyntaxError):
        project_version = None
if project_version != requested:
    raise SystemExit(1)
tree = ast.parse(release_file.read_text(encoding="utf-8"), filename=str(release_file))
values = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        try:
            values[node.targets[0].id] = ast.literal_eval(node.value)
        except (ValueError, TypeError):
            pass
version = values.get("RELEASE_VERSION")
tag = values.get("RELEASE_TAG")
commit = values.get("RELEASE_COMMIT")
if version != requested or tag != f"v{requested}" or not isinstance(commit, str):
    raise SystemExit(1)
if re.fullmatch(r"[0-9a-f]{40}", commit):
    raise SystemExit(0)
# Published archives must contain a substituted full commit; the checkout's
# ``$Format:%H$`` token is never accepted after extraction.
raise SystemExit(1)
PY
    then
        incomplete "release metadata does not match requested version $REQUESTED_VERSION"
        return 1
    fi
}

run_tests() {
    # Installation performs a bounded package/filesystem smoke.  The complete
    # release upgrade matrix is owned by scripts/test_integration.py.
    local checkout_pythonpath="$CHECKOUT_ROOT"
    if [[ -n "${PYTHONPATH:-}" ]]; then
        checkout_pythonpath+=":$PYTHONPATH"
    fi
    local started
    started="$(date +%s)"
    printf 'MAM installation: running checkout smoke with %s\n' "$SOURCE_PYTHON"
    if ! (
        cd -- "$CHECKOUT_ROOT"
        export PYTHONPATH="$checkout_pythonpath"
        unset MAM_SERVICE_MANAGER MAM_INSTALL_ARCHIVE PIPX_HOME PIPX_BIN_DIR
        "$SOURCE_PYTHON" -B -c '
from pathlib import Path
import multi_agent_manager.cli as cli
import multi_agent_manager.release as release
assert release.RELEASE_VERSION
assert callable(cli.main)
for relative in ("pyproject.toml", "scripts/install.sh", "multi_agent_manager/release.py"):
    assert (Path.cwd() / relative).is_file(), relative
'
    ); then
        incomplete 'checkout tests failed; pipx and the existing scheduler were left untouched'
        return 1
    fi
    INSTALL_TEST_SECONDS=$(( $(date +%s) - started ))
}

prepare_local_bin() {
    if [[ -z "${HOME:-}" || "$HOME" != /* || "$HOME" == *$'\n'* || "$HOME" == *$'\r'* ]]; then
        incomplete 'HOME must be a single-line absolute path'
        return 1
    fi
    LOCAL_BIN="${PIPX_BIN_DIR:-$HOME/.local/bin}"
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
    local started
    started="$(date +%s)"
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
    INSTALL_PIPX_SECONDS=$(( $(date +%s) - started ))
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
    if [[ -n "${PIPX_HOME:-}" ]]; then
        pipx_home="$PIPX_HOME"
    elif ! pipx_home="$(pipx environment --value PIPX_HOME 2>/dev/null)"; then
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

validate_installed_metadata() {
    local metadata
    if ! metadata="$(cd -- "$INSTALL_TMP" && "$INSTALLED_PYTHON" - "$REQUESTED_VERSION" <<'PY'
import re
import sys
from multi_agent_manager import release

requested = sys.argv[1]
version = getattr(release, "RELEASE_VERSION", None)
tag = getattr(release, "RELEASE_TAG", None)
commit = getattr(release, "RELEASE_COMMIT", None)
if version != requested or tag != f"v{requested}" or not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
    raise SystemExit(1)
print(version)
print(commit)
PY
)"; then
        incomplete "installed package metadata does not match release $REQUESTED_VERSION"
        return 1
    fi
    if [[ "$(wc -l <<<"$metadata")" -ne 2 ]]; then
        incomplete 'installed package returned incomplete release metadata'
        return 1
    fi
    INSTALLED_VERSION="$(sed -n '1p' <<<"$metadata")"
    INSTALLED_COMMIT="$(sed -n '2p' <<<"$metadata")"
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
if not isinstance(data, dict) or data.get("status") != "passed":
    raise SystemExit(1)
if not isinstance(data.get("stages"), list) or not isinstance(data.get("counts"), dict):
    raise SystemExit(1)
if data.get("code") not in {"compatibility", "live-delivery", None}:
    raise SystemExit(1)
PY
}

run_compatibility_check() {
    local output="$INSTALL_TMP/compatibility.json" errors="$INSTALL_TMP/compatibility.stderr" detail started
    started="$(date +%s)"
    printf 'MAM installation: running shared Codex compatibility acceptance\n'
    local probe_root="${PROJECT_ROOT:-$INSTALL_TMP}"
    if ! (cd -- "$probe_root" && env -u CODEX_THREAD_ID "$INSTALLED_PYTHON" -B -m multi_agent_manager.compatibility --output "$output" >"$INSTALL_TMP/compatibility.out" 2>"$errors"); then
        persist_compatibility_failure "$output" "$errors"
        detail="$(bounded_diagnostic "$INSTALL_TMP/compatibility.out" "$errors")"
        incomplete "shared Codex compatibility acceptance failed${detail:+: $detail}"
        return 1
    fi
    if ! validate_compatibility_json "$output"; then
        persist_compatibility_failure "$output" "$errors"
        detail="$(bounded_diagnostic "$output" "$errors")"
        incomplete "shared Codex compatibility acceptance returned invalid evidence${detail:+: $detail}"
        return 1
    fi
    COMPATIBILITY_JSON="$output"
    INSTALL_COMPAT_SECONDS=$(( $(date +%s) - started ))
    printf 'MAM installation: shared Codex compatibility PASS\n'
}

persist_compatibility_failure() {
    local output="$1" errors="$2" destination="$HOME/.local/share/multi-agent-manager/install-evidence" stamp raw
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    mkdir -p -- "$destination" || return 0
    raw="$destination/${stamp}-${REQUESTED_VERSION}.compatibility-failed.json"
    if [[ -f "$output" ]]; then
        cp -p -- "$output" "$raw" || true
    elif [[ -f "$errors" ]]; then
        cp -p -- "$errors" "$raw" || true
    fi
}

persist_install_evidence() {
    local destination="$HOME/.local/share/multi-agent-manager/install-evidence" stamp summary raw
    stamp="$(date -u +%Y%m%dT%H%M%SZ)"
    if ! mkdir -p -- "$destination"; then
        incomplete "cannot create persistent installation evidence directory: $destination"
        return 1
    fi
    raw="$destination/${stamp}-${INSTALLED_VERSION}.compatibility.json"
    summary="$destination/${stamp}-${INSTALLED_VERSION}.json"
    if ! cp -p -- "$COMPATIBILITY_JSON" "$raw"; then
        incomplete 'cannot retain compatibility evidence after installation'
        return 1
    fi
    if ! "$INSTALLED_PYTHON" - "$summary" "$raw" "$INSTALLED_VERSION" "$INSTALLED_COMMIT" "$INSTALL_TEST_COUNT" "$INSTALL_STARTED_EPOCH" "$INSTALL_TEST_SECONDS" "$INSTALL_PIPX_SECONDS" "$INSTALL_COMPAT_SECONDS" <<'PY'
import json
from pathlib import Path
import sys

summary_path = Path(sys.argv[1])
raw_path = Path(sys.argv[2])
version, commit = sys.argv[3:5]
test_count = int(sys.argv[5])
started = int(sys.argv[6])
stage_seconds = {
    "install_smoke": int(sys.argv[7]),
    "pipx_install": int(sys.argv[8]),
    "compatibility": int(sys.argv[9]),
}
compatibility = json.loads(raw_path.read_text(encoding="utf-8"))
summary_path.write_text(json.dumps({
    "version": version,
    "commit": commit,
    "tests": {"mode": "install-smoke", "count": test_count},
    "elapsed_seconds": max(0, int(__import__("time").time()) - started),
    "stages": stage_seconds,
    "compatibility": compatibility,
    "compatibility_evidence": str(raw_path),
}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
    then
        incomplete 'cannot write persistent installation summary'
        return 1
    fi
    INSTALL_EVIDENCE_PATH="$summary"
}

main() {
    parse_args "$@" || return 1
    INSTALL_STARTED_EPOCH="$(date +%s)"
    local local_checkout=''
    if [[ -z "$REQUESTED_VERSION" && -z "$INSTALL_ARCHIVE" ]]; then
        # Every invocation, including one launched from a checkout, resolves
        # a release archive so local and formal installs exercise one path.
        REQUESTED_VERSION='0.2.1'
    fi
    if [[ -z "$REQUESTED_VERSION" ]]; then
        REQUESTED_VERSION='0.2.1'
    fi
    if ! version_is_valid "$REQUESTED_VERSION"; then
        incomplete "invalid release version: $REQUESTED_VERSION"
        return 1
    fi
    if [[ -z "$CHECKOUT_ROOT" ]]; then
        create_install_tmp
        prepare_release_source
    fi
    choose_source_python
    validate_release_metadata
    run_tests
    prepare_local_bin
    install_with_pipx
    resolve_installed_python
    validate_installed_metadata
    if [[ -z "$INSTALL_TMP" ]]; then
        create_install_tmp
    fi
    run_compatibility_check
    persist_install_evidence
    printf 'MAM installation: PASS version=%s commit=%s tests=%s evidence=%s\n' "$INSTALLED_VERSION" "$INSTALLED_COMMIT" "$INSTALL_TEST_COUNT" "$INSTALL_EVIDENCE_PATH"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
