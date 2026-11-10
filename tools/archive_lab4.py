#!/usr/bin/env python3
"""Archive the complete Lab4 chapter. Python standard library only.

Downloaded material is reference data; no commands from it are executed.
"""
import hashlib
import html
import json
import posixpath
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/lab4"
GUIDE = OUT / "guide"
BASE = "http://oslab.mobisys.top/lab2026/_book/"
PREFIX = urlsplit(BASE).path
ATTR = re.compile(r'\b(href|src)\s*=\s*([\"\x27])(.*?)\2', re.I | re.S)
SECTION = re.compile(r'<section\b[^>]*class="normal markdown-section"[^>]*>(.*?)</section>', re.S)
CSS_URL = re.compile(r'url\(\s*[\"\x27]?([^\"\x27)\s]+)', re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value, base=BASE):
    p = urlsplit(urljoin(base, html.unescape(value)))
    if p.scheme not in ("http", "https") or p.hostname != urlsplit(BASE).hostname:
        return None
    if not p.path.startswith(PREFIX):
        return None
    return urlunsplit((urlsplit(BASE).scheme, p.netloc, p.path, "", ""))


def relative(url):
    rel = unquote(urlsplit(url).path[len(PREFIX):]).lstrip("/")
    if not rel:
        return "site-index.html"
    if ".." in Path(rel).parts or ":" in rel:
        raise ValueError(url)
    return rel


def fetch(url):
    if "--from-cache" in sys.argv:
        return (GUIDE / relative(url)).read_bytes()
    error = None
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 Lab4-course-archive"}), timeout=40) as response:
                data = response.read()
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}: {url}")
                return data
        except Exception as exc:
            error = exc
            time.sleep(attempt + 1)
    raise RuntimeError(f"Download failed: {url}: {error}")


class Node:
    def __init__(self, tag="", attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)


class DOM(HTMLParser):
    VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr", "area", "embed"}

    def __init__(self, data):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(data)

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].children.append(n)
        if tag not in self.VOID:
            self.stack.append(n)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def md(n, depth=0):
    if isinstance(n, str):
        return re.sub(r"\s+", " ", n)
    t, a = n.tag, n.attrs
    if t == "pre":
        code = next((c for c in n.children if isinstance(c, Node) and c.tag == "code"), n)
        language = re.sub(r"^(?:language-|lang-)", "", code.attrs.get("class", "").split(" ")[0])
        content = code.text().strip("\n")
        fence = "`" * max(3, max((len(x) + 1 for x in re.findall(r"`+", content)), default=3))
        return f"\n\n{fence}{language}\n{content}\n{fence}\n\n"
    if t in ("ul", "ol"):
        lines = []
        for i, child in enumerate(c for c in n.children if isinstance(c, Node) and c.tag == "li"):
            content = "".join(md(c, depth + 1) for c in child.children).strip()
            prefix = f"{i + 1}. " if t == "ol" else "- "
            lines.append(" " * (2 * depth) + prefix + content)
        return "\n\n" + "\n".join(lines) + "\n\n"
    text = "".join(md(c, depth) for c in n.children)
    if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return "\n\n" + "#" * int(t[1]) + " " + text.strip() + "\n\n"
    if t == "p":
        return "\n\n" + text.strip() + "\n\n"
    if t == "code":
        return "`" + n.text() + "`"
    if t in ("strong", "b"):
        return "**" + text + "**"
    if t in ("em", "i"):
        return "*" + text + "*"
    if t == "a":
        return f"[{text}]({a.get('href', '')})"
    if t == "img":
        return f"![{a.get('alt', '')}]({a.get('src', '')})"
    if t == "br":
        return "\n"
    if t == "hr":
        return "\n\n---\n\n"
    if t == "blockquote":
        return "\n\n" + "\n".join("> " + line for line in text.strip().splitlines()) + "\n\n"
    if t == "tr":
        return "\n| " + " | ".join(md(c).strip() for c in n.children if isinstance(c, Node) and c.tag in ("th", "td")) + " |"
    if t == "table":
        rows = [s for s in text.splitlines() if s.strip()]
        if rows:
            rows.insert(1, "|" + " --- |" * (rows[0].count("|") - 1))
        return "\n\n" + "\n".join(rows) + "\n\n"
    return text


