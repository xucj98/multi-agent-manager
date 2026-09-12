# 最终定向复核：PASS

审阅候选：`e4bc9821d9ea1457e47b3f1e44e9957902f50e09`（本轮修复源提交：`e7b3f5785e1ed98556e6815d255aa9d7ee80de5c`）。

本次只复核 d51 已确认的 `.bashrc` 所有权 blocker；此前对 runtime、源码隔离、optional wait 共存和文档的审阅结论维持接受。

`update_bashrc()` 现在只在恰有一组、且逐行精确匹配当前 canonical MAM trace block 的 marker 时替换该 block。marker 外任何内容均不再按 `RUST_LOG`/`LOG_FORMAT` 文本过滤。因此原 d51 的未标记条件块中的两个 export 会保留在条件内，不会被移到全局 MAM block。

我用隔离临时 HOME/项目 fixture 独立复现并确认：

- 原未标记条件块保持，输出可由 `bash -n` 解析；第二次安装结果字节一致，且只创建一次 backup。
- 未知完整 marker、残缺 marker 和重复 marker 都以非零退出；原 `.bashrc` 字节不变，不创建 backup，也不会进入 `ensure_runtime_logging`/service 路径。
- `prepare_wait_trace` 在 `start_project_service` 前执行，故上述失败不会触及 daemon/service。

独立验证通过：

```text
.venv/bin/python -B -m unittest discover -s tests -p 'test_wait_compat.py' -v
33 tests, OK

.venv/bin/python -B -m unittest discover -s tests -p 'test_wake_compat.py' -q
26 tests, OK

bash -n scripts/install.sh
git diff --check a05aff6..e4bc982
```

未发现新的 blocker。未运行 liveprobe 或模型调用，未做全局安装，也未触碰生产 shell、App Server、service、线程、机器人或 GPU。隔离 fixture 与本 worktree 的 Python 缓存已清理；worktree 保持干净。建议接受该候选。
