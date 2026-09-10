# 目标
本机yrfs禁止跨目录hardlink且无reflink。用户核心是快速独立环境并省空间，请验证 uv --link-mode symlink 是否可作为实际替代，而非共享整个venv。
# 背景与范围
Python3.12；canonical /mnt/public/xcj/Projects/table-1000/table-1000，其 .local/uv-cache 已有完整CUDA/ManiSkill包5.8G；environment agent正在实施，不修改其代码/cache。允许你在本任务workspace建独立小实验目录和两个真实venv（本任务不改业务代码无须完整worktree），使用独立实验cache，必要时只读复用已有wheel源，不清理现有cache。
用小包两个版本验证：两个独立venv symlink安装相同版本的时间/字节、链接去向，A中用uv升级/卸载是否破坏B或cache，editable项目是否保持各自源码，可选模拟受控临时cache清理证明限制。不要改包源码以伪造安装隔离。阅读官方uv docs cache/reference cli并据其说明symlink模式cache清理会破坏环境；cache应作为持久包仓库不可clean/prune，不应称可随意删的缓存。
先回报CODEX_THREAD_ID。尽快给manager可行结论、实测证据、边界、适用的脚本最小改动建议；发布report。只在本机，不访问wuwen-2不同集群，不派发agent。
