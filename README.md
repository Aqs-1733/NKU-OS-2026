# 操作系统 Lab4：进程管理

本分支 `lab4` 从 `main` 的 `9e725207f870e1ed2faba0ab0d9399f9f7747b56` 创建，不继承 Lab3 的实验实现。分支只保留本次实验的代码与资料；历史 Lab1 材料仍保留在 `main`。

## 阅读入口

- [Lab4 完整实验要求](docs/lab4/requirements.md)：前置任务、3 个功能模块 / 12 个函数、Challenge、报告与提交要求，附课程原文。
- [指导书全文](docs/lab4/guide-full.md)：全部 16 个页面的正文、代码示例、表格与图片。
- [离线 HTML 指导书](docs/lab4/guide/index.html)：下载后直接用浏览器打开，支持目录跳转和本地图片。
- [资料来源、校验与构建状态](docs/lab4/README.md)。
- [Lab2 / Lab3 前置迁移与实测](docs/lab4/prerequisite-migration.md)。

## 代码状态

`code/` 以用户提供的 `lab4.zip` 内 `lab4_new/` 为基底，68 个文件中 63 个仍与附件逐字节一致，5 个完成 Lab2 / Lab3 前置迁移及必要接口适配。起始 ZIP 原件仍保留于 `docs/lab4/source/`；Lab4 新增的 12 个函数尚未填写。

源码自带 `Makefile`、`tools/grade.sh`、`tools/inject.py`、`tools/test_lab4.c`，原有框架测试保持原样。当前阶段完成分支初始化、要求归档和前置迁移，并非完成 Lab4。

使用已有 RISC-V 工具链，在 `code/` 下运行 `make`；后续完成实现后再运行 `make qemu`、`make grade`。迁移后全部源码可编译为对象文件，整项目 `make` 仍返回 2，链接阶段仅报告尚未实现的 Lab4 函数 `page_insert`、`page_remove`、`proc_init`、`cpu_idle`。独立前置测试内核已在 QEMU 的 64M / 128M / 256M 配置下通过，见迁移记录。

## 复核与更新资料

在分支根目录运行（Python 3，仅标准库）：

```sh
python tools/verify_lab4_import.py
python tools/archive_lab4.py
```

第一条按迁移清单检查 5 个已适配文件的摘要，并逐字节核对其余 63 个附件文件，同时核对指导书内容和资源。`--starter-only` 用于显式比较未迁移的 ZIP 基线。第二条会重新抓取课程站点；仅从已保存页面重新生成阅读版时使用 `python tools/archive_lab4.py --from-cache`。

在已有 RISC-V 工具链与 QEMU 的 Linux / WSL 环境中，执行前置专项测试（不修改真实 `code/`）：

```sh
python3 tools/test_lab23_prereqs.py --output-dir /tmp/lab4-prereq-evidence
```

实验实现完成后按 `AGENTS.md` 整理 `report/report.md`、`report/prompt.md` 和图片；本次未生成虚构的完成报告。
