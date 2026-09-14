# 首波两个 S 模型独立验收
源任务 e3bc64f1-7f0d-46d2-9e54-831aa1727384，报告 a5ad92ea445b7f1ea99fa134db6102684756e8a3。仅核验 swap S / cover S；六个 N/J 已验收，无需重复。
按 AGENTS.md 读取合同并使用独立 worktree。真实训练 J/S 源为 clean 34002dce65962734c59725a0f6d982ae2c438a2d，勿把 review 自动列出的开发 HEAD 当作训练身份。
核查两条20k最终保存日志、元数据/参数目录及 binding/schema/norm provenance、从 pi05_base 独立初始化和seed0/bs32/H50/K30/serial_lag30合同；从原件复核 CPU/GPU checkpoint-only恢复记录及 source-read guard实际边界。已完成的多GB CPU/GPU数值恢复不重复运行，不启动GPU，不新增训练/评测。不以loss证明算法效果。
最终原件在 /mnt/public/xcj/Projects/openpi/checkpoints/wave1_js_formal20k_34002dce_nocmdbuf_20260913T1020Z/validation/final20k_swap_s/swap_s_final20k_receipt.json（4b8dde2011c800127eb74b25b65000e2821d42000535e573789d710f8f3f5fc9）和 validation/final20k_cover_s/cover_s_final20k_receipt.json（da1073d98b5712b4aea843b95ae601458d9b41eacbd6a40d8b5dad25bf5f2a8d）。cover训练GPU7、恢复GPU2应可区分；cache软链与HF_LEROBOT_HOME unset、XLA兼容项须据实际收据核对。
发布简明报告和独立JSON证据/原件哈希，列阻断项、验证覆盖及未重复执行的边界。保留必要材料供Manager独立裁决；不修改论文、不归档源任务。
