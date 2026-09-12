# C1/C2/C3 PID visibility evidence (2026-09-13 CST)

This is a compact record of read-only command results. It contains no process
environment, credentials, or `/proc/*/fd/0` data.

## C1: `wuwen-4090-1`

- Hostname: `is-ddfwxekq6usner7v-devmachine-0`; caller PID namespace:
  `pid:[4026541571]`; 8 RTX 4090 GPUs; NVIDIA driver/NVML `550.127.08`.
- `/usr/bin/nvidia-smi` reported all active process names as `[Not Found]`.
  `nvidia-smi -q -d PIDS` included both compute and graphics entries, including
  `C+G` and separate `G` entries. The reported numeric PIDs were absent from
  the caller's `/proc` in the candidate run.
- Local formal-evaluation launcher/worker pairs stayed alive before and after
  the probe (for example, launcher `2130358`, worker `2130887`), with elapsed
  time increasing. The NVML list did not contain a verified mapping to them.
- The installed nvitop is `1.7.1`. Its `Device.processes()` output returned
  NVML PIDs with `command='No Such Process'`, `user='N/A'`, and `cpu='N/A'` for
  both a compute-containing GPU and GPU 3's graphics entries.

## C2: `wuwen-4090-2`

- Hostname: `is-ddj72hiexddjfwo6-devmachine-0`; caller PID namespace:
  `pid:[4026541748]`; 8 RTX 4090 GPUs; driver/NVML `550.127.08`.
- At the test window the GPU6 reset gate was alive as local launcher `1970635`
  and worker `1970705`; its command specifies `--device 6`.
- In the same window GPU6's driver-visible rows included `488723`, `488726`,
  and `4010425` (the latter had a `C+G` context). All were absent from the
  current `/proc`. This is evidence of unusable NVML PID identity at the
  caller, not evidence that any particular local PID owns one of those rows.
- A disposable virtual environment with pinned `nvitop==1.7.1`,
  `nvidia-ml-py==13.595.45`, and `psutil==7.2.2` returned
  `command='No Such Process'`, `user='N/A'`, and `cpu='N/A'` for the
  driver-visible GPU6 graphics PID.

## C3: `wuwen-4090-3`

- Hostname: `is-ddj72jhhjdy7hiyj-devmachine-0`; caller PID namespace:
  `pid:[4026541020]`; 4 RTX 4090 GPUs; driver/NVML `580.82.07`.
- During a real GPU0 evaluation, `nvidia-smi` reported local PID `1032416` as
  compute and local PID `1032527` as `C+G`, with real Python paths. Both
  remained alive before and after nvitop runs. At 01:42:20 CST it also reported
  compute PIDs `1050583` and `1050584`; GPU0 used `14173MiB / 24564MiB`.
- C3's **pre-existing** `/root/.local/bin/nvitop` resolves to
  `/root/.local/share/pipx/venvs/nvitop/bin/nvitop`. In an SSH login shell it
  reports `nvitop 1.7.1`; a prior non-login `command -v` result was therefore
  not evidence that C3 lacked nvitop.
- At 01:42:20/21 CST, the original login-shell commands
  `nvitop --once --readonly --compute --only 0` and
  `nvitop --once --readonly --graphics --only 0` showed real command/user/CPU
  fields. The compute view listed PIDs `1032416`, `1032527`, `1050583`, and
  `1050584`, all as `root`, with numeric CPU values; the graphics view listed
  PID `1032527` as `root` with a numeric CPU value. `ps` in the same window
  confirmed those four local PIDs and users.
- The temporary duplicate `/root/.local/bin/nvitop-c3` link and
  `/root/.local/share/venvs/nvitop-c3` venv were confirmed to be task-created,
  then removed. The original pipx link and venv were preserved.

## Interpretation boundary

The observations establish that C1/C2's `nvidia-smi`/nvitop display failure is
downstream of a driver-visible PID that is not resolvable in the current PID
namespace. They do not establish a host-to-container PID mapping. C3's
current R580/runtime behavior is a useful platform comparison, but does not by
itself prove that the driver version caused the difference.
