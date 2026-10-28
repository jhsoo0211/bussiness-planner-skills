# -*- coding: utf-8 -*-
"""사업계획서용 차트 템플릿 (한글 폰트 자동 설정 포함).

사용법: 스킬 폴더에 캐시를 만들지 않도록 경로만 추가해 import 한다(python3 -B 권장).
    import sys; sys.path.insert(0, "<설치 위치>/bizplan-visual/scripts")
    from chart_templates import set_target, use_palette, bar_compare, growth_line, tam_sam_som, positioning_map, gantt, funnel, pnl_combo
각 함수는 데이터만 바꿔 호출하며 저장된 파일 경로를 반환한다. 출력 파일은 작업 폴더에 둔다.
공통 규칙: 심사용 도표는 장식보다 가독성 — 큰 글씨, 값 라벨 직접 표기, 출처는 그림 안 캡션에.
"""
import logging
import tempfile
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 굵은 글꼴 파일이 따로 없을 때 매번 찍히는 findfont 경고를 숨긴다(결과물에는 굵게 표시된다)
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

PALETTE = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#64748b"]
DPI = 200            # 문서·슬라이드 공통 저장 해상도 (bizplan-visual 규격)
_SCALE = 1.0         # set_target("slide")면 글자를 키운다


def use_palette(colors):
    """슬라이드 템플릿 색 등으로 팔레트를 바꾼다. 첫 색이 강조(자사)색이다."""
    global PALETTE
    PALETTE = list(colors) + PALETTE[len(colors):]
    return PALETTE


def set_target(target="doc"):
    """doc=A4 문서용(기본), slide=16:9 슬라이드 삽입용(글자 약 1.35배)."""
    global _SCALE
    _SCALE = 1.35 if target == "slide" else 1.0
    return _SCALE


def _fs(size):
    return size * _SCALE


def setup_korean_font():
    """설치된 한글 폰트를 탐색해 matplotlib 기본으로 지정. 없으면 경고만 하고 진행."""
    candidates = ["NanumGothic", "NanumBarunGothic", "Malgun Gothic",
                  "Noto Sans CJK KR", "Noto Sans KR",
                  # Noto CJK JP/SC/TC/HK ttc에도 한글 글리프가 포함되어 있다 —
                  # 리눅스 컨테이너에는 KR 대신 이들만 있는 경우가 많다.
                  "Noto Sans CJK JP", "Noto Sans CJK SC",
                  "Noto Sans CJK TC", "Noto Sans CJK HK", "AppleGothic",
                  # 마지막 후보: 한글 글리프가 있는 범용 CJK 폰트(웹 샌드박스·컨테이너에 흔하다)
                  "Apple SD Gothic Neo", "Source Han Sans KR", "WenQuanYi Zen Hei",
                  "Droid Sans Fallback"]

    def pick():
        installed = {f.name for f in fm.fontManager.ttflist}
        return next((n for n in candidates if n in installed), None)

    name = pick()
    if name is None:
        # 폰트를 설치한 뒤라도 matplotlib 캐시가 옛 목록이면 못 찾는다 — 한 번만 다시 읽는다
        fm._load_fontmanager(try_read_cache=False)
        name = pick()
    if name:
        plt.rcParams["font.family"] = name
    else:
        print("[경고] 한글 폰트를 찾지 못했습니다. apt install fonts-nanum 후 다시 실행하세요")
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 100
    return plt.rcParams["font.family"]


def _fmt_val(v):
    """값 라벨 포맷: 정수는 천단위 콤마, 소수는 1자리 유지."""
    return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"


def _source(fig, text, prefix="출처: ", y=-0.02):
    """출처 캡션. 기본은 그림 아래 바깥(y<0) — 축 이름과 겹치지 않게 저장 때 캔버스가 늘어난다."""
    if text:
        fig.text(0.99, y, f"{prefix}{text}", ha="right", va="top" if y < 0 else "bottom",
                 fontsize=_fs(8), color="#64748b")


