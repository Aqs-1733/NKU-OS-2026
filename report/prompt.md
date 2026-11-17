# Lab4 提示词记录

## 成员 A

以下记录两轮原始提示词及原报告中的页映射要求摘录，保留四段式结构和原文内容。

### 第一轮：页映射功能实现

````text
[PROMPT]

**任务**：完成 Lab4 虚拟内存页操作部分，在 `kern/mm/pmm.c` 中实现 `page_insert()` 和 `page_remove()`，使内核能够建立、修改和删除虚拟地址到物理页的映射。

**操作要求**：

先阅读 `pmm.c`、`pmm.h`、`mmu.h` 中相关的数据结构和函数，再结合实验指导书及现有测试理解这两个函数的要求。

直接修改项目中的实际代码，保留原来的函数声明和实验注释，只完成成员 A 负责的部分。Lab2、Lab3 的代码已经有现成实现，不需要重新编写。不要修改进程管理、调度模块或测试程序。

**输出要求**：

完成两个函数后，使用项目原有的测试进行验证。最后说明修改了哪些代码、测试是否通过以及还有什么问题。暂时不要提交 Git。

[RELY]

以项目中的实际定义为准，主要使用以下内容：

- 数据结构：`struct Page`、`pde_t`、`pte_t`。
- 页表相关宏：`PGSIZE`、`PTE_V`、`PTE_U`、`PTE_W`、`PTE_R`、`PTE_ADDR`。
- 页表操作：`get_pte()`、`get_page()`、`pte2page()`。
- 物理页管理：`page_ref()`、`page_ref_inc()`、`page_ref_dec()`、`free_page()`。
- TLB 操作：`tlb_invalidate()`、`flush_tlb()`。
- 错误码：`E_NO_MEM`。

具体参数和使用方式以现有源码为准，优先使用已有函数，不重复实现相同功能。

[GUARANTEE]

需要完成以下两个函数：
```cpp
int page_insert(pde_t *pgdir, struct Page *page,
                uintptr_t la, uint32_t perm);

void page_remove(pde_t *pgdir, uintptr_t la);
```

函数签名保持不变。如果需要使用已有的 `page_remove_pte()` 或增加内部辅助函数，可以根据实际代码处理，但不要改变其他模块的接口。

[SPECIFICATION]

### 1. page_insert()

**Pre-Condition**

`pgdir` 指向有效页表，`page` 是需要映射的物理页，`la` 是目标线性地址，`perm` 指定映射权限。

**Post-Condition**

成功返回 0，目标地址映射到指定物理页，页表权限和引用计数正确。无法分配所需页表页则返回 `-E_NO_MEM`，不能破坏原有映射。

**Case 1：目标地址没有映射**

建立新的页表映射，并增加目标物理页的引用计数。

**Case 2：目标地址已经映射到同一物理页**

更新权限即可，不能重复增加引用计数，也不能错误释放该页。

**Case 3：目标地址已经映射到其他物理页**

先正确处理旧映射和旧页引用计数，再建立新映射，保证两个物理页的引用计数都正确。

**Case 4：页表创建失败**

返回对应错误码，不留下不完整的映射或错误的引用计数。

**Requirements**

正确设置页表有效位和权限位，映射改变后处理对应的 TLB 失效。注意 Sv39 多级页表的结构及现有 `get_pte()` 的行为。

### 2. page_remove()

**Pre-Condition**

`pgdir` 指向有效页表，`la` 是需要撤销映射的线性地址。

**Post-Condition**

目标地址原有的有效映射被删除，物理页引用计数正确，其他地址的映射不受影响。

**Case 1：映射存在**

清除页表项，减少原物理页的引用计数。引用计数归零后按现有内存管理规则释放物理页，并刷新对应的 TLB 项。

**Case 2：映射不存在**

直接返回，不报错，也不分配新的页表或释放其他物理页。

**Requirements**

重复删除同一个地址不能出错，不能出现重复释放或引用计数错误。

### 3. 测试要求

完成代码后：

1. 执行 `make`，检查是否存在编译错误。
2. 如果项目已经具备完整运行条件，执行 `make qemu`，查看 `check_pgdir()`、`check_boot_pgdir()` 等原有检查结果。
3. 项目支持完整评分后，执行 `make grade`，验证 `[Test PMM] PASS`。
4. 如果由于其他成员的函数尚未完成而无法编译或运行，说明具体原因，不修改其他成员负责的代码。
5. 测试没有通过就根据实际报错修改，不要删除断言或修改评分脚本，也不需要额外编写一套测试框架。

