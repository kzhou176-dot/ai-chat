#!/usr/bin/env python3
"""
aichat-hub arxiv 工具
=====================
简化版 arxiv 下载器,针对 aichat-hub 目录结构。
复用 v6-loop/arxiv-corpus 的 pipeline.py 经验。

Usage:
  python3 arxiv_tool.py search --query "large language model" --max 10
  python3 arxiv_tool.py download --query "instruction tuning" --max 5 --keyword instruction_tuning
  python3 arxiv_tool.py count                    # 统计各 keyword 已有论文数
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

ROOT = Path("/Users/yuefeng/.mavis/agents/mavis/workspace/aichat-hub")
PAPERS = ROOT / "papers"
PDFS = ROOT / "papers" / "pdfs"
PARSED = ROOT / "papers" / "parsed"

for p in (PAPERS, PDFS, PARSED):
    p.mkdir(parents=True, exist_ok=True)

ARXIV_API = "http://export.arxiv.org/api/query"
ARXIV_PDF = "https://arxiv.org/pdf/"
ARXIV_ABS = "https://arxiv.org/abs/"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def arxiv_search(query: str, max_results: int = 10) -> List[Dict]:
    """Return list of {arxiv_id, title, authors, abstract, ...}"""
    if any(tok in query for tok in ["abs:", "ti:", "au:", "AND", "OR"]):
        q = urllib.parse.quote(query)
    else:
        q = urllib.parse.quote(f'all:"{query}"')
    url = (
        f"{ARXIV_API}?search_query={q}"
        f"&max_results={max_results}"
        f"&sortBy=submittedDate&sortOrder=descending"
    )
    log(f"GET arxiv: {query[:60]}")
    out = subprocess.run(
        ["curl", "-sL", "--max-time", "20", url],
        capture_output=True, text=True
    )
    if out.returncode != 0 or not out.stdout.strip():
        return []
    try:
        root = ET.fromstring(out.stdout)
    except ET.ParseError:
        return []
    results = []
    for entry in root.findall("atom:entry", NS):
        eid = entry.findtext("atom:id", default="", namespaces=NS).strip()
        m = re.search(r"arxiv\.org/abs/([0-9]+\.[0-9]+)", eid)
        if not m:
            continue
        arxiv_id = m.group(1)
        title = re.sub(r"\s+", " ", entry.findtext("atom:title", default="", namespaces=NS).strip())
        abstract = re.sub(r"\s+", " ", entry.findtext("atom:summary", default="", namespaces=NS).strip())
        authors = [
            a.findtext("atom:name", default="", namespaces=NS).strip()
            for a in entry.findall("atom:author", NS)
        ]
        published = entry.findtext("atom:published", default="", namespaces=NS).strip()
        cats = [c.attrib.get("term", "") for c in entry.findall("atom:category", NS)]
        results.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "published": published,
            "categories": cats,
            "abs_url": f"{ARXIV_ABS}{arxiv_id}",
            "pdf_url": f"{ARXIV_PDF}{arxiv_id}",
        })
    log(f"  -> {len(results)} results")
    return results


def download_pdf(arxiv_id: str, timeout: int = 60) -> Optional[Path]:
    target = PDFS / f"{arxiv_id}.pdf"
    if target.exists() and target.stat().st_size > 1000:
        return target
    url = f"{ARXIV_PDF}{arxiv_id}"
    log(f"  PDF {arxiv_id}")
    out = subprocess.run(
        ["curl", "-sL", "--max-time", str(timeout), "-o", str(target), url],
        capture_output=True, text=True
    )
    if out.returncode == 0 and target.exists() and target.stat().st_size > 1000:
        return target
    if target.exists():
        target.unlink()
    return None


def parse_pdf(arxiv_id: str) -> Optional[str]:
    pdf = PDFS / f"{arxiv_id}.pdf"
    out = PARSED / f"{arxiv_id}.txt"
    if not pdf.exists():
        return None
    if out.exists() and out.stat().st_size > 100:
        return out.read_text()
    text = ""
    try:
        import fitz
        doc = fitz.open(str(pdf))
        text = "\n\n".join(page.get_text() for page in doc)
        doc.close()
    except ImportError:
        try:
            subprocess.run(
                ["pdftotext", "-layout", str(pdf), str(out)],
                capture_output=True, text=True
            )
            if out.exists():
                text = out.read_text()
        except FileNotFoundError:
            pass
    if not text.strip():
        return None
    text = re.sub(r"\n{3,}", "\n\n", text)
    out.write_text(text)
    return text


def save_metadata(arxiv_id: str, title: str, authors: list, abstract: str,
                  published: str, categories: list, keyword: str):
    """以 keyword 分类保存 metadata 到 papers/<keyword>/<id>.json"""
    kdir = PAPERS / keyword
    kdir.mkdir(parents=True, exist_ok=True)
    meta = {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "published": published,
        "categories": categories,
        "keyword": keyword,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "abs_url": f"{ARXIV_ABS}{arxiv_id}",
        "pdf_url": f"{ARXIV_PDF}{arxiv_id}",
    }
    (kdir / f"{arxiv_id}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))


def count_papers() -> Dict[str, int]:
    """统计各 keyword 已有论文数"""
    counts = {}
    for kdir in PAPERS.iterdir():
        if kdir.is_dir() and kdir.name not in ("pdfs", "parsed"):
            counts[kdir.name] = len(list(kdir.glob("*.json")))
    return counts


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("--query", required=True)
    s.add_argument("--max", type=int, default=10)

    d = sub.add_parser("download")
    d.add_argument("--query", required=True)
    d.add_argument("--max", type=int, default=5)
    d.add_argument("--keyword", required=True, help="存储分类名,如 instruction_tuning")
    d.add_argument("--no-parse", action="store_true")

    c = sub.add_parser("count")

    args = ap.parse_args()

    if args.cmd == "search":
        rs = arxiv_search(args.query, args.max)
        for r in rs:
            print(f"{r['arxiv_id']} | {r['title'][:80]}")
    elif args.cmd == "download":
        rs = arxiv_search(args.query, args.max)
        ok = 0
        for r in rs:
            target = PAPERS / args.keyword / f"{r['arxiv_id']}.json"
            if target.exists():
                continue
            save_metadata(
                r["arxiv_id"], r["title"], r["authors"], r["abstract"],
                r["published"], r["categories"], args.keyword
            )
            pdf = download_pdf(r["arxiv_id"])
            if pdf and not args.no_parse:
                parse_pdf(r["arxiv_id"])
            ok += 1
            time.sleep(2)
        log(f"DONE: {ok} new papers under {args.keyword}")
    elif args.cmd == "count":
        cnt = count_papers()
        total = sum(cnt.values())
        print(f"TOTAL: {total} papers across {len(cnt)} keywords")
        for k, v in sorted(cnt.items(), key=lambda x: -x[1]):
            print(f"  {k:30s} {v:4d}")


if __name__ == "__main__":
    main()