def _save(fig, out):
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def bar_compare(labels, values, title, ylabel, out="bar.png", source=None, highlight=None):
    """경쟁 비교·수치 대비용 막대그래프. highlight=강조할 라벨명."""
    setup_korean_font()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    colors = [PALETTE[0] if (highlight and l == highlight) else "#94a3b8" for l in labels] \
        if highlight else PALETTE[: len(labels)]
    bars = ax.bar(labels, values, color=colors, width=0.55)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v, _fmt_val(v), ha="center", va="bottom",
                fontsize=_fs(11), fontweight="bold")
    ax.set_title(title, fontsize=_fs(14), fontweight="bold", pad=12)
    ax.set_ylabel(ylabel, fontsize=_fs(10))
    ax.tick_params(labelsize=_fs(10))
    ax.spines[["top", "right"]].set_visible(False)
    _source(fig, source)
    return _save(fig, out)


def growth_line(years, values, title, ylabel, out="growth.png", cagr=None, source=None):
    """시장 규모 성장 추이(CAGR 주석 포함).

    cagr를 주지 않으면 첫해·말년 값으로 계산해 표기한다. 주면 계산값과 대조해
    0.5%p 넘게 다르면 경고한다(보고서 인용치와 산식의 모순 방지).
    """
    setup_korean_font()
    numeric = all(isinstance(x, (int, float)) for x in years)
    computed = None
    if numeric and len(values) > 1 and values[0] > 0:
        computed = ((values[-1] / values[0]) ** (1 / (years[-1] - years[0])) - 1) * 100
    if cagr is None and computed is not None:
        cagr = f"{computed:.1f}% (자동 계산)"
    elif computed is not None:
        try:
            stated = float(str(cagr).split("%")[0])
        except ValueError:
            stated = computed      # "약 30%"처럼 숫자가 아니면 대조를 건너뛴다
        if abs(stated - computed) > 0.5:
            print(f"[경고] CAGR 표기 {stated}%가 값으로 계산한 {computed:.1f}%와 다릅니다 — 출처·기간을 확인하세요")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(years, values, marker="o", lw=2.5, color=PALETTE[0])
    # 연도 축은 소수 눈금(2022.5 등)이 나오지 않도록 실제 연도값으로 고정
    if numeric:
        ax.set_xticks(list(years))
        ax.set_xticklabels([f"{int(x)}" if float(x).is_integer() else str(x) for x in years])
    for x, y in zip(years, values):
        ax.annotate(_fmt_val(y), (x, y), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=_fs(10), fontweight="bold")
    if cagr:
        # 숫자로 받으면 %를 붙이고, 문자열이면 호출자가 정한 표기를 그대로 쓴다
        cagr_label = f"CAGR {cagr}%" if isinstance(cagr, (int, float)) else f"CAGR {cagr}"
        ax.text(0.03, 0.92, cagr_label, transform=ax.transAxes, fontsize=_fs(13),
                fontweight="bold", color=PALETTE[3],
                bbox=dict(boxstyle="round,pad=0.35", fc="#fef2f2", ec=PALETTE[3]))
    ax.set_title(title, fontsize=_fs(14), fontweight="bold", pad=12)
    ax.set_ylabel(ylabel, fontsize=_fs(10))
    ax.tick_params(labelsize=_fs(10))
    ax.spines[["top", "right"]].set_visible(False)
    _source(fig, source)
    return _save(fig, out)


def tam_sam_som(tam, sam, som, unit="억 원", out="tam_sam_som.png", labels=("TAM", "SAM", "SOM"),
                descs=("전체 시장", "유효 시장", "수익 시장"), bases=None, source=None):
    """TAM/SAM/SOM 동심원 도식. bases=층위별 산정근거 한 줄 3개, source=출처 캡션."""
    setup_korean_font()
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    vals = [tam, sam, som]
    radii = [1.0, 0.66, 0.36]
    colors = ["#dbeafe", "#93c5fd", PALETTE[0]]
    for r, c in zip(radii, colors):
        ax.add_patch(plt.Circle((0, -1 + r), r, color=c, ec="white", lw=2))
    ys = [0.72, 0.05, -0.5]
    tc = ["#1e3a8a", "#1e3a8a", "white"]
    for (lab, d), v, y, col in zip(zip(labels, descs), vals, ys, tc):
        ax.text(0, y + 0.12, lab, ha="center", fontsize=_fs(15), fontweight="bold", color=col)
        ax.text(0, y - 0.02, f"{v:,.0f}{unit}", ha="center", fontsize=_fs(12), fontweight="bold", color=col)
        ax.text(0, y - 0.14, d, ha="center", fontsize=_fs(9), color=col)
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal"); ax.axis("off")
    y = 0.06
    if bases:
        # 각 층위에 금액 + 산정근거 한 줄 병기(visual-guide 공통 원칙)
        fig.text(0.02, y, "\n".join(f"{l}: {b}" for l, b in zip(labels, bases)),
                 ha="left", va="top", fontsize=_fs(9), color="#334155", linespacing=1.5)
        y -= 0.045 * len(bases) + 0.01
    _source(fig, source, y=y if bases else -0.02)
    return _save(fig, out)


