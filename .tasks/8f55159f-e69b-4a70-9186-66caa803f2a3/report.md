# pi05 retired virtual-environment cleanup

- Removed exactly `/mnt/public/xcj/Projects/RMBench/policy/pi05/.venv`.  The `/root/Projects/RMBench/policy/pi05/.venv` spelling was the same non-symlink directory (same device/inode) and is absent as well.
- Pre-removal `du -sh` was `9.0G`.  This is an apparent disk-use figure and does not establish the actual bytes freed because hardlinks may be present.
- Before removal, local and `wuwen-1` read-only `/proc` checks found no direct reference to either exact path spelling.  The checks covered process cwd, executable, root, open file descriptors, command line, environment, mappings, and mount information; the scanner and its ancestor processes were excluded to avoid self-matches.  No processes were stopped and the remote host was not changed.
- The target was asserted to be the expected directory, then deleted with `shutil.rmtree` without following contained symlinks.  Post-removal checks confirmed both path spellings are absent.
- Preserved and rechecked: `checkpoints`, `packages`, `scripts`, `src`, `pyproject.toml`, `uv.lock`, and shared uv Python `/root/.local/share/uv/python/cpython-3.11.14-linux-x86_64-gnu/bin/python3.11`.

No source, manifest, documentation, other environment, cache, checkpoint, remote-resource, or GPU changes were made.  No code commit is expected for this cleanup task.
