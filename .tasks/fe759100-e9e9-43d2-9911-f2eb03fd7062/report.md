# wuwen-4090-3 Vulkan 诊断与修复报告

## 结论

`wuwen-4090-3` 的共享 Table-1000 环境失败并非 ICD 路径、NVIDIA
kernel/userspace 版本、GPU/DRM 映射或 `/dev/nvidia-caps` 缺失造成。容器镜像
缺少 GLVND 的 EGL dispatcher `libEGL.so.1`（Ubuntu `libegl1` 包），而 NVIDIA
ICD 的 `libGLX_nvidia.so.0` 在协商阶段会动态加载它。加载失败被 ICD 折叠为
`VK_ERROR_INITIALIZATION_FAILED (-3)`，进而使 loader 找不到
`vkCreateInstance` 并返回 `VK_ERROR_INCOMPATIBLE_DRIVER (-9)`。

已在 4090-3 以最小范围修复：只新增 `/usr/local/lib/libEGL.so.1.1.0` 和
`/usr/local/lib/libEGL.so.1 -> libEGL.so.1.1.0`，随后执行 `ldconfig`。没有运行
`apt install`，没有更新 Mesa/DRM/NVIDIA 包、内核驱动或设备映射，也没有重启。
普通 `activate.sh` 环境（未设置 `LD_LIBRARY_PATH`）下，Vulkan instance、ManiSkill
CPU 和 render smoke 均通过。

## 可复现证据

- 激活后 `VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json`；JSON 指向正常的
  `libGLX_nvidia.so.0`。其真实目标和 `libnvidia-glcore` 都是 `580.82.07`，不存在
  `LD_LIBRARY_PATH` 或 `LD_PRELOAD` 污染，`NVIDIA_DRIVER_CAPABILITIES=all`。
- 修复前 `ldconfig -p` 没有 `libEGL.so.1`，`dpkg-query` 显示 `libegl1` 未安装，
  `.venv/bin/python` 的 `ctypes.CDLL("libEGL.so.1")` 明确报 ENOENT。保留的
  `icd-negotiate-ld-debug.log` 显示 `libGLX_nvidia.so.0` 依次尝试全部默认
  library path 后仍找不到 `libEGL.so.1`。
- 同一 ICD 的 `vk_icdNegotiateLoaderICDInterfaceVersion(7)` 修复前返回 `-3`，
  `vk_icdGetInstanceProcAddr(NULL, "vkCreateInstance")` 及 instance-extension
  查询均为 NULL；本机健康对照返回 `0` 和非空指针。
- 4090-3 的四张可见 GPU 都有 NVIDIA DRM card/render 节点；`nvidia-smi` 显示空闲，
  `CUDA_VISIBLE_DEVICES=0` 下 torch 报 `cuda_available=True`、一张 RTX 4090。
  因此没有把缺少 `nvidia-caps` 当作根因。

## 因果验证与修复边界

`apt-get -s install --no-install-recommends libegl1` 会同时引入 Mesa 包并升级 13 个
Mesa/libdrm 包，故没有采用它。作为无系统改动的因果实验，从 Ubuntu noble main 下载
精确的 `libegl1=1.7.0-1build1`（已安装的 `libglvnd0` 也是 `1.7.0-1build1`）：

- deb SHA-256：`e549f7776216f7bd3b1c216729fb40a97a562e2eb7c563cde632b4931f9a4e57`
- 解包的 `libEGL.so.1.1.0` SHA-256：
  `875ecbb2a07d60e32216c9f102965abc1e9cc1da7789558e2e9b8b9c107e231d`
- 解包位置：
  `/mnt/public/xcj/Projects/table-1000/table-1000/outputs/fe759100-e9e9-43d2-9911-f2eb03fd7062/remote-wuwen-4090-3/egl-dispatch-libegl1-1.7.0-1build1/root/usr/lib/x86_64-linux-gnu/`

仅以该目录注入 `LD_LIBRARY_PATH` 后，ICD 协商变为 `0`、入口指针恢复、标准 loader
的 `vkCreateInstance=0`，CPU/render smoke 都通过。这直接证明 dispatcher 缺失是
充分原因。随后确认 `/usr/local/lib/libEGL.so.1*` 不存在后，复制相同真实文件、创建
SONAME symlink 并运行 `ldconfig`，得到持久的最小修复。若要回滚，只需删除这两个
`/usr/local/lib` 文件并再次运行 `ldconfig`。

## 验证结果

在修复后，未设置 `LD_LIBRARY_PATH`、`CUDA_VISIBLE_DEVICES=0`，并使用
`TABLE1000_CACHE_DIR=outputs/remote-wuwen-4090-3/runtime-cache`：

- 标准 Vulkan loader：`vkCreateInstance=0`，instance 非空；
- `scripts/smoke_maniskill.py --level cpu`：`reset_ok=True`、`step_ok=True`；
- `scripts/smoke_maniskill.py --level render`：`reset_ok=True`、`step_ok=True`。

日志和诊断文件均在：
`/mnt/public/xcj/Projects/table-1000/table-1000/outputs/fe759100-e9e9-43d2-9911-f2eb03fd7062/remote-wuwen-4090-3/`

- `icd-negotiate-ld-debug.log`：修复前的动态加载失败证据；
- `vkcreate-after-usrlocal-egl.log`：修复后的标准 loader probe；
- `cpu-after-usrlocal-egl.log`、`render-after-usrlocal-egl.log`：最终 smoke。

## Workspace 与交付

- Workspace：`/mnt/public/xcj/Projects/table-1000/workspace/fe759100-e9e9-43d2-9911-f2eb03fd7062/table-1000`
- Branch / base：`task/fe759100-e9e9-43d2-9911-f2eb03fd7062` /
  `b56e55ef6c799c800c12573bde1b0a7a3c25556c`
- 未改业务代码，因此无业务代码 commit；worktree 保持干净。