def positioning_map(points, x_label, y_label, out="positioning.png", ours=None, title="포지셔닝 맵",
                    source=None):
    """points={이름:(x,y)} 0~10 스케일. ours=자사 이름(강조). source=좌표 근거(공개 스펙·리뷰 등)."""
    setup_korean_font()
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.axhline(5, color="#cbd5e1", lw=1); ax.axvline(5, color="#cbd5e1", lw=1)
    for name, (x, y) in points.items():
        is_ours = name == ours
        ax.scatter(x, y, s=420 if is_ours else 240,
                   color=PALETTE[0] if is_ours else "#94a3b8", zorder=3,
                   edgecolors="white", linewidths=1.5)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(0, 16), ha="center",
                    fontsize=_fs(11), fontweight="bold" if is_ours else "normal",
                    color=PALETTE[0] if is_ours else "#334155")
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_xlabel(x_label, fontsize=_fs(12), fontweight="bold")
    ax.set_ylabel(y_label, fontsize=_fs(12), fontweight="bold")
    ax.set_title(title, fontsize=_fs(14), fontweight="bold", pad=12)
    ax.set_xticks([]); ax.set_yticks([])
    _source(fig, source, prefix="좌표 근거: ")
    return _save(fig, out)


_STATUS = {"완료": (1.0, None), "진행": (0.85, None), "예정": (0.45, "//")}


