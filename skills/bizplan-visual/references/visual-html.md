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
- 형식을 보여 주려고 임의 숫자를 쓴 그림은 `kicker`에 '(예시 형식)'을 붙이고 `note`에 교체 시점을 적는다.

## 2. 설계 규칙

1. **말하려는 것 → 형식.** 주제가 아니라 그림이 증명할 관계로 유형을 고른다(3절 표, 관계 유형은 `info-patterns.md`).
2. **강조는 하나.** 우리(`ours`)·도입 후·목표 칸만 강조색, 나머지는 회색. 강조가 둘이면 아무것도 강조되지 않는다.
3. **축은 하나.** 단위가 다른 값을 한 그림에 겹치지 않는다(이중 축 금지). 손익은 같은 단위라 한 축에 둔다.
4. **값은 그림 위에 직접.** 범례를 찾아 오가지 않게 막대 끝·점 옆에 값을 쓴다. 모든 점에 숫자를 달지는 않는다(처음·끝·최고·최저·변곡점).
5. **글자는 잉크색.** 값·라벨은 검정·회색 글자로 쓰고, 색은 표식(점·막대)에만 쓴다.
6. **불리한 것도 보인다.** 비교표에는 우리가 불리한 행(`disadvantage`)을 1개 이상 둔다. 포지셔닝 맵에는 대체재(고객의 현재 방법)를 넣는다.
7. **합계는 그림이 검산한다.** 채널별 매출·사업비·표의 합계 행은 렌더러가 더해 보고 목표·상한과 다르면 그림과 경고에 표시한다.
8. **장식 금지.** 3D·그림자·그라데이션·아이콘 남용을 하지 않는다. 남는 공간은 비워 둔다.

## 3. 유형 (33종)

