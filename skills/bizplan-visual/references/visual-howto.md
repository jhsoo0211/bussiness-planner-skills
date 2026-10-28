# 시각자료 제작 방법 (visual-guide 분리본)

> 사례 출처·용어는 [visual-guide.md](visual-guide.md) 머리말과 같다. 그림은 `scripts/html_visuals.py`(유형·규칙은 [visual-html.md](visual-html.md))를 먼저 쓰고, Node가 없으면 `scripts/chart_templates.py`를 쓴다 — 아래 코드는 둘 다에 없는 도식을 만들 때의 참고용이다.

## 시각자료 유형별 제작 절차

### 1) 시장규모 그래프 (막대 + CAGR + 추세선)
- **데이터 준비**: 최근 4~5개년 시장규모를 공신력 있는 출처(KMAPS, 통계청, 업계 보고서)에서 확보. 통화·단위(억원/조원) 통일.
- **산정/계산**: CAGR = (말년값/초년값)^(1/연수) − 1. 계산 결과를 보고서 인용치와 교차 검증(바이오에탄올 사례의 "67%" 같은 모순 방지).
- **도식화**: 연도별 막대 + 점선 추세선 + CAGR 라벨. 막대 위에 수치 라벨, 하단에 출처 각주. 결론 한 줄 캡션(예: "연 6.6% 성장하는 2,860억 시장").
- **검증**: 축 단위 표기 확인(투수 보도블록 사례의 '6.0E-02' 과학표기+단위 누락 반면교사), 출처·기준연도 병기 확인.

### 2) 비교표 (O/△/X vs 실측치)
- **데이터 준비**: 경쟁 2~3사 선정, 비교 항목 4~6개(고객의 구매 판단 요소에서 도출 — 투수 보도블록 사례는 세그먼트별 구매 기준 조사 결과를 항목으로 씀).
- **산정/계산**: O/△/X 판정 기준을 먼저 정의하고, 가능한 항목은 실측치를 병기(휨강도 △(4.0) vs O(5.0)처럼). 전 항목 자사 O는 자의성 의심을 산다(해조류 사례 p.10의 약점).
- **도식화**: 자사 행/열을 색 테두리·배경으로 강조(바이오에탄올 사례의 녹색 행, 교육키트 사례의 주황 테두리), 범례("O: 완전 가능…") 필수.
- **검증**: 모든 수치의 시점·측정 조건 통일 여부, 경쟁사 수치 출처(조달청 공시가/실측) 각주 여부.

### 3) 포지셔닝맵 (2축)
- **데이터 준비**: 고객 구매 판단 요소 중 자사가 우위이면서 **고객이 실제로 중요시하는** 2개 축 선정. 축 선정 근거를 본문에 한 줄로 명시(예: "자치구 인터뷰에서 구매 기준 1·2위가 투수 지속성과 단가").
- **산정/계산**: 각 사 좌표의 근거 데이터 확보(자사=실측/리뷰, 경쟁사=공개 스펙·리뷰). 해조류 사례 p.10은 자사 좌표를 리뷰 캡처·구매 544명과 연결해 '주장+증거' 쌍으로 만들었다.
- **도식화**: 자사를 우상단(목표 포지션)에 색 강조 배치, 경쟁사는 로고로 표기. 축 끝에 방향 라벨.
- **검증**: 축에 눈금·수치가 없으면 정성 주장에 그친다(바이오에탄올 사례 그림8의 한계). 최소한 경쟁사 좌표의 근거를 각주로.

