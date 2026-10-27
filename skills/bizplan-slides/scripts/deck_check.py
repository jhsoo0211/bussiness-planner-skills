#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""발표 .pptx의 수치·날짜가 원문(사업계획서 .md/.txt/.docx/.hwpx)에 있는지 대조하고, 미확보 표기·작은 글자를 센다.

    python3 -B deck_check.py 슬라이드/발표.pptx --against 사업계획서.md [--against 브리프.md] [--min-pt 12]

theme_deck.py·pptx_build.py 어느 쪽으로 만든 덱에도 쓴다. 차트 값도 대조한다.
- 원문에 없는 수치: 같은 값·단위가 원문 어디에도 없다 → 오타·계산 실수·지어낸 숫자일 수 있다(종료 코드 1).
- 단위 확인: 값은 원문에 있으나 단위가 다르거나 없다 → 같은 숫자인지 사람이 본다.
- 쪽번호·단계 번호·목차 번호처럼 이름이 정해진 장식 숫자, 영문자에 붙은 식별자(P1·M3·S2)는 건너뛴다.
"""
import argparse
import os
import re
import subprocess
import sys
import zipfile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER
from pptx.util import Emu

SKIP_NAMES = ("쪽번호", "단계 번호", "번호", "간지 번호", "범례", "장식", "날짜", "브랜드")   # 발표 날짜는 원문 주장이 아니다
CHROME = ("출처", "단위", "브랜드", "태그라인", "머리말", "날짜", "연락처", "Footer", "Date")
UNIT = r"(%|퍼센트|조\s*원|억\s*원|만\s*원|천\s*원|조|억|만|천|원|달러|명|건|개사|개|배|점|회|곳|종|대|개월|년|월|일|시간|분|초|MPa|kg|t|㎡)"
NUM = re.compile(r"(?<![A-Za-z\d.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*" + UNIT + "?")
DATE = re.compile(r"(?<!\d)((?:19|20)\d{2})\s*[.\-/년]\s*(\d{1,2})(?:\s*[.\-/월]\s*(\d{1,2}))?")
MARK = re.compile(r"\[(작성 필요|산정 예정|미확보)")


def read_source(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".md", ".txt", ".csv", ".json"):
        return open(path, encoding="utf-8").read()
    if ext == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        return re.sub(r"<[^>]+>", " ", xml)
    if ext in (".hwpx", ".hwp", ".pdf"):
        here = os.path.dirname(os.path.abspath(__file__))
        reader = os.path.join(here, "..", "..", "bizplan", "scripts", "read_form.py")
        if ext == ".pdf":
            return subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "본문.md")
            subprocess.run([sys.executable, "-B", reader, path, "--out", out], capture_output=True, text=True)
            return open(out, encoding="utf-8").read() if os.path.isfile(out) else ""
    return open(path, encoding="utf-8", errors="ignore").read()


def tokens(text):
    """(값, 단위) 목록. 날짜는 ('날짜', 'YYYY-M') 로 따로 센다."""
    out = []
    for m in DATE.finditer(text):
        out.append(("날짜", f"{m.group(1)}-{int(m.group(2))}"))
    text = DATE.sub(" ", text)
    for m in NUM.finditer(text):
        v = m.group(1).replace(",", "")
        unit = re.sub(r"\s+", "", m.group(2) or "").replace("퍼센트", "%")
        try:
            val = float(v)
        except ValueError:
            continue
        out.append((val, unit))
    return out


def slide_texts(prs):
    for i, slide in enumerate(prs.slides, 1):
        texts, small = [], []

        def walk(shapes):
            for sh in shapes:
                if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
                    walk(sh.shapes)
                    continue
                if any(sh.name.startswith(n) for n in SKIP_NAMES):
                    continue
                if sh.is_placeholder and sh.placeholder_format.type in (PP_PLACEHOLDER.SLIDE_NUMBER, PP_PLACEHOLDER.DATE):
                    continue
                if sh.has_text_frame:
                    texts.append(sh.text_frame.text)
                    for p in sh.text_frame.paragraphs:
                        for r in p.runs:
                            if r.font.size is not None and r.text.strip() and not sh.name.startswith(CHROME):
                                small.append((Emu(r.font.size).pt, r.text.strip()[:20]))
                if getattr(sh, "has_table", False) and sh.has_table:
                    for row in sh.table.rows:
                        for cell in row.cells:
                            texts.append(cell.text)
                if getattr(sh, "has_chart", False) and sh.has_chart:
                    for plot in sh.chart.plots:
                        texts.extend(str(c) for c in plot.categories)
                        for se in plot.series:
                            texts.append(" ".join(f"{v:g}" for v in se.values if v is not None))
        walk(slide.shapes)
        yield i, "\n".join(texts), small


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pptx")
    ap.add_argument("--against", action="append", required=True, help="원문 파일(여러 번 줄 수 있다)")
    ap.add_argument("--min-pt", type=float, default=10.0, help="이보다 작은 글자를 센다(출처·단위·브랜드·머리말 제외)")
    a = ap.parse_args()

    src = "\n".join(read_source(p) for p in a.against)
    src_tok = tokens(src)
    exact = set(src_tok)
    values = {v for v, _ in src_tok if v != "날짜"}
    prs = Presentation(a.pptx)
    rows, bad_total, unit_total = [], 0, 0
    for i, text, small in slide_texts(prs):
        bad, unit = [], []
        for v, u in tokens(text):
            if v == "날짜":
                if (v, u) not in exact:
                    bad.append(u)
                continue
            if (v, u) in exact:
                continue
            if v in values:
                if u:
                    unit.append(f"{v:g}{u}")
                continue
            if not u and v < 10 and float(v).is_integer():
                continue          # 단위 없는 한 자리 정수(순번 등)는 넘긴다
            bad.append(f"{v:g}{u}")
        marks = len(MARK.findall(text))
        tiny = [t for t in small if t[0] < a.min_pt]
        bad_total += len(bad)
        unit_total += len(unit)
        if bad or unit or marks or tiny:
            rows.append((i, bad, unit, marks, tiny))
    print(f"대조: {a.pptx} ↔ {', '.join(a.against)}")
    print(f"원문에 없는 수치 {bad_total}건 · 단위 확인 {unit_total}건 · "
          f"미확보 표기 {sum(r[3] for r in rows)}곳 · {a.min_pt:g}pt 미만 글 {sum(len(r[4]) for r in rows)}개")
    if rows:
        print("| 장 | 원문에 없는 수치 | 단위 확인 | 미확보 표기 | 작은 글(예) |")
        print("|----|------------------|-----------|-------------|-------------|")
        for i, bad, unit, marks, tiny in rows:
            ex = ", ".join(f"{t[1]}({t[0]:g}pt)" for t in tiny[:2]) + (f" 외 {len(tiny) - 2}" if len(tiny) > 2 else "")
            print(f"| {i} | {', '.join(sorted(set(bad))) or '—'} | {', '.join(sorted(set(unit))) or '—'} | "
                  f"{marks or '—'} | {ex or '—'} |")
    sys.exit(1 if bad_total else 0)


if __name__ == "__main__":
    main()
