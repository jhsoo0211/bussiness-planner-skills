#!/usr/bin/env python3
"""Block confidential material from the public repository.

    python3 scripts/check_confidential.py [--terms FILE] [--root DIR]

Checks every file tracked by git (the index, so staged files count too):
- private folders: 자료/, 분석/, */templates/local/, */themes/local/, graphify-out/
- original-document formats: .pdf .hwp .hwpx .doc .docx .xlsx .ppt
  (.pptx/.potx only inside the public template folder; .zip only inside dist/,
  and the entries of each zip are checked with the same rules)
- private terms (one per line in --terms, case-insensitive) in text files and zip entry names

Prints only paths, line numbers and reasons — never the matched term, because Actions logs
of a public repository are public. Without a terms file that step is skipped.
Exit code 1 on any finding.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import zipfile

PRIVATE_DIRS = ("자료/", "분석/", "graphify-out/")
PRIVATE_PARTS = ("/templates/local/", "/themes/local/")
BLOCKED_EXT = {".pdf", ".hwp", ".hwpx", ".doc", ".docx", ".xlsx", ".ppt"}
TEMPLATE_DIR = "skills/bizplan-slides/assets/templates/"
DEFAULT_TERMS = Path("~/.config/bizplan/confidential-terms.txt").expanduser()
TEXT_LIMIT = 2_000_000


def path_reason(path):
    """Why this path may not be in the repository, or None."""
    p = path.replace("\\", "/")
    if p.startswith(PRIVATE_DIRS) or any(part in "/" + p for part in PRIVATE_PARTS):
        return "private folder"
    ext = os.path.splitext(p)[1].lower()
    if ext in BLOCKED_EXT:
        return f"original document format ({ext})"
    if ext in (".pptx", ".potx") and not p.startswith(TEMPLATE_DIR):
        return f"slide file outside {TEMPLATE_DIR}"
    return None


def load_terms(path):
    if not path or not path.is_file():
        return []
    return [t.strip().lower() for t in path.read_text(encoding="utf-8").splitlines()
            if t.strip() and not t.lstrip().startswith("#")]


def term_hits(text, terms):
    """Line numbers that contain any term."""
    hits = []
    for number, line in enumerate(text.lower().splitlines(), 1):
        if any(t in line for t in terms):
            hits.append(number)
    return hits


def masked(path, terms):
    """Hide path segments that contain a private term, so the log never shows it."""
    return "/".join("***" if any(t in seg.lower() for t in terms) else seg for seg in path.split("/"))


def tracked(root):
    out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                         capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def check(root, terms):
    findings = []
    for rel in tracked(root):
        reason = path_reason(rel)
        if reason:
            findings.append((rel, reason))
            continue
        full = root / rel
        if not full.is_file():
            continue
        if rel.lower().endswith(".zip"):
            if not rel.startswith("dist/"):
                findings.append((rel, "zip outside dist/"))
                continue
            with zipfile.ZipFile(full) as z:
                for name in z.namelist():
                    inner = path_reason(name)
                    if inner:
                        findings.append((f"{rel}!{name}", inner))
                    elif terms and term_hits(name, terms):
                        findings.append((f"{rel}!{masked(name, terms)}", "private term in entry name"))
                    elif terms and not name.endswith("/"):
                        data = z.read(name)
                        if b"\0" not in data[:1024]:
                            lines = term_hits(data.decode("utf-8", "ignore"), terms)
                            if lines:
                                findings.append((f"{rel}!{masked(name, terms)}", f"private term (line {', '.join(map(str, lines[:5]))})"))
            continue
        if terms:
            if term_hits(rel, terms):
                findings.append((masked(rel, terms), "private term in path"))
                continue
            if full.stat().st_size > TEXT_LIMIT:
                continue
            data = full.read_bytes()
            if b"\0" in data[:1024]:
                continue
            lines = term_hits(data.decode("utf-8", "ignore"), terms)
            if lines:
                findings.append((rel, f"private term (line {', '.join(map(str, lines[:5]))})"))
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--terms", type=Path, help=f"private terms, one per line (default: {DEFAULT_TERMS} if present)")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    a = ap.parse_args()

    terms = load_terms(a.terms or DEFAULT_TERMS)
    findings = check(a.root.resolve(), terms)
    print(f"Checked tracked files · private terms: {len(terms) if terms else 'none (term check skipped)'}")
    for path, reason in findings:
        print(f"FAIL {path} — {reason}")
    print(f"{len(findings)} finding(s)")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