### 4) BM 캔버스 / 구성도
- **데이터 준비**: 이해관계자 목록(공급자·생산·고객·회수), 각 관계에서 오가는 것(돈/물자/데이터)을 정리. 파트너는 실명으로(투수 보도블록 사례 p.8: 협력기관 8곳 실명+시기).
- **산정/계산**: 수익원별 단가·마진 숫자를 준비해 화살표 옆에 붙일 수 있게.
- **도식화**: 순환·양방향 구조가 핵심이면 커스텀 구성도(투수 보도블록 사례 p.4의 원료 무상 수급↔판매↔회수 순환)가 BM 캔버스보다 낫다. 표준 9블록 캔버스는 사업 전모 조망용이나 텍스트 과밀 주의(교육키트 사례 표7은 10초 파악 실패).
- **검증**: 도식의 각 노드에 실존 파트너가 대응되는지(BM 도식과 협력기관 표의 상호 참조).

### 5) 간트 / 로드맵
- **데이터 준비**: 과업 목록을 트랙(제품/사업/인증 등)으로 묶고 월 단위 기간, 마일스톤(런칭·인증·PoC), 정량 목표를 정리.
- **산정/계산**: 매출 목표·원가 계획과 연도별 정합성 확인(투수 보도블록 사례는 3개년 로드맵이 p.3 매출 목표·p.4 원가표와 정확히 맞물림).
- **도식화**: 트랙별 색 구분(해조류 사례 p.9), 마일스톤은 다이아몬드+라벨, 완료/진행/예정 상태 배지. 확정 전 일정은 "* 협의 후 확정" 각주(공공 감리 제안서 사례 p.8의 좋은 디테일).
- **검증**: 빈 바·라벨 누락 렌더링 오류 검수(공공 감리 제안서 사례 p.8의 빈 흰색 바 반면교사).

### 6) 문제-솔루션 1:1 대응 도식
- **데이터 준비**: 문제를 2~3개로 수렴시키고 각 문제의 정량 지표(규모·비용·추이)를 확보.
- **산정/계산**: 각 솔루션 요소가 해결하는 문제와 개선 폭을 수치화(투수 보도블록 사례 p.2: "50배 압축 강도", "공극 +10%").
- **도식화**: 번호 매긴 솔루션 카드 병렬 배치, 카드마다 고유 시각 형식(미니 그래프/단면도/공정사진)과 핵심 수치 1개. 해조류 사례는 문제 1(해양폐기물)+문제 2(해녀 소멸)가 '해녀와 함께 수거'라는 하나의 솔루션으로 수렴하는 복선 구조(p.3~4)를 썼다.
- **검증**: 문제 없이 등장하는 솔루션, 솔루션 없이 방치된 문제가 없는지 1:1 대응 확인.

---

---

## 도구별 제작 방법

### matplotlib (한글 폰트 설정 포함)

```python
import platform
import numpy as np
import matplotlib.pyplot as plt

if platform.system() == "Windows":
    plt.rcParams["font.family"] = "Malgun Gothic"
elif platform.system() == "Darwin":
    plt.rcParams["font.family"] = "AppleGothic"
else:
    plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

# 예시 데이터: 시장규모 추이(억원) — 실제 작성 시 수치·출처 교체
years = [2021, 2022, 2023, 2024, 2025]
size = [2210, 2355, 2510, 2675, 2860]
cagr = (size[-1] / size[0]) ** (1 / (len(years) - 1)) - 1  # CAGR 산식

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(years, size, color="#4C72B0", width=0.6)
z = np.polyfit(years, size, 1)                             # 추세선
ax.plot(years, np.poly1d(z)(years), "--", color="#C44E52",
        linewidth=2, label=f"추세선 (CAGR {cagr * 100:.1f}%)")
for b, v in zip(bars, size):                               # 막대 위 수치 라벨
    ax.text(b.get_x() + b.get_width() / 2, v + 25, f"{v:,}",
            ha="center", fontsize=10)

ax.set_title("국내 보도블록 시장 규모 추이", fontsize=14, pad=12)
ax.set_ylabel("시장 규모 (억원)")                            # 축 단위 필수 표기
ax.legend(loc="upper left")
ax.spines[["top", "right"]].set_visible(False)
fig.text(0.99, 0.01, "출처: KMAPS(2025) — 실제 출처로 교체",
         ha="right", fontsize=8, color="gray")
plt.tight_layout()
plt.savefig("market_size.png", dpi=200)
```

