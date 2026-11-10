# Lab4 完整实验要求

> 2026-11-10（Asia/Shanghai）从课程站点抓取。以下保留实验目的、实验内容、全部练习与报告要求的原文；未代写实验实现。

完整原理、项目组成、代码示例与图表见 [指导书全文](guide-full.md)，也可打开 [离线阅读入口](guide/index.html)。

## 要求导航

- 前置：补齐当前源码中 Lab2 / Lab3 注释对应的实现。
- 模块一：`page_insert`、`page_remove`。
- 模块二：`alloc_proc`、`proc_init`、`kernel_thread`、`do_fork`、`copy_thread`、`copy_mm`。
- 模块三：`cpu_idle`、`schedule`、`proc_run`、`switch_to`。
- Challenge：中断保存/恢复原理；Sv32 / Sv39 / Sv48 与 `get_pte` 设计讨论。
- 报告：Markdown、整体逻辑线、核心函数、spec / prompt、AI 生成问题与修复、实验和 OS 原理知识点对照、未覆盖的重要知识点。
- 提交：保留 Lab4 标记，完成时以学号替换 `YOUR CODE`，提交代码及报告到小组 Git 仓库。
- 路径说明：手册中的 `labcodes/lab4` 在本分支对应 `code/`；`switch.s` 在附件中实际为 `code/kern/process/switch.S`。

---

## 以下为课程原文


来源：<http://oslab.mobisys.top/lab2026/_book/lab4/lab4_1_goals.html>

## 实验目的

- 了解虚拟内存管理的基本结构，掌握虚拟内存的组织与管理方式
- 了解内核线程创建/执行的管理过程
- 了解内核线程的切换和基本调度过程


来源：<http://oslab.mobisys.top/lab2026/_book/lab4/lab4_2_labs.html>

## 实验内容

在前面的实验中，我们已经完成了物理内存管理和基础页表机制的实现，使内核具备了对物理内存页的分配与管理能力，并能够建立起虚拟地址到物理地址的基本映射结构。但当前系统仍然只能以单一执行流的方式运行，无法并发执行多个任务，也尚未体现虚拟内存机制在进程或线程隔离中的作用。

本实验将在此基础上进一步扩展，完成以下两方面内容：

首先，**进一步完善虚拟内存管理，实现基本的地址空间结构**。通过引入虚拟内存描述结构，管理进程或线程的虚拟地址空间布局，为每个执行实体提供逻辑上的运行空间。与后续实验中的缺页异常和页面置换不同，本实验中的虚拟内存仍采用**预映射方式**，即在建立地址空间时一次性完成所有需要的页表映射，不涉及按需分配或页面置换。

其次，**引入内核线程机制，实现多执行流并发运行能力**。内核线程是一种特殊形式的“进程”。当一个程序加载到内存中运行时，首先通过ucore OS的内存管理子系统分配合适的空间，然后就需要考虑如何分时使用CPU来“并发”执行多个程序，让每个运行的程序（这里用线程或进程表示）“感到”它们各自拥有“自己”的CPU。本实验将实现线程控制块、上下文切换和调度器等内容，从而实现多线程并发执行，使内核能够调度多个执行实体轮流使用 CPU 运行。

内核线程与用户进程的区别如下：

| 比较项 | 内核线程 | 用户进程 |   
| --- | --- | --- |
| 运行模式 | 仅在内核态运行 | 在用户态和内核态之间切换 | 
| 地址空间 | 共享内核地址空间 | 拥有独立的用户虚拟地址空间 |  

通过本实验，系统将从“单一执行流的内核”发展为“支持多线程调度的内核”，并完成基本的虚拟内存环境框架搭建，为后续实现用户进程、系统调用、缺页异常处理和页面置换等功能奠定基础。

需要注意的是，在ucore的调度和执行管理中，**对线程和进程做了统一的处理**。且由于ucore内核中的所有内核线程共享一个内核地址空间和其他资源，所以这些内核线程从属于同一个唯一的内核进程，即ucore内核本身。


来源：<http://oslab.mobisys.top/lab2026/_book/lab4/lab4_2_1_exercises.html>

### 练习

