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
| 누가 누구와 무엇을 주고받는가(사용료 ↔ 서비스) | `bm` | 4절 | R4·R13 |
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

**BM 구조도는 '누가 누구와 무엇을 주고받는가'를 보이는 그림이다.** 화살표마다 오가는 것의 이름을 쓴다: 우리가 주는 것(서비스 · SW · 데이터 · 장비)과 받는 것(사용료 · 구독료 · 수수료 · 데이터). 금액은 그림에 쓰지 않는다. 금액은 3-1 본문의 매출 산식과 3-2 채널별 기대 매출(`revenue_mix`)에 둔다.

```json
{"type": "bm", "headline": "운영사는 부스 사용료를, 사진관은 SW 구독료를 낸다 — 촬영자는 무료로 쓰고 선택 이력을 남긴다",
 "actors": [{"name": "필터픽", "role": "앱 + 부스 SW", "ours": true},
            {"name": "촬영자", "role": "무료 사용자"},
            {"name": "행사 운영사", "role": "1차 고객", "payer": true},
            {"name": "장비 렌탈사", "role": "파트너"}],
 "flows": [{"from": "필터픽", "to": "촬영자", "kind": "value", "label": "필터 추천 서비스", "detail": "무료"},
           {"from": "촬영자", "to": "필터픽", "kind": "goods", "label": "선택 이력 데이터"},
           {"from": "행사 운영사", "to": "필터픽", "kind": "money", "label": "부스 사용료", "detail": "행사 1건마다"},
           {"from": "필터픽", "to": "행사 운영사", "kind": "value", "label": "부스 운영 서비스"},
           {"from": "장비 렌탈사", "to": "필터픽", "kind": "goods", "label": "아이패드·거치대"},
           {"from": "필터픽", "to": "장비 렌탈사", "kind": "money", "label": "장비 렌탈료"}],
 "streams": [{"name": "부스 사용료", "how": "행사 운영사가 행사 1건마다 낸다", "share": "1년 차 주력"}]}
```

- **짝으로 쓴다**: 두 주체 사이에는 보통 '주는 것 ↔ 받는 것'이 한 쌍이다(부스 운영 서비스 ↔ 부스 사용료). 한쪽만 있으면 왜 주는지(무료 사용자가 남기는 데이터 등)가 빠진 것이다.
- **흐름 세 가지**: 돈(`money` — 사용료·구독료·수수료)은 실선, 서비스·가치(`value`)는 점선, 물건·데이터(`goods`)는 가는 실선이다. 칩은 모두 같은 크기로 쓰고, 돈 칩만 옅은 강조색 바탕으로 구분한다.
- **언제 · 어떻게**(`detail`): 과금 단위나 조건이 중요하면 칩 뒤에 작게 붙인다(행사 1건마다 · 월 정액 · 무료 · 성사 시). 숫자 금액은 쓰지 않는다 — 쓰면 렌더러가 경고한다.
- **결제자 표시**: 돈을 내는 주체에 `payer: true` → 상자 위에 '결제자' 표시가 붙는다. 사용자 ≠ 결제자인 모델에서 꼭 쓴다.
- **배치**: 주체가 3개 이하면 한 줄(왼쪽 → 가운데 → 오른쪽), 4개 이상이면 우리를 가운데 둔 허브로 자동 배치한다. 원하는 자리가 있으면 `pos`(left · right · top · bottom · top-left …)로 정한다. 6개를 넘으면 그림을 나눈다.
- **수익원**(`streams`): 무엇에 대해 누가 내는지와 언제부터 주력인지를 쓴다.
- **산식 띠**(`formula`)는 선택이다. 양식이 BM 칸 하나에 매출 근거까지 요구할 때만 그림 아래에 붙이고, 같은 값이 숫자 등록부·3지표·채널별 매출과 같아야 한다.
- 이름 없는 화살표는 쓰지 않는다. "무엇이 오가는지 모르는 BM"으로 읽힌다.

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
| 3-1 비즈니스 모델 | 누가 누구와 무엇을 주고받는가 | **`bm`(주고받는 것 · 결제자)**, `bmc`(양식이 요구할 때), `waterfall`(단위 경제성). 매출 산식은 본문 한 줄 |
| 3-2 목표시장 진입 | 첫 고객까지의 경로 | **`funnel`**, **`revenue_mix`(채널별 기대 매출)** |
| 3-3 매출·투자·고용 | 협약 기간 3지표와 이후 3년 | **`kpi`**, `columns`(월별 목표 매출 + 마일스톤), **`pnl`**, `table`(3년 표) |
| 3-4 로드맵·중장기 | 과업 → 성과의 인과, 단계별 확장 | **`roadmap` 또는 `stairs`**, `swot`(전략 하나를 고른) |
| 4-1·4-2 대표자·팀 | 역할 · 상태 · 빈 곳을 채울 계획 | **`team`(보완 계획 포함)** |
| 4-3 협력·인프라 | 협력처의 단계와 시기 | **`partners`**, `photos`(시설) |

