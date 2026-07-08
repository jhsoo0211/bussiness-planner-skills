# -*- coding: utf-8 -*-
"""
PILLY TAM/SAM/SOM 동심원 — bizplan-visual visual-guide.md 동심원 코드를 PILLY 데이터로 변형.
각 층위에 금액 + 산정근거 한 줄 병기, SOM만 진한 색으로 강조.
실행: python pilly_tam_sam_som.py  ->  pilly_tam_sam_som.png
"""
import platform
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

# (이름, 시장 정의, 금액, 산정근거 한 줄, 반지름, 색) — 반지름은 포함관계 표현용(값 비례 아님)
layers = [
    ("TAM", "국내 시니어 헬스케어 시장", "약 33.6조원",
     "시니어산업 168조(2030) × 헬스케어 비중 20% [예시 추정]", 1.00, "#DCE7F2"),
    ("SAM", "독거+만성질환 어르신 복약관리", "약 8,500억원/년",
     "약 212만 명 × 연 40만 원 [모수 실제·단가 추정]", 0.60, "#7FA8D4"),
    ("SOM", "지자체 시범사업(초기 3년)", "ARR 약 43억원",
     "1만 대(20개 지자체×500대) = SAM의 약 0.5%, 보수적", 0.32, "#1F4E79"),
]

fig, ax = plt.subplots(figsize=(11, 7))
ax.set_xlim(-1.15, 3.4)
ax.set_ylim(-1.25, 1.2)
ax.set_aspect("equal")
ax.axis("off")

for i, (name, label, value, basis, r, color) in enumerate(layers):
    is_som = (i == 2)
    ax.add_patch(Circle((0, r - 1.0), r, facecolor=color,
                        edgecolor="white", linewidth=2.5, zorder=i + 1))
    top_y = 2 * r - 1.0  # 각 원의 꼭대기(아래 끝 y=-1 정렬)
    ax.text(0, top_y - 0.13, name, ha="center",
            fontsize=15 if is_som else 13,
            fontweight="bold", color="white" if is_som else "#1A2A3A",
            zorder=10)
    # 우측 리더라인: 금액 + 산정근거 한 줄 병기(핵심 원칙)
    label_color = "#1F4E79" if is_som else "#333333"
    ax.annotate(f"{name}  {label}\n{value}\n근거: {basis}",
                xy=(0.18, top_y - 0.16), xytext=(1.32, top_y - 0.08),
                fontsize=10.5 if is_som else 9.5, va="top",
                fontweight="bold" if is_som else "normal", color=label_color,
                arrowprops=dict(arrowstyle="-", color="#888888", lw=1))

ax.text(0.35, 1.12, "PILLY 시장 규모 (TAM / SAM / SOM)",
        ha="center", fontsize=15, fontweight="bold", color="#1A2A3A")
ax.text(1.12, -1.2,
        "출처: 시니어산업 168조(2030) 한국무역협회 [실제] / 헬스케어 비중·단가·목표 점유율 [예시 추정]",
        fontsize=8, color="gray", ha="center")

plt.tight_layout()
plt.savefig("pilly_tam_sam_som.png", dpi=200, bbox_inches="tight")
print("saved pilly_tam_sam_som.png")
