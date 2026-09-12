# C1/C2 GPU PID visibility: platform-support reproduction draft

**Status: draft only. Do not send externally without user authorization.**

Subject: C1/C2 instance-local `nvidia-smi` / NVML process PID visibility

We see driver-visible GPU memory/process rows in two development instances,
but their PID and process-name fields cannot be resolved from the same
instance's process namespace.

## Minimal observations

| Instance | Hostname | Driver/NVML | Local result |
| --- | --- | --- | --- |
| C1 `wuwen-4090-1` | `is-ddfwxekq6usner7v-devmachine-0` | `550.127.08` | `nvidia-smi` reports active rows as `[Not Found]`; nvitop 1.7.1 reports `No Such Process` / `N/A` for compute and graphics contexts. |
| C2 `wuwen-4090-2` | `is-ddj72hiexddjfwo6-devmachine-0` | `550.127.08` | GPU6 had a live local renderer-reset gate, while its driver-visible compute/`C+G` PIDs were absent from the instance `/proc`; isolated nvitop 1.7.1 had the same fallback. |
| C3 `wuwen-4090-3` (comparison only) | `is-ddj72jhhjdy7hiyj-devmachine-0` | `580.82.07` | During a real GPU0 evaluation, C3's pre-existing login-shell pipx nvitop 1.7.1 and `nvidia-smi` both resolved local PID, command, user, CPU, compute and graphics (`C+G`) fields. |

The basic reproduction command is:

```bash
nvidia-smi -q -d PIDS
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader
```

On C1/C2, the PIDs listed by these commands are not visible in that instance's
`/proc` at the same sampling point. We deliberately did not infer a mapping
from memory size, device number, numeric PID collision, or workload arguments.

## Requested platform clarification / capability

Please confirm whether the C1/C2 runtime intentionally exposes host-namespace
NVML PIDs without an instance-local translation, and whether there is a
supported tenant-scoped monitoring endpoint or NVML/SMI adapter that provides
instance-visible process identity.

The needed result is per current instance only: each compute/graphics row needs
an authoritative local PID plus an anti-PID-reuse identity (for example process
start identity), with no general host `/proc` exposure or cross-tenant process
metadata. We are not requesting a host PID namespace mount, container rebuild,
driver change, or an online service restart.

The C3 R580 comparison is observational only; it does not establish a driver
version cause and should not be treated as a request for a user-side driver
upgrade.
