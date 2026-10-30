#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사업계획서·발표용 시각자료를 HTML(인라인 SVG)로 만들고 PNG로 찍는다.

    python3 -B html_visuals.py 시각자료.json --out 시각자료/ [--theme 테마.json | --accent 0066FF] [--print | --slide] [--no-png]

입력(JSON): {"visuals": [{"id": "tam", "type": "tam", "headline": "결론 문장", ...}, ...]}
- 모든 시각자료에 공통: id · type · headline(필수 — 무엇을 보여주는지가 아니라 무엇을 말하는지)
  · kicker(어느 절의 그림인지, 예: "1-3 · 목표 고객") · sub(읽는 법 한 줄) · takeaway(그래서 무엇인가 한 줄) · note(출처 · 시점 · 표본)
- type 33종(사업계획서 목차순 쓰임새는 references/visual-html.md):
  시장·고객 tam · segments · persona · survey · quotes · donut / 문제·해결 trend · ps_map · photos · screens · flow
  차별 compare · positioning · venn · bar · before_after / 돈 bm · bmc · waterfall · revenue_mix · budget · pnl · columns · kpi
  실행 funnel · gantt · roadmap · stairs · timeline · swot · team · partners · table
  {"type": "chapter", "title": "1. 문제 인식"}은 미리보기 쪽의 장 구분(그림 아님)
  (필드는 각 함수 설명과 assets/html-visuals-sample.json 참고. `--sample 예시.json`으로 목차순 예시 spec을 복사한다)
출력: <out>/visuals.html(모두 한 장에) + <out>/<id>.png(2배 해상도, Node + Playwright가 있을 때).
'○○'(미확보 값)은 점선 밑줄로 표시돼 빈칸이 보인다. 강조는 우리(ours) 하나에만 쓰고 나머지는 회색으로 둔다.
"""
import argparse
import base64
import html
import json
import math
import re
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TXT = 1.0      # SVG 글자 배율 — 문서용(--print)에서 키운다. tw()와 font-size 후처리가 같은 값을 쓴다
BODY_W = 1024  # HTML 유형의 본문 폭(확대 전 px) — build()가 모드에 맞춰 바꾼다
MIN_FS = 0     # SVG 최소 글자(배율 전) — 문서용은 13: 170mm 폭에서 가장 작은 글자가 7.5pt 안팎이 되게
BASE_DIR = os.getcwd()          # 이미지 경로의 기준(spec 파일 폴더) — main에서 바꾼다
FONT = "Pretendard, 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', system-ui, sans-serif"
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
GRAY, GRAY_FILL, SECOND = "#a3a19a", "#d9d7d0", "#eb6834"
HALO = 'paint-order="stroke" stroke="#fff" stroke-width="5" stroke-linejoin="round"'   # 선 위 글자를 읽히게


# ---------------------------------------------------------------- 공통

def esc(text):
    """HTML 이스케이프 + '○○'를 미확보 표시로."""
    s = html.escape(str(text if text is not None else ""))
    return s.replace("○○", '<span class="ph">○○</span>')


def fsz(size):
    """SVG 글자의 실제 크기 — 최소 글자와 배율을 적용한다(글 폭 계산과 font-size 후처리가 같이 쓴다)."""
    return max(size, MIN_FS) * TXT


def tw(text, size):
    """글자 폭 근사(px) — 한글·전각 기호(①○★) 1em, 영문·숫자 0.56em, 공백 0.3em."""
    w = 0.0
    for ch in str(text):
        w += 0.3 if ch.isspace() else 1.0 if ord(ch) > 0x2E7F or 0x2460 <= ord(ch) <= 0x27BF else 0.56
    return w * fsz(size)


def pct(part, whole):
    """전환율 표기 — 10% 이상 정수, 1% 이상 소수 1자리, 그 아래는 유효숫자 2자리(0.16%). 0%로 뭉개지 않는다."""
    if not whole:
        return "—"
    p = part / whole * 100
    if p >= 10 or p == 0:
        return f"{p:.0f}%"
    if p >= 1:
        return f"{p:.1f}%"
    return f"{p:.2g}%"


def fmt(v):
    if isinstance(v, (int, float)):
        return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"
    return str(v)


def mix(hex_color, t):
    """흰색과 섞은 색(t=0 흰색, 1 원색)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(round(255 - (255 - c) * t) for c in (r, g, b))


def darker(hex_color, f=0.75):
    h = hex_color.lstrip("#")
    return "#%02x%02x%02x" % tuple(round(int(h[i:i + 2], 16) * f) for i in (0, 2, 4))


def nice_ticks(lo, hi, n=5):
    """깔끔한 눈금(0 포함)."""
    lo, hi = min(lo, 0), max(hi, 0)
    span = (hi - lo) or 1
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    start = math.floor(lo / step) * step
    ticks, v = [], start
    while v <= hi + step * 0.001:
        ticks.append(round(v, 10))
        v += step
    if ticks[-1] < hi:
        ticks.append(ticks[-1] + step)
    return ticks


def chip(text, kind=""):
    return f'<span class="chip {kind}">{esc(text)}</span>'


LEVEL = {"확인": "lv-ok", "산출": "lv-calc", "관찰": "lv-obs", "가정": "lv-assume"}


def level_chip(level):
    return chip(level, LEVEL.get(level, "")) if level else ""


# ---------------------------------------------------------------- 유형별 본문

def v_tam(v, A):
    """layers: [{label, value, name, formula, basis}] 바깥(TAM)부터 안쪽(1차 고객)까지 3~4개."""
    layers = v["layers"][:4]
    n = len(layers)
    radii = {2: [170, 96], 3: [178, 122, 64], 4: [182, 130, 84, 44]}[max(2, n)]
    bottom, cx, H = 372, 196, 384
    shades = {2: [0.12, 1], 3: [0.12, 0.38, 1], 4: [0.1, 0.28, 0.55, 1]}[max(2, n)]
    svg, rows = [], []
    ys = []
    for i, (lay, r) in enumerate(zip(layers, radii)):
        top = bottom - 2 * r
        last = i == n - 1
        y = bottom - r if last else top + 34
        ys.append(y)
        fill = mix(A, shades[i])
        svg.append(f'<circle cx="{cx}" cy="{bottom - r}" r="{r}" fill="{fill}" stroke="#fff" stroke-width="2"/>')
        tc = "#fff" if shades[i] >= 0.55 else INK
        svg.append(f'<text x="{cx}" y="{y + 5}" text-anchor="middle" font-size="15" font-weight="700" fill="{tc}">'
                   f'{html.escape(lay.get("label", ""))}</text>')
    for i, (lay, r, y) in enumerate(zip(layers, radii, ys)):
        cy = bottom - r
        dx = math.sqrt(max(r * r - (y - cy) ** 2, 0))
        x0 = cx + dx + 6
        svg.append(f'<line x1="{x0:.1f}" y1="{y}" x2="420" y2="{y}" stroke="{BASE}" stroke-width="1"/>')
        svg.append(f'<circle cx="{x0:.1f}" cy="{y}" r="3" fill="{INK2}"/>')
        rows.append(
            f'<div class="tam-row" style="top:{y - 15}px">'
            f'<div class="tam-val">{esc(lay.get("value", ""))}'
            f'<span class="tam-name">{esc(lay.get("name", ""))}</span>{level_chip(lay.get("basis"))}</div>'
            f'<div class="tam-formula">{esc(lay.get("formula", ""))}</div></div>')
    return (f'<div class="tam" style="height:{H}px"><svg width="440" height="{H}" class="abs">{"".join(svg)}</svg>'
            f'{"".join(rows)}</div>')


def _place_labels(points, box, size_of):
    """점 라벨을 오른쪽·왼쪽·위·아래 중 겹치지 않는 자리에 놓는다."""
    placed, out = [], []
    x0, y0, x1, y1 = box
    for (px, py, r, text, fs) in points:
        w, h = size_of(text, fs), fsz(fs) * 1.3
        cands = [(px + r + 8, py - h / 2), (px - r - 8 - w, py - h / 2), (px - w / 2, py - r - 6 - h),
                 (px - w / 2, py + r + 6)]
        best = None
        for (lx, ly) in cands:
            rect = (lx, ly, lx + w, ly + h)
            inside = rect[0] >= x0 and rect[2] <= x1 and rect[1] >= y0 and rect[3] <= y1
            hit = any(not (rect[2] < q[0] or rect[0] > q[2] or rect[3] < q[1] or rect[1] > q[3]) for q in placed)
            if inside and not hit:
                best = rect
                break
        best = best or (cands[0][0], cands[0][1], cands[0][0] + w, cands[0][1] + h)
        placed.append(best)
        out.append(best)
    return out


def v_positioning(v, A):
    """x_axis/y_axis: {label, low, high}; points: [{name, x, y (0~10), ours, kind:'substitute'}]; quadrant: {x, y, label}."""
    W, H = 1024, 500
    L, R, T, B = 70, 954, 24, 452
    if TXT > 1:                     # 문서용: 글자가 커진 만큼 판을 낮춰 쪽 높이를 아낀다
        H, B = 430, 382
    sx = lambda x: L + (R - L) * x / 10
    sy = lambda y: B - (B - T) * y / 10
    xa, ya = v.get("x_axis", {}), v.get("y_axis", {})
    mx, my = (L + R) / 2, (T + B) / 2
    s = []
    q = v.get("quadrant")
    if q:
        qx0 = mx if q.get("x", "high") == "high" else L
        qy0 = T if q.get("y", "high") == "high" else my
        s.append(f'<rect x="{qx0}" y="{qy0}" width="{(R - L) / 2}" height="{(B - T) / 2}" fill="{mix(A, 0.07)}"/>')
        if q.get("label"):
            tx = qx0 + (R - L) / 2 - 14 if q.get("x", "high") == "high" else qx0 + 14
            anchor = "end" if q.get("x", "high") == "high" else "start"
            ty = qy0 + 26 if q.get("y", "high") == "high" else qy0 + (B - T) / 2 - 14
            s.append(f'<text x="{tx}" y="{ty}" text-anchor="{anchor}" font-size="14" font-weight="700" '
                     f'fill="{darker(A, 0.8)}">{html.escape(q["label"])}</text>')
    s.append(f'<rect x="{L}" y="{T}" width="{R - L}" height="{B - T}" fill="none" stroke="{GRID}"/>')
    s.append(f'<line x1="{L}" y1="{my}" x2="{R}" y2="{my}" stroke="{BASE}" stroke-width="1.2"/>')
    s.append(f'<line x1="{mx}" y1="{T}" x2="{mx}" y2="{B}" stroke="{BASE}" stroke-width="1.2"/>')
    # 축 이름과 양 끝 설명
    s.append(f'<text x="{L}" y="{B + 24}" font-size="13" fill="{MUTED}">◀ {html.escape(xa.get("low", "낮음"))}</text>')
    s.append(f'<text x="{R}" y="{B + 24}" text-anchor="end" font-size="13" fill="{MUTED}">{html.escape(xa.get("high", "높음"))} ▶</text>')
    s.append(f'<text x="{mx}" y="{B + 24}" text-anchor="middle" font-size="14" font-weight="700" fill="{INK2}">'
             f'{html.escape(xa.get("label", ""))}</text>')
    s.append(f'<text x="{L - 14}" y="{T + 4}" text-anchor="end" font-size="13" fill="{MUTED}" '
             f'transform="rotate(-90 {L - 14} {T + 4})">{html.escape(ya.get("high", "높음"))} ▶</text>')
    s.append(f'<text x="{L - 14}" y="{B}" text-anchor="start" font-size="13" fill="{MUTED}" '
             f'transform="rotate(-90 {L - 14} {B})">◀ {html.escape(ya.get("low", "낮음"))}</text>')
    s.append(f'<text x="{L - 14}" y="{my}" text-anchor="middle" font-size="14" font-weight="700" fill="{INK2}" '
             f'transform="rotate(-90 {L - 14} {my})">{html.escape(ya.get("label", ""))}</text>')
    pts = sorted(v["points"], key=lambda p: not p.get("ours"))      # 우리 라벨을 먼저 놓는다
    items = []
    for p in pts:
        r = 11 if p.get("ours") else 7
        fs = 16 if p.get("ours") else 14
        label = p["name"] + (" (대체재)" if p.get("kind") == "substitute" else "")
        items.append((sx(p["x"]), sy(p["y"]), r, label, fs))
    boxes = _place_labels(items, (L + 4, T + 4, R - 4, B - 4), lambda t, f: tw(t, f))
    gap = lambda px, py, b: math.hypot(max(b[0] - px, 0, px - b[2]), max(b[1] - py, 0, py - b[3]))
    LABEL_WARN[v.get("id")] = [it[3] for k, (it, b) in enumerate(zip(items, boxes))      # 라벨이 남의 점에 더 붙으면 헷갈린다
                               if any(gap(o[0], o[1], b) + 4 < gap(it[0], it[1], b) for j, o in enumerate(items) if j != k)]
    for p, (px, py, r, label, fs), bx in zip(pts, items, boxes):
        if p.get("ours"):
            s.append(f'<circle cx="{px}" cy="{py}" r="{r + 6}" fill="{mix(A, 0.18)}"/>')
            s.append(f'<circle cx="{px}" cy="{py}" r="{r}" fill="{A}" stroke="#fff" stroke-width="3"/>')
            weight, color = 700, INK
        elif p.get("kind") == "substitute":
            s.append(f'<circle cx="{px}" cy="{py}" r="{r}" fill="#fff" stroke="{GRAY}" stroke-width="2"/>')
            weight, color = 500, MUTED
        else:
            s.append(f'<circle cx="{px}" cy="{py}" r="{r}" fill="{GRAY}" stroke="#fff" stroke-width="2"/>')
            weight, color = 500, INK2
        s.append(f'<text x="{bx[0]:.1f}" y="{bx[1] + fsz(fs):.1f}" font-size="{fs}" font-weight="{weight}" fill="{color}" '
                 f'{HALO}>{html.escape(label)}</text>')
    legend = ('<div class="legend"><span><i class="dot" style="background:var(--accent)"></i>우리</span>'
              f'<span><i class="dot" style="background:{GRAY}"></i>경쟁 서비스</span>'
              f'<span><i class="dot ring"></i>대체재(고객의 현재 방법)</span></div>')
    return f'<svg width="{W}" height="{H + 10}" viewBox="0 0 {W} {H + 10}">{"".join(s)}</svg>{legend}'


def v_swot(v, A):
    """s · w · o · t: 항목 목록, strategies: {SO, WO, ST, WT}, focus: 'SO' 등."""
    def quad(letter, name, items, pos):
        lis = "".join(f'<li><span class="n">{i}</span>{esc(t)}</li>' for i, t in enumerate(items, 1))
        return (f'<div class="q {"pos" if pos else "neg"}"><div class="qh"><b>{letter}</b><span>{name}</span></div>'
                f'<ol>{lis}</ol></div>')
    grid = ('<div class="swot"><div></div><div class="colh">도움이 되는 것</div><div class="colh">해가 되는 것</div>'
            '<div class="rowh"><span>내부</span></div>'
            + quad("S", "강점 Strength", v.get("s", []), True) + quad("W", "약점 Weakness", v.get("w", []), False)
            + '<div class="rowh"><span>외부</span></div>'
            + quad("O", "기회 Opportunity", v.get("o", []), True) + quad("T", "위협 Threat", v.get("t", []), False)
            + '</div>')
    st = v.get("strategies") or {}
    if st:
        focus = v.get("focus")
        names = {"SO": "강점으로 기회 잡기", "WO": "기회로 약점 보완", "ST": "강점으로 위협 막기", "WT": "약점·위협 최소화"}
        cards = "".join(
            f'<div class="sc{" focus" if k == focus else ""}"><div class="sk">{k}<span>{names[k]}</span></div>'
            f'<div class="sv">{esc(st[k])}</div></div>' for k in ("SO", "WO", "ST", "WT") if k in st)
        grid += f'<div class="strat">{cards}</div>'
    return grid


