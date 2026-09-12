# C1 GPU 进程不可见：只读诊断简报

已完成只读 SSH 诊断；证据见 task workspace 的 evidence.md。未停止或重启评估、
服务或 GPU，未改动 namespace、软件、运行时或评估配置，也未读取禁止的
/proc/*/fd/0。

## 已验证事实

- 2026-09-13 00:57--01:02 CST，SSH 到 wuwen-4090-1 的身份为 root，
  hostname 为 is-ddfwxekq6usner7v-devmachine-0。PID 1 为
  runsvdir -P /opt/devmachine/init/service；当前 /proc 与 SSH shell 在
  pid:[4026541571]。
- C1 GPU1 正式评估的真实本地树仍可读：
  2130358 launcher -> 2130667 benchmark -> 2130759 robot server ->
  2130887 rmbench_sim_worker。它们的 status NSpid 都只有当前可见 PID；
  01:02 时 worker 2130887 仍为 Ssl。
- 同一诊断窗口，nvidia-smi 报告八张卡均有约 13--17 GiB 显存占用，
  compute-apps 有 25 行，所有 process_name 都是 [Not Found]。
  代表性 NVML PID（1966034、2020663、2200274、2281919、2522345、
  2909622、3250550）在当前 /proc 中不存在。已确认的本地 worker
  2130887 也不在该 NVML PID 集合中。
- 原 owner 在 00:53 已发布 GPU1/GPU7 终态记录数 52/11。本次读取的
  episode_diagnostics.jsonl 为 56/14，最后 episode_id 为 55/13，
  mtime 分别为 00:58:46/00:58:13；说明两条评估相对该基线仍有推进。
  GPU1 最后记录为 Success，GPU7 最后记录为 Fail；后者只是单个终态
  episode 结果，不能推出 formal job 已退出。

## nvitop 的 No Such Process / N/A

wuwen-4090-1 安装的是 nvitop 1.7.1。
/usr/local/lib/python3.12/dist-packages/nvitop/api/process.py 的
auto_garbage_clean 会捕获 host.PsutilError；GpuProcess.cmdline 经
self.host.cmdline() 查询失败时用 No Such Process 回退，AccessDenied
专门显示 No Permissions。username、CPU 等主机进程字段用 NA 回退。

因此，截图中的 No Such Process / N/A 表示 nvitop 对 NVML 给出的 PID
无法完成当前可见进程视图中的 psutil 查询。它可由进程在两个采样间退出，
或 NVML PID 与当前容器可见 PID 视图不同引起；它本身不表示显存已释放，
也不表示评估必然停止。

## 结论与边界

当前事实高度符合 NVML 返回的 PID 与该 devmachine 当前 /proc 视图不一致，
因而 nvidia-smi/nvitop 无法解析名称或命令行。这个会话没有可读取的
host-to-container PID 映射，不能把任一 NVML PID 与本地评估 worker
一一对应，也不能仅凭 /proc 不可见把某行显存归属断言为其他隔离环境。
GPU0 或任何未映射条目的实际 owner 仍未确定；不应据此终止作业。

采样也有边界：诊断中 numeric PID 2522345 曾短暂在本地 /proc 可见，后续
又不可见，而 NVML 仍返回该数字。允许的只读证据无法区分 PID 重用、退出
清理和不同 namespace，故未将它作为映射证据。

用户可用以下两条只读命令查看自己的评估，不要用 GPU PID 的不可解析性判断
作业归属：

~~~bash
ssh wuwen-4090-1 'ps -ww -eo pid,ppid,stat,etime,args | grep "[r]un_memory_schema_eval.py.*--run-name c_rearrange_serial_lag30_trainseed1_evalseed1_100ep_r3"'
~~~

~~~bash
ssh wuwen-4090-1 'd=/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910/c_rearrange_serial_lag30_trainseed1_evalseed1_100ep_r3; wc -l "$d/episode_diagnostics.jsonl"; stat -c "%y" "$d/episode_diagnostics.jsonl"; tail -n 1 "$d/episode_diagnostics.jsonl" | jq -c "{episode_id,result}"'
~~~

## 交付

- Workspace: /mnt/public/xcj/Projects/workspace/82bbbd0b-ee27-4a34-92c6-3d8e1cccdd8b
- 代码改动 / worktree / commit：无；任务明确为只读诊断。
- 验证：SSH 身份、hostname、PID namespace、/proc mount、已知 launcher/worker
  status/NSpid、NVML compute/显存查询、nvitop 1.7.1 本地源码和两条
  episode diagnostics 均已读取。
