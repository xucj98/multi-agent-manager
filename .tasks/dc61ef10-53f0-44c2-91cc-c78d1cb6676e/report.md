task_revision: b8d0439bbe4fac57f10f8e6db09bd77698812ce6

完成与未完成：

- 本次修正 Manager 对 `3d4fe31` 的发现：`meta/metadata` 目录改用标准库 `copytree` 完整继承，保留目录布局和文件字节，不再按内部文件名过滤。源根仍只选现有 command/config/binding 等小文件，根目录 labels、Parquet、媒体、源码及 `data/videos` payload 目录不进入 checkpoint；未扩展文件名白名单。
- checkpoint 留痕继续复用 `checkpoint_metadata.save`：在 `metadata/command.txt` 的注释头记录保存时 OpenPI HEAD、git status、实际 cwd，正文记录本进程 `sys.orig_argv` 和已有 GPU/JAX 环境开关。本次补上进程已设置的 `HF_LEROBOT_HOME`、`HF_HOME`、`OPENPI_DATA_HOME`，用 shlex 引用含空格路径，不 dump 环境或记录 token。不读取或冒用旧试跑命令，不新增 `git_commit.txt` 或 runtime 信息对象；正式训练仍需按库规范固定 commit。
- 上游继承继续复用现有 `LeRobotDatasetMetadata` 查询：复制到 `metadata/upstream/dataset_<index>`，用 `datasets.json.metadata_path` 关联。读取约定的 `TrainConfig.memory_bindings.sidecar_path`，从其父目录继承到 `metadata/upstream/memory_bindings`。相对源路径以 OpenPI 根解析；不构造训练 data loader。metadata 目录作为完整继承边界，其内部合法 JSON/JSONL 均保留。
- 候选 memory YAML 的生成规则及产物重生成由 data owner 负责。本任务不读取项目 memory YAML 目录，继承上游实际 metadata/config；训练最终 schema 仍只由原 `TrainConfig.memory_config` 字段负责，未编辑 config/train.py。
- 完成 BF16/FP32 推理参数导出：`save_state` 直接读取 `config.save_dtype`，仅转换拆出的浮点 params 副本，整数和布尔叶子不变，训练内 FP32 params/优化器不变。`save_full_state=False` 的真实 Orbax tiny checkpoint 只含 `params`、`assets`、`metadata`，没有 `train_state`。
- 已交付 checkpoint-only loader：先下载再读取 metadata；policy 直接调用训练侧约定的 `create_data_config(training=False)`，并将唯一 `TrainConfig.memory_config` 对象运行时透传到 server metadata。没有复制 memory transform、model spec 或第二份持久化 metadata。
- 修复 Tyro YAML 顶部注释后才出现 `!dataclass` 标签时被误判为 safe YAML 的恢复问题；safe-YAML 的旧模板恢复测试仍通过。
- 未完成项属于并行依赖：Banach 的 B1/B2 对应当前 worktree 尚未合入的训练 `save_dtype`、`memory_config` / `create_data_config` 等接口，按要求未重复定义。新增 metadata 测试用临时 `_MetadataTestConfig` / `_Bindings` 隔离待合入字段和模型构造，不声称验收真实训练 factory。训练增量合入后由训练 owner / combined reviewer 确认 `Normalize → AttachMemoryAfterNormalize → TokenizePrompt`，输出先 `MemoryOutputs` 再 robot-only `Unnormalize`，及完整仅 checkpoint 推理。未运行 GPU、6B 或 20k 任务。

workspace、各库交付 commit：

- OpenPI workspace: `/mnt/public/xcj/Projects/workspace/dc61ef10-53f0-44c2-91cc-c78d1cb6676e/openpi`
- 依赖 core 修复: `7acff60d561ac009d2fc57ddb3784c053db15546`
- 前次交付: `489359f8655c0a0af35447caa71f4db702fefabe`（6 files，318 additions / 7 deletions；仅 checkpoints、checkpoint_metadata、policy_config 及定向 tests）
- 前次 metadata 增量: `3d4fe31d0efef5e3dd8cdb30a3dc9d9050ecf2c5`，在 `489359f` 后；2 files，183 additions / 3 deletions。
- 本次修正交付: `cc706e37fb5c2190281789affce0095569a781af`，可在 `3d4fe31` 后 cherry-pick；2 files，55 additions / 12 deletions，其中 `checkpoint_metadata.py` +13/-7，`checkpoint_metadata_test.py` +42/-5。没有修改训练 owner 写集。

验证结果与成果位置：

- 本次在上述 OpenPI workspace 执行：`JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest src/openpi/training/checkpoint_metadata_test.py src/openpi/training/checkpoints_test.py src/openpi/training/config_test.py src/openpi/policies/policy_test.py -m 'not manual' --basetemp=/tmp/dc61ef10-complete-metadata-tests -q`：14 passed，2 manual tests deselected（8.99 秒）。包括真实 tiny Orbax BF16/FP32 参数保存恢复和旧 safe-YAML 回归。
- 真实文件名回归：`meta/stats.json`、`tasks.jsonl`、`episodes_stats.jsonl`、`provenance.json`、`nested/unlisted.json`，以及 `metadata/source/scene_info.json`、`robot_edge_comparison.json` 和 sidecar `metadata/provenance.json` 均逐字保留。继续验证多数据集同名文件不覆盖，root episode/raw memory labels、Parquet、视频、源码及 data 下即使名为 config.yaml 的文件不复制；非项目 cwd、相对来源、移走全部来源后的 checkpoint 配置和 datasets 恢复均通过。
- command 参数化验证三个数据定位 env 的设置/省略两种情形，含空格的值可通过 shlex 无损还原；HF_TOKEN 和其测试值不被保存。当前项目 commit/cwd、本次真实参数、覆盖旧 command、无独立 git_commit 文件的原检查继续通过。
- `ruff check`、`ruff format --check`（两个改动文件）及 `git diff --check` 通过。
- 前次已验证、此次未重复运行的 core memory_config 回归：`JAX_PLATFORMS=cpu CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q packages/openpi-client/src/openpi_client/memory_config_test.py`：18 passed。
- 本次 `/tmp/dc61ef10-complete-metadata-tests` 已清理，tiny checkpoint 和临时上游 metadata 均未保留；无 GPU/长进程或新增 job，worktree 干净，保留供 Manager / 同一 combined reviewer 验收。