完成后简要汇报两个函数的实现思路、实际测试结果和遇到的问题。保留原有 LAB4 注释，暂不进行 Git commit 或 push。
````

### 第二轮：代码复查和 Challenge 2

````text
[PROMPT]

**任务**：继续完成 Lab4 成员 A 的工作。先审查已经实现的 `page_insert()`、`page_remove()`，然后完成实验指导书 Challenge 2 的两道思考题，整理本模块的验收情况。

**操作要求**：

1. 阅读当前 `kern/mm/pmm.c` 中的实际实现，对照实验指导书、`check_pgdir()`、`check_boot_pgdir()` 和 `tools/test_lab4.c` 检查代码。
2. 重点检查映射替换、引用计数、TLB 刷新及页表分配失败后的清理。如果发现问题，直接修改 `pmm.c`；如果没有问题，就保留现有实现。
3. 完成 Challenge 2 的全部内容，结合项目代码解释原理，答案写得准确、自然，适合直接整理到本科实验报告中。
4. 不修改其他成员的代码、测试程序和评分脚本，不重新实现 Lab2/Lab3。
5. 暂时不提交 Git，也不编写完整实验报告。

**输出要求**：给出代码审查结果、Challenge 2 完整答案，以及当前测试完成情况。没有实际运行的测试不能写成通过。

[RELY]

主要参考：

- `kern/mm/pmm.c` 中的 `get_pte()`、`get_page()`、`page_insert()`、`page_remove()`、`tlb_invalidate()`。
- `kern/mm/pmm.h`、`kern/mm/mmu.h` 中的页表结构、地址转换宏和物理页管理接口。
- 原有的 `check_pgdir()`、`check_boot_pgdir()`。
- `tools/test_lab4.c` 中的 `test_lab4_pmm_basic()`。
- 实验指导书第 9 页 Challenge 2，以及虚拟内存管理相关章节。

所有分析以项目源码和实验指导书为准，涉及 Sv32、Sv39、Sv48 的区别时使用 RISC-V 分页规范，不自行编造项目中不存在的函数。

[GUARANTEE]

本轮需要完成：

1. 审查已有 `page_insert()`、`page_remove()`，必要时修复，不改变函数签名。
2. 回答 Challenge 2 的两道思考题：
   - 结合 Sv32、Sv39、Sv48 的异同，解释 `get_pte()` 中两段代码为什么相似。
   - 分析 `get_pte()` 将查找和分配放在一起是否合理，以及是否需要拆开。
3. 整理 A 部分基础要求、Challenge、测试的完成状态。

[SPECIFICATION]

### 1. 代码审查

**Pre-Condition**

两个目标函数已经实现，`pmm.o` 编译通过。完整 `make` 因 `proc_init`、`cpu_idle` 未定义而无法完成链接。

**Post-Condition**

两个函数符合指导书和现有测试的要求。发现实际问题则完成修复，未发现问题不做无关修改。

**Case 1：映射建立与替换**

检查首次映射、同页重新映射、替换不同物理页、权限更新后的页表项与引用计数是否正确。

**Case 2：映射删除**

检查正常删除、重复删除、删除不存在的映射，以及共享物理页的引用计数处理。

**Case 3：页表分配失败**

结合 `get_pte()` 的实际行为，分析中间页表分配失败后的资源清理。重点保证不破坏已有映射、不释放仍被使用的页表页。

**Requirements**

不要为了形式上的优化重构代码。只有确认存在错误或不符合实验要求，才修改实现。

### 2. Challenge 2

**第一题：分页模式与 get_pte()**

先说明 Sv32、Sv39、Sv48 的虚拟地址位数、页表层级、各级索引位数以及地址转换过程。

然后结合本项目的 `get_pte()`，解释两段相似代码分别处理哪一级页表，为什么使用相似的检查、分配和初始化逻辑。

**第二题：查找与分配是否应该拆开**

结合 `get_pte()` 的 `create` 参数说明现有设计的优点和不足。

分别分析接口复用、代码简洁性、资源分配副作用、错误处理和后续维护问题，最后给出有依据的个人看法。

