# 目标
独立诊断 wuwen-4090-3 无法运行共享table1000环境的Vulkan初始化，并判断能否通过用户态环境配置修复。只负责4090-3，environment agent负责4090-2。
# 背景
用户要求worktree仅本机创建，其他同集群机器直接运行。现成共享env：/mnt/public/xcj/Projects/table-1000/workspace/b52655b9-cb65-4c6e-94be-2cad789235e6/table-1000/.venv（实体独立，三方包symlink至/mnt/public/xcj/cache/uv）；canonical main为b56e55e，读其AGENTS/环境文档。wuwen-4090-3为x86_64/glibc2.39/Python3.12、4x4090/driver580.82.07。Python包导入/资产probe通过，但ManiSkill CPU smoke的renderer创建ErrorIncompatibleDriver。现有最小Vulkan loader probe：本机23 instance extensions且vkCreateInstance=0，远端3仅4个扩展且-9，ICD=/etc/vulkan/icd.d/nvidia_icd.json，用户库/内核版本匹配；远端3有modeset/DRM节点但缺本机的/dev/nvidia-caps。不要把缺节点直接当确定根因，查loader调试/库加载/权限/graphics capability等证据，优先找不影响现有GPU作业的用户态配置办法。
# 约束
先回报CODEX_THREAD_ID。通过SSH只读诊断为主，可在本任务outputs下建临时probe/日志；不创建新的远端venv、不运行uv或安装/更换内核驱动，不重启机器/容器/其他进程，不擅自改设备映射或权限。若需系统改变先给manager精确证据与最小方案；可逆用户态环境变量配置/本任务ICD文件可试。一次只跑一份有界smoke，选择空闲GPU。与/root/environment协调共享已完成证据，不重复大矩阵。报告可实现修复或确切所需运行端条件并发布MAM report；不改业务代码，不派发agent。
