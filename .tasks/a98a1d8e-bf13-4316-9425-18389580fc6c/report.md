# V 工程独立审查：最新修复增量复核

本轮审查对象为 OpenPI `66d9253cf1bdc4971e59cdae7827846eccdb4714`、RMBench `f402babca5e7621be83f1725033e858aef69d091` 和 robot-bridge `20dae84e5fc2e48f93e72b5c1b8a0001071fec94`。本审查未修改作者分支；本地第二轮独立 worktree 为 `workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/latest/{openpi,RMBench}`，B 集群 profile worktree 固定在相同 OpenPI commit。

## 裁决

- **接受原 P1 的代码修复、初始锚点强制和五个真实任务的 CPU/norm 输入准入。** reset 后旧 pending 与反序 pending 都不能写入当前 episode；V 的第一帧强制为 `logical_step=0`；五个已就绪任务都实际 materialize 了 batch 32 和 18 个图像键。
- **不准入 V 的正式训练、运行时评测或“已恢复”主张。** 在不改变 batch 32、三相机、源分辨率、H=50/K=30、四条历史 query、18 槽或 Pi0.5/FSDP=1 的实际两步 profile 中，单张空闲 A800 在首个 optimizer update OOM。step-2 checkpoint 不存在，因此不能把 metadata gate 当作实际 policy restore，也没有 `[50,14]` 的生成 checkpoint 推理 mean/p95 可验收。
- Manager 已说明 BF16 model-only checkpoint 与 N/S/J 一致，**不将 optimizer-state resume 缺失列为缺陷**。完成 checkpoint 的 checkpoint-only policy restore 仍是必须实测的准入项；本轮只因 OOM 无法执行。

## P1、并发与初始锚点：接受

`VisualHistoryRuntime` 现在把 pending 绑定到 generation 和 state revision；`reset()` 增加 generation，`commit()` 对旧 generation 或旧 revision 返回 `False`。`Policy` 的 RLock 覆盖 V 的 prepare、JAX RNG split/model sample、commit 和 reset，因此普通 `Policy.infer()` 不会发生 commit 反序或 reset 穿插。

我没有只依赖新增单元测试，而是以真实 JAX `Policy`、18 个图像键和阻塞的 model sample 复现并发边界：in-flight old-episode infer 尚未返回时 reset 被锁阻塞；释放 infer 后 reset 清空 cache，new episode 的 step 0 只留下自身帧；JAX RNG 从 `[0,0]` 变为 `[1797259609,2579123966]`。同一独立脚本还验证 `prepare(0), prepare(30), prepare(60), commit(60), commit(30)` 会拒绝后者，reset 后旧 pending 被拒绝，且首帧 step 30 抛出 anchor 错误。证据见 `workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/evidence/policy_runtime_review.{py,json}`。

这与定向 suite 一致：

```text
JAX_PLATFORMS=cpu PYTHONPATH=src .venv/bin/pytest -q -m 'not manual' \
  src/openpi/training/visual_history_test.py src/openpi/training/config_test.py \
  src/openpi/training/checkpoint_metadata_test.py src/openpi/training/data_loader_test.py \
  src/openpi/policies/policy_test.py
# 45 passed, 2 deselected
```

训练侧 bounded LRU 也为 16 帧；本轮真实 preflight 的五行均实际达到该上限，而没有保留整个 worker 生命周期的数据集帧。

## 五任务、14D norm 与 manifest：接受为 CPU 输入准入

独立重跑 `scripts/visual_history_preflight.py` 的全部五行，输出保存在 `workspace/a98a1d8e-bf13-4316-9425-18389580fc6c/evidence/full_v_cpu_preflight_20260915.json`（SHA-256 `d6acfc5c…d0819e5`）。每行均为 50 episode、raw state/action `[32]` 的前 14D robot prefix、三路 `[3,480,640]`、K=30、batch 32、模型 padding 后 state `[32,32]` / actions `[32,50,32]`、恰好 18 个 image/image-mask keys。