def gantt(tasks, out="gantt.png", title="사업 추진 일정", xlabel="개월차", milestones=None, source=None):
    """추진 일정표.

    tasks=[(이름, 시작개월, 기간개월[, 상태]), ...] 1-indexed. 상태는 완료/진행/예정(배지·투명도로 구분).
    milestones=[(이름, 개월), ...] 해당 월 끝에 마름모로 표시. 막대가 라벨보다 짧으면 라벨을 막대 오른쪽에 쓴다.
    """
    setup_korean_font()
    fig_w = 8
    fig, ax = plt.subplots(figsize=(fig_w, 0.55 * len(tasks) + 1.6))
    total = max(t[1] - 1 + t[2] for t in tasks)
    month_in = fig_w * 0.82 / total            # 한 달이 차지하는 대략 폭(인치)
    for i, task in enumerate(reversed(tasks)):
        name, start, dur = task[:3]
        status = task[3] if len(task) > 3 else None
        alpha, hatch = _STATUS.get(status, (0.9, None))
        color = PALETTE[i % len(PALETTE)]
        ax.barh(i, dur, left=start - 1, height=0.5, color=color, alpha=alpha, hatch=hatch,
                edgecolor=color)
        label = f"{name} [{status}]" if status else name
        text_in = len(label) * _fs(10) / 72 * 0.95
        if text_in < dur * month_in * 0.92:
            ax.text(start - 1 + dur / 2, i, label, ha="center", va="center", fontsize=_fs(10),
                    color="white" if alpha > 0.6 else "#1e293b", fontweight="bold")
        else:
            ax.text(start - 1 + dur + 0.08, i, label, ha="left", va="center", fontsize=_fs(10),
                    color="#1e293b", fontweight="bold")
    for name, month in (milestones or []):
        ax.scatter(month, -0.75, marker="D", s=70, color=PALETTE[3], zorder=4, clip_on=False)
        ax.text(month + 0.1, -0.75, name, ha="left", va="center", fontsize=_fs(9), color=PALETTE[3])
    ax.set_yticks([])
    ax.set_xlim(0, total + (0.6 if any(len(t[0]) > 6 for t in tasks) else 0))
    # 눈금 라벨은 각 달의 가운데에 1..N (축 끝에 N+1이 찍히지 않게)
    ax.set_xticks([m - 0.5 for m in range(1, total + 1)])
    ax.set_xticklabels([str(m) for m in range(1, total + 1)], fontsize=_fs(10))
    ax.set_xticks(range(0, total + 1), minor=True)
    ax.set_xlabel(xlabel, fontsize=_fs(10))
    ax.set_title(title, fontsize=_fs(14), fontweight="bold", pad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", which="minor", color="#e2e8f0", lw=0.8)
    ax.tick_params(axis="x", which="major", length=0)
    ax.set_axisbelow(True)
    # x축 이름(개월차) 아래로 내려 겹치지 않게
    _source(fig, source, prefix="", y=-0.04)
    return _save(fig, out)


_LEVEL_COLOR = {"확인": "#10b981", "산출": "#2563eb", "관찰": "#8b5cf6", "가정": "#ef4444"}


def funnel(stages, title, out="funnel.png", source=None):
    """고객 확보 퍼널. stages=[(단계명, 인원·곳 수, 근거 수준), ...] — 근거 수준은 확인·산출·관찰·가정(생략 가능).

    단계 사이에 구간 전환율을 적고, 근거 수준 라벨을 오른쪽에 색으로 붙인다(가정은 빨강).
    제목에는 결론 수치를 넣는다(예: "유료 전환 2곳 — 모집단 500곳에서").
    """
    setup_korean_font()
    n = len(stages)
    fig, ax = plt.subplots(figsize=(7, 0.75 * n + 1.4))
    top = max(c for _, c, *_ in stages) or 1
    for i, st in enumerate(stages):
        name, count = st[0], st[1]
        level = st[2] if len(st) > 2 else None
        w = max((count / top) ** 0.5, 0.34)     # 면적감은 유지하되 작은 단계도 글자가 들어가게
        y = n - 1 - i
        ax.barh(y, w, left=(1 - w) / 2, height=0.62, color=PALETTE[0] if i == n - 1 else "#93c5fd")
        ax.text(0.5, y, f"{name}  {_fmt_val(count)}", ha="center", va="center", fontsize=_fs(11),
                fontweight="bold", color="white" if i == n - 1 else "#0f172a")
        if level:
            ax.text(1.02, y, level, ha="left", va="center", fontsize=_fs(9), fontweight="bold",
                    color=_LEVEL_COLOR.get(level, "#64748b"))
        if i:
            prev = stages[i - 1][1]
            p = count / prev * 100 if prev else None      # 1% 아래는 유효숫자 2자리 — 0%로 뭉개지 않는다
            rate = "—" if p is None else f"{p:.0f}%" if p >= 10 or p == 0 else f"{p:.1f}%" if p >= 1 else f"{p:.2g}%"
            ax.text(0.5, y + 0.5, f"↓ {rate}", ha="center", va="center", fontsize=_fs(9), color="#475569")
    ax.set_xlim(0, 1.12)
    ax.set_ylim(-0.6, n - 0.4)
    ax.axis("off")
    ax.set_title(title, fontsize=_fs(14), fontweight="bold", pad=10)
    _source(fig, source)
    return _save(fig, out)


def pnl_combo(periods, revenue, cost, title, unit="백만 원", profit=None, out="pnl.png", source=None):
    """매출(막대) · 총비용 · 영업이익(선) 콤보 차트. 영업이익이 처음 0 이상이 되는 기간에 ★(흑자 전환)을 단다.

    profit을 주지 않으면 매출 − 총비용으로 계산한다. 주면 계산값과 대조해 다르면 경고한다.
    """
    setup_korean_font()
    calc = [r - c for r, c in zip(revenue, cost)]
    if profit is None:
        profit = calc
    elif any(abs(p - q) > 0.5 for p, q in zip(profit, calc)):
        print("[경고] 영업이익이 매출 − 총비용과 다릅니다 — 표를 검산하세요")
    x = list(range(len(periods)))
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    bars = ax.bar(x, revenue, width=0.55, color=PALETTE[0], label="매출")
    for b, v in zip(bars, revenue):
        ax.text(b.get_x() + b.get_width() / 2, v, _fmt_val(v), ha="center", va="bottom",
                fontsize=_fs(10), fontweight="bold")
    ax.plot(x, cost, marker="o", lw=2, color="#94a3b8", label="총비용")
    ax.plot(x, profit, marker="o", lw=2.4, color=PALETTE[3], label="영업이익")
    for xi, v in zip(x, profit):
        ax.annotate(_fmt_val(v), (xi, v), textcoords="offset points", xytext=(16, 0), ha="left", va="center",
                    fontsize=_fs(9), fontweight="bold", color=PALETTE[3],
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))
    ax.axhline(0, color="#475569", lw=0.8)
    lo = min(0, min(profit), min(cost))
    hi = max(max(revenue), max(cost))
    ax.set_ylim(lo - (hi - lo) * 0.12 if lo < 0 else 0, hi * 1.15)
    be = next((i for i, v in enumerate(profit) if v >= 0), None)
    if be is not None and be > 0:
        ax.annotate("★ 흑자 전환", (be, profit[be]), textcoords="offset points", xytext=(0, 16),
                    ha="center", fontsize=_fs(10), fontweight="bold", color=PALETTE[3])
    ax.set_xticks(x)
    ax.set_xticklabels([str(p) for p in periods])
    ax.set_ylabel(unit, fontsize=_fs(10))
    ax.tick_params(labelsize=_fs(10))
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=_fs(9), loc="upper left")
    ax.set_title(title, fontsize=_fs(14), fontweight="bold", pad=12)
    _source(fig, source)
    return _save(fig, out)


