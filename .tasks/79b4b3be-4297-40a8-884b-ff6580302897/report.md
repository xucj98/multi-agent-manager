# Probe-0001 historical-video audit and physical replay

## Result

No artifact found establishes that any historical trajectory was accepted by the
user.  In particular, the 2026-08-20 physical-tidy run is a useful historical
candidate, not an acceptance claim.

The user supplied the previously viewed video as a read-only attachment:

- `/root/.codex/attachments/4fab4938-bbba-48fe-9e71-a57087bb125c/probe-0001-physical-tidy-best-effort (1).mp4`
- H.264, 2560x960, 20 fps, 1,319 frames, 65.95 s.
- SHA-256: `1a8b976645613214230eba725fdf567f3fe8557e5dd5495c9a32a0bca2cd3d90`.

That hash does not match the `6f8ad6088032e74ef17260e9b8177217151d1e29d946be855538505ee2b8d3cc`
recorded by historical commit `ea73166987d14242836269c9c205520731ad4940`
(`origin/feat/solver-tidy-0001`).  It must therefore be treated as a supplied
video evidence file, rather than represented as the exact 2026-08-20 artifact.
The source worklog describes that run as best effort (7/14 primary-support,
9/14 geometric), not a complete tidy demonstration.

The migration backup was checked by filenames only.  It contains Table-10 and
Open videos but no `probe-0001`, `solver-runs`, physical-tidy MP4, plan, or
trajectory artifact.  Participant-token files were not read.

## Historical-video inspection

Derived inspection files, all in the task output directory and without editing
the attachment:

- `historical-probe-0001/contact-sheet-keyframes-12.png` — twelve timestamped
  frames at 0, 4, 8, 12, 18, 24, 30, 36, 42, 48, 55, and 65 seconds.
- `historical-probe-0001/frame-000s-initial.png`,
  `frame-030s-cup-tipped.png`, and `frame-065s-final.png` — original-resolution
  inspection frames.

Visible evidence supports the user's visual concern: much of the tabletop is
open at the initial state; motion is predominantly repeated top-down
pick/place; and the green cup is visibly tilted at roughly 30 s and remains
tilted in the final frame.  The final storage basket is visibly crowded, with
a cable coil protruding.  The video alone does not establish the semantic
status of individual small objects, so this report does not call any object a
success or failure solely from its apparent final location.

## Fresh real physical replay

Worktree: `/mnt/public/xcj/Projects/table-1000/workspace/79b4b3be-4297-40a8-884b-ff6580302897/table-1000`

Source commit: `f8340d5de7ac5452a6a8d726c1fc11047c0ae6b1`.

Command (after sourcing `scripts/worktree_env/activate.sh` and `.venv/bin/activate`):

```bash
CUDA_VISIBLE_DEVICES=2 python scripts/record_reference_plans.py \
  --scene data/probe/scenes/t1k-probe-office-dense-0001-v1/scene.yaml \
  --plan tidy-video \
  --output-dir outputs/probe-0001-tidy-video-replay \
  --report outputs/probe-0001-tidy-video-replay/report.json \
  --stride 4 --fps 20 --hold-frames 20
```

This is a fresh seed-0 ManiSkill physical execution with `render_mode=rgb_array`;
the report records `maniskill3` / `physx_cpu`.  It executed 1,105 controller
steps.  Thirteen requests succeeded, then request 14/33 (`pick scissors`)
failed with `grasp_failed` because bilateral finger contacts were not
established.  The final GoalGraph check is false and hard constraints pass.
This is therefore a real, explicitly **partial** replay, not a replacement for
the historic user-provided video and not an accepted trajectory.

- Video: `probe-0001-tidy-video-replay/t1k-probe-office-dense-0001-v1__tidy-video.mp4`
  (512x512, 20 fps, 316 frames / 15.8 s; SHA-256
  `a634dda52aec8ddd1d1ddbfae3e43ed9914b2e2701677174feffa63ab09b99fa`).
- Execution report: `probe-0001-tidy-video-replay/report.json`.
- Visual evidence: `probe-0001-tidy-video-replay/contact-sheet-keyframes-12.png`.
  Its in-frame labels show the initial state, paper-wad A/B pick-discard,
  ink-cartridge placement, red/blue pen drawer insertion, the scissors pick,
  and the terminal FAIL frame.

No source files were changed.  `bash scripts/worktree_env/cleanup.sh` completed
with `PASS`; generated artifacts remain under the task outputs symlink for
manager review.
