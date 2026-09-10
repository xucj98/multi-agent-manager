# 审查结论：通过

审查对象为 Table-1000 环境链的 `2af4b12`、`d30dca0`、
`b049801`、`9fe95e0` 与最终
`b56e55ef6c799c800c12573bde1b0a7a3c25556c`。
对最终提交未发现未解决的 P0/P1/P2 问题；review 未修改实施代码。

## 交付与布局

- review worktree：`/mnt/public/xcj/Projects/table-1000/workspace/c4a71639-62bd-478d-b654-928a8183ab0e/table-1000`
- 分支：`task/c4a71639-62bd-478d-b654-928a8183ab0e`
- MAM creation base：`9fe95e0a088a48cfa6ee7bd5b0edcfa1113702c7`；最终 review HEAD：`b56e55ef6c799c800c12573bde1b0a7a3c25556c`
- canonical `.cache`、`outputs` 和 `.local` 均为实体目录，顶层没有业务软链接；PROJECT_ROOT 顶层只保留 `.mam`、MAM repo、canonical repo 与 `workspace`。
- `/root/.cache -> /mnt/public/xcj/cache`，`/mnt/public/xcj/cache/uv` 为实体持久 store；canonical `.local/worktree-env.conf` 的唯一设置为 `TABLE1000_UV_CACHE_DIR=/mnt/public/xcj/cache/uv`，旧 canonical `.local/uv-cache` 不存在。
- review worktree 顶层业务链接恰为 `.cache -> canonical/.cache`、`outputs -> canonical/outputs/c4a71639-62bd-478d-b654-928a8183ab0e`；`.venv` 是实体目录。canonical 与 review 的 `pyproject.toml`、两个 `.venv` inode 均不同。

## 热创建与隔离证据

`mam workspace add c4a71639-62bd-478d-b654-928a8183ab0e --repo table-1000 --base 9fe95e0` 成功，耗时 28.062 s。

- 创建前 uv store：6,246,853,120 B；创建后：6,246,896,640 B，增量 43,520 B。
- review `.venv` 物理占用 21,485,568 B（apparent 8,022,125 B）；site-packages 内有 28,748 个 symlink。抽样 `traitlets` 的 `METADATA` 直接解析到 `/mnt/public/xcj/cache/uv/archive-v0/...`。
- `table1000-0.1.0.dev0.dist-info/direct_url.json` 为 `editable: true` 且指向 review worktree 自身；`import table1000` 也解析到该 worktree 的 `src/table1000`。因此第三方包复用没有共享 editable 源码或元数据。
- symlink store marker 是实体文件，明确禁止 `uv cache clean`、任意 `uv cache prune` 与手工改删 store。`b049801` 已将该 marker 写入移动到首次 symlink 安装之前，覆盖后续 editable/验证失败时仍可能留下 venv symlink 的恢复路径。

## 重试、恢复与归档保护

MAM 的 `workspace add` 对已 `ready` 的登记按既定协议只验证 git worktree/branch 后返回，不会重跑环境入口。我在 review worktree 中可逆地移走 `outputs` 链接后确认该 raw MAM 调用仍返回 ready 且不修复链接。

这不是最终 repo 一键入口的遗漏：`b049801` 的 `mam_workspace_add.sh` 检测既有 worktree 后会重入同一版本化 `.local/create_worktree.sh`。由于当前 canonical `main` 尚未合入该 tracked helper，不能从 primary 路径直接执行它；已直接运行其完全相同的 local repair 端点，4.645 s 内恢复正确 `outputs` 链接，原有 `outputs/smoke/preflight.json`、GSO probe 与 reference replay 结果均保留。后续 blank-agent 会在 helper 合入 primary 后做该端到端验收。

`b56e55e` 修复了无残留时 `cleanup.sh` 在 `set -e` 下错误返回非零的问题。我在最终 review HEAD 连续运行两次 cleanup，二者均以 0 退出；git ignored 状态仍仅为 `.cache`、`.venv/`、`outputs`。直接调用 MAM 的只读 `dirty()` 归档预检返回恰这三项，均属于 MAM 允许移除/保留的类别；canonical `outputs/TASK-ID` 的 smoke 成果仍存在。未执行实际 archive，以保留 review worktree 供 Manager 验收。repair 后 uv store 仅再增 19,968 B。

## 运行验证

- `git diff --check`、所有 worktree environment shell 脚本 `bash -n`：PASS；最终 `b56e55e` 的 cleanup 双次幂等性：PASS。
- GPU 1 完整 `bash scripts/worktree_env/smoke.sh`：PASS，99.969 s。
  - 真 GSO `Markings_Letter_Holder` 资产 probe：PASS；
  - ManiSkill CPU、Table-10 0002 `red-then-blue` reference replay：PASS，`valid=true`；
  - ManiSkill render 与 GPU physics：PASS；
  - `tests/unit/test_data_validation.py tests/unit/test_cli.py`：40 passed。

同集群 peer 的实际运行验证由 environment task 按最新 `9fe95e0` 文档单独执行；本 review 未重复该矩阵，符合 Manager 指示。