本实验按“虚拟内存页操作 -> 进程创建与初始化 -> 进程调度”三条主线展开，核心目标是让内核从“已经具备物理内存管理和基础页表能力”进一步走到“能够创建线程、登记线程、调度线程并完成上下文切换”。对应的执行链可以概括为 `kern_init -> pmm_init -> pic_init/idt_init -> vmm_init -> proc_init -> cpu_idle -> schedule -> proc_run -> switch_to`，其中前半段负责把地址空间准备好，后半段负责让第一个可运行线程真正跑起来。

本实验依赖实验2/3。请使用你此前设计的提示词生成相应实验代码，并将生成结果填写到本实验代码中标有“lab2”/“lab3”注释的对应位置，确保代码能够正确编译。

#### 功能模块一：虚拟内存页操作功能（设计提示词借助 ai 完成）

要求实现的函数有：

```c
int page_insert(pde_t *pgdir, struct Page *page, uintptr_t la, uint32_t perm);(kern/mm/pmm.c)
void page_remove(pde_t *pgdir, uintptr_t la);(kern/mm/pmm.c)
```

整个功能模块的具体功能为：这个模块负责在现有多级页表框架上完成最基本的映射维护，也就是把物理页挂到指定线性地址上，以及把已有映射安全地撤销掉。`page_insert` 负责建立或更新映射，`page_remove` 负责删除映射，它们共同决定一个线性地址最终对应哪一页物理内存，同时也决定物理页引用计数是否正确、页表状态是否一致、TLB 是否需要失效。这个模块完成后，页表测试、静态内核映射检查以及后续线程地址空间相关逻辑才有可靠基础。

整个功能模块的注意事项为：这里最关键的是保持“页表项内容、物理页引用计数、TLB 状态”三者同步。`page_insert` 不能简单覆盖旧项，而要正确处理原地址已经映射到同一物理页、或者原地址已经映射到其他物理页这两种情况；`page_remove` 也不能假定目标地址一定存在有效映射。由于 `get_pte(pgdir, la, 1)` 可能需要分配中间级页表页，所以映射建立过程本身可能失败，调用路径必须能正确返回错误并保持系统状态干净。所有页表更新完成后都要考虑对应 TLB 失效，否则测试中会出现看似已更新、实际上仍在使用旧翻译结果的情况。

整个功能模块应该满足的对外的接口为：对外只需要提供“建立映射”和“撤销映射”两个动作。`page_insert` 成功时应让指定线性地址稳定映射到目标物理页，并把权限位设置为调用者要求的状态；失败时应返回 `-E_NO_MEM`，且不能留下半完成映射。`page_remove` 则应作为一个幂等删除接口存在，目标地址有映射时删除映射、无映射时安静返回，不应把“未映射地址”当作异常情况。

整个功能模块可以借助的接口函数、结构体、数据结构为：这个模块主要依赖 `get_pte()`、`pte_create()`、`pte2page()`、`page_ref_inc()`、`page_ref_dec()`、`set_page_ref()`、`alloc_page()`、`free_page()`、`tlb_invalidate()`、`flush_tlb()` 等现成接口，也依赖 `pde_t`、`pte_t`、`struct Page`、`pages`、`boot_pgdir_va` 以及页表权限位宏 `PTE_V`、`PTE_U`、`PTE_W`、`PTE_R`。其中 `get_pte()` 负责定位目标页表项，后续两个函数则在此基础上完成映射建立和映射删除。

#### 功能模块二：进程创建及初始化功能（设计提示词借助 ai 完成）

要求实现的函数有：

```c
static struct proc_struct *alloc_proc(void);(kern/process/proc.c)
void proc_init(void);(kern/process/proc.c)
int kernel_thread(int (*fn)(void *), void *arg, uint32_t clone_flags);(kern/process/proc.c)
int do_fork(uint32_t clone_flags, uintptr_t stack, struct trapframe *tf);(kern/process/proc.c)
static void copy_thread(struct proc_struct *proc, uintptr_t esp, struct trapframe *tf);(kern/process/proc.c)
static int copy_mm(uint32_t clone_flags, struct proc_struct *proc);(kern/process/proc.c)
```