def v_bar(v, A):
    """items: [{label, value, ours}], unit. 우리만 강조색, 나머지는 회색. 막대 끝에 값."""
    items = v["items"]
    mx = max(i["value"] for i in items) or 1
    unit = v.get("unit", "")
    rows = []
    for it in items:
        pct = it["value"] / mx * 100
        color = "var(--accent)" if it.get("ours") else GRAY_FILL
        rows.append(f'<div class="br"><div class="bl{" b" if it.get("ours") else ""}">{esc(it["label"])}</div>'
                    f'<div class="bt"><div class="bb" style="width:{pct * 0.86:.1f}%;background:{color}"></div>'
                    f'<span class="bv{" b" if it.get("ours") else ""}">{fmt(it["value"])}{esc(unit)}</span></div></div>')
    return f'<div class="bars">{"".join(rows)}</div>'


def v_before_after(v, A):
    """metrics: [{label, before, after, unit, better:'lower'|'higher'}], labels: [전, 후] 이름(기본 도입 전·도입 후).
    지표마다 전(회색)·후(강조) 막대 두 줄 + 오른쪽에 변화율. 3개까지."""
    lb, la = (v.get("labels") or ["도입 전", "도입 후"])[:2]
    rows = []
    for m in v["metrics"][:3]:
        b, a = m["before"], m["after"]
        top = max(b, a) or 1
        change = (a - b) / b * 100 if b else 0
        good = (change < 0) == (m.get("better", "lower") == "lower")
        u = m.get("unit", "")
        bar = lambda val, cls, name: (
            f'<div class="bab"><span class="bak">{esc(name)}</span><div class="bat">'
            f'<div class="bafill {cls}" style="width:{val / top * 88:.1f}%"></div>'
            f'<span class="bav {cls}">{fmt(val)}{esc(u)}</span></div></div>')
        rows.append(f'<div class="ba"><div class="bal">{esc(m["label"])}</div>'
                    f'<div class="babars">{bar(b, "before", lb)}{bar(a, "after", la)}</div>'
                    f'<div class="badelta{" good" if good else ""}">{change:+.0f}%'
                    f'<small>{"줄었다" if change < 0 else "늘었다"}</small></div></div>')
    return f'<div class="bas">{"".join(rows)}</div>'


def calc_cagr(v):
    """첫 값→끝 값 연평균 성장률(%). 라벨이 연도면 연도 차, 아니면 구간 수로 나눈다."""
    xs, ys = v.get("labels", []), v.get("values", [])
    if len(ys) < 2 or not ys[0] or ys[0] <= 0:
        return None
    try:
        yrs = float(xs[-1]) - float(xs[0])
    except (TypeError, ValueError, IndexError):
        yrs = len(ys) - 1
    return ((ys[-1] / ys[0]) ** (1 / (yrs or 1)) - 1) * 100


def v_trend(v, A):
    """labels(연도), values, unit, cagr(없으면 계산), forecast_from(전망 시작 인덱스)."""
    xs, ys = v["labels"], v["values"]
    W, H, L, R, T, B = 1024, 340, 64, 990, 28, 300
    ticks = nice_ticks(0, max(ys))
    top = ticks[-1]
    px = lambda i: L + (R - L) * (i / (len(xs) - 1) if len(xs) > 1 else 0.5)
    py = lambda y: B - (B - T) * y / top
    s = []
    for t in ticks:
        s.append(f'<line x1="{L}" y1="{py(t)}" x2="{R}" y2="{py(t)}" stroke="{GRID if t else BASE}"/>')
        s.append(f'<text x="{L - 10}" y="{py(t) + 4}" text-anchor="end" font-size="12" fill="{MUTED}">{fmt(t)}</text>')
    fc = v.get("forecast_from")
    pts = [(px(i), py(y)) for i, y in enumerate(ys)]
    area = f"M{pts[0][0]},{B} " + " ".join(f"L{x},{y}" for x, y in pts) + f" L{pts[-1][0]},{B} Z"
    s.append(f'<path d="{area}" fill="{A}" fill-opacity="0.1"/>')
    solid = pts if fc is None else pts[:fc + 1]
    if len(solid) > 1:
        s.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in solid) + f'" fill="none" stroke="{A}" '
                 'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
    if fc is not None:
        # 전망 구간: 경계선 + 점선 + 속이 빈 점. 실측과 한눈에 갈린다
        x0 = (pts[fc][0] + pts[fc + 1][0]) / 2 if fc + 1 < len(pts) else pts[fc][0]
        s.append(f'<line x1="{x0}" y1="{T}" x2="{x0}" y2="{B}" stroke="{BASE}" stroke-dasharray="3 4"/>')
        s.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in pts[fc:]) + f'" fill="none" stroke="{A}" '
                 'stroke-width="2.5" stroke-dasharray="7 6" stroke-linejoin="round"/>')
        s.append(f'<text x="{x0 - 8}" y="{B - 10}" text-anchor="end" font-size="12" font-weight="600" fill="{MUTED}">실측</text>')
        s.append(f'<text x="{x0 + 8}" y="{B - 10}" font-size="12" font-weight="600" fill="{MUTED}">전망 →</text>')
    for i, ((x, y), lab) in enumerate(zip(pts, xs)):
        fut = fc is not None and i > fc
        s.append(f'<circle cx="{x}" cy="{y}" r="{4.5 if fut else 5}" fill="{"#fff" if fut else A}" stroke="{A if fut else "#fff"}" '
                 f'stroke-width="2"/>')
        s.append(f'<text x="{x}" y="{B + 22}" text-anchor="middle" font-size="13" fill="{INK2}">{html.escape(str(lab))}</text>')
    # 값 라벨: 처음 · 끝 + 가운데의 최고·최저점(제목이 '정점'·'바닥'을 말할 때 그 점이 보이게)
    marks = {0, len(pts) - 1}
    for k in (ys.index(max(ys)), ys.index(min(ys))):
        if 0 < k < len(pts) - 1:
            marks.add(k)
    for i in sorted(marks):
        x, y = pts[i]
        s.append(f'<text x="{x}" y="{y - 14}" text-anchor="middle" font-size="15" font-weight="700" fill="{INK}">'
                 f'{fmt(ys[i])}</text>')
    cagr = v.get("cagr")
    if cagr is None and calc_cagr(v) is not None:
        cagr = f"{calc_cagr(v):.1f}%"
    badge = f'<div class="badge">연평균 성장률 <b>{esc(cagr)}</b></div>' if cagr else ""
    unit = f'<div class="unit">단위: {esc(v["unit"])}</div>' if v.get("unit") else ""
    return f'<div class="rel">{badge}{unit}<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(s)}</svg></div>'


def v_funnel(v, A):
    """stages: [{name, count, level}], unit. 아래로 갈수록 좁아지고, 단계 사이에 구간 전환율."""
    st = v["stages"]
    top = max(s["count"] for s in st) or 1
    unit = v.get("unit", "")
    n = len(st)
    rows = []
    for i, s in enumerate(st):
        w = max(math.sqrt(s["count"] / top), 0.22) * 100
        t = 0.25 + 0.75 * (i / (n - 1) if n > 1 else 1)
        bg = mix(A, t)
        fg = "#fff" if t >= 0.6 else INK
        if i:
            rate = pct(s["count"], st[i - 1]["count"])
            rows.append(f'<div class="fr conv"><div></div><div class="fconv">↓ {rate}</div><div></div></div>')
        rows.append(f'<div class="fr"><div class="fn">{esc(s["name"])}</div>'
                    f'<div class="fbw"><div class="fb" style="width:{w:.1f}%;background:{bg};color:{fg}">'
                    f'{fmt(s["count"])}{esc(unit)}</div></div><div class="fl">{level_chip(s.get("level"))}</div></div>')
    return f'<div class="funnel">{"".join(rows)}</div>'


def v_pnl(v, A):
    """periods, revenue, cost, profit(없으면 매출 − 비용), unit. 축 하나(같은 단위) — 매출 막대 + 비용·영업이익 선."""
    P, rev, cost = v["periods"], v["revenue"], v["cost"]
    prof = v.get("profit") or [r - c for r, c in zip(rev, cost)]
    W, H, L, R, T, B = 1024, 360, 70, 990, 30, 318
    ticks = nice_ticks(min(prof + [0]), max(rev + cost))
    lo, hi = ticks[0], ticks[-1]
    py = lambda y: B - (B - T) * (y - lo) / (hi - lo)
    n = len(P)
    band = (R - L) / n
    cxs = [L + band * (i + 0.5) for i in range(n)]
    s = []
    for t in ticks:
        s.append(f'<line x1="{L}" y1="{py(t)}" x2="{R}" y2="{py(t)}" stroke="{BASE if t == 0 else GRID}" '
                 f'stroke-width="{1.2 if t == 0 else 1}"/>')
        s.append(f'<text x="{L - 10}" y="{py(t) + 4}" text-anchor="end" font-size="12" fill="{MUTED}">{fmt(t)}</text>')
    bw = min(56, band * 0.42)
    for x, r in zip(cxs, rev):
        y0, y1 = py(0), py(r)
        s.append(f'<path d="M{x - bw / 2},{y0} L{x - bw / 2},{y1 + 4} Q{x - bw / 2},{y1} {x - bw / 2 + 4},{y1} '
                 f'L{x + bw / 2 - 4},{y1} Q{x + bw / 2},{y1} {x + bw / 2},{y1 + 4} L{x + bw / 2},{y0} Z" fill="{A}"/>')
        s.append(f'<text x="{x}" y="{y1 - 8}" text-anchor="middle" font-size="14" font-weight="700" fill="{INK}">{fmt(r)}</text>')
    for series, color in ((cost, "#6b6a65"), (prof, SECOND)):
        s.append('<polyline points="' + " ".join(f"{x},{py(y)}" for x, y in zip(cxs, series)) + f'" fill="none" '
                 f'stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>')
        for x, y in zip(cxs, series):
            s.append(f'<circle cx="{x}" cy="{py(y)}" r="5" fill="{color}" stroke="#fff" stroke-width="2"/>')
    be = next((i for i, y in enumerate(prof) if y >= 0), None)
    for i, (x, y) in enumerate(zip(cxs, prof)):
        # 영업이익 값은 막대 오른쪽 바깥에. 다음 구간 선이 오르면 아래, 내리면 위에 놓아 선을 피한다
        star = " ★ 흑자 전환" if be is not None and be > 0 and i == be else ""
        dy = 5 if i == n - 1 else (22 if prof[i + 1] >= y else -12)
        s.append(f'<text x="{x + bw / 2 + 10}" y="{py(y) + dy}" font-size="14" font-weight="700" fill="{INK}" {HALO}>'
                 f'{fmt(y)}<tspan font-size="13" fill="{INK2}">{star}</tspan></text>')
    for x, p in zip(cxs, P):
        s.append(f'<text x="{x}" y="{B + 24}" text-anchor="middle" font-size="14" fill="{INK2}">{html.escape(str(p))}</text>')
    legend = ('<div class="legend"><span><i class="sw" style="background:var(--accent)"></i>매출</span>'
              '<span><i class="ln" style="background:#6b6a65"></i>총비용</span>'
              f'<span><i class="ln" style="background:{SECOND}"></i>영업이익</span>'
              f'<span class="unit-in">단위: {esc(v.get("unit", ""))}</span></div>')
    return f'{legend}<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(s)}</svg>'


def v_compare(v, A):
    """entities: [{name, ours, substitute}], rows: [{label, cells: [[기호, 설명], …], disadvantage}], verify: [확인 경로…].
    기호: ● 충족 · ◐ 부분 · ○ 없음 (또는 짧은 값). 우리 열만 강조, 우리가 불리한 행에 표시."""
    def harvey(mark):
        # ●◐○는 글꼴마다 크기가 달라 SVG로 그린다. 그 밖의 값(짧은 글)은 그대로
        part = {"●": 1, "◐": 0.5, "○": 0}.get(str(mark).strip())
        if part is None:
            return f'<span class="mk txt">{esc(mark)}</span>'
        c = "var(--accent-ink)" if part else GRAY
        fill = (f'<path d="M9,2 A7,7 0 0,0 9,16 Z" fill="{INK}"/>' if part == 0.5
                else f'<circle cx="9" cy="9" r="7" fill="{INK}"/>' if part == 1 else "")
        return (f'<svg class="mk" width="18" height="18" viewBox="0 0 18 18"><circle cx="9" cy="9" r="7" fill="#fff" '
                f'stroke="{INK if part else c}" stroke-width="1.6"/>{fill}</svg>')

    ents = v["entities"]
    head = "".join(f'<th class="{"ours" if e.get("ours") else "sub" if e.get("substitute") else ""}">'
                   f'{esc(e["name"])}{"<small>대체재</small>" if e.get("substitute") else ""}</th>' for e in ents)
    body = []
    for row in v["rows"]:
        tds = []
        for e, cell in zip(ents, row["cells"]):
            mark, text = (cell + [""])[:2] if isinstance(cell, list) else (cell, "")
            ct = f'<span class="ct">{esc(text)}</span>' if text else ""
            tds.append(f'<td class="{"ours" if e.get("ours") else ""}">{harvey(mark)}{ct}</td>')
        tag = '<span class="dis">우리가 불리</span>' if row.get("disadvantage") else ""
        body.append(f'<tr><th class="rl">{esc(row["label"])}{tag}</th>{"".join(tds)}</tr>')
    if v.get("verify"):
        tds = "".join(f'<td class="vf{" ours" if e.get("ours") else ""}">{esc(t)}</td>' for e, t in zip(ents, v["verify"]))
        body.append(f'<tr class="vrow"><th class="rl">확인 경로</th>{tds}</tr>')
    legend = f'<div class="legend small"><span>{harvey("●")}충족</span><span>{harvey("◐")}부분</span><span>{harvey("○")}없음</span></div>'
    return f'<table class="cmp"><thead><tr><th></th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>{legend}'


def _clip(p, d, c, hw, hh):
    """사각형(중심 c, 반폭 hw·반높이 hh) 안의 점 p에서 방향 d로 나가 경계에 닿는 거리."""
    ts = []
    if d[0] > 1e-9:
        ts.append((c[0] + hw - p[0]) / d[0])
    if d[0] < -1e-9:
        ts.append((c[0] - hw - p[0]) / d[0])
    if d[1] > 1e-9:
        ts.append((c[1] + hh - p[1]) / d[1])
    if d[1] < -1e-9:
        ts.append((c[1] - hh - p[1]) / d[1])
    return max(0.0, min(ts)) if ts else 0.0


BM_SLOTS = {"left": (96, 0), "center": (512, 0), "right": (928, 0), "top": (512, -1), "bottom": (512, 1),
            "top-left": (96, -1), "top-right": (928, -1), "bottom-left": (96, 1), "bottom-right": (928, 1)}
BM_FILL = ["left", "right", "bottom", "top", "bottom-left", "bottom-right", "top-left", "top-right"]


def _formula(f):
    """매출 산식 띠: terms(항·연산자 목록) = result. 문자열이면 그대로 한 줄."""
    if isinstance(f, str):
        return f'<div class="fx"><span class="fx-text">{esc(f)}</span></div>'
    parts = []
    for t in f.get("terms", []):
        if isinstance(t, str):
            parts.append(f'<span class="fx-op">{esc(t)}</span>')
        else:
            parts.append(f'<span class="fx-term"><small>{esc(t.get("label", ""))}</small><b>{esc(t.get("value", ""))}</b></span>')
    r = f.get("result")
    if r:
        parts.append('<span class="fx-op">=</span>')
        parts.append(f'<span class="fx-term res"><small>{esc(r.get("label", ""))}</small><b>{esc(r.get("value", ""))}</b></span>')
    lead = f'<span class="fx-lead">{esc(f["title"])}</span>' if f.get("title") else ""
    return f'<div class="fx">{lead}{"".join(parts)}</div>'