- 문서형 10쪽이면 그림 12~16개다(섹션 설계도 3-2). 위 표의 굵은 것만 써도 15개 안팎이 된다.
- 같은 숫자가 여러 그림에 나오면(협약 기간 매출 → `kpi`·`revenue_mix`·`columns`) 숫자 등록부의 한 값을 쓴다.
- 예시 spec: `python3 -B html_visuals.py --sample 예시.json` — 위 목차 순서대로 34개 그림이 들어 있다.

## 6. 만드는 법

```bash
python3 -B html_visuals.py --sample 예시.json                       # 목차순 예시 spec(33종)
python3 -B html_visuals.py 시각자료.json --out 시각자료/ --print      # 사업계획서(docx·hwpx·PDF)에 넣을 그림 — 이것을 쓴다
python3 -B html_visuals.py 시각자료.json --out 시각자료/발표 --slide   # 발표용 16:9(넘치면 장에 맞춰 줄인다)
python3 -B html_visuals.py 시각자료.json --out 시각자료/화면           # 화면 보기용(폭 1120px)
python3 -B html_visuals.py 시각자료.json --print --theme <bizplan-slides>/assets/themes/report-blue.json
```

- 결과: `visuals.html`(모두 한 장에, 장 구분 포함 — 브라우저로 열어 확인) + `<id>.png`(2배 해상도). PNG는 Node + Playwright가 있을 때 `html_shot.cjs`가 찍는다. 없으면 HTML을 브라우저로 열어 캡처한다.
- **문서에 넣는 그림은 `--print`로 만든다.** 화면 보기용(폭 1120px)을 A4 본문 폭 170mm에 넣으면 가장 작은 글자가 4.7~5.2pt로 줄어 인쇄 심사본에서 읽히지 않는다. `--print`는 폭 860px에 SVG 글자를 1.3배(최소 13px)로, HTML 글자를 1.15배로 키우고 장식(머리 꼬리표)을 빼서 170mm 폭에서 가장 작은 글자가 7.4pt 이상이 되게 한다. 페르소나 2장은 나란히, 간트·로드맵 행은 촘촘히, 그린 화면 틀은 낮게 놓아 그림 높이도 줄인다.
- 그림 높이는 170mm 폭 기준 120mm 이하가 되게 한다(`md_to_docx.py`·`md_to_hwpx.py`가 이보다 크면 줄이고, 그만큼 글자도 작아진다). 넘치는 그림은 항목·행 수를 줄이거나 두 그림으로 나눈다.
- 문서 변환: `md_to_docx.py 사업계획서.md 사업계획서.docx --gov-bullets` → `export_pdf.py 사업계획서.docx` → `preview.py 사업계획서.pdf`로 쪽마다 연다. 변환기는 그림 alt 글을 캡션으로 다시 달지 않고(`--captions`로 켠다), 그림·표 바로 앞 문단(헤드라인·표 제목)을 같은 쪽에 묶고, 표 행이 두 쪽에 갈라지지 않게 한다. 확인할 것: 헤드라인만 쪽 끝에 남았는지, 그림이 넘어가며 생긴 빈 공간, 표 칸에서 낱말이 한 글자씩 끊기는지, 그림 숫자 = 숫자 등록부 = 본문 헤드라인, 쪽 수와 그림 수(브리프 16절 이미지 예산).
- 강조색: 기본 `#2a78d6`. `--accent 0B3D91` 또는 `--theme`(테마의 `colors.primary`)로 발표 템플릿과 맞춘다.
- 글꼴: Pretendard → Apple SD Gothic Neo → Noto Sans KR → 맑은 고딕 순으로 찾는다.
- 본문에는 `![결론 문장](시각자료/<id>.png)`로 넣는다. 그림 안 제목이 결론이므로 본문 캡션 줄에 같은 문장을 반복하지 않는다.
- 만든 뒤 PNG를 직접 열어 겹침·잘림을 본다. 렌더러 경고(`[확인]`)는 고치거나 이유를 남긴다: 출처 없음, 강조 대상 없음, 불리한 축 없음, 제목 성장률 ≠ 계산 CAGR, 영업이익 ≠ 매출 − 비용, 채널 합 ≠ 목표, 비목 합 ≠ 상한, 단일 선택 응답 합 ≠ 100%, 표 합계 행 불일치, 이미지 파일 없음, BM 화살표에 금액, 이름 없는 BM 화살표.
