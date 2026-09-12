# C1 GPU PID visibility evidence

All collection was read-only over SSH to wuwen-4090-1.  No evaluation,
service, GPU, namespace, package, runtime, or configuration was changed.

## Environment

Captured 2026-09-13 00:57--01:02 CST:

- SSH identity was root; hostname was
  is-ddfwxekq6usner7v-devmachine-0, as expected.
- PID 1 is runsvdir -P /opt/devmachine/init/service.  /proc is a normal
  proc mount in pid:[4026541571]; PID 1 and the SSH shell use that same
  visible namespace.
- The known C1 formal launcher 2130358 and its local tree were readable:
  2130358 (formal --gpu 1) -> 2130667 (benchmark) -> 2130759
  (robot server) -> 2130887 (rmbench_sim_worker, pt_main_thread).
  Each status file reported a single visible NSpid value.  At 01:02,
  2130887 was Ssl and its NSpid was 2130887.

## NVML versus visible /proc

- nvidia-smi reported all eight cards with 13--17 GiB used.  Its
  compute-app query had 25 rows and rendered process_name as [Not Found]
  for every row.
- Representative NVML PIDs 1966034, 2020663, 2200274, 2281919, 2522345,
  2909622, and 3250550 had no corresponding directory in the current
  /proc when checked.  These are values returned by NVML; this session has
  no allowed host-side PID-namespace mapping with which to associate them.
- Confirmed local worker 2130887 was not a numeric member of the
  contemporaneous NVML compute-PID list.  This shows that treating the
  visible container PID and an NVML PID as the same identifier is invalid
  here; it does not identify that worker's host PID.
- One earlier read saw a local process with numeric PID 2522345, while a
  subsequent read did not, even though NVML still returned that number.
  The allowed observations cannot distinguish PID reuse, process teardown,
  or different PID views, so it is deliberately not used as a mapping.

## Installed nvitop behavior

wuwen-4090-1 has nvitop 1.7.1 at
/usr/local/lib/python3.12/dist-packages/nvitop/api/process.py.

- Lines 120--140: auto_garbage_clean catches host.PsutilError.  When
  cmdline uses its configured fallback, it returns No Such Process; an
  AccessDenied exception is specifically rendered No Permissions.
- Lines 799--847 give username/CPU-related fields an NA fallback.
- Lines 901--915 decorate GpuProcess.cmdline with the No Such Process
  fallback and obtain the command through self.host.cmdline().

Thus the nvitop text means its psutil host-process lookup could not be
completed.  It can occur if the process has exited between samples, or if
the NVML PID is outside the current process view; it is not evidence by
itself that GPU memory disappeared or that the workload belongs to a
different user.

## Evaluation progress

The owner had published 00:53 terminal counts of 52 (GPU1 run) and 11
(GPU7 run).  This read-only check found:

- GPU1 formal run
  c_rearrange_serial_lag30_trainseed1_evalseed1_100ep_r3:
  56 diagnostics lines; last record episode_id 55, result Success;
  file mtime 00:58:46 CST.
- GPU7 formal run
  c_rearrange_serial_lag30_trainseed0_evalseed2_100ep_r3:
  14 diagnostics lines; last record episode_id 13, result Fail;
  file mtime 00:58:13 CST.

Both counts increased from the owner's published baseline.  A terminal
Fail record is an episode result, not a conclusion that the whole formal
process has exited; the local worker was still present at 01:02.
