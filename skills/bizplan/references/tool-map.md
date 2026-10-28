# 도구 지도 — 환경에 있는 스킬을 하나의 기준으로 쓰기

bizplan 스킬이 작업 중에 **다른 스킬·도구를 부를 때 보는 단일 기준표**다. 각 스킬 본문에 연동 문장을 흩어 두지 않고, 여기 한 곳에서 정한다.

## 규칙

1. 작업을 시작할 때 아래 표에서 그 작업 행을 찾는다.
2. '있으면 부를 스킬'이 **지금 환경의 스킬 목록**에 있으면 그 스킬로 하위 작업을 맡긴다.
   - 결과는 bizplan 형식(출처 표 · 근거 라벨 · 숫자 등록부)으로 받아 옮긴다.
   - 목록이 안 보이는 환경(Codex·로컬 설치)에서는 `bizplan/scripts/find_tools.py`로 확인한다.
   - **기준은 bizplan 절차다.** 다른 스킬이 주는 구조(인터뷰 길이·단계, 카드 형식 등)가 '없으면' 칸의 절차와 다르면 그 절차를 따르고, 다른 스킬은 그 안의 하위 작업(질문 문장 다듬기, 모집 문구, 표 채우기)에만 쓴다.
   - 행에 적힌 **조건**(커넥터, 수주·실주 기록 같은 입력 자료)이 없으면 부르지 않는다.
3. 없거나 실패하면 **'없으면'** 칸의 내장 절차로 한다. 실패는 숨기지 않고 한 줄로 알린다. 스킬 목록에 있어도 연결(MCP 등)이 실패하면 한 번만 시도하고 넘어간다.
4. 사내 커넥터(CRM·메일·통화 기록·사내 문서)가 필요한 기능은 커넥터가 연결됐을 때만 쓴다. 영업·법무·재무 계열 스킬은 사업계획서에 맞는 부분만 쓴다.
5. 다른 스킬이 만든 숫자·출처도 검증(조사 스킬 5절)을 거친다. 지어낸 숫자·출처는 쓰지 않는다.
6. **호출 범위는 조사 깊이를 따른다**(조사 스킬 0절).
   - 빠름: 부르지 않는다. 내장 절차만 쓴다.
   - 보통: 웹 조사 1개와 수치 검증 1개까지 부른다.
   - 심층: 해당 행을 모두 쓴다. 토큰이 많이 드는 작업(심층 웹 조사, 서브에이전트 병렬 조사)은 처음 한 번 묻는다.
   - 조사 밖의 작업(차트·문서 편집·발표 파일)은 해당 행만 묻지 않고 부른다.
7. 산출물 끝 '보강 제안' 블록에 사용한 도구를 한 줄로 적는다(예: "조사: exa:search → 연결 실패, 내장 검색 사용").
8. 법무 계열 스킬의 결과는 법률 자문이 아니다. 사업계획서에는 "법률 확인 필요"를 함께 적는다.

## 표

