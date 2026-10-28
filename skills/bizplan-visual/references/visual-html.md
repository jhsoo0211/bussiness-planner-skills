# HTML 시각자료 — 의도가 먼저 보이는 그림

> `scripts/html_visuals.py`의 사용법과 설계 규칙. 시각자료는 HTML(인라인 SVG)로 만들고 PNG로 찍어 문서·슬라이드에 넣는다. matplotlib 템플릿(`chart_templates.py`)은 Node·Playwright가 없을 때 쓰는 대체 경로다.

## 1. 한 장의 틀

모든 시각자료는 같은 틀을 쓴다. 이 틀 덕분에 **보는 사람이 그림을 해석하기 전에 무엇을 말하는지부터 읽는다.**

| 자리 | 필드 | 쓰는 법 |
|------|------|---------|
| 위 작은 글 | `kicker` | 어느 절의 그림인지(예: `1-3 · 목표 고객`). 생략할 수 있다 |
| 제목 | `headline` (필수) | **결론 문장.** "시장 규모"가 아니라 "첫 고객은 ○○ 지역 행사 운영사 ○○곳이다". 숫자를 하나 넣는다 |
| 제목 아래 | `sub` | 읽는 법 한 줄(축의 뜻, 범위). 필요할 때만 |
| 본문 | 유형별 필드 | 아래 3절 |
| 강조 띠 | `takeaway` | "그래서 무엇을 한다" 한 문장. 제목을 반복하지 않는다 |
| 맨 아래 | `note` (권장) | 출처 · 시점 · 표본. 없으면 렌더러가 경고한다 |

- 미확보 값은 `○○`로 쓴다. 점선 밑줄로 표시돼 빈칸이 보인다. 그럴듯한 숫자로 채우지 않는다.
- 근거 수준 칩: TAM 층·퍼널 단계에 `basis`/`level`로 `확인`·`산출`·`관찰`·`가정`을 붙인다(섹션 설계도 1-7). `가정`은 점선 칩으로 보인다.

## 2. 설계 규칙

1. **말하려는 것 → 형식.** 주제가 아니라 그림이 증명할 관계로 유형을 고른다(3절 표, 관계 유형은 `info-patterns.md`).
2. **강조는 하나.** 우리(`ours`)·도입 후·목표 칸만 강조색, 나머지는 회색. 강조가 둘이면 아무것도 강조되지 않는다.
3. **축은 하나.** 단위가 다른 값을 한 그림에 겹치지 않는다(이중 축 금지). 손익은 같은 단위라 한 축에 둔다.
4. **값은 그림 위에 직접.** 범례를 찾아 오가지 않게 막대 끝·점 옆에 값을 쓴다. 모든 점에 숫자를 달지는 않는다(처음·끝·변곡점).
5. **글자는 잉크색.** 값·라벨은 검정·회색 글자로 쓰고, 색은 표식(점·막대)에만 쓴다.
6. **불리한 것도 보인다.** 비교표에는 우리가 불리한 행(`disadvantage`)을 1개 이상 둔다. 포지셔닝 맵에는 대체재(고객의 현재 방법)를 넣는다.
7. **장식 금지.** 3D·그림자·그라데이션·아이콘 남용을 하지 않는다. 남는 공간은 비워 둔다.

## 3. 유형

