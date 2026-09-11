# C 离线安装窄审阅

独立审阅RMBench423291f4a819cabe9190ca440b12232449073299相对c59c656的可选offline-lock-dir安装变更。源task2a879870与继承5773报告可查。按MAM入口创建本机独立RMBench worktree并读AGENTS，仅新增安装路径，不复查全模拟器或改MAM。

核对C可选路径四阶段no-deps安装：锁文件来自已验证本机CPython3.10环境，torch/cu121、PyPI、torchvision、pytorch3d/curobo闭包完整、实际版本可对照；不能忽略新出现缺依赖/版本冲突。默认本机hardlink/常规解析行为保持；只读检查C稳定wrapper/两锁及fresh日志、raw uv pip check（由作者提供或你只读运行），确认严格旧运行树不被patch污染。必要本机CPU/fixture，禁止C写入/安装/GPU，避免干扰现场三机验收。

交付代码准入PASS/具体问题和证据、未验收范围，发布report。现场三机真实smoke/C100由作者负责，本review不替代。清理自己的pytest/ruff/__pycache__/fixture等且不跟随共享软链，保留worktree供Manager归档。不重复建立依赖体系，不修改业务代码。