| 작업 | 쓰는 bizplan 스킬 | 있으면 부를 스킬 | 넘길 것 | 받을 것 | 없으면 |
|------|-------------------|------------------|---------|---------|--------|
| 심층 웹 조사(시장·경쟁 목록, 깊이 '심층') | research | `exa:search`, `exa:exa-agent` | 하위 질문 · 기준연도 · 출처 표 열 | 출처 표 행(수치·단위·연도·출처·URL·품질 메모) | 내장 웹 검색 + 조사 스킬 0~1절 |
| 질의 분해 · 출처 종합 | research | `enterprise-search:search-strategy`, `enterprise-search:knowledge-synthesis` | 조사 질문 | 하위 질의 · 권위·신선도 판정 | 조사 스킬 0~1절 |
| 경쟁 요약 카드 | research, solution | `sales:competitive-intelligence`(수주·실주 기록이 있을 때만), `sales:account-research` | 경쟁사 실명 · 우리 차별 축 | 강점 · 안 맞는 곳 · 증거 · 차이 질문 | 조사 스킬 4절 |
| 인터뷰 설계 | research, interview | `design:user-research` | 문제 가설 · 대상 · 조사 스킬 3절의 5단계 틀 | 질문 문장 · 모집 문구(길이·단계는 3절 기준) | 조사 스킬 3절 |
| 인터뷰 · 설문 종합 | research, problem | `design:research-synthesis` | 메모 · 녹취 · CSV | 주제별 n/N · 인용 · 함의 | 조사 스킬 3절 |
| 기존 고객 인용 수집 | research | `sales:customer-voice`(통화·메일 커넥터 있을 때) | 주제 | 출처 붙은 인용 | 인터뷰 |
| 설문 데이터 분석 | research | `data:explore-data`, `data:statistical-analysis`, `data:analyze` | CSV | 분포 · 교차표 · 유의성 | 직접 계산 |
| 수치 검증 | research, review | `data:validate-data` | 출처 표 · 산식 | 판정(그대로·단서·재조사) | 조사 스킬 5절 |
| 차트 | visual | `dataviz`, `data:create-viz`, `data:data-visualization` | 만든 spec · PNG(원자료 탐색이면 CSV) | 형식 · 색 점검(그림은 렌더러로 만든다) | `bizplan-visual/scripts/html_visuals.py`(결론 제목·출처 틀, PNG — 문서용 `--print`, 발표용 `--slide`) — Node가 없으면 `chart_templates.py` |
| 파싱·디자인 분류 | visual, slides | — | 기존 단위 JSON·덱 스펙 또는 읽은 원문 Markdown · 대화의 아이템·고객·톤 | 기존 관계를 보존한 표현 추천 · 선택 테마 | `bizplan-slides/scripts/design_advisor.py --units`·`--deck`(재사용) 또는 `--doc`(기존 파서 호출). 실행 도구가 없으면 `design-selection.md`로 대화 안에서 분류 |
| 손익 · 재무 표 | growth | `finance:financial-statements` | 매출·비용 가정 | 손익 형식 표 | growth E절 |
| 계획 대비 실적(단계 평가) | growth, review | `finance:variance-analysis` | 계획 · 실적 | 차이 원인 | 직접 비교 |
| 규제 · 인허가 확인 | solution | `legal:compliance-check`, `legal:legal-risk-assessment` | 기능 · 데이터 · 업종 | 해당 규제 · 필요 승인 · 위험 등급 | 라우터 분야표의 게이트 + "법률 확인 필요" |
| MOU · NDA 검토 | team | `legal:review-contract`, `legal:triage-nda` | 문서 | 위험 조항 | 사람 검토 요청 |
| 양식 파일 편집 · 읽기 | 산출 전반 | `docx`, `pdf`, `xlsx` | 양식 파일 · 본문 | 채운 파일 · 추출 텍스트 | `md_to_docx.py` · `md_to_hwpx.py` · `read_form.py` · `check_tables.py --xlsx` |
| 완성본 한 번에 빌드 | document | — | `사업계획서.md` · `시각자료/spec.json` | .docx · .pdf · .hwpx · 쪽 미리보기 · 쪽 수·그림·남은 자리 보고 | `build_document.py`(검산 → 그림 `--print` → docx·pdf·미리보기·hwpx, `--style form`) |
| 공유 문서 | 산출 전반 | `docs`, `google-workspace` | 본문 | 공유 링크 | 파일 전달 |
| 발표 파일 편집 | slides | `pptx` | 템플릿 · 스펙 | 편집한 PPTX | `pptx_build.py` · `theme_deck.py` |
| 시각 검토 | review, slides | `design:design-critique`, `design:accessibility-review` | 미리보기 PNG | 문제 목록 | `bizplan-slides` 점검표 |
| 한 줄 소개 다듬기 | summary | `design:ux-copy` | 한 줄 후보 3개 | 다듬은 안 | 섹션 설계도 B1 공식·검증 |
| 예상 질문 답변 | pitch | `sales:handle-objection` | 질문 · 근거 | 답변 + 증거 | pitch 예상 질문 절 |
| 원페이저 | pitch | `sales:create-an-asset` | 숫자 등록부 · 개요 | 한 장 자료 | summary 개요 |
| 스킬 평가 · 개선(관리자) | — | `skill-creator` | 스킬 폴더 · 평가 질문 | 평가 결과 | `evals/` |

- 스킬 이름은 환경마다 접두어(플러그인 이름)가 다를 수 있다. 이름 끝부분(`competitive-intelligence` 등)으로 찾는다.
- 이 표에 없는 도구를 쓰려면 같은 열(넘길 것 · 받을 것 · 없으면)을 정한 뒤 쓴다.
