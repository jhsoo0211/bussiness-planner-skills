# bizplan — 한국 PSST 사업계획서 스킬

[한국어](README.md) | [English](README.en.md)

> 한국 정부 창업지원사업의 사업계획서를 **작성·검토·발표 준비**까지 단계별로 돕는 한국어 스킬 15종. Claude Code와 Codex에서 같은 `skills/` 원본을 사용한다.

**한국 사업계획서의 PSST(Problem · Solution · Scale-up · Team) 구조에 맞춰 설계했다.** 문제 인식 → 실현 가능성 → 성장 전략 → 팀 구성의 흐름으로 아이디어를 구체화한다. 범용 글로벌 사업계획서나 해외 투자 IR 전용 템플릿이 아니며, 다른 유형에는 해당 공고·양식·평가 기준에 맞춘 조정이 필요하다.

- 대상 사업: 예비창업패키지, 청년창업사관학교(청창사), U300, 로컬크리에이터, 수출바우처 등
- 스킬 본문·기본 안내·예시는 한국어다. **영어 README는 사용 설명의 번역이며, 스킬 전체의 영어 현지화나 해외 지원사업 적합성을 의미하지 않는다.**
- 지원사업마다 양식·금액·기간이 다르므로, 각 스킬은 먼저 **어떤 지원사업·양식 대상인지 확인**하고 예산·기간을 해당 공고 기준으로 조정한다. (기본값 예시: 예창패 1단계 2천만 + 2단계 4천만, 8개월)

## 스킬 목록

| 스킬                 | 용도                     | 이럴 때                                                                                                                               |
| -------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `bizplan`          | 라우터                   | "사업계획서 도와줘"처럼 막연할 때. 상황을 물어 알맞은 모드로 안내                                                                     |
| `bizplan-quick`    | 간략 모드                | 5가지(업종·타겟·핵심기능·차별점·약점)만 답하고 PSST 전체 초안을 한 번에                                                                 |
| `bizplan-item`     | ① 아이템 구체화         | 아이디어만 있음. 아이템명·문제·솔루션·차별점·페르소나 도출                                                                        |
| `bizplan-problem`  | ② 문제 인식 (P)         | SPIN 기법으로 Pain Point 설득, "배경 및 필요성" 작성                                                                                  |
| `bizplan-research` | ③ 시장·고객·경쟁 조사 | 시장 규모, 타겟 고객·페르소나, 경쟁사 비교 분석                                                                                      |
| `bizplan-solution` | ④ 실현 가능성 (S)       | 기술 구현 계획, 예산 계획(1·2단계), 추진 일정표                                                                                      |
| `bizplan-growth`   | ⑤ 성장 전략 (S)         | 비즈니스 모델·마케팅, SWOT, BM 구성도                                                                                                |
| `bizplan-team`     | ⑥ 팀 구성 (T)           | 대표자 역량, 팀 현황, 협력 기관                                                                                                       |
| `bizplan-summary`  | ⑦ 개요·마무리          | 개요 요약, 기업명·스토리텔링                                                                                                         |
| `bizplan-visual`   | 시각자료 모드            | 사업계획서에 넣을 그래프·도식·표 구성안 제안 및 제작 지원(matplotlib 그래프, 냅킨AI 인포그래픽 텍스트, 이미지 생성 AI용 영문 프롬프트, 포지셔닝맵·BM구성도 스케치) |
| `bizplan-review`   | ⑧ 심사위원 검토         | 초안 완성 후 점수·강약점·예상 질문, 데이터 신뢰도 검증                                                                              |
| `bizplan-pitch`    | 발표(피칭) 준비          | 발표 슬라이드 구성안, 스토리텔링, 예상 질문·모범 답변                                                                                |
| `bizplan-slides`   | 발표 슬라이드 제작       | HTML 슬라이드(16:9) 생성 + 레이아웃·콘텐츠 검증                                                                                      |
| `bizplan-export`   | 수출바우처               | 수출바우처 종합 구성, 목표시장 분석                                                                                                   |
| `bizplan-analyze`  | 벤치마킹 분석            | 남의 계획서·합격 사례 비교 분석, 작성 공식 도출                                                                                      |

## 설치 방법

### ① Codex에 설치

Git과 Python 3가 필요하다. 먼저 이 저장소를 내려받고 저장소 폴더로 이동한다. Windows에서 `python` 대신 `py`를 사용하는 환경이면 아래 명령의 `python`을 `py`로 바꾼다.

