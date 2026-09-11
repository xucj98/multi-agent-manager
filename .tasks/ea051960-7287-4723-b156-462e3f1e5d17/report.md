# Table-1000 proposal 对照现状：只读审计

## 范围与证据口径

- 审计基线：`table-1000` 的 `f8340d5de7ac5452a6a8d726c1fc11047c0ae6b1`，worktree 为
  `/mnt/public/xcj/Projects/table-1000/workspace/ea051960-7287-4723-b156-462e3f1e5d17/table-1000`，分支
  `task/ea051960-7287-4723-b156-462e3f1e5d17`。未改源码，未重跑 GPU suite、正式生成或训练。
- 计数由提交的 YAML/JSONL 实际解析而来；`outputs/` 里的历史大产物不作为已复验数据。
- 本报告严格分开：接口/测试、指定 oracle 的物理回放、人类标注、真实模型实验和可供学习的轨迹。
  前三者不能互相替代。

## 结论

仓库已经有很扎实的工程地基：ManiSkill reference backend、schema/validator、Open/Explicit 视图隔离、
集合值 outcome evaluator、标注 server、reference/native replay，以及小型物理 oracle。它还没有达到
proposal 的 Phase 0 科学结论，更没有达到 MVP-200：目前没有真实人类标注、没有 human-calibrated
evaluator、没有真实 VLM/VLA 结果，也没有可声明为 SOP-open 的 release。最合适的近期路线是先把
“场景是否真有多解、是否可物理落地、人与 evaluator 是否同意”三个问题做成可审计证据，再做
Open–Explicit 模型诊断。

## 实际数据、实现和实验的边界