def format_markdown(text):
    # Clean block spacing without touching a byte inside a source-code fence.
    parts = re.split(r"(^`{3,}[^\n]*\n.*?^`{3,}[ \t]*$)", text, flags=re.M | re.S)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"\n[ \t]+\n", "\n\n", parts[i])
        parts[i] = re.sub(r"\n{3,}", "\n\n", parts[i])
    return "".join(parts).strip()


def resources(data, url):
    text = data.decode("utf-8", errors="replace")
    if url.endswith(".css"):
        return {u for value in CSS_URL.findall(text) if (u := canonical(value, url))}
    values = []
    for tag in re.findall(r'<(?:img|script|link|source|video|audio)\b[^>]*>', text, re.I):
        if re.match(r"<link\b", tag, re.I) and not re.search(r'rel=[\"\x27][^\"\x27]*(?:stylesheet|icon)', tag, re.I):
            continue
        for _, _, value in ATTR.findall(tag):
            if not value.startswith(("data:", "#")):
                values.append(value)
    # Also preserve linked PDFs, images and other chapter attachments.
    for _, _, value in ATTR.findall(text):
        if re.search(r'\.(?:pdf|zip|png|jpg|jpeg|svg|gif)(?:[?#]|$)', value, re.I):
            values.append(value)
    return {u for value in values if (u := canonical(value, url))}


