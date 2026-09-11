# SimFoundry × Table-1000 接入核查

核查日期：2026-09-11。只读核查；未安装 SimFoundry、未下载模型、未改动 Table-1000 或现有环境。

## 结论

**建议把 SimFoundry 作为可选的“真实桌面视频 → 候选物理资产/OmniGibson 场景”来源，开展一个受限的 2 周 4090 pilot；不要把它当作 Table-1000 的后端、训练数据管线，或多解整理语义/偏好标注的替代品。** 其当前输出天然服务 OmniGibson/Isaac 生态；Table-1000 的 reference backend 是 ManiSkill 3，因而需要独立的资产和场景编译适配层。

以下“事实”均来自官方材料；“建议/门槛”是本报告的工程建议。

## 官方开源边界（截至所见 `main`）

观察到的 `NVlabs/SimFoundry` `main` commit：[`9e34ebefcd020583fbb755a8b57268dce78eca26`](https://github.com/NVlabs/SimFoundry/commit/9e34ebefcd020583fbb755a8b57268dce78eca26)，提交时间 2026-08-27 UTC。源码许可证为 Apache-2.0，但该许可证**不覆盖**其安装时取得的第三方代码、模型、数据集和 SDK。

| 范围 | 当前事实 | 对 Table-1000 的含义 |
|---|---|---|
| 已发布的核心 | README 记录 2026-08-14 发布 rigid-body 与 articulation V0，2026-08-26 发布 example scenes/assets；A 为视频/ZED 到物理场景的重建，B 为 cousin/场景变体及 task proposal，C 为 OmniGibson 加载、smoke、eval、teleop、demo/replay 辅助阶段。见[发布状态](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/README.md#L23-L30)、[A/B/C](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/scripts/pipeline/README.md#L21-L101)和[C stages](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/scripts/pipeline/README.md#L240-L279)。 | 可验证地复现单场景重建与 OG native smoke；C 的存在不等于已获得通用训练数据生产线。 |
| 未发布的部分 | 官方 README 在 sim-to-real 章节明确写明：论文所用的 data generation 与 policy training code 不在仓库，未来 release 才会提供；新闻栏同样将 robotics data generation/training/evaluation 标为 Coming Soon。见[明确边界](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/README.md#L254-L260)。 | 不应以论文中的训练规模、policy transfer 结果或网页演示推断当前可获得训练/数据生成能力。 |
| A 的输入与产物 | A 的正式输入是视频或 ZED capture；采集约束为单平面、斜向平移、所有物体始终可见。A 生成 mesh、pose、metadata、sim-ready URDF/collision、USD dataset assets 和最终 `s14_og/reconstructed_og_scene.json`/`settled_poses.json`。见[采集约束](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/scripts/pipeline/README.md#L58-L101)、[最终输出](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/scripts/pipeline/README.md#L173-L184)。 | “图像输入”不应被表述为稳定公开主接口；首个 pilot 应用符合视频采集约束的刚体单桌面。最终 scene 是 OG JSON，不是 Table-1000 SceneSpec，也不是 ManiSkill scene。 |
| B 的 task generation | B stage 7 的官方定义是“propose **simple** task YAMLs”。其 VLM prompt 为每个 task 固定 `semantic_group_mapping` 和 `goal_predicates_all/any`；模板类型是 `PickPlaceTask`，允许多对象关系的合取，但每个 YAML 是显式、可判定的单一任务/成功谓词。见[阶段说明](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/scripts/pipeline/README.md#L207-L238)、[生成器 prompt](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/scripts/pipeline/B_augmentation/stages/7_propose_scene_tasks.py#L33-L90)。 | 它并非“每任务只能一个物体”，但也不是多个人类认可终态的生成器。可把结果当作候选 hard-constraint 或人工标注提示，不能当作 Table-1000 的 goal distribution、keep/discard 决策、persona 或 pairwise preference 真值。 |

论文是系统能力和实验主张的来源，但不能扩大当前开源边界；见[论文](https://arxiv.org/abs/2606.28276)。

## 产物与 ManiSkill 适配缺口

Table-1000 的 schema 刻意保持后端无关：SceneSpec 要有稳定 asset/object ID、asset provenance、类别、初始 pose、workspace/zones，并可表达 semantic role、affordance、状态和 goal graph；项目规划要求 ManiSkill 3 完整实现、其他后端经 contract conformance 接入。[本地 SceneSpec](/mnt/public/xcj/Projects/table-1000/table-1000/schemas/scene.v0.schema.json:7)；[后端边界](/mnt/public/xcj/Projects/table-1000/table-1000/docs/proposal/project-plan.md:46)。

| SimFoundry 产物 | 可复用价值 | 必做适配/QA |
|---|---|---|
| GLB visual mesh、估计 pose、`settled_poses.json` | 可作为初始 geometry/pose 候选。 | 定义 OG→Table→ManiSkill 的米制、轴向、四元数与 scale 约定；用已测物体核对尺度。不能把 OG 的 transform 原样写成 canonical state。 |
| sim-ready URDF/collision、physics settle | 省去从零制作碰撞资产的起点。 | 在 ManiSkill 重建 collision/material/mass/articulation，并做 reset、稳定性、可达性和 primitive skill QA。官方自身也建议 custom/reconstructed mesh 使用 AABB predicates，因为 collision mesh 可能破坏 OmniGibson 的 sampling predicates，[见此处](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/scripts/pipeline/README.md#L281-L309)。 |
| USD dataset assets + OG scene JSON | 保留资产和 OG native validation 的可追溯来源。 | 不是 ManiSkill exporter。对该 pinned tree 的路径检索未发现 `maniskill` 或 `sapien` 实现，官方文档也只承诺 USD/OmniGibson；需新建独立 importer/compiler，不能假设 USD/URDF 一键可运行。 |
| object name/category 与 B task YAML | 可辅助建立对象 catalog 和候选关系。 | 人工补充 stable IDs、来源/许可/哈希、semantic role、affordance、discardable/current-use 等字段。Table-1000 的 release QA 明确包括 license、scale、collision、stability、reachability 和 reset determinism。[本地 QA 要求](/mnt/public/xcj/Projects/table-1000/table-1000/docs/proposal/project-plan.md:143)。 |
| VLM task predicate | 可提出可验证的低层关系候选。 | 不能补足 human layout 的 object-level move/keep/discard/align/leave-accessible、rationale，也不能补足 pairwise human preference。前者见[layout schema](/mnt/public/xcj/Projects/table-1000/table-1000/schemas/human-layout.v1.schema.json:7)，后者仍须独立标注/评测。 |

**推荐边界：** canonical `SceneSpec` 与 Table-1000 evaluator 中不保存 OG/Isaac 原生句柄；OG JSON、USD、URDF、SimFoundry commit、模型/配置和原始视频许可作为 adapter artifact/provenance 保存。Table-1000 的工程规划本来也把“资产导入、碰撞体、scene/state codec、控制器”列为可替换的 backend 层，而非稳定 benchmark 语义层。[本地规划](/mnt/public/xcj/Projects/table-1000/table-1000/docs/proposal/project-plan.md:48)

## 实际环境与许可成本（官方数字）

- 完整安装约 **250 GB**：conda env 约 100 GB、`deps/` 约 82 GB（其中 VOID 41 GB）、HF cache 约 12 GB，外加 checkpoints；标准安装建立多个 conda env（`simfoundry`、`hunyuan`、`any6d`、`da3`、`void`、`nerfstudio_simfoundry`、`3dgrut`）。见[INSTALL](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/docs/INSTALL.md#L5-L75)。
- 24 GiB RTX 4090 可跑标准视频 pipeline，但 stage 7 默认约需 29 GiB，必须设置 `s7_mesh.low_vram=true`（约 6 GiB、CPU offload）；16 GiB 是总的最低下限，articulation 至少 18 GiB。见[VRAM 说明](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/docs/INSTALL.md#L17-L28)。首 pilot 不选 `pixal3d`：官方把它的 24 GiB profile 限为 low-vram，且多物体/cousin 仍标为未覆盖实验。[该 caveat](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/docs/INSTALL.md#L151-L171)。
- reconstruction、articulation 和 B 都调用 Vertex AI/Gemini，要求启用 billing 的 GCP project/认证；HF gated models 也需账号/接受条款，checkpoint 下载并非小依赖。见[服务与 checkpoint](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/docs/INSTALL.md#L180-L226)。
- Apache-2.0 只覆盖 NVIDIA 代码。官方列出了 required/optional 的非 OSS、non-commercial、地域限制和无许可组件；尤其 Any6D、FoundationPose/Stereo、Hunyuan 等必须逐项审查。见[安装边界](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/docs/INSTALL.md#L418-L436)。

**建议：** 若获准安装，使用专用的 SimFoundry conda 根和独立 data/cache，绝不混入 Table-1000 的 ManiSkill `.venv`。这是根据其多 conda env、editable installs 和外部 assets 的隔离建议，不是官方承诺的兼容性结论。

## 最小接入路径与两周 4090 pilot（建议）

先不做：批量 1,000 场景、auto-background、articulation、Pixal3D、B cousin 扩增、训练/teleop data generation，或把 B 的 YAML 当 benchmark 标签。

先做的可复现第一里程碑：在专用环境以 pinned commit 重跑一个官方示例视频的 A 完整重建，保存 `s14_og/reconstructed_og_scene.json`、preview、`settled_poses.json`，再运行官方 C `smoke-random`。这是官方 documented smoke 路径；先证明 native OG 加载，再谈移植。[官方 smoke](https://github.com/NVlabs/SimFoundry/blob/9e34ebefcd020583fbb755a8b57268dce78eca26/docs/INSTALL.md#L274-L291)。

建议 pilot 范围为 3 个单平面刚体桌面场景、每个 6–10 个物体、无 articulation；同时保留原视频的取得许可与三件已知尺寸物体作尺度核验。量化 go/no-go：

1. 3/3 完成 A 并通过 OG native smoke；每个场景有固定 commit、配置、模型调用/缓存状态和输出 hash。
2. ≥90% 目标物体能一对一映射为 Table-1000 object ID；100% 进入候选库的资产有 source/capture 权利、hash、SimFoundry commit、模型/配置和许可审查记录。
3. 三个已知尺寸物体的 median bbox 相对误差 ≤15%，且无一件 >25%；超过此值说明需要人工重建/尺度校正，自动导入无成本优势。
4. ManiSkill adapter 导入后，每场景 10 次 reset/settle 中 ≥9 次无穿透、飞散或掉出 workspace；每场景至少一个 pick→place primitive ≥8/10 成功。未达到时先修资产/碰撞，不进入语义扩容。
5. 每场景收集 ≥3 个独立 human layout；至少保留两种可接受但结构不同的终态，且 B task YAML 不作为标签或主榜 evaluator。否则它只证明可生成显式 task，不证明 SOP-open 场景价值。

任一许可/provenance 缺口、无法确定性转入 ManiSkill、或第 4 项失败，即为 **no-go（暂停扩容，保留为 OG-only 原型）**；通过后才值得比较“人工资产制作时间 vs. SimFoundry+adapter+QA 总时间”。

## 可并行工作包（不分配具体人员）

| 工作包 | 可立即开始的产物 | 依赖 / 完成条件 |
|---|---|---|
| P0 环境与复现 preflight | 250 GB/24 GiB/credential/license checklist，pinned manifest，官方 example native smoke 记录。 | 是唯一的启动 gate；完成后允许 P1 的真实运行。 |
| P1 捕获与 A 重建 | 三段符合官方采集约束的视频、A output manifest、OG smoke video。 | 依赖 P0；不跑 B/cousin。 |
| P2 adapter contract | OG/URDF/USD → asset catalog + SceneSpec 的字段映射、坐标/scale 约定、artifact layout；可先用 schema mock 编写设计。 | 可与 P1 并行；用 P1 产物做实现验收。 |
| P3 资产 provenance/physics QA | source-rights、许可证、hash、visual/collision/scale/reachability checklist。 | 可与 P1/P2 并行；是任何场景入库的硬 gate。 |
| P4 ManiSkill compiler 与 reset/skill QA | 仅导入 P2 合格资产的 minimal scene compiler，10-reset 与 primitive 报告。 | 依赖 P2/P3；不把 OG native pass 误认为 ManiSkill pass。 |
| P5 多解语义与人类标注 | 人类 layout/pairwise protocol、goal-graph 映射、B YAML 的“候选而非真值”审计规则。 | 与 P0–P3 并行；独立于 SimFoundry 是否通过，避免生成管线定义评价语义。 |

## 交付说明

- MAM task: `d05ee593-fc5f-4beb-bf76-b7dca11502ac`
- Agent thread: `01a08dfd-2621-71a0-9376-6522b9a091d8`
- Workspace/worktree: 未创建。任务明确允许仅只读 canonical proposal/schema，且本任务没有修改或独立 review Table-1000 仓库的需要。
- 验证：读取并交叉核对 NVIDIA 官方 GitHub README、pipeline reference、INSTALL、第三方许可边界、官方项目页/论文与 Table-1000 proposal/schema；未执行安装、模型下载、GPU 程序或测试。
