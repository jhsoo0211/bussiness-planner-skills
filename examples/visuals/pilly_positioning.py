# -*- coding: utf-8 -*-
"""
PILLY 2x2 포지셔닝맵 — visual-guide.md 포지셔닝맵(2축) 절차 기반.
X축: 어르신 독립 사용성(폰 의존<->폰 불필요), Y축: 데이터 신뢰성(자가보고<->센서 실측).
PILLY는 우상단에 강조. '지자체 연동은 PILLY만(◎)' 주석.
실행: python pilly_positioning.py  ->  pilly_positioning.png
"""
import platform
import matplotlib.pyplot as plt

if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

# (라벨, x, y, 강조여부, 지자체연동)
points = [
    ("스마트폰 앱\n(Medisafe·MyTherapy)", 2.0, 2.0, False, "X"),
    ("요일별 약통·알람시계", 7.2, 2.4, False, "X"),
    ("해외 디스펜서\n(MedMinder·Hero)", 6.8, 6.6, False, "X"),
    ("PILLY", 8.6, 8.7, True, "◎"),
]

fig, ax = plt.subplots(figsize=(8.5, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)

# 사분면 구분선
ax.axhline(5, color="#BBBBBB", linewidth=1, linestyle="--", zorder=1)
ax.axvline(5, color="#BBBBBB", linewidth=1, linestyle="--", zorder=1)

for label, x, y, hi, gov in points:
    if hi:
        ax.scatter(x, y, s=620, color="#1F4E79", edgecolor="white",
                   linewidth=2, zorder=5)
        ax.text(x, y - 0.72, label, ha="center", va="top", fontsize=13,
                fontweight="bold", color="#1F4E79", zorder=6)
        ax.text(x, y + 0.02, "◎", ha="center", va="center", fontsize=15,
                color="white", zorder=7)
    else:
        ax.scatter(x, y, s=300, color="#9AA7B4", edgecolor="white",
                   linewidth=1.5, zorder=4)
        ax.text(x, y - 0.55, label, ha="center", va="top", fontsize=10.5,
                color="#3A4A5A", zorder=6)

# 축 라벨
ax.set_xlabel("어르신 독립 사용성  (폰 의존  →  폰 불필요)",
              fontsize=12, fontweight="bold")
ax.set_ylabel("데이터 신뢰성  (자가보고  →  센서 실측)",
              fontsize=12, fontweight="bold")
ax.set_title("경쟁 포지셔닝맵 — PILLY만 우상단(폰 불필요 × 복용 실측) 독점",
             fontsize=13, pad=14, fontweight="bold")

# 눈금 대신 방향만
ax.set_xticks([])
ax.set_yticks([])
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)

# 지자체 연동 주석(축 밖 차별 요소)
ax.text(0.25, 9.6,
        "◎ = 국내 지자체 돌봄 대시보드 연동 (PILLY만 해당)",
        fontsize=10, color="#1F4E79", fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#EAF1F9",
                  edgecolor="#1F4E79", linewidth=1))

fig.text(0.99, 0.005,
         "축 선정 근거: 독거·고령 도달의 핵심(X) + 돌봄 의사결정의 근거(Y) — 본문 2-3",
         ha="right", fontsize=8, color="gray")

plt.tight_layout()
plt.savefig("pilly_positioning.png", dpi=200, bbox_inches="tight")
print("saved pilly_positioning.png")