| 말하려는 것 | `type` | 핵심 필드 | 관계 |
|-------------|--------|-----------|------|
| 큰 시장 안에서 우리가 처음 닿을 곳은 여기다 | `tam` | `layers[{label, value, name, formula, basis}]` 바깥→안쪽 3~4층 | R9 |
| 아무도 없는 칸을 우리가 차지한다 | `positioning` | `x_axis/y_axis{label, low, high}`, `points[{name, x, y(0~10), ours, kind:'substitute'}]`, `quadrant{x, y, label}` | R12 |
| 약점을 이렇게 메운다 | `swot` | `s·w·o·t` 목록, `strategies{SO, WO, ST, WT}`, `focus` | R18 |
| 우리만 다르다(그리고 불리한 것도 있다) | `compare` | `entities[{name, ours, substitute}]`, `rows[{label, cells[[●◐○, 설명]], disadvantage}]`, `verify` | R10 |
| 같은 지표에서 우리가 이만큼 낫다 | `bar` | `items[{label, value, ours}]`, `unit` | R7 |
| 쓰고 나니 이만큼 줄었다(늘었다) | `before_after` | `metrics[{label, before, after, unit, better}]`, `labels` | R11 |
| 시장이 이 속도로 커진다 | `trend` | `labels`(연도), `values`, `unit`, `forecast_from`, `cagr`(생략 시 계산) | R6 |
| 모집단에서 첫 유료 고객까지 이렇게 좁힌다 | `funnel` | `stages[{name, count, level}]`, `unit` | R13 |
| n년 차에 흑자로 돌아선다 | `pnl` | `periods`, `revenue`, `cost`, `profit`(생략 시 매출−비용), `unit` | R6 |
| 누가 누구에게 얼마를 내는가 | `bm` | `actors[{name, role, ours}]` 3개 이내, `flows[{from, to, kind:'money'·'value', label}]`, `partner` | R4·R13 |
| 협약 기간에 이것을 만든다(매출·투자·고용) | `kpi` | `tiles[{label, value, basis, status}]` | R5 |
| 무엇을 언제 끝내는가 | `gantt` | `periods`, `tasks[{name, start, length, status, out}]`, `milestones[{label, at}]` | R15 |
| 이 과업이 이 성과로 이어진다 | `roadmap` | `periods`, `rows[{axis, cells}]`, `kpi`; `★`로 시작하는 칸 = 변곡점 | R15 |
| 문제 n을 기능 n이 푼다 | `ps_map` | `rows[{no, problem, evidence, solution, benefit}]` | R19 |

- **TAM**: TAM은 시장 전체 지출, SOM과 1차 층은 우리 몫이다. 층마다 값 · 정의 · 산식 · 근거 수준을 한 줄에 둔다(`visual-tam.md`). 값이 없으면 `○○`로 두고 산식만 쓴다.
- **포지셔닝**: 축 이름보다 **양 끝 설명**(`low`·`high`)이 중요하다. 비어 있는 칸을 `quadrant`로 칠하고 이름을 붙인다. 좌표 근거는 `note`에 쓴다.
- **SWOT**: 네 칸만 있으면 정리일 뿐이다. 전략 4개 중 하나를 `focus`로 골라 결론을 낸다.
- **퍼널**: 단계 사이 구간 전환율을 자동으로 쓴다(1% 아래는 0.16%처럼 유효숫자 2자리). 첫 단계만 `확인`, 접촉 이후는 `관찰`, 아직 없는 단계는 `가정`.
- **손익**: 영업이익을 따로 주면 `매출 − 비용`과 대조해 다르면 경고한다. 첫 흑자 해에 ★.
- **추이**: `forecast_from` 이후는 점선·빈 점으로 실측과 갈린다. 제목에 적은 성장률이 값으로 계산한 CAGR과 다르면 경고한다.
- **BM**: 돈은 실선(금액 칩), 가치는 점선. 화살표마다 무엇이 오가는지 쓴다. 주체가 4개를 넘으면 그림을 나눈다.

## 4. 만드는 법

```bash
python3 -B html_visuals.py --sample 예시.json                       # 14개 유형 예시 spec
python3 -B html_visuals.py 시각자료.json --out 시각자료/              # 문서용(폭 1120px)
python3 -B html_visuals.py 시각자료.json --out 시각자료/발표 --slide   # 발표용 16:9
python3 -B html_visuals.py 시각자료.json --theme <bizplan-slides>/assets/themes/report-blue.json
```

- 결과: `visuals.html`(모두 한 장에, 브라우저로 열어 확인) + `<id>.png`(2배 해상도). PNG는 Node + Playwright가 있을 때 `html_shot.cjs`가 찍는다. 없으면 HTML을 브라우저로 열어 캡처한다.
- 강조색: 기본 `#2a78d6`. `--accent 0B3D91` 또는 `--theme`(테마의 `colors.primary`)로 발표 템플릿과 맞춘다.
- 글꼴: Pretendard → Apple SD Gothic Neo → Noto Sans KR → 맑은 고딕 순으로 찾는다.
- 본문에는 `![결론 문장](시각자료/<id>.png)`로 넣는다. 캡션 대신 그림 안 제목이 결론이므로, 본문 캡션 줄에는 출처만 반복하지 않는다.
- 만든 뒤 PNG를 직접 열어 겹침·잘림을 본다. 렌더러 경고(`[확인]`)는 고치거나 이유를 남긴다.