def v_bm(v, A):
    """BM 구조도 — 누가 누구와 무엇을 주고받는가(사용료·구독료·수수료 ↔ 서비스·SW·데이터·장비). 금액은 쓰지 않는다.
    actors: [{name, role, ours, payer, pos}] — pos를 생략하면 3개 이하는 한 줄(chain), 4개 이상은 우리를 가운데 둔 허브.
    pos: left · center · right · top · bottom · top-left · top-right · bottom-left · bottom-right.
    flows: [{from, to(번호나 이름), kind:'money'|'value'|'goods', label(무엇), detail(언제·어떻게, 선택)}]
      — 돈(사용료 등)은 실선, 서비스·가치는 점선, 물건·데이터는 가는 실선.
    formula: (선택) 매출 산식 띠 {title, terms: [{label, value}, '×', …], result: {label, value}} 또는 문자열.
    streams: 수익원 [{name, how, share}]. partner: (예전 형식) 아래쪽 파트너 한 곳."""
    acts = [dict(a) for a in v["actors"]]
    flows = list(v.get("flows", []))
    if v.get("partner"):
        acts.append({**v["partner"], "pos": "bottom", "_partner": True})
        if v["partner"].get("label"):                      # 예전 형식: 파트너 → 우리 한 줄
            hub = next((k for k, a in enumerate(acts) if a.get("ours")), 0)
            flows.append({"from": len(acts) - 1, "to": hub, "kind": "goods", "label": v["partner"]["label"]})
    if not any(a.get("pos") for a in acts if not a.get("_partner")):
        main_ = [a for a in acts if not a.get("_partner")]
        if len(main_) <= 3 and v.get("layout") != "hub":
            for a, slot in zip(main_, {1: ["center"], 2: ["left", "right"], 3: ["left", "center", "right"]}[len(main_)]):
                a["pos"] = slot
        else:
            ours = next((a for a in main_ if a.get("ours")), main_[0])
            ours["pos"] = "center"
            free = iter(s for s in BM_FILL if s not in {a.get("pos") for a in acts})
            for a in main_:
                if not a.get("pos"):
                    a["pos"] = next(free)
    rows = sorted({BM_SLOTS[a["pos"]][1] for a in acts})
    top, gap, foot = (54, 150, 52) if TXT > 1 else (62, 168, 70)   # 문서용: 행 간격·아래 여백을 줄여 쪽 높이를 아낀다(칩은 두 줄까지 들어간다)
    ys = {r: top + gap * k for k, r in enumerate(rows)}
    W, H = 1024, top + gap * (len(rows) - 1) + foot
    geo = []
    for a in acts:
        x, r = BM_SLOTS[a["pos"]]
        w, h = (208, 96) if a.get("ours") else (172, 80)     # 좌우 상자 사이에 '무엇 · 언제' 칩이 들어갈 간격
        geo.append(((x, ys[r]), w / 2, h / 2))
    names = {a["name"]: i for i, a in enumerate(acts)}
    idx = lambda k: names.get(k, k) if not isinstance(k, int) else k
    mk = lambda mid, color: (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="11" markerHeight="11" '
                             f'markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="{color}"/></marker>')
    money_c, value_c, goods_c = darker(A, 0.8), MUTED, INK2
    s = [f'<defs>{mk("am", money_c)}{mk("av", value_c)}{mk("ag", goods_c)}</defs>']
    lines, chips = [], []
    pair_n = {}
    for f in flows:
        i, j = idx(f["from"]), idx(f["to"])
        if not (isinstance(i, int) and isinstance(j, int)) or max(i, j) >= len(acts) or i == j:
            continue
        a, b = sorted((i, j))
        k = pair_n.get((a, b), 0)
        pair_n[(a, b)] = k + 1
        (ca, hwa, hha), (cb, hwb, hhb) = geo[a], geo[b]
        dx, dy = cb[0] - ca[0], cb[1] - ca[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L                         # 짝마다 같은 법선 — 오가는 화살표가 양쪽으로 갈린다
        off = [-15, 15, -40, 40][k % 4]
        ci, cj = (geo[i][0], geo[j][0])
        pi = (ci[0] + nx * off, ci[1] + ny * off)
        pj = (cj[0] + nx * off, cj[1] + ny * off)
        ex, ey = pj[0] - pi[0], pj[1] - pi[1]
        el = math.hypot(ex, ey) or 1
        d = (ex / el, ey / el)
        t0 = _clip(pi, d, ci, geo[i][1] + 5, geo[i][2] + 5)
        t1 = _clip(pj, (-d[0], -d[1]), cj, geo[j][1] + 9, geo[j][2] + 9)
        x1, y1 = pi[0] + d[0] * t0, pi[1] + d[1] * t0
        x2, y2 = pj[0] - d[0] * t1, pj[1] - d[1] * t1
        kind = f.get("kind", "value")
        color, width, dash, mid = {"money": (money_c, 2.6, "", "am"), "goods": (goods_c, 1.6, "", "ag")}.get(
            kind, (value_c, 1.8, ' stroke-dasharray="6 5"', "av"))
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{width}"{dash} '
                     f'marker-end="url(#{mid})"/>')
        label, detail = f.get("label", ""), f.get("detail", "")
        if label:
            fs = 13.5
            cw = tw(label, fs) + (tw(" · " + detail, 12) if detail else 0) + 20
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            vertical = abs(dy) > abs(dx) * 0.6
            room = math.hypot(x2 - x1, y2 - y1) - 14          # 가로 선: 칩이 두 상자 사이에 들어가야 한다
            two = bool(detail) and not vertical and cw > room  # 안 들어가면 '무엇'과 '언제'를 두 줄로
            if two:
                cw = max(tw(label, fs), tw(detail, 12)) + 20
            if not vertical and cw > room:                     # 그래도 넘치면 글자를 조금 줄인다(최소 0.82배)
                f_ = max(0.82, MIN_FS / fs, (room - 20) / (cw - 20))   # 문서용 최소 글자 아래로는 줄이지 않는다
                fs, cw = fs * f_, (cw - 20) * f_ + 20
            chh = (40 if two else 24) * TXT
            if vertical:                                       # 세로에 가까운 선: 칩을 그 선이 비켜 선 쪽 바깥으로
                side = 1 if nx * off >= 0 else -1
                mx += side * (cw / 2 + 8)
            else:                                              # 가로 선: 오가는 두 칩이 맞닿지 않게 바깥쪽으로 민다
                push = max(0.0, chh / 2 - abs(off) + 3)
                my += (1 if ny * off >= 0 else -1) * push
            money = kind == "money"
            # 칩은 '무엇을 주고받는가'를 같은 무게로 보인다 — 돈 칩만 옅은 강조색 바탕으로 구분
            if two:
                body_ = (f'<text x="{mx:.1f}" y="{my - chh / 2 + 18 * TXT:.1f}" text-anchor="middle" font-size="{fs:.1f}" '
                         f'font-weight="600" fill="{INK}">{html.escape(label)}'
                         f'<tspan x="{mx:.1f}" dy="{16 * TXT:.1f}" font-size="12" font-weight="500" fill="{MUTED}">'
                         f'{html.escape(detail)}</tspan></text>')
            else:
                sub = f'<tspan font-size="12" font-weight="500" fill="{MUTED}"> · {html.escape(detail)}</tspan>' if detail else ""
                body_ = (f'<text x="{mx:.1f}" y="{my + 5 * TXT:.1f}" text-anchor="middle" font-size="{fs:.1f}" '
                         f'font-weight="600" fill="{INK}">{html.escape(label)}{sub}</text>')
            chips.append(f'<rect x="{mx - cw / 2:.1f}" y="{my - chh / 2:.1f}" width="{cw:.1f}" height="{chh:.1f}" '
                         f'rx="{min(chh / 2, 12 * TXT):.1f}" '
                         f'fill="{mix(A, 0.12) if money else "#fff"}" stroke="{mix(A, 0.35) if money else GRAY_FILL}"/>{body_}')
    boxes = []
    for a, ((x, y), hw, hh) in zip(acts, geo):
        ours = a.get("ours")
        boxes.append(f'<rect x="{x - hw}" y="{y - hh}" width="{2 * hw}" height="{2 * hh}" rx="14" '
                     f'fill="{A if ours else "#fff"}" stroke="{A if ours else GRAY_FILL}" stroke-width="{0 if ours else 1.5}"/>')
        tag = a.get("tag") or ("결제자" if a.get("payer") else "")
        if tag:
            tw_, th = tw(tag, 11.5) + 14, fsz(11.5) + 8.5
            boxes.append(f'<rect x="{x - tw_ / 2:.1f}" y="{y - hh - th / 2 - 1:.1f}" width="{tw_:.1f}" height="{th:.1f}" '
                         f'rx="{th / 2:.1f}" fill="{INK}"/>'
                         f'<text x="{x}" y="{y - hh - 1 + fsz(11.5) * 0.36:.1f}" text-anchor="middle" font-size="11.5" '
                         f'font-weight="700" fill="#fff">{html.escape(tag)}</text>')
        boxes.append(f'<text x="{x}" y="{y - 3}" text-anchor="middle" font-size="{19 if ours else 17}" font-weight="700" '
                     f'fill="{"#fff" if ours else INK}">{html.escape(a["name"])}</text>')
        if a.get("role"):
            boxes.append(f'<text x="{x}" y="{y + 20}" text-anchor="middle" font-size="13" fill="{"#fff" if ours else MUTED}" '
                         f'fill-opacity="{0.92 if ours else 1}">{html.escape(a["role"])}</text>')
    s += lines + boxes + chips
    kinds = {f.get("kind", "value") for f in flows}
    leg = ['<span><i class="ln" style="background:var(--accent-ink)"></i>돈(사용료·구독료·수수료)</span>'] if "money" in kinds else []
    leg += ['<span><i class="ln dash"></i>서비스·가치</span>'] if "value" in kinds else []
    leg += [f'<span><i class="ln" style="background:{goods_c};height:2px"></i>물건·데이터</span>'] if "goods" in kinds else []
    out = f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(s)}</svg><div class="legend">{"".join(leg)}</div>'
    if v.get("formula"):
        out += _formula(v["formula"])
    if v.get("streams"):
        out += '<div class="streams">' + "".join(
            f'<div class="strm"><b>{esc(x["name"])}</b><span>{esc(x.get("how", ""))}</span>'
            f'{chip(x["share"], "st") if x.get("share") else ""}</div>' for x in v["streams"]) + "</div>"
    return out


def v_kpi(v, A):
    """tiles: [{label, value, basis, status}] — 매출 · 투자 · 고용처럼 3개."""
    tiles = "".join(
        f'<div class="tile"><div class="tl">{esc(t["label"])}{chip(t["status"], "st") if t.get("status") else ""}</div>'
        f'<div class="tv{" long" if len(str(t["value"])) > 7 else ""}">{esc(t["value"])}</div><div class="tbs">{esc(t.get("basis", ""))}</div></div>'
        for t in v["tiles"])
    return f'<div class="kpis" style="grid-template-columns:repeat({len(v["tiles"])},1fr)">{tiles}</div>'


def v_roadmap(v, A):
    """periods: [..], rows: [{axis, cells}], kpi: {axis, cells}. 칸 글이 '★'로 시작하면 변곡점으로 강조."""
    per = v["periods"]
    cols = f"140px repeat({len(per)}, 1fr)"
    out = [f'<div class="rm" style="grid-template-columns:{cols}"><div class="rh"></div>']
    out += [f'<div class="rh">{esc(p)}</div>' for p in per]
    for row in v["rows"] + ([v["kpi"]] if v.get("kpi") else []):
        is_kpi = row is v.get("kpi")
        out.append(f'<div class="ra{" kpi" if is_kpi else ""}">{esc(row["axis"])}</div>')
        for c in row["cells"]:
            star = str(c).startswith("★")
            out.append(f'<div class="rc{" kpi" if is_kpi else ""}{" star" if star else ""}">{esc(c)}</div>')
    out.append("</div>")
    return "".join(out)


def v_ps_map(v, A):
    """rows: [{no, problem, evidence, solution, benefit}] — 문제 n → 솔루션 n → 고객 편익."""
    circled = {chr(0x2460 + i): str(i + 1) for i in range(20)}      # ①② → 1 2 (원 안에 원이 겹치지 않게)
    out = ['<div class="ps"><div class="psh">문제</div><div></div><div class="psh">해결</div><div></div><div class="psh">고객이 얻는 것</div>']
    for i, r in enumerate(v["rows"], 1):
        no = circled.get(str(r.get("no", "")).strip(), str(r.get("no", "")).strip() or str(i))
        ev = f'<small>{esc(r["evidence"])}</small>' if r.get("evidence") else ""
        out.append(f'<div class="psc prob"><span class="no">{esc(no)}</span><b>{esc(r["problem"])}</b>{ev}</div>'
                   '<div class="arr">→</div>'
                   f'<div class="psc sol"><span class="no">{esc(no)}</span><b>{esc(r["solution"])}</b></div>'
                   '<div class="arr">→</div>'
                   f'<div class="psc ben"><b>{esc(r["benefit"])}</b></div>')
    out.append("</div>")
    return "".join(out)


def v_gantt(v, A):
    """periods: 열 이름(월·분기), tasks: [{name, start(1부터), length, status:'완료'|'진행'|'예정', out(산출물)}],
    milestones: [{label, at(열 번호)}]. 상태는 진하기로(완료 진함 · 진행 강조 · 예정 옅은 점선) 구분한다."""
    per, n = v["periods"], len(v["periods"])
    cols = f"190px repeat({n}, 1fr)"
    cls = {"완료": "done", "진행": "doing", "예정": "todo"}
    out = [f'<div class="gt" style="grid-template-columns:{cols}"><div class="gh"></div>']
    out += [f'<div class="gh">{esc(p)}</div>' for p in per]
    out.append("</div>")
    col_w = (BODY_W - 190) / n
    for t in v["tasks"]:
        st = cls.get(t.get("status", "예정"), "todo")
        start = max(1, min(int(t["start"]), n))
        span = max(1, min(int(t.get("length", 1)), n - start + 1))
        cells = "".join(f'<div class="gc" style="grid-column:{i + 2};grid-row:1"></div>' for i in range(n))
        text = str(t.get("out", "") or t.get("status", ""))
        label = f'<span>{esc(text)}</span>'                 # flex 안에서 '○○' 앞뒤 띄어쓰기가 사라지지 않게 감싼다
        bar = f'<div class="gb {st}" style="grid-column:{start + 1} / span {span};grid-row:1">'
        if tw(text, 12.5) / TXT + 28 <= span * col_w:
            bar += f'{label}</div>'
        elif start + span <= n:                              # 막대에 안 들어가면 오른쪽 빈칸에, 끝 열이면 왼쪽에
            bar += f'</div><div class="gb-out" style="grid-column:{start + span + 1} / {n + 2};grid-row:1">{label}</div>'
        else:
            bar += f'</div><div class="gb-out l" style="grid-column:2 / {start + 1};grid-row:1">{label}</div>'
        out.append(f'<div class="gt grow" style="grid-template-columns:{cols}">'
                   f'<div class="gn" style="grid-row:1">{esc(t["name"])}</div>{cells}{bar}</div>')
    if v.get("milestones"):
        cells = "".join(f'<div class="gc" style="grid-column:{i + 2};grid-row:1"></div>' for i in range(n))
        # 글자는 마름모 아래 가운데 — 이웃 열의 마일스톤과 옆으로 맞붙지 않는다
        marks = "".join(f'<div class="gm" style="grid-column:{max(1, min(int(m["at"]), n)) + 1};grid-row:1">'
                        f'<i></i><span>{esc(m["label"])}</span></div>' for m in v["milestones"])
        out.append(f'<div class="gt grow ms" style="grid-template-columns:{cols}"><div class="gn" style="grid-row:1">'
                   f'마일스톤</div>{cells}{marks}</div>')
    legend = ('<div class="legend small"><span><i class="gl done"></i>완료</span><span><i class="gl doing"></i>진행</span>'
              '<span><i class="gl todo"></i>예정</span></div>')
    return "".join(out) + legend


def img_src(path):
    """spec 폴더 기준 이미지 경로 → data URI(한 파일로 들고 다니게). 없으면 None."""
    if not path:
        return None
    p = path if os.path.isabs(path) else os.path.join(BASE_DIR, path)
    if not os.path.isfile(p):
        return None
    ext = os.path.splitext(p)[1].lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp", "svg": "svg+xml"}.get(ext, "png")
    with open(p, "rb") as f:
        return f"data:image/{mime};base64," + base64.b64encode(f.read()).decode()


def _slot(what, kind="사진"):
    """자료가 아직 없을 때의 자리 — 무엇을 넣을지 보이게."""
    return f'<div class="slot"><span>{esc(kind)} 자리</span><b>{esc(what)}</b></div>'