| 말하려는 것 | `type` | 핵심 필드 | 관계 |
|-------------|--------|-----------|------|
| **시장 · 고객** | | | |
| 큰 시장 안에서 우리가 처음 닿을 곳은 여기다 | `tam` | `layers[{label, value, name, formula, basis}]` 바깥→안쪽 3~4층 | R9 |
| 여러 세분 시장 중 여기를 고른 이유 | `segments` | `rows[{name, size, size_label, growth, note, chosen}]` | R7 |
| 돈 내는 사람과 쓰는 사람이 누구인가 | `persona` | `cards[{name, size, def, tags[], scene, pains[{text, hypothesis}], verified}]` 1~2장 | R21 |
| 고객이 가장 불편한 단계는 여기다 | `survey` | `question`, `n`, `options[{label, value}]`, `highlight` | R7 |
| 고객의 말(실제 발언만) | `quotes` | `items[{text, who, source, date, pending}]` | R22 |
| 지금 고객은 이렇게 버틴다(구성비) | `donut` | `parts[{label, value}]` 5조각 이하, `highlight`, `center` | R8 |
| **문제 · 해결 · 근거** | | | |
| 문제가 커지고 있다(추이) | `trend` | `labels`, `values`, `unit`, `forecast_from`, `cagr` | R6 |
| 문제 n을 기능 n이 푼다 | `ps_map` | `rows[{no, problem, evidence, solution, benefit}]` | R19 |
| 현장·실물이 있다(사진 격자) | `photos` | `items[{src \| what, caption, date, place, badge}]`, `cols` | R22 |
| 이렇게 쓴다(화면 ①②③) | `screens` | `screens[{no, title, desc, src \| ui{title, rows, highlight, button}}]` | R13·R22 |
| 서비스·공정이 이렇게 돈다 | `flow` | `steps[{title, sub, who, ours}]`, `loop`, `loop_label` | R13 |
| **차별** | | | |
| 우리만 다르다(그리고 불리한 것도 있다) | `compare` | `entities`, `rows[{label, cells[[●◐○, 설명]], disadvantage}]`, `verify` | R10 |
| 아무도 없는 칸을 우리가 차지한다 | `positioning` | `x_axis/y_axis{label, low, high}`, `points[{name, x, y, ours, kind}]`, `quadrant` | R12 |
| 두 시장이 겹치는 자리 | `venn` | `sets[{label, items[]}]` 2~3개, `center`, `center_note` | R4 |
| 같은 지표에서 우리가 이만큼 낫다 | `bar` | `items[{label, value, ours}]`, `unit` | R7 |
| 쓰고 나니 이만큼 줄었다(늘었다) | `before_after` | `metrics[{label, before, after, unit, better}]` | R11 |
| **돈** | | | |
| 누가 누구에게 무엇을 주고 얼마를 내는가 | `bm` | 4절 | R4·R13 |
| 사업 모델 전체를 한 장에 | `bmc` | `blocks{kp, ka, kr, vp, cr, ch, cs, cost, rev}`, `highlight` | R20 |
| 한 건 팔면 이만큼 남는다 | `waterfall` | `start{label, value}`, `steps[{label, value(−)}]`, `end_label` | R6 |
| 채널별로 이만큼 벌어 목표가 된다 | `revenue_mix` | `channels[{name, formula, amount}]`, `target` | R7 |
| 지원금을 이렇게 쓴다 | `budget` | `items[{name, basis, amount}]`, `cap` | R8·R16 |
| n년 차에 흑자로 돌아선다 | `pnl` | `periods`, `revenue`, `cost`, `profit` | R6 |
| 월별로 매출이 이렇게 붙는다 | `columns` | `labels`, `values`, `notes[{at, text}]`, `target`, `highlight` | R6 |
| 협약 기간에 매출·투자·고용 | `kpi` | `tiles[{label, value, basis, status}]` | R5 |
| **실행 · 팀** | | | |
| 모집단에서 첫 유료 고객까지 | `funnel` | `stages[{name, count, level}]` | R13 |
| 무엇을 언제 끝내는가 | `gantt` | `periods`, `tasks[{name, start, length, status, out}]`, `milestones` | R15 |
| 이 과업이 이 성과로 이어진다 | `roadmap` | `periods`, `rows[{axis, cells}]`, `kpi` (`★` = 변곡점) | R15 |
| 단계별로 키운다(1→2→3년 차) | `stairs` | `steps[{period, title, items[], kpi}]` | R14 |
| 여기까지 왔고 다음은 이것 | `timeline` | `events[{date, title, desc, status}]` | R14 |
| 약점을 이렇게 메운다 | `swot` | `s·w·o·t`, `strategies{SO, WO, ST, WT}`, `focus` | R18 |
| 누가 무엇을 맡고 빈 곳은 언제 채우나 | `team` | `members[{role, name, duty, skills, status}]`, `plan[{gap, how, when, budget}]` | R21 |
| 협력처가 어느 단계까지 왔나 | `partners` | `rows[{name, ability, role, when, stage}]` (접촉→협의→LOI→MOU→실적) | R21 |
| 숫자 표(3년 표·인력 표 등) | `table` | `columns`, `rows`, `highlight_col`, `highlight_row`, `total` | R16 |

- `{"type": "chapter", "title": "1. 문제 인식"}`은 미리보기 쪽의 장 구분이다(그림이 아니라 PNG를 만들지 않는다).
- 사진·화면이 아직 없으면 `src` 대신 `what`에 무엇을 찍을지 쓴다. 점선 자리로 보인다. `src`는 spec 파일 기준 경로이고, HTML 안에 그대로 넣어 한 파일로 들고 다닌다.
- `screens`의 `ui`는 캡처 전 화면 틀이다. MVP가 나오면 `src`로 바꾼다.

## 4. BM 구조도 그리는 법 (`bm`)

**한 장에 보여 줄 것**: 누가(주체) · 무엇을 받고(가치) · 얼마를 내는가(돈) · 그 돈이 연 매출로 어떻게 커지는가(산식).

