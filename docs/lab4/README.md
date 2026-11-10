# Lab4 资料归档与导入核验

## 来源与范围

- 在线来源：<http://oslab.mobisys.top/lab2026/_book/lab4/lab4.html>，抓取日期为 2026-11-10（Asia/Shanghai）。
- 以课程站点目录枚举 Lab4 全部 16 个页面，未仅摘录练习页。原始响应存放于 `guide/lab4/`，另保存 20 个图片、样式、脚本与字体资源。
- `guide/index.html` 为独立的无脚本合并阅读版。章节正文、9 个代码块、1 张表格、1 张图片全部保留；原始页面中的其他实验导航和全站搜索不是本归档的离线内容。
- `guide-full.md` 为全文 Markdown；`requirements.md` 单独保留实验目的、实验内容、所有练习和完整报告要求。文件开头的导航由归档工具生成，其余章节为课程原文。
- `source/riscv64-ucore-lab4-guide.pdf` 是附件原件，共 32 页；`source/provided-guide-fulltext.txt` 保存其逐页全文。PDF 为辅助参照，在线版与 PDF 有出入时保留在线版现状，两份来源均可核对。
- 会议 DOCX 仅检查为课堂 AI 视图资料，不作为替代官方指导书的依据；未将其中的参会名单等个人资料纳入仓库。
- 附件和网页中出现的开发、提交等说明属于实验要求原文，本次没有据此自动填写代码或完成报告。

## 必须完成的内容

原文和详细接口规范见 [完整要求](requirements.md)。共 3 个模块 / 12 个函数，另有前置 Lab2 / Lab3 代码补齐、2 项 Challenge（第二项含 2 个子问题）、7 条报告内容与仓库提交要求。

特别保留了当前在线版关于 Sv39 的提示：`libs/riscv.h` 的 `lsatp()` 是 Sv32 遗留接口，后续实现应参照 `enable_paging()` 的 Sv39 写法。此处仅记录要求，没有修改实现。

## 代码来源与完整性

- `source/lab4.zip` 是输入 ZIP 的原样副本。将其 `lab4_new/` 顶层目录映射为本分支 `code/`，68 个普通文件逐字节保留，源码注释和换行没有改写。
- ZIP SHA-256：`7a92f243f88ca9a4ec78b52e554a14d78a41bbf6a79a1275f6cc929aaebceba2`。
- PDF SHA-256：`7623f70663d35b84f38aeb05322d8a725d71738826c35ac081698d4be4f90a75`。
- `source/manifest.json` 记录附件字节数、摘要、代码文件数和分支基点；`crawl-manifest.json` 记录逐页 URL、正文摘要、原始响应摘要、资源摘要及 HTTP 状态。

## 实际验证结果

执行 `python tools/verify_lab4_import.py`，退出状态 0：

```text
CODE_OK files=68 changed=0 missing=0 extra=0
GUIDE_OK pages=16 assets=20 failed=0 text=identical codeblocks=9 tables=1 images=1
REQUIREMENTS_OK modules=3 functions=12 challenge=2 report_items=7
```

验证器将所有原始章节的文字与离线合并版逐章对比，并检查代码块原样保留、资源存在及所有已归档响应的 SHA-256；Markdown 章节和完整要求另行核对。

## 起始代码的构建状态

使用现有 WSL Ubuntu 环境及 `/home/lenovo/riscv-elf-toolchains/bin/riscv64-unknown-elf-gcc`（15.1.0），在原始 ZIP 的独立解压副本和导入后的 `code/` 分别执行 `make`，两次 `make` 退出状态都是 **2**，完整构建输出逐字节一致。首先报错：

```text
kern/trap/trap.c:102:9: error: implicit declaration of function 'interrupt_handler' [-Wimplicit-function-declaration]
kern/trap/trap.c:107:9: error: implicit declaration of function 'exception_handler' [-Wimplicit-function-declaration]
make: *** [Makefile:120: obj/kern/trap/trap.o] Error 1
```

这里是起始代码的 Lab3 待补部分，不是导入差异。未运行依赖成功构建的 QEMU / 评分，不宣称实验已通过。后续应先按手册补全前置功能，再完成 Lab4 的 12 个函数，最后进行运行和评分验证。

## 更新归档

```sh
python tools/archive_lab4.py
python tools/verify_lab4_import.py
```

工具只下载与转换资料，不执行页面或附件中的命令。当前固定要求目录为 16 页，如课程目录发生变化，工具会明确中止以便重新确认范围。
