#!/usr/bin/env python3
"""Verify exact starter bytes and the complete offline course capture."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

from archive_lab4 import DOM, Node, SECTION, ATTR

ROOT = Path(__file__).resolve().parents[1]


def walk(n):
    if isinstance(n, Node):
        yield n
        for child in n.children:
            yield from walk(child)


def compact(text):
    return re.sub(r"\s+", "", text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--code-dir", type=Path, default=ROOT / "code")
    p.add_argument("--code-only", action="store_true")
    p.add_argument("--starter-only", action="store_true", help="Compare against ZIP only, before prerequisite migration")
    args = p.parse_args()
    source = ROOT / "docs/lab4/source"
    with zipfile.ZipFile(source / "lab4.zip") as z:
        expected = {str(Path(i.filename).relative_to("lab4_new")).replace("\\", "/"): z.read(i)
                    for i in z.infolist() if not i.is_dir()}
    actual = {f.relative_to(args.code_dir).as_posix(): f.read_bytes() for f in args.code_dir.rglob("*")
              if f.is_file() and f.relative_to(args.code_dir).parts[0] not in ("bin", "obj", "build")}
    migrated = 0
    migration_file = source / "migration-manifest.json"
    if migration_file.exists() and not args.starter_only:
        migration = json.loads(migration_file.read_text(encoding="utf-8"))
        for rel, item in migration["code_changes"].items():
            assert hashlib.sha256(expected[rel]).hexdigest() == item["starter_sha256"], (rel, "starter hash")
            assert rel in actual and hashlib.sha256(actual[rel]).hexdigest() == item["migrated_sha256"], (rel, "migration hash")
            expected[rel] = actual[rel]
            migrated += 1
    missing, extra = set(expected) - set(actual), set(actual) - set(expected)
    changed = {k for k in expected.keys() & actual.keys() if expected[k] != actual[k]}
    assert not (missing or extra or changed), (sorted(missing), sorted(extra), sorted(changed))
    if migrated:
        print(f"CODE_OK files={len(expected)} migrated={migrated} unchanged={len(expected)-migrated} missing=0 extra=0")
    else:
        print(f"CODE_OK files={len(expected)} changed=0 missing=0 extra=0")
    if args.code_only:
        return
    for name, item in json.loads((source / "manifest.json").read_text(encoding="utf-8")).items():
        if isinstance(item, dict):
            data = (source / name).read_bytes()
            assert len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"], name
    docs = ROOT / "docs/lab4"
    guide = docs / "guide"
    m = json.loads((docs / "crawl-manifest.json").read_text(encoding="utf-8"))
    assert m["page_count"] == 16 and len(m["pages"]) == 16
    for rel, item in m["files"].items():
        data = (guide / rel).read_bytes()
        assert item["status"] == 200 and len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"], rel
    combined = (guide / "index.html").read_text(encoding="utf-8")
    articles = [n for n in walk(DOM(combined).root) if n.tag == "article"]
    assert len(articles) == 16
    markdown = (docs / "guide-full.md").read_text(encoding="utf-8")
    codeblocks = tables = images = 0
    for page, article in zip(m["pages"], articles):
        raw = (guide / page["path"]).read_text(encoding="utf-8")
        body = SECTION.search(raw).group(1).strip()
        assert hashlib.sha256(body.encode()).hexdigest() == page["body_sha256"]
        original = DOM(body).root
        # The first paragraph is generated source attribution, not course text.
        actual_body = Node()
        actual_body.children = article.children[1:]
        assert compact(original.text()) == compact(actual_body.text()), page["path"]
        assert page["url"] in markdown
        for n in walk(original):
            if n.tag == "pre":
                assert n.text().strip("\n") in markdown, (page["path"], "code block lost")
                codeblocks += 1
            if n.tag == "table":
                tables += 1
            if n.tag == "img":
                images += 1
        for _, _, value in ATTR.findall(body):
            if value.startswith("data:"):
                continue
            if re.search(r"\.(png|jpg|jpeg|gif|svg)(?:[?#]|$)", value, re.I):
                assert unquote(urlsplit(value).path).split("/")[-1] in combined
    for _, _, value in ATTR.findall(combined):
        u = urlsplit(value)
        if u.scheme or value.startswith("#"):
            continue
        assert (guide / unquote(u.path)).is_file(), value
    requirements = (docs / "requirements.md").read_text(encoding="utf-8")
    for token in ["page_insert", "page_remove", "alloc_proc", "proc_init", "kernel_thread", "do_fork",
                  "copy_thread", "copy_mm", "cpu_idle", "schedule", "proc_run", "switch_to",
                  "Challenge", "Sv39", "spec", "prompt", "YOUR CODE"]:
        assert token in requirements, token
    print(f"GUIDE_OK pages=16 assets={m['asset_count']} failed=0 text=identical codeblocks={codeblocks} tables={tables} images={images}")
    print("REQUIREMENTS_OK modules=3 functions=12 challenge=2 report_items=7")


if __name__ == "__main__":
    main()
