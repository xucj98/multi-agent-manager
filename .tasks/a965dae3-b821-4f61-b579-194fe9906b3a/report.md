# 真实 ManiSkill 场景图审计

- Workspace：`/mnt/public/xcj/Projects/table-1000/workspace/a965dae3-b821-4f61-b579-194fe9906b3a/table-1000`，基线 `f8340d5de7ac5452a6a8d726c1fc11047c0ae6b1`；未改源码、场景或资产。
- 输出：`/mnt/public/xcj/Projects/table-1000/table-1000/outputs/a965dae3-b821-4f61-b579-194fe9906b3a/scene-visual-audit/`；图像级命令、commit、配置/场景和图像 SHA-256 见 `provenance.json`（3 场景、13 图，均存在）。
- 命令：激活 worktree 后以 `CUDA_VISIBLE_DEVICES=1` 跑 `render_compare.py --legacy-goal-config ...0001... --hide-zone-markers`，以及 `render_strip.py --package ...0006|0007... --camera cam-top|cam-diag --force`；ManiSkill 3.0.1 / maniskill3 / physx_cpu，seed 0、静置 4 step、无下载。
- 0001 图：`probe-0001/compare--initial--terminal--cam-{top,diag,front-high}.png`。机器人遮挡中部取放区，书在文件架旁、篮子混装、黑桶占前景；当前实图不同于历史验收证据，整理功能不清晰。
- 0006 图：`strips/t1k-probe-office-stationery-0006-v1--strip--cam-{top,diag}.png`。初态没有明确阻挡/先后取放依赖，`inventory-close` 与 `preserve-project` 肉眼近乎相同，深色收纳件用途也不清楚。
- 0007 图：`strips/t1k-probe-kitchen-breakfast-0007-v1--strip--cam-{top,diag}.png`。长餐具直线铺台不自然，物件更像陈列而非功能性餐前阻挡；两个终态视觉差异不足以说明真实多解。
- 所有终态都是**手写静态 target**，非实际执行轨迹终态；静帧未见明显漂浮/穿透，但不构成物理、可达或轨迹验收。所有人工状态均为待用户确认。
- 已亲自查看全部顶视/斜视，manager 已看关键图；`python -m json.tool provenance.json` 通过且全部图记录存在。未跑全库测试（任务要求短复现）；`cleanup.sh` 通过并清除了 119 KB 临时字体/NVIDIA 渲染缓存。