def v_flow(v, A):
    """steps: [{title, sub, who, ours}] 왼쪽→오른쪽 3~6단계(서비스 구조·공정·사용 흐름).
    loop: true면 마지막 → 처음 되돌이(선순환), loop_label. 단계 번호는 자동."""
    st = v["steps"]
    cards = []
    for i, s in enumerate(st, 1):
        who = f'<div class="fw-who">{esc(s["who"])}</div>' if s.get("who") else ""
        sub = f'<small>{esc(s["sub"])}</small>' if s.get("sub") else ""
        cards.append(f'<div class="fw{" ours" if s.get("ours") else ""}">{who}<span class="fw-n">{i}</span>'
                     f'<b>{esc(s["title"])}</b>{sub}</div>')
    out = f'<div class="flow" style="grid-template-columns:repeat({len(st)},1fr)">{"".join(cards)}</div>'
    if v.get("loop"):
        edge = 50 / len(st)
        out += (f'<div class="loopbar" style="margin:0 {edge}%"><span>{esc(v.get("loop_label", "다시 처음으로"))}</span></div>')
    return out


def v_screens(v, A):
    """screens: [{no, title, desc, src | ui: {title, rows[], highlight(번호), button}}] 3~4개.
    화면 캡처가 없으면 ui로 간단한 화면 틀을 그린다(문제 n ↔ 솔루션 n ↔ 화면 n 번호를 맞춘다)."""
    out = []
    circled = {chr(0x2460 + i): str(i + 1) for i in range(20)}
    for i, sc in enumerate(v["screens"], 1):
        no = circled.get(str(sc.get("no", "")).strip(), str(sc.get("no", "")).strip() or str(i))
        src = img_src(sc.get("src"))
        if src:
            inner = f'<img src="{src}" alt="">'
        elif sc.get("ui"):
            ui = sc["ui"]
            rows = "".join(f'<div class="ui-row{" on" if k == ui.get("highlight") else ""}">{esc(r)}</div>'
                           for k, r in enumerate(ui.get("rows", []), 1))
            btn = f'<div class="ui-btn">{esc(ui["button"])}</div>' if ui.get("button") else ""
            inner = f'<div class="ui"><div class="ui-top">{esc(ui.get("title", ""))}</div>{rows}{btn}</div>'
        else:
            inner = _slot(sc.get("what", sc.get("title", "")), "화면")
        mock = "" if src else " mock"                     # 그린 화면 틀은 인쇄에서 낮춰도 된다(캡처는 비율을 지킨다)
        out.append(f'<div class="scr"><div class="phone{mock}">{inner}</div><div class="scr-cap"><span class="no">{esc(no)}</span>'
                   f'<b>{esc(sc.get("title", ""))}</b><small>{esc(sc.get("desc", ""))}</small></div></div>')
    return f'<div class="screens" style="grid-template-columns:repeat({len(out)},1fr)">{"".join(out)}</div>'


def v_photos(v, A):
    """items: [{src | what, caption, date, place, badge}], cols(기본 3). 사진이 없으면 무엇을 찍을지 적힌 점선 자리.
    캡션은 '무엇인지 + 언제 · 어디서 · 몇 명'(섹션 설계도 3-3)."""
    cols = v.get("cols") or min(4, max(2, len(v["items"])))
    out = []
    for it in v["items"]:
        src = img_src(it.get("src"))
        frame = f'<img src="{src}" alt="">' if src else _slot(it.get("what", it.get("caption", "")))
        meta = " · ".join(x for x in (it.get("date"), it.get("place")) if x)
        badge = f'<span class="ph-badge">{esc(it["badge"])}</span>' if it.get("badge") else ""
        out.append(f'<figure class="pho">{badge}<div class="ph-frame">{frame}</div><figcaption><b>{esc(it.get("caption", ""))}</b>'
                   f'{f"<small>{esc(meta)}</small>" if meta else ""}</figcaption></figure>')
    return f'<div class="photos" style="grid-template-columns:repeat({cols},1fr)">{"".join(out)}</div>'


def v_persona(v, A):
    """cards: [{name, def, tags[], scene, pains: [{text, hypothesis}], verified: 'n/N', size}] 1~2장.
    불편 장면은 심리 → 기회비용 → 금전 순. 실제 발언만 따옴표, 인터뷰 전이면 hypothesis: true(가설)."""
    out = []
    labels = ["심리", "기회비용", "금전"]
    for c in v["cards"]:
        tags = "".join(f'<span class="pt">#{esc(t)}</span>' for t in c.get("tags", []))
        pains = []
        for k, p in enumerate(c.get("pains", [])):
            hyp = p.get("hypothesis")
            txt = esc(p["text"]) if hyp else f'“{esc(p["text"])}”'
            pains.append(f'<div class="pp"><span class="pk">{labels[k] if k < 3 else ""}</span><p>{txt}'
                         f'{chip("가설", "lv-assume") if hyp else ""}</p></div>')
        ver = c.get("verified")
        foot = (f'<div class="pv">검증 <b>{esc(ver)}</b></div>' if ver else '<div class="pv off">검증 전 — 인터뷰 후 n/N 기록</div>')
        size = f'<div class="psize">{esc(c["size"])}</div>' if c.get("size") else ""
        out.append(f'<div class="persona"><div class="pl"><div class="pname">{esc(c["name"])}</div>{size}'
                   f'<div class="pdef">{esc(c.get("def", ""))}</div><div class="ptags">{tags}</div>'
                   f'<div class="pscene">{esc(c.get("scene", ""))}</div>{foot}</div>'
                   f'<div class="pr"><div class="pr-h">불편 장면</div>{"".join(pains)}</div></div>')
    return f'<div class="personas{" two" if len(out) == 2 else ""}">{"".join(out)}</div>'


def v_quotes(v, A):
    """items: [{text, who, source, date, pending}] — 실제 발언·글만(인터뷰 메모·리뷰·커뮤니티 글). 3~4개.
    아직 듣지 않은 장면은 pending: true(또는 '['로 시작) — 따옴표 없이 점선으로 보인다."""
    out = "".join(f'<blockquote class="qt{" pend" if q.get("pending") or str(q["text"]).startswith("[") else ""}"><p>{esc(q["text"])}</p><footer><b>{esc(q.get("who", ""))}</b>'
                  f'<span>{esc(" · ".join(x for x in (q.get("source"), q.get("date")) if x))}</span></footer></blockquote>'
                  for q in v["items"])
    return f'<div class="quotes" style="grid-template-columns:repeat({min(len(v["items"]), 3)},1fr)">{out}</div>'


def v_survey(v, A):
    """question, n(응답 수), options: [{label, value(%)}], highlight(라벨, 생략 시 가장 큰 값), keep_order.
    값이 비율이 아니라 명 수면 unit: '명'으로 주고 %를 자동 계산한다."""
    opts = list(v["options"])
    if not v.get("keep_order"):
        opts.sort(key=lambda o: -o["value"])
    unit = v.get("unit", "%")
    total = sum(o["value"] for o in opts) if unit != "%" else None
    top = v.get("highlight") or opts[0]["label"]
    mx = max(o["value"] for o in opts) or 1
    rows = []
    for o in opts:
        on = o["label"] == top
        val = f'{o["value"]:g}%' if unit == "%" else f'{pct(o["value"], total)} ({fmt(o["value"])}{esc(unit)})'
        rows.append(f'<div class="br"><div class="bl{" b" if on else ""}">{esc(o["label"])}</div><div class="bt">'
                    f'<div class="bb" style="width:{o["value"] / mx * 82:.1f}%;background:{"var(--accent)" if on else GRAY_FILL}"></div>'
                    f'<span class="bv{" b" if on else ""}">{val}</span></div></div>')
    n = f' <span>(n={esc(v["n"])})</span>' if v.get("n") else ""
    q = f'<div class="sq">Q. {esc(v["question"])}{n}</div>' if v.get("question") else ""
    return f'{q}<div class="bars">{"".join(rows)}</div>'


def v_donut(v, A):
    """parts: [{label, value}] 5조각 이하, unit, highlight(라벨, 생략 시 가장 큰 조각), center: {value, label}."""
    parts = v["parts"]
    tot = sum(p["value"] for p in parts) or 1
    hi = v.get("highlight") or max(parts, key=lambda p: p["value"])["label"]
    grays = ["#c9c7c0", "#dad8d1", "#b3b1aa", "#e6e4de", "#a3a19a"]
    cx = cy = 130
    r, w = 104, 36
    s, ang, legend, g = [], -90.0, [], 0
    for p in parts:
        sweep = p["value"] / tot * 360
        color = A if p["label"] == hi else grays[g % len(grays)]
        if p["label"] != hi:
            g += 1
        a0, a1 = math.radians(ang + 0.8), math.radians(ang + sweep - 0.8)     # 조각 사이 흰 틈
        large = 1 if sweep - 1.6 > 180 else 0
        x0, y0, x1, y1 = cx + r * math.cos(a0), cy + r * math.sin(a0), cx + r * math.cos(a1), cy + r * math.sin(a1)
        s.append(f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f}" fill="none" stroke="{color}" '
                 f'stroke-width="{w}"/>')
        ang += sweep
        legend.append(f'<div class="dl{" b" if p["label"] == hi else ""}"><i style="background:{color}"></i><span>{esc(p["label"])}</span>'
                      f'<b>{pct(p["value"], tot)}</b>'
                      + ("" if v.get("unit", "") == "%" else f'<small>{fmt(p["value"])}{esc(v.get("unit", ""))}</small>') + '</div>')
    c = v.get("center") or {"value": pct(next(p["value"] for p in parts if p["label"] == hi), tot), "label": hi}
    if not isinstance(c, dict):                             # 문자열로 주면 값만 쓴다
        c = {"value": str(c), "label": ""}
    s.append(f'<text x="{cx}" y="{cy + 2}" text-anchor="middle" font-size="30" font-weight="800" fill="{INK}">{html.escape(str(c["value"]))}</text>'
             f'<text x="{cx}" y="{cy + 26}" text-anchor="middle" font-size="13" fill="{INK2}">{html.escape(str(c.get("label", "")))}</text>')
    return (f'<div class="donut"><svg width="260" height="260" viewBox="0 0 260 260">{"".join(s)}</svg>'
            f'<div class="dleg">{"".join(legend)}</div></div>')


def v_venn(v, A):
    """sets: [{label, items[]}] 2~3개, center(교집합 = 우리 자리), center_note."""
    sets = v["sets"][:3]
    W, H = 1024, 380
    if len(sets) == 2:
        cs, R = [(400, 190), (624, 190)], 160
    else:
        cs, R = [(420, 150), (604, 150), (512, 290)], 135
    vid = re.sub(r"\W", "", str(v.get("id", "v")))
    s = [f'<defs>' + "".join(f'<clipPath id="vc{vid}{k}"><circle cx="{x}" cy="{y}" r="{R}"/></clipPath>' for k, (x, y) in enumerate(cs)) + '</defs>']
    for (x, y), st in zip(cs, sets):
        s.append(f'<circle cx="{x}" cy="{y}" r="{R}" fill="{GRAY}" fill-opacity="0.1" stroke="{GRAY}" stroke-width="1.5"/>')
    # 모두가 겹치는 칸(우리 자리)만 강조색으로 칠한다
    inner = f'<circle cx="{cs[-1][0]}" cy="{cs[-1][1]}" r="{R}" fill="{mix(A, 0.28)}"/>'
    for k in range(len(cs) - 1):
        inner = f'<g clip-path="url(#vc{vid}{k})">{inner}</g>'
    s.append(inner)
    pos = ([(cs[0][0] - R * 0.45, cs[0][1]), (cs[1][0] + R * 0.45, cs[1][1])] if len(sets) == 2 else
           [(cs[0][0] - R * 0.42, cs[0][1] - R * 0.3), (cs[1][0] + R * 0.42, cs[1][1] - R * 0.3), (cs[2][0], cs[2][1] + R * 0.5)])
    for (x, y), st in zip(pos, sets):
        anchor = "middle"
        s.append(f'<text x="{x:.0f}" y="{y - 10:.0f}" text-anchor="{anchor}" font-size="16" font-weight="700" fill="{INK}">'
                 f'{html.escape(st["label"])}</text>')
        for k, it in enumerate(st.get("items", [])[:3]):
            s.append(f'<text x="{x:.0f}" y="{y + 14 + k * 19:.0f}" text-anchor="{anchor}" font-size="13" fill="{INK2}">'
                     f'{html.escape(it)}</text>')
    mx = sum(x for x, _ in cs) / len(cs)
    my = sum(y for _, y in cs) / len(cs) + (0 if len(sets) == 2 else -6)
    label = v.get("center", "우리")
    cw = tw(label, 17) + 36
    s.append(f'<rect x="{mx - cw / 2:.0f}" y="{my - 18:.0f}" width="{cw:.0f}" height="36" rx="18" fill="{A}"/>'
             f'<text x="{mx:.0f}" y="{my + 6:.0f}" text-anchor="middle" font-size="17" font-weight="800" fill="#fff">{html.escape(label)}</text>')
    if v.get("center_note"):
        s.append(f'<text x="{mx:.0f}" y="{my + 40:.0f}" text-anchor="middle" font-size="12.5" font-weight="600" fill="{INK}" {HALO}>'
                 f'{html.escape(v["center_note"])}</text>')
    return f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(s)}</svg>'


def v_segments(v, A):
    """rows: [{name, size(숫자), size_label, growth('+12%'), note, chosen}], unit — 세분 시장 중 고른 곳을 보여 준다."""
    rows = v["rows"]
    mx = max((r.get("size") or 0) for r in rows) or 1
    out = ['<div class="seg seg-h"><span>세분 시장</span><span>규모</span><span>성장</span><span>특징</span></div>']
    for r in rows:
        on = r.get("chosen")
        g = str(r.get("growth", ""))
        gcls = "up" if g.startswith("+") else "down" if g.startswith(("-", "−")) else ""
        size = r.get("size_label") or (f'{fmt(r["size"])}{v.get("unit", "")}' if r.get("size") is not None else "○○")
        bar = (f'<div class="segbar"><i style="width:{(r.get("size") or 0) / mx * 100:.1f}%;'
               f'background:{"var(--accent)" if on else GRAY_FILL}"></i></div>')
        out.append(f'<div class="seg{" on" if on else ""}"><b>{esc(r["name"])}{" <em>선택</em>" if on else ""}</b>'
                   f'<div class="segsz">{bar}<span>{esc(size)}</span></div><span class="gr {gcls}">{esc(g)}</span>'
                   f'<small>{esc(r.get("note", ""))}</small></div>')
    return "".join(out)


def _sum_line(total, target, unit, word="목표"):
    if target is None:
        return f'<div class="sumline">합계 <b>{fmt(total)}{esc(unit)}</b></div>'
    ok = abs(total - target) <= max(abs(target) * 0.005, 0.5)
    return (f'<div class="sumline{"" if ok else " bad"}">합계 <b>{fmt(total)}{esc(unit)}</b> '
            f'{"=" if ok else "≠"} {word} <b>{fmt(target)}{esc(unit)}</b>{"" if ok else " — 숫자를 맞춘다"}</div>')


def v_revenue_mix(v, A):
    """channels: [{name, formula('○○개 × ○○원'), amount(숫자, 없으면 생략)}], unit, target — 채널 합이 목표와 같은지 보인다."""
    ch = v["channels"]
    known = [c["amount"] for c in ch if isinstance(c.get("amount"), (int, float))]
    mx = max(known, default=0) or 1           # 채널이 모두 0원이어도 막대 비율이 0으로 나뉘지 않게
    rows = []
    for c in ch:
        amt = c.get("amount")
        has = isinstance(amt, (int, float))
        bar = (f'<i style="width:{amt / mx * 100:.1f}%"></i>' if has else '<i class="none"></i>')
        rows.append(f'<div class="rv"><b>{esc(c["name"])}</b><small>{esc(c.get("formula", ""))}</small>'
                    f'<div class="rvbar">{bar}</div><span>{fmt(amt) + esc(v.get("unit", "")) if has else esc(amt or "○○")}</span></div>')
    tail = _sum_line(sum(known), v.get("target"), v.get("unit", "")) if known and len(known) == len(ch) else (
        '<div class="sumline">합계 — 미확보 채널이 있어 아직 계산하지 않는다</div>')
    return f'<div class="rvs">{"".join(rows)}</div>{tail}'