| 项目 | 实际完成的内容 | 不能据此声明的内容与证据 |
|---|---|---|
| 协议与 evaluator 接口 | Open/Explicit `AgentView` 会将 stable IDs alias 化，Open 模式剥离 goal/zone/semantic-role 等私有字段并 fail-closed（`src/table1000/benchmark/views.py:104-223,244-261`）；集合值 evaluator 已可匹配任一 cluster，但结果硬编码为 `diagnostic_only=true`、`eligible_for_leaderboard=false`（`src/table1000/evaluation/outcome_set.py:1-8,126-182`）。对应 unit tests 已在仓库中（`tests/unit/test_benchmark_views.py`、`test_open_validation.py`）。 | 这是接口与测试覆盖，不是公开 release 的泄漏审计，也不是人类校准。ADR-004 的 release 边界仍要求 evaluator 在 agent 进程外运行（`docs/adr/004-open-explicit-firewall.md:7-23`）。 |
| `data/table10` 工程切片 | 10 个 manifest scene，合计 32 个对象（每 scene 1–4 个）和各 1 个显式 GoalGraph；20 条 reference-plan YAML；30 个 accepted layout、20 个 near-miss、20 个 pairwise record。每个 preference 都是同一 `annotator_id: fixture-v0` 和 `label_source: fixture_derived`，不是人类数据。见 `data/table10/manifest.yaml:1-77`、`data/table10/README.md:5-15`、各 package 的 `annotations/*.jsonl`。 | 它只支持工程回归。30 个 accepted layout 是同一显式图内的位置扰动；20 条 plan 主要是顺序/抓取变体，文档明确否认它们能证明多语义终态（`data/table10/README.md:38-40`；`docs/spec/table10-open-v1.md:7-20`）。数据包中也没有已提交的 trajectory/physical-validation artifact；reference-plan 不是学习 demonstration。 |
| Table-10 指定计划物理闭环 | `run_reference_plan_replay` 确实 build/reset ManiSkill、逐 skill 执行、再重算 GoalGraph 与 hard constraints（`src/table1000/benchmark/reference_replay.py:269-334`）。README/工程记录报告 CPU seed-0 的 20/20 completed、0 failed、0 skipped；包括 stack/discard/insert/drawer（`README.md:69-84`、`data/table10/README.md:31-36`；历史证据 commit `f3ab864`）。 | 这是已指定 oracle plan 的单栈工程 QA，不是多样轨迹数据、不同语义终态、三 seed Open 可行性或人类认可。该审计未重跑该矩阵。 |
| `data/table10-open` | 实际为 10 个、每个 10-object 的 draft package：共 30 个语义 outcome cluster、30 个 strategy family、60 条 plan；一例可见 cluster 的 disposition/assignment 差异在 `data/table10-open/scenes/t1k-open-0001-v2/annotations/outcome-set.yaml:20-170`。统一参与者提示为“请把桌面整理好”（`data/table10-open/manifest.yaml:1-18`）。 | 10 个 `layouts.jsonl`、`near_misses.jsonl`、`preferences.jsonl` 都是 0 bytes；全部 60 plan 的 `execution_status: provisional_fixture`，所有 package 的 `physical_validation_status: not_started`。manifest 也明确为 `open_eligible:false`、`human_support:none`、`physical_seed_evidence:none`（`data/table10-open/manifest.yaml:1-18,25-135`）。因此它是结构化假设，不能算人类多解、物理多解或 Open benchmark。 |
| R2 dense probe 场景 | `data/probe/scenes` 有 10 个目录；0002–0010 的 outcome-set 都是 `draft`，并带 author fixture、初态/终态稳定性及 view-set 资产。该方向可复用作场景生成与人评准备，而不是已经合格的数据集。 | 9 个 outcome-set 的 `human_support_status` 与 `physical_validation_status` 均为 `not_started`；5 条 preference 也都是 `author-v0`/`author-fixture-v1` 的 `fixture_derived`。0006 的两个 accepted layouts 逐物体 position/orientation 最大差均为 0，只有 ID/rationale 不同；其 outcome-set 也写明 `fixture_source: author_config`、`human_support:false`、无 trajectory evidence（`docs/roadmap.md:77-85`；`data/probe/scenes/t1k-probe-office-stationery-0006-v1/annotations/terminal-set.yaml:1-17`、`outcome-set.yaml:140-142,249-279`）。故 0006 不计为多解或可人评场景；10 个 probe 不可整体计入“合格人评场景”。 |
| 人类标注与偏好模型 | 两阶段 annotation server、freeze、coverage audit 和去标识导出已实现；协议明确 10 人独立布局、冻结后 pairwise 的目标和 coverage 门（`docs/spec/human-pilot.md:16-109`；`src/table1000/annotation/study.py:81-184`）。 | 当前未发现 annotation SQLite、export、coverage 或任何真实参与者记录。proposal 要求的每场景多位独立人类终态、anchor 密集 pairwise、human ceiling 尚为零（proposal `docs/proposal/research-proposal.md:324-370,402-430`）。 |
| Baseline/模型实验 | 三个规则 baseline 有一次真实 `physx_cpu` 运行：5 个 probe × 3=15 episodes；DoNothing/Random/Category 的 required relation 都为 0/42，后两者均首个技能失败（`docs/worklog/baseline-first-run-2026-08-15.md:3-19,63-88`；commit `7eed18e`）。VLM runner 可接 stub/replay/configured live provider（`src/table1000/baselines/vlm.py:119-162,256-358`）。 | VLM 首轮是 offline deterministic stub，记录明确说明不是任何真实模型能力分数；5/5 skill failure、0/42（`docs/worklog/baseline-vlm-first-run-2026-08-15.md:5-20`；commit `489750e`）。没有 live VLM/VLA checkpoint、模型版本、真实 provider response 或 Open track 主结果。 |
| 长程执行/轨迹 | Probe-0001 有真实 fresh-build 物理搜索与部分闭环证据：严格可复现 ceiling 为 5/14 目标对象、13/13 已发技能通过（`docs/worklog/probe-0001-physical-tidy-2026-08-20.md:14-36,89-129`；commit `ea73166`）。 | 这不是完整 tidy trajectory，也不能作为 IL demonstration；同文档明确禁止把 partial trajectory 作为训练数据。它反而表明当前低层 grasp/placement/packing 仍会混淆 Track-1 的高层规划归因。 |

## Proposal 对照的 7 项状态

1. **已完成：工程协议 MVP。** schema、backend registry、scene compiler、Open/Explicit firewall、result/replay contracts 和 fixture evaluator 都可供开发使用。
2. **已完成但只限工程：Table-10 指定计划物理 QA。** 可作为 CI、oracle 回归和 executor 改动的保护网，不能作为 SOP-open 证据。
3. **已完成但只限结构：集合值目标与 Open-v1 数据契约。** 30 个 draft cluster/strategy 的编码说明了目标表示，但没有验证“人类认可且可执行”。
4. **未完成：Phase-0 的多解性与可判定性。** proposal 的 go/no-go 需要独立人类终态与高于随机的一致性（`docs/proposal/research-proposal.md:669-677`）；现有数据没有满足它。
5. **未完成：真实人类 preference model / calibrated evaluator。** 现有 fixture evaluator 和 author priors 不能替代 pairwise、human ceiling、校准或 population/persona 结论。
6. **未完成：可发布的 Open 物理闭环与多样轨迹。** Open-v1 规定每 strategy family 在 seeds 0/13/37 物理通过（`docs/spec/table10-open-v1.md:70-92`），实际均为 not_started；Table-10 的 20 条指定 reference plan 也不是 dataset trajectory。
7. **未完成：论文级模型比较。** 当前只有失败诊断的规则 baseline 和 VLM stub；缺 Open–Explicit 成对、真实模型、执行归因、置信区间及 leakage/generalization split 审计。

