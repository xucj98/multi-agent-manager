# C2/C3 renderer 生命周期候选：整合交接

## 候选与范围

已在独立 RMBench worktree
`/mnt/public/xcj/Projects/workspace/923ea224-ab1e-4a48-830f-83d2e5969b76/RMBench`
从冻结基线 `9d8f47887a50ea691e5624de139f10bfcfb54412` 生成候选分支
`task/923ea224-ab1e-4a48-830f-83d2e5969b76`：

- `eba81b41b39652b940fdb6d93dc4451a91352960`：精确 cherry-pick 已验收的
  `17b55bff1c79a0c5a836d1da089765934cb3a5b0`。
- `77477931bee18c2476bea36b400ab45dc67d9ebe`：单独的 CPU-only 静态生命周期回归。

`git show --format=` 的旧 patch 与 `eba81b4` patch 用 `diff -u` 比较无输出。运行时改动仅为
`envs/_base_task.py` 的 8 行新增、1 行替换：模块级 `_PROCESS_RENDERER = None`，在
`setup_scene()` 内以 `global` 和空值守卫创建一次 `sapien.SapienRenderer()`，随后赋给
`self.renderer` 并继续传入 `self.engine.set_renderer(...)`。

`self.engine = sapien.Engine()`、`sapien.Scene(...)`、`self.engine.create_scene(...)` 及其后的
scene/物理/相机/灯光代码均留在每次 `setup_scene()` 路径内；bridge、RPC、Warp、seed、动作、观测、
video 和 timeout 均未改动。静态比较也确认：基线与候选都保留每次 setup 的 fresh engine，而只有候选
新增进程级 renderer 声明。

共享 renderer 的有效前提是一个 worker 不在进程内改渲染设备。现有单卡启动将物理卡映射为
`CUDA_VISIBLE_DEVICES=<card>`、`SAPIEN_RENDER_DEVICE=cuda:0`，满足此前约束；本候选未修改该设置。

## CPU 验证

```bash
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests \
  .venv/bin/python -m unittest -v \
  test_eval_diagnostics.EvalDiagnosticsRecorderTest.test_records_jsonl_and_aggregates_generic_schema \
  test_renderer_lifecycle.RendererLifecycleSourceTest
```

结果：**3 passed**。新增的两项测试只解析 `envs/_base_task.py` AST，不导入 SAPIEN；它检查模块级
singleton、`global` 空值守卫、唯一 renderer 构造、fresh engine、两条 scene 创建路径，以及将共享
renderer 交给 engine。`git diff --check 9d8f478..HEAD` 通过。

RMBench `.venv` 未安装 pytest，未为此安装或重建环境。全量 `unittest discover` 不适合作为 CPU 门禁：
现有 `test_dm05_integration.py` 会导入 SAPIEN，在无 ICD 的主机上阻塞；该本地测试进程已停止，未将其
视为通过或失败证据。没有 GPU run、远端写入、部署或活跃评测运行时修改。

这些 CPU 检查验证源码生命周期契约，**不替代** native renderer、40-reset 或 policy/video 验证。

## 诊断与结果口径保持不变

六个 C2/C3 partial 的可操作近因仍是同一 worker 内重复 renderer 创建；r2 原始证据中 episode id 22
先出现 `ErrorIncompatibleDriver`，随后 worker stdout EOF。SAPIEN/Vulkan/driver 的内部根因仍未被
该证据完全证明。C1 完整结果没有该 marker，保持有效。

episode 22 的 raw `seed_preflight.jsonl` 为 `accepted=null, response.status=error`。正式口径只能是
**22 个 terminal episodes + 1 条 reset-error record**，绝非 23 个有效 rollout；partial 不进入正式
分母，也不能在新 leaf 中拼接。

## 给 e690 的门禁交接（等待独立 review 后）

1. Manager 先独立审阅 `eba81b4` 与 `7747793`，确认目标部署树固定设备且干净；不得将候选直接写入
   活跃树。
2. 在获准的独立树和单一映射设备上，以原有 worker/reset harness 运行 **40 个连续 reset**
   （跨过旧的 episode id 22），不写 result leaf、不计分。门禁要求 40/40 accepted、exit 0，且 stderr/
   RPC 中没有 `ErrorIncompatibleDriver`、EOF、traceback 或 segfault。
3. 只在该门禁通过后，在每个被安排的目标 host 复用 e690 已有入口做 matching smoke2，例如：
   `run_memory_schema_eval.py --variant <fixed-variant> --checkpoint <approved-20000> --run-name <fresh-smoke-leaf> --gpu <assigned> --mode smoke`。
   保持原 checkpoint、配置、seed 和设备映射；验收 video/no-video、连续 accepted、产物、服务退出和
   worktree clean。
4. 通过 matching smoke 后，按 e690 已记录的 formal launch manifest 从新的 leaf 使用原始完整 seed
   列表运行 formal100。不要复用这六份 partial 的 22 条 terminal 或 reset-error 记录。

RMBench 候选树与 robot-bridge 独立树（仍为 `f9626636c4776d8eb15f9c556775cb2d12c000e5`）均干净并保留，
供独立 review；未做远端或 active-runtime 变更。
