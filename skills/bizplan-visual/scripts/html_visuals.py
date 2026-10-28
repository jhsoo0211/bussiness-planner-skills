#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사업계획서·발표용 시각자료를 HTML(인라인 SVG)로 만들고 PNG로 찍는다.

    python3 -B html_visuals.py 시각자료.json --out 시각자료/ [--theme 테마.json | --accent 0066FF] [--slide] [--no-png]

입력(JSON): {"visuals": [{"id": "tam", "type": "tam", "headline": "결론 문장", ...}, ...]}
- 모든 시각자료에 공통: id · type · headline(필수 — 무엇을 보여주는지가 아니라 무엇을 말하는지)
  · kicker(어느 절의 그림인지, 예: "1-3 · 목표 고객") · sub(읽는 법 한 줄) · takeaway(그래서 무엇인가 한 줄) · note(출처 · 시점 · 표본)
- type: tam · positioning · swot · bar · before_after · trend · funnel · pnl · compare · bm · kpi · roadmap · gantt · ps_map
  (필드는 아래 각 함수 설명과 SAMPLE 참고. `python3 -B html_visuals.py --sample 예시.json`으로 예시 spec을 만든다)
출력: <out>/visuals.html(모두 한 장에) + <out>/<id>.png(2배 해상도, Node + Playwright가 있을 때).
'○○'(미확보 값)은 점선 밑줄로 표시돼 빈칸이 보인다. 강조는 우리(ours) 하나에만 쓰고 나머지는 회색으로 둔다.
"""
import argparse
import html
import json
import math
import re
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "Pretendard, 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', system-ui, sans-serif"
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
GRAY, GRAY_FILL, SECOND = "#a3a19a", "#d9d7d0", "#eb6834"
HALO = 'paint-order="stroke" stroke="#fff" stroke-width="5" stroke-linejoin="round"'   # 선 위 글자를 읽히게


# ---------------------------------------------------------------- 공통

def esc(text):
    """HTML 이스케이프 + '○○'를 미확보 표시로."""
    s = html.escape(str(text if text is not None else ""))
    return s.replace("○○", '<span class="ph">○○</span>')


def tw(text, size):
    """글자 폭 근사(px) — 한글 1em, 영문·숫자 0.56em, 공백 0.3em."""
    w = 0.0
    for ch in str(text):
        w += 0.3 if ch.isspace() else 1.0 if ord(ch) > 0x2E7F else 0.56
    return w * size


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
        w, h = size_of(text, fs), fs * 1.3
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
        s.append(f'<text x="{bx[0]:.1f}" y="{bx[1] + fs:.1f}" font-size="{fs}" font-weight="{weight}" fill="{color}" '
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


def v_bm(v, A):
    """actors: [{name, role, ours}] 왼쪽→오른쪽 3개, flows: [{from, to, kind:'money'|'value', label}], partner: {name, role}."""
    acts = v["actors"][:3]
    cy, bw, bh = 66, 230, 104
    W, H = 1024, cy + bh / 2 + (156 if v.get("partner") else 40)
    cxs = {1: [512], 2: [300, 724], 3: [160, 512, 864]}[len(acts)]
    mk = lambda mid, color: (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="11" markerHeight="11" '
                             f'markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9 z" fill="{color}"/></marker>')
    s = [f'<defs>{mk("am", darker(A, 0.8))}{mk("av", MUTED)}</defs>']
    for x, a in zip(cxs, acts):
        ours = a.get("ours")
        s.append(f'<rect x="{x - bw / 2}" y="{cy - bh / 2}" width="{bw}" height="{bh}" rx="14" '
                 f'fill="{A if ours else "#fff"}" stroke="{A if ours else GRAY_FILL}" stroke-width="{0 if ours else 1.5}"/>')
        s.append(f'<text x="{x}" y="{cy - 4}" text-anchor="middle" font-size="19" font-weight="700" '
                 f'fill="{"#fff" if ours else INK}">{html.escape(a["name"])}</text>')
        s.append(f'<text x="{x}" y="{cy + 22}" text-anchor="middle" font-size="13" '
                 f'fill="{"#fff" if ours else MUTED}" fill-opacity="{0.9 if ours else 1}">{html.escape(a.get("role", ""))}</text>')
    pair_count = {}
    for f in v.get("flows", []):
        i, j = f["from"], f["to"]
        if max(i, j) >= len(acts):
            continue
        key = tuple(sorted((i, j)))
        k = pair_count.get(key, 0)
        pair_count[key] = k + 1
        off = [-30, 30, -10, 10][k % 4]
        y = cy + off
        x1 = cxs[i] + (bw / 2 + 6) * (1 if j > i else -1)
        x2 = cxs[j] - (bw / 2 + 10) * (1 if j > i else -1)
        money = f.get("kind") == "money"
        color = darker(A, 0.8) if money else MUTED
        dash = "" if money else ' stroke-dasharray="6 5"'
        s.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="{2.5 if money else 1.8}"{dash} '
                 f'marker-end="url(#{"am" if money else "av"})"/>')
        lx, label = (x1 + x2) / 2, f.get("label", "")
        lw = tw(label, 13) + 16
        ly = y - 22 if off < 0 else y + 8
        s.append(f'<rect x="{lx - lw / 2}" y="{ly}" width="{lw}" height="20" rx="10" '
                 f'fill="{mix(A, 0.12) if money else "#fff"}" stroke="{mix(A, 0.35) if money else GRAY_FILL}"/>')
        s.append(f'<text x="{lx}" y="{ly + 14.5}" text-anchor="middle" font-size="13" font-weight="{700 if money else 500}" '
                 f'fill="{INK if money else INK2}">{html.escape(label)}</text>')
    p = v.get("partner")
    if p and len(acts) >= 2:
        px, py = cxs[len(cxs) // 2], cy + bh / 2 + 116
        s.append(f'<rect x="{px - 110}" y="{py - 30}" width="220" height="60" rx="12" fill="#fff" stroke="{GRAY_FILL}" stroke-width="1.5"/>')
        s.append(f'<text x="{px}" y="{py - 4}" text-anchor="middle" font-size="16" font-weight="700" fill="{INK}">{html.escape(p["name"])}</text>')
        s.append(f'<text x="{px}" y="{py + 16}" text-anchor="middle" font-size="12" fill="{MUTED}">{html.escape(p.get("role", ""))}</text>')
        s.append(f'<line x1="{px}" y1="{cy + bh / 2 + 4}" x2="{px}" y2="{py - 34}" stroke="{MUTED}" stroke-width="1.8" '
                 f'stroke-dasharray="6 5" marker-end="url(#av)"/>')
        if p.get("label"):
            s.append(f'<text x="{px + 12}" y="{(cy + bh / 2 + py - 30) / 2 + 4}" font-size="13" fill="{INK2}">{html.escape(p["label"])}</text>')
    legend = ('<div class="legend"><span><i class="ln" style="background:var(--accent-ink)"></i>돈의 흐름(금액)</span>'
              f'<span><i class="ln dash"></i>가치의 흐름</span></div>')
    return f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{"".join(s)}</svg>{legend}'


def v_kpi(v, A):
    """tiles: [{label, value, basis, status}] — 매출 · 투자 · 고용처럼 3개."""
    tiles = "".join(
        f'<div class="tile"><div class="tl">{esc(t["label"])}{chip(t["status"], "st") if t.get("status") else ""}</div>'
        f'<div class="tv">{esc(t["value"])}</div><div class="tb">{esc(t.get("basis", ""))}</div></div>'
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
    for t in v["tasks"]:
        st = cls.get(t.get("status", "예정"), "todo")
        start = max(1, min(int(t["start"]), n))
        span = max(1, min(int(t.get("length", 1)), n - start + 1))
        cells = "".join(f'<div class="gc" style="grid-column:{i + 2};grid-row:1"></div>' for i in range(n))
        label = esc(t.get("out", "")) or esc(t.get("status", ""))
        out.append(f'<div class="gt grow" style="grid-template-columns:{cols}">'
                   f'<div class="gn" style="grid-row:1">{esc(t["name"])}</div>{cells}'
                   f'<div class="gb {st}" style="grid-column:{start + 1} / span {span};grid-row:1">{label}</div></div>')
    if v.get("milestones"):
        cells = "".join(f'<div class="gc" style="grid-column:{i + 2};grid-row:1"></div>' for i in range(n))
        marks = "".join(f'<div class="gm" style="grid-column:{max(1, min(int(m["at"]), n)) + 1};grid-row:1">'
                        f'<i></i>{esc(m["label"])}</div>' for m in v["milestones"])
        out.append(f'<div class="gt grow ms" style="grid-template-columns:{cols}"><div class="gn" style="grid-row:1">'
                   f'마일스톤</div>{cells}{marks}</div>')
    legend = ('<div class="legend small"><span><i class="gl done"></i>완료</span><span><i class="gl doing"></i>진행</span>'
              '<span><i class="gl todo"></i>예정</span></div>')
    return "".join(out) + legend


RENDER = {"tam": v_tam, "positioning": v_positioning, "swot": v_swot, "bar": v_bar, "before_after": v_before_after,
          "trend": v_trend, "funnel": v_funnel, "pnl": v_pnl, "compare": v_compare, "bm": v_bm, "kpi": v_kpi,
          "roadmap": v_roadmap, "ps_map": v_ps_map, "gantt": v_gantt}


# ---------------------------------------------------------------- 페이지

def css(A, slide):
    w = "1600px" if slide else "1120px"
    # 발표 장(16:9): 본문이 남는 높이를 채우고, SVG는 폭에 맞춰 키우되 높이를 넘지 않게
    extra = ("section.viz{height:900px;display:flex;flex-direction:column;padding:56px 72px 36px}"
             "section.viz .body{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center}"
             "section.viz .body>svg,section.viz .body>.rel>svg{width:100%;height:auto;max-height:540px}"
             ".tam,.swot,.strat,.bars,.bas,.funnel,.kpis,.rm,.ps,.gt,table.cmp{zoom:1.25}"
             "h2.headline{font-size:38px}.sub{font-size:18px}.takeaway{font-size:20px}.note{font-size:14px}") if slide else ""
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
table.cmp th, table.cmp td{{padding:12px 12px;border-bottom:1px solid {GRID};text-align:center;vertical-align:top}}
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
.tv{{font-size:38px;font-weight:800;margin:10px 0 8px;letter-spacing:-.02em}}
.tb{{font-size:13.5px;color:{INK2};line-height:1.5;word-break:keep-all}}
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
.gm{{z-index:1;justify-self:center;font-size:12.5px;font-weight:700;display:flex;align-items:center;gap:6px;white-space:nowrap}}
.gm i{{width:12px;height:12px;background:{INK};transform:rotate(45deg);display:inline-block}}
.legend .gl{{display:inline-block;width:18px;height:10px;border-radius:3px;margin-right:6px}}
.gl.done{{background:var(--accent-ink)}} .gl.doing{{background:var(--accent)}} .gl.todo{{background:var(--a50);border:1.5px dashed var(--accent)}}
{extra}
"""