整个功能模块的具体功能为：这个模块负责把系统中“已经能运行内核代码”推进到“已经能创建并登记多个内核线程”。`alloc_proc` 负责得到一个干净的进程控制块，`proc_init` 负责把当前执行现场包装成 `idleproc` 并创建第一个真正的内核线程 `initproc`，`kernel_thread` 负责把函数入口和参数整理成线程首次运行所需的临时上下文，`do_fork` 负责把这些信息和内核栈、PID、链表、状态位等资源真正组合成一个可运行实体，`copy_thread` 负责把 trapframe 和 context 安放到新线程自己的内核栈上，而 `copy_mm` 则在当前实验阶段承担地址空间处理接口的占位作用。这个模块完成后，系统里至少要存在 `idleproc` 和 `initproc` 两个关键线程，并且 `initproc` 需要能够在后续调度中被真正切换执行。

整个功能模块的注意事项为：这里最容易出错的是“线程生命周期状态”和“资源挂接顺序”不一致。`alloc_proc` 必须把 PCB 置于安全空白状态，避免后续代码误用未初始化字段；`proc_init` 中的 `idleproc` 并不是普通 fork 出来的线程，而是直接复用当前执行现场，所以它的 PID、内核栈、调度标记和 `current` 位置都带有特殊含义；`kernel_thread` 与 `copy_thread` 必须配合 `forkret`、`forkrets`、`__trapret` 形成正确的首次运行链路；`do_fork` 则必须正确处理失败清理、PID 分配、链表挂接和唤醒顺序，否则会出现资源泄漏、僵尸结构或线程状态错误。当前阶段的 `copy_mm` 不做真正的用户地址空间复制，但仍需要维持函数形态完整，方便后续实验继续扩展。

整个功能模块应该满足的对外的接口为：这个模块提供的是“线程从哪里来、如何进入系统、如何第一次运行”的完整外部接口。`alloc_proc` 应返回一个已完成基础字段初始化的 PCB；`proc_init` 执行后应保证进程管理全局结构、`idleproc`、`current` 和 `initproc` 都处于可用状态；`kernel_thread` 应把普通函数包装成可创建线程的上下文并返回新线程 PID；`do_fork` 应返回新线程 PID 或负错误码；`copy_thread` 与 `copy_mm` 则作为内部辅助接口，分别负责首次运行现场和地址空间处理。

整个功能模块可以借助的接口函数、结构体、数据结构为：这个模块主要依赖 `struct proc_struct`、`struct context`、`struct trapframe`、`list_entry_t`、`proc_list`、`hash_list`、`idleproc`、`initproc`、`current`、`nr_process` 等核心数据结构和全局变量，也依赖 `kmalloc()`、`kfree()`、`memset()`、`memcpy()`、`alloc_pages()`、`free_pages()`、`page2kva()`、`kva2page()`、`set_proc_name()`、`find_proc()`、`get_pid()`、`wakeup_proc()`、`list_init()`、`list_add()`、`boot_pgdir_pa`、`bootstack`、`read_csr(sstatus)`、`SSTATUS_SPP`、`SSTATUS_SPIE`、`SSTATUS_SIE`、`kernel_thread_entry`、`forkret`、`forkrets` 等已有接口与符号。

#### 功能模块三：进程调度（设计提示词借助 ai 完成）

要求实现的函数有：

```c
void cpu_idle(void);(kern/process/proc.c)
void schedule(void);(kern/schedule/sched.c)
void proc_run(struct proc_struct *proc);(kern/process/proc.c)
void switch_to(struct context *from, struct context *to);(kern/process/switch.s)
```

整个功能模块的具体功能为：这个模块负责把已经创建出来的内核线程真正交给 CPU 执行。`cpu_idle` 作为空闲线程的执行主体，持续等待调度需求；`schedule` 负责从进程链表中选出下一个可运行线程；`proc_run` 负责在安全的临界区内切换当前线程、页表和执行现场；`switch_to` 则负责最底层的寄存器上下文保存与恢复。这个模块完成后，系统不再只是“拥有线程对象”，而是已经具备让 `initproc` 从 `idleproc` 手中接管 CPU 的能力。

