# 最终交付：Table-1000 MAM 独立 worktree 环境

- task：`b52655b9-cb65-4c6e-94be-2cad789235e6`
- worktree：`/mnt/public/xcj/Projects/table-1000/workspace/b52655b9-cb65-4c6e-94be-2cad789235e6/table-1000`
- branch：`task/b52655b9-cb65-4c6e-94be-2cad789235e6`
- 交付 HEAD：`f8340d5de7ac5452a6a8d726c1fc11047c0ae6b1`

提交链：`2af4b12`（MAM 入口）、`d30dca0`（持久 symlink package
store）、`b049801`（可重复 setup/archive clean）、`9fe95e0`（peer
运行说明）、`b56e55e`（无残留 cleanup 幂等退出码）、`7b3a907`（peer Vulkan
运行前提与 probe）、`fda9506`（最小 peer EGL 修复说明）、`f8340d5`（EGL 修复范围
澄清）。

## 一键入口与布局

从任意 cwd 创建或修复任务 worktree：

```bash
bash /mnt/public/xcj/Projects/table-1000/table-1000/scripts/worktree_env/mam_workspace_add.sh \
  TASK-ID BASE-COMMIT
```

入口通过 MAM 的 `.local/create_worktree.sh` 调用版本化 setup。每个 task 是真实、私有的
`.venv`，且仅有两个顶层业务软链接：

- `.cache -> /mnt/public/xcj/Projects/table-1000/table-1000/.cache`；
- `outputs -> /mnt/public/xcj/Projects/table-1000/table-1000/outputs/TASK-ID`。

canonical `.cache` 和 `outputs` 均为实体目录。历史 `outputs/` 迁移会先全量预检冲突，绝不
覆盖。运行时缓存写到 task-specific `outputs/runtime-cache`；`cleanup.sh` 只清理 worktree
的旧 runtime、pytest/ruff 和源 `__pycache__`，不触碰 `.venv` 或 outputs 成果。

## 依赖、链接策略和占用

默认完整依赖来自 `requirements/lock-linux-cu124-py312.txt`：Linux x86_64、Python 3.12、
CUDA 12.4，含 `torch==2.6.0+cu124`、`mani-skill==3.0.1`、`sapien==3.0.3` 和
`mplib==0.2.1`。

默认包模式为 `symlink`。持久 uv package store 为 `/mnt/public/xcj/cache/uv`，由 ignored
canonical `.local/worktree-env.conf` 指定；其中有 store 生命周期 marker，禁止运行
`uv cache clean`、任何 `uv cache prune` 或手工改删文件。当前 venv 有 `28,752` 个第三方
文件链接到该 store（例如 `.venv/bin/ruff` 指向 store archive）；editable `table1000`
固定从自身 worktree 以 `--no-deps --link-mode copy -e` 安装，避免共享 editable 元数据。

实测当前 `.venv` 占用 `22,002,176` B（表观 `8,537,687` B），全局 uv store 占用
`6,246,896,640` B。yrfs 即使同一 `st_dev` 也拒绝跨目录 hardlink（`EPERM`），reflink
也不支持；严格 `hardlink` 模式会做真实 inode/link-count 预检并失败，未将 copy fallback
误报为 hardlink 成功。

## 本机验证

在最终 symlink 环境和空闲 GPU 1 上执行：

```bash
TABLE1000_SMOKE_CUDA_VISIBLE_DEVICES=1 bash scripts/worktree_env/smoke.sh
bash scripts/worktree_env/cleanup.sh
```

全部通过：真实 GSO `Markings_Letter_Holder` 资产 probe、ManiSkill CPU、render、GPU
physics、Table-10 0002 `red-then-blue` reference replay（`valid=true`），以及 focused
data/CLI tests 的 `40 passed`。随后连续两次 `cleanup.sh` 都返回 0，worktree 无
`.table1000-runtime-cache`、`.pytest_cache`、`.ruff_cache` 或源 `__pycache__`。

独立 blank-context 验收只经 MAM 一键入口创建新 worktree：约 5 秒、私有 venv 约 21 MiB，
并完成完整 smoke（40 tests）和 cleanup。重复 repair 由独立 review 验证；archive preflight
和实际归档由 manager 的验收证据确认。

## 远端只运行验证和最小 EGL 修复

未在远端运行 uv、创建 venv 或写入 package store。`wuwen-4090-2`（选择 GPU 2）与
`wuwen-4090-3`（选择 GPU 0）都可直接运行共享 `.venv/bin/python`、导入
Torch 2.6.0+cu124 / ManiSkill 3.0.1，并完成真实 `Markings_Letter_Holder` 资产 probe；
结果在 task outputs 的各 `remote-wuwen-*` 目录下。

两机最初均缺 `libEGL.so.1`，使 NVIDIA ICD 的
`vk_icdGetInstanceProcAddr(NULL, "vkCreateInstance")` 返回 NULL，进而导致
`VK_ERROR_INCOMPATIBLE_DRIVER`。这是运行端的系统 EGL dispatch 缺失，不是 uv、Python
ABI、资产、链接模式或 venv 问题。`apt-get -s install --no-install-recommends libegl1` 会
升级 13 个 Mesa/DRM 包，因此没有运行 apt 安装。

改为最小、可核验修复：从精确 Ubuntu Noble `libegl1=1.7.0-1build1` deb
（SHA-256 `e549f7776216f7bd3b1c216729fb40a97a562e2eb7c563cde632b4931f9a4e57`）抽取
`libEGL.so.1.1.0`（SHA-256
`875ecbb2a07d60e32216c9f102965abc1e9cc1da7789558e2e9b8b9c107e231d`，SONAME
`libEGL.so.1`）。两机均先确认 `/usr/local/lib/libEGL.so.1` 和 `.1.1.0` 不存在，随后
只写入该真实文件和 `libEGL.so.1 -> libEGL.so.1.1.0` 链接并运行 `ldconfig`；未改 dpkg、
驱动、内核、uv 或 venv。

修复后两台 peer 的标准 loader probe 均为 `vulkan-icd=PASS`，并且 CPU 与 render
ManiSkill smoke 都完成 `reset_ok=True`、`step_ok=True`。4090-2 的持久修复日志和完成标记为
`outputs/remote-wuwen-4090-2/persistent-egl-{cpu-render.log,complete.txt}`；4090-3 的同类
日志为 canonical `outputs/fe759100-e9e9-43d2-9911-f2eb03fd7062/remote-wuwen-4090-3/`
下的 `cpu-after-usrlocal-egl.log` 和 `render-after-usrlocal-egl.log`。

以后在 peer 运行前可执行以下无副作用 probe；只有输出 `vulkan-icd=PASS` 后才开始
ManiSkill smoke：

```bash
cd /mnt/public/xcj/Projects/table-1000/workspace/TASK-ID/table-1000
.venv/bin/python -c 'import ctypes as c; c.CDLL("libEGL.so.1"); lib=c.CDLL("libGLX_nvidia.so.0"); f=lib.vk_icdGetInstanceProcAddr; f.argtypes=[c.c_void_p,c.c_char_p]; f.restype=c.c_void_p; assert f(None,b"vkCreateInstance"), "NVIDIA Vulkan ICD is unusable"; print("vulkan-icd=PASS")'
```

MAM 本机 ignored `.local/README.md` 已记录统一的 `~/.cache -> /mnt/public/xcj/cache` 迁移
与 `/mnt/public/xcj/cache/uv` 的不可 clean/prune 约定。`wuwen-2` 仅作早期只读参考，未创建
环境或写入文件，且不与本机共享存储。