포인트: 축 단위를 반드시 라벨에 쓰고(투수 보도블록 사례의 '6.0E-02' 무단위 반면교사), 출처를 그림 안에 각주로 박아 그림만 복사돼도 출처가 따라가게 하라.

### 냅킨AI (Napkin AI) — 입력 텍스트 형식
냅킨AI는 구조화된 텍스트를 도식으로 변환한다. 원하는 도식 구조가 나오도록 입력을 계층·순서로 써라.

```text
# 순환 BM 구성도용 입력 예 (투수 보도블록 사례 p.4 구조)
협력 업체(폐기물 수거 기관) → 자사: 무상 원료 공급
자사 → 협력 업체: 세라믹 폐기물 문제 해결
자사 → B2B 건설사: 제품 판매
자사 → B2G 지자체: 제품 판매
B2B/B2G → 자사: 폐블록 회수 → 재생산

# 단계 로드맵용 입력 예 (상태 배지 포함)
1단계 기본 물성 검증 — KS F 4419 성능시험 (완료)
2단계 장기 투수 지속성 — 서울시 품질시험소 (진행 예정)
3단계 현장 검증 — PoC 구간 적용 (진행 중)
4단계 양산 품질 — KS 제품인증, KCL (인증 추진)
```

생성 후 수치·기관명이 누락되지 않았는지 반드시 대조하라. 도식화 과정에서 숫자가 떨어져 나가면 정성 도식(공공 감리 제안서 사례의 8개 무수치 카드)이 된다.

### 이미지 생성 AI (GPT-4o·Gemini·Nano Banana 등) — 개념 도식용 영문 프롬프트

이미지 생성 AI는 **개념 도식·일러스트(서비스 개요도, 사용 시나리오 컷, BM 순환 구성도)**에만 쓴다. 수치·축이 들어가는 그래프는 숫자를 정확히 그리지 못하므로 matplotlib로 만든다(위 절 참조). 편집 가능한 구조 도식이 필요하면 냅킨AI가 낫다.

**원칙**

1. 프롬프트는 영어로 쓴다(이미지 모델은 영어 지시 추종이 더 정확하다). 단 도식 안 텍스트·라벨은 전부 한국어로, 프롬프트에 따옴표로 그대로 지정하고 "번역·변형 금지"를 명시한다.
2. 스타일은 정부지원사업 문서 톤으로 고정한다: 플랫·미니멀 벡터, 흰 배경, 기본 1색+강조 1색(아래 PPT 도식 팁과 동일 원칙). 미국식 클립아트 인물·핸드셰이크 스톡 사진·만화 마스코트·달러 기호를 금지 항목으로 프롬프트에 적는다.
3. 생성 후 한국어 라벨을 지정 문구와 전수 대조한다. 이미지 모델은 한글 획을 자주 뭉갠다 — 깨진 라벨은 재생성하거나, 라벨 없이 생성한 뒤 PPT·이미지 편집 도구로 텍스트를 얹는다.

**프롬프트 템플릿** (대괄호를 채워 사용, 한국어 라벨은 그대로 유지)

