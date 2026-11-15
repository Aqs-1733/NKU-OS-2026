# C 部分提示词与迭代记录

以下按四段式整理调度模块开发时的需求与验收约束，供复现和说明设计使用，不是逐字对话记录。

## 调度与上下文切换

```text
[PROMPT]
实现 Lab4 的线程调度与上下文切换：cpu_idle、schedule、proc_run 和 switch_to。
只修改 proc.c 中的调度函数、sched.c 的调度函数及 switch.S，保留线程创建模块和 wakeup_proc。

[RELY]
以源码中的 proc_struct、context、proc_list、current、idleproc 为准。
使用 PROC_RUNNABLE、local_intr_save/local_intr_restore、read_csr/write_csr 和 sfence.vma。
context 包含 ra、sp、s0-s11；pgdir 是页对齐的根页表物理地址。
参考 pmm.c 的 Sv39 satp 写法，不使用 Sv32 遗留接口 lsatp。

[GUARANTEE]
void cpu_idle(void);  // 不返回
void schedule(void);
void proc_run(struct proc_struct *proc);
void switch_to(struct context *from, struct context *to);

[SPECIFICATION]
Pre-Condition：单 hart RV64 Sv39 环境；current、idleproc 和进程链表已初始化。
目标线程处于 PROC_RUNNABLE，具有有效内核栈和页表；新旧页表均保留切换代码及栈的内核映射。
Post-Condition：调度后 current、satp 与执行线程一致；旧线程可在再次调度后继续原调用。
Case 1：idle 从表头查找；普通线程从自身之后查找，并正确跨表头回环。
Case 2：跳过非就绪线程；仅当前可运行时继续当前线程；无普通就绪线程时选择 idle。
Case 3：proc_run 的目标等于 current 时不切换；实际切换时保存并恢复原中断状态。
Requirements：清除当前 need_resched，更新所选线程 runs；切换采用 Sv39 MODE=8 和物理页号，
写 satp 后执行 sfence.vma。switch_to 按 context 布局保存、加载 ra/sp/s0-s11 后 ret，
通过编译期断言核对偏移。保留 LAB4 标记，填写学号 2411788。
Validation：编译后验证调度顺序、回退行为、寄存器保持、中断状态及页表切换；保存运行日志。
```

## 独立测试与 GDB 验证

```text
[PROMPT]
为调度模块建立独立运行测试，并用 GDB 检查上下文保存与恢复。

[RELY]
链接实际 proc.c、sched.c、switch.S 及必要的项目库函数，使用 QEMU 4.1.1。
在独立测试目录中准备静态 PCB、线程栈和测试页表，不改动正式创建模块与内核初始化流程。

[GUARANTEE]
提供可复现的运行脚本、GDB 命令和原始日志，记录每项检查的实际结果。

[SPECIFICATION]
Pre-Condition：调度代码已能编译；测试线程具有有效栈和初始化的 context。
Post-Condition：检查通过时，能观察到线程实际运行及恢复；失败时输出对应断言并结束测试。
Cases：覆盖空链表、非就绪过滤、仅当前可运行、跨表头轮转、多线程往返、cpu_idle 调度、
中断初始开/关和嵌套恢复、全部 s0-s11 的哨兵保持及 proc_run(current)。
Requirements：分别在 M 态和带有效 Sv39 页表的 S 态运行；通过 satp 读回检查页表根，
用 GDB 比较旧 SP/RA 的保存值和目标 SP/RA 的恢复值。
Validation：独立测试与完整启动、首次线程入口、正式评分分别记录；说明各自覆盖范围。
```

## 实现过程中的问题

首先在 M 态独立环境中检查调度选择和寄存器切换，再加入 S 态页表切换与 `cpu_idle` 调度路径。测试链接实际实现代码，PCB 和线程栈由测试程序准备，因此可以在线程创建模块完成前检查调度模块。

测试程序第一次链接时出现 `memset` 未定义。原因是编译器将结构体清零转换成了 `memset` 调用，而独立测试没有链接该函数。加入项目已有的 `string.c` 后，测试正常运行。

GDB 检查中，QEMU 4.1.1 的虚拟 `priv` 寄存器读数与测试启动流程不符，未采用该读数判断特权级。S 态测试在启动代码中设置 `MPP=S` 后执行 `mret`，随后检查 `satp` 和上下文切换。保存、恢复是否正确则直接比较寄存器与 `context` 中的数值，结果见 5.5。
