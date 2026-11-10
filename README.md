# 操作系统 Lab4：进程管理

本分支 `lab4` 从 `main` 的 `9e725207f870e1ed2faba0ab0d9399f9f7747b56` 创建，不继承 Lab3 的实验实现。分支只保留本次实验的代码与资料；历史 Lab1 材料仍保留在 `main`。

## 阅读入口

- [Lab4 完整实验要求](docs/lab4/requirements.md)：前置任务、3 个功能模块 / 12 个函数、Challenge、报告与提交要求，附课程原文。
- [指导书全文](docs/lab4/guide-full.md)：全部 16 个页面的正文、代码示例、表格与图片。
- [离线 HTML 指导书](docs/lab4/guide/index.html)：下载后直接用浏览器打开，支持目录跳转和本地图片。
- [资料来源、校验与构建状态](docs/lab4/README.md)。

## 代码状态

`code/` 原样来自用户提供的 `lab4.zip` 内 `lab4_new/`，68 个文件逐字节一致；没有填充 Lab2 / Lab3 / Lab4 待实现部分，也没有使用旧实验代码替换它。

源码自带 `Makefile`、`tools/grade.sh`、`tools/inject.py`、`tools/test_lab4.c`。本次任务仅初始化分支和完整归档要求，并非完成实验。

使用已有 RISC-V 工具链，在 `code/` 下运行 `make`；后续完成实现后再运行 `make qemu`、`make grade`。当前原始附件与导入版本的 `make` 均返回 2，首先在 `kern/trap/trap.c:102,107` 报 `interrupt_handler` / `exception_handler` 未声明，见资料说明。

## 复核与更新资料

在分支根目录运行（Python 3，仅标准库）：

```sh
python tools/verify_lab4_import.py
python tools/archive_lab4.py
```

第一条检查当前代码是否仍与起始 ZIP 完全一致，并核对指导书内容和资源；开始填写实验后，源码一致性检查报告差异是预期行为。第二条会重新抓取课程站点；仅从已保存页面重新生成阅读版时使用 `python tools/archive_lab4.py --from-cache`。

实验实现完成后按 `AGENTS.md` 整理 `report/report.md`、`report/prompt.md` 和图片；本次未生成虚构的完成报告。