```text
Create a clean, professional [DIAGRAM TYPE — e.g., circular business-model flow diagram / service overview diagram / 3-step process illustration] for a formal Korean government startup grant application document (사업계획서).

Structure:
- [Describe layout and elements: e.g., three boxes connected in a cycle by labeled arrows, with the company box at the center]

All text labels inside the image MUST be written in Korean, exactly as specified below — do not translate, romanize, or alter them:
- [Element 1]: "한국어 라벨 1"
- [Element 2]: "한국어 라벨 2"
- [Arrow / caption]: "한국어 라벨 3"

Style:
- Flat, minimal vector infographic; white background; base text color [SELECTED_THEME_TEXT_HEX] plus accent [SELECTED_THEME_PRIMARY_HEX] only
- Select colors from the confirmed brand or item-specific design theme; do not default every business to navy or blue
- Preserve the supplied structure, labels, order, hierarchy and arrow directions exactly; use references only for spacing, visual grouping and emphasis
- Calm, neutral, document-friendly tone appropriate for an official Korean business plan — not flashy, not cartoonish
- Do NOT use American/Western stock-imagery cliches: no clip-art office workers, no handshake photos, no cartoon mascots, no dollar-sign icons
- No photorealistic people; if human figures are needed, use simple abstract pictograms in a Korean business context
- Generous white space; labels large enough to remain legible when printed on A4

Format: 16:9, high resolution, plain background without decorative frames.
```

**작성 예시** — 순환 BM 구성도(투수 보도블록 사례 p.4 구조): Structure에 "three entities in a circular flow", 라벨에 `"협력 업체 (폐기물 수거 기관)"`, `"자사 (제품 생산)"`, `"B2B/B2G 고객"`, 화살표 라벨 `"무상 원료 공급"`, `"제품 판매"`, `"폐블록 회수"`를 지정한다.

**검수 체크**: ① 모든 한국어 라벨이 지정 문구와 정확히 일치하는가(오타·누락·획 뭉개짐) ② 라벨에 숫자를 넣었다면 정확한가(의심되면 숫자는 라벨에서 빼고 본문·캡션으로) ③ 스타일이 문서의 다른 도식과 이질적이지 않은가(기본 1색+강조 1색 유지).

### 마크다운 표 → 한글(HWP)/워드 이관
1. 표를 마크다운으로 먼저 작성(버전 관리·검산 용이).
2. 문서 전체를 옮길 때는 `bizplan/scripts/md_to_hwpx.py`(한글 .hwpx/.hwp, 표 테두리·개조식) 또는 `md_to_docx.py`(A4·표 테두리 .docx)로 변환한 뒤 연다. 표 몇 개만 옮길 때는 VS Code 미리보기·브라우저에서 렌더한 표를 드래그 복사해 한글/워드에 '표'로 붙여넣는다.
3. 옮기기 전 `bizplan/scripts/check_tables.py`로 합계·비율을 검산하고, 이관 후 필수 검수: 셀 줄바꿈 깨짐, 숫자 천 단위 콤마, **빈 셀 잔존 여부**(교육키트 사례의 '빈 표' 오독, 공공 감리 제안서 사례의 빈 카드 참사 방지).
4. 표를 이미지로 캡처해 붙이지 마라 — 교육키트 사례는 표 9개를 이미지로 넣어 검색·복사·검증이 전부 불가능해졌다.

### PPT 도식 팁
- SmartArt 자동 도식보다 도형+정렬 가이드로 직접 그려라. 번호 카드+상태 배지 문법(투수 보도블록 사례)을 템플릿화해 문서 전체에 재사용하면 일관성이 생긴다.
- 색은 기본 1색+강조 1색으로 제한하고, 강조색은 '차별화 요소'에만 쓴다(공공 감리 제안서 사례 p.6: 표준 점검=네이비, AI 특화 점검=오렌지로 분리한 문법이 모범).
- 카드에는 '한글 제목+영문 부제+태그 칩' 3층 구조(공공 감리 제안서 사례 p.4)로 훑는 심사자와 정독자 모두에게 독해 경로를 제공.
- 완성 후 PDF로 내보내 최종 렌더를 검수하라 — 슬라이드 번호 중복·점프(공공 감리 제안서 사례 02·02·04·07), 빈 간트 바(같은 사례 p.8) 같은 결함은 렌더에서만 보인다.
- 다른 자료를 재촬영·캡처해 넣지 마라. 판독 불가 이미지는 증거가 아니라 지면 채우기다(투수 보도블록 사례 p.6 샌드박스 캡처).

---
