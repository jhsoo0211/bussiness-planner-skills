# 도구 지도 — 환경에 있는 스킬을 하나의 기준으로 쓰기

bizplan 스킬이 작업 중에 **다른 스킬·도구를 부를 때 보는 단일 기준표**다. 각 스킬 본문에 연동 문장을 흩어 두지 않고, 여기 한 곳에서 정한다.

## 규칙

1. 작업을 시작할 때 아래 표에서 그 작업 행을 찾는다.
2. '있으면 부를 스킬'이 **지금 환경의 스킬 목록**에 있으면 그 스킬로 하위 작업을 맡긴다.
   - 결과는 bizplan 형식(출처 표 · 근거 라벨 · 숫자 등록부)으로 받아 옮긴다.
   - 목록이 안 보이는 환경(Codex·로컬 설치)에서는 `bizplan/scripts/find_tools.py`로 확인한다.
3. 없거나 실패하면 **'없으면'** 칸의 내장 절차로 한다. 실패는 숨기지 않고 한 줄로 알린다.
4. 사내 커넥터(CRM·메일·통화 기록·사내 문서)가 필요한 기능은 커넥터가 연결됐을 때만 쓴다. 영업·법무·재무 계열 스킬은 사업계획서에 맞는 부분만 쓴다.
5. 다른 스킬이 만든 숫자·출처도 검증(조사 스킬 5절)을 거친다. 지어낸 숫자·출처는 쓰지 않는다.
6. **자동 호출 강도**: 토큰이 많이 드는 작업(심층 웹 조사, 서브에이전트 병렬 조사)은 처음 한 번 묻는다. 나머지는 묻지 않고 부른다.
7. 산출물 끝 '보강 제안' 블록에 사용한 도구를 한 줄로 적는다(예: "조사: exa:search → 연결 실패, 내장 검색 사용").
8. 법무 계열 스킬의 결과는 법률 자문이 아니다. 사업계획서에는 "법률 확인 필요"를 함께 적는다.

## 표

| 작업 | 쓰는 bizplan 스킬 | 있으면 부를 스킬 | 넘길 것 | 받을 것 | 없으면 |
|------|-------------------|------------------|---------|---------|--------|
| 심층 웹 조사(시장·경쟁 목록) | research | `exa:search`, `exa:exa-agent` | 하위 질문 · 기준연도 · 출처 표 열 | 출처 표 행(수치·단위·연도·출처·URL·품질 메모) | 내장 웹 검색 + 조사 스킬 0~1절 |
| 질의 분해 · 출처 종합 | research | `enterprise-search:search-strategy`, `enterprise-search:knowledge-synthesis` | 조사 질문 | 하위 질의 · 권위·신선도 판정 | 조사 스킬 0~1절 |
| 경쟁 요약 카드 | research, solution | `sales:competitive-intelligence`(파일만 모드), `sales:account-research` | 경쟁사 실명 · 우리 차별 축 | 강점 · 안 맞는 곳 · 증거 · 차이 질문 | 조사 스킬 4절 |
| 인터뷰 설계 | research, interview | `design:user-research` | 문제 가설 · 대상 | 인터뷰 가이드 | 조사 스킬 3절 |
| 인터뷰 · 설문 종합 | research, problem | `design:research-synthesis` | 메모 · 녹취 · CSV | 주제별 n/N · 인용 · 함의 | 조사 스킬 3절 |
| 기존 고객 인용 수집 | research | `sales:customer-voice`(통화·메일 커넥터 있을 때) | 주제 | 출처 붙은 인용 | 인터뷰 |
| 설문 데이터 분석 | research | `data:explore-data`, `data:statistical-analysis`, `data:analyze` | CSV | 분포 · 교차표 · 유의성 | 직접 계산 |
| 수치 검증 | research, review | `data:validate-data` | 출처 표 · 산식 | 판정(그대로·단서·재조사) | 조사 스킬 5절 |
| 차트 | visual | `dataviz`, `data:create-viz`, `data:data-visualization` | 값 · 출처 · 결론 수치 | 차트 파일 | `bizplan-visual/scripts/chart_templates.py` |
| 손익 · 재무 표 | growth | `finance:financial-statements` | 매출·비용 가정 | 손익 형식 표 | growth E절 |
| 계획 대비 실적(단계 평가) | growth, review | `finance:variance-analysis` | 계획 · 실적 | 차이 원인 | 직접 비교 |
| 규제 · 인허가 확인 | solution | `legal:compliance-check`, `legal:legal-risk-assessment` | 기능 · 데이터 · 업종 | 해당 규제 · 필요 승인 · 위험 등급 | 라우터 분야표의 게이트 + "법률 확인 필요" |
| MOU · NDA 검토 | team | `legal:review-contract`, `legal:triage-nda` | 문서 | 위험 조항 | 사람 검토 요청 |
| 양식 파일 편집 · 읽기 | 산출 전반 | `docx`, `pdf`, `xlsx` | 양식 파일 · 본문 | 채운 파일 · 추출 텍스트 | `md_to_docx.py` · `md_to_hwpx.py` · `read_form.py` · `check_tables.py --xlsx` |
| 공유 문서 | 산출 전반 | `docs`, `google-workspace` | 본문 | 공유 링크 | 파일 전달 |
| 발표 파일 편집 | slides | `pptx` | 템플릿 · 스펙 | 편집한 PPTX | `pptx_build.py` · `theme_deck.py` |
| 시각 검토 | review, slides | `design:design-critique`, `design:accessibility-review` | 미리보기 PNG | 문제 목록 | `bizplan-slides` 점검표 |
| 한 줄 소개 다듬기 | summary | `design:ux-copy` | 한 줄 후보 3개 | 다듬은 안 | 섹션 설계도 B1 공식·검증 |
| 예상 질문 답변 | pitch | `sales:handle-objection` | 질문 · 근거 | 답변 + 증거 | pitch 예상 질문 절 |
| 원페이저 | pitch | `sales:create-an-asset` | 숫자 등록부 · 개요 | 한 장 자료 | summary 개요 |
| 스킬 평가 · 개선(관리자) | — | `skill-creator` | 스킬 폴더 · 평가 질문 | 평가 결과 | `evals/` |

- 스킬 이름은 환경마다 접두어(플러그인 이름)가 다를 수 있다. 이름 끝부분(`competitive-intelligence` 등)으로 찾는다.
- 이 표에 없는 도구를 쓰려면 같은 열(넘길 것 · 받을 것 · 없으면)을 정한 뒤 쓴다.
