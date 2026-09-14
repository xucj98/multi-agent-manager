# 六个首波N/J模型20k保存与恢复证据审查

terra/max，只读审查，科学结论与最终验收由Manager。先读MAM/相关repo AGENTS与本地说明，mam task show本task，再读源task e3bc64f1-7f0d-46d2-9e54-831aa1727384 已发布report7819a47007450a5faa262b97d507c483fba7582c及实际20k合同。范围仅swap_blocks/battery_try/cover_blocks各N/J seed0，共6个20k模型；不碰尚在运行的S、不新训练/仿真/转换/传输/改缓存，不重复已接受代码schema/50step gate。

实际训练代码N clean5835fa04055d520e418cc1448c1bd58fa1e665cb、J clean34002dce65962734c59725a0f6d982ae2c438a2d，区别于task登记开发HEAD。共同train0、bs32、H50/K30、从pi05_base初始化、BF16 model-only。wuwen-1 /root/.cache指向/mnt/public/xcj/cache、无HF_LEROBOT_HOME覆盖、XLA_FLAGS=--xla_gpu_enable_command_buffer= 的CUDA12.2兼容项按实际launcher/receipt留痕，checkpoint command allowlist不含该变量的限制保留，不篡改metadata。

两组最终receipt：
- /mnt/public/xcj/Projects/openpi/checkpoints/wave1_n_formal20k_5835fa0_nocmdbuf_20260913T0940Z/validation/final20k/final20k_receipt.json SHA b8240d5689c8f38f9e7d5ff5e198ccf9410b54749b41f734e4941fc78ea3b774。
- /mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z/validation/final20k/final20k_receipt.json SHA 01a4ad8016b888f5a322dee2225b41e4a7e0bb0afc5530ffd6c99c31646e8577。

独立核验receipt/脚本和其引用日志hash，实际step20000及Orbax finalization结束/无fatal、params/metadata清单和norm/schema/task/seed/code/data绑定，模型是model-only完整20k而非smoke。检查CPU验证确实覆盖全参数51 leaves/3,353,433,872 elements/BF16 finite shape，检查GPU checkpoint-only恢复日志和source-read guard（动作[50,14]，J memory分别[50,3]/[50,1]/[50,4]）。阅读验证器确认没有依赖原YAML/source侧车/pi05_base/dataset来补回checkpoint缺项。无需重跑完整CPU大模型加载或GPU恢复，明确基于已运行验证日志与脚本、没有亲自重新计算参数全量数值的范围限制。若发现实质缺口报告而不自行重跑占卡。

从MAM与进程收据核实六条作业身份已归档，未误杀/动用两条S；checkpoint和来源只读。保留可复算小型证据、六模型具体checkpoint清单及独立receipt到本task evidence；如需源码worktree仅为涉及版本创建，不能改运行树。交紧凑报告、是否有训练完成计数/移交eval阻断、证据路径/hash与实际限制。不要声称已有正式评测成绩。报告发布后正常结束turn。
