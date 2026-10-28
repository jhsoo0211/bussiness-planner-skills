#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""누적한 사업계획서 .md를 한글(.hwpx, 선택 시 .hwp)로 만든다 — 제출 양식으로 옮기기 전 초안용.

    python3 -B md_to_hwpx.py 사업계획서.md 사업계획서.hwpx [--hwp] [--no-gov-bullets] [--resource-path 그림폴더] [--captions]
                             [--style form]
서식: 제목(#·##·###)은 굵게 16/14/12pt, 불릿은 공문서 개조식(□ → ○ → - → ·, 기본 켬), 표는 테두리 + 머리행 음영·굵게,
**굵게**는 굵은 글자로, 그림은 본문 폭(최대 160mm, 높이 120mm까지)으로 넣는다(alt 캡션은 --captions일 때만).
필요: python-hwpx(pip install python-hwpx, Apache-2.0). 저장 뒤 구조 검증(validate)과 다시 읽기 대조를 한다.
한계: 이 환경에서는 한컴오피스 렌더를 확인할 수 없다 — 글꼴·줄간격·표 너비는 한글 프로그램에서 1회 열어 확인한다.
--style form은 완성 문서 서식(md_to_docx.py와 같은 표기): 회색 상자 제목, 장 띠, 주제구 밑줄, '- 소주제', 불릿 '- ·',
연노랑 머리행, ```개요``` 양식 표(이름표 회색·칸 병합·그림은 칸 안에), 쪽 번호 '- n -'.
공고 양식 파일의 칸을 채우는 작업(양식 채우기)은 하지 않는다 — 새 문서를 만든다.
"""
import argparse
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from form_style import FORM_MARKS, MARK_RE, OVERVIEW_MM, heading_kind, label_text, layout, split_forms  # noqa: E402

MM = 283.465                                     # HWPUNIT per mm
SIZES = {"title": 18, "square": 14, "chapter": 14, "section": 15, "sub": 12.5, "topic": 13, "subtopic": 11}

GOV = ["□", "○", "-", "·"]
INLINE = re.compile(r"(\*\*[^*]+\*\*|\[[^\]]+\]\{\.underline\}|<u>[^<]+</u>)")
IMG = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
PLAIN = lambda t: re.sub(r"<u>([^<]+)</u>", r"\1", re.sub(r"\[([^\]]+)\]\{\.underline\}", r"\1", t))


def _cells(line):
    return [PLAIN(c.strip().replace("**", "")) for c in line.strip().strip("|").split("|")]


def build(md, resource_path, gov=True, captions=False, style="plain"):
    from hwpx import HwpxDocument
    doc = HwpxDocument.new()
    form = style == "form"
    forms = []
    if form:
        md, forms = split_forms(md)
    marks = FORM_MARKS if form else GOV
    bold = doc.ensure_run_style(bold=True)
    uline = doc.ensure_run_style(underline=True)
    heads = {1: doc.ensure_run_style(bold=True, size=16), 2: doc.ensure_run_style(bold=True, size=14),
             3: doc.ensure_run_style(bold=True, size=12)}
    kinds = {k: doc.ensure_run_style(bold=k != "square", size=v, underline=k == "topic") for k, v in SIZES.items()}
    note = doc.ensure_run_style(size=9, color="#555555")
    cell_head, cell_small = doc.ensure_run_style(bold=True, size=11), doc.ensure_run_style(size=10)
    aligns = {}

    def align(name):
        """정렬 문단 속성 id — 임시 문단에 서식을 주고 id만 받아 둔다(표 칸 문단에도 같은 id를 쓴다)."""
        if name not in aligns:
            tmp = doc.add_paragraph("")
            doc.set_paragraph_format(paragraph_index=len(doc.paragraphs) - 1, alignment=name)
            aligns[name] = doc.paragraphs[-1].para_pr_id_ref
            tmp.remove()
        return aligns[name]
    lines = md.splitlines()
    indents = [len(m.group(1)) for m in re.finditer(r"^( +)[-*+] ", md, re.M)]
    unit = min(indents) if indents else 2
    stats = {"heading": 0, "para": 0, "table": 0, "picture": 0}
    missing = []

    def runs(p, text, base=None):
        for part in INLINE.split(text):
            if not part:
                continue
            if part.startswith("**") and part.endswith("**"):
                p.add_run(part[2:-2], char_pr_id_ref=bold if base is None else base)
            elif part.endswith("{.underline}") or part.startswith("<u>"):
                p.add_run(PLAIN(part), char_pr_id_ref=uline)
            elif base is not None:
                p.add_run(part, char_pr_id_ref=base)
            else:
                p.add_run(part)

    def para(text, prefix="", char=None, pp=None):
        p = doc.add_paragraph("", include_run=False, para_pr_id_ref=pp) if pp else doc.add_paragraph("", include_run=False)
        if prefix:
            p.add_run(prefix, char_pr_id_ref=char) if char else p.add_run(prefix)
        runs(p, text, char)
        stats["para"] += 1

    def cell_lines(cell, lines_, center=False, head=False):
        """표 칸에 줄마다 문단을 쓴다: '○' 줄은 굵게, 나머지는 작게. 칸의 빈 첫 문단은 지운다."""
        first = cell.paragraphs[0] if cell.paragraphs else None
        for ln in lines_:
            p = cell.add_paragraph("", para_pr_id_ref=align("CENTER") if center else None)
            runs(p, ln, cell_head if head or ln.startswith("○") else cell_small)
        if first is not None and lines_ and not first.text:
            first.remove()

    def cell_picture(cell, src, width_mm):
        path = src if os.path.isabs(src) else os.path.join(resource_path, src)
        if not os.path.exists(path):
            missing.append(src)
            cell_lines(cell, [f"[그림 없음: {src}]"], center=True)
            return
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        width = min(width_mm - 4, 62.0 * w / h)          # 개요 칸 그림 높이 62mm까지(docx와 같다)
        with open(path, "rb") as f:
            bid = doc.add_image(f.read(), os.path.splitext(path)[1].lstrip(".").lower().replace("jpg", "jpeg"))
        p = cell.paragraphs[0]
        p.para_pr_id_ref = align("CENTER")
        p.add_picture(bid, width=int(width * MM), height=int(width * h / w * MM))
        stats["picture"] += 1

    def form_table(fm):
        """개요 양식 표: 이름표 열 회색, 명칭|범주 한 줄, 값은 세 칸 병합, 그림 2개씩 + 캡션 줄."""
        rows = layout(fm)
        if not rows:
            return
        t = doc.add_table(len(rows), 4)
        t.set_column_widths(list(OVERVIEW_MM))
        cells, pics = {}, [k for k, r in enumerate(rows) if r[0] in ("img", "cap")]
        for k, row in enumerate(rows):
            if row[0] == "pair":
                for c in range(4):
                    cells[(k, c)] = t.cell(k, c)
                t.set_cell_shading(k, 0, "#D9D9D9")
                t.set_cell_shading(k, 2, "#D9D9D9")
            elif row[0] == "full":
                cells[(k, 0)] = t.cell(k, 0)
                t.set_cell_shading(k, 0, "#D9D9D9")
                cells[(k, 1)] = t.merge_cells(k, 1, k, 3)
            elif len(row[1]) == 2:
                cells[(k, 1)] = t.cell(k, 1)
                cells[(k, 2)] = t.merge_cells(k, 2, k, 3)
            else:
                cells[(k, 1)] = t.merge_cells(k, 1, k, 3)
        if pics:
            t.set_cell_shading(pics[0], 0, "#D9D9D9")
            cell_lines(t.merge_cells(pics[0], 0, pics[-1], 0), [label_text("이미지")], center=True, head=True)
        for k, row in enumerate(rows):
            if row[0] == "pair":
                (k1, v1), (k2, v2) = row[1], row[2]
                cell_lines(cells[(k, 0)], [label_text(k1)], center=True, head=True)
                cell_lines(cells[(k, 1)], v1)
                cell_lines(cells[(k, 2)], [label_text(k2)], center=True, head=True)
                cell_lines(cells[(k, 3)], v2)
            elif row[0] == "full":
                cell_lines(cells[(k, 0)], [label_text(row[1])], center=True, head=True)
                cell_lines(cells[(k, 1)], row[2])
            else:
                widths = ([OVERVIEW_MM[1], OVERVIEW_MM[2] + OVERVIEW_MM[3]] if len(row[1]) == 2 else [sum(OVERVIEW_MM[1:])])
                for c, (src, cap), w in zip((1, 2), row[1], widths):
                    if row[0] == "img":
                        cell_picture(cells[(k, c)], src, w)
                    else:
                        cell_lines(cells[(k, c)], [cap], center=True)
        stats["table"] += 1

    def boxed(text, kind):
        """제목 상자(회색 바탕, 본문 폭) · 장 띠(테두리, 글 길이만큼) — 1칸 표로 만든다."""
        width = None if kind == "title" else int(min(170, len(text) * SIZES[kind] * 0.36 + 14) * MM)
        t = doc.add_table(1, 1, width=width) if width else doc.add_table(1, 1)
        if kind == "title":
            t.set_cell_shading(0, 0, "#D9D9D9")
        t.set_cell_borders(0, 0, color="#000000")
        cell = t.cell(0, 0)
        first = cell.paragraphs[0] if cell.paragraphs else None
        p = cell.add_paragraph("", para_pr_id_ref=align("CENTER") if kind == "title" else None)
        p.add_run(text, char_pr_id_ref=kinds[kind])
        if first is not None and not first.text:
            first.remove()

    def picture(alt, src, width=160.0):
        path = src if os.path.isabs(src) else os.path.join(resource_path, src)
        if not os.path.exists(path):
            missing.append(src)
            para(f"[그림: {alt}]")
            return
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        width = min(width, 120.0 * w / h)          # 높이 120mm까지(docx와 같은 상한)
        with open(path, "rb") as f:
            doc.add_picture(f.read(), os.path.splitext(path)[1].lstrip(".").lower().replace("jpg", "jpeg"),
                            width_mm=width, height_mm=width * h / w)
        stats["picture"] += 1

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
            text = m.group(2).replace("**", "")
            if form:
                kind = heading_kind(len(m.group(1)), text)
                if kind in ("title", "chapter"):
                    boxed(text, kind)
                else:
                    doc.add_paragraph(("- " if kind == "subtopic" else "") + text, char_pr_id_ref=kinds[kind])
            else:
                doc.add_paragraph(text, char_pr_id_ref=heads[min(len(m.group(1)), 3)])
            stats["heading"] += 1
            i += 1
            continue
        mk = MARK_RE.match(s)
        if mk:
            if int(mk.group(1)) < len(forms):
                form_table(forms[int(mk.group(1))])
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{2,}", lines[i + 1].strip()):
            header = _cells(s)
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            grid = [header] + rows
            if any(IMG.search(c) for row in grid for c in row):
                # 사진 격자 표: 한글 표 칸에 그림을 넣지 않고 그림 + '▲ 캡션'을 차례로 놓는다
                for r, row in enumerate(grid):
                    for c, cell in enumerate(row):
                        m = IMG.search(cell)
                        if not m:
                            continue
                        nxt = grid[r + 1][c] if r + 1 < len(grid) and c < len(grid[r + 1]) else ""
                        cap = nxt if nxt and not IMG.search(nxt) else (m.group(1) or "")
                        picture(m.group(1), m.group(2), width=80.0)
                        if cap:
                            para(f"▲ {cap}")
                stats["table"] += 1
                continue
            t = doc.add_table(1 + len(rows), len(header))
            for c, h in enumerate(header):
                t.set_cell_text(0, c, h)
                t.set_cell_shading(0, c, "#FFF2CC" if form else "#E5E7EB")
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
            picture(m.group(1), m.group(2))
            # 시각자료는 그림 안에 결론 제목이 있다 — alt 글을 그림 아래에 한 번 더 쓰지 않는다(--captions로 켠다)
            if captions and m.group(1) and os.path.exists(m.group(2) if os.path.isabs(m.group(2)) else os.path.join(resource_path, m.group(2))):
                para(m.group(1))
            i += 1
            continue
        m = re.match(r"^( *)([-*+])\s+(.*)$", line)
        if m:
            level = min(len(m.group(1)) // unit, len(GOV) - 1)
            level = min(level, len(marks) - 1)
            prefix = ("　" * level + marks[level] + " ") if (gov or form) else ("　" * level + "• ")
            if re.match(r"^[□○◦·■●▪-] ", m.group(3)):   # 글이 이미 ○·□로 시작하면 기호를 겹쳐 붙이지 않는다
                prefix = "　" * level
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
        text = " ".join(buf)
        if form and (text.startswith("※") or text.startswith("(출처") or text.startswith("(확인")):
            para(text, char=note, pp=align("RIGHT") if text.startswith("(") else None)
        elif form:
            para(text, pp=align("JUSTIFY"))
        else:
            para(text)
    if form:
        doc.set_page_number(prefix="- ", suffix=" -")
    return doc, stats, missing


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md")
    ap.add_argument("out")
    ap.add_argument("--hwp", action="store_true", help=".hwp(한글 97 이후 바이너리)도 함께 저장")
    ap.add_argument("--no-gov-bullets", action="store_true")
    ap.add_argument("--resource-path")
    ap.add_argument("--captions", action="store_true", help="그림 alt 글을 그림 아래 문단으로도 단다(기본: 달지 않음)")
    ap.add_argument("--style", choices=("plain", "form"), default="plain", help="form = 완성 문서 서식")
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
    doc, stats, missing = build(md, res, gov=not args.no_gov_bullets, captions=args.captions, style=args.style)
    doc.save_to_path(args.out)
    os.chmod(args.out, 0o644)                           # python-hwpx는 0600으로 쓴다 — 다른 산출물과 같은 권한으로
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
