task_revision: db65224a8ca9928f1112b5a198c9ed4c42d6e569

当前阶段：wash GPU2 full / GPU3 serial 各实际50更新，通过各自gate后在同卡从base独立正式20k。056bcc8树已冻结，CPU独立GO与旧阶段证据见report publication 1ab252db0d2a97ad2e47f79e98833ea1071ffd59。

- workspace: /mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/openpi
- 实际SHA: 056bcc887637cc6eda565a8ad7d45c88021d4bcd；源码工作树干净，独立.venv。
- 2026-09-10 10:45:15 CST 已启动GPU2 full smoke PID 2475683、GPU3 serial smoke PID 2475794。两者均python -u -B、batch32、seed0、50次optimizer更新、save_interval50、BF16 model-only，base由验收配置默认pi05_base初始化；暂无正式20k job，等待各自GPU gate。
- 启动前GPU2/3各1MiB，主机可用RAM约872GiB。没有占用其他卡。
- full日志：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/wash_full_smoke50_seed0_056bcc8.log
- serial日志：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/wash_serial_smoke50_seed0_056bcc8.log
- 完整启动命令、environment、PID与checkpoint目标：/mnt/public/xcj/Projects/workspace/ad6bb77e-3892-4730-ae1a-7d9cd99a5728/wash_gpu_logs/smoke_launches.json
- 数据HF_LEROBOT_HOME=/mnt/public/xcj/Projects/openpi/data/lerobot；wash v3专用robot-only norm共享于原openpi/assets/memory_v1/x1pro_wash_cup_s2m_robot/norm_stats.json。
- 剩余：两路JIT/50更新、完整BF16/shape与model-only目录检查、fresh-process仅checkpoint真实GPU infer wire；各路通过立即正式20k并MAM本机job登记。启动阶段持续查看日志，稳定训练后每小时检查。
- 原rearrange d10两份50step及必要日志继续为e6908de7保留。
