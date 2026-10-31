#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""내용 스펙(JSON)을 테마의 디자인 문법으로 그려 편집 가능한 .pptx를 만든다.

사용자 템플릿이 PDF·이미지뿐이거나 템플릿이 없을 때 쓴다(.pptx 템플릿이 있으면 pptx_build.py).
장마다 정보 유형에 맞는 패턴(type)을 고르면, 패턴이 항목 개수·글 길이에 맞춰 배치를 계산한다.
정보 유형 → 패턴 고르는 법은 bizplan-visual/references/info-patterns.md.

    python3 -B theme_deck.py --spec 슬라이드/deck.json --out 슬라이드/발표.pptx [--theme report-blue] [--font "맑은 고딕"]
    python3 -B theme_deck.py --check --spec 슬라이드/deck.json     # 그리지 않고 스펙만 검사
    python3 -B theme_deck.py --catalog                             # 패턴별 필드·개수 표(마크다운)
    python3 -B theme_deck.py --themes                              # 쓸 수 있는 테마
    python3 -B theme_deck.py --sample --theme mono-line --out 샘플.pptx

스펙 최상위: {"theme": "report-blue", "meta": {"brand", "tagline", "date", "presenter", "org", "contact": [[라벨, 값]]},
             "slides": [{"type": "cards", "title": "...", ...}, ...]}
- 글 안의 **굵게** 는 강조(굵게 + 테마 강조색). 문자열 안 줄바꿈(\\n)은 문단을 나눈다. 목록 안의 목록은 하위 항목.
- 그림 경로는 스펙 파일 기준 상대 경로. "[이미지: 서비스 화면]"처럼 대괄호로 시작하면 자리 표시 상자를 그린다.
- 검사 단계에서 모르는 키·개수 초과·필수 누락은 오류로 멈춘다 — 내용이 조용히 빠지지 않게 한다.
- 만든 뒤 스펙의 모든 글이 실제 슬라이드에 들어갔는지 다시 열어 대조한다(누락 0이어야 한다).
글 넘침은 글꼴 폭을 보수적으로 어림해 판단한다. 반드시 export_pdf.py + preview.py 렌더로 눈으로 확인한다.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE, XL_TICK_MARK
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
THEME_DIR = os.path.normpath(os.path.join(HERE, "..", "assets", "themes"))
SW, SH = 960.0, 540.0      # 16:9 슬라이드 크기(pt)
LH = 1.2                   # 글꼴 기본 줄 높이(em) — Pretendard·맑은 고딕 모두 약 1.2
NO_STYLE_TABLE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"   # 표 스타일 없음·격자 없음
ALIGN = {"l": "l", "left": "l", "왼쪽": "l", "c": "c", "center": "c", "가운데": "c", "r": "r", "right": "r", "오른쪽": "r"}
# 팀 카드 이름 칸에 사람 이름 대신 역할을 적은 경우 — 이니셜을 찍지 않고 사람 모양 자리로 둔다
ROLE = re.compile(r"대표|팀장|팀원|개발자|디자이너|기획자|담당|마케터|연구원|이사|매니저|자문|채용|예정|미정|공석|"
                  r"\b(CEO|CTO|COO|CFO|CMO|PM|PO|TBD|Lead|Manager|Engineer|Developer|Designer|Marketer|Hire)\b", re.I)


def E(v):
    return Emu(int(round(v * 12700)))


# ---------------------------------------------------------------- 패턴 정의(검사·카탈로그의 단일 기준)

def _items(lo, hi, req="", opt="", text_ok=False):
    return {"min": lo, "max": hi, "req": req.split(), "opt": opt.split(), "text_ok": text_ok}


COMMON = {"type", "title", "eyebrow", "lead", "source", "notes"}
PATTERNS = {
    "cover": {"use": "표지 — 사업명·한 줄 소개·발표자", "keys": "subtitle presenter org date contact image"},
    "toc": {"use": "목차", "req": "items", "items": _items(2, 8, "title", "sub", text_ok=True)},
    "section": {"use": "간지 — 대제목 구분", "req": "title", "keys": "no desc", "items": _items(0, 4, text_ok=True)},
    "statement": {"use": "한 문장 메시지·결론", "req": "title", "keys": "sub"},
    "bullets": {"use": "개조식 설명 3±1줄(+오른쪽 그림)", "req": "title bullets", "keys": "image image_caption callout"},
    "cards": {"use": "대등한 항목 2~6개(+결론으로 수렴)", "req": "title items", "keys": "callout converge",
              "items": _items(2, 6, "title", "body tag value")},
    "radial": {"use": "중심 개념 + 둘레 요인 3~6개", "req": "title center items", "keys": "center_sub callout",
               "items": _items(3, 6, "title", "body")},
    "kpi": {"use": "핵심 수치 2~4개", "req": "title items", "keys": "callout",
            "items": _items(2, 4, "value label", "desc percent")},
    "chart": {"use": "추이·비교·구성비 그래프(편집 가능한 차트)", "req": "title", "keys": "chart image caption points callout"},
    "tam": {"use": "시장 규모 TAM ⊃ SAM ⊃ SOM", "req": "title items", "keys": "callout",
            "items": _items(3, 3, "value", "label desc")},
    "compare": {"use": "자사 vs 경쟁·기존 — 기준별 대조", "req": "title left right", "keys": "criteria ours callout"},
    "before_after": {"use": "도입 전 → 도입 후", "req": "title before after", "keys": "callout"},
    "process": {"use": "순서가 있는 단계 3~6개", "req": "title items", "keys": "callout",
                "items": _items(3, 6, "title", "body label")},
    "timeline": {"use": "시점별 이정표 3~6개(완료·진행·예정)", "req": "title items", "keys": "callout",
                 "items": _items(3, 6, "when title", "body status")},
    "gantt": {"use": "과업 × 기간 추진 일정", "req": "title periods rows", "keys": "milestones"},
    "table": {"use": "여러 속성의 기록 — 예산·계획·비교표", "req": "title",
              "keys": "header rows total highlight_row widths align size note tables"},
    "swot": {"use": "SWOT 2×2", "req": "title s w o t", "keys": "callout"},
    "rows": {"use": "라벨-내용 쌍 2~6행 — 리스크→대응·요약·FAQ", "req": "title items", "keys": "callout",
             "items": _items(2, 6, "title", "label body")},
    "pillars": {"use": "비전 → 미션 → 추진 축(전략 체계)", "req": "title items", "keys": "vision mission foundation",
                "items": _items(2, 5, "title", "body")},
    "team": {"use": "대표자·팀원 1~4명", "req": "title items", "keys": "callout",
             "items": _items(1, 4, "name", "role career photo")},
    "positioning": {"use": "2축 포지셔닝 맵", "req": "title x_axis y_axis items", "keys": "points",
                    "items": _items(2, 8, "name x y", "ours")},
    "image": {"use": "제품·화면 사진 + 설명", "req": "title image", "keys": "caption bullets callout"},
    "closing": {"use": "마무리·Q&A", "keys": "sub contact"},
}
SUBKEYS = {
    "left": {"title", "items"}, "right": {"title", "items"},
    "before": {"title", "items", "body"}, "after": {"title", "items", "body"},
    "chart": {"kind", "categories", "series", "unit", "number_format", "highlight", "labels", "percent"},
    "tables": {"caption", "header", "rows", "total", "highlight_row", "widths", "align"},
    "rows@gantt": {"task", "start", "end", "label", "status"}, "milestones": {"at", "label"},
}
CHART_KINDS = {"column": XL_CHART_TYPE.COLUMN_CLUSTERED, "bar": XL_CHART_TYPE.BAR_CLUSTERED,
               "line": XL_CHART_TYPE.LINE_MARKERS, "stacked": XL_CHART_TYPE.COLUMN_STACKED,
               "doughnut": XL_CHART_TYPE.DOUGHNUT, "pie": XL_CHART_TYPE.PIE}
NONTEXT = {"type", "image", "photo", "notes", "kind", "number_format", "widths", "align", "ours", "converge",
           "labels", "percent", "highlight", "size", "highlight_row", "total", "x", "y", "start", "end", "at", "values"}


# ---------------------------------------------------------------- 글 폭 어림

def strip_md(t):
    return str(t).replace("**", "")


def em(text):
    """글자 폭(em) 어림 — 한글 0.93(맑은 고딕 기준, Pretendard는 더 좁다), 영문 소문자 0.56, 대문자 0.68."""
    w = 0.0
    for ch in text:
        o = ord(ch)
        if ch.isspace():
            w += 0.28
        elif 0xAC00 <= o <= 0xD7A3 or 0x1100 <= o <= 0x11FF or 0x3130 <= o <= 0x318F or 0x2E80 <= o <= 0x9FFF \
                or 0xFF00 <= o <= 0xFFEF or ch in "○□■●◆◇▶→←↑↓※":
            w += 0.93
        elif ch in "·•.,:;'|!ilI":
            w += 0.3
        elif ch.isupper() or ch in "%&@#mwMW—~":
            w += 0.7
        else:
            w += 0.58
    return w


def n_lines(text, size, width, bold=False):
    """어절 단위 줄바꿈(eaLnBrk=0)을 흉내 내 줄 수를 센다. 한 줄보다 긴 어절은 음절 단위로 끊긴다고 본다."""
    avail = max(width, size) * 0.96 / size
    k = 1.03 if bold else 1.0
    total = 0
    for raw in str(text).split("\n"):
        lines, cur = 1, 0.0
        for word in raw.split(" "):
            if not word:
                continue
            w = em(word) * k
            need = w if cur == 0 else cur + 0.28 * k + w
            if need <= avail:
                cur = need
                continue
            if cur > 0:
                lines += 1
            while w > avail:
                lines += 1
                w -= avail
            cur = w
        total += lines
    return total


def _paras(content):
    """문자열·목록을 [(글, 수준)] 로 편다. 목록 안의 목록은 수준 1."""
    if content is None:
        return []
    if isinstance(content, (int, float)):
        content = str(content)
    if isinstance(content, str):
        return [(line, 0) for line in content.split("\n")]
    out = []
    for it in content:
        if isinstance(it, (list, tuple)):
            out += [(str(t), 1) for t in it]
        else:
            out.append((str(it), 0))
    return out


def _hex(v):
    return v.lstrip("#").upper()


def mix(a, b, t):
    """색 a와 b를 t(0~1) 비율로 섞는다(b 쪽으로)."""
    a, b = _hex(a), _hex(b)
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


def luminance(h):
    h = _hex(h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _set_ea(rpr, font):
    """rPr/defRPr에 동아시아 글꼴(a:ea)을 latin 바로 뒤에 넣는다."""
    ea = rpr.find(qn("a:ea"))
    if ea is None:
        ea = rpr.makeelement(qn("a:ea"), {})
        latin = rpr.find(qn("a:latin"))
        if latin is not None:
            latin.addnext(ea)
        else:
            nxt = [rpr.find(qn(t)) for t in ("a:cs", "a:sym", "a:hlinkClick", "a:hlinkMouseOver", "a:rtl", "a:extLst")]
            nxt = [n for n in nxt if n is not None]
            nxt[0].addprevious(ea) if nxt else rpr.append(ea)
    ea.set("typeface", font)


def _nostyle(shape):
    st = shape._element.find(qn("p:style"))
    if st is not None:
        shape._element.remove(st)


# ---------------------------------------------------------------- 테마

def list_themes():
    out = []
    for d in (os.path.join(THEME_DIR, "local"), THEME_DIR):
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".json") and not f.startswith("sample"):
                    out.append(os.path.join(d, f))
    return out


