# 集群 B 只读审计报告

审计时间：2026-09-22（Asia/Shanghai）。范围为 `wuwen-11`、`wuwen-12`、B 侧 `/mnt/public3/xcj/Projects/state-vla`，以及 A 侧对应 `/mnt/public/xcj/Projects/openpi/checkpoints`。全程只读；未创建 worktree、未启动/停止进程、未改动或删除实验资产，也未做多 GB 全量 hash。

## 主机与进程

| 主机 | 结果 |
| --- | --- |
| `wuwen-11` | SSH 可达（A800-SXM4-80GB ×8）。审计时 `nvidia-smi --query-compute-apps` 和 `nvidia-smi pmon` 均无计算进程；GPU 利用率均为 0%，GPU5 仅有约 1288 MiB 持久上下文。进程只有旧 tmux/nvitop/bash，会话 cwd 不在实验 workspace；workspace 内 PID 文件指向的 9 个 PID 均不存在。 |
| `wuwen-12` | TCP `183.233.148.6:43447` 可连接，但 root 公钥认证失败（`Permission denied (publickey)`），因此无法核查该主机的 GPU、进程和 workspace。 |

`wuwen-11` 稳定仓库均 clean：openpi `frozen-34002dce`/`34002dc`、RMBench `frozen-f401f527`/`f401f52`、robot-bridge `frozen-f9626636`/`f962663`。项目根没有 `AGENTS.md`；已读取 `openpi/AGENTS.md` 和 `RMBench/AGENTS.md`，没有进入修改流程。

## B checkpoint 与 A 回传

B 侧 `openpi/checkpoints` 顶层只有 7 个目录：battery S formal/smoke、observe-and-pickup N formal/两份 smoke、两个 V profile 空目录。没有发现 `rearrange_blocks`、`put_back_block`、`swap_blocks`、`cover_blocks`、`swap_T`、`blocks_ranking_try`、`press_button` 的其它 B checkpoint，也没有九任务新增 S/J checkpoint。

| setting | B 侧状态（相对路径） | A 侧核对 | 结论 |
| --- | --- | --- | --- |
| `battery_try.S.t0` | `battery_s_formal20k_34002dce_nocmdbuf_20260914T120610Z`；step 20,000。模型删除后保留约 922K 的 log/validation；删除收据 `validation/model_deletion_receipt_20260920.json`：`deleted_verified`，删除前 43 文件/5,258,067,697 bytes。 | A 有同名正式 checkpoint；`_CHECKPOINT_METADATA` 386 bytes，SHA-256 `6a5beb...e318`，与 B 收据一致。A CPU restore PASS：56 leaves、6,706,900,520 BF16 bytes、finite/shape complete。 | **已回传、已验证、B 模型已删除**；B 只保留审计记录。 |
| `observe_and_pickup.N.t0` | `observe_and_pickup_n_b_formal20k_ec86d857_20260914T162824Z`；step 20,000。模型删除后保留约 920K 的 log/validation；收据 `deleted_verified`，删除前 258 文件/5,261,987,027 bytes。 | A 有同名正式 checkpoint；`_CHECKPOINT_METADATA` 386 bytes，SHA-256 `2e7e3b...e9e8`，与 B 收据一致。A CPU restore PASS：51 leaves、6,706,867,744 BF16 bytes、finite/shape complete。A 侧 `checkpoint-transfer-20260920/observe-command.txt` 记录 source `zx-data`（B via `wuwen-nx-aic`）到 A。 | **已回传、已验证、B 模型已删除**；B 只保留审计记录。 |
| 其它九任务 N/S/J | B 正式 checkpoint 根未发现对应目录。 | A 侧有既有 wave1/legacy N/S/J；`swap_T.N`、`blocks_ranking_try.N`、`press_button.N` 也有 A 侧目录。 | 这些是 A 侧资产或尚未在 B 训练；不能把它们记为 B 回传。 |

关键文件大小核对仅针对 metadata、日志和收据；未对参数树做全量 hash。A 侧正式目录仍完整存在，B 侧两份正式模型不存在是有收据的验证删除，不是传输失败。

## B workspace

所有列出的 git 仓库用 `git status --porcelain --untracked-files=all` 核对为 0 dirty；部署目录中的日志、PID 文件和环境目录不属于 git tracked 状态。`du -sh --apparent-size` 为近似值。