```bash
git clone https://github.com/jhsoo0211/bussiness-planner-skills.git
cd bussiness-planner-skills
python scripts/install_skills.py --agent codex
```

15개 스킬과 하위 참조 문서·스크립트를 `~/.agents/skills/`에 설치한다. 하나라도 같은 이름이 이미 있으면 **아무것도 덮어쓰지 않고 중단**한다. 기존 설치를 업데이트할 때는 사용자 수정본을 먼저 백업하고 대상 폴더를 비운 뒤 다시 실행한다. 여러 위치에 중복 설치하지 않는다.

특정 프로젝트에서만 쓰려면 목적지를 지정한다:

```bash
python scripts/install_skills.py --agent codex --dest /path/to/project/.agents/skills
```

```powershell
# Windows PowerShell
python scripts/install_skills.py --agent codex --dest 'C:\Projects\my-project\.agents\skills'
```

새 턴/세션에서 `bizplan` 스킬을 선택하거나 다음처럼 요청한다. Codex CLI/IDE에서는 `/skills` 또는 `$`로 스킬을 찾을 수 있다. 보이지 않으면 Codex를 재시작한다. [공식 스킬 문서](https://learn.chatgpt.com/docs/build-skills)

```text
$bizplan 예비창업패키지 사업계획서를 쓰고 싶어. 공고문을 먼저 확인해줘.
$bizplan-problem 제공한 메모의 문제 우선순위를 유지해 문제 인식 파트를 써줘.
$bizplan-growth 제공한 근거와 제약을 반영해 성장 전략 파트를 써줘.
$bizplan-review 이 초안을 제공한 배점표로 검토해줘.
```

특정 파트를 정했다면 라우터를 거치지 않고 해당 스킬을 직접 지정할 수 있다. 이름을 지정하지 않는 자연어 요청에서는 Codex가 설명에 맞는 스킬을 선택한다. **직접 지정과 자동 선택은 별도로 검증**하며, 스킬을 불렀다는 사실만으로 모든 파트·참고문서를 적용했다고 보지 않는다.

설치본에 `bizplan/references/common-rules.md`가 포함됐는지 확인한다. 세부 스킬도 이 공통 문서를 참조하므로 15개를 함께 설치하는 것을 권장한다. Codex용 별도 프롬프트 복사본이나 영구 분기 없이 같은 스킬을 유지한다.

### ② Claude Code에 설치

위와 같이 저장소를 내려받은 뒤 실행하면 `~/.claude/skills/`에 설치한다:

```bash
python scripts/install_skills.py --agent claude
```

이 로컬 설치에서는 `/bizplan` 또는 자연어로 요청한다. 특정 파트는 다음처럼 직접 지정한다. 스킬이 보이지 않으면 Claude Code를 재시작한다.

```text
/bizplan-problem 제공한 메모의 문제 우선순위를 유지해 문제 인식 파트를 써줘.
/bizplan-growth 제공한 근거와 제약을 반영해 성장 전략 파트를 써줘.
```

기존 Claude Code 마켓플레이스 설치도 사용할 수 있다:

```text
/plugin marketplace add jhsoo0211/bussiness-planner-skills
/plugin install bizplan@business-planner-skills
```

플러그인 이름은 `bizplan`이므로 플러그인 설치에서는 `/bizplan:bizplan-problem`, `/bizplan:bizplan-growth`, `/bizplan:bizplan-review`처럼 namespace를 포함해 지정한다. Claude Code도 직접 호출과 자동 선택을 모두 지원한다. [Claude Code 공식 스킬 문서](https://code.claude.com/docs/en/skills)

이 `/plugin` 명령은 **Claude Code용**이다. Codex에서는 위의 로컬 설치 절차를 사용한다. 마켓플레이스 업데이트는 Claude Code의 `/plugin marketplace update`를 사용한다.

**Claude.ai 일반 채팅은 별도 환경이다.** 공식 도움말은 Customize → Skills에서 활성화하고, 필요하면 사용할 스킬 이름을 요청에 명시하도록 안내한다. 이 저장소의 Claude Code 설치·slash 명령을 그대로 적용할 수 있다는 뜻은 아니다. [Claude.ai 공식 스킬 도움말](https://support.claude.com/en/articles/12512180-use-skills-in-claude)

### 저자 인사이트와 파트별 작성

각 파트와 `bizplan-quick`은 **[파트별 저자 인사이트 지도](skills/bizplan/references/author-insights.md)에 연결된 필수 원문을 작성 전에 읽고**, 해당 파트의 작성 기준에 적용해야 한다. 검토 단계까지 미루거나 공통 규칙만 읽은 것으로 대신하지 않는다. 사용자가 제공한 메모의 문제 우선순위·기술·비용·안전 제약은 양식의 해당 항목에 연결하고, 사례에서 얻은 작성 원칙과 현재 팀의 검증된 사실은 구분한다.

검증에서는 **참고문서를 읽은 기록**과 **본문에 실제 적용한 근거**를 따로 확인한다. 필수 참조 연결을 추가했다는 사실만으로 검증 완료를 주장하지 않는다. 이전 U300 실행은 Codex에서 자동으로 quick 경로를 선택한 1회 작성 사례이며 Claude 성능 비교가 아니다. 변경 후의 제한된 명시 호출 검사는 [가상 입력과 결과](evals/author-insights/README.md)에 기록한다. 전체 작성 흐름·Claude 비교·원본 문서의 페이지 검증은 별도다. [평가 절차와 증거 범위](evals/README.md)

### 도구와 검증 범위

- 기본 작성·검토 지침은 Markdown 스킬이며 별도의 API 키를 포함하지 않는다. 실행할 Claude Code 또는 Codex 계정·환경은 사용자가 준비한다.
- 웹 조사, Python 그래프, DOCX 변환, HTML 슬라이드 검수는 해당 환경의 도구·권한이 있을 때 수행한다. 설치만으로 외부 도구나 서비스를 추가하지 않는다.
- 도구가 없으면 수행하지 못한 작업과 필요한 자료를 밝힌다. 확인하지 못한 통계·출처·팀 실적을 검증 완료로 쓰지 않는다.
- `dist/*v0.4.0.zip`은 기존 배포 파일이다. 이번 Codex 안내와 변경을 사용하려면 이 저장소의 현재 체크아웃으로 설치한다.

```bash
python scripts/check_installation.py
```

위 명령은 임시 폴더에서 15개 스킬·리소스 복사와 덮어쓰기 방지를 확인한다. 모델을 실행하지 않으며 **Codex와 Claude의 작성 품질·속도·비용을 비교한 결과가 아니다**. 실제 평가 절차와 기록 기준은 [evals/README.md](evals/README.md)를 참고한다.

## 빠른 시작 (스텝 바이 스텝)

**Step 1.** Claude Code 또는 Codex에 이렇게 말한다 (공고문 파일이 있으면 함께 첨부):

> 예비창업패키지 사업계획서 쓰고 싶어. 아이템은 시니어용 복약관리 약통이야.

**Step 2.** 라우터(`bizplan`)가 시작 질문을 한다:

- 어떤 지원사업·공모전인지 (평가 기준표/배점표가 있으면 첨부 요청)
- 진행 단계 — 아이디어만 / 특정 섹션 작성 중 / 초안 완성
- **빠른 버전**(전체 초안 한 번에) vs **꼼꼼 버전**(조사 포함 단계별, 오래 걸림) vs 특정 섹션만
- 출력 형식 — 채팅만 / .md 파일 저장 / .docx 파일 (세션에서 한 번만 정한다)

> 질문에 답하기 어려우면 아이디어 메모·파일만 던져도 된다 — 스킬이 기획 요약 초안을 먼저 만들어 "이런 기획이 맞나요?"라고 확인받고 시작한다.

**Step 3.** 선택한 모드가 실행된다. 예를 들어 빠른 버전이면 `bizplan-quick`이 5가지(업종·타겟·핵심기능·차별점·단점)만 묻고 PSST 전체 초안 + 문제-솔루션 1:1 자체 점검표를 만든다.

**Step 4.** 초안이 나오면 검토를 돌린다:

> 심사위원처럼 점수 매기고 피드백해줘

`bizplan-review`가 배점 항목별 득점표, 11대 체크포인트(O/△/X), 약점별 "더 나은 방향", 데이터 신뢰도 검증, 예상 질문까지 제공한다. 출력 예시: [examples/예시-검토리포트-PILLY.md](examples/예시-검토리포트-PILLY.md)

**Step 5.** 발표 심사가 있으면:

> 발표 준비해줘. 발표 7분 + 질의응답 10분이야.

`bizplan-pitch`가 발표 흐름(대회 성격별 조정) → 슬라이드 구성안(슬라이드별 유도 질문 포함) → 장점 30초 답변·약점 방어 → 예상 질문을 만든다.

## 한 줄 사용 예시

- "예비창업패키지 사업계획서 쓰고 싶은데 뭐부터 해야 할지 모르겠어" → `bizplan`(라우터)
- "AI 반려동물 건강관리 앱 아이디어를 구체화해줘" → `bizplan-item`
- "문제 인식 파트를 심사위원이 납득하게 써줘" → `bizplan-problem`
- "이 시장 규모랑 경쟁사 좀 조사해줘" → `bizplan-research`
- "예산 계획이랑 8개월 추진 일정 만들어줘" → `bizplan-solution`
- "TAM SAM SOM 도식이랑 시장 그래프 만들어줘" → `bizplan-visual`
- "초안 다 썼는데 심사위원처럼 점수 매기고 피드백해줘" → `bizplan-review`
- "발표 슬라이드랑 예상 질문 준비해줘" → `bizplan-pitch`
- "빠르게 전체 초안부터 뽑아줘" → `bizplan-quick`

## 산출물 미리보기

`bizplan-visual`이 실제로 생성하는 시각자료 (가상 아이템 PILLY 예시, 재현 스크립트는 [examples/visuals/](examples/visuals/)):

| TAM/SAM/SOM 동심원                                     | 경쟁 포지셔닝맵                                       |
| ------------------------------------------------------ | ----------------------------------------------------- |
| ![TAM/SAM/SOM](examples/visuals/pilly_tam_sam_som.png) | ![포지셔닝맵](examples/visuals/pilly_positioning.png) |

완성 예시 전문:

- **PILLY** (AI 복약관리 스마트 약통 — 스킬이 직접 작성→검토): [제작 예시](examples/예시-사업계획서-PILLY.md) · [검토 리포트](examples/예시-검토리포트-PILLY.md)
- **Re:Shell** (굴 패각 제설제 — 외부 작성 계획서를 검토): [사업계획서 예시](examples/예시-사업계획서-리쉘-굴패각제설제.md) · [검토 리포트](examples/예시-검토리포트-리쉘-굴패각제설제.md)

## 참고 문서

- `docs/psst.md` — 25개 원본 프롬프트를 모드별로 재구성한 마스터 문서
- `examples/` — 가상 아이템 2종의 완성 예시. **PILLY**(AI 복약관리 약통)는 스킬 파이프라인으로 작성→검토한 예시(문제-솔루션 1:1 대응표·TAM/SAM/SOM 산정·시각자료 구성안·자체 채점 포함). **Re:Shell**(굴 패각 제설제)은 외부에서 작성된 U300 초안을 `bizplan-review`로 평가한 예시(배점 득점표·11대 체크포인트·심사위원 납득도·데이터 검산 포함). 모두 데모용 가상 콘텐츠

## 유의사항

- 정부지원사업 외 문서(투자 IR·민간 공모전·정책자금·B2B 제안 등)는 해당 심사 자료·양식에 맞춰 조정한 뒤 보조 도구로 활용한다. 기본 PSST 구성을 그대로 적용하면 맞지 않을 수 있다.
- 공식 평가 기준표(배점표)가 있으면 스킬에 첨부하라 — 배점 항목에 본문을 매핑해 검토·작성한다.
- 개인정보(학교명·직장명)는 기재하지 않는다. 필요하면 이니셜(예: S대학교)을 사용한다. 단, **제출 양식이 소속·실명 기재를 공식 요구하면**(예: 학생창업 트랙의 소속대학) 양식을 따른다.
- AI가 생성한 시장 데이터·통계는 **반드시 원출처로 검증**한 뒤 제출한다.
- 비현실적인 예산·일정은 지양한다.
- 출력 형식(채팅/.md/.docx)은 라우터가 세션 시작 때 한 번 묻는다. 웹/앱에서는 섹션별로 파일에 누적하고 채팅에는 요약만 보여준다(.docx 변환은 pandoc, 없으면 python-docx).
- U300 등 학생 트랙은 라우터가 깊이 인터뷰(원가·시제품·실적·재무 근거 보유 여부)를 먼저 한다 — 증빙이 있는 항목만 예창패 수준 깊이로 쓰고, 없는 항목은 "산정 예정(근거·확보 시점 명시)"로 처리한다.
