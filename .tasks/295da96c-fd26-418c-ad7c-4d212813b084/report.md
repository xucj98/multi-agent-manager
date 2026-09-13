# C3 冻结工具与执行身份核对

只读核验完成。C3 `probe_side_effect_check` 部署的工具、tests、README 与 source audit 均同时匹配给定 SHA-256 和 MAM 本机副本；`plan_20260914_v4/plan.json` 为预期 SHA `4408a8732f3fa259f5224de6dfe7c40add97e40e5a7fc511a076f8f4fb5a9916`，其 YAML、保存 request 及六个冻结源码引用也全部匹配计划记录。

冻结运行树 `c3-highfreq-engineering-20260914` 的 `openpi`、`robot-bridge`、`RMBench` 分别处于 `0ce566bd`、`ffa12249`、`6abebf08`，三个 worktree 均 clean。checkpoint 路径为 put-back J train0 / step 20000；只确认 metadata/params 存在，未读取参数树。

README 的模板 Python 是 `FROZEN/openpi/.venv/bin/python`，模板 PYTHONPATH 指向冻结 bridge 和 openpi-client。冻结 venv 的 editable metadata 指向同一 frozen OpenPI 树；仅用标准库 `importlib.machinery.PathFinder`（未执行目标包）按该模板解析，`openpi` 落在 `FROZEN/openpi/src/openpi/__init__.py`，`robot_bridge` 落在 `FROZEN/robot-bridge/robot_bridge/__init__.py`。

发现两项需由后续运行者显式处理的模板差异，未改文件：

- README 的 `TOOL` 仍指向 MAM 本机 `.tasks` 副本；C3 运行必须改为已核验的部署根 `/mnt/public/xcj/Projects/state-vla/workspace/0acf5d43-91b6-4171-b727-e3fe0f7e7939/probe_side_effect_check/tools/probe_side_effect_check.py`。
- README 直调模板只固定 `RB_OPENPI_POLICY_DIR` 和 `PYTHONPATH`。已记录的 baseline launcher 还固定 `CUDA_VISIBLE_DEVICES=0`、`SAPIEN_RENDER_DEVICE=cuda:0`、`VK_ICD_FILENAMES=/etc/vulkan/icd.d/nvidia_icd.json`，且 policy 子进程固定 `XLA_PYTHON_CLIENT_MEM_FRACTION=0.40`。这是模板与已记录 baseline 的静态差异，不能据此推断未来继承环境的实际值。

未运行测试、Python 包导入、backend/model、JAX device、GPU、环境 reset 或任何 checkpoint 加载；未改冻结三库、计划、源码或既有证据。核验不构成 `3 action + 5 probe` 执行授权。

完整机器可读回执：`evidence/c3_probe_identity_receipt.json`，SHA-256 `bf20b8ec6603d3d138d8c180843757e34405cae92ad78a0ff36125a052ff7924`。
