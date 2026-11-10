#!/usr/bin/env python3
"""Build/run migrated Lab2/3 prerequisites, without implementing Lab4.

Only a disposable copy gets a test entry and a static-function test wrapper.
The real Lab4 entry, page tests and unfinished process functions stay intact.
Requires the existing RISC-V toolchain and QEMU on PATH; standard library only.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PMM_WRAPPER = r'''
/* Test-copy-only wrapper: do not bypass any tests in the real Lab4 tree. */
void lab23_prereq_pmm_check(void)
{
    init_pmm_manager();
    page_init();
    check_alloc_page();
    assert(npage * PGSIZE <= KERNTOP - PHYSICAL_MEMORY_OFFSET);
    assert(npage * PGSIZE <= get_memory_base() + get_memory_size());
    assert(nr_free_pages() > 0);
    cprintf("[LAB23] page_init and Best-Fit framework tests PASS\n");

    size_t before = nr_free_pages();
    struct Page *root = alloc_page();
    assert(root != NULL);
    pde_t *pgdir = page2kva(root);
    memset(pgdir, 0, PGSIZE);
    uintptr_t la = 0x400000;
    assert(get_pte(pgdir, la, 0) == NULL);
    pte_t *pte = get_pte(pgdir, la, 1);
    assert(pte != NULL && *pte == 0);
    assert(get_pte(pgdir, la, 0) == pte);
    assert(nr_free_pages() == before - 3);
    pde_t *middle = KADDR(PDE_ADDR(pgdir[PDX1(la)]));
    free_page(pde2page(middle[PDX0(la)]));
    free_page(pde2page(pgdir[PDX1(la)]));
    free_page(root);
    assert(nr_free_pages() == before);
    cprintf("[LAB23] inherited Sv39 page-table allocation PASS\n");
    kmalloc_init();
}
'''

TEST_ENTRY = r'''
#include <defs.h>
#include <stdio.h>
#include <string.h>
#include <console.h>
#include <pmm.h>
#include <vmm.h>
#include <trap.h>
#include <picirq.h>
#include <clock.h>
#include <intr.h>
#include <dtb.h>
#include <sbi.h>

void lab23_prereq_pmm_check(void);
int kern_init(void) __attribute__((noreturn));
int kern_init(void)
{
    extern char edata[], end[];
    memset(edata, 0, end - edata);
    dtb_init();
    cons_init();
    lab23_prereq_pmm_check();
    vmm_init();
    pic_init();
    idt_init();

    asm volatile(".4byte 0x0000000b" ::: "memory");
    cprintf("[LAB23] illegal32 resume PASS\n");
    asm volatile(".2byte 0x0000" ::: "memory");
    cprintf("[LAB23] illegal16 resume PASS\n");
    asm volatile(".4byte 0x00100073" ::: "memory");
    cprintf("[LAB23] breakpoint32 resume PASS\n");
    asm volatile(".2byte 0x9002" ::: "memory");
    cprintf("[LAB23] breakpoint16 resume PASS\n");

    clock_init();
    intr_enable();
    while (ticks < 1100) {
        asm volatile("wfi");
    }
    intr_disable();
    cprintf("[LAB23] timer >=1100 without Lab3 auto-shutdown PASS\n");
    cprintf("LAB23_PREREQ_SMOKE_PASS\n");
    sbi_shutdown();
    for (;;) { asm volatile("wfi"); }
}
'''


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and p.relative_to(root).parts[0] not in ("obj", "bin", "build")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-dir", type=Path, default=ROOT / "code")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    code = args.code_dir.resolve()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    original = hashes(code)
    with tempfile.TemporaryDirectory(prefix="lab4-prereq-") as tmp:
        target = Path(tmp) / "code"
        shutil.copytree(code, target, ignore=shutil.ignore_patterns("obj", "bin", "build"))
        with (target / "kern/mm/pmm.c").open("a", encoding="utf-8", newline="\n") as f:
            f.write(PMM_WRAPPER)
        (target / "kern/init/init.c").write_text(TEST_ENTRY, encoding="utf-8")
        build = subprocess.run(["make"], cwd=target, capture_output=True)
        (out / "smoke-build.txt").write_bytes(build.stdout + build.stderr)
        if build.returncode:
            print(f"PREREQ_BUILD_FAILED make_exit={build.returncode}")
            raise SystemExit(build.returncode)

        def run(memory):
            command = [os.environ.get("QEMU", "qemu-system-riscv64"), "-machine", "virt", "-m", memory,
                       "-nographic", "-bios", "default", "-device", f"loader,file={target/'bin/ucore.img'},addr=0x80200000"]
            try:
                run = subprocess.run(command, cwd=target, capture_output=True, timeout=45)
                data = run.stdout + run.stderr
                (out / f"qemu-{memory}.txt").write_bytes(data)
                markers = [b"page_init and Best-Fit framework tests PASS", b"inherited Sv39 page-table allocation PASS",
                           b"check_vma_struct() succeeded!", b"illegal32 resume PASS", b"illegal16 resume PASS",
                           b"breakpoint32 resume PASS", b"breakpoint16 resume PASS",
                           b"timer >=1100 without Lab3 auto-shutdown PASS", b"LAB23_PREREQ_SMOKE_PASS"]
                passed = run.returncode == 0 and all(x in data for x in markers) and b"kernel panic" not in data
                return {"memory": memory, "qemu_exit": run.returncode, "pass": passed, "command": command}
            except subprocess.TimeoutExpired as exc:
                (out / f"qemu-{memory}.txt").write_bytes((exc.stdout or b"") + (exc.stderr or b""))
                return {"memory": memory, "qemu_exit": 124, "pass": False, "command": command}

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(run, ["64M", "128M", "256M"]))
        (out / "smoke-results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        assert hashes(code) == original, "The source tree changed during smoke testing"
        for result in results:
            print(f"QEMU memory={result['memory']} exit={result['qemu_exit']} pass={str(result['pass']).lower()}")
        if not all(r["pass"] for r in results):
            raise SystemExit(1)
        print("PREREQ_OK allocator=pass page_init=pass sv39=pass traps=4/4 timer=1100 memory=64M,128M,256M lab4_implemented=0")


if __name__ == "__main__":
    main()