def load_theme(name):
    if name and os.path.isfile(name):
        path = name
    else:
        cands = [os.path.join(THEME_DIR, "local", f"{name}.json"), os.path.join(THEME_DIR, f"{name}.json")]
        path = next((c for c in cands if os.path.isfile(c)), None)
        if not path:
            names = [os.path.splitext(os.path.basename(p))[0] for p in list_themes()]
            sys.exit(f"테마 '{name}'를 찾지 못했다. 가능: {', '.join(names)}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- 그리기

class Deck:
    def __init__(self, theme, meta=None, font=None, base_dir="."):
        self.t = theme
        self.colors = theme["colors"]
        self.lay = theme["layout"]
        self.sz = theme["sizes"]
        self.sty = theme["styles"]
        self.ch = theme["chrome"]
        self.fb = font or theme["fonts"]["body"]
        self.fh = font or theme["fonts"].get("head", self.fb)
        self.fa = theme["fonts"].get("accent", self.fb) if not font else font
        self.meta = meta or {}
        self.base = base_dir
        self.X = float(self.lay["x"])
        self.CW = SW - 2 * self.X
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = E(SW), E(SH)
        self.blank = self.prs.slide_layouts[6]
        self.warnings = []
        self.placeholders = 0
        self.no = 0
        self.texts = {}
        self._apply_theme()

    # --- 색·경고
    def c(self, name):
        if name is None:
            return None
        alias = {"title": "text", "band": "soft", "on_primary": None}
        if name in self.colors:
            return _hex(self.colors[name])
        if name == "on_primary":
            return "FFFFFF"
        if name in alias and alias[name]:
            return self.c(alias[name])
        return _hex(name)

    def on(self, fill):
        """채움색 위에 올릴 글자색(밝으면 본문색, 어두우면 흰색)."""
        return "FFFFFF" if luminance(self.c(fill)) < 0.6 else self.c("text")

    def tint(self, t):
        """강조색을 흰색 쪽으로 t만큼 옅게."""
        return mix(self.c("primary"), "FFFFFF", t)

    def warn(self, msg):
        self.warnings.append(f"#{self.no}: {msg}")

    def _apply_theme(self):
        """테마 색·글꼴을 프레젠테이션 테마에도 넣어 PowerPoint 색 선택기·새 도형이 같은 색을 쓰게 한다."""
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        series = [self.c(x) for x in self.colors.get("series", [])] or [self.c("primary")]
        series += [self.c("neutral")] * 6
        mapping = {"dk1": self.c("text"), "lt1": "FFFFFF", "dk2": self.c("text"), "lt2": self.c("soft"),
                   "accent1": self.c("primary"), "accent2": series[1], "accent3": series[2], "accent4": series[3],
                   "accent5": series[4], "accent6": self.c("neutral"), "hlink": self.c("primary"), "folHlink": self.c("muted")}
        master = self.prs.slide_master
        for rel in master.part.rels.values():
            if not rel.reltype.endswith("/theme"):
                continue
            part = rel.target_part
            root = etree.fromstring(part.blob)
            cs = root.find(".//a:clrScheme", ns)
            for el in cs:
                tag = etree.QName(el).localname
                if tag in mapping:
                    for child in list(el):
                        el.remove(child)
                    etree.SubElement(el, qn("a:srgbClr"), val=mapping[tag])
            for which, face in (("majorFont", self.fh), ("minorFont", self.fb)):
                f = root.find(f".//a:fontScheme/a:{which}", ns)
                f.find("a:latin", ns).set("typeface", face)
                f.find("a:ea", ns).set("typeface", face)
            part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        try:
            master.background.fill.solid()
            master.background.fill.fore_color.rgb = RGBColor.from_string(self.c("bg"))
        except Exception:
            pass

    # --- 기본 도형
    def bg(self, slide, color):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor.from_string(self.c(color))

    def box(self, slide, x, y, w, h, fill=None, line=None, lw=0.75, shape="rect", radius=None, rot=0,
            name="장식", shadow=False):
        kinds = {"rect": MSO_SHAPE.RECTANGLE, "round": MSO_SHAPE.ROUNDED_RECTANGLE, "oval": MSO_SHAPE.OVAL,
                 "diamond": MSO_SHAPE.DIAMOND, "chevron": MSO_SHAPE.CHEVRON, "home": MSO_SHAPE.PENTAGON,
                 "down": MSO_SHAPE.DOWN_ARROW, "right": MSO_SHAPE.RIGHT_ARROW}
        if shape == "round" and not radius:
            shape = "rect"
        sp = slide.shapes.add_shape(kinds[shape], E(x), E(y), E(w), E(h))
        _nostyle(sp)
        if fill:
            sp.fill.solid()
            sp.fill.fore_color.rgb = RGBColor.from_string(self.c(fill))
        else:
            sp.fill.background()
        if line:
            sp.line.color.rgb = RGBColor.from_string(self.c(line))
            sp.line.width = Pt(lw)
        else:
            sp.line.fill.background()
        if shape == "round":
            sp.adjustments[0] = min(0.5, radius / max(min(w, h), 1))
        if rot:
            sp.rotation = rot
        sp.name = name
        if shadow:
            spPr = sp._element.spPr
            eff = spPr.makeelement(qn("a:effectLst"), {})
            sh = etree.SubElement(eff, qn("a:outerShdw"), blurRad=str(12 * 12700), dist=str(2 * 12700),
                                  dir="5400000", algn="t", rotWithShape="0")
            clr = etree.SubElement(sh, qn("a:srgbClr"), val="1F2A44")
            etree.SubElement(clr, qn("a:alpha"), val="12000")
            spPr.find(qn("a:ln")).addnext(eff)
        sp.text_frame.word_wrap = True
        return sp

    def rule(self, slide, x1, y1, x2, y2, color="line", w=0.75, dash=False, arrow=False, name="장식:선"):
        cn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(x1), E(y1), E(x2), E(y2))
        _nostyle(cn)
        cn.line.color.rgb = RGBColor.from_string(self.c(color))
        cn.line.width = Pt(w)
        if dash:
            cn.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        if arrow:
            ln = cn.line._get_or_add_ln()
            ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
        cn.name = name
        return cn

    def poly(self, slide, pts, fill, name="장식"):
        fb = slide.shapes.build_freeform(E(pts[0][0]), E(pts[0][1]), scale=1.0)
        fb.add_line_segments([(E(x), E(y)) for x, y in pts[1:]], close=True)
        sp = fb.convert_to_shape()
        _nostyle(sp)
        sp.fill.solid()
        sp.fill.fore_color.rgb = RGBColor.from_string(self.c(fill))
        sp.line.fill.background()
        sp.name = name
        return sp

    # --- 글
    def _height(self, paras, size, width, ls, bold, bullet, space):
        h = 0.0
        for i, (t, lvl) in enumerate(paras):
            s = size if lvl == 0 else max(size * 0.9, 9)
            ind = s * 1.1 * (lvl + 1) if bullet else 0
            h += n_lines(strip_md(t), s, max(width - ind, s * 2), bold) * s * LH * ls
            if i:
                h += s * space
        return h

    def block_h(self, content, size, width, ls=1.15, bold=False, space=0.35):
        paras = _paras(content)
        return self._height(paras, size, width, ls, bold, isinstance(content, list), space)

    def _runs(self, p, text, size, color, bold, font, italic, emph):
        parts = re.split(r"\*\*(.+?)\*\*", text)
        for i, part in enumerate(parts):
            if not part:
                continue
            r = p.add_run()
            r.text = part
            f = r.font
            f.size = Pt(size)
            f.bold = bool(bold or i % 2 == 1)
            f.italic = bool(italic)
            col = emph if (i % 2 == 1 and emph) else color
            f.color.rgb = RGBColor.from_string(self.c(col))
            f.name = font
            _set_ea(r._r.get_or_add_rPr(), font)

    def _write(self, tf, paras, size, color, bold, align, anchor, ls, font, bullet, italic, space, emph, pad):
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = E(pad)
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        for i, (t, lvl) in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            s = size if lvl == 0 else max(size * 0.9, 9)
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            p.line_spacing = ls
            if i:
                p.space_before = Pt(s * space)
            pPr = p._p.get_or_add_pPr()
            pPr.set("eaLnBrk", "0")      # 한국어를 어절 단위로 줄바꿈
            pPr.set("latinLnBrk", "0")
            if bullet:
                ind = s * 1.1
                pPr.set("marL", str(int(ind * (lvl + 1) * 12700)))
                pPr.set("indent", str(int(-ind * 12700)))
                bc = self.c(self.sty.get("bullet_color", "primary")) if lvl == 0 else self.c("muted")
                clr = etree.SubElement(pPr, qn("a:buClr"))
                etree.SubElement(clr, qn("a:srgbClr"), val=bc)
                etree.SubElement(pPr, qn("a:buSzPct"), val="90000")
                etree.SubElement(pPr, qn("a:buFont"), typeface=font)
                etree.SubElement(pPr, qn("a:buChar"), char=(bullet if lvl == 0 else "–"))
            self._runs(p, t, s, color if lvl == 0 else "muted", bold, font, italic, emph)

    def _fit(self, paras, size, lo, w, h, ls, bold, bullet, space):
        s = size
        while self._height(paras, s, w, ls, bold, bullet, space) > h + 0.5 and s - 0.5 >= lo:
            s -= 0.5
        return s

    def _check(self, paras, size, w, h, ls, bold, bullet, space, name):
        need = self._height(paras, size, w, ls, bold, bullet, space)
        if need > h + 1:
            chars = sum(len(strip_md(t)) for t, _ in paras)
            cut = max(1, int(chars * (1 - h / need) + 0.999))
            self.warn(f"'{name}' 글이 칸을 넘친다({size:g}pt) — 약 {cut}자 줄이거나 장을 나눈다")
        for t, lvl in paras:
            for token in strip_md(t).split():
                if em(token) * size > (w - (size * 1.1 * (lvl + 1) if bullet else 0)) * 0.96:
                    self.warn(f"'{name}' 공백 없는 긴 어절 '{token[:16]}'이 음절 단위로 끊긴다 — 띄어 쓴다")
                    return need
        return need

    def _reg(self, paras):
        self.texts.setdefault(self.no, []).extend(strip_md(t) for t, _ in paras)

    def text(self, slide, box, content, size, color="text", bold=False, align="l", anchor="t", ls=1.15,
             min_size=None, font=None, bullet=None, italic=False, name="글", space=0.35, shrink=False,
             fit=True, emph="primary", pad=0):
        """글상자를 만든다. 넘치면 min_size까지 줄인다. (도형, 쓴 크기, 내용 높이)를 돌려준다."""
        x, y, w, h = box
        paras = _paras(content)
        if bullet is True:
            bullet = self.sty.get("bullet", "•")
        font = font or self.fb
        iw, ih = w - 2 * pad, h - 2 * pad
        lo = min_size if min_size is not None else max(size - 3, 10)
        s = self._fit(paras, size, lo, iw, ih, ls, bold, bullet, space) if fit else size
        need = self._check(paras, s, iw, ih, ls, bold, bullet, space, name)
        if shrink:
            h = min(h, need + 2 * pad + s * 0.3)
        tb = slide.shapes.add_textbox(E(x), E(y), E(w), E(max(h, 1)))
        self._write(tb.text_frame, paras, s, color, bold, align, anchor, ls, font, bullet, italic, space, emph, pad)
        tb.name = name
        self._reg(paras)
        return tb, s, need + 2 * pad

    def label(self, slide, x, y, w, h, content, size, fill, color=None, bold=True, align="c", shape="rect",
              radius=None, line=None, name="라벨", pad=6, min_size=None, shadow=False):
        """채운 도형 안에 글을 넣는다(알약·머리띠·배지)."""
        sp = self.box(slide, x, y, w, h, fill=fill, line=line, shape=shape, radius=radius, name=name, shadow=shadow)
        paras = _paras(content)
        lo = min_size if min_size is not None else max(size - 2.5, 9)
        k = 0.7 if shape == "oval" else 1.0        # 원 안의 글 영역은 내접 사각형(약 70%)
        s = self._fit(paras, size, lo, w * k - 2 * pad, h * k - 4, 1.0, bold, None, 0.2)
        self._check(paras, s, w * k - 2 * pad, h * k - 2, 1.0, bold, None, 0.2, name)
        col = color or (self.on(fill) if fill else self.c("text"))
        tf = sp.text_frame
        self._write(tf, paras, s, col, bold, align, "m", 1.0, self.fb, None, False, 0.2, col, 0)
        tf.margin_left = tf.margin_right = E(pad)
        tf.margin_top = tf.margin_bottom = E(1)
        self._reg(paras)
        return sp

    def value(self, slide, box, val, size, color="text", align="l", anchor="b", name="수치"):
        """'3,200억 원'의 숫자는 크게, 앞뒤 단위는 작게 쓴다."""
        x, y, w, h = box
        v = strip_md(val)
        while em(v) * size * 1.03 > w and size > 16:
            size -= 1
        m = re.match(r"^(\D*?)(\d[\d,.]*)(.*)$", v)
        tb = slide.shapes.add_textbox(E(x), E(y), E(w), E(h))
        tf = tb.text_frame
        self._write(tf, [("", 0)], size, color, True, align, anchor, 1.0, self.fh, None, False, 0, None, 0)
        p = tf.paragraphs[0]
        segs = [(m.group(1), 0.5), (m.group(2), 1.0), (m.group(3), 0.5)] if m else [(v, 1.0)]
        for seg, k in segs:
            if not seg:
                continue
            r = p.add_run()
            r.text = seg
            r.font.size = Pt(max(size * k, 10))
            r.font.bold = True
            r.font.color.rgb = RGBColor.from_string(self.c(color))
            r.font.name = self.fh
            _set_ea(r._r.get_or_add_rPr(), self.fh)
        tb.name = name
        self._reg([(v, 0)])
        return tb

    def picture(self, slide, path, x, y, w, h, mode="contain", geom=None, name="그림"):
        """그림을 상자 안에 비율 유지로 넣는다. 놓인 영역 (x, y, w, h)를 돌려준다."""
        if isinstance(path, str) and path.strip().startswith("["):
            self.placeholders += 1
            self.box(slide, x, y, w, h, fill="soft", line="line", name="자리표시")
            self.text(slide, (x + 12, y, w - 24, h), path.strip(), 13, "muted", align="c", anchor="m", name="자리표시 글")
            return x, y, w, h
        full = path if os.path.isabs(path) else os.path.join(self.base, path)
        from PIL import Image
        with Image.open(full) as im:
            iw, ih = im.size
        if mode == "cover":
            pic = slide.shapes.add_picture(full, E(x), E(y), E(w), E(h))
            br, ir = w / h, iw / ih
            if ir > br:
                c = (1 - br / ir) / 2
                pic.crop_left = pic.crop_right = c
            else:
                c = (1 - ir / br) / 2
                pic.crop_top = pic.crop_bottom = c
            px, py, pw, ph = x, y, w, h
        else:
            k = min(w / iw, h / ih)
            pw, ph = iw * k, ih * k
            px, py = x + (w - pw) / 2, y + (h - ph) / 2
            pic = slide.shapes.add_picture(full, E(px), E(py), E(pw), E(ph))
        if geom:
            pic._element.spPr.find(qn("a:prstGeom")).set("prst", geom)
        pic.name = name
        return px, py, pw, ph

    # --- 머리·바닥(크롬)
    def chrome(self, slide):
        self.bg(slide, "bg")
        X = self.X
        brand = self.meta.get("brand", "")
        band = self.ch.get("band")
        if band:
            self.box(slide, 0, 0, SW, band, fill="band", name="장식:머리띠")
            if brand:
                self.text(slide, (X, 0, 300, band), brand, 9.5, "text", bold=True, anchor="m", fit=False, name="브랜드")
            tag = self.meta.get("tagline")
            if tag:
                self.text(slide, (SW - X - 320, 0, 320, band), tag, 9.5, "faint", italic=True, align="r", anchor="m",
                          fit=False, font=self.fa, name="태그라인")
        elif brand:
            self.text(slide, (SW - X - 260, 24, 260, 14), brand, 9.5, "text", bold=True, align="r", fit=False, name="브랜드")
        fr = self.ch.get("footer_rule")
        if fr:
            self.rule(slide, X, fr, SW - X, fr, "text", 1.0, name="장식:바닥선")
            tx = SW - X
            self.poly(slide, [(tx - 112, fr), (tx - 100, fr - 11), (tx, fr - 11), (tx, fr)], "text", name="장식:바닥탭")

    def page_no(self, slide):
        fr = self.ch.get("footer_rule")
        if fr:
            self.text(slide, (SW - self.X - 96, fr - 11, 90, 11), f"{self.no:02d}", 8, "FFFFFF", bold=True,
                      align="r", anchor="m", fit=False, name="쪽번호")
        else:
            self.text(slide, (SW - self.X - 60, SH - 26, 60, 12), f"{self.no:02d}", 9, "faint", align="r",
                      fit=False, name="쪽번호")
        self.texts[self.no].pop()      # 쪽번호는 검증 대상이 아니다

    def header(self, slide, s):
        X, CW = self.X, self.CW
        ts, lsz, es = self.sz["title"], self.sz["lead"], self.sz["eyebrow"]
        y = float(self.lay["title_y"])
        if s.get("eyebrow"):
            self.text(slide, (X, y - es * 1.9, CW * 0.7, es * 1.45), s["eyebrow"], es, "primary", bold=True,
                      fit=False, name="머리말")
        title, lead = s.get("title", ""), s.get("lead")
        tw = em(strip_md(title)) * ts * 1.03
        if lead and self.ch.get("header") == "split" and tw <= CW * 0.5:
            _, _, th = self.text(slide, (X, y, tw / 0.95 + 16, ts * LH + 4), title, ts, "title", bold=True, ls=1.0,
                                 fit=False, font=self.fh, name="제목")
            lx = X + max(tw / 0.95 + 40, CW * 0.36)
            _, _, lh = self.text(slide, (lx, y + 1, X + CW - lx, lsz * LH * 1.15 * 3 + 2), lead, lsz, "muted",
                                 min_size=lsz - 1, shrink=True, name="설명")
            bottom = y + max(th, lh)
        else:
            _, _, th = self.text(slide, (X, y, CW, ts * LH * 2 + 6), title, ts, "title", bold=True, ls=1.0,
                                 min_size=ts - 4, shrink=True, font=self.fh, name="제목")
            bottom = y + th
            if lead:
                _, _, lh = self.text(slide, (X, bottom + 6, CW, lsz * LH * 1.15 * 2 + 4), lead, lsz, "muted",
                                     min_size=lsz - 1, shrink=True, name="설명")
                bottom += 6 + lh
        return bottom + float(self.lay.get("gap", 24))

    def area(self, top, s, reserve=0.0):
        bottom = float(self.lay["bottom"]) - (18 if s.get("source") else 0) - reserve
        return self.X, top, self.CW, bottom - top

    def callout_h(self, text, w):
        return max(42.0, self.block_h(text, 14, w - 56, 1.1, True) + 22)

    def callout(self, slide, x, y, w, text):
        h = self.callout_h(text, w)
        solid = self.sty.get("callout") == "solid"
        fill = "primary" if solid else "soft"
        col = self.on("primary") if solid else self.c("text")
        self.box(slide, x, y, w, h, fill=fill, shape="round", radius=self.sty.get("radius"), name="결론")
        self.text(slide, (x + 28, y, w - 56, h), text, 14, col, bold=True, align="c", anchor="m", min_size=12,
                  ls=1.1, emph=(col if solid else "primary"), name="결론 글")
        return h

    def finish(self, slide, s, numbered=True):
        if s.get("source"):
            src = str(s["source"])
            if not src.startswith(("출처", "자료", "주:", "※")):
                src = "출처: " + src
            self.text(slide, (self.X, float(self.lay["bottom"]) - 13, self.CW, 13), src, 9, "muted", min_size=8,
                      name="출처")
        if s.get("notes"):
            slide.notes_slide.notes_text_frame.text = s["notes"]
        if numbered:
            self.page_no(slide)

    # --- 슬라이드 추가
    def add(self, s):
        self.no += 1
        self.texts[self.no] = []
        slide = self.prs.slides.add_slide(self.blank)
        kind = s["type"]
        if kind in ("cover", "section", "closing", "statement", "toc"):
            getattr(self, "p_" + kind)(slide, s)
            self.finish(slide, s, numbered=kind in ("statement", "toc"))
        else:
            self.chrome(slide)
            top = self.header(slide, s)
            getattr(self, "p_" + kind)(slide, s, top)
            self.finish(slide, s)
        return slide

    # ============================================================ 패턴

    def dots(self, slide, x, y, cols, rows, gap, focal=None, base="line", r0=1.6, name="장식:점"):
        """점 격자 모티프. focal(열, 행)에 가까울수록 점이 커지고 진해진다."""
        for i in range(cols):
            for j in range(rows):
                if focal:
                    d = math.hypot(i - focal[0], j - focal[1])
                    if d < 0.5:
                        r, col = 6.0, "primary"
                    elif d < 1.6:
                        r, col = 3.6, "text"
                    elif d < 2.7:
                        r, col = 2.6, "neutral"
                    else:
                        r, col = r0, base
                else:
                    r, col = r0, base
                cx, cy = x + i * gap, y + j * gap
                self.box(slide, cx - r, cy - r, 2 * r, 2 * r, fill=col, shape="oval", name=name)

    def p_cover(self, slide, s):
        X = self.X
        title = s.get("title") or self.meta.get("title", "")
        who = " | ".join(v for v in (s.get("org") or self.meta.get("org"), s.get("presenter") or self.meta.get("presenter")) if v)
        date = s.get("date") or self.meta.get("date")
        contact = s.get("contact") or self.meta.get("contact") or []
        if self.sty["cover"] == "dots":
            self.bg(slide, "bg")
            brand = self.meta.get("brand")
            if brand:
                self.text(slide, (SW - X - 260, 24, 260, 14), brand, 9.5, "text", bold=True, align="r", fit=False, name="브랜드")
            if date:
                self.text(slide, (X, 44, 300, 16), date, 11, "primary", bold=True, fit=False, name="날짜")
            y = 150.0
            if s.get("eyebrow"):
                self.text(slide, (X, y, 520, 20), s["eyebrow"], 13, "primary", bold=True, fit=False, name="머리말")
                y += 26
            tw = 520 if not s.get("image") else 470
            _, _, th = self.text(slide, (X, y, tw, 40 * LH * 3), title, 40, "title", bold=True, ls=1.05, min_size=28,
                                 shrink=True, font=self.fh, name="제목")
            y += th + 14
            if s.get("subtitle"):
                self.text(slide, (X, y, tw, 70), s["subtitle"], 16, "muted", min_size=13, shrink=True, name="부제")
            if who:
                self.text(slide, (X, 452, 520, 18), who, 12.5, "text", bold=True, fit=False, name="발표자")
            if contact:
                line = "   ".join(f"**{a}** {b}" for a, b in contact)
                self.text(slide, (X, 476, 600, 16), line, 10.5, "muted", emph="primary", name="연락처")
            if s.get("image"):
                self.picture(slide, s["image"], 560, 110, 340, 320)
            else:
                self.dots(slide, 622, 128, 9, 9, 32, focal=(5, 4))
        else:
            self.chrome(slide)
            y = 140.0
            if s.get("eyebrow"):
                self.text(slide, (80, y, SW - 160, 20), s["eyebrow"], 13, "muted", bold=True, align="c", fit=False, name="머리말")
                y += 30
            _, _, th = self.text(slide, (80, y, SW - 160, 42 * LH * 2.2), title, 42, "title", bold=True, align="c",
                                 ls=1.08, min_size=30, shrink=True, font=self.fh, name="제목")
            y += th + 16
            if s.get("subtitle"):
                _, _, sh_ = self.text(slide, (120, y, SW - 240, 50), s["subtitle"], 16, "muted", align="c",
                                      min_size=13, shrink=True, name="부제")
                y += sh_ + 14
            if who:
                self.text(slide, (120, y, SW - 240, 22), f"**발표자**  {who}", 14, "text", align="c",
                          emph="title", name="발표자")
            if s.get("image"):
                self.warn("가운데 정렬 표지에는 그림을 넣지 않는다 — image는 무시하지 않고 오른쪽 아래 작게 넣었다")
                self.picture(slide, s["image"], SW - X - 160, 300, 150, 120)
            fr = self.ch.get("footer_rule") or (SH - 40)
            if date:
                self.text(slide, (X, fr - 26, 300, 16), date, 12, "text", fit=False, name="날짜")
            if contact:
                line = "   ".join(f"**{a}** {b}" for a, b in contact)
                self.text(slide, (X + 200, fr - 26, SW - 2 * X - 330, 16), line, 10.5, "muted", align="r",
                          emph="text", name="연락처")

    def p_section(self, slide, s):
        X = self.X
        no = s.get("no")
        if self.sty["section"] == "full":
            self.bg(slide, "primary")
            self.dots(slide, 34, 30, 15, 8, 64, base=self.tint(0.32), r0=1.5)
            y = 196.0
            if no:
                lab = f"Section. {no}"
                lw = em(lab) * 12 + 18
                self.label(slide, (SW - lw) / 2, y, lw, 20, lab, 12, "FFFFFF", color=self.c("primary"), name="간지 번호")
                y += 34
            _, _, th = self.text(slide, (80, y, SW - 160, 40 * LH * 2), s["title"], 40, "FFFFFF", bold=True,
                                 align="c", min_size=30, shrink=True, font=self.fh, emph="FFFFFF", name="제목")
            y += th + 14
            if s.get("desc"):
                _, _, dh = self.text(slide, (120, y, SW - 240, 44), s["desc"], 15, self.tint(0.78), align="c",
                                     min_size=13, shrink=True, name="설명")
                y += dh + 10
            if s.get("items"):
                self.text(slide, (120, y + 4, SW - 240, 40), "   ·   ".join(map(str, s["items"])), 12.5,
                          self.tint(0.7), align="c", name="세부")
        else:
            self.chrome(slide)
            y = 140.0
            if no:
                self.text(slide, (X, y, 300, 80), str(no), 64, "primary", bold=True, ls=1.0, fit=False, font=self.fh,
                          name="간지 번호")
                y += 88
            _, _, th = self.text(slide, (X, y, self.CW * 0.8, 34 * LH * 2), s["title"], 34, "title", bold=True,
                                 min_size=26, shrink=True, font=self.fh, name="제목")
            y += th + 10
            if s.get("desc"):
                _, _, dh = self.text(slide, (X, y, self.CW * 0.7, 50), s["desc"], 15, "muted", min_size=13,
                                     shrink=True, name="설명")
                y += dh + 12
            if s.get("items"):
                self.text(slide, (X, y, self.CW * 0.7, 110), list(map(str, s["items"])), 13.5, "text", bullet=True,
                          name="세부")
        self.section = (no, s["title"])

    def p_toc(self, slide, s):
        X = self.X
        items = [it if isinstance(it, dict) else {"title": it} for it in s["items"]]
        n = len(items)
        title = s.get("title") or ("Contents" if self.sty["toc"] == "list" else "목차")
        if self.sty["toc"] == "list":
            self.bg(slide, "bg")
            brand = self.meta.get("brand")
            if brand:
                self.text(slide, (SW - X - 260, 24, 260, 14), brand, 9.5, "text", bold=True, align="r", fit=False, name="브랜드")
            self.text(slide, (X, 64, 340, 44), title, 30, "title", bold=True, font=self.fh, name="제목")
            self.dots(slide, X + 6, 330, 6, 5, 28, focal=(1, 4))
            x0 = SW * 0.44
            w0 = SW - X - x0
            rh = min(64.0, 420.0 / n)
            y0 = (SH - rh * n) / 2
            for i, it in enumerate(items):
                ry = y0 + i * rh
                self.text(slide, (x0, ry, 40, rh), f"{i + 1:02d}", 15, "primary", bold=True, anchor="m", fit=False, name="번호")
                self.text(slide, (x0 + 46, ry, w0 * 0.5 - 46, rh), it["title"], 15.5, "title", bold=True, anchor="m",
                          min_size=12.5, name="목차 항목")
                if it.get("sub"):
                    sub = it["sub"] if isinstance(it["sub"], list) else [it["sub"]]
                    self.text(slide, (x0 + w0 * 0.52, ry, w0 * 0.48, rh), "\n".join(f"- {t}" for t in sub), 10.5,
                              "muted", anchor="m", ls=1.05, space=0.1, min_size=9, name="목차 세부")
                self.rule(slide, x0, ry + rh, x0 + w0, ry + rh, "line", 0.75)
        else:
            self.chrome(slide)
            self.text(slide, (X + 20, 220, 260, 50), title, 30, "title", bold=True, font=self.fh, name="제목")
            x0 = SW * 0.4
            colw = (SW - X - x0 - 30) / 2
            rows = math.ceil(n / 2)
            rh = min(66.0, 300.0 / rows)
            y0 = (SH - rh * rows) / 2 + 6
            for i, it in enumerate(items):
                cx = x0 + (i // rows) * (colw + 30)
                ry = y0 + (i % rows) * rh
                self.text(slide, (cx, ry, 34, rh - 8), f"{i + 1:02d}", 13, "faint", anchor="b", fit=False, name="번호")
                lab = it["title"] + (f"\n{it['sub'] if isinstance(it.get('sub'), str) else ' · '.join(it['sub'])}"
                                     if it.get("sub") else "")
                self.text(slide, (cx + 36, ry, colw - 36, rh - 8), lab, 16, "title", anchor="b", ls=1.05,
                          min_size=12, name="목차 항목")
                self.rule(slide, cx, ry + rh - 2, cx + colw, ry + rh - 2, "line", 0.75)

    def p_statement(self, slide, s):
        self.chrome(slide)
        y0 = 150.0
        if s.get("eyebrow"):                     # 공통 선택 키 — 강조선 위 가운데
            self.text(slide, (100, y0 - 34, SW - 200, 20), s["eyebrow"], self.sz["eyebrow"], "primary", bold=True,
                      align="c", fit=False, name="머리말")
        self.box(slide, SW / 2 - 22, y0, 44, 4, fill="primary", name="장식:강조선")
        _, _, th = self.text(slide, (100, y0 + 26, SW - 200, 34 * LH * 3), s["title"], 34, "title", bold=True,
                             align="c", ls=1.12, min_size=24, shrink=True, font=self.fh, name="메시지")
        if s.get("sub"):
            self.text(slide, (140, y0 + 40 + th, SW - 280, 60), s["sub"], 16, "muted", align="c", min_size=13,
                      name="보조")

    def p_closing(self, slide, s):
        title = s.get("title") or "감사합니다"
        contact = s.get("contact") or self.meta.get("contact") or []
        line = "    ".join(f"**{a}**  {b}" for a, b in contact)
        if self.sty.get("closing", "full") == "full":
            self.bg(slide, "primary")
            self.dots(slide, 34, 30, 15, 8, 64, base=self.tint(0.32), r0=1.5)
            _, _, th = self.text(slide, (80, 200, SW - 160, 44 * LH * 2), title, 44, "FFFFFF", bold=True, align="c",
                                 min_size=30, shrink=True, font=self.fh, emph="FFFFFF", name="제목")
            y = 200 + th + 14
            if s.get("sub"):
                _, _, sh_ = self.text(slide, (120, y, SW - 240, 48), s["sub"], 16, self.tint(0.8), align="c",
                                      min_size=13, shrink=True, name="보조")
                y += sh_ + 18
            if line:
                self.text(slide, (100, y, SW - 200, 20), line, 12, self.tint(0.85), align="c", emph="FFFFFF", name="연락처")
        else:
            self.chrome(slide)
            _, _, th = self.text(slide, (80, 190, SW - 160, 44 * LH * 2), title, 44, "title", bold=True, align="c",
                                 min_size=30, shrink=True, font=self.fh, name="제목")
            y = 190 + th + 14
            if s.get("sub"):
                _, _, sh_ = self.text(slide, (120, y, SW - 240, 48), s["sub"], 16, "muted", align="c", min_size=13,
                                      shrink=True, name="보조")
                y += sh_ + 18
            if line:
                self.text(slide, (100, y, SW - 200, 20), line, 12, "muted", align="c", emph="text", name="연락처")

    def p_bullets(self, slide, s, top):
        cb = s.get("callout")
        x, y, w, h = self.area(top, s, self.callout_h(cb, self.CW) + 18 if cb else 0)
        img = s.get("image")
        tw = w * 0.5 if img else w
        self.text(slide, (x, y, tw, h), s["bullets"], self.sz["body"], "text", bullet=True, ls=1.18, space=0.7,
                  min_size=13, name="본문")
        if img:
            ix, iw = x + w * 0.54, w * 0.46
            cap = s.get("image_caption")
            px, py, pw, ph = self.picture(slide, img, ix, y, iw, h - (24 if cap else 0))
            if cap:
                self.text(slide, (ix, py + ph + 6, iw, 16), cap, 11, "muted", align="c", name="그림 설명")
        if cb:
            self.callout(slide, x, y + h + 18, w, cb)

    def _group_y(self, y, h, need):
        return y + max(0.0, (h - need) * 0.38)

    def p_cards(self, slide, s, top):
        items = s["items"]
        n = len(items)
        cols = n if n <= 4 else 3
        nrow = math.ceil(n / cols)
        cb = s.get("callout")
        conv = bool(s.get("converge") and cb and nrow == 1)
        x, y, w, h = self.area(top, s)
        gap = 18.0
        cw = (w - gap * (cols - 1)) / cols
        cbh = self.callout_h(cb, w) if cb else 0
        link = 40.0 if conv else (18.0 if cb else 0)
        avail = (h - cbh - link - gap * (nrow - 1)) / nrow
        pill = self.sty["card"] == "pill"
        head = 32.0 if pill else 34.0
        pad = 16.0 if pill else 12.0
        top_off = (14 + head + 14) if pill else (head + 12)
        val_h = 40.0 if any(it.get("value") for it in items) else 0
        bw = cw - 2 * pad
        bodies = [it.get("body") for it in items]
        lim = avail - top_off - val_h - pad
        bs = self.sz["small"] + 0.5
        while bs > 11 and max((self.block_h(b, bs, bw) for b in bodies if b), default=0) > lim:
            bs -= 0.5
        need = max((self.block_h(b, bs, bw) for b in bodies if b), default=0)
        ch_ = min(avail, max(top_off + val_h + need + pad + 4, 120.0))
        group = nrow * ch_ + gap * (nrow - 1) + link + cbh
        y0 = self._group_y(y, h, group)
        r = self.sty.get("radius")
        for i, it in enumerate(items):
            cx = x + (i % cols) * (cw + gap)
            cy = y0 + (i // cols) * (ch_ + gap)
            ttl = f"{it['tag']}  {it['title']}" if it.get("tag") else it["title"]
            if pill:
                self.box(slide, cx, cy, cw, ch_, fill="surface", line="line", shape="round", radius=r, name="카드")
                self.label(slide, cx + pad, cy + 14, cw - 2 * pad, head, ttl, 13.5, "primary", shape="round",
                           radius=head / 2, name="카드 제목")
            else:
                self.label(slide, cx, cy, cw, head, ttl, 13.5, "primary", align="l", pad=12, name="카드 제목")
                self.rule(slide, cx, cy + ch_, cx + cw, cy + ch_, "faint", 0.75)
            by = cy + top_off
            if it.get("value"):
                self.value(slide, (cx + pad, by, bw, 34), it["value"], 26, "primary", align="c" if pill else "l",
                           anchor="m", name="카드 수치")
            by += val_h             # 수치가 없는 카드도 본문 시작선을 맞춘다
            b = it.get("body")
            if b:
                center = pill and isinstance(b, str)
                self.text(slide, (cx + pad, by, bw, cy + ch_ - pad - by + 2), b, bs, "text",
                          bullet=isinstance(b, list), align="c" if center else "l", fit=False, name="카드 본문")
        cy_end = y0 + nrow * ch_ + gap * (nrow - 1)
        if conv:
            ym = cy_end + 16
            centers = [x + i * (cw + gap) + cw / 2 for i in range(n)]
            for c in centers:
                self.box(slide, c - 3, cy_end - 3, 6, 6, fill="primary", shape="oval", name="장식:점")
                self.rule(slide, c, cy_end, c, ym, "primary", 1.25)
            self.rule(slide, centers[0], ym, centers[-1], ym, "primary", 1.25)
            self.rule(slide, x + w / 2, ym, x + w / 2, cy_end + link - 2, "primary", 1.25, arrow=True)
        if cb:
            self.callout(slide, x, cy_end + link, w, cb)

    def p_radial(self, slide, s, top):
        items = s["items"]
        n = len(items)
        cb = s.get("callout")
        x, y, w, h = self.area(top, s, self.callout_h(cb, self.CW) + 18 if cb else 0)
        D = min(h * 0.8, 196.0)
        cx, cy = x + w / 2, y + h / 2
        self.box(slide, cx - D / 2 - 14, cy - D / 2 - 14, D + 28, D + 28, fill=self.tint(0.9), shape="oval", name="장식:고리")
        self.box(slide, cx - D / 2, cy - D / 2, D, D, fill="primary", shape="oval", name="중심")
        _, _, th = self.text(slide, (cx - D * 0.4, cy - D * 0.4, D * 0.8, D * 0.8), s["center"], 18,
                             self.on("primary"), bold=True, align="c", anchor="m", min_size=13,
                             emph=self.on("primary"), name="중심 개념", shrink=False)
        if s.get("center_sub"):
            self.text(slide, (cx - D * 0.38, cy + D * 0.14, D * 0.76, D * 0.3), s["center_sub"], 11.5,
                      self.tint(0.8) if self.on("primary") == "FFFFFF" else "muted", align="c", min_size=9.5,
                      name="중심 설명")
        left = math.ceil(n / 2)
        cw = (w - D - 28 - 2 * 40) / 2
        for side, group in ((0, items[:left]), (1, items[left:])):
            k = len(group)
            gap = 14.0
            chh = min(104.0, (h - gap * (k - 1)) / k)
            gy = cy - (chh * k + gap * (k - 1)) / 2
            bx = x if side == 0 else x + w - cw
            for j, it in enumerate(group):
                by = gy + j * (chh + gap)
                card = self.sty["card"] == "pill"
                self.box(slide, bx, by, cw, chh, fill="surface" if card else "soft", line="line" if card else None,
                         shape="round", radius=self.sty.get("radius"), name="요인")
                _, _, tth = self.text(slide, (bx + 14, by + 10, cw - 28, 20), it["title"], 14, "title", bold=True,
                                      min_size=12, shrink=True, name="요인 제목")
                if it.get("body"):
                    self.text(slide, (bx + 14, by + 14 + tth, cw - 28, chh - 24 - tth), it["body"], 12, "muted",
                              min_size=10.5, name="요인 설명")
                ax = bx + cw if side == 0 else bx
                ay = by + chh / 2
                dx, dy = ax - cx, ay - cy
                d = math.hypot(dx, dy) or 1
                ex, ey = cx + dx / d * (D / 2 + 14), cy + dy / d * (D / 2 + 14)
                self.rule(slide, ax, ay, ex, ey, "neutral", 1.0)
                self.box(slide, ex - 3.5, ey - 3.5, 7, 7, fill="primary", shape="oval", name="장식:점")
        if cb:
            self.callout(slide, x, y + h + 18, w, cb)

    def p_kpi(self, slide, s, top):
        items = s["items"]
        n = len(items)
        cb = s.get("callout")
        x, y, w, h = self.area(top, s)
        gap = 18.0
        cw = (w - gap * (n - 1)) / n
        cbh = self.callout_h(cb, w) if cb else 0
        avail = h - cbh - (20 if cb else 0)
        descs = [it.get("desc") for it in items]
        dh = max((self.block_h(d, 12, cw - 36) for d in descs if d), default=0)
        bar = self.sty["kpi"] == "bar"
        ch_ = min(avail, max(150.0, 50 + dh + 70 + (14 if any("percent" in it for it in items) else 0)))
        y0 = self._group_y(y, h, ch_ + (20 + cbh if cb else 0))
        for i, it in enumerate(items):
            cx = x + i * (cw + gap)
            pct = it.get("percent")
            if bar:
                self.box(slide, cx, y0, cw, ch_, fill="surface", line="line", shape="round",
                         radius=self.sty.get("radius"), name="수치 카드")
                self.box(slide, cx + 18, y0 + 20, 3, 15, fill="primary", name="장식:막대")
                self.text(slide, (cx + 28, y0 + 17, cw - 46, 22), it["label"], 13.5, "title", bold=True,
                          min_size=11.5, name="수치 이름")
                if it.get("desc"):
                    self.text(slide, (cx + 18, y0 + 46, cw - 36, ch_ - 46 - 64), it["desc"], 12, "muted",
                              min_size=10.5, name="수치 설명")
                vy = y0 + ch_ - 60 - (10 if pct is not None else 0)
                self.value(slide, (cx + 18, vy, cw - 36, 46), it["value"], 32, "title", align="r", name="수치")
            else:
                self.box(slide, cx, y0, cw, ch_, fill="soft", name="수치 카드")
                self.value(slide, (cx + 18, y0 + 16, cw - 36, 44), it["value"], 30, "title", align="l", anchor="m",
                           name="수치")
                self.text(slide, (cx + 18, y0 + 68, cw - 36, 22), it["label"], 14, "title", bold=True,
                          min_size=12, name="수치 이름")
                if it.get("desc"):
                    self.text(slide, (cx + 18, y0 + 94, cw - 36, ch_ - 94 - 18), it["desc"], 12, "muted",
                              min_size=10.5, name="수치 설명")
            if pct is not None:
                p = max(0.0, min(1.0, float(pct) / (100.0 if float(pct) > 1 else 1.0)))
                by = y0 + ch_ - 16
                self.box(slide, cx + 18, by, cw - 36, 5, fill=self.tint(0.85), name="장식:막대 바탕")
                if p > 0:
                    self.box(slide, cx + 18, by, (cw - 36) * p, 5, fill="primary", name="장식:막대 값")
        if cb:
            self.callout(slide, x, y0 + ch_ + 20, w, cb)

    def native_chart(self, slide, spec, x, y, w, h):
        kind = spec.get("kind", "column")
        cats = spec["categories"]
        series = spec["series"]
        fmt = spec.get("number_format", "#,##0.##")
        cd = CategoryChartData(number_format=fmt)
        cd.categories = cats
        for se in series:
            cd.add_series(se.get("name", ""), se["values"])
        gf = slide.shapes.add_chart(CHART_KINDS[kind], E(x), E(y), E(w), E(h), cd)
        gf.name = "차트"
        chart = gf.chart
        chart.has_title = False
        chart.font.size = Pt(12)
        chart.font.name = self.fb
        chart.font.color.rgb = RGBColor.from_string(self.c("text"))
        _set_ea(chart.font._rPr, self.fb)
        cs = chart._chartSpace
        sp = cs.makeelement(qn("c:spPr"), {})
        etree.SubElement(sp, qn("a:noFill"))
        ln = etree.SubElement(sp, qn("a:ln"))
        etree.SubElement(ln, qn("a:noFill"))
        txpr = cs.find(qn("c:txPr"))
        txpr.addprevious(sp) if txpr is not None else cs.find(qn("c:chart")).addnext(sp)
        palette = [self.c(c) for c in self.colors.get("series", [])] or [self.c("primary")]
        multi = len(series) > 1
        round_ = kind in ("doughnut", "pie")
        chart.has_legend = multi or round_
        if chart.has_legend:
            chart.legend.position = XL_LEGEND_POSITION.RIGHT if round_ else XL_LEGEND_POSITION.TOP
            chart.legend.include_in_layout = False
            chart.legend.font.size = Pt(11.5)
        plot = chart.plots[0]
        labels = spec.get("labels", True)
        hl = spec.get("highlight")
        if isinstance(hl, str) and hl in cats:
            hl = cats.index(hl) + 1
        if round_:
            ser = plot.series[0]
            for i, point in enumerate(ser.points):
                point.format.fill.solid()
                point.format.fill.fore_color.rgb = RGBColor.from_string(palette[i % len(palette)])
                point.format.line.color.rgb = RGBColor.from_string("FFFFFF")
            if labels:
                plot.has_data_labels = True
                dl = plot.data_labels
                pct = spec.get("percent", True)
                dl.show_percentage = bool(pct)
                dl.show_value = not pct
                dl.number_format = "0%" if pct else fmt
                dl.number_format_is_linked = False
                dl.font.size = Pt(12)
                dl.font.bold = True
            if kind == "doughnut":
                hole = plot._element.find(qn("c:holeSize"))
                if hole is not None:
                    hole.set("val", "58")
            return chart
        if kind != "line":
            plot.gap_width = 70
            if kind == "stacked":
                plot.overlap = 100
        for i, ser in enumerate(plot.series):
            col = palette[i % len(palette)]
            if kind == "line":
                ser.format.line.color.rgb = RGBColor.from_string(col)
                ser.format.line.width = Pt(2.5)
                ser.smooth = False
                ser.marker.style = XL_MARKER_STYLE.CIRCLE
                ser.marker.size = 8
                ser.marker.format.fill.solid()
                ser.marker.format.fill.fore_color.rgb = RGBColor.from_string(col)
                ser.marker.format.line.color.rgb = RGBColor.from_string("FFFFFF")
            else:
                ser.format.fill.solid()
                ser.format.fill.fore_color.rgb = RGBColor.from_string(col)
                if not multi and hl:
                    for j, point in enumerate(ser.points):
                        point.format.fill.solid()
                        point.format.fill.fore_color.rgb = RGBColor.from_string(
                            col if j + 1 == int(hl) else mix(col, "FFFFFF", 0.6))
        if labels:
            plot.has_data_labels = True
            dl = plot.data_labels
            dl.number_format = fmt
            dl.number_format_is_linked = False
            dl.font.size = Pt(12)
            dl.font.bold = True
            if kind == "stacked":
                dl.position = XL_LABEL_POSITION.CENTER
            else:
                dl.position = XL_LABEL_POSITION.ABOVE if kind == "line" else XL_LABEL_POSITION.OUTSIDE_END
        va = chart.value_axis
        va.has_major_gridlines = not labels
        if not labels:
            va.major_gridlines.format.line.color.rgb = RGBColor.from_string(self.c("line"))
        va.visible = not labels
        va.tick_labels.font.size = Pt(11)
        ca = chart.category_axis
        if kind == "bar":                        # 가로 막대는 첫 항목이 아래에 그려진다 — 표·글 순서대로 위에서부터
            ca.reverse_order = True
        ca.format.line.color.rgb = RGBColor.from_string(self.c("line"))
        ca.major_tick_mark = XL_TICK_MARK.NONE
        ca.tick_labels.font.size = Pt(12)
        return chart

    def p_chart(self, slide, s, top):
        cb = s.get("callout")
        x, y, w, h = self.area(top, s, self.callout_h(cb, self.CW) + 18 if cb else 0)
        pts = s.get("points")
        cw = w * 0.6 if pts else w
        cap = s.get("caption")
        cy = y
        if cap:
            _, _, chh = self.text(slide, (x, y, cw, 36), cap, 14, "title", bold=True, min_size=12, shrink=True,
                                  name="그래프 결론")
            cy += chh + 6
        spec = s.get("chart")
        if spec:
            if spec.get("unit"):
                self.text(slide, (x, cy, cw, 14), f"(단위: {spec['unit']})", 10, "muted", align="r", fit=False,
                          name="단위")
                cy += 14
            self.native_chart(slide, spec, x, cy, cw, y + h - cy)
            self.texts[self.no] += [str(c) for c in spec["categories"]] + [se.get("name", "") for se in spec["series"]]
        else:
            self.picture(slide, s["image"], x, cy, cw, y + h - cy)
        if pts:
            self.text(slide, (x + cw + 28, y + 6, w - cw - 28, h - 6), pts, 14, "text", bullet=True, ls=1.18,
                      space=0.7, min_size=12, name="요점")
        if cb:
            self.callout(slide, x, y + h + 18, w, cb)

    def p_tam(self, slide, s, top):
        cb = s.get("callout")
        x, y, w, h = self.area(top, s, self.callout_h(cb, self.CW) + 18 if cb else 0)
        D1 = min(h, w * 0.44)
        D2, D3 = D1 * 0.68, D1 * 0.38
        lx = x + D1 / 2 + 4
        by = y + (h + D1) / 2
        names = ["TAM", "SAM", "SOM"]
        kinds = ["전체 시장", "유효 시장", "목표 시장"]
        fills = [self.tint(0.88), self.tint(0.55), self.c("primary")]
        for d, f in zip((D1, D2, D3), fills):
            self.box(slide, lx - d / 2, by - d, d, d, fill=f, line=self.tint(0.6) if d == D1 else None, shape="oval",
                     name="시장 원")
        for i, (top_, nxt) in enumerate(((by - D1, by - D2), (by - D2, by - D3))):
            cyy = (top_ + nxt) / 2
            self.text(slide, (lx - 60, cyy - 10, 120, 20), names[i], 14, "primary" if i == 0 else self.on(fills[1]),
                      bold=True, align="c", anchor="m", fit=False, name="시장 층위")
        self.text(slide, (lx - D3 / 2, by - D3, D3, D3), names[2], 14, self.on("primary"), bold=True, align="c",
                  anchor="m", fit=False, name="시장 층위")
        rx = x + D1 + 44
        rw = x + w - rx
        rh = h / 3
        for i, it in enumerate(s["items"]):
            ry = y + i * rh
            self.box(slide, rx, ry + 16, 12, 12, fill=fills[i], line=self.tint(0.6) if i == 0 else None,
                     shape="oval", name="장식:표식")
            lab = it.get("label") or f"{names[i]} · {kinds[i]}"
            self.text(slide, (rx + 22, ry + 12, rw - 22, 20), lab, 13.5, "title", bold=True, min_size=11.5, name="층위 이름")
            self.value(slide, (rx + 22, ry + 34, rw - 22, 32), it["value"], 24, "primary", anchor="m", name="시장 규모")
            if it.get("desc"):
                self.text(slide, (rx + 22, ry + 68, rw - 22, rh - 74), it["desc"], 11.5, "muted", min_size=10,
                          name="산정 근거")
            if i < 2:
                self.rule(slide, rx, ry + rh, x + w, ry + rh, "line", 0.75)
        if not s.get("source"):
            self.warn("시장 규모에 출처(source)가 없다 — 층위마다 산식·출처를 단다")
        if cb:
            self.callout(slide, x, y + h + 18, w, cb)

    def _columns_head(self, slide, x, y, w, title, ours):
        fill = "primary" if ours else "neutral"
        self.label(slide, x, y, w, 36, title, 14, fill, shape="round", radius=self.sty.get("radius"), name="비교 머리")

    def p_compare(self, slide, s, top):
        cb = s.get("callout")
        x, y, w, h = self.area(top, s, self.callout_h(cb, self.CW) + 18 if cb else 0)
        L, R = s["left"], s["right"]
        crit = s.get("criteria")
        ours = s.get("ours", "right")
        li, ri = L.get("items", []), R.get("items", [])
        n = max(len(li), len(ri), len(crit or []))
        if crit and not (len(li) == len(ri) == len(crit)):
            self.warn(f"비교 기준 {len(crit)}개와 항목 수(왼쪽 {len(li)}·오른쪽 {len(ri)})가 다르다 — 빈칸으로 둔다")
        gap = 10.0
        mw = w * 0.17 if crit else 0
        colw = (w - mw - gap * (2 if crit else 1)) / 2
        lx = x
        mx = x + colw + gap
        rx = (mx + mw + gap) if crit else (x + colw + gap)
        self._columns_head(slide, lx, y, colw, L.get("title", "기존"), ours == "left")
        self._columns_head(slide, rx, y, colw, R.get("title", "자사"), ours == "right")
        if crit:
            self.label(slide, mx, y, mw, 36, "구분", 13, "soft", shape="round", radius=self.sty.get("radius"), name="기준 머리")
        ry0 = y + 44
        size = 13.0
        cells = [(li, colw), (ri, colw)]
        while size > 11 and any(self.block_h(t, size, cw - 20) > (h - 44) / n - 8 for col, cw in cells for t in col):
            size -= 0.5
        rh_need = max([self.block_h(t, size, cw - 20) for col, cw in cells for t in col] + [14]) + 16
        rh = min((h - 44) / n, max(rh_need, 34.0))
        for k in range(n):
            ry = ry0 + k * rh
            for col, cx in ((li, lx), (ri, rx)):
                if k < len(col):
                    bold = (cx == rx and ours == "right") or (cx == lx and ours == "left")
                    self.text(slide, (cx + 10, ry, colw - 20, rh), col[k], size, "text", bold=bold, align="c",
                              anchor="m", fit=False, name="비교 칸")
                self.rule(slide, cx, ry + rh, cx + colw, ry + rh, "line", 0.75)
            if crit and k < len(crit):
                self.label(slide, mx, ry + 4, mw, rh - 8, crit[k], 12, "soft", radius=None, name="비교 기준")
        if cb:
            self.callout(slide, x, y + h + 18, w, cb)

    def p_before_after(self, slide, s, top):
        cb = s.get("callout")
        x, y, w, h = self.area(top, s, self.callout_h(cb, self.CW) + 18 if cb else 0)
        aw = 46.0
        colw = (w - aw - 24) / 2
        for side, key, cx in ((0, "before", x), (1, "after", x + colw + aw + 24)):
            part = s[key]
            ttl = part.get("title", "Before · 기존" if side == 0 else "After · 도입 후")
            self._columns_head(slide, cx, y, colw, ttl, side == 1)
            body = part.get("items") or part.get("body") or ""
            self.box(slide, cx, y + 44, colw, h - 44, fill="surface" if side else "soft",
                     line="primary" if side else None, lw=1.0, shape="round", radius=self.sty.get("radius"), name="비교 판")
            self.text(slide, (cx + 18, y + 60, colw - 36, h - 76), body, 14, "text", bullet=isinstance(body, list),
                      ls=1.18, space=0.6, min_size=11.5, name="비교 본문")
        ax = x + colw + 12
        self.box(slide, ax, y + 44 + (h - 44) / 2 - 22, aw, 44, fill="primary", shape="right", name="장식:화살표")
        if cb:
            self.callout(slide, x, y + h + 18, w, cb)

    def p_process(self, slide, s, top):
        items = s["items"]
        n = len(items)
        cb = s.get("callout")
        x, y, w, h = self.area(top, s)
        cbh = self.callout_h(cb, w) + 20 if cb else 0
        gap = 6.0
        sw = (w - gap * (n - 1)) / n
        bs = 12.5
        tw = sw - 16
        body_need = max((self.block_h(it.get("body"), bs, tw) for it in items if it.get("body")), default=0)
        steps = [mix(self.tint(0.78), self.c("primary"), i / max(n - 1, 1)) for i in range(n)]
        if self.sty["process"] == "chevron":
            need = 40 + 16 + 24 + body_need
            y0 = self._group_y(y, h - cbh, need)
            for i, it in enumerate(items):
                cx = x + i * (sw + gap)
                lab = it.get("label") or f"STEP {i + 1}"
                self.label(slide, cx, y0, sw + (12 if i < n - 1 else 0), 40, lab, 12.5, steps[i],
                           shape="home" if i == 0 else "chevron", pad=18, name="단계")
                _, _, tth = self.text(slide, (cx + 4, y0 + 54, tw + 8, 40), it["title"], 15, "title", bold=True,
                                      min_size=12.5, shrink=True, name="단계 제목")
                if it.get("body"):
                    self.text(slide, (cx + 4, y0 + 58 + tth, tw + 8, y + h - cbh - (y0 + 58 + tth)), it["body"], bs,
                              "muted", bullet=isinstance(it["body"], list), min_size=11, name="단계 설명")
        else:
            need = 34 + 22 + 30 + 12 + body_need + 24
            y0 = self._group_y(y, h - cbh, need)
            ly = y0 + 34 + 22 + 13
            c0, c1 = x + sw / 2, x + w - sw / 2
            self.rule(slide, c0, ly, c1, ly, "line", 1.5)
            for i, it in enumerate(items):
                cx = x + i * (sw + gap)
                mid = cx + sw / 2
                self.label(slide, cx + 6, y0, sw - 12, 34, it["title"], 13.5, "primary", shape="round", radius=17,
                           name="단계 제목")
                self.label(slide, mid - 13, ly - 13, 26, 26, f"{i + 1:02d}", 10.5, "surface", color=self.c("primary"),
                           shape="oval", line="primary", pad=1, name="단계 번호")
                by = ly + 24
                if it.get("label"):
                    self.text(slide, (cx + 4, by, sw - 8, 18), it["label"], 12, "primary", bold=True, align="c",
                              fit=False, name="단계 시기")
                    by += 22
                if it.get("body"):
                    self.text(slide, (cx + 8, by, sw - 16, y + h - cbh - by), it["body"], bs, "muted", align="c",
                              bullet=isinstance(it["body"], list), min_size=11, name="단계 설명")
        if cb:
            self.callout(slide, x, min(y0 + need + 24, y + h - cbh + 20), w, cb)

    def p_timeline(self, slide, s, top):
        items = s["items"]
        n = len(items)
        cb = s.get("callout")
        x, y, w, h = self.area(top, s)
        cbh = self.callout_h(cb, w) + 20 if cb else 0
        colw = w / n
        has_status = any(it.get("status") for it in items)
        body_need = max((self.block_h(it.get("body"), 12.5, colw - 20) for it in items if it.get("body")), default=0)
        need = 30 + 12 + (24 if has_status else 0) + 46 + body_need
        y0 = self._group_y(y, h - cbh, need)
        ly = y0 + 34
        self.rule(slide, x, ly, x + w, ly, "neutral", 1.25, arrow=True)
        for i, it in enumerate(items):
            cx = x + i * colw
            mid = cx + colw / 2
            st = str(it.get("status", ""))
            self.text(slide, (cx + 4, y0, colw - 8, 24), it["when"], 15, "primary", bold=True, align="c",
                      min_size=11, name="시점")
            if st in ("예정", "계획", "todo"):
                self.box(slide, mid - 7, ly - 7, 14, 14, fill="surface", line="primary", lw=1.75, shape="oval", name="이정표")
            elif st in ("진행", "진행중", "진행 중"):
                self.box(slide, mid - 7, ly - 7, 14, 14, fill=self.tint(0.5), line="primary", lw=1.75, shape="oval", name="이정표")
            else:
                self.box(slide, mid - 7, ly - 7, 14, 14, fill="primary", shape="oval", name="이정표")
            by = ly + 18
            if st:
                stw = em(st) * 10.5 + 16
                self.label(slide, mid - stw / 2, by, stw, 18, st, 10.5,
                           "primary" if st == "완료" else ("soft" if st in ("예정", "계획") else self.tint(0.55)),
                           shape="round", radius=9, pad=4, name="상태")
            if has_status:
                by += 24
            _, _, tth = self.text(slide, (cx + 8, by, colw - 16, 40), it["title"], 14.5, "title", bold=True,
                                  align="c", min_size=12, shrink=True, name="이정표 제목")
            if it.get("body"):
                self.text(slide, (cx + 10, by + tth + 4, colw - 20, y + h - cbh - (by + tth + 4)), it["body"], 12.5,
                          "muted", align="c", bullet=isinstance(it["body"], list), min_size=10.5, name="이정표 설명")
        if cb:
            self.callout(slide, x, min(y0 + need + 28, y + h - cbh + 20), w, cb)

    def p_gantt(self, slide, s, top):
        periods = [str(p) for p in s["periods"]]
        rows = s["rows"]
        ms = s.get("milestones") or []
        x, y, w, h = self.area(top, s)
        statuses = {str(r.get("status")) for r in rows if r.get("status")}
        foot = 22.0 if (ms or statuses) else 0
        lab_w = min(max(w * 0.2, 120.0), 200.0)
        gx, gw = x + lab_w, w - lab_w
        colw = gw / len(periods)
        hh = 28.0
        rh = min(36.0, (h - hh - foot) / len(rows))
        head = "primary"
        self.label(slide, x, y, lab_w, hh, "과업", 12, head, name="일정 머리")
        self.box(slide, gx, y, gw, hh, fill=head, name="일정 머리")
        psz = 11.5
        while psz > 8 and max(em(p) for p in periods) * psz > colw - 4:
            psz -= 0.5
        for j, p in enumerate(periods):
            self.text(slide, (gx + j * colw, y, colw, hh), p, psz, self.on(head), bold=True, align="c", anchor="m",
                      fit=False, name="기간")
        gy = y + hh
        for j in range(1, len(periods)):
            self.rule(slide, gx + j * colw, gy, gx + j * colw, gy + rh * len(rows), "line", 0.5)
        for i, r in enumerate(rows):
            ry = gy + i * rh
            self.text(slide, (x + 8, ry, lab_w - 14, rh), r["task"], 12, "title", bold=True, anchor="m", min_size=9.5,
                      ls=1.0, name="과업")
            self.rule(slide, x, ry + rh, x + w, ry + rh, "line", 0.75)
            st = str(r.get("status", ""))
            bx = gx + (int(r["start"]) - 1) * colw + 3
            bw = (int(r["end"]) - int(r["start"]) + 1) * colw - 6
            bh = rh * 0.58
            byy = ry + (rh - bh) / 2
            if st in ("예정", "계획"):
                fill, line, tc = "surface", "primary", self.c("primary")
            elif st in ("진행", "진행중", "진행 중"):
                fill, line, tc = self.tint(0.45), None, self.on(self.tint(0.45))
            else:
                fill, line, tc = "primary", None, self.on("primary")
            lab = r.get("label") or ""
            fits = em(strip_md(lab)) * 10.5 + 12 <= bw
            sp = self.box(slide, bx, byy, bw, bh, fill=fill, line=line, lw=1.0, shape="round", radius=bh / 2, name="일정 막대")
            if lab and fits:
                self.text(slide, (bx + 4, byy, bw - 8, bh), lab, 10.5, tc, bold=True, align="c", anchor="m", fit=False,
                          name="막대 글")
            elif lab:
                rest = x + w - (bx + bw) - 6
                if em(strip_md(lab)) * 10 <= rest:
                    self.text(slide, (bx + bw + 6, ry, rest, rh), lab, 10, "text", anchor="m", fit=False, name="막대 글")
                else:
                    self.text(slide, (bx + 2, byy, bw - 4, bh), lab, 8.5, tc, align="c", anchor="m", min_size=7,
                              name="막대 글")
        gb = gy + rh * len(rows)
        for m in ms:
            mx = gx + (float(m["at"]) - 0.5) * colw
            self.rule(slide, mx, gy, mx, gb + 4, "primary", 1.0, dash=True)
            self.box(slide, mx - 5, gb + 2, 10, 10, fill="primary", shape="diamond", name="이정표")
            self.text(slide, (mx - 70, gb + 12, 140, 14), m.get("label", ""), 10, "primary", bold=True, align="c",
                      fit=False, name="이정표 글")
        if statuses:
            legend = "   ".join(f"{k} {v}" for k, v in (("■", "완료"), ("▣", "진행"), ("□", "예정")))
            self.text(slide, (x + w - 220, gb + 12 if not ms else gb + 26, 220, 14), legend, 10, "muted", align="r",
                      fit=False, name="범례")
            self.texts[self.no].pop()

    def _table(self, slide, t, x, y, w, h, size):
        header = t.get("header")
        rows = [[str(c) for c in r] for r in t["rows"]]
        ncol = len(header or rows[0])
        caption = t.get("caption")
        cap_h = 30.0 if caption else 0
        if caption:
            self.label(slide, x, y, w, cap_h, caption, 14, "primary", name="표 제목")
        if t.get("widths"):
            ws = [float(v) for v in t["widths"]]
        else:
            ws = [min(max(max(em(strip_md(r[j])) for r in ([header] if header else []) + rows), 4.0), 24.0)
                  for j in range(ncol)]
        tot = sum(ws)
        colw = [w * v / tot for v in ws]
        allrows = ([header] if header else []) + rows

        def heights(sz):
            out = []
            for r in allrows:
                lines = max(n_lines(strip_md(c), sz, colw[j] - 14) for j, c in enumerate(r))
                out.append(max(lines * sz * LH * 1.05 + 10, 24.0))
            return out

        sz = size
        avail = h - cap_h
        while sum(heights(sz)) > avail and sz > 10:
            sz -= 0.5
        while sz < 15 and sum(heights(sz + 0.5)) <= avail * 0.75:     # 자리가 남으면 읽기 쉽게 키운다
            sz += 0.5
        hs = heights(sz)
        if sum(hs) > avail + 1:
            self.warn(f"표가 칸을 넘친다({sz:g}pt, 행 {len(rows)}개) — 행을 줄이거나 장을 나눈다")
        gf = slide.shapes.add_table(len(allrows), ncol, E(x), E(y + cap_h), E(w), E(sum(hs)))
        gf.name = "표"
        tbl = gf.table
        tblPr = gf._element.graphic.graphicData.tbl.tblPr
        sid = tblPr.find(qn("a:tableStyleId"))
        if sid is None:
            sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
        sid.text = NO_STYLE_TABLE
        for k in ("firstRow", "bandRow"):
            tblPr.attrib.pop(k, None)
        for j, cw in enumerate(colw):
            tbl.columns[j].width = E(cw)
        for i, hh in enumerate(hs):
            tbl.rows[i].height = E(hh)
        solid = self.sty.get("table") == "solid"
        hl = t.get("highlight_row")
        total = t.get("total")
        aligns = t.get("align")
        for i, r in enumerate(allrows):
            is_head = bool(header) and i == 0
            bi = i - (1 if header else 0) + 1
            is_total = bool(total) and i == len(allrows) - 1
            is_hl = hl is not None and bi == int(hl) and not is_head
            if is_head:
                fill = "primary" if solid else "soft"
            elif is_total:
                fill = "soft"
            elif is_hl:
                fill = self.tint(0.88)
            else:
                fill = "surface"
            for j, c in enumerate(r):
                cell = tbl.cell(i, j)
                cell.margin_left = cell.margin_right = E(7)
                cell.margin_top = cell.margin_bottom = E(3)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor.from_string(self.c(fill))
                self._borders(cell, top=("primary", 1.5) if is_head and not solid else None,
                              bottom=("text", 1.0) if is_head else ("line", 0.75))
                if aligns:
                    al = ALIGN.get(str(aligns[j]).lower(), "c")
                else:
                    plain = strip_md(c)
                    al = "c" if (len(plain) <= 10 or re.fullmatch(r"[\d,.\s%~+\-()억만천원조개명건배년월일·]+", plain)) else "l"
                color = self.on(fill) if is_head else self.c("text")
                self._write(cell.text_frame, _paras(c), sz, color, is_head or is_total or is_hl or (j == 0 and not is_head and t.get("first_bold", True) and ncol > 2),
                            al, "m", 1.05, self.fb, None, False, 0.1, "primary", 0)
                cell.margin_left = cell.margin_right = E(7)
                self._reg(_paras(c))
        return cap_h + sum(hs)

    def _borders(self, cell, top=None, bottom=None):
        tcPr = cell._tc.get_or_add_tcPr()
        for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
            old = tcPr.find(qn(tag))
            if old is not None:
                tcPr.remove(old)
        for idx, (tag, spec) in enumerate((("a:lnL", None), ("a:lnR", None), ("a:lnT", top), ("a:lnB", bottom))):
            ln = tcPr.makeelement(qn(tag), {"w": str(int((spec[1] if spec else 0) * 12700)), "cap": "flat",
                                            "cmpd": "sng", "algn": "ctr"})
            if spec:
                sf = etree.SubElement(ln, qn("a:solidFill"))
                etree.SubElement(sf, qn("a:srgbClr"), val=self.c(spec[0]))
                etree.SubElement(ln, qn("a:prstDash"), val="solid")
            else:
                etree.SubElement(ln, qn("a:noFill"))
            tcPr.insert(idx, ln)

    def p_table(self, slide, s, top):
        note = s.get("note")
        x, y, w, h = self.area(top, s, 20 if note else 0)
        tables = s.get("tables") or [{k: s[k] for k in ("header", "rows", "total", "highlight_row", "widths", "align")
                                      if k in s}]
        size = float(s.get("size", 12.5))
        gap = 22.0
        tw = (w - gap * (len(tables) - 1)) / len(tables)
        used = 0.0
        for i, t in enumerate(tables):
            used = max(used, self._table(slide, t, x + i * (tw + gap), y, tw, h, size))
        if note:
            self.text(slide, (x, y + min(used, h) + 6, w, 16), note, 10.5, "muted", min_size=9, name="표 주석")

    def p_swot(self, slide, s, top):
        cb = s.get("callout")
        x, y, w, h = self.area(top, s, self.callout_h(cb, self.CW) + 18 if cb else 0)
        gap = 14.0
        qw, qh = (w - gap) / 2, (h - gap) / 2
        pal = [self.c(c) for c in self.colors.get("series", [])] + [self.c("neutral")] * 4
        spec = [("s", "S", "강점 Strength", pal[0]), ("w", "W", "약점 Weakness", pal[2]),
                ("o", "O", "기회 Opportunity", pal[1]), ("t", "T", "위협 Threat", pal[3])]
        for k, (key, letter, name, col) in enumerate(spec):
            qx = x + (k % 2) * (qw + gap)
            qy = y + (k // 2) * (qh + gap)
            self.box(slide, qx, qy, qw, qh, fill="surface", line="line", shape="round", radius=self.sty.get("radius"),
                     name="SWOT 칸")
            self.label(slide, qx, qy, qw, 34, f"{letter}   {name}", 13.5, col, align="l", pad=14, name="SWOT 머리")
            self.text(slide, (qx + 16, qy + 44, qw - 32, qh - 52), s[key], 13, "text", bullet=True, ls=1.12,
                      space=0.45, min_size=11, name=f"SWOT {letter}")
        if cb:
            self.callout(slide, x, y + h + 18, w, cb)

    def p_rows(self, slide, s, top):
        items = s["items"]
        n = len(items)
        cb = s.get("callout")
        x, y, w, h = self.area(top, s)
        cbh = self.callout_h(cb, w) + 40 if cb else 0
        has_label = any(it.get("label") for it in items)
        lw = min(max(w * 0.2, 110.0), 200.0) if has_label else 0
        tx = x + (lw + 18 if has_label else 18)
        tw = x + w - 18 - tx
        gap = 10.0
        avail = (h - cbh - gap * (n - 1)) / n
        ts, bs = 14.0, 12.5

        def inner(it, ts_, bs_):
            t = self.block_h(it["title"], ts_, tw, 1.1, True)
            return t + (4 + self.block_h(it["body"], bs_, tw) if it.get("body") else 0)

        while max(inner(it, ts, bs) for it in items) + 20 > avail and (ts > 12 or bs > 10.5):
            ts, bs = max(ts - 0.5, 12), max(bs - 0.5, 10.5)
        rh = min(avail, max(max(inner(it, ts, bs) for it in items) + 22, 54.0))
        for i, it in enumerate(items):
            ry = y + i * (rh + gap)
            pill = self.sty["card"] == "pill"
            self.box(slide, x, ry, w, rh, fill="surface" if pill else "soft", line="line" if pill else None,
                     shape="round", radius=self.sty.get("radius"), name="행")
            if has_label:
                self.label(slide, x + 10, ry + 9, lw - 10, rh - 18, it.get("label", ""), 13, "primary", shape="round",
                           radius=self.sty.get("radius"), name="행 라벨")
            th = self.block_h(it["title"], ts, tw, 1.1, True)
            ty = ry + (rh - inner(it, ts, bs)) / 2
            self.text(slide, (tx, ty, tw, th + 2), it["title"], ts, "title", bold=True, ls=1.1, fit=False,
                      name="행 제목")
            if it.get("body"):
                self.text(slide, (tx, ty + th + 4, tw, ry + rh - (ty + th + 4) - 4), it["body"], bs, "muted",
                          bullet=isinstance(it["body"], list), fit=False, name="행 설명")
        if cb:
            ay = y + n * (rh + gap) - gap + 6
            self.box(slide, x + w / 2 - 12, ay, 24, 18, fill="primary", shape="down", name="장식:화살표")
            self.callout(slide, x, ay + 24, w, cb)

    def p_pillars(self, slide, s, top):
        items = s["items"]
        n = len(items)
        x, y, w, h = self.area(top, s)
        cy = y
        for key, tag in (("vision", "비전"), ("mission", "미션")):
            if s.get(key):
                self.box(slide, x, cy, w, 40, fill="soft", shape="round", radius=self.sty.get("radius"), name=f"{tag} 띠")
                self.label(slide, x + 8, cy + 7, 76, 26, tag, 12, "primary" if key == "vision" else "neutral",
                           shape="round", radius=13, name=f"{tag} 라벨")
                self.text(slide, (x + 98, cy, w - 112, 40), s[key], 14.5, "title", bold=True, anchor="m", min_size=12,
                          name=tag)
                cy += 50
        fh = 40.0 if s.get("foundation") else 0
        gap = 14.0
        cw = (w - gap * (n - 1)) / n
        ph = y + h - cy - (fh + 10 if fh else 0) - 4
        for i, it in enumerate(items):
            px = x + i * (cw + gap)
            self.label(slide, px, cy + 4, cw, 34, it["title"], 13.5, "primary", shape="round",
                       radius=self.sty.get("radius"), name="추진 축")
            self.box(slide, px, cy + 44, cw, ph - 40, fill="surface", line="line", shape="round",
                     radius=self.sty.get("radius"), name="추진 축 본문")
            if it.get("body"):
                self.text(slide, (px + 14, cy + 56, cw - 28, ph - 64), it["body"], 12.5, "text",
                          bullet=isinstance(it["body"], list), min_size=10.5, name="추진 축 설명")
        if fh:
            self.label(slide, x, y + h - fh, w, fh, s["foundation"], 13.5, "soft", shape="round",
                       radius=self.sty.get("radius"), name="기반")

    def p_team(self, slide, s, top):
        items = s["items"]
        n = len(items)
        cb = s.get("callout")
        x, y, w, h = self.area(top, s, self.callout_h(cb, self.CW) + 18 if cb else 0)
        gap = 20.0
        cw = (w - gap * (n - 1)) / n if n > 1 else min(w, 420.0)
        D = 78.0
        need = max(150 + (self.block_h(it.get("career"), 12, cw - 32, 1.12, space=0.4) if it.get("career") else 0)
                   for it in items) + 20
        full_h = h
        h = min(h, max(need, 220.0))
        if cb:
            y += max(0.0, (full_h - h) * 0.3)
        for i, it in enumerate(items):
            cx = x + i * (cw + gap)
            if self.sty["card"] == "pill":
                self.box(slide, cx, y, cw, h, fill="surface", line="line", shape="round", radius=self.sty.get("radius"),
                         name="팀원 카드")
            mid = cx + cw / 2
            if it.get("photo"):
                self.picture(slide, it["photo"], mid - D / 2, y + 16, D, D, mode="cover", geom="ellipse", name="사진")
            else:
                self.box(slide, mid - D / 2, y + 16, D, D, fill="soft", shape="oval", name="사진 자리")
                nm = strip_md(it["name"])
                ini = nm[:1]
                if re.fullmatch(r"[가-힣]{2,4}|[A-Za-z][A-Za-z .'-]{1,30}", nm) and not ROLE.search(nm):   # 사람 이름일 때만 이니셜
                    self.text(slide, (mid - D / 2, y + 16, D, D), ini, 28, "primary", bold=True, align="c", anchor="m",
                              fit=False, name="이니셜")
                    self.texts[self.no].pop()
                else:       # 이름을 가렸으면(○○○) 사람 모양으로
                    self.box(slide, mid - 12, y + 30, 24, 24, fill=self.tint(0.55), shape="oval", name="장식:머리")
                    self.box(slide, mid - 22, y + 58, 44, 36, fill=self.tint(0.55), shape="round", radius=18,
                             name="장식:몸")
            self.text(slide, (cx + 10, y + 102, cw - 20, 22), it["name"], 16, "title", bold=True, align="c",
                      min_size=13, name="이름")
            yy = y + 126
            if it.get("role"):
                self.text(slide, (cx + 10, yy, cw - 20, 18), it["role"], 12.5, "primary", bold=True, align="c",
                          min_size=11, name="역할")
                yy += 24
            self.rule(slide, cx + 16, yy + 2, cx + cw - 16, yy + 2, "line", 0.75)
            if it.get("career"):
                self.text(slide, (cx + 16, yy + 12, cw - 32, y + h - yy - 20), it["career"], 12, "text",
                          bullet=isinstance(it["career"], list), ls=1.12, space=0.4, min_size=10, name="경력")
        if cb:
            self.callout(slide, x, y + h + 18, w, cb)

    def p_positioning(self, slide, s, top):
        x, y, w, h = self.area(top, s)
        pts = s.get("points")
        mw = w * 0.6 if pts else w
        mx0, my0 = x + 40, y + 10
        mw_, mh_ = mw - 80, h - 34
        midx, midy = mx0 + mw_ / 2, my0 + mh_ / 2
        self.rule(slide, mx0, midy, mx0 + mw_, midy, "neutral", 1.25, arrow=True)
        self.rule(slide, midx, my0 + mh_, midx, my0, "neutral", 1.25, arrow=True)
        xa, ya = s["x_axis"], s["y_axis"]
        self.text(slide, (mx0 - 40, midy + 6, 120, 16), xa[0], 11, "muted", fit=False, name="축 낮음")
        self.text(slide, (mx0 + mw_ - 120, midy + 6, 120, 16), xa[1], 11, "muted", bold=True, align="r", fit=False, name="축 높음")
        self.text(slide, (midx + 8, my0 - 4, 160, 16), ya[1], 11, "muted", bold=True, fit=False, name="축 높음")
        self.text(slide, (midx + 8, my0 + mh_ - 14, 160, 16), ya[0], 11, "muted", fit=False, name="축 낮음")
        scale = 100.0 if any(float(it["x"]) > 1 or float(it["y"]) > 1 for it in s["items"]) else 1.0
        taken = []          # 이미 놓은 원·이름표 영역 — 이름표가 겹치지 않게 아래 → 위 → 오른쪽 → 왼쪽 순으로 자리를 찾는다

        def free(r):
            return all(r[0] + r[2] <= q[0] or q[0] + q[2] <= r[0] or r[1] + r[3] <= q[1] or q[1] + q[3] <= r[1]
                       for q in taken)

        for it in s["items"]:
            px = mx0 + 16 + float(it["x"]) / scale * (mw_ - 32)
            py = my0 + mh_ - 16 - float(it["y"]) / scale * (mh_ - 32)
            d = max(62.0, (em(strip_md(it["name"])) * 12 * 1.03 / 0.96 + 8) / 0.7 + 4) if it.get("ours") else 22.0
            taken.append((px - d / 2, py - d / 2, d, d))
        for it in s["items"]:
            px = mx0 + 16 + float(it["x"]) / scale * (mw_ - 32)
            py = my0 + mh_ - 16 - float(it["y"]) / scale * (mh_ - 32)
            if it.get("ours"):
                d = max(62.0, (em(strip_md(it["name"])) * 12 * 1.03 / 0.96 + 8) / 0.7 + 4)
                self.label(slide, px - d / 2, py - d / 2, d, d, it["name"], 12, "primary", shape="oval", pad=4, name="자사")
            else:
                d = 22.0
                self.box(slide, px - d / 2, py - d / 2, d, d, fill=mix(self.c("neutral"), "FFFFFF", 0.35), shape="oval",
                         name="경쟁사")
                lw = em(strip_md(it["name"])) * 11 + 8
                spots = [(px - lw / 2, py + d / 2 + 2, "c"), (px - lw / 2, py - d / 2 - 18, "c"),
                         (px + d / 2 + 4, py - 8, "l"), (px - d / 2 - 4 - lw, py - 8, "r")]
                lx, ly, al = next(((x_, y_, a_) for x_, y_, a_ in spots if free((x_, y_, lw, 16))), spots[0])
                taken.append((lx, ly, lw, 16))
                self.text(slide, (lx, ly, lw, 16), it["name"], 11, "text", align=al, fit=False, name="경쟁사 이름")
        if pts:
            self.text(slide, (x + mw + 20, y + 10, w - mw - 20, h - 10), pts, 14, "text", bullet=True, ls=1.18,
                      space=0.7, min_size=12, name="요점")
        if not s.get("source"):
            self.warn("포지셔닝 축의 선정 근거(source)가 없다 — 심사위원은 축의 자의성을 본다")

    def p_image(self, slide, s, top):
        cb = s.get("callout")
        x, y, w, h = self.area(top, s, self.callout_h(cb, self.CW) + 18 if cb else 0)
        bl = s.get("bullets")
        cap = s.get("caption")
        iw = w * 0.56 if bl else w
        px, py, pw, ph = self.picture(slide, s["image"], x, y, iw, h - (26 if cap else 0))
        if cap:
            self.text(slide, (x, py + ph + 8, iw, 18), cap, 12.5, "title", bold=True, align="c", min_size=10.5,
                      name="그림 설명")
        if bl:
            self.text(slide, (x + iw + 28, y + 6, w - iw - 28, h - 6), bl, 14.5, "text", bullet=True, ls=1.18,
                      space=0.7, min_size=12, name="본문")
        if cb:
            self.callout(slide, x, y + h + 18, w, cb)


# ---------------------------------------------------------------- 검사·검증

def _spec_texts(obj, key=None):
    if key in NONTEXT:
        return
    if isinstance(obj, str):
        if obj.strip():
            yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _spec_texts(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from _spec_texts(v, key)


def _norm(t):
    return re.sub(r"\s+", "", strip_md(t))


def validate(spec, base):
    errs, warns = [], []
    slides = spec.get("slides")
    if not isinstance(slides, list) or not slides:
        return ["slides가 비었다"], warns
    for i, s in enumerate(slides, 1):
        if not isinstance(s, dict):
            errs.append(f"#{i}: 장은 객체여야 한다")
            continue
        t = s.get("type")
        if t not in PATTERNS:
            errs.append(f"#{i}: 모르는 type '{t}' — 가능: {', '.join(PATTERNS)}")
            continue
        P = PATTERNS[t]
        allowed = COMMON | set(P.get("keys", "").split()) | set(P.get("req", "").split()) | ({"items"} if "items" in P else set())
        for k in s:
            if k not in allowed:
                errs.append(f"#{i} {t}: 모르는 키 '{k}' — 가능: {', '.join(sorted(allowed - {'type'}))}")
        for k in P.get("req", "").split():
            if s.get(k) in (None, "", [], {}):
                errs.append(f"#{i} {t}: 필수 '{k}' 없음")
        spec_it = P.get("items")
        if spec_it and isinstance(s.get("items"), list):
            n = len(s["items"])
            if not spec_it["min"] <= n <= spec_it["max"]:
                errs.append(f"#{i} {t}: 항목 {n}개 — {spec_it['min']}~{spec_it['max']}개만 된다(장을 나누거나 rows·table로)")
            for j, it in enumerate(s["items"], 1):
                if isinstance(it, (str, int, float)):
                    if not spec_it["text_ok"]:
                        errs.append(f"#{i} {t} 항목{j}: 객체여야 한다 — 필수 {spec_it['req']}")
                    continue
                for k in it:
                    if k not in spec_it["req"] + spec_it["opt"]:
                        errs.append(f"#{i} {t} 항목{j}: 모르는 키 '{k}' — 가능: {', '.join(spec_it['req'] + spec_it['opt'])}")
                for k in spec_it["req"]:
                    if it.get(k) in (None, "", []):
                        errs.append(f"#{i} {t} 항목{j}: 필수 '{k}' 없음")
        for key in ("left", "right", "before", "after"):
            if key in s:
                if not isinstance(s[key], dict):
                    errs.append(f"#{i} {t}: '{key}'는 객체({{title, items}})여야 한다")
                else:
                    bad = set(s[key]) - SUBKEYS[key]
                    if bad:
                        errs.append(f"#{i} {t}.{key}: 모르는 키 {sorted(bad)} — 가능: {sorted(SUBKEYS[key])}")
        if t == "chart":
            ch = s.get("chart")
            if not ch and not s.get("image"):
                errs.append(f"#{i} chart: chart 또는 image 중 하나가 필요하다")
            if ch:
                bad = set(ch) - SUBKEYS["chart"]
                if bad:
                    errs.append(f"#{i} chart.chart: 모르는 키 {sorted(bad)}")
                if ch.get("kind", "column") not in CHART_KINDS:
                    errs.append(f"#{i} chart: kind는 {', '.join(CHART_KINDS)} 중 하나")
                cats = ch.get("categories") or []
                if not cats or not ch.get("series"):
                    errs.append(f"#{i} chart: categories·series 필요")
                for se in ch.get("series", []):
                    vals = se.get("values", [])
                    if len(vals) != len(cats):
                        errs.append(f"#{i} chart: 계열 '{se.get('name', '')}' 값 {len(vals)}개 ≠ 항목 {len(cats)}개")
                    if any(not isinstance(v, (int, float)) for v in vals):
                        errs.append(f"#{i} chart: 계열 '{se.get('name', '')}' 값은 숫자만 — 단위는 unit에")
        if t == "gantt":
            np_ = len(s.get("periods") or [])
            for j, r in enumerate(s.get("rows") or [], 1):
                bad = set(r) - SUBKEYS["rows@gantt"]
                if bad:
                    errs.append(f"#{i} gantt 행{j}: 모르는 키 {sorted(bad)}")
                try:
                    a, b = int(r["start"]), int(r["end"])
                    if not 1 <= a <= b <= np_:
                        errs.append(f"#{i} gantt 행{j}: start {a}~end {b}가 기간 1~{np_} 밖이거나 거꾸로다")
                except (KeyError, ValueError, TypeError):
                    errs.append(f"#{i} gantt 행{j}: task·start·end(기간 번호, 1부터) 필요")
            if len(s.get("rows") or []) > 10:
                errs.append(f"#{i} gantt: 행 {len(s['rows'])}개 — 10개까지(과업을 묶거나 장을 나눈다)")
            for m in s.get("milestones") or []:
                if not 1 <= float(m.get("at", 0)) <= np_:
                    errs.append(f"#{i} gantt: 이정표 at {m.get('at')}가 기간 밖")
        if t == "table":
            tables = s.get("tables") or ([{k: s[k] for k in ("header", "rows") if k in s}] if s.get("rows") else [])
            if not tables:
                errs.append(f"#{i} table: rows(또는 tables) 필요")
            if len(tables) > 2:
                errs.append(f"#{i} table: tables는 2개까지(나란히)")
            for tb in tables:
                bad = set(tb) - SUBKEYS["tables"]
                if bad:
                    errs.append(f"#{i} table: 모르는 키 {sorted(bad)}")
                ncol = len(tb.get("header") or (tb.get("rows") or [[]])[0])
                for j, r in enumerate(tb.get("rows") or [], 1):
                    if len(r) != ncol:
                        errs.append(f"#{i} table 행{j}: 칸 {len(r)}개 ≠ 열 {ncol}개")
        if t == "swot":
            for k in "swot":
                v = s.get(k)
                if v is not None and (not isinstance(v, list) or not 1 <= len(v) <= 5):
                    errs.append(f"#{i} swot: '{k}'는 1~5개 목록")
        if t == "positioning":
            for k in ("x_axis", "y_axis"):
                if not (isinstance(s.get(k), list) and len(s[k]) == 2):
                    errs.append(f"#{i} positioning: {k}는 [낮음 쪽 이름, 높음 쪽 이름]")
            for j, it in enumerate(s.get("items") or [], 1):
                if not all(isinstance(it.get(k), (int, float)) for k in ("x", "y")):
                    errs.append(f"#{i} positioning 항목{j}: x·y는 숫자(0~1 또는 0~100)")
            if not any(it.get("ours") for it in s.get("items") or []):
                warns.append(f"#{i} positioning: 자사(ours: true)가 없다")
        if t == "tam":
            units = set()
            for it in s.get("items") or []:
                m = re.search(r"[\d,.]+\s*(만|억|조|천)?\s*([가-힣A-Za-z%]+)", str(it.get("value", "")) if isinstance(it, dict) else "")
                if m:
                    units.add("원" if m.group(2) in ("원", "달러") or m.group(1) else m.group(2))
            if len(units) > 1:
                warns.append(f"#{i} tam: 층마다 단위가 다르다({', '.join(sorted(units))}) — 포함 관계 그림은 한 단위(금액 또는 고객 수)로 맞춘다")
        if t == "table":
            for tb in s.get("tables") or [s]:
                bad = [x for x in (tb.get("align") or []) if str(x).lower() not in ALIGN]
                if bad:
                    errs.append(f"#{i} table: align 값 {bad} — l·c·r(또는 left·center·right) 중에서")
        if t == "compare" and s.get("criteria"):
            if not isinstance(s["criteria"], list):
                errs.append(f"#{i} compare: criteria는 목록")
        for k in ("image",):
            p = s.get(k)
            if isinstance(p, str) and not p.strip().startswith("["):
                full = p if os.path.isabs(p) else os.path.join(base, p)
                if not os.path.isfile(full):
                    errs.append(f"#{i} {t}: 그림 파일 없음 '{p}' (자리 표시는 \"[이미지: 설명]\")")
        for it in s.get("items") or []:
            p = it.get("photo") if isinstance(it, dict) else None
            if p and not os.path.isfile(p if os.path.isabs(p) else os.path.join(base, p)):
                errs.append(f"#{i} {t}: 사진 파일 없음 '{p}'")
        if t in ("kpi", "chart", "tam") and not s.get("source"):
            warns.append(f"#{i} {t}: 출처(source) 없음 — 수치가 있는 장은 출처를 단다")
    return errs, warns


def deck_texts(path):
    prs = Presentation(path)
    out = []
    for slide in prs.slides:
        buf = []

        def walk(shapes):
            for sh in shapes:
                if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
                    walk(sh.shapes)
                if sh.has_text_frame:
                    buf.append(sh.text_frame.text)
                if getattr(sh, "has_table", False) and sh.has_table:
                    for row in sh.table.rows:
                        for cell in row.cells:
                            buf.append(cell.text)
                if getattr(sh, "has_chart", False) and sh.has_chart:
                    plot = sh.chart.plots[0]
                    buf.extend([str(c) for c in plot.categories] + [se.name for se in plot.series])
        walk(slide.shapes)
        out.append(_norm("".join(buf)))
    return out


def verify(spec, out_path):
    """스펙의 모든 글이 만든 .pptx의 해당 장에 실제로 들어갔는지 대조한다."""
    got = deck_texts(out_path)
    missing = []
    for i, s in enumerate(spec["slides"]):
        page = got[i] if i < len(got) else ""
        for t in _spec_texts(s):
            if _norm(t) and _norm(t) not in page:
                missing.append(f"#{i + 1}: '{strip_md(t)[:40]}'")
    return missing


# ---------------------------------------------------------------- 카탈로그

def catalog():
    lines = ["| type | 쓰임(정보 유형) | 필수 키 | 선택 키 | 항목(items) |", "|------|----------------|---------|---------|-------------|"]
    for name, P in PATTERNS.items():
        it = P.get("items")
        its = ""
        if it:
            its = f"{it['min']}~{it['max']}개 · 필수 {', '.join(it['req']) or '—'} · 선택 {', '.join(it['opt']) or '—'}"
            if it["text_ok"]:
                its += " · 문자열도 됨"
        lines.append(f"| `{name}` | {P['use']} | {', '.join(P.get('req', '').split()) or '—'} | "
                     f"{', '.join(P.get('keys', '').split()) or '—'} | {its or '—'} |")
    lines.append("")
    lines.append("모든 장 공통 선택 키: title, eyebrow(작은 머리말), lead(한 줄 설명), source(출처), notes(발표 대본).")
    lines.append("하위 구조: compare.left/right = {title, items[]} · before_after.before/after = {title, items[] 또는 body} · "
                 "chart.chart = {kind(column·bar·line·stacked·doughnut·pie), categories[], series[{name, values[]}], unit, "
                 "number_format, highlight(강조할 항목 번호·이름), labels, percent} · gantt.rows = [{task, start, end, label, status}] "
                 "(start·end는 periods 번호, 1부터) · gantt.milestones = [{at, label}] · table.tables = [{caption, header, rows, total, "
                 "highlight_row, widths, align}](2개까지 나란히) · contact = [[라벨, 값]]")
    return "\n".join(lines)


# ---------------------------------------------------------------- 실행

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--spec")
    ap.add_argument("--out")
    ap.add_argument("--theme")
    ap.add_argument("--font", help="모든 글꼴을 이 글꼴로(예: '맑은 고딕') — 발표 PC에 테마 글꼴이 없을 때")
    ap.add_argument("--check", action="store_true", help="그리지 않고 스펙만 검사")
    ap.add_argument("--catalog", action="store_true")
    ap.add_argument("--themes", action="store_true")
    ap.add_argument("--sample", action="store_true", help="모든 패턴을 담은 예시 덱을 만든다")
    ap.add_argument("--strict", action="store_true", help="경고가 있으면 종료 코드 1")
    a = ap.parse_args()

    if a.catalog:
        print(catalog())
        return
    if a.themes:
        for p in list_themes():
            with open(p, encoding="utf-8") as f:
                t = json.load(f)
            loc = "local" if os.sep + "local" + os.sep in p else "공개"
            print(f"- {t['name']} ({loc}) — {t.get('label', '')}: {t.get('summary', '')}")
        return
    if a.sample:
        a.spec = a.spec or os.path.join(THEME_DIR, "sample-deck.json")
    if not a.spec:
        ap.error("--spec이 필요하다(또는 --catalog·--themes·--sample)")
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    base = os.path.dirname(os.path.abspath(a.spec))
    errs, warns = validate(spec, base)
    for w in warns:
        print("주의:", w)
    if errs:
        print(f"스펙 오류 {len(errs)}건 — 고친 뒤 다시 실행한다:")
        for e in errs:
            print("  -", e)
        sys.exit(2)
    n_marks = sum(len(re.findall(r"\[(작성 필요|산정 예정|미확보)", t)) for t in _spec_texts(spec["slides"]))
    if a.check:
        print(f"스펙 검사 통과: {len(spec['slides'])}장, 미확보 표기 {n_marks}곳")
        return
    if not a.out:
        ap.error("--out이 필요하다")
    theme = load_theme(a.theme or spec.get("theme") or "report-blue")
    want = a.font or spec.get("font")
    if want and shutil.which("fc-list"):
        fams = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
        if want not in fams:
            print(f"주의: '{want}' 글꼴이 이 컴퓨터에 없다 — PDF·미리보기는 대체 글꼴로 그려져 줄바꿈·겹침이 실제와 다르다. "
                  "발표 PC 글꼴을 모르면 --font 없이 테마 글꼴로 만들고 PDF를 함께 낸다")
    deck = Deck(theme, spec.get("meta"), font=a.font or spec.get("font"), base_dir=base)
    for s in spec["slides"]:
        deck.add(s)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    deck.prs.save(a.out)
    missing = verify(spec, a.out)
    print(f"저장: {a.out} — {len(spec['slides'])}장, 테마 {theme['name']}, 글꼴 {deck.fb}")
    print(f"검증: 스펙 글 누락 {len(missing)}건, 넘침·끊김 경고 {len(deck.warnings)}건, "
          f"그림 자리 표시 {deck.placeholders}곳, 미확보 표기 {n_marks}곳")
    for m in missing:
        print("  누락", m)
    for w in deck.warnings:
        print("  경고", w)
    if missing or (a.strict and deck.warnings):
        sys.exit(1)


if __name__ == "__main__":
    main()
