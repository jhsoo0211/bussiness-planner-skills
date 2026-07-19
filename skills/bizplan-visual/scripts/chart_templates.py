# -*- coding: utf-8 -*-
"""사업계획서용 차트 템플릿 (한글 폰트 자동 설정 포함).

사용법: 각 함수를 import 해서 데이터만 바꿔 호출한다. 반환값은 저장된 파일 경로.
    from chart_templates import setup_korean_font, bar_compare, growth_line, tam_sam_som, positioning_map, gantt
공통 규칙: 심사용 도표는 장식보다 가독성 — 큰 글씨, 값 라벨 직접 표기, 출처는 캡션에.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch

PALETTE = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#64748b"]


def setup_korean_font():
    """설치된 한글 폰트를 탐색해 matplotlib 기본으로 지정. 없으면 경고만 하고 진행."""
    candidates = ["NanumGothic", "NanumBarunGothic", "Malgun Gothic",
                  "Noto Sans CJK KR", "Noto Sans KR", "AppleGothic"]
    installed = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            plt.rcParams["font.family"] = name
            break
    else:
        print("[경고] 한글 폰트를 찾지 못했습니다. apt install fonts-nanum 후 fm._load_fontmanager(try_read_cache=False)")
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 150
    return plt.rcParams["font.family"]


def _save(fig, out):
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight", facecolor="white")
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
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    if source:
        fig.text(0.99, 0.01, f"출처: {source}", ha="right", fontsize=8, color="#64748b")
    return _save(fig, out)


def growth_line(years, values, title, ylabel, out="growth.png", cagr=None, source=None):
    """시장 규모 성장 추이(CAGR 주석 포함)."""
    setup_korean_font()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(years, values, marker="o", lw=2.5, color=PALETTE[0])
    for x, y in zip(years, values):
        ax.annotate(f"{y:,.0f}", (x, y), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=10, fontweight="bold")
    if cagr:
        ax.text(0.03, 0.92, f"CAGR {cagr}", transform=ax.transAxes, fontsize=13,
                fontweight="bold", color=PALETTE[3],
                bbox=dict(boxstyle="round,pad=0.35", fc="#fef2f2", ec=PALETTE[3]))
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    if source:
        fig.text(0.99, 0.01, f"출처: {source}", ha="right", fontsize=8, color="#64748b")
    return _save(fig, out)


def tam_sam_som(tam, sam, som, unit="억 원", out="tam_sam_som.png", labels=("TAM", "SAM", "SOM"), descs=("전체 시장", "유효 시장", "수익 시장")):
    """TAM/SAM/SOM 동심원 도식."""
    setup_korean_font()
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    vals = [tam, sam, som]
    radii = [1.0, 0.66, 0.36]
    colors = ["#dbeafe", "#93c5fd", "#2563eb"]
    for r, c in zip(radii, colors):
        ax.add_patch(plt.Circle((0, -1 + r), r, color=c, ec="white", lw=2))
    ys = [0.72, 0.05, -0.5]
    tc = ["#1e3a8a", "#1e3a8a", "white"]
    for (lab, d), v, y, col in zip(zip(labels, descs), vals, ys, tc):
        ax.text(0, y + 0.12, lab, ha="center", fontsize=15, fontweight="bold", color=col)
        ax.text(0, y - 0.02, f"{v:,.0f}{unit}", ha="center", fontsize=12, fontweight="bold", color=col)
        ax.text(0, y - 0.14, d, ha="center", fontsize=9, color=col)
    ax.set_xlim(-1.15, 1.15); ax.set_ylim(-1.15, 1.15)
    ax.set_aspect("equal"); ax.axis("off")
    return _save(fig, out)


def positioning_map(points, x_label, y_label, out="positioning.png", ours=None, title="포지셔닝 맵"):
    """points={이름:(x,y)} 0~10 스케일. ours=자사 이름(강조)."""
    setup_korean_font()
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    ax.axhline(5, color="#cbd5e1", lw=1); ax.axvline(5, color="#cbd5e1", lw=1)
    for name, (x, y) in points.items():
        is_ours = name == ours
        ax.scatter(x, y, s=420 if is_ours else 240,
                   color=PALETTE[0] if is_ours else "#94a3b8", zorder=3,
                   edgecolors="white", linewidths=1.5)
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(0, 16), ha="center",
                    fontsize=11, fontweight="bold" if is_ours else "normal",
                    color=PALETTE[0] if is_ours else "#334155")
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_xlabel(x_label, fontsize=12, fontweight="bold")
    ax.set_ylabel(y_label, fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xticks([]); ax.set_yticks([])
    return _save(fig, out)


def gantt(tasks, out="gantt.png", title="사업 추진 일정", xlabel="개월차"):
    """tasks=[(이름, 시작개월, 기간개월), ...] 1-indexed."""
    setup_korean_font()
    fig, ax = plt.subplots(figsize=(8, 0.55 * len(tasks) + 1.6))
    for i, (name, start, dur) in enumerate(reversed(tasks)):
        ax.barh(i, dur, left=start - 1, height=0.5, color=PALETTE[i % len(PALETTE)], alpha=0.9)
        ax.text(start - 1 + dur / 2, i, name, ha="center", va="center", fontsize=10,
                color="white", fontweight="bold")
    total = max(s - 1 + d for _, s, d in tasks)
    ax.set_yticks([])
    ax.set_xticks(range(0, total + 1))
    ax.set_xticklabels([str(m) for m in range(1, total + 2)])
    ax.set_xlabel(xlabel)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color="#e2e8f0", lw=0.8)
    ax.set_axisbelow(True)
    return _save(fig, out)


if __name__ == "__main__":
    # 자체 테스트: 5종 전부 샘플 생성
    print("font:", setup_korean_font())
    print(bar_compare(["자사", "경쟁 A", "경쟁 B"], [92, 61, 48], "핵심 지표 비교", "정확도(%)",
                      out="/tmp/t_bar.png", highlight="자사", source="자체 실험(2026)"))
    print(growth_line([2022, 2023, 2024, 2025, 2026], [120, 156, 210, 275, 360],
                      "국내 시장 규모 추이", "시장 규모(억 원)", cagr="31.6%",
                      out="/tmp/t_growth.png", source="OO리서치 2026"))
    print(tam_sam_som(5200, 1300, 180, out="/tmp/t_tss.png"))
    print(positioning_map({"자사": (8, 8), "경쟁 A": (3, 7), "경쟁 B": (7, 3), "경쟁 C": (2, 2)},
                          "개인화 수준", "실시간성", ours="자사", out="/tmp/t_pos.png"))
    print(gantt([("MVP 개발", 1, 3), ("베타 테스트", 3, 2), ("정식 출시", 5, 1),
                 ("마케팅 확대", 5, 3), ("성과 검증", 7, 2)], out="/tmp/t_gantt.png"))