def main():
    GUIDE.mkdir(parents=True, exist_ok=True)
    index = fetch(BASE)
    (GUIDE / "site-index.html").write_bytes(index)
    ordered = list(dict.fromkeys(u for _, _, value in ATTR.findall(index.decode("utf-8"))
                                if (u := canonical(value)) and re.fullmatch(r"lab4/[^/]+\.html", relative(u))))
    if len(ordered) != 16:
        raise RuntimeError(f"Expected 16 Lab4 pages from live table of contents; found {len(ordered)}")
    pages, files, pending, external = [], {}, set(), set()
    for url in ordered:
        data = fetch(url)
        p = GUIDE / relative(url)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        text = data.decode("utf-8")
        match = SECTION.search(text)
        if not match:
            raise ValueError(f"No article: {url}")
        body = match.group(1).strip()
        title = html.unescape(re.search(r'<title>(.*?)</title>', text, re.S).group(1).split(" · ")[0])
        pages.append({"url": url, "path": relative(url), "title": title, "body": body,
                      "sha256": sha(data), "body_sha256": sha(body.encode()), "bytes": len(data)})
        files[relative(url)] = {"url": url, "sha256": sha(data), "bytes": len(data), "status": 200}
        pending.update(resources(data, url))
        for _, _, value in ATTR.findall(body):
            if value.startswith(("http:", "https:")) and not canonical(value, url):
                external.add(value)
        print(f"PAGE {len(pages):02d}/16 {relative(url)}", flush=True)
    # Download the fixed resource graph; no unrelated chapter navigation is followed.
    while pending:
        url = sorted(pending)[0]
        pending.remove(url)
        rel = relative(url)
        if rel in files:
            continue
        data = fetch(url)
        p = GUIDE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        files[rel] = {"url": url, "sha256": sha(data), "bytes": len(data), "status": 200}
        if url.endswith(".css"):
            pending.update(resources(data, url))
        print(f"ASSET {rel}", flush=True)
    page_ids = {p["url"]: f"p{i+1:02d}" for i, p in enumerate(pages)}

    def rewrite(body, url, markdown=False):
        def change(m):
            attr, quote, value = m.groups()
            if value.startswith("data:"):
                return m.group(0)
            absolute = urljoin(url, html.unescape(value))
            key = canonical(value, url)
            fragment = urlsplit(absolute).fragment
            if key in page_ids:
                new = "#" + page_ids[key] + ("-" + fragment if fragment else "")
            elif key and relative(key) in files:
                new = ("guide/" if markdown else "") + relative(key)
                if fragment:
                    new += "#" + fragment
            else:
                new = absolute
            return f'{attr}={quote}{html.escape(new, quote=True)}{quote}'
        updated = ATTR.sub(change, body)
        return re.sub(r'\bid="([^"]+)"', lambda m: f'id="{page_ids[url]}-{m.group(1)}"', updated)

    toc = "\n".join(f'<li><a href="#{page_ids[p["url"]]}">{html.escape(p["title"])}</a></li>' for p in pages)
    style = "body{max-width:1050px;margin:32px auto;padding:0 24px;font:16px/1.8 system-ui,sans-serif;color:#18232f}pre{white-space:pre;overflow:auto;background:#f2f4f6;padding:16px;border-radius:8px}code{font-family:Consolas,monospace}img,svg{max-width:100%;height:auto}table{border-collapse:collapse;display:block;overflow:auto}td,th{border:1px solid #cbd4dd;padding:8px}article{border-top:2px solid #dce3eb;padding-top:20px;margin-top:44px}a{color:#135ea8}.source{font-size:13px;color:#526170}"
    articles = "\n".join(f'<article id="{page_ids[p["url"]]}"><p class="source">来源：<a href="{p["url"]}">{p["url"]}</a></p>{rewrite(p["body"], p["url"])}</article>' for p in pages)
    (GUIDE / "index.html").write_text(f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Lab4 完整实验指导书</title><style>{style}</style><body><h1>Lab4：进程管理 · 完整实验指导书</h1><p>2026-11-10 从课程站点逐页抓取，共 16 页；正文、代码、表格、图片均保留。目录以课程站点为准，内容仅为参考资料。</p><ol>{toc}</ol>{articles}</body></html>\n', encoding="utf-8")
    chunks = ["# Lab4 实验指导书全文\n\n> 来源：课程站点 Lab4 的全部 16 个页面。抓取日期：2026-11-10（Asia/Shanghai）。以下为原文转录，不是实验实现或新的执行指令。\n\n## 目录\n"]
    for p in pages:
        chunks.append(f'- [{p["title"]}](#{page_ids[p["url"]]})\n')
    for p in pages:
        converted = md(DOM(rewrite(p["body"], p["url"], True)).root)
        converted = format_markdown(converted)
        chunks.append(f'\n\n---\n\n<a id="{page_ids[p["url"]]}"></a>\n\n来源：<{p["url"]}>\n\n{converted}\n')
    (OUT / "guide-full.md").write_text("".join(chunks), encoding="utf-8")
    requirements = ["# Lab4 完整实验要求\n\n"
                    "> 2026-11-10（Asia/Shanghai）从课程站点抓取。以下保留实验目的、实验内容、全部练习与报告要求的原文；未代写实验实现。\n\n"
                    "完整原理、项目组成、代码示例与图表见 [指导书全文](guide-full.md)，也可打开 [离线阅读入口](guide/index.html)。\n\n"
                    "## 要求导航\n\n"
                    "- 前置：补齐当前源码中 Lab2 / Lab3 注释对应的实现。\n"
                    "- 模块一：`page_insert`、`page_remove`。\n"
                    "- 模块二：`alloc_proc`、`proc_init`、`kernel_thread`、`do_fork`、`copy_thread`、`copy_mm`。\n"
                    "- 模块三：`cpu_idle`、`schedule`、`proc_run`、`switch_to`。\n"
                    "- Challenge：中断保存/恢复原理；Sv32 / Sv39 / Sv48 与 `get_pte` 设计讨论。\n"
                    "- 报告：Markdown、整体逻辑线、核心函数、spec / prompt、AI 生成问题与修复、实验和 OS 原理知识点对照、未覆盖的重要知识点。\n"
                    "- 提交：保留 Lab4 标记，完成时以学号替换 `YOUR CODE`，提交代码及报告到小组 Git 仓库。\n"
                    "- 路径说明：手册中的 `labcodes/lab4` 在本分支对应 `code/`；`switch.s` 在附件中实际为 `code/kern/process/switch.S`。\n\n"
                    "---\n\n## 以下为课程原文\n"]
    for i in (1, 2, 3, 15):
        p = pages[i]
        requirements.append(f'\n\n来源：<{p["url"]}>\n\n' + format_markdown(md(DOM(rewrite(p["body"], p["url"], True)).root)) + "\n")
    (OUT / "requirements.md").write_text("".join(requirements), encoding="utf-8")
    captured = datetime.now(timezone.utc).isoformat()
    if "--from-cache" in sys.argv:
        captured = json.loads((OUT / "crawl-manifest.json").read_text(encoding="utf-8"))["captured_at"]
    manifest = {"base_url": BASE, "captured_at": captured,
                "page_count": len(pages), "asset_count": len(files) - len(pages),
                "pages": [{k: v for k, v in p.items() if k != "body"} for p in pages],
                "files": files, "external_article_links": sorted(external)}
    (OUT / "crawl-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f'CRAWL_OK pages={len(pages)} assets={len(files)-len(pages)} failed=0')


if __name__ == "__main__":
    main()