| task | query rows | N robot norm SHA-256 |
| --- | ---: | --- |
| rearrange_blocks | 700 | `5d84df27e9fce3c6ec28585319ed293fa59fc1822063ecfa0e95c5bf4478606b` |
| put_back_block | 609 | `7a014e42dc9d51c8601b05dca5c876c58dda1308e61d1619e3d1c367baa7f261` |
| swap_blocks | 1,018 | `acb30919ff4be931da9c62173959971f9944bfc6d304ee80ab09448d79f6b336` |
| battery_try | 1,111 | `5ebaa98a5bf1151f9480811173cf5cd4de0a5e53ca6e123dea75a997bbb0be89` |
| cover_blocks | 1,718 | `ca4cf5ffdf648b61bcfa63e40532ab285b1368ceff728efa53fafa60bd27e551` |

还独立核对了各本地 dataset `info.json` 的 50 episode、32D state/action、三相机形状以及五份实际 `norm_stats.json` 的 hash。V config 会拒绝未知 repo 和 repo/asset 交叉绑定；`compute_norm_stats.py --config-name pi05_visual_history_aloha_v` 也按预期拒绝重算 V-specific norm。两份 manifest validator 均通过：smoke manifest 含且仅含一个真实 rearrange 两步候选，formal manifest 保持 `jobs: []`，没有被误认为已启动的 formal 作业。

formal 配方固定 `save_interval=20000`、`save_full_state=False`、`save_dtype=bfloat16`；两步 technical smoke 固定 save interval 2。这一 model-only 合同本身接受。

## B 集群实际容量 profile：拒绝

Manager 的 B 集群授权已执行，而不是仅保留候选。远端先导入精确 OpenPI/RMBench commits，使用 B 已有的 `rearrange_blocks_demo_clean_state_shared_memory`（4.4 GB）和 Pi0.5 base params；复制并校验 matching norm SHA-256。GPU 6 的两次 launch 前探测均为 A800 80GB、`81,149 MiB` free、0% utilization、无 compute process。

实际命令保持候选所有冻结输入，额外只有 `CUDA_VISIBLE_DEVICES=6` 的独占放置和外部 timing hook（它只使 update 同步以记录时间，不改变 TrainConfig、模型、数据、batch、图像、相机、分辨率或 H/K）。结果如下：

- GPU：A800 index 6，UUID `GPU-248ccab7-521f-d7ef-e7ee-c36b27bd03e8`。
- model-init：`228.194 s`。
- 0.25 s GPU sampler：747 个样本，峰值 `81,150 MiB` used，最低 `4 MiB` free，最大 GPU utilization 100%。
- 首个 optimizer update 未完成。XLA 在请求额外 `25,444,257,920` bytes（`23.697 GiB`）时抛出 `RESOURCE_EXHAUSTED`；整个 technical profile 在 `288.240 s` 后以 exit 1 结束。
- 没有 completed train-step timing、checkpoint-save timing 或 `.../2` checkpoint；因此 restore result 为 `not_run`，实际 18-slot policy inference mean/p95 与 `[50,14]` 输出均**不存在**，不能声称通过。

B 的 `visual_history_preflight.py` 曾在读取 N checkpoint provenance metadata 时因该 metadata 未镜像到 B 而停止；这不是 V data/norm mismatch：本地五行 preflight 已独立通过，B 上的 copied norm hash 已匹配，实际 profile 也已用 B 的真实 dataset 完成 loader 和 model initialization。它不改变上述 GPU OOM 结论。

MAM job `d420f9ce-6515-4f5c-bb21-87492f4b2dfe` 已按 stopped 结果归档。远端日志、GPU sampler、timing events、runner 和 checksums 已回传且逐项 SHA-256 一致；完整失败 receipt 在：

```text
/mnt/public/xcj/Projects/openpi/checkpoints/pi05_visual_history_v_capacity_profile/
  pi05_visual_history_aloha_v/v_rearrange_blocks_capacity_profile_seed0/
  a98_review_failure_20260915/profile_receipt.json
```

该目录没有模型 checkpoint，因此也不存在可删除的 B 模型副本。

## 后续准入条件

在不降低冻结输入合同的前提下，必须先由 Manager 批准并实现新的资源方案；当前单卡 FSDP=1 配置不能通过。方案在新的精确 profile 成功生成 step-2 checkpoint 后，仍须从该 checkpoint 创建 policy，在不访问训练 source dataset 的条件下执行六帧满 history（18 个有效 image slots）推理，记录 metadata/run kind、`[50,14]` 输出、mean/p95 和显存。完成这些证据前，formal V training 与 eval 保持不准入。

所有本地 review worktree、作者 worktree 和远端 profile worktree 均无源码改动；定向 `git diff --check` 通过。
