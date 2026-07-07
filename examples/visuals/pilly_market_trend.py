# -*- coding: utf-8 -*-
"""
PILLY 시니어 산업 규모 추이 막대 — visual-guide.md 시장규모 그래프 코드를 PILLY 데이터로 변형.
2020년 72조 -> 2030년 168조 [실제, 한국무역협회], 중간 연도는 CAGR 8.8% 보간 [예시 추정].
실행: python pilly_market_trend.py  ->  pilly_market_trend.png
"""
import platform
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

# 실측 앵커: 2020=72조, 2030=168조 [실제, 한국무역협회]. 중간값은 CAGR로 보간 [예시 추정].
anchor_start, anchor_end, n_years = 72.0, 168.0, 10
cagr = (anchor_end / anchor_start) ** (1 / n_years) - 1  # ≈ 0.0884

years = [2020, 2022, 2024, 2026, 2028, 2030]
size = [round(anchor_start * (1 + cagr) ** (y - 2020), 1) for y in years]
is_actual = [y in (2020, 2030) for y in years]  # 양 끝만 실측

fig, ax = plt.subplots(figsize=(9, 5.5))
colors = ["#1F4E79" if a else "#A9C4E4" for a in is_actual]
bars = ax.bar(years, size, color=colors, width=1.3)

# 추세선(전체 CAGR 반영)
z = np.polyfit(years, size, 1)
ax.plot(years, np.poly1d(z)(years), "--", color="#C44E52", linewidth=2,
        label=f"추세선 (CAGR {cagr * 100:.1f}%)")

# 막대 위 수치 라벨 + 실측/보간 구분
for b, v, a in zip(bars, size, is_actual):
    tag = " [실제]" if a else ""
    ax.text(b.get_x() + b.get_width() / 2, v + 3, f"{v:g}조{tag}",
            ha="center", fontsize=9.5,
            fontweight="bold" if a else "normal")

ax.set_title("국내 시니어 산업 시장 규모 추이 (2020→2030)", fontsize=14, pad=12)
ax.set_ylabel("시장 규모 (조원)")
ax.set_ylim(0, 195)
ax.set_xticks(years)

legend_items = [
    Patch(facecolor="#1F4E79", label="실측 앵커 (한국무역협회)"),
    Patch(facecolor="#A9C4E4", label="CAGR 8.8% 보간 [예시 추정]"),
]
h, l = ax.get_legend_handles_labels()
ax.legend(handles=legend_items + h, loc="upper left", fontsize=9)
ax.spines[["top", "right"]].set_visible(False)

fig.text(0.99, 0.01,
         "출처: 시니어산업 2020년 72조→2030년 168조, 한국무역협회 [실제] / 중간 연도는 CAGR 보간 [예시 추정]",
         ha="right", fontsize=7.5, color="gray")

plt.tight_layout()
plt.savefig("pilly_market_trend.png", dpi=200)
print(f"saved pilly_market_trend.png (CAGR={cagr*100:.2f}%)")