def section(v, A):
    kind = v.get("type")
    if kind not in RENDER:
        raise SystemExit(f"[오류] {v.get('id')}: 모르는 type '{kind}' — {', '.join(RENDER)}")
    if not v.get("headline"):
        raise SystemExit(f"[오류] {v.get('id')}: headline(결론 문장)이 없다 — 이 시각자료가 말하는 것을 한 문장으로 쓴다")
    parts = [f'<section class="viz" id="{html.escape(v["id"])}">']
    if v.get("kicker"):
        parts.append(f'<div class="kicker">{esc(v["kicker"])}</div>')
    parts.append(f'<h2 class="headline">{esc(v["headline"])}</h2>')
    if v.get("sub"):
        parts.append(f'<p class="sub">{esc(v["sub"])}</p>')
    parts.append(f'<div class="body">{RENDER[kind](v, A)}</div>')
    if v.get("takeaway"):
        parts.append(f'<div class="takeaway">{esc(v["takeaway"])}</div>')
    if v.get("note"):
        parts.append(f'<div class="note">{esc(v["note"])}</div>')
    parts.append("</section>")
    return "".join(parts)


def build(spec, accent, slide=False):
    A = "#" + accent.lstrip("#")
    secs = "".join(section(v, A) for v in spec["visuals"])
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>시각자료</title>'
            f'<style>{css(A, slide)}</style></head><body><div class="page">{secs}</div></body></html>')