def v_budget(v, A):
    """items: [{name, basis(산출 근거), amount}], unit, cap(상한) — 비목 구성 막대 + 산출 근거 표 + 상한 검산."""
    items = v["items"]
    known = [i["amount"] for i in items if isinstance(i.get("amount"), (int, float))]
    tot = sum(known) or 1
    shades = [1, 0.72, 0.5, 0.34, 0.22, 0.14]
    seg, rows = [], []
    for k, it in enumerate(items):
        amt = it.get("amount")
        has = isinstance(amt, (int, float))
        col = mix(A, shades[k % len(shades)])
        fg = "#fff" if shades[k % len(shades)] >= 0.5 else INK
        if has and amt / tot >= 0.06:
            seg.append(f'<div class="bgs" style="flex:{amt};background:{col};color:{fg}">{esc(it["name"])} {pct(amt, tot)}</div>')
        elif has:
            seg.append(f'<div class="bgs" style="flex:{amt};background:{col}"></div>')
        rows.append(f'<tr><td><i class="sw" style="background:{col}"></i>{esc(it["name"])}</td><td>{esc(it.get("basis", ""))}</td>'
                    f'<td class="num">{fmt(amt) if has else esc(amt or "○○")}</td><td class="num">{pct(amt, tot) if has else "—"}</td></tr>')
    bar = f'<div class="bgbar">{"".join(seg)}</div>' if known else ""
    unit = v.get("unit", "")
    table = (f'<table class="tb"><thead><tr><th>비목</th><th>산출 근거</th><th class="num">금액({esc(unit)})</th>'
             f'<th class="num">비율</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')
    tail = _sum_line(sum(known), v.get("cap"), unit, "상한") if len(known) == len(items) else (
        '<div class="sumline">합계 — ○○ 칸이 있어 상한 검산은 금액 확정 후</div>')
    return bar + table + tail


def v_waterfall(v, A):
    """start: {label, value}(판매가·객단가), steps: [{label, value(음수 = 빼는 원가)}], end_label('마진'), unit — 단위 경제성."""
    start, steps = v["start"], v["steps"]
    vals = [start["value"]] + [s["value"] for s in steps]
    end = sum(vals)
    labels = [start["label"]] + [s["label"] for s in steps] + [v.get("end_label", "마진")]
    W, H, L, R, T, B = 1024, 330, 40, 1000, 34, 290
    top = max(start["value"], end) * 1.12 or 1
    py = lambda y: B - (B - T) * y / top
    n = len(labels)
    band = (R - L) / n
    bw = min(64, band * 0.5)
    s = [f'<line x1="{L}" y1="{B}" x2="{R}" y2="{B}" stroke="{BASE}"/>']
    run = 0.0
    for k, lab in enumerate(labels):
        x = L + band * (k + 0.5)
        if k == 0:
            y0, y1, color, val = 0, start["value"], darker(A, 0.85), start["value"]
            run = start["value"]
        elif k == n - 1:
            y0, y1, color, val = 0, end, A, end
        else:
            val = steps[k - 1]["value"]
            y0, y1 = sorted((run, run + val))
            run += val
            color = GRAY_FILL if val < 0 else mix(A, 0.4)
        s.append(f'<rect x="{x - bw / 2:.1f}" y="{py(y1):.1f}" width="{bw:.1f}" height="{max(py(y0) - py(y1), 1):.1f}" rx="3" fill="{color}"/>')
        if 0 < k < n - 1 and k < n - 1:
            nx = L + band * (k + 1.5)
            s.append(f'<line x1="{x + bw / 2:.1f}" y1="{py(run):.1f}" x2="{nx - bw / 2:.1f}" y2="{py(run):.1f}" stroke="{BASE}" stroke-dasharray="3 3"/>')
        elif k == 0:
            nx = L + band * 1.5
            s.append(f'<line x1="{x + bw / 2:.1f}" y1="{py(run):.1f}" x2="{nx - bw / 2:.1f}" y2="{py(run):.1f}" stroke="{BASE}" stroke-dasharray="3 3"/>')
        sign = "" if k in (0, n - 1) or val < 0 else "+"
        s.append(f'<text x="{x:.1f}" y="{py(y1) - 8:.1f}" text-anchor="middle" font-size="14" font-weight="700" fill="{INK}">{sign}{fmt(val)}</text>')
        s.append(f'<text x="{x:.1f}" y="{B + 22}" text-anchor="middle" font-size="13" fill="{INK2}">{html.escape(lab)}</text>')
    end_l = v.get("end_label", "마진")
    last = end_l[-1:]
    jong = (ord(last) - 0xAC00) % 28 if "가" <= last <= "힣" else 0
    suffix = "율" if jong in (0, 4) else "률"            # 받침 없음·ㄴ 받침 → 율(마진율), 그 밖 → 률(이익률)
    rate = f'<div class="badge" style="left:auto;right:30px">{esc(end_l)}{suffix} <b>{pct(end, start["value"])}</b></div>'
    unit = f'<div class="unit" style="left:44px;right:auto">단위: {esc(v["unit"])}</div>' if v.get("unit") else ""
    return f'<div class="rel">{rate}{unit}<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(s)}</svg></div>'


def v_columns(v, A):
    """labels(월·분기), values(없는 값은 null), unit, notes: [{at(인덱스), text}] 마일스톤, target: {value, label}, highlight: [인덱스].
    값 글은 첫 막대·강조 막대·최고점에 붙는다(헤드라인이 인용하는 값이 그림에 보이게). label_at: [인덱스]로 더하거나 "all"로 전부."""
    xs, ys = v["labels"], v["values"]
    known = [y for y in ys if isinstance(y, (int, float))]
    tg = v.get("target") or {}
    ticks = nice_ticks(0, max(known + [tg.get("value", 0)]) if known else 1)
    top = ticks[-1]
    W, H, L, R, T, B = 1024, 340, 60, 1000, 40, 298
    py = lambda y: B - (B - T) * y / top
    n = len(xs)
    band = (R - L) / n
    bw = min(46, band * 0.56)
    hl = set(v.get("highlight", [n - 1]))
    la = v.get("label_at", [])
    shown = set(range(n)) if la == "all" else hl | {0} | set(la) | (
        {max((k for k in range(n) if isinstance(ys[k], (int, float))), key=lambda k: ys[k])} if known else set())
    s = []
    for t in ticks:
        s.append(f'<line x1="{L}" y1="{py(t)}" x2="{R}" y2="{py(t)}" stroke="{GRID if t else BASE}"/>'
                 f'<text x="{L - 10}" y="{py(t) + 4}" text-anchor="end" font-size="12" fill="{MUTED}">{fmt(t)}</text>')
    for k, (lab, y) in enumerate(zip(xs, ys)):
        x = L + band * (k + 0.5)
        if isinstance(y, (int, float)):
            on = k in hl
            y1 = py(y)
            s.append(f'<path d="M{x - bw / 2},{B} L{x - bw / 2},{y1 + 4} Q{x - bw / 2},{y1} {x - bw / 2 + 4},{y1} L{x + bw / 2 - 4},{y1} '
                     f'Q{x + bw / 2},{y1} {x + bw / 2},{y1 + 4} L{x + bw / 2},{B} Z" fill="{A if on else mix(A, 0.32)}"/>')
            if k in shown:
                s.append(f'<text x="{x}" y="{y1 - 8}" text-anchor="middle" font-size="14" font-weight="{700 if on or k == 0 else 600}" '
                         f'fill="{INK if on or k == 0 else INK2}">{fmt(y)}</text>')
        else:
            s.append(f'<rect x="{x - bw / 2}" y="{B - 30}" width="{bw}" height="30" rx="3" fill="none" stroke="{GRAY}" stroke-dasharray="4 3"/>'
                     f'<text x="{x}" y="{B - 38}" text-anchor="middle" font-size="12" fill="{MUTED}">○○</text>')
        s.append(f'<text x="{x}" y="{B + 22}" text-anchor="middle" font-size="13" fill="{INK2}">{html.escape(str(lab))}</text>')
    if tg.get("value") is not None:
        s.append(f'<line x1="{L}" y1="{py(tg["value"])}" x2="{R}" y2="{py(tg["value"])}" stroke="{INK2}" stroke-dasharray="6 5"/>'
                 f'<text x="{R}" y="{py(tg["value"]) - 8}" text-anchor="end" font-size="12.5" font-weight="700" fill="{INK2}" {HALO}>'
                 f'{html.escape(tg.get("label", "목표"))} {fmt(tg["value"])}</text>')
    for nt in v.get("notes", []):
        k = nt["at"]
        x = L + band * (k + 0.5)
        y = ys[k] if isinstance(ys[k], (int, float)) else 0
        yt = max(T - 22, py(y) - 34)
        s.append(f'<text x="{x}" y="{yt}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{darker(A, 0.8)}" {HALO}>'
                 f'★ {html.escape(nt["text"])}</text>')
    unit = f'<div class="unit">단위: {esc(v["unit"])}</div>' if v.get("unit") else ""
    return f'<div class="rel">{unit}<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(s)}</svg></div>'


def v_stairs(v, A):
    """steps: [{period, title, items[], kpi}] 3~4단 — 단계별 성장(왼쪽 아래 → 오른쪽 위). 마지막 단이 강조."""
    st = v["steps"]
    n = len(st)
    out = []
    for k, s in enumerate(st):
        h = 52 + 48 * k / max(n - 1, 1)
        last = k == n - 1
        items = "".join(f"<li>{esc(i)}</li>" for i in s.get("items", []))
        kpi = f'<div class="sk-kpi">{esc(s["kpi"])}</div>' if s.get("kpi") else ""
        out.append(f'<div class="stp" style="height:{h:.0f}%"><div class="stp-in{" last" if last else ""}" style="background:{A if last else mix(A, 0.1 + 0.22 * k / max(n - 1, 1))}">'
                   f'<span class="sp">{esc(s.get("period", ""))}</span><b>{esc(s["title"])}</b><ul>{items}</ul>{kpi}</div></div>')
    return f'<div class="stairs" style="grid-template-columns:repeat({n},1fr)">{"".join(out)}</div>'


def v_team(v, A):
    """members: [{role, name('○○'), duty, skills, status:'확보'|'예정'|'협의 중'}], plan: [{gap, how, when, budget}] 보완 계획."""
    cls = {"확보": "ok", "예정": "todo", "협의 중": "talk"}       # 그 밖의 상태(예: '파트타임 → 정규직 예정')는 글 그대로, 색은 '예정
    cards = []
    for m in v["members"]:
        st = m.get("status", "확보")
        cards.append(f'<div class="tm {cls.get(st, "todo")}"><div class="tm-top"><span class="tm-role">{esc(m["role"])}</span>'
                     f'<span class="tm-st">{esc(st)}</span></div><b>{esc(m.get("name", "○○"))}</b>'
                     f'<div class="tm-duty">{esc(m.get("duty", ""))}</div><small>{esc(m.get("skills", ""))}</small></div>')
    out = f'<div class="team" style="grid-template-columns:repeat({min(len(cards), 4)},1fr)">{"".join(cards)}</div>'
    if v.get("plan"):
        rows = "".join(f'<tr><td><b>{esc(p["gap"])}</b></td><td>{esc(p.get("how", ""))}</td><td>{esc(p.get("when", ""))}</td>'
                       f'<td>{esc(p.get("budget", ""))}</td></tr>' for p in v["plan"])
        out += (f'<table class="tb plan"><thead><tr><th>보완할 역량</th><th>방법 · 검증</th><th>시기</th><th>예산</th></tr></thead>'
                f'<tbody>{rows}</tbody></table>')
    return out


STAGES = ["접촉", "협의", "LOI", "MOU", "실적"]


def v_partners(v, A):
    """rows: [{name, ability(보유 역량), role(협력 내용), when(시기 · 조건), stage: 접촉|협의|LOI|MOU|실적}] — 단계 사다리로 격식을 보인다."""
    out = ['<div class="pt-row pt-h"><span>기관</span><span>보유 역량 · 협력 내용</span><span>시기</span><span>단계</span></div>']
    for r in v["rows"]:
        lv = STAGES.index(r["stage"]) if r.get("stage") in STAGES else -1
        dots = "".join(f'<i class="{"on" if k <= lv else ""}{" cur" if k == lv else ""}" title="{s}"></i>' for k, s in enumerate(STAGES))
        out.append(f'<div class="pt-row"><b>{esc(r["name"])}</b><div><span>{esc(r.get("ability", ""))}</span>'
                   f'<small>{esc(r.get("role", ""))}</small></div><span>{esc(r.get("when", ""))}</span>'
                   f'<div class="ladder"><div class="dots">{dots}</div><em>{esc(r.get("stage", "—"))}</em></div></div>')
    out.append('<div class="legend small">단계: 접촉 → 협의 → LOI → MOU → 실적 (증빙 범위 안에서 가장 높은 단계)</div>')
    return "".join(out)


def v_timeline(v, A):
    """events: [{date, title, desc, status:'완료'|'진행'|'예정'}] 3~7개 — 연혁·준비 경과."""
    ev = v["events"]
    cls = {"완료": "done", "진행": "doing", "예정": "todo"}
    items = "".join(f'<div class="tle {cls.get(e.get("status", "완료"), "done")}"><i></i><span class="tl-d">{esc(e["date"])}</span>'
                    f'<b>{esc(e["title"])}</b><small>{esc(e.get("desc", ""))}</small><em>{esc(e.get("status", ""))}</em></div>'
                    for e in ev)
    n = len(ev)
    last = max((k for k, e in enumerate(ev) if e.get("status", "완료") != "예정"), default=-1)
    span = f"calc({100 * (n - 1) / n:.2f}% + 8px)"
    prog = f"calc({100 * last / n:.2f}% + 8px)" if last > 0 else "0px"
    return (f'<div class="tline" style="grid-template-columns:repeat({n},1fr)">'
            f'<div class="tl-line" style="width:{span}"></div><div class="tl-prog" style="width:{prog}"></div>{items}</div>')


BMC = [("kp", "핵심 파트너"), ("ka", "핵심 활동"), ("kr", "핵심 자원"), ("vp", "가치 제안"), ("cr", "고객 관계"),
       ("ch", "채널"), ("cs", "고객 세그먼트"), ("cost", "비용 구조"), ("rev", "수익원")]


def v_bmc(v, A):
    """blocks: {kp, ka, kr, vp, cr, ch, cs, cost, rev} 각 항목 목록. highlight: 강조할 칸(기본 vp)."""
    b = v["blocks"]
    hl = v.get("highlight", "vp")
    cell = lambda k, name: (f'<div class="bmc-{k}{" on" if k == hl else ""}"><h4>{name}</h4><ul>'
                            + "".join(f"<li>{esc(x)}</li>" for x in b.get(k, [])) + "</ul></div>")
    return '<div class="bmc">' + "".join(cell(k, n) for k, n in BMC) + "</div>"


def v_table(v, A):
    """columns, rows(행 목록), highlight_col(번호), highlight_row(번호), total: true면 마지막 행을 합계로 보고 검산."""
    cols, rows = v["columns"], v["rows"]
    hc, hr = v.get("highlight_col"), v.get("highlight_row")
    isnum = lambda x: isinstance(x, (int, float)) or bool(re.fullmatch(r"[-+]?[\d,.]+\s*[%만억원명곳건개]*", str(x).strip()))
    head = "".join(f'<th class="{"num " if k and all(isnum(r[k]) for r in rows if k < len(r)) else ""}{"hc" if k == hc else ""}">{esc(c)}</th>'
                   for k, c in enumerate(cols))
    body = []
    for i, r in enumerate(rows):
        tot = v.get("total") and i == len(rows) - 1
        tds = "".join(f'<td class="{"num " if k and isnum(x) else ""}{"hc" if k == hc else ""}">{esc(fmt(x) if isinstance(x, (int, float)) else x)}</td>'
                      for k, x in enumerate(r))
        body.append(f'<tr class="{"tot" if tot else ""}{" hr" if i == hr else ""}">{tds}</tr>')
    return f'<table class="tb gen"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