| TASK/workspace | 大小 | B 侧内容与 git | MAM 状态 / 依赖 |
| --- | ---: | --- | --- |
| `2b8c1566-f2ca-4591-bb69-a28ad52e29f9` | 8.4G | CPU RMBench `f401f52`、robot-bridge `f962663` clean；bootstrap-staging 和 CPU 环境日志。 | MAM archived，A 侧 workspace/repo 已 removed；无运行依赖，可在 retained evidence 核对后清理远端环境副本。 |
| `a98a1d8e-bf13-4316-9425-18389580fc6c` | 7.7G | openpi `review/a98a1d8e-vfix-bprofile`、`66d9253` clean；V profile deployment。 | MAM pending（V review）；PID 文件均为 stale、对应进程不存在。pending 前保留。 |
| `bed9952b-c1a2-40ec-9f6d-34feeba91aa5` | 16G | RMBench/openpi/robot-bridge 分别 `f401f52`/`34002dc`/`f962663`，均 clean；共享结果和 `.venv` symlink。 | MAM archived；CPU 验收证据已发布，清理需先确认 retained archive 与无依赖。 |
| `e34ba9b3-34e2-4df4-92d8-4cea983b7303` | 7.7G | openpi `task/e34...`、`66d9253` clean；V profile deployment。 | MAM pending（V source task）；保留。 |
| `f0011538-fbad-49f6-b117-4d628f2bf30c` | 7.7G | openpi `task/f001...-b-observe-n`、`ec86d85` clean；observe N deployment/logs。 | MAM pending，7 个 job 已 archived；formal 模型已回传并删除，保留日志/收据直到 Manager 归档。 |
| `fa928e8d-a486-426b-8381-16c207d37262` | 7.7G | `battery-s/openpi` `task/fa928...-battery-s-openpi`、`34002dc` clean；B controls v3-v7、失败 probe 和收据。 | MAM archived，A 侧 workspace removed，2 个 job archived；v7/收据已形成证据链，旧控制包可候选清理但目前仍是 B 侧独有记录。 |

## B 独有资产、失败/缓存与清理候选

- `battery_s_smoke_34002dce_nocmdbuf_20260914T120610Z`：约 4.9G，step 50；CPU full restore 和 GPU policy restore 均 PASS。A 侧没有同名完整 smoke 模型（仅有另一时间戳的精简记录），因此当前视为 B-only；没有已证明的 A 接收位置，按规则当前保留。只有建立 A 侧归档/证据位置并确认无 eval 依赖后，才可列候选。
- `observe_and_pickup_n_b_smoke_ec86d857_20260914T162824Z`：约 27K，首因是 multiprocessing spawn 导致 CUDA OOM，`checkpoint_step=none`；这是 B-only 失败记录，当前保留，需先把精简 receipt 放入 A/MAM retained evidence 后再评估清理。
- `observe_and_pickup_n_b_smoke_ec86d857_retry1_20260914T165414Z`：约 5.0G，step 50，CPU restore PASS；A 侧无同名完整 smoke 模型，当前保留。只有建立 A 侧归档位置、保留 receipt 并确认 formal 不再引用后，才可列候选。
- `fa928.../deployment` 约 5.6M：v3-v7 控制包、v5/v6 失败 probe、v7 最终 launcher/receipt 和多个 tar.gz。MAM retained evidence 位置为 `/mnt/public/xcj/Projects/multi-agent-manager/.local/retained-workspaces/fa928e8d-a486-426b-8381-16c207d37262`；仅在该证据完整、确认无 active dependency 后才可清理旧版本，本审计未删除。
- 两个 V profile 目录为空（0 bytes），但 `a98...`/`e34...` 仍 pending；在 review/archive 前不清理。
- 共享 `/mnt/public3/xcj/cache`（battery 数据约 7.4G、observe 数据约 1.9G、pi05_base 约 12G）是预训练/数据缓存，按任务约束不列为清理候选。

形式上没有 B 侧唯一的已完成 formal checkpoint：battery S 和 observe N 的参数树均已在 A 验证后删除。B-only 的 smoke/控制包/失败记录仍需按上面的前置条件处理。

## 与当前进度及 MAM 的差异

- `PROJECT_PROGRESS.zh-CN.md` 与 `experiment_matrix.csv` 仍把 `swap_T.N.t0`、`blocks_ranking_try.N.t0` 标为 `artifact_pending_restore_acceptance`（两者 0/3 eval）；A 侧目录已存在，MAM task `2a792e9a-9fbe-4334-bf8e-b7e293bdd64a` 的报告称两者 CPU gate PASS。该状态需要 Manager 独立验收后再更新，不能由本次 B 审计直接改写。
- 上述 task 仍有两个 stopped、未归档 job：`8a828bdf-4711-400e-89c3-1526b1694f22`（blocks ranking N）和 `f39ba4a8-a6ca-4b6c-9cd2-b6a9f5330a57`（swap_T N）。这是当前 MAM 收尾阻塞。
- 进度文档的总数（23 个 20k 产物、21 accepted/2 pending；46 个完整终态批次）与 CSV 算术一致：experiment matrix 完成 28 批，deployment matrix 完成 18 批，共 46；HF 18 批的 `first_action_protocol_gate_pending` 也仍未闭合。B 审计未发现新的正式 eval 批次。
- B 侧 battery S、observe N 的回传/删除证据与进度入口一致；未发现 S/J 新增任务在 B 启动的证据。

## 阻塞项

1. `wuwen-12` 公钥认证失败，无法证明该主机无遗留进程或独有资产；需恢复只读 SSH 凭据后复核。
2. `2a792e9a...` 的两个 stopped job 尚未归档，且 CSV/PROJECT_PROGRESS 的 pending 标签尚未根据 CPU gate 收据更新。
3. V 任务 `a98...`、`e34...` 仍 pending，相关 workspace、空 profile 和环境副本不能清理。
4. B-only smoke 和旧控制包虽无活跃 PID，但清理前仍需保留精简失败/恢复收据并确认 A 侧接收位置；本报告不执行删除。