两题均需要结合实际实现，不要只写一般概念，也不要为了回答思考题而修改 `get_pte()`。

### 3. 验收与交付

1. 如果修改了 `pmm.c`，重新编译 `pmm.o`，记录实际结果。
2. 不再反复执行已知会因其他成员缺失函数而失败的完整构建。
3. 列出 `check_pgdir()`、`check_boot_pgdir()`、`[Test PMM] PASS` 的真实状态，未运行的标记为待验收。
4. 输出两道 Challenge 的完整答案，并整理 A 部分已完成内容、尚未完成的测试及交接注意事项。
5. 最后确认 `git diff`，不得出现其他成员文件的修改。

不需要增加新的测试框架、回滚脚本或额外工具文件，不需要修改报告文件。最终只汇报实际完成的工作。
````

### 页映射要求摘录

以下为原报告记录的实现要求摘录。

```text
[PROMPT]
修改 kern/mm/pmm.c，完成 page_insert 和 page_remove。只修改成员 A 的代码，
保留实验注释与已有接口，不修改测试程序、进程管理和调度模块。

[RELY]
struct Page、pde_t、pte_t；get_pte、pte2page、page_ref_inc、
page_ref_dec、free_page、tlb_invalidate、flush_tlb；PTE_V、E_NO_MEM。

[GUARANTEE]
int page_insert(pde_t *pgdir, struct Page *page, uintptr_t la, uint32_t perm);
void page_remove(pde_t *pgdir, uintptr_t la);

[SPECIFICATION]
Pre-Condition：页表根有效，目标物理页已分配，地址和权限由调用者给出。
Post-Condition：插入成功返回 0，映射和引用计数正确；分配失败返回
-E_NO_MEM，原有映射不受影响。删除后目标地址无有效映射。
Case 1：建立新映射，增加物理页引用计数。
Case 2：同页更新权限，引用计数不变。
Case 3：替换旧页，减少旧页引用计数，计数为零才释放。
Case 4：页表分配失败，清理本次新建的空中间页表。
Case 5：删除有效映射，重复删除直接返回。
Requirements：按页表修改类型执行相应 TLB 失效操作。
```

## 成员 B

### 内核线程创建

以下记录 `do_fork` 阶段的提示词。在 `[RELY]` 中列出寄存器、结构体和汇编入口，在 `[SPECIFICATION]` 中约定分配失败的回滚动作，并比较进程计数、链表长度、空闲页数和 `kmalloc` 计数。

````markdown
[PROMPT]
完成从“指定内核函数及参数”到“已登记、可被调度的内核线程”的闭环。必须联合设计和验证
kernel_thread / do_fork / copy_thread / copy_mm。只修改 proc.c 的 B 区域，复用已有 get_pid、
setup_kstack、put_kstack、hash_proc、forkret、kernel_thread_entry、wakeup_proc。

[RELY]
trap.h 的 struct trapframe；entry.S 的 kernel_thread_entry（s1 为参数、s0 为函数地址）；
trapentry.S 的 forkrets -> __trapret；CLONE_VM、KSTACKSIZE、boot_pgdir_pa；
-E_NO_MEM、-E_NO_FREE_PROC；SSTATUS_SPP/SPIE/SIE。所有原型和宏从真实源码核对。

[GUARANTEE]
int do_fork(uint32_t clone_flags, uintptr_t stack, struct trapframe *tf);

[SPECIFICATION]
Pre-Condition：已有 current 和可用 PCB/物理页分配器；传入的 Trap Frame 有效。
Post-Condition：成功时返回唯一正 PID，线程具有独立 PCB、独立内核栈、正确父进程、页表和首次
执行现场，已挂入进程链表及 PID 哈希表，进程计数准确且状态可调度；失败时返回负错误码、
释放所有本次申请的资源、全局状态不变。
Case 2：进程上限返回 -E_NO_FREE_PROC，不改变计数。
Case 3：PCB、内核栈或 mm 处理失败，按已获得资源的逆序清理，无成功 PID。
Requirements：PID 分配、链表/哈希挂接、nr_process 更新及状态转移受中断临界区保护；
初始化完成前不能让调度器选中。
````

## 成员 C

以下按四段式整理调度模块的需求和测试要求。

### 线程调度

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

### 独立测试和 GDB 调试

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
