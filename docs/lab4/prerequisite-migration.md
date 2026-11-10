# Lab2 / Lab3 前置代码迁移记录

## 结论

Lab4 附件并非独立完整项目，现已补齐其全部 Lab2 / Lab3 标记处。只修改了 5 个源码文件，63 个附件文件原样保留，Lab4 新增 12 个函数没有提前实现。

课程站点的 16 页完整归档和全部要求保持不变；本记录是工程迁移说明，不替代指导书。

## 使用了哪些已有成果

- 基线：`efcfac7304e94b29546fa0782fce9fe1cc2f1f75`，即本分支首次导入附件后的提交。
- 来源：本仓库已完成、已集成的 `lab3` 提交 `d6c36827b67797214b73df167223087d067dd588`。
- 复核发现远端 `lab2` 当前分支仍含起始代码留空，因此没有盲目复制它；Lab2 的已完成 Best-Fit 和 `page_init` 采用 `lab3` 中继承、适配好的版本。
- 源文件与原件 / 迁移后摘要均记录于 [`source/migration-manifest.json`](source/migration-manifest.json)，可按固定提交追溯，不依赖分支以后如何变化。

## 逐项迁移和适配

| Lab4 文件 | 迁移内容 | 必要适配 |
| --- | --- | --- |
| `code/kern/mm/default_pmm.c` | Lab2 Best-Fit 初始化、内存块登记、分配、释放合并、空闲页统计 | 使用现有 `default_pmm.h`，以 `default_pmm_manager` 导出 Best-Fit，避免引入缺失的 `best_fit_pmm.h`；原有 `basic_check` / `best_fit_check` 原样保留 |
| `code/kern/mm/pmm.c` | Lab2 物理内存探测及 Page 描述符初始化 | 从 Lab4 的 KERNBASE / KERNTOP / 偏移计算物理边界，按 `sizeof(struct Page)` 预留元数据，初始化新增的 `pra_page_link` / `pra_vaddr` |
| `code/kern/trap/trap.c` | Lab3 中断分类、时钟续订和计数、异常分类及 16 / 32 位指令返回地址推进 | 保留 Lab4 的 `idt_init`、SUM 和分发框架，不携带 Lab3 演示用的“打印十次后关机” |
| `code/kern/trap/trapentry.S` | Lab3 的寄存器 / CSR 恢复以及向 `trap` 传参和调用 | 这是三处 C 文件之外的两处 Lab3 留空；保留 Lab4 特有的 `forkrets` 入口，保存 x0、清零 sscratch，并保证 stvec 入口对齐 |
| `code/kern/mm/kmalloc.c` | 现有堆分配器的接口兼容 | 只把整数虚拟地址显式转换为 `kva2page` 要求的 `void *`，消除现有 GCC 15 的编译错误；没有更换工具链或压低诊断等级 |

没有整文件覆盖启动流程、页表框架或进程框架。特别是 `proc.c`、`switch.S`、`sched.c`、真实 `init.c`、官方评分和注入工具均未改变；Lab4 页映射练习标记之后的全部原有测试及代码保持原样。

## 实际验证

### 1. 来源和改动边界

执行 `python tools/verify_lab4_import.py`，退出状态 **0**：

```text
CODE_OK files=68 migrated=5 unchanged=63 missing=0 extra=0
GUIDE_OK pages=16 assets=20 failed=0 text=identical codeblocks=9 tables=1 images=1
REQUIREMENTS_OK modules=3 functions=12 challenge=2 report_items=7
```

另逐字节确认原始分配器测试、Lab4 function1 区域之后的原有代码、进程 / 调度源码和官方测试工具没有变化。

### 2. 真实构建边界

迁移前的 `make` 返回 **2**，停在 Lab3 `interrupt_handler` / `exception_handler` 未声明。

迁移后的 `make` 仍返回 **2**，但全部 C / 汇编对象文件已成功生成，链接错误仅来自 Lab4 尚待填写的 `page_insert`、`page_remove`、`proc_init`、`cpu_idle`。没有添加空实现、绕过真实启动流程或伪造整项目构建成功。

### 3. 可独立运行的前置专项测试

使用现有 GCC 15.1.0、QEMU 4.1.1、默认 OpenSBI。可复用命令（先将现有交叉工具链加入当前进程 PATH）：

```sh
python3 tools/test_lab23_prereqs.py --output-dir /tmp/lab4-prereq-evidence
```

测试工具只在临时源码副本中设置专项入口和静态函数包装；它不修改真实 `code/`，也不依赖未完成的 Lab4 页映射 / 进程函数。真实项目中的原始启动、页表测试和评分入口仍完整保留。

三个 QEMU 内存配置 **64M、128M、256M** 全部退出 **0** 并通过：

- DTB 内存范围、Page 元数据预留和 Lab4 映射上限检查。
- 原有 Best-Fit 框架测试，包括分裂、选择和回收 / 合并。
- 已有 Sv39 页表页分配 / 查找及回收前后空闲页计数一致性。
- 现有 VMA 结构测试。
- 非法指令 16 / 32 位、断点 16 / 32 位，共 4 类异常均能返回继续执行。
- 至少 1100 次时钟中断，确认续订 / 计数正常且没有继承 Lab3 的自动关机行为。

结果末行：

```text
PREREQ_OK allocator=pass page_init=pass sv39=pass traps=4/4 timer=1100 memory=64M,128M,256M lab4_implemented=0
```

原始测试输出见 [`evidence/prereqs/`](evidence/prereqs/)。完整 Lab4 的 `make qemu` / `make grade` 需在新增函数实现后再验证；专项测试通过不等同于整个 Lab4 通过。

## 对后续分工的影响

- 本次迁移作为一次性共享前置工作，后续 A / C 不再把 Lab2 / Lab3 代码复制单独算成一个新功能模块。
- 工作量应按 Lab4 新增逻辑、失败清理、首次上下文恢复和集成调试衡量，不按函数数量机械均分，也不据此前置工作声称三人已经均衡。
- 若继续按 A 页映射、B 创建初始化、C 调度分工，应让 A / C 分担 B 的低内存失败路径测试和首次切换联调，重点照顾创建与初始化模块的资源管理复杂度。