```json
{"type": "bm", "headline": "운영사는 행사당, 사진관은 월 구독으로 내고 — 촬영자는 무료로 쓴다",
 "actors": [{"name": "필터픽", "role": "앱 + 부스 SW", "ours": true},
            {"name": "촬영자", "role": "무료 사용자"},
            {"name": "행사 운영사", "role": "1차 고객", "payer": true},
            {"name": "장비 렌탈사", "role": "파트너"}],
 "flows": [{"from": "행사 운영사", "to": "필터픽", "kind": "money", "label": "행사당 ○○만 원"},
           {"from": "필터픽", "to": "행사 운영사", "kind": "value", "label": "차별화된 부스"},
           {"from": "장비 렌탈사", "to": "필터픽", "kind": "goods", "label": "아이패드·거치대"}],
 "formula": {"title": "연 매출", "terms": [{"label": "운영사", "value": "○○곳"}, "×", {"label": "행사당", "value": "○○만 원"}],
             "result": {"label": "1년 차 목표", "value": "○○만 원"}},
 "streams": [{"name": "행사 부스 이용료", "how": "행사 1건 단위", "share": "1년 차 주력"}]}
```

- **배치**: 주체가 3개 이하면 한 줄(왼쪽 → 가운데 → 오른쪽), 4개 이상이면 우리를 가운데 둔 허브로 자동 배치한다. 원하는 자리가 있으면 `pos`(left · right · top · bottom · top-left …)로 정한다.
- **흐름 세 가지**: 돈(`money`)은 굵은 실선 + 금액 칩, 가치·서비스(`value`)는 점선, 물건·데이터(`goods`)는 가는 실선이다. 오가는 두 흐름은 같은 두 주체 사이에서 양쪽으로 갈라 그린다.
- **결제자 표시**: 돈을 내는 주체에 `payer: true` → 상자 위에 '결제자' 표시가 붙는다. 사용자 ≠ 결제자인 모델에서 꼭 쓴다.
- **산식 띠**(`formula`): 그림 아래에 `항 × 항 = 결과`로 둔다. 같은 값이 숫자 등록부·3지표·채널별 매출과 같아야 한다.
- **수익원**(`streams`): 수익원이 2개 이상이면 언제부터 · 얼마나 차지하는지 함께 쓴다.
- 금액을 모르면 칩에 `○○만 원`을 그대로 둔다. 화살표만 있고 금액이 없는 BM은 "어떻게 버는지 모른다"로 읽힌다.

## 5. 사업계획서 목차별 시각자료 지도

사업계획서는 절마다 증명할 것이 정해져 있고, 그에 맞는 그림이 있다. 기본 목차(섹션 설계도 4-1) 기준이다. **굵은 것이 그 절의 기본 그림**이고 나머지는 자료가 있을 때 더한다.

