task_revision: 8b6180a14f423c72ee497b1d181b9f043326cd5c

# ed2f2f34：原两项 P1 关闭，剩余 X1 异步 wait 回归

**剩余1项：X1 非零 action_queue_remaining 也被 SDK handoff 锁阻塞，尚不能整体放行 live。** 原同步 wait 提前返回、延迟 tick 错误映射两个 P1 均已修复。F0/sim、新 wire 7项、latency、wheel 已GO结论维持；历史证据引用已发布报告 `f51353f`、`05ba1a0`，不重开这些 gate。

候选：`ed2f2f34a1eea74e8449d39b889555fdfcc659fc`。原独立工作区 `/mnt/public/xcj/Projects/workspace/0bc5129d-623c-4c3d-8bce-b8c172ccca56/`；bridge HEAD `c44824bfdbfcf47a4662d22a561b44cc4a5affe9`（候选等价 cherry-pick），OpenPI保持 `f3f645938170cc6f84082d3b07bdc9820cb223c1`（ffa308d等价树）。未修改作者实现。

## 剩余 P1：仅 X1，非零 wait 新增同步阻塞

位置：`robot_bridge/robot/controllers/x1/controller.py:523–525`。新增 `_wait` 无条件获取 `_action_execution_lock`；真实 `_exec_loop` 在持有同一锁时调用 `_publish_action`。因此即使排期剩余已满足非零 threshold，也必须等 SDK 返回，后面的 `threshold != 0` 无法避免这次等待。这改变了本task明确保留的异步 get_obs→infer 流水线，也影响该controller的legacy调用者。

独立同输入对照：真实execute接受1行，发送已进入但由Event暂缓返回；传感器及图像时间在排期末端之后。真实 `get_obs(slave_state_ts=[0], image_ts=[0], wait_condition={action_queue_remaining:1})`：

| 实现 | SDK阻塞100ms期间get_obs是否返回 | 返回progress |
| --- | --- | --- |
| ed2f2f34 X1 | 否；释放SDK后才返回 | completed=0, queued=1（旧图像） |
| 父版本X1的_wait，其余相同 | 是 | completed=0, queued=1 |
| ed2f2f34 X1Pro | 是 | completed=0, queued=1 |

父版本对照只在reviewer进程内载入HEAD^的 `_wait`，未修改源码。应保留非零threshold原有排期判断，使新增handoff等待仅作用于零剩余drain；不需要改实时发送顺序、补发过期动作或新RPC。后续只需此小增量及零/非零wait对照。

## 原两项关闭及边界证据

使用真实X1 loop、X1Pro **multiprocessing.spawn子进程**中的真实 `exec_worker_main`、真实execute/get_obs、JPEG/pose buffers与MemoryContext。只替换ROS/SDK初始化及发送函数为CPU Event/记录器；没有硬件或GPU。

- **同步wait P1关闭（两controller）。** 单行发送暂缓时，零剩余get_obs不返回；释放发送、仅更新pose而保留旧图像时仍不返回。此时无图像查询为1/0，旧图像查询仍为0/1；更新图像后，同一个待返回get_obs成功，progress为1/0。
- **跳tick位置 P1关闭（两controller）。** 3行14维目标依次全1/2/3、间隔20ms，延迟90ms才允许loop处理：实际只发送3，progress为3/0；H50/K3、逐行ID1/2/3的真实Context得到actual_k=3、index2、cache=[3]，零剩余get_obs可drain，无过期动作补发。handoff前的观察时间仍显示0/3。
- **partial prefix/cut/reset通过（两controller）。** 间隔200ms，tick落在第2/3端点之间，首次交接插值约2.25，进度2/1，Context消费index1、cache=[2]。cut丢掉剩余1项，reset后cache=[0]；迟到尾项与重复已处理端点均不增加进度。
- **真实子进程旧epoch隔离通过。** X1Pro旧SDK调用未返回时cut；实际迟到的旧epoch事件不计进度、不复活parent anchor。再接受新动作，并注入“新timestamp但旧epoch”事件仍保持0/1；新epoch实际handoff后才变1/0。
- **X1 inflight cut通过。** cut等待持锁发送完成，随后保留已交接位置3、pending=0；Context reset并接受新proposal后，旧completed基线不冒充新执行（新trace actual_k=0），无旧proposal重发。

上文数字对均为completed/queued，表示交接确认的轨迹位置，不是物理到位或SDK调用次数。

## 命令、规模与交付

bridge CPU定向回归：

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/robot/controllers/test_execution_progress.py \
  tests/scheduler/test_memory_context.py \
  tests/scheduler/test_openpi_takeover.py
# 56 passed in 15.31s
```

独立harness在同一CPU环境执行 `review_live.py wait prefix epoch async`，补充定向 `partial_pro`、`baseline_async`、`x1cut`；输入、Event门控顺序及输出见上述证据。partial复现先等spawn进程ready，再按轨迹时间放行tick，排除进程启动耗时干扰。临时脚本按task要求清理。56项回归全绿未覆盖新增非零wait阻塞，不能据此整体放行。

候选增量：生产4文件 **+81/-50**，测试2文件 **+290/-3**，文档1文件 **+3/-2**。前缀与时间证据集中于既有tracker，两个controller只接入wait，无新增Context状态机/RPC。新增loop/worker/cut验证有必要；剩余问题是X1共享锁的作用范围，不要求删测试或重构控制器。

`git diff --check`通过。临时harness已删除，启动的线程及spawn子进程均已join，双库worktree保留。没有GPU/hardware/rollout新增范围；未重复Banach的模型/loss/checkpoint审查。