RENDER = {"tam": v_tam, "positioning": v_positioning, "swot": v_swot, "bar": v_bar, "before_after": v_before_after,
          "trend": v_trend, "funnel": v_funnel, "pnl": v_pnl, "compare": v_compare, "bm": v_bm, "kpi": v_kpi,
          "roadmap": v_roadmap, "ps_map": v_ps_map, "gantt": v_gantt, "flow": v_flow, "screens": v_screens,
          "photos": v_photos, "persona": v_persona, "quotes": v_quotes, "survey": v_survey, "donut": v_donut,
          "venn": v_venn, "segments": v_segments, "revenue_mix": v_revenue_mix, "budget": v_budget,
          "waterfall": v_waterfall, "columns": v_columns, "stairs": v_stairs, "team": v_team, "partners": v_partners,
          "timeline": v_timeline, "bmc": v_bmc, "table": v_table}


# ---------------------------------------------------------------- 페이지

HTML_TYPES = (".swot,.strat,.bars,.bas,.funnel,.kpis,.rm,.ps,.gt,table.cmp,.flow,.screens,.photos,.personas,.quotes,"
              ".donut,.seg,.rvs,.bgbar,table.tb,.stairs,.team,.pt-row,.tline,.bmc,.fx,.streams")
PRINT_CSS = ("section.viz{width:860px;padding:24px 28px 18px}.kicker{display:none}"
             "h2.headline{font-size:22px}.sub{font-size:14px}.body{margin-top:16px}"
             ".takeaway{margin-top:14px;padding:9px 14px;font-size:15px}.note{margin-top:8px;font-size:13.5px}"
             ".legend{font-size:14px}.legend.small{font-size:13.5px}"
             "section.viz svg{max-width:100%;height:auto}"
             # 문서 쪽 높이를 아끼는 압축 — 그린 화면 틀은 낮게, 표·간트 행은 촘촘히, 페르소나 2장은 나란히
             ".phone.mock{aspect-ratio:9/13}.grow{min-height:38px}.gb{height:25px}"
             ".rc,.ra{padding:8px 9px}.rh{padding:4px 6px}"
             # 가장 작은 HTML 글자(11~11.5px)도 확대 후 7.5pt 안팎이 되게, 갤러리 바탕은 흰색(캡처 가장자리에 회색 선이 안 남게)
             "body{background:#fff}.chip,.dis,.fw-who,.ph-badge,.tle em,.pk,.pt,.fx-term small,.slot span,.tm-st,.seg b em,"
             "table.cmp thead th small,tr.vrow td,.pho figcaption small,.qt footer span{font-size:12px}"
             # 확대(zoom)를 받지 않는 자리(TAM 오른쪽 글, 단위, 되돌이 화살표 글)는 글자를 직접 키운다
             ".unit,.tam .chip,.loopbar span,.legend .unit-in{font-size:13.5px}.tam-formula{font-size:14px}"
             ".personas.two{grid-template-columns:1fr 1fr}.personas.two .persona{grid-template-columns:1fr}"
             ".pl{padding:14px 16px;gap:6px}.pr{padding:12px 16px;gap:6px}"
             ".q{padding:12px 16px 8px;min-height:0}.qh{margin-bottom:4px}.qh b{font-size:26px}.q li{margin:3px 0}"
             ".strat{margin-top:10px}.sc{padding:8px 12px}table.cmp th,table.cmp td{padding:8px 10px}"
             ".swot{gap:8px}.personas{gap:10px}.pp p{line-height:1.4}.pscene{line-height:1.45}"
             # 수익원 카드: 칩을 이름 줄 오른쪽에 둔다
             ".strm{padding:7px 12px;display:grid;grid-template-columns:1fr auto;column-gap:8px;row-gap:2px}"
             ".strm b{grid-area:1/1}.strm .chip{grid-area:1/2;margin:0;align-self:start}.strm>span{grid-area:2/1/3/3}"
             # 반폭(size: half) — 개요 이미지 칸용: 폭 430px, 제목·여백을 줄인다(HTML 유형 권장 — SVG는 글자가 함께 작아진다)
             "section.viz.half{width:430px;padding:12px 12px 8px}section.viz.half h2.headline{font-size:17px}"
             "section.viz.half .sub,section.viz.half .note{font-size:14px;margin-top:6px}"
             "section.viz.half .takeaway{font-size:14px;padding:6px 10px;margin-top:8px}section.viz.half .body{margin-top:8px}"
             "section.viz.half .phone{max-width:124px;border-width:5px;border-radius:20px}section.viz.half .scr-cap small{display:none}"
             "section.viz.half .ui{padding:8px 7px;gap:5px}section.viz.half .ui-top{font-size:11.5px;padding:2px 2px 5px}"
             "section.viz.half .ui-row{font-size:11px;padding:5px 6px}section.viz.half .ui-btn{font-size:11px;padding:6px}"
             + HTML_TYPES + "{zoom:1.15}"
             + ",".join("section.viz.half " + t for t in HTML_TYPES.split(",")) + "{zoom:1.3}")


