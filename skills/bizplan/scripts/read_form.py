#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""공고 양식·제출 양식(.hwp/.hwpx/.docx/.pdf/.md/.txt)을 읽어 마크다운 본문과 '양식 핏'용 요약을 뽑는다.

    python3 -B read_form.py 양식.hwpx [--out 양식.md]
출력
  - 목차 후보: '1.', '1-1.', '가.', '□', '○', 제목 문단처럼 보이는 줄 — 산출물 목차·항목 번호를 맞출 때 쓴다
  - 안내 문구 후보: '※'로 시작하거나 '작성', '기재', '삭제' 지시가 든 줄 — 제출 전 삭제 대상 표시용
  - 분량 지시: 'n페이지', 'n쪽', 'n자 이내' 등
  - 표 목록(행×열)
.hwp/.hwpx는 python-hwpx(pip install python-hwpx, Apache-2.0)를 쓴다. 없으면 .hwpx만 내장 XML 파서로 글자를 뽑는다.
배포용(암호화) 문서처럼 열 수 없는 파일은 그 사실을 알리고 목차 텍스트 붙여넣기를 요청한다.
"""
import argparse
import os
import re
import subprocess
import sys
import warnings
import zipfile
import xml.etree.ElementTree as ET

warnings.filterwarnings("ignore", category=DeprecationWarning)

TOC = re.compile(r"^\s*(\d+(?:-\d+)*[.)]\s|\d+\.\d+\s|[가-하][.)]\s|[□■○●◦▪◇◆]\s?|[IVX]+\.\s|제\s*\d+\s*[장절]|#+\s)")
GUIDE = re.compile(r"^\s*※|작성\s*(요령|방법|예시)|기재\s*(하|바람|요망)|삭제\s*(후|하고)|(작성|기재)하시기\s*바랍니다|예\s*시\s*[)）:]")
LENGTH = re.compile(r"\d+\s*(페이지|쪽|매|장)\s*(이내|내외|이하)?|\d[\d,]*\s*자\s*(이내|이하|내외)")


def from_hwp(path):
    try:
        from hwpx import HwpxDocument
    except ImportError:
        if path.lower().endswith(".hwpx"):
            return hwpx_stdlib(path), "내장 XML 파서(python-hwpx 없음 — 표 구조는 단순화됨)"
        raise RuntimeError(".hwp를 읽으려면 python-hwpx가 필요하다: pip install python-hwpx")
    doc = HwpxDocument.open(path)
    text = doc.text.markdown() if hasattr(doc, "text") else doc.export_markdown()
    return text, "python-hwpx"


def hwpx_stdlib(path):
    """python-hwpx 없이 .hwpx 본문(Contents/section*.xml)의 문단·표 글자를 뽑는다."""
    out = []
    with zipfile.ZipFile(path) as z:
        for name in sorted(n for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n)):
            root = ET.fromstring(z.read(name))
            for el in root.iter():
                tag = el.tag.split("}")[-1]
                if tag == "tbl":
                    rows = []
                    for tr in [e for e in el.iter() if e.tag.split("}")[-1] == "tr"]:
                        cells = []
                        for tc in [e for e in tr if e.tag.split("}")[-1] == "tc"]:
                            cells.append(" ".join(t.text or "" for t in tc.iter() if t.tag.split("}")[-1] == "t").strip())
                        rows.append(cells)
                    if rows:
                        out.append("| " + " | ".join(rows[0]) + " |")
                        out.append("|" + "---|" * len(rows[0]))
                        out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                        out.append("")
                    el.clear()
                elif tag == "p":
                    t = "".join(x.text or "" for x in el.iter() if x.tag.split("}")[-1] == "t").strip()
                    if t:
                        out.append(t)
                        out.append("")
    return "\n".join(out)


def from_docx(path):
    from docx import Document
    doc = Document(path)
    out = []
    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            text = "".join(t.text or "" for t in child.iter() if t.tag.endswith("}t")).strip()
            style = child.find(".//{*}pStyle")
            level = None
            if style is not None:
                m = re.search(r"(\d)", style.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", ""))
                if "Heading" in style.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "") and m:
                    level = int(m.group(1))
            if text:
                out.append(("#" * level + " " if level else "") + text)
                out.append("")
        elif tag == "tbl":
            rows = []
            for tr in child.iter("{*}tr"):
                rows.append([" ".join(t.text or "" for t in tc.iter() if t.tag.endswith("}t")).strip()
                             for tc in tr.iter("{*}tc")])
            if rows:
                out.append("| " + " | ".join(rows[0]) + " |")
                out.append("|" + "---|" * len(rows[0]))
                out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                out.append("")
    return "\n".join(out)


def from_pdf(path):
    r = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("pdftotext 실패(스캔 PDF면 페이지 이미지를 직접 판독한다)")
    if not r.stdout.strip():
        raise RuntimeError("글자 층이 없는 PDF(스캔본) — 페이지 이미지를 직접 판독한다")
    return r.stdout


def read(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".hwp", ".hwpx"):
        return from_hwp(path)
    if ext == ".docx":
        return from_docx(path), "python-docx"
    if ext == ".pdf":
        return from_pdf(path), "pdftotext"
    with open(path, encoding="utf-8") as f:
        return f.read(), "텍스트"


def summarize(text):
    lines = [l.rstrip() for l in text.splitlines()]
    toc, guide, length = [], [], []
    for l in lines:
        in_table = l.strip().startswith("|")
        # 표 행은 칸마다 안내 문구만 본다(예창패 양식의 안내 박스는 표 칸에 있다)
        parts = [c.strip() for c in l.strip().strip("|").split("|")] if in_table else [l.strip()]
        for s in parts:
            if s and GUIDE.search(s):
                guide.append(s)
        s = l.strip()
        if not s or in_table:
            continue
        if not GUIDE.search(s) and TOC.match(s) and len(s) <= 60:
            toc.append(s)
        for m in LENGTH.finditer(s):
            length.append(f"{m.group(0)} — {s[:70]}")
    tables = []
    i = 0
    while i < len(lines) - 1:
        if lines[i].strip().startswith("|") and re.match(r"^\|?\s*-{3}", lines[i + 1].strip()):
            cols = len(lines[i].strip().strip("|").split("|"))
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            tables.append(f"{j - i - 1}행×{cols}열: {lines[i].strip()[:80]}")
            i = j
        else:
            i += 1
    return toc, guide, length, tables


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("form")
    ap.add_argument("--out", help="본문 마크다운 저장 경로")
    args = ap.parse_args()
    try:
        text, engine = read(args.form)
    except Exception as e:  # 암호화·손상 파일 등
        print(f"양식을 읽지 못했다: {e}", file=sys.stderr)
        print("→ 사용자에게 양식의 목차·항목·분량 지시를 붙여넣어 달라고 요청한다.", file=sys.stderr)
        return 1
    toc, guide, length, tables = summarize(text)
    print(f"읽기: {args.form} (엔진: {engine}, {len(text):,}자)")
    print("\n[목차 후보]")
    print("\n".join("  " + t for t in toc) or "  (없음 — 본문을 직접 훑어 항목을 정한다)")
    print("\n[안내 문구 후보 — 제출 전 삭제 대상]")
    print("\n".join("  " + g[:100] for g in guide) or "  (없음)")
    print("\n[분량 지시]")
    print("\n".join("  " + l for l in length) or "  (없음 — 공고문에서 확인)")
    print("\n[표]")
    print("\n".join("  " + t for t in tables) or "  (없음)")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n본문 저장: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
