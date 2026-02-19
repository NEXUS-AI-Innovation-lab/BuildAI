#!/usr/bin/env python3
"""Report scraped files in raw_data with type and probable source site.

Usage:
  python scripts/report_raw_data_files.py [--raw-dir PATH] [--out-json PATH] [--out-csv PATH]

Heuristics for source:
- .html/.txt files are checked for domain strings
- For binaries (pdf/images), try to match a sibling .txt/.html with same stem
- If path or filename contains a known domain, use it
Scans both storage/raw_data and scrapping/raw_data when present.
"""

import argparse
import csv
import json
import mimetypes
import os
import time
from pathlib import Path

BTP_DOMAIN = "btp-cours.com"
GENIE_DOMAIN = "geniecivilpdf.com"
TPDEMAIN_DOMAIN = "tpdemain.com"


def guess_source_from_text(text: str) -> str:
    lower = text.lower()
    if TPDEMAIN_DOMAIN in lower:
        return TPDEMAIN_DOMAIN
    if GENIE_DOMAIN in lower:
        return GENIE_DOMAIN
    if BTP_DOMAIN in lower:
        return BTP_DOMAIN
    return "unknown"


def read_text_safe(path: Path, max_bytes: int = 200_000) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="ignore")
        return data[:max_bytes]
    except Exception:
        return ""


def detect_file_kind(path: Path, mime: str | None) -> str:
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        return "html"
    if suffix == ".pdf" or (mime or "").lower() == "application/pdf":
        return "pdf"
    if (mime or "").lower().startswith("image/") or suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}:
        return "image"
    if suffix == ".txt" or (mime or "").lower().startswith("text/"):
        return "text"
    return "other"


def detect_source_for_file(path: Path, sibling_map: dict) -> str:
    suffix = path.suffix.lower()
    lower_path = path.as_posix().lower()

    # 1) Path contains domain -> highest priority
    for domain in (TPDEMAIN_DOMAIN, GENIE_DOMAIN, BTP_DOMAIN):
        if domain in lower_path:
            return domain

    # 2) Text/html -> analyze content
    if suffix in {".html", ".htm", ".txt"}:
        text = read_text_safe(path)
        src = guess_source_from_text(text)
        return src

    # 3) Binaries -> check siblings content (txt/html)
    stem = path.stem
    siblings = sibling_map.get(stem, set())

    if ".txt" in siblings:
        txt_path = path.with_suffix(".txt")
        if txt_path.exists():
            text = read_text_safe(txt_path)
            src = guess_source_from_text(text)
            if src != "unknown":
                return src

    if ".html" in siblings:
        html_path = path.with_suffix(".html")
        if html_path.exists():
            text = read_text_safe(html_path)
            src = guess_source_from_text(text)
            if src != "unknown":
                return src

    return "unknown"


def build_sibling_map(files):
    sibling_map = {}
    for p in files:
        sibling_map.setdefault(p.stem, set()).add(p.suffix.lower())
    return sibling_map


def main():
    default_raw = Path(os.getenv("RAW_DATA_PATH", "storage/raw_data"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default=str(default_raw))
    parser.add_argument("--out-json", default="storage/raw_data_report.json")
    parser.add_argument("--out-csv", default="storage/raw_data_report.csv")
    args = parser.parse_args()

    raw_dirs = []
    primary = Path(args.raw_dir)
    if primary.exists():
        raw_dirs.append(primary)

    for candidate in (Path("storage/raw_data"), Path("scrapping/raw_data")):
        if candidate.exists() and candidate not in raw_dirs:
            raw_dirs.append(candidate)

    if not raw_dirs:
        raise SystemExit(f"Raw data directory not found: {args.raw_dir}")

    files = []
    for d in raw_dirs:
        files.extend([p for p in d.iterdir() if p.is_file()])
    sibling_map = build_sibling_map(files)

    rows = []
    for p in sorted(files):
        mime, _ = mimetypes.guess_type(p.name)
        file_type = mime or "application/octet-stream"
        file_kind = detect_file_kind(p, mime)
        source = detect_source_for_file(p, sibling_map)
        source_confidence = "high" if source != "unknown" else "low"
        rows.append({
            "filename": p.name,
            "path": str(p),
            "type": file_type,
            "file_kind": file_kind,
            "size_bytes": p.stat().st_size,
            "source": source,
            "source_confidence": source_confidence,
        })

    # Write JSON
    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write CSV
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    try:
        with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["filename", "path", "type", "file_kind", "size_bytes", "source", "source_confidence"],
                delimiter=";",
            )
            writer.writeheader()
            writer.writerows(rows)
    except PermissionError:
        alt_csv = out_csv.with_name(f"{out_csv.stem}_{time.time_ns()}{out_csv.suffix}")
        with alt_csv.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["filename", "path", "type", "file_kind", "size_bytes", "source", "source_confidence"],
                delimiter=";",
            )
            writer.writeheader()
            writer.writerows(rows)
        out_csv = alt_csv

    dirs_label = ", ".join(str(d) for d in raw_dirs)
    print(f"Found {len(rows)} files in {dirs_label}")
    print(f"Report JSON: {out_json}")
    print(f"Report CSV: {out_csv}")


if __name__ == "__main__":
    main()