| 절 | 증명할 것 | 그림 |
|----|-----------|------|
| 개요(요약) | 무엇을 · 누구에게 · 어떻게 버는가를 한눈에 | **`screens`(핵심 화면 ①②③)**, **`flow` 또는 `bm`(서비스 구조)**, 실물 사진(`photos`) |
| 1-1 창업 배경 | 대표가 직접 겪은 장면 + 외부에서도 커지는 문제 | **`photos`(현장·활동)**, **`trend`(문제 규모 추이)**, `quotes`(언론·커뮤니티 원문) |
| 1-2 문제와 필요성 | 문제의 빈도·손실과 지금의 대처 | **`survey` 또는 `donut`(1차 조사)**, `quotes`(고객 발언), **`ps_map`(문제 n → 해결 n)** |
| 1-3 시장·목표 고객 | 결제자 기준 시장과 첫 고객 수 | **`tam`(층별 산식)**, `segments`(세분 시장 중 고른 곳), **`persona`(결제자·사용자)** |
| 2-1 준비 정도·개발 계획 | 이미 한 것 · 하는 중 · 할 것 | **`timeline`(준비 경과)**, **`gantt`(추진 일정)**, `photos`(실물 증빙, 별첨 번호), `before_after`(시범 결과) |
| 2-2 차별성 | 실명 비교와 비어 있는 자리 | **`compare`(확인 경로 열)**, **`positioning`**, `venn`, `bar`(성능·비용 실측) |
| 2-3 사업비 | 비목 · 산출 근거 · 상한 | **`budget`** |
| 3-1 비즈니스 모델 | 돈의 흐름과 매출 산식 | **`bm`(산식 띠 포함)**, `bmc`(양식이 요구할 때), `waterfall`(단위 경제성) |
| 3-2 목표시장 진입 | 첫 고객까지의 경로 | **`funnel`**, **`revenue_mix`(채널별 기대 매출)** |
| 3-3 매출·투자·고용 | 협약 기간 3지표와 이후 3년 | **`kpi`**, `columns`(월별 목표 매출 + 마일스톤), **`pnl`**, `table`(3년 표) |
| 3-4 로드맵·중장기 | 과업 → 성과의 인과, 단계별 확장 | **`roadmap` 또는 `stairs`**, `swot`(전략 하나를 고른) |
| 4-1·4-2 대표자·팀 | 역할 · 상태 · 빈 곳을 채울 계획 | **`team`(보완 계획 포함)** |
| 4-3 협력·인프라 | 협력처의 단계와 시기 | **`partners`**, `photos`(시설) |

- 문서형 10쪽이면 그림 12~16개다(섹션 설계도 3-2). 위 표의 굵은 것만 써도 15개 안팎이 된다.
- 같은 숫자가 여러 그림에 나오면(협약 기간 매출 → `kpi`·`revenue_mix`·`columns`·`bm` 산식) 숫자 등록부의 한 값을 쓴다.
- 예시 spec: `python3 -B html_visuals.py --sample 예시.json` — 위 목차 순서대로 34개 그림이 들어 있다.

## 6. 만드는 법

```bash
python3 -B html_visuals.py --sample 예시.json                       # 목차순 예시 spec(33종)
python3 -B html_visuals.py 시각자료.json --out 시각자료/              # 문서용(폭 1120px)
python3 -B html_visuals.py 시각자료.json --out 시각자료/발표 --slide   # 발표용 16:9(넘치면 장에 맞춰 줄인다)
python3 -B html_visuals.py 시각자료.json --theme <bizplan-slides>/assets/themes/report-blue.json
```

- 결과: `visuals.html`(모두 한 장에, 장 구분 포함 — 브라우저로 열어 확인) + `<id>.png`(2배 해상도). PNG는 Node + Playwright가 있을 때 `html_shot.cjs`가 찍는다. 없으면 HTML을 브라우저로 열어 캡처한다.
- 강조색: 기본 `#2a78d6`. `--accent 0B3D91` 또는 `--theme`(테마의 `colors.primary`)로 발표 템플릿과 맞춘다.
- 글꼴: Pretendard → Apple SD Gothic Neo → Noto Sans KR → 맑은 고딕 순으로 찾는다.
- 본문에는 `![결론 문장](시각자료/<id>.png)`로 넣는다. 그림 안 제목이 결론이므로 본문 캡션 줄에 같은 문장을 반복하지 않는다.
- 만든 뒤 PNG를 직접 열어 겹침·잘림을 본다. 렌더러 경고(`[확인]`)는 고치거나 이유를 남긴다: 출처 없음, 강조 대상 없음, 불리한 축 없음, 제목 성장률 ≠ 계산 CAGR, 영업이익 ≠ 매출 − 비용, 채널 합 ≠ 목표, 비목 합 ≠ 상한, 단일 선택 응답 합 ≠ 100%, 표 합계 행 불일치, 이미지 파일 없음.