整个功能模块的注意事项为：这里最重要的是切换过程必须保持原子性。`schedule` 和 `proc_run` 都需要在关键区域内避免被中断打断，否则当前线程、页表和实际执行现场之间可能出现不一致。`schedule` 负责选择正确的 runnable 线程，并在找不到可运行线程时退回 `idleproc`；`proc_run` 负责更新 `current`、切换页表并调用 `switch_to`；`switch_to` 只做上下文保存和恢复，不参与调度策略判断。新线程第一次运行时之所以能走到正确入口，是因为前一个模块已经把它的 `context.ra` 和 `trapframe` 预先组织成了 `forkret -> forkrets -> __trapret` 这条恢复链路。

整个功能模块应该满足的对外的接口为：对外而言，`cpu_idle` 应持续作为空闲循环存在，检测到需要重调度时调用 `schedule`；`schedule` 应完成一次合法的调度选择并触发进程切换；`proc_run` 应让目标线程成为当前运行线程并完成页表切换；`switch_to` 则应根据两个 `struct context` 指针完成从旧线程到新线程的寄存器状态迁移。

整个功能模块可以借助的接口函数、结构体、数据结构为：这个模块主要依赖 `struct proc_struct`、`struct context`、`read_csr()`、`write_csr()`、`SATP_MODE_SV39`、`RISCV_PGSHIFT`、`boot_pgdir_pa`、`flush_tlb()`、`proc_list`、`current`、`idleproc`、`need_resched`、`runs`、`PROC_RUNNABLE`、`local_intr_save()`、`local_intr_restore()`、`switch_to()`、`list_next()`、`le2proc()` 以及 `forkret`、`forkrets`、`__trapret` 这一条首次运行恢复链路。注意 `libs/riscv.h` 中的 `lsatp()` 是 Sv32 遗留，无法表达 Sv39 的 satp，本实验中不可用；`kern/mm/pmm.c` 中的 `enable_paging()` 为正确写法参照。

#### 扩展练习 Challenge

1. 说明语句 `local_intr_save(intr_flag); ... local_intr_restore(intr_flag);` 是如何实现开关中断的。
2. 深入理解不同分页模式的工作原理（思考题）。

`get_pte()` 函数位于 `kern/mm/pmm.c`，用于在页表中查找或创建页表项，从而实现对指定线性地址对应的物理页的访问和映射操作。这在操作系统的分页机制下，是虚拟内存与物理内存建立映射关系的关键基础。

- `get_pte()` 函数中有两段形式类似的代码，结合 `sv32`、`sv39`、`sv48` 的异同，解释这两段代码为什么如此相像。
- 目前 `get_pte()` 函数将页表项查找和页表页分配合并在一个函数里，你认为这种写法好吗？有没有必要把两个功能拆开？


来源：<http://oslab.mobisys.top/lab2026/_book/lab4/lab4_5_labs_requirement.html>

## 实验报告要求

1. 基于 `markdown` 格式完成实验报告，以文本说明为主。
2. 说明自己对本章节整体逻辑线的理解，即本章节是按照什么顺序、围绕哪些功能逐步实现的。
3. 说明自己对每个功能的核心函数或功能模块的理解。
4. 说明每个练习的 `spec` 是怎么写的，`prompt` 是怎么写的。
5. 说明在使用提示词让 AI 生成代码的过程中出现了什么 bug，以及你是怎么解决的。
6. 列出你认为本实验中重要的知识点，以及与对应 OS 原理中的知识点，并简要说明二者的含义、关系和差异。
7. 列出你认为 OS 原理中很重要、但在本实验中没有对应上的知识点。

从 oslab 网站上取得实验代码后，进入目录 `labcodes/lab4`，完成实验要求的各个练习。在目录 `labcodes/lab4` 下存放实验报告，推荐使用 `markdown` 格式。每个小组建立一个 gitee 或 github 仓库，对于 lab4 中的编程任务，完成编写之后，再通过 `git push` 命令把代码和报告上传到仓库，最后请提前或按时提交到 git 网站。

注意有“lab4”的注释，代码中所有需要完成的地方（challenge 除外）都有“lab4”和“YOUR CODE”的注释，请在提交时特别注意保持注释，并将“YOUR CODE”替换为自己的学号，并把所有标有对应注释的部分填上正确的代码。