## 最重要的三个研究瓶颈

1. **科学有效性瓶颈：没有真实人类证据来证明“多解但非任意解”。** 这同时阻断 G0、preference evaluator、H4/H5 和 Open 主榜。0006 的复制终态说明 scene QA 必须在招募前阻断“语义名不同、物理状态相同”的伪多解。
2. **执行归因瓶颈：semantic outcome、可放置终态与可执行长程轨迹尚未连接。** Table-10 的 oracle QA 是积极信号，但 dense probe 的 5/14 ceiling 和 Open 的三-seed 物理验证记录为零表明，现阶段不能把模型失败归因给 goal induction/规划。
3. **可比较性瓶颈：Open–Explicit 还没有冻结的真实模型矩阵。** firewall 的代码/测试存在，但 Open 数据仍是 draft；没有真实 provider/VLA、版本化 result bundle、group-aware split 或对 human hidden labels 的评价。因此不能验证 proposal 的 H1–H3 或声称 Open gap。

## 建议的可并行工作包（不按学生背景指派）

| 工作包 | 交付物 | 验收标准 | 依赖与边界 |
|---|---|---|---|
| A. 场景多解与物理 QA | 一套可冻结的 pilot scene manifest；每 scene 的资产/provenance、初态、≥3 语义不同 outcome、负样本、outcome signatures、render review、0/13/37 physical-validation report。先替换或退役 0006，并新增“逐对象终态差异/容器视觉语义”硬门。 | 自动检查拒绝零状态差的不同 cluster；每 accepted outcome 在 disposition/assignment/关键关系之一不同；资产容器的 visual/collision/provenance 审计通过；所有报告可从 manifest 重算。 | 可立即并行于 B/C 的工具工作；完整三-seed execution 依赖公共 solver/oracle。不要把 author fixture 计作 human support。 |
| B. 独立人类多解与 evaluator 校准 | 小规模、版本化两阶段 pilot：同意/招募记录留在私有区，匿名 layout export、冻结 pairwise 图、coverage/human-ceiling/一致性/顺序偏差报告，以及冻结的 evaluator calibration split。 | 每场景独立布局和 pairwise coverage 达到 `docs/spec/table10-open-v1.md:94-111` 的门；原始 human、author fixture、near-miss 分层保存；报告明确样本量和不确定性。 | 实质采集依赖 A 选出无伪多解且可审阅的 scene；需项目负责人解决招募/伦理/数据管理。可先并行完成 dry-run、界面可用性和导出审计。 |
| C. Open–Explicit 模型诊断与结果基础设施 | 冻结 prompt/view/scene/evaluator hash 的 paired runner；真实 provider/VLM 的可重放 response/result bundle；按 goal induction、planning、skill/execution、hard gate 分类的逐 episode 与聚合分析。先用 Table-10 explicit 做 executor regression，Open 仅作为 draft diagnostic。 | 每个结果包含 model/version/config/prompt hash/seed/backend/scene/evaluator version；明确标记 fixture/stub；同一 agent 在 paired Open/Explicit scene 的比较不读取私有字段；发布前有 group-aware split 和失败归因。 | runner/logging 可与 A/B 并行，科学主结论依赖 A 的冻结 package、B 的 human-calibrated evaluator；不能用当前 stub 或 reference plan 冒充真实模型比较。 |

Dense solver、grasp/placement 与完整 trajectory recovery 应继续作为资深维护的公共 P 线：它是 A/C 的共享依赖，且目前的 5/14 结果需要系统性解决，不宜承诺为上述三个工作包中的“已解决低层执行”。

## 交付

- 代码改动：无。
- 验证：仅只读解析、文件/提交历史核验；未运行测试或 GPU 任务。
- 可供验收的 workspace：`/mnt/public/xcj/Projects/table-1000/workspace/ea051960-7287-4723-b156-462e3f1e5d17/table-1000`（base `f8340d5`）。
