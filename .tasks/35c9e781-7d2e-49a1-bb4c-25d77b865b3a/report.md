task_revision: 51d1634247d93727e97bf27cd4e3ddff6a4c247c

## 正式100完成；GPU0可移交Q2

完成与未完成：BF16两条smoke、连续100、50条中点、完整逐seed配对、结果README、smoke/临时输入清理、job归档与GPU0退出检查全部完成。工作区保留待Manager归档。

最终BF16 **92/100**，本次FP32文件F0 row30 **92/100**。共同成功85、共同失败1；BF16成功/FP32失败7、BF16失败/FP32成功7。BF16失败为button_not_pressed 4次、button_press_insufficient 4次。前50条45/50，相对完整F0基线−2个百分点，同seed前50条同为45/50，未触发>10个百分点gate。

accepted seeds完整为100000–100099。1471个已执行query均满足K30、index29/row30及terminal trace；前5视频391/405/400/399/401帧匹配步数；100条视频开关检查通过。无runtime_error，scheduler全部正常退出。正式期间三库保持固定且干净，policy有效配置、scheduler与F0一致，私有manifest与继承metadata哈希核对通过，没有重新训练、导出或改变推理精度。

正式13:20:30启动，最后scheduler于**2026-09-10 16:00:08.519 +08:00**结束，summary completed。
**16:01:58.771 +08:00明确确认GPU0可释放/移交Q2**：runner PID2710786及所有自有服务/worker退出；GPU0无计算进程（1MiB/0%），TCP19300/19302、UDP19301空闲。证据为gpu0_handoff_verification.json；不再占用GPU0。

MAM job `577e7ab0-eb55-4c65-bed5-3b725e958435`通过新版job status实时确认stopped，16:02:27归档。后续无需监控本评测。

## 产物与验证边界

正式产物：`/mnt/public/xcj/Projects/RMBench/eval_result/memory_chunk_20260910/precision_rearrange_full_row30_bf16_100ep_seed0`。

- `final_review_0100.json`：最终协议/视频/进程/lineage审核。
- `paired_seed_results.json`：100条逐seed配对及失败原因；`midpoint_review_0050.json`保留中点。
- `checkpoint_metadata/lineage/config_source`：完整manifest/audit及F0 config/command/final_review副本，已逐文件核对。
- `smoke_gate_evidence`保存小型原始门禁文件，`smoke_cleanup_receipt.json`记录删除。
- 正式config/command、诊断、视频及进程日志保留；smoke、任务.local/precision_validation、专用Warp cache、queue日志已清理。

BF16 checkpoint保留：`/mnt/public/xcj/Projects/openpi/user_checkpoints/precision_validation/rearrange_full_key_state_30k_bf16/30000`。ad6导出证据随metadata继承：51叶子3353433872元素，两条BF16加载路径数值和uint16位模式差异0；未重复完整转换或数值验证。

本次100条观察成功率相同，但14个seed结果不同；不代表轨迹一致或统计等价，不将差异直接归因于文件dtype。本实验比较的是文件存储dtype，两个入口仍使用既有BF16推理。

## 工作区与交付

workspace：`/mnt/public/xcj/Projects/workspace/35c9e781-7d2e-49a1-bb4c-25d77b865b3a`。
结果说明：`RMBench/experiments/memory_chunk_20260910/README_precision_validation.zh-CN.md`。
RMBench交付commit：`2ccc7bf97463bd556491c17877a509e4a3b88468`（仅事后结果文档；diff --check通过，工作树干净）。
实际运行RMBench：`f022badd11228e5763a301339a5d1fe5574962b4`。
robot-bridge交付/运行：`bc842036e3735390f35fe1138aa7b19f5ae2f95b`。
openpi交付/运行：`58d6f2155acc3af03017677bb3f536101e6699f4`。