def css(A, slide, print_=False):
    w = "1600px" if slide else "1120px"
    # 발표 장(16:9): 본문이 남는 높이를 채우고, SVG는 폭에 맞춰 키우되 높이를 넘지 않게
    extra = ("section.viz{height:900px;display:flex;flex-direction:column;padding:56px 72px 36px}"
             "section.viz .body{flex:1;min-height:0;position:relative;overflow:hidden}"
             ".fit{position:absolute;left:0;right:0;top:0;transform-origin:top center}"
             "section.viz .body>svg,section.viz .body>.rel>svg{width:100%;height:auto;max-height:540px}"
             ".tam," + HTML_TYPES + "{zoom:1.2}"
             "h2.headline{font-size:38px}.sub{font-size:18px}.takeaway{font-size:20px}.note{font-size:14px}") if slide else (
        PRINT_CSS if print_ else "")
    return f"""
:root{{--accent:{A};--accent-ink:{darker(A, 0.78)};--a50:{mix(A, 0.07)};--a100:{mix(A, 0.14)};--a200:{mix(A, 0.3)}}}
*{{box-sizing:border-box}}
body{{margin:0;background:#efeeeb;font-family:{FONT};color:{INK};-webkit-font-smoothing:antialiased}}
.page{{display:flex;flex-direction:column;gap:28px;padding:28px;align-items:flex-start}}
section.viz{{width:{w};background:#fff;padding:40px 48px 30px}}
.kicker{{font-size:13px;font-weight:700;color:var(--accent-ink);letter-spacing:.02em;margin-bottom:8px}}
h2.headline{{font-size:26px;line-height:1.38;font-weight:700;margin:0;letter-spacing:-.01em;word-break:keep-all}}
.sub{{font-size:15px;color:{INK2};margin:8px 0 0;word-break:keep-all}}
.body{{margin-top:26px}}
.takeaway{{margin-top:22px;padding:13px 18px;border-left:4px solid var(--accent);background:var(--a50);font-size:16px;font-weight:600;line-height:1.5;word-break:keep-all}}
.note{{margin-top:12px;font-size:12px;color:{MUTED}}}
.ph{{border-bottom:1.5px dashed {MUTED};color:{INK2};padding:0 1px}}
svg{{display:block;font-family:{FONT};overflow:visible}}
.rel{{position:relative}} .abs{{position:absolute;left:0;top:0}}
.legend{{display:flex;gap:22px;align-items:center;font-size:13px;color:{INK2};margin:10px 0 0}}
.legend.small{{font-size:12px;color:{MUTED};gap:16px}} .legend.small span{{display:inline-flex;align-items:center;gap:6px}} .legend.small .mk{{margin:0;width:14px;height:14px}}
.legend .dot{{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:7px;vertical-align:-1px}}
.legend .dot.ring{{background:#fff;border:2px solid {GRAY};width:12px;height:12px}}
.legend .sw{{display:inline-block;width:14px;height:14px;border-radius:3px;margin-right:7px;vertical-align:-2px}}
.legend .ln{{display:inline-block;width:22px;height:3px;border-radius:2px;margin-right:7px;vertical-align:3px}}
.legend .ln.dash{{background:repeating-linear-gradient(90deg,{MUTED} 0 6px,transparent 6px 11px)}}
.legend .unit-in{{margin-left:auto;color:{MUTED};font-size:12px}}
.chip{{display:inline-block;font-size:11.5px;font-weight:600;padding:2px 8px;border-radius:999px;border:1px solid {GRAY_FILL};color:{INK2};margin-left:8px;vertical-align:2px;white-space:nowrap}}
.chip.lv-ok{{background:#f1f0ec}} .chip.lv-calc{{background:#fff}} .chip.lv-obs{{background:#fff;border-style:solid}}
.chip.lv-assume{{background:#fff;border:1.5px dashed {GRAY};color:{MUTED}}}
.chip.st{{background:var(--a50);border-color:var(--a200);color:var(--accent-ink)}}
/* TAM */
.tam{{position:relative}}
.tam-row{{position:absolute;left:432px;right:0}}
.tam-val{{font-size:22px;font-weight:700;line-height:30px}}
.tam-name{{font-size:15px;font-weight:500;color:{INK2};margin-left:12px}}
.tam-formula{{font-size:13px;color:{MUTED};margin-top:2px}}
/* SWOT */
.swot{{display:grid;grid-template-columns:44px 1fr 1fr;gap:10px}}
.colh{{font-size:13px;font-weight:700;color:{MUTED};text-align:center;padding-bottom:2px}}
.rowh{{display:flex;align-items:center;justify-content:center}}
.rowh span{{writing-mode:vertical-rl;font-size:13px;font-weight:700;color:{MUTED};letter-spacing:.2em}}
.q{{padding:18px 20px 16px;min-height:150px}}
.q.pos{{background:var(--a50)}} .q.neg{{background:#f4f3f0}}
.qh{{display:flex;align-items:baseline;gap:10px;margin-bottom:10px}}
.qh b{{font-size:30px;font-weight:800;line-height:1}}
.q.pos .qh b{{color:var(--accent)}} .q.neg .qh b{{color:{INK2}}}
.qh span{{font-size:14px;font-weight:700;color:{INK2}}}
.q ol{{list-style:none;margin:0;padding:0}}
.q li{{font-size:15px;line-height:1.5;margin:6px 0;display:flex;gap:9px;word-break:keep-all}}
.q li .n{{flex:none;width:20px;height:20px;border-radius:50%;font-size:11.5px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;background:#fff;color:{INK2};margin-top:2px}}
.strat{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px;padding-left:54px}}
.sc{{border:1px solid {GRAY_FILL};padding:12px 14px}}
.sc.focus{{border:2px solid var(--accent);background:var(--a50)}}
.sk{{font-size:15px;font-weight:800}} .sk span{{font-size:12px;font-weight:600;color:{MUTED};margin-left:6px}}
.sv{{font-size:14px;line-height:1.5;margin-top:6px;word-break:keep-all}}
/* bar */
.br{{display:grid;grid-template-columns:200px 1fr;align-items:center;gap:16px;margin:12px 0}}
.bl{{text-align:right;font-size:15px;color:{INK2}}} .bl.b{{color:{INK};font-weight:700}}
.bt{{display:flex;align-items:center;gap:10px}}
.bb{{height:26px;border-radius:0 5px 5px 0}}
.bv{{font-size:15px;color:{INK2};white-space:nowrap}} .bv.b{{font-weight:700;color:{INK}}}
/* before → after */
.ba{{display:grid;grid-template-columns:200px 1fr 120px;gap:22px;align-items:center;padding:16px 0;border-bottom:1px solid {GRID}}}
.ba:last-child{{border-bottom:0}}
.bal{{font-size:16px;font-weight:700;text-align:right;word-break:keep-all}}
.bab{{display:grid;grid-template-columns:64px 1fr;align-items:center;gap:10px;margin:5px 0}}
.bak{{font-size:12.5px;color:{MUTED};text-align:right}}
.bat{{display:flex;align-items:center;gap:10px}}
.bafill{{height:22px;border-radius:0 5px 5px 0}} .bafill.before{{background:{GRAY_FILL}}} .bafill.after{{background:var(--accent)}}
.bav{{font-size:15px;white-space:nowrap}} .bav.before{{color:{INK2}}} .bav.after{{font-weight:700;color:{INK}}}
.badelta{{font-size:30px;font-weight:800;color:{INK2};letter-spacing:-.02em;line-height:1}} .badelta.good{{color:var(--accent-ink)}}
.badelta small{{display:block;font-size:12.5px;font-weight:600;color:{MUTED};margin-top:6px;letter-spacing:0}}
/* trend */
.badge{{position:absolute;left:70px;top:0;font-size:14px;color:{INK2};background:var(--a50);border:1px solid var(--a200);padding:6px 12px;border-radius:999px}}
.badge b{{color:{INK};font-size:16px;margin-left:4px}}
.unit{{position:absolute;right:30px;top:6px;font-size:12px;color:{MUTED}}}
/* funnel */
.fr{{display:grid;grid-template-columns:150px 1fr 90px;align-items:center;gap:16px}}
.fn{{text-align:right;font-size:15px;font-weight:600;color:{INK2}}}
.fbw{{display:flex;justify-content:center}}
.fb{{height:44px;display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:700;border-radius:6px}}
.fr.conv{{height:26px}} .fconv{{text-align:center;font-size:13px;color:{MUTED}}}
/* compare */
table.cmp{{width:100%;border-collapse:collapse;font-size:14.5px}}
table.cmp th, table.cmp td{{padding:12px 12px;border-bottom:1px solid {GRID};text-align:center;vertical-align:top;word-break:keep-all}}
table.cmp thead th{{font-size:15px;font-weight:700;border-bottom:2px solid {BASE}}}
table.cmp thead th.ours{{background:var(--accent);color:#fff;border-bottom-color:var(--accent)}}
table.cmp thead th small{{display:block;font-size:11.5px;font-weight:500;color:{MUTED}}}
table.cmp td.ours{{background:var(--a50)}}
table.cmp th.rl{{text-align:left;font-weight:600;color:{INK};width:170px}}
.mk{{display:block;margin:0 auto}} .mk.txt{{font-size:15px;font-weight:700;line-height:1.2}} .ct{{display:block;font-size:12.5px;color:{INK2};margin-top:3px;word-break:keep-all}}
.dis{{display:block;font-size:11px;font-weight:700;color:{SECOND};margin-top:3px}}
tr.vrow td{{font-size:11.5px;color:{MUTED};word-break:break-all}}
/* KPI */
.kpis{{display:grid;gap:14px}}
.tile{{border:1px solid {GRAY_FILL};padding:20px 22px;border-top:4px solid var(--accent)}}
.tl{{font-size:15px;font-weight:700;color:{INK2}}}
.tv{{font-size:38px;font-weight:800;margin:10px 0 8px;letter-spacing:-.02em;word-break:keep-all}} .tv.long{{font-size:28px;line-height:1.25}}
.tbs{{font-size:13.5px;color:{INK2};line-height:1.5;word-break:keep-all}}
/* roadmap */
.rm{{display:grid;gap:4px}}
.rh{{font-size:13px;font-weight:700;color:{MUTED};padding:6px 8px;text-align:center}}
.ra{{font-size:14px;font-weight:700;padding:12px 10px;background:#f4f3f0;display:flex;align-items:center}}
.ra.kpi{{background:var(--accent);color:#fff}}
.rc{{font-size:13.5px;line-height:1.45;padding:12px 10px;background:#fafaf8;word-break:keep-all}}
.rc.kpi{{background:var(--a50);font-weight:700}}
.rc.star{{outline:2px solid var(--accent);outline-offset:-2px;background:#fff}}
/* ps_map */
.ps{{display:grid;grid-template-columns:1fr 34px 1fr 34px 1fr;gap:10px 6px;align-items:stretch}}
.psh{{font-size:13px;font-weight:700;color:{MUTED};padding-left:4px}}
.psc{{padding:14px 16px;font-size:15px;line-height:1.45;word-break:keep-all;position:relative}}
.psc b{{font-weight:700}} .psc small{{display:block;font-size:12.5px;color:{MUTED};margin-top:6px;font-weight:500}}
.psc.prob{{background:#f4f3f0}} .psc.sol{{background:var(--a50)}} .psc.ben{{background:#fff;border:1.5px solid var(--a200)}}
.no{{display:inline-flex;width:22px;height:22px;border-radius:50%;background:{INK};color:#fff;font-size:12px;font-weight:700;align-items:center;justify-content:center;margin-right:8px;vertical-align:1px}}
.psc.sol .no{{background:var(--accent)}}
.arr{{display:flex;align-items:center;justify-content:center;color:{MUTED};font-size:20px}}
/* gantt */
.gt{{display:grid;column-gap:0}}
.gh{{font-size:13px;font-weight:700;color:{MUTED};text-align:center;padding:4px 0 8px}}
.grow{{border-top:1px solid {GRID};min-height:46px;align-items:center}}
.gn{{grid-column:1;font-size:14.5px;font-weight:600;padding:0 12px 0 0;word-break:keep-all}}
.gc{{align-self:stretch;border-left:1px solid {GRID}}}
.gb{{z-index:1;height:28px;margin:0 4px;border-radius:6px;font-size:12.5px;font-weight:600;display:flex;align-items:center;padding:0 10px;white-space:nowrap;overflow:hidden}}
.gb.done{{background:var(--accent-ink);color:#fff}} .gb.doing{{background:var(--accent);color:#fff}}
.gb.todo{{background:var(--a50);border:1.5px dashed var(--accent);color:var(--accent-ink)}}
.gb-out{{z-index:1;font-size:12.5px;font-weight:600;color:var(--accent-ink);padding:0 8px;white-space:nowrap}} .gb-out.l{{justify-self:end}}
.gm{{z-index:1;justify-self:center;font-size:12.5px;font-weight:700;display:flex;flex-direction:column;align-items:center;gap:7px;white-space:nowrap;padding:8px 0 6px}}
.gm i{{width:12px;height:12px;background:{INK};transform:rotate(45deg);display:inline-block}}
.legend .gl{{display:inline-block;width:18px;height:10px;border-radius:3px;margin-right:6px}}
.gl.done{{background:var(--accent-ink)}} .gl.doing{{background:var(--accent)}} .gl.todo{{background:var(--a50);border:1.5px dashed var(--accent)}}
/* chapter (갤러리 구분) */
h1.chapter{{font-size:20px;font-weight:800;color:{INK2};margin:18px 0 -8px;letter-spacing:-.01em}}
.slot{{width:100%;height:100%;min-height:120px;border:1.5px dashed {GRAY};background:#fafaf8;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;padding:12px;text-align:center}}
.slot span{{font-size:11.5px;font-weight:700;color:{MUTED};letter-spacing:.04em}} .slot b{{font-size:13.5px;font-weight:600;color:{INK2};word-break:keep-all;line-height:1.4}}
/* BM 산식 띠 · 수익원 */
.fx{{display:flex;align-items:center;flex-wrap:wrap;gap:10px;margin-top:14px;padding:14px 18px;background:#f6f5f2;border-radius:10px}}
.fx-lead{{font-size:13px;font-weight:700;color:{MUTED};margin-right:6px}}
.fx-term{{display:flex;flex-direction:column;align-items:center;background:#fff;border:1px solid {GRAY_FILL};border-radius:8px;padding:6px 14px;min-width:84px}}
.fx-term small{{font-size:11.5px;color:{MUTED}}} .fx-term b{{font-size:17px;font-weight:800}}
.fx-term.res{{background:var(--accent);border-color:var(--accent)}} .fx-term.res small{{color:#fff;opacity:.85}} .fx-term.res b{{color:#fff}}
.fx-op{{font-size:22px;font-weight:700;color:{INK2}}} .fx-text{{font-size:16px;font-weight:700}}
.streams{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin-top:10px}}
.strm{{border:1px solid {GRAY_FILL};border-radius:8px;padding:10px 14px;display:flex;flex-direction:column;gap:3px}}
.strm b{{font-size:14.5px}} .strm>span{{font-size:13px;color:{INK2};word-break:keep-all}} .strm .chip{{align-self:flex-start;margin:4px 0 0}}
/* flow */
.flow{{display:grid;gap:44px;position:relative}}
.fw{{position:relative;border:1.5px solid {GRAY_FILL};border-radius:12px;padding:16px 16px 14px;background:#fff;min-height:110px;display:flex;flex-direction:column;gap:6px}}
.fw:not(:last-child)::after{{content:"";position:absolute;right:-34px;top:50%;width:24px;height:2px;background:{GRAY}}}
.fw:not(:last-child)::before{{content:"";position:absolute;right:-36px;top:calc(50% - 5px);border:6px solid transparent;border-left:8px solid {GRAY};border-right:0}}
.fw.ours{{border-color:var(--accent);background:var(--a50)}}
.fw-n{{width:24px;height:24px;border-radius:50%;background:{INK};color:#fff;font-size:12px;font-weight:800;display:inline-flex;align-items:center;justify-content:center}}
.fw.ours .fw-n{{background:var(--accent)}}
.fw b{{font-size:15.5px;line-height:1.35;word-break:keep-all}} .fw small{{font-size:12.5px;color:{INK2};line-height:1.45;word-break:keep-all}}
.fw-who{{position:absolute;top:-11px;right:12px;font-size:11px;font-weight:700;background:#fff;border:1px solid {GRAY_FILL};border-radius:999px;padding:1px 8px;color:{INK2}}}
.loopbar{{height:26px;border:2px solid {GRAY};border-top:0;border-radius:0 0 10px 10px;margin-top:10px;position:relative;display:flex;justify-content:center}}
.loopbar::before{{content:"";position:absolute;left:-7px;top:-6px;border:6px solid transparent;border-bottom:9px solid {GRAY};border-top:0}}
.loopbar span{{position:absolute;bottom:-11px;background:#fff;padding:0 10px;font-size:13px;font-weight:700;color:{INK2}}}
/* screens */
.screens{{display:grid;gap:22px;justify-items:center}}
.scr{{display:flex;flex-direction:column;align-items:center;gap:12px;width:100%}}
.phone{{width:100%;max-width:180px;aspect-ratio:9/16.5;border:7px solid #232323;border-radius:28px;overflow:hidden;background:#fff;position:relative}}
.phone img{{width:100%;height:100%;object-fit:cover;display:block}}
.ui{{padding:14px 12px;display:flex;flex-direction:column;gap:8px;height:100%}}
.ui-top{{font-size:13px;font-weight:800;padding:4px 2px 8px;border-bottom:1px solid {GRID}}}
.ui-row{{font-size:12px;padding:10px 10px;border-radius:8px;background:#f4f3f0;color:{INK2}}}
.ui-row.on{{background:var(--a100);color:{INK};font-weight:700;outline:1.5px solid var(--accent)}}
.ui-btn{{margin-top:auto;font-size:12px;font-weight:700;text-align:center;padding:10px;border-radius:8px;background:var(--accent);color:#fff}}
.scr-cap{{text-align:center;display:flex;flex-direction:column;align-items:center;gap:4px;max-width:240px}}
.scr-cap b{{font-size:15px}} .scr-cap small{{font-size:12.5px;color:{INK2};line-height:1.45;word-break:keep-all}}
.scr-cap .no{{background:var(--accent);margin:0}}
/* photos */
.photos{{display:grid;gap:12px}}
.pho{{margin:0;position:relative}} .ph-frame{{aspect-ratio:4/3;overflow:hidden;background:#f4f3f0}}
.ph-frame img{{width:100%;height:100%;object-fit:cover;display:block}}
.pho figcaption{{background:#f4f3f0;padding:8px 10px;display:flex;flex-direction:column;gap:2px}}
.pho figcaption b{{font-size:13.5px;word-break:keep-all}} .pho figcaption small{{font-size:11.5px;color:{MUTED}}}
.ph-badge{{position:absolute;top:8px;left:8px;z-index:1;font-size:11px;font-weight:700;background:{INK};color:#fff;border-radius:999px;padding:2px 9px}}
/* persona */
.personas{{display:grid;gap:14px}}
.persona{{display:grid;grid-template-columns:1fr 1.25fr;border:1.5px solid {GRAY_FILL};border-radius:14px;overflow:hidden}}
.pl{{padding:20px 22px;background:var(--a50);display:flex;flex-direction:column;gap:10px}}
.pname{{font-size:20px;font-weight:800}} .psize{{font-size:13px;font-weight:700;color:var(--accent-ink)}}
.pdef{{font-size:14.5px;line-height:1.5;word-break:keep-all}}
.ptags{{display:flex;flex-wrap:wrap;gap:6px}} .pt{{font-size:12px;font-weight:600;background:#fff;border:1px solid var(--a200);color:var(--accent-ink);border-radius:999px;padding:2px 9px}}
.pscene{{font-size:13.5px;color:{INK2};line-height:1.55;word-break:keep-all}}
.pv{{margin-top:auto;font-size:12.5px;color:{INK2}}} .pv b{{font-size:15px;color:{INK}}} .pv.off{{color:{MUTED}}}
.pr{{padding:18px 22px;display:flex;flex-direction:column;gap:10px}}
.pr-h{{font-size:12.5px;font-weight:700;color:{MUTED}}}
.pp{{display:grid;grid-template-columns:64px 1fr;gap:10px;align-items:start}}
.pk{{font-size:11.5px;font-weight:700;color:{INK2};background:#f4f3f0;border-radius:6px;text-align:center;padding:4px 0}}
.pp p{{margin:0;font-size:14.5px;line-height:1.5;word-break:keep-all}}
/* quotes */
.quotes{{display:grid;gap:14px}}
.qt{{margin:0;border-left:4px solid {GRAY_FILL};background:#fafaf8;padding:14px 16px 12px;display:flex;flex-direction:column;gap:10px}}
.qt p{{margin:0;font-size:15px;line-height:1.55;word-break:keep-all}} .qt p::before{{content:"“";font-weight:800;color:var(--accent);margin-right:2px}}
.qt p::after{{content:"”";font-weight:800;color:var(--accent);margin-left:2px}}
.qt.pend{{border-left-style:dashed;background:#fff}} .qt.pend p{{color:{MUTED}}} .qt.pend p::before,.qt.pend p::after{{content:none}}
.qt footer{{display:flex;flex-direction:column;gap:2px}} .qt footer b{{font-size:12.5px}} .qt footer span{{font-size:11.5px;color:{MUTED}}}
/* survey */
.sq{{font-size:15px;font-weight:700;margin-bottom:6px}} .sq span{{font-weight:500;color:{MUTED}}}
/* donut */
.donut{{display:flex;align-items:center;gap:40px;justify-content:center}}
.dleg{{display:flex;flex-direction:column;gap:10px;min-width:320px}}
.dl{{display:grid;grid-template-columns:14px 1fr auto auto;gap:10px;align-items:center;font-size:14.5px;color:{INK2}}}
.dl i{{width:14px;height:14px;border-radius:3px}} .dl b{{font-size:16px;color:{INK}}} .dl small{{font-size:12px;color:{MUTED};min-width:70px;text-align:right}}
.dl.b span{{color:{INK};font-weight:700}}
/* segments */
.seg{{display:grid;grid-template-columns:200px 1.3fr 80px 1.4fr;gap:16px;align-items:center;padding:12px 10px;border-bottom:1px solid {GRID}}}
.seg-h{{font-size:12.5px;font-weight:700;color:{MUTED};border-bottom:2px solid {BASE};padding-top:0}}
.seg b{{font-size:15px}} .seg b em{{font-style:normal;font-size:11px;font-weight:700;background:var(--accent);color:#fff;border-radius:999px;padding:1px 8px;margin-left:6px;vertical-align:2px}}
.seg.on{{background:var(--a50)}}
.segsz{{display:flex;align-items:center;gap:10px}} .segbar{{flex:1;height:14px;background:#f4f3f0;border-radius:0 4px 4px 0}}
.segbar i{{display:block;height:100%;border-radius:0 4px 4px 0}} .segsz span{{font-size:13.5px;min-width:76px;color:{INK2}}}
.gr{{font-size:15px;font-weight:800;color:{INK2}}} .gr.up{{color:var(--accent-ink)}} .gr.down{{color:{MUTED}}}
.seg small{{font-size:13px;color:{INK2};word-break:keep-all}}
/* revenue mix · budget · sum */
.rvs{{display:flex;flex-direction:column}}
.rv{{display:grid;grid-template-columns:170px 1.2fr 1.4fr 110px;gap:14px;align-items:center;padding:11px 4px;border-bottom:1px solid {GRID}}}
.rv b{{font-size:15px}} .rv small{{font-size:13px;color:{INK2}}} .rv>span{{font-size:15px;font-weight:700;text-align:right}}
.rvbar{{height:16px;background:#f4f3f0;border-radius:0 4px 4px 0}} .rvbar i{{display:block;height:100%;background:var(--accent);border-radius:0 4px 4px 0}}
.rvbar i.none{{width:100%;background:repeating-linear-gradient(90deg,{GRAY_FILL} 0 6px,transparent 6px 11px);height:2px;margin-top:7px}}
.sumline{{margin-top:10px;text-align:right;font-size:14px;color:{INK2}}} .sumline b{{color:{INK};font-size:16px}}
.sumline.bad{{color:{SECOND};font-weight:700}} .sumline.bad b{{color:{SECOND}}}
.bgbar{{display:flex;height:40px;border-radius:8px;overflow:hidden;gap:2px;margin-bottom:14px}}
.bgs{{display:flex;align-items:center;justify-content:center;font-size:12.5px;font-weight:700;white-space:nowrap;overflow:hidden;padding:0 6px}}
table.tb{{width:100%;border-collapse:collapse;font-size:14px}}
table.tb th{{font-size:12.5px;font-weight:700;color:{MUTED};text-align:left;border-bottom:2px solid {BASE};padding:8px 10px}}
table.tb td{{padding:10px 10px;border-bottom:1px solid {GRID};vertical-align:top;word-break:keep-all}}
table.tb .num{{text-align:right;font-variant-numeric:tabular-nums}}
table.tb .sw{{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:8px;vertical-align:-1px}}
table.tb tr.tot td{{font-weight:800;border-top:2px solid {BASE};background:#fafaf8}}
table.tb th.hc{{color:var(--accent-ink)}} table.tb td.hc{{background:var(--a50);font-weight:700}}
table.tb tr.hr td{{background:var(--a50)}}
table.tb.plan{{margin-top:14px}}
/* stairs */
.stairs{{display:grid;gap:10px;align-items:end;height:330px}}
.stp{{display:flex;flex-direction:column;justify-content:flex-end}}
.stp-in{{height:100%;border-radius:12px 12px 0 0;padding:16px 16px 14px;display:flex;flex-direction:column;gap:6px}}
.stp-in.last{{color:#fff}} .stp-in.last .sp{{background:rgba(255,255,255,.2);color:#fff}}
.sp{{align-self:flex-start;font-size:12px;font-weight:700;background:#fff;border-radius:999px;padding:2px 10px;color:{INK2}}}
.stp-in b{{font-size:16px;word-break:keep-all}} .stp-in ul{{margin:0;padding-left:16px;font-size:13px;line-height:1.5}}
.sk-kpi{{margin-top:auto;font-size:13px;font-weight:800;border-top:1px solid rgba(0,0,0,.12);padding-top:8px}}
.stp-in.last .sk-kpi{{border-color:rgba(255,255,255,.35)}}
/* team */
.team{{display:grid;gap:12px}}
.tm{{border:1.5px solid {GRAY_FILL};border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:6px}}
.tm-top{{display:flex;justify-content:space-between;align-items:center}}
.tm-role{{font-size:12.5px;font-weight:700;color:var(--accent-ink)}}
.tm-st{{font-size:11px;font-weight:700;border-radius:999px;padding:2px 9px}}
.tm.ok .tm-st{{background:var(--accent-ink);color:#fff}} .tm.todo{{border-style:dashed}} .tm.todo .tm-st{{border:1.5px dashed {GRAY};color:{INK2}}}
.tm.talk .tm-st{{border:1.5px solid {GRAY};color:{INK2}}}
.tm b{{font-size:17px}} .tm-duty{{font-size:13.5px;font-weight:600;word-break:keep-all}} .tm small{{font-size:12.5px;color:{INK2};line-height:1.45;word-break:keep-all}}
/* partners */
.pt-row{{display:grid;grid-template-columns:180px 1.6fr 1fr 170px;gap:14px;align-items:center;padding:12px 6px;border-bottom:1px solid {GRID}}}
.pt-h{{font-size:12.5px;font-weight:700;color:{MUTED};border-bottom:2px solid {BASE}}}
.pt-row>b{{font-size:15px}} .pt-row div span{{display:block;font-size:14px}} .pt-row div small{{display:block;font-size:12.5px;color:{INK2};margin-top:2px}}
.pt-row>span{{font-size:13.5px;color:{INK2}}}
.ladder{{display:flex;align-items:center;gap:10px}} .dots{{display:flex;align-items:center}}
.dots i{{width:12px;height:12px;border-radius:50%;border:2px solid {GRAY_FILL};background:#fff;position:relative}}
.dots i+i{{margin-left:10px}} .dots i+i::before{{content:"";position:absolute;left:-12px;top:3px;width:10px;height:2px;background:{GRAY_FILL}}}
.dots i.on{{background:var(--accent);border-color:var(--accent)}} .dots i.cur{{box-shadow:0 0 0 3px var(--a200)}}
.ladder em{{font-style:normal;font-size:13px;font-weight:700}}
/* timeline */
.tline{{display:grid;position:relative;padding-top:8px}}
.tl-line{{position:absolute;left:0;top:15px;height:0;border-top:2px dashed {GRAY_FILL}}}
.tl-prog{{position:absolute;left:0;top:15px;height:2px;background:var(--accent-ink)}}
.tle{{position:relative;display:flex;flex-direction:column;gap:4px;padding:0 10px 0 0}}
.tle i{{width:16px;height:16px;border-radius:50%;position:relative;z-index:1;margin-bottom:8px;border:3px solid #fff}}
.tle.done i{{background:var(--accent-ink)}} .tle.doing i{{background:var(--accent);box-shadow:0 0 0 3px var(--a200)}}
.tle.todo i{{background:#fff;border:2px dashed {GRAY}}}
.tl-d{{font-size:12.5px;font-weight:700;color:{MUTED}}} .tle b{{font-size:15px;word-break:keep-all}}
.tle small{{font-size:12.5px;color:{INK2};line-height:1.45;word-break:keep-all}} .tle em{{font-style:normal;font-size:11px;font-weight:700;color:{MUTED}}}
.tle.todo b{{color:{INK2}}}
/* BMC */
.bmc{{display:grid;grid-template-columns:repeat(10,1fr);grid-template-rows:auto auto auto;gap:4px}}
.bmc>div{{background:#f6f5f2;padding:12px 12px;min-height:110px}}
.bmc h4{{margin:0 0 6px;font-size:12.5px;font-weight:800;color:{INK2}}}
.bmc ul{{margin:0;padding-left:15px;font-size:13px;line-height:1.5;word-break:keep-all}}
.bmc .on{{background:var(--accent);color:#fff}} .bmc .on h4{{color:#fff}}
.bmc-kp{{grid-column:1/3;grid-row:1/3}} .bmc-ka{{grid-column:3/5;grid-row:1}} .bmc-kr{{grid-column:3/5;grid-row:2}}
.bmc-vp{{grid-column:5/7;grid-row:1/3}} .bmc-cr{{grid-column:7/9;grid-row:1}} .bmc-ch{{grid-column:7/9;grid-row:2}}
.bmc-cs{{grid-column:9/11;grid-row:1/3}} .bmc-cost{{grid-column:1/6;grid-row:3}} .bmc-rev{{grid-column:6/11;grid-row:3}}
{extra}
"""