if __name__ == "__main__":
    # 자체 테스트: 7종 전부 샘플 생성 (임시 폴더)
    tmp = tempfile.mkdtemp(prefix="bizplan-charts-")
    p = lambda n: os.path.join(tmp, n)
    print("font:", setup_korean_font())
    print(bar_compare(["자사", "경쟁 A", "경쟁 B"], [92, 61, 48], "핵심 지표 비교", "정확도(%)",
                      out=p("t_bar.png"), highlight="자사", source="자체 실험(2026)"))
    print(growth_line([2022, 2023, 2024, 2025, 2026], [120, 156, 210, 275, 360],
                      "국내 시장 규모 추이", "시장 규모(억 원)", cagr="31.6%",
                      out=p("t_growth.png"), source="OO리서치 2026"))
    print(tam_sam_som(5200, 1300, 180, out=p("t_tss.png"),
                      bases=("국내 OO 시장 전체", "20~30대 앱 사용자 지출", "3년 누적 목표 매출"),
                      source="OO통계(2026)"))
    print(positioning_map({"자사": (8, 8), "경쟁 A": (3, 7), "경쟁 B": (7, 3), "경쟁 C": (2, 2)},
                          "개인화 수준", "실시간성", ours="자사", out=p("t_pos.png"),
                          source="공개 스펙 비교(2026-10)"))
    print(gantt([("설계", 1, 1, "완료"), ("MVP 개발", 1, 3, "진행"), ("베타 테스트", 3, 2, "예정"),
                 ("정식 출시", 5, 1, "예정"), ("성과 검증", 5, 2, "예정")],
                milestones=[("M1", 2), ("M2", 4), ("M3", 6)], out=p("t_gantt.png")))
    print(funnel([("모집단", 500, "확인"), ("접촉", 50, "관찰"), ("설명", 18, "관찰"),
                  ("사전 신청", 7, "관찰"), ("유료", 2, "가정")],
                 "유료 전환 2곳 — 모집단 500곳에서", out=p("t_funnel.png"), source="OO통계(2026) · 자체 접촉 기록"))
    print(pnl_combo(["1년 차", "2년 차", "3년 차"], [40, 150, 300], [160, 210, 240],
                    "3년 차 영업이익 60백만 원 · 3년 차 흑자 전환", out=p("t_pnl.png"), source="자체 추정(산정 기준은 본문 표)"))
