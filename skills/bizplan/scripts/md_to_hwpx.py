#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""누적한 사업계획서 .md를 한글(.hwpx, 선택 시 .hwp)로 만든다 — 제출 양식으로 옮기기 전 초안용.

    python3 -B md_to_hwpx.py 사업계획서.md 사업계획서.hwpx [--hwp] [--no-gov-bullets] [--resource-path 그림폴더]
서식: 제목(#·##·###)은 굵게 16/14/12pt, 불릿은 공문서 개조식(□ → ○ → - → ·, 기본 켬), 표는 테두리 + 머리행 음영·굵게,
**굵게**는 굵은 글자로, 그림은 본문 폭(최대 160mm)으로 넣는다.
필요: python-hwpx(pip install python-hwpx, Apache-2.0). 저장 뒤 구조 검증(validate)과 다시 읽기 대조를 한다.
한계: 이 환경에서는 한컴오피스 렌더를 확인할 수 없다 — 글꼴·줄간격·표 너비는 한글 프로그램에서 1회 열어 확인한다.
공고 양식 파일의 칸을 채우는 작업(양식 채우기)은 하지 않는다 — 새 문서를 만든다.
"""
import argparse
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

GOV = ["□", "○", "-", "·"]
INLINE = re.compile(r"(\*\*[^*]+\*\*)")


def _cells(line):
    return [c.strip().replace("**", "") for c in line.strip().strip("|").split("|")]


def build(md, resource_path, gov=True):
    from hwpx import HwpxDocument
    doc = HwpxDocument.new()
    bold = doc.ensure_run_style(bold=True)
    heads = {1: doc.ensure_run_style(bold=True, size=16), 2: doc.ensure_run_style(bold=True, size=14),
             3: doc.ensure_run_style(bold=True, size=12)}
    lines = md.splitlines()
    indents = [len(m.group(1)) for m in re.finditer(r"^( +)[-*+] ", md, re.M)]
    unit = min(indents) if indents else 2
    stats = {"heading": 0, "para": 0, "table": 0, "picture": 0}
    missing = []

    def para(text, prefix=""):
        p = doc.add_paragraph("", include_run=False)
        if prefix:
            p.add_run(prefix)
        for part in INLINE.split(text):
            if not part:
                continue
            if part.startswith("**") and part.endswith("**"):
                p.add_run(part[2:-2], char_pr_id_ref=bold)
            else:
                p.add_run(part)
        stats["para"] += 1

    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s or re.match(r"^(-{3,}|\*{3,})$", s) or s.startswith("<!--"):
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                para(lines[i])
                i += 1
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            level = min(len(m.group(1)), 3)
            doc.add_paragraph(m.group(2).replace("**", ""), char_pr_id_ref=heads[level])
            stats["heading"] += 1
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{2,}", lines[i + 1].strip()):
            header = _cells(s)
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            t = doc.add_table(1 + len(rows), len(header))
            for c, h in enumerate(header):
                t.set_cell_text(0, c, h)
                t.set_cell_shading(0, c, "#E5E7EB")
            for r, row in enumerate(rows, 1):
                for c in range(len(header)):
                    t.set_cell_text(r, c, row[c] if c < len(row) else "")
            for r in range(1 + len(rows)):
                for c in range(len(header)):
                    t.set_cell_borders(r, c, color="#000000")
            lens = [max([len(row[c]) for row in rows if c < len(row)] + [len(header[c]), 2]) for c in range(len(header))]
            t.set_column_widths([max(l, sum(lens) * 0.1) for l in lens])
            stats["table"] += 1
            continue
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", s)
        if m:
            path = m.group(2) if os.path.isabs(m.group(2)) else os.path.join(resource_path, m.group(2))
            if os.path.exists(path):
                from PIL import Image
                with Image.open(path) as im:
                    w, h = im.size
                width = 160.0
                with open(path, "rb") as f:
                    doc.add_picture(f.read(), os.path.splitext(path)[1].lstrip(".").lower().replace("jpg", "jpeg"),
                                    width_mm=width, height_mm=width * h / w)
                stats["picture"] += 1
                if m.group(1):
                    para(m.group(1))
            else:
                missing.append(m.group(2))
                para(f"[그림: {m.group(1)}]")
            i += 1
            continue
        m = re.match(r"^( *)([-*+])\s+(.*)$", line)
        if m:
            level = min(len(m.group(1)) // unit, len(GOV) - 1)
            prefix = ("　" * level + GOV[level] + " ") if gov else ("　" * level + "• ")
            para(m.group(3), prefix)
            i += 1
            continue
        m = re.match(r"^( *)(\d+[.)])\s+(.*)$", line)
        if m:
            para(m.group(3), "　" * (len(m.group(1)) // unit) + m.group(2) + " ")
            i += 1
            continue
        buf = [s.lstrip("> ")]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||!\[|```|( *)([-*+]|\d+[.)])\s)", lines[i].strip()):
            buf.append(lines[i].strip().lstrip("> "))
            i += 1
        para(" ".join(buf))
    return doc, stats, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md")
    ap.add_argument("out")
    ap.add_argument("--hwp", action="store_true", help=".hwp(한글 97 이후 바이너리)도 함께 저장")
    ap.add_argument("--no-gov-bullets", action="store_true")
    ap.add_argument("--resource-path")
    args = ap.parse_args()
    try:
        import hwpx  # noqa: F401
    except ImportError:
        print("python-hwpx가 없다: pip install python-hwpx — 설치할 수 없으면 md_to_docx.py로 .docx를 만들어 한글에서 연다",
              file=sys.stderr)
        return 1
    with open(args.md, encoding="utf-8") as f:
        md = f.read()
    res = args.resource_path or os.path.dirname(os.path.abspath(args.md))
    doc, stats, missing = build(md, res, gov=not args.no_gov_bullets)
    doc.save_to_path(args.out)
    report = doc.validate()
    issues = getattr(report, "issues", [])
    from hwpx import HwpxDocument
    back = HwpxDocument.open(args.out)
    text = back.text.plain() if hasattr(back, "text") else back.export_text()
    print(f"저장: {args.out} (제목 {stats['heading']}, 문단 {stats['para']}, 표 {stats['table']}, 그림 {stats['picture']})")
    print(f"구조 검증: 이슈 {len(issues)}건 / 다시 읽기 {len(text):,}자")
    for it in issues[:10]:
        print("  ! " + str(it))
    for mpath in missing:
        print(f"  ! 그림 없음: {mpath}")
    if args.hwp:
        hwp = os.path.splitext(args.out)[0] + ".hwp"
        with open(hwp, "wb") as f:
            f.write(doc.to_bytes(format="hwp"))
        HwpxDocument.open(hwp)
        print(f"저장: {hwp} (다시 열기 확인)")
    print("확인 필요: 한컴오피스 한글에서 1회 열어 글꼴·줄간격·표 너비를 확인한다(이 도구는 렌더 검증을 하지 못한다).")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