def section(v, A):
    kind = v.get("type")
    if kind not in RENDER:
        raise SystemExit(f"[오류] {v.get('id')}: 모르는 type '{kind}' — {', '.join(RENDER)}")
    if not v.get("headline"):
        raise SystemExit(f"[오류] {v.get('id')}: headline(결론 문장)이 없다 — 이 시각자료가 말하는 것을 한 문장으로 쓴다")
    half = " half" if v.get("size") == "half" else ""     # 개요 양식 표의 이미지 칸(약 70mm)에 넣을 반폭 그림
    parts = [f'<section class="viz{half}" id="{html.escape(v["id"])}">']
    if v.get("kicker"):
        parts.append(f'<div class="kicker">{esc(v["kicker"])}</div>')
    parts.append(f'<h2 class="headline">{esc(v["headline"])}</h2>')
    if v.get("sub"):
        parts.append(f'<p class="sub">{esc(v["sub"])}</p>')
    body = RENDER[kind](v, A)
    if TXT != 1.0 or MIN_FS:      # SVG 글자만 키운다(HTML 글자는 CSS가 맡는다)
        body = re.sub(r'font-size="([\d.]+)"', lambda m: f'font-size="{fsz(float(m.group(1))):.1f}"', body)
    parts.append(f'<div class="body"><div class="fit">{body}</div></div>')
    if v.get("takeaway"):
        parts.append(f'<div class="takeaway">{esc(v["takeaway"])}</div>')
    if v.get("note"):
        parts.append(f'<div class="note">{esc(v["note"])}</div>')
    parts.append("</section>")
    return "".join(parts)


FIT_JS = """<script>
// 발표 장: 본문이 남은 높이보다 크면 비율을 유지한 채 줄이고, 작으면 가운데에 둔다
window.__fit = function () {
  document.querySelectorAll('section.viz .body').forEach(function (b) {
    var f = b.firstElementChild; f.style.transform = '';
    var h = f.scrollHeight, H = b.clientHeight, s = Math.min(1, H / h);
    f.style.transform = 'translateY(' + Math.max(0, (H - h * s) / 2) + 'px) scale(' + s.toFixed(3) + ')';
  });
};
document.fonts.ready.then(window.__fit);
</script>"""


def build(spec, accent, slide=False, print_=False):
    global TXT, BODY_W, MIN_FS
    TXT = 1.3 if print_ else 1.0
    MIN_FS = 13 if print_ else 0
    # HTML 유형이 실제로 쓰는 본문 폭(확대 전 px) — 간트 라벨이 막대에 들어가는지 가늠할 때 쓴다
    BODY_W = (1600 - 144) / 1.2 if slide else (860 - 56) / 1.15 if print_ else 1120 - 96
    A = "#" + accent.lstrip("#")
    secs = "".join(f'<h1 class="chapter">{esc(v.get("title", ""))}</h1>' if v.get("type") == "chapter" else section(v, A)
                   for v in spec["visuals"])
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{esc(spec.get("title", "시각자료"))}</title>'
            f'<style>{css(A, slide, print_)}</style></head><body><div class="page">{secs}</div>{FIT_JS if slide else ""}</body></html>')


def warn(spec):
    out = []
    for v in spec["visuals"]:
        if v.get("type") == "chapter":
            continue
        if not v.get("note"):
            out.append(f"{v['id']}: note(출처 · 시점 · 표본)가 없다")
        if v.get("type") in ("bar", "positioning", "compare") and not any(
                x.get("ours") for x in v.get("items", v.get("points", v.get("entities", [])))):
            out.append(f"{v['id']}: 우리(ours) 표시가 없다 — 무엇을 강조하는지 정한다")
        if v.get("type") == "compare" and not any(r.get("disadvantage") for r in v.get("rows", [])):
            out.append(f"{v['id']}: 우리가 불리한 축이 없다 — 1개 이상 넣으면 신뢰가 오른다")
        if v.get("type") == "trend" and calc_cagr(v) is not None:
            calc = calc_cagr(v)
            said = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", f"{v.get('headline', '')} {v.get('cagr', '')}")]
            off = [x for x in said if abs(x - calc) > 0.15]
            if off:
                out.append(f"{v['id']}: 적힌 성장률 {', '.join(f'{x:g}%' for x in off)} ≠ 값으로 계산한 {calc:.1f}% — 기간·값을 맞춘다")
        num = lambda x: isinstance(x, (int, float))
        if v.get("type") == "revenue_mix" and v.get("target") is not None and all(num(c.get("amount")) for c in v["channels"]):
            tot = sum(c["amount"] for c in v["channels"])
            if abs(tot - v["target"]) > max(abs(v["target"]) * 0.005, 0.5):
                out.append(f"{v['id']}: 채널 합 {fmt(tot)} ≠ 목표 {fmt(v['target'])} — 채널 금액이나 목표를 맞춘다")
        if v.get("type") == "budget" and v.get("cap") is not None and all(num(i.get("amount")) for i in v["items"]):
            tot = sum(i["amount"] for i in v["items"])
            if abs(tot - v["cap"]) > 0.5:
                out.append(f"{v['id']}: 비목 합 {fmt(tot)} ≠ 상한 {fmt(v['cap'])}")
        if v.get("type") == "survey" and v.get("unit", "%") == "%" and not v.get("multi"):
            tot = sum(o["value"] for o in v["options"])
            if abs(tot - 100) > 1:
                out.append(f"{v['id']}: 단일 선택 응답 합이 {tot:g}% — 복수 선택이면 multi: true로 표시한다")
        if v.get("type") == "table" and v.get("total"):
            rows = v["rows"]
            for k in range(1, len(v["columns"])):
                col = [r[k] for r in rows[:-1] if k < len(r)]
                if col and all(num(x) for x in col) and num(rows[-1][k]) and abs(sum(col) - rows[-1][k]) > 0.5:
                    out.append(f"{v['id']}: '{v['columns'][k]}' 열 합 {fmt(sum(col))} ≠ 합계 행 {fmt(rows[-1][k])}")
        if v.get("type") in ("screens", "photos"):
            missing = [x.get("src") for x in v.get("screens", v.get("items", [])) if x.get("src") and not img_src(x.get("src"))]
            if missing:
                out.append(f"{v['id']}: 이미지 파일을 찾지 못했다 — {', '.join(missing)}")
        if v.get("type") == "bm":
            priced = [f.get("label", "") for f in v.get("flows", [])
                      if re.search(r"(\d[\d,.]*|○+)\s*(만|억|천|백)?\s*(원|달러|%)", f.get("label", "") + " " + f.get("detail", ""))]
            if priced:
                out.append(f"{v['id']}: BM 화살표는 금액보다 주고받는 것(사용료·서비스 등)을 쓴다 — "
                           f"{', '.join(priced)} → 금액은 매출 산식·채널별 매출(revenue_mix)로")
            unnamed = [f for f in v.get("flows", []) if not f.get("label")]
            if unnamed:
                out.append(f"{v['id']}: 이름 없는 화살표 {len(unnamed)}개 — 무엇이 오가는지 적는다")
            pairs = {}
            for f in v.get("flows", []):
                key = tuple(sorted((str(f.get("from")), str(f.get("to")))))
                pairs[key] = pairs.get(key, 0) + 1
            crowded = [f"{a}↔{b} {n}개" for (a, b), n in pairs.items() if n > 2]
            if crowded:
                out.append(f"{v['id']}: 같은 두 주체 사이 화살표가 3개 이상({', '.join(crowded)}) — 칩이 겹친다. "
                           "하나로 묶거나 수익원 카드(streams)로 옮긴다")
            long_ = [f.get("detail") for f in v.get("flows", []) if len(f.get("detail", "")) > 12]
            if long_:
                out.append(f"{v['id']}: detail이 길다({', '.join(long_)}) — 12자 안으로(칩이 상자를 덮는다)")
        if v.get("type") == "flow" and any(re.match(r"\s*([①-⑳]|\d+[.)])", s_.get("title", "")) for s_ in v.get("steps", [])):
            out.append(f"{v['id']}: flow는 단계 번호를 자동으로 붙인다 — 제목 앞 번호(①·1.)를 뺀다")
        if v.get("type") == "positioning" and LABEL_WARN.get(v.get("id")):
            out.append(f"{v['id']}: 라벨이 다른 점에 더 가깝게 놓였다({', '.join(LABEL_WARN[v['id']])}) — "
                       "좌표를 조금 옮기거나 이름을 줄인다")
        if v.get("type") == "pnl":
            prof = v.get("profit")
            if prof and any(abs((r - c) - p) > 0.5 for r, c, p in zip(v["revenue"], v["cost"], prof)):
                out.append(f"{v['id']}: 영업이익 ≠ 매출 − 비용 — 숫자 등록부와 맞춘다")
    return out


def tall(spec, out_dir):
    """문서용(--print) 그림이 쪽에서 줄어들 만큼 높은지 본다 — 본문 폭 170mm에서 120mm, 반폭(개요 칸 70mm)에서 62mm."""
    try:
        from PIL import Image
    except ImportError:
        return []
    out = []
    for v in spec.get("visuals", []):
        path = os.path.join(out_dir, f"{v.get('id')}.png")
        if v.get("type") == "chapter" or not os.path.exists(path):
            continue
        with Image.open(path) as im:
            w, h = im.size
        width, limit = (70, 62) if v.get("size") == "half" else (170, 120)
        if h / w * width > limit:
            out.append(f"{v['id']}: 문서에서 높이 {h / w * width:.0f}mm({width}mm 폭) — {limit}mm를 넘어 변환기가 줄이고 "
                       f"글자도 작아진다. 항목·행을 줄이거나 그림을 둘로 나눈다")
    return out


def shoot(html_path, out_dir):
    node = shutil.which("node")
    if not node:
        return None, "Node가 없다 — visuals.html을 브라우저로 열어 캡처한다"
    r = subprocess.run([node, os.path.join(HERE, "html_shot.cjs"), html_path, out_dir, "2"],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        return None, (r.stderr.strip() or "html_shot.cjs 실패") + " — Playwright(Node) 설치 여부 확인"
    lines = r.stdout.split("\n")
    SHOT_WARN[:] = [l.split(" ", 1)[1] for l in lines if l.startswith("OVERFLOW ")]
    return [l for l in lines if l.endswith(".png")], None


SHOT_WARN = []      # html_shot.cjs가 찍으며 잰 가로 넘침(그림 id)
LABEL_WARN = {}     # 포지셔닝 그림 id → 다른 점에 더 가깝게 놓인 라벨


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--out", default="시각자료")
    ap.add_argument("--accent", help="강조색 hex(기본 #2a78d6)")
    ap.add_argument("--theme", help="bizplan-slides 테마 JSON — colors.primary를 강조색으로")
    ap.add_argument("--slide", action="store_true", help="16:9(1600×900) 장 크기로")
    ap.add_argument("--print", dest="print_", action="store_true",
                    help="사업계획서(A4)에 넣을 크기 — 폭 860px, 글자를 키워 본문 폭 170mm에서 가장 작은 글자 7.4pt 이상")
    ap.add_argument("--no-png", action="store_true")
    ap.add_argument("--sample", metavar="경로", help="예시 spec을 이 경로에 쓰고 끝낸다")
    a = ap.parse_args()
    if a.sample:
        shutil.copyfile(SAMPLE, a.sample)
        print(f"예시 spec: {a.sample}")
        return
    if not a.spec:
        ap.error("spec(JSON) 경로가 필요하다")
    if a.slide and a.print_:
        ap.error("--slide와 --print는 함께 쓸 수 없다")
    spec = json.load(open(a.spec, encoding="utf-8"))
    global BASE_DIR
    BASE_DIR = os.path.dirname(os.path.abspath(a.spec))
    accent = a.accent or "2a78d6"
    if a.theme:
        accent = json.load(open(a.theme, encoding="utf-8"))["colors"].get("primary", accent)
    os.makedirs(a.out, exist_ok=True)
    page = os.path.join(a.out, "visuals.html")
    with open(page, "w", encoding="utf-8") as f:
        f.write(build(spec, accent, a.slide, a.print_))
    print(f"HTML: {page} ({sum(1 for v in spec['visuals'] if v.get('type') != 'chapter')}개)")
    for w in warn(spec):
        print(f"[확인] {w}")
    if not a.no_png:
        files, err = shoot(page, a.out)
        if err:
            print(f"[PNG 건너뜀] {err}")
        else:
            print(f"PNG {len(files)}개: {', '.join(os.path.basename(f) for f in files)}")
            for vid in SHOT_WARN:
                print(f"[확인] {vid}: 내용이 그림 폭 밖으로 넘친다(잘림) — 단계·칸 수나 글을 줄인다")
            if a.print_:
                for w in tall(spec, a.out):
                    print(f"[확인] {w}")


SAMPLE = os.path.join(HERE, "..", "assets", "html-visuals-sample.json")   # 기본 목차 순서의 예시 spec

if __name__ == "__main__":
    main()