def warn(spec):
    out = []
    for v in spec["visuals"]:
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
        if v.get("type") == "pnl":
            prof = v.get("profit")
            if prof and any(abs((r - c) - p) > 0.5 for r, c, p in zip(v["revenue"], v["cost"], prof)):
                out.append(f"{v['id']}: 영업이익 ≠ 매출 − 비용 — 숫자 등록부와 맞춘다")
    return out


def shoot(html_path, out_dir):
    node = shutil.which("node")
    if not node:
        return None, "Node가 없다 — visuals.html을 브라우저로 열어 캡처한다"
    r = subprocess.run([node, os.path.join(HERE, "html_shot.cjs"), html_path, out_dir, "2"],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        return None, (r.stderr.strip() or "html_shot.cjs 실패") + " — Playwright(Node) 설치 여부 확인"
    return r.stdout.split(), None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--out", default="시각자료")
    ap.add_argument("--accent", help="강조색 hex(기본 #2a78d6)")
    ap.add_argument("--theme", help="bizplan-slides 테마 JSON — colors.primary를 강조색으로")
    ap.add_argument("--slide", action="store_true", help="16:9(1600×900) 장 크기로")
    ap.add_argument("--no-png", action="store_true")
    ap.add_argument("--sample", metavar="경로", help="예시 spec을 이 경로에 쓰고 끝낸다")
    a = ap.parse_args()
    if a.sample:
        with open(a.sample, "w", encoding="utf-8") as f:
            json.dump(SAMPLE, f, ensure_ascii=False, indent=1)
        print(f"예시 spec: {a.sample}")
        return
    if not a.spec:
        ap.error("spec(JSON) 경로가 필요하다")
    spec = json.load(open(a.spec, encoding="utf-8"))
    accent = a.accent or "2a78d6"
    if a.theme:
        accent = json.load(open(a.theme, encoding="utf-8"))["colors"].get("primary", accent)
    os.makedirs(a.out, exist_ok=True)
    page = os.path.join(a.out, "visuals.html")
    with open(page, "w", encoding="utf-8") as f:
        f.write(build(spec, accent, a.slide))
    print(f"HTML: {page} ({len(spec['visuals'])}개)")
    for w in warn(spec):
        print(f"[확인] {w}")
    if not a.no_png:
        files, err = shoot(page, a.out)
        if err:
            print(f"[PNG 건너뜀] {err}")
        else:
            print(f"PNG {len(files)}개: {', '.join(os.path.basename(f) for f in files)}")


SAMPLE = {"visuals": [
    {"id": "tam", "type": "tam", "kicker": "1-3 · 목표 고객", "headline": "첫 고객은 ○○ 지역 행사 운영사 ○○곳이다",
     "sub": "결제자(행사 운영사·매장) 기준으로 시장을 좁혔다", "takeaway": "전체 시장보다 반복 수요가 있는 좁은 시장부터 들어간다",
     "note": "출처: OO통계(2026) · 자체 인터뷰(2026.○, n=○○)",
     "layers": [{"label": "TAM", "value": "9,671만 달러", "name": "세계 포토부스 시장", "formula": "리포트 인용(2024)", "basis": "확인"},
                {"label": "SAM", "value": "○○억 원", "name": "국내 행사·소형 셀프 사진관 부스 지출", "formula": "운영 단위 ○○ × 연 이용료 ○○만 원", "basis": "산출"},
                {"label": "SOM", "value": "○○억 원", "name": "3년 안에 닿을 수 있는 지역", "formula": "수도권 행사 운영사 ○○곳 × 연 ○○만 원", "basis": "산출"},
                {"label": "1차", "value": "○○곳", "name": "첫해 계약 목표", "formula": "모집단 ○○ × 행사 보유율 ○○% × 의향 ○○% × ½", "basis": "가정"}]},
    {"id": "positioning", "type": "positioning", "kicker": "2-2 · 차별성", "headline": "취향 반영과 현장 연결을 함께 하는 곳은 아직 없다",
     "sub": "가로는 현장(부스) 연결, 세로는 개인 취향 반영 정도", "takeaway": "앱의 취향을 부스까지 잇는 오른쪽 위 칸을 처음 차지한다",
     "note": "좌표 근거: 각 서비스 공식 안내·요금표(2026.10 확인)",
     "x_axis": {"label": "현장 연결", "low": "앱 안에서만", "high": "현장 부스까지"},
     "y_axis": {"label": "개인 취향 반영", "low": "모두 같은 필터", "high": "내 취향대로"},
     "quadrant": {"x": "high", "y": "high", "label": "취향 × 현장"},
     "points": [{"name": "필터픽", "x": 8.4, "y": 8.3, "ours": True}, {"name": "보정 앱 A", "x": 1.8, "y": 6.4},
                {"name": "보정 앱 B", "x": 2.6, "y": 5.2}, {"name": "셀프 사진관 키오스크", "x": 7.6, "y": 2.0},
                {"name": "아이패드 부스 앱", "x": 6.4, "y": 3.1}, {"name": "수동 보정", "x": 1.2, "y": 3.0, "kind": "substitute"}]},
    {"id": "swot", "type": "swot", "kicker": "3-4 · SWOT", "headline": "약점(근거·팀 공백)을 행사 PoC로 먼저 메운다",
     "takeaway": "핵심 전략은 WO — 기회(매장 차별화 수요)를 이용해 약점(실증 부족)을 메운다", "note": "근거: 조사노트 2026.10",
     "s": ["앱↔부스 취향 연결", "기기 안 분석(얼굴 서버 전송 없음)", "아이패드 1대 저비용 구성"],
     "w": ["고객 직접 근거 없음", "팀 ML 역량 공백", "매출 실적 없음"],
     "o": ["셀프 사진관 과밀 → 차별화 수요", "행사·팝업 증가", "온디바이스 AI 비용 하락"],
     "t": ["대형 보정 앱의 기능 추가", "키오스크 업체의 가격 인하", "개인정보 규제"],
     "strategies": {"SO": "행사 부스로 취향 연결을 먼저 보여 준다", "WO": "행사 PoC 3건으로 실증·데이터 확보",
                    "ST": "부스 설치 네트워크로 따라오기 어렵게", "WT": "얼굴 데이터는 기기 안에서만 처리"}, "focus": "WO"},
    {"id": "funnel", "type": "funnel", "kicker": "3-2 · 목표시장 진입", "headline": "첫해 유료 운영사 2곳 — 모집단 500곳에서 좁힌다",
     "takeaway": "접촉 수가 아니라 이미 접촉한 곳(관찰)부터 숫자를 채운다", "note": "모집단: OO통계(2026) · 이후 단계: 자체 접촉 기록",
     "unit": "곳", "stages": [{"name": "모집단", "count": 500, "level": "확인"}, {"name": "접촉", "count": 50, "level": "관찰"},
                              {"name": "설명", "count": 18, "level": "관찰"}, {"name": "사전 신청", "count": 7, "level": "관찰"},
                              {"name": "유료", "count": 2, "level": "가정"}]},
    {"id": "pnl", "type": "pnl", "kicker": "3-3 · 3년 손익", "headline": "3년 차에 영업이익 60백만 원으로 흑자 전환한다",
     "takeaway": "흑자 전환 조건: 유료 전환율 ○○%, 운영사 유지율 ○○%", "note": "자체 추정 — 산정 기준은 본문 3년 표",
     "unit": "백만 원", "periods": ["1년 차", "2년 차", "3년 차"], "revenue": [40, 150, 300], "cost": [160, 210, 240]},
    {"id": "compare", "type": "compare", "kicker": "2-2 · 경쟁 비교", "headline": "고르는 일까지 대신하는 곳은 필터픽뿐이다 — 가격은 불리하다",
     "note": "확인: 각 사 공식 안내·요금표(2026.10)",
     "entities": [{"name": "필터픽", "ours": True}, {"name": "보정 앱 A"}, {"name": "키오스크 B"}, {"name": "수동 보정", "substitute": True}],
     "rows": [{"label": "필터 고르기 대신", "cells": [["●", "추천 3개"], ["○", "직접 선택"], ["○", "고정 필터"], ["○", ""]]},
              {"label": "앱↔현장 연결", "cells": [["●", "QR 프로필"], ["○", ""], ["◐", "매장 안에서만"], ["○", ""]]},
              {"label": "도입 비용", "cells": [["◐", "○○만 원"], ["●", "무료"], ["○", "1,200만 원~"], ["●", "0원"]], "disadvantage": True}],
     "verify": ["—", "앱 마켓 2026.10", "가맹 안내 2026.10", "—"]},
    {"id": "bm", "type": "bm", "kicker": "3-1 · 비즈니스 모델", "headline": "운영사가 행사당 ○○만 원을 내고, 촬영자는 무료로 쓴다",
     "note": "단가 근거: 운영사 지불 의향 중앙값(2026.○, n=○○)",
     "actors": [{"name": "촬영자", "role": "무료 사용자"}, {"name": "필터픽", "role": "앱 + 아이패드 부스", "ours": True},
                {"name": "행사 운영사", "role": "결제자"}],
     "flows": [{"from": 0, "to": 1, "kind": "value", "label": "취향 프로필"}, {"from": 1, "to": 0, "kind": "value", "label": "추천 필터 3개"},
               {"from": 2, "to": 1, "kind": "money", "label": "행사당 ○○만 원"}, {"from": 1, "to": 2, "kind": "value", "label": "차별화된 결과물"}],
     "partner": {"name": "장비 렌탈사", "role": "파트너", "label": "부스 장비 공급"}},
    {"id": "kpi", "type": "kpi", "kicker": "3-3 · 협약 기간 매출·투자·고용", "headline": "협약 기간 매출 ○○만 원 · 투자 미팅 ○곳 · 고용 2명",
     "note": "근거: 숫자 등록부(브리프 15장)",
     "tiles": [{"label": "매출", "value": "○○만 원", "basis": "행사 ○건 × ○○만 원", "status": "계획"},
               {"label": "투자", "value": "○곳 미팅", "basis": "엔젤·AC ○곳, ○월 진행", "status": "진행"},
               {"label": "고용", "value": "2명", "basis": "○월 iOS 개발 1 · ○월 ML 개발 1", "status": "계획"}]},
    {"id": "roadmap", "type": "roadmap", "kicker": "3-4 · 로드맵", "headline": "PoC 3건이 첫 유료 계약으로 이어진다",
     "takeaway": "Q3에 행사 PoC를 하기 때문에 유료 전환이 Q4에 처음 생긴다", "note": "협약 8개월 가정",
     "periods": ["1년 차 Q1", "Q2", "Q3", "Q4", "2년 차"],
     "rows": [{"axis": "제품", "cells": ["추천 v0", "부스 모드", "운영자 대시보드", "안정화", "매장 구독판"]},
              {"axis": "고객 검증", "cells": ["인터뷰 30명", "목업 반응 ○곳", "★ 행사 PoC 3건", "만족도 측정", "매장 PoC"]},
              {"axis": "판매", "cells": ["—", "운영사 접촉 ○곳", "견적 ○건", "★ 유료 ○곳", "유료 ○곳"]}],
     "kpi": {"axis": "KPI", "cells": ["—", "—", "선택률 ○○%", "월 ○○만 원", "월 ○○만 원"]}},
    {"id": "gantt", "type": "gantt", "kicker": "2-1 · 추진 일정", "headline": "협약 8개월 안에 PoC 3건까지 끝낸다",
     "takeaway": "6월 PoC 결과가 7월 첫 유료 계약의 근거가 된다", "note": "협약 8개월 가정 · 2026.○ 기준",
     "periods": ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월"],
     "tasks": [{"name": "추천 엔진 v0", "start": 1, "length": 2, "status": "완료", "out": "추천 정확도 측정"},
               {"name": "부스 모드 개발", "start": 2, "length": 3, "status": "진행", "out": "아이패드 부스 앱"},
               {"name": "운영자 대시보드", "start": 4, "length": 3, "status": "예정", "out": "운영사용 화면"},
               {"name": "행사 PoC 3건", "start": 5, "length": 2, "status": "예정", "out": "만족도·선택률"},
               {"name": "유료 전환", "start": 7, "length": 2, "status": "예정", "out": "계약 ○곳"}],
     "milestones": [{"label": "M1 시제품", "at": 3}, {"label": "M2 PoC 완료", "at": 6}, {"label": "M3 첫 매출", "at": 8}]},
    {"id": "ps_map", "type": "ps_map", "kicker": "1-2 → 2-1 · 문제와 해결", "headline": "두 문제를 두 기능이 하나씩 푼다",
     "note": "근거 수준: 문제 근거는 인터뷰 후 갱신",
     "rows": [{"no": "①", "problem": "필터 고르기 피로", "evidence": "사진 1장당 ○○초(관찰 예정)", "solution": "취향·조건 기반 추천 3개", "benefit": "선택 시간 ○○% 단축"},
              {"no": "②", "problem": "앱 취향이 부스로 안 이어짐", "evidence": "매장마다 고정 필터", "solution": "QR로 부스에서 프로필 불러오기", "benefit": "어디서나 같은 내 톤"}]},
    {"id": "trend", "type": "trend", "kicker": "1-1 · 외부 배경", "headline": "세계 포토부스 시장은 연 9%씩 커진다",
     "note": "출처: QYResearch(2024) — 2025~2031은 전망", "unit": "백만 달러",
     "labels": ["2024", "2025", "2026", "2027", "2028", "2029", "2030", "2031"],
     "values": [96.7, 105.3, 114.7, 124.9, 136.1, 148.2, 161.4, 176.5], "forecast_from": 0},
    {"id": "before_after", "type": "before_after", "kicker": "2-1 · 검증 결과(예시 형식)", "headline": "추천을 쓰면 필터 고르는 시간이 ○○% 줄었다",
     "note": "시범 사용 ○명 · ○주(2026.○) — 측정 후 갱신", "metrics": [{"label": "필터 선택 시간", "before": 40, "after": 9, "unit": "초", "better": "lower"},
                                                               {"label": "다시 보정한 비율", "before": 62, "after": 21, "unit": "%", "better": "lower"}]},
    {"id": "bar", "type": "bar", "kicker": "2-2 · 비용 비교(예시 형식)", "headline": "부스 한 세트 비용은 키오스크의 ○○% 수준이다",
     "note": "견적·공개 가격 기준(2026.○) — 견적 확보 후 갱신", "unit": "만 원",
     "items": [{"label": "셀프 사진관 키오스크", "value": 1200}, {"label": "렌탈 부스(행사 1회)", "value": 150},
               {"label": "필터픽 부스 1세트", "value": 180, "ours": True}]},
]}

if __name__ == "__main__":
    main()
