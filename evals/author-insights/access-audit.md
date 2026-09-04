# 저자 인사이트 평가 — 접근·런타임 로그 독립 감사

감사일: 2026-09-04. 최초 실행 6개와 별도 재시도 2개를 대상으로 `events.jsonl`, `stderr.txt`, `record.json`과 동결된 스킬 파일을 읽었다. 모델 실행·종료·조건 변경은 하지 않았다. **본문 품질이나 저자 기준의 실제 적용 여부는 이 감사의 판정 대상이 아니다.**

## 판정 범위

- 조건: 동일한 명시 스킬 요청, Codex CLI의 설정 모델 `gpt-5.6-sol`, reasoning `ultra`, `--ephemeral`, `read-only`, 최대 2개 동시 실행. 가상 사례 3개 × before/after 각 1회다.
- before 기준 커밋은 `182e45a113ae4945cf3b5cd4eae61dfab3993dde`다. after는 `manifest.json`에 기록된 파일별 해시가 기준이다.
- 감사 시점에 6개 실행 폴더의 스킬 파일 목록·SHA-256이 모두 manifest와 같았다. 각 prompt의 해시는 record와 같고, `cases.json`·`gold.md`도 manifest 해시와 같았다. 현재 개발 작업트리를 모델이 읽었다는 이벤트는 없다.
- 최초 실행의 정상 완료는 4개, 미완료는 2개다. 별도 재시도 2개는 모두 완료됐다. 총 8번 시도 중 6번 완료·2번 미완료이며, 각 사례·조건의 완료 답안은 여전히 1개다. 미완료 실행에서 남은 메시지를 완성 답안으로 보지 않는다. 참고문서 읽기 성공과 최종 모델 작성 완료를 구분한다.

## 최초 실행 상태

| 실행 폴더 (`runs/` 아래) | 종료 | 모델 턴 | 접근 기록의 용도 |
| --- | --- | --- | --- |
| `research_growth_tracks-before` | exit 0, stop 없음 | 완료 | 지정 스킬·공통 규칙 읽기 확인 |
| `research_growth_tracks-after` | exit 0, stop 없음 | 완료 | 추가 저자 지도·J/C 지정 범위 읽기 확인 |
| `problem_solution_team_priority-before` | exit 1, `480_second_limit` | 미완료 | 중단 전 읽기 증거만 유지; 품질·속도 비교 제외 |
| `problem_solution_team_priority-after` | exit 1, `provider_or_network_failure` | 미완료 | 중단 전 읽기 증거만 유지; 품질·속도 비교 제외 |
| `quick_integrated-before` | exit 0, stop 없음 | 완료 | quick·공통 규칙 읽기 확인 |
| `quick_integrated-after` | exit 0, stop 없음 | 완료 | quick·공통 규칙·저자 지도·J/C 전체 읽기 확인 |

## 실제 성공 읽기

아래 경로는 각 실행 폴더의 `.agents/skills/`를 기준으로 한다. `item_N (L숫자)`는 그 폴더 `events.jsonl`의 완료 이벤트 ID와 1부터 센 JSONL 행이다. **전체** 표시는 성공 명령의 반환 본문에 동결된 파일 전문이 포함되는지 줄바꿈을 정규화해 대조했다. 명령의 exit 0만으로 전체 읽기를 추정하지 않았다.

| 실행 | 파일·범위 | 이벤트 근거 |
| --- | --- | --- |
| research before | `bizplan-research/SKILL.md` 전체 | `item_2 (L8)` |
| research before | `bizplan/references/common-rules.md` 전체 | `item_3 (L9)` |
| research before | `bizplan-growth/SKILL.md` 전체 | `item_4 (L10)` |
| research after | `bizplan-research/SKILL.md`, `bizplan/references/common-rules.md`, `bizplan-growth/SKILL.md`, `bizplan/references/author-insights.md` 각각 전체 | `item_2 (L9)`, `item_3 (L10)`, `item_4 (L11)`, `item_5 (L12)` |
| research after | `bizplan-review/references/judge-insights.md`의 제목·굵은 항목 검색 후 원문 L1–6, L46–58 | 검색 `item_6 (L15)`; 범위 읽기 `item_8 (L19)` |
| research after | `bizplan-review/references/case-insights.md`의 제목·굵은 항목 검색 후 원문 L1–7, L23–28, L73–85, L131–136 | 검색 `item_7 (L16)`; 범위 읽기 `item_9 (L20)` |
| problem/solution/team before | `bizplan-team/SKILL.md`, `bizplan-solution/SKILL.md`, `bizplan-problem/SKILL.md`, `bizplan/references/common-rules.md` 각각 전체 | `item_2 (L9)`, `item_4 (L10)`, `item_3 (L11)`, `item_5 (L12)` |
| problem/solution/team after | `bizplan-problem/SKILL.md`, `bizplan-solution/SKILL.md`, `bizplan-team/SKILL.md` 전체 | 묶음 읽기 `item_2 (L6)` |
| problem/solution/team after | `bizplan/references/common-rules.md`, `bizplan/references/author-insights.md` 전체 | 묶음 읽기 `item_3 (L8)` |
| problem/solution/team after | `bizplan-review/references/case-insights.md`, `bizplan-review/references/judge-insights.md` 전체 | 묶음 읽기 `item_4 (L10)` |
| quick before | `bizplan-quick/SKILL.md`, `bizplan/references/common-rules.md` 각각 전체 | `item_2 (L6)`, `item_3 (L8)` |
| quick after | `bizplan-quick/SKILL.md`, `bizplan/references/common-rules.md`, `bizplan/references/author-insights.md` 전체 | 묶음 읽기 `item_2 (L6)` |
| quick after | `bizplan-review/references/judge-insights.md`, `bizplan-review/references/case-insights.md` 전체 | 묶음 읽기 `item_3 (L8)` |

research after의 선택 범위는 저자 지도에 지정된 J의 신뢰도 구분·§4, C의 목적·사용법·첫 체크리스트 6/8번·성장전략·PSST 학생 트랙 범위를 포함한다. 이는 필수 원문 접근이 이루어졌다는 판정이며, 작성 본문에서 이를 정확히 적용했다는 판정은 아니다.

before 3개 사례에서는 J/C 원문을 별도로 읽은 이벤트가 관찰되지 않았다. after 3개 사례에서는 저자 지도 및 J/C 원문 접근이 모두 관찰됐다. 다만 problem/solution/team after는 최종 작성이 미완료이므로 이 읽기를 성공 답안으로 환산하지 않는다.

## 잘림·추가 읽기·접근 경계

- 최초 6개에서 완료된 shell 명령은 총 22개이며 모두 exit 0이다. 명령 반환에 `truncated`/잘림 경고는 관찰되지 않았다. 전체 읽기라고 표시한 반환은 실제 파일 전문과 대조했다.
- research after의 `rg` 검색 후 두 번의 범위 읽기는 필요한 절을 선택한 추가 읽기다. 잘림 오류를 복구한 재시도로 기록하지 않는다. 나머지 최초 실행에서 잘림 복구가 필요한 상황은 관찰되지 않았다.
- 22개 명령은 모두 해당 조건의 `.agents/skills` 파일을 읽거나 검색했다. `gold.md`, 형제 조건 폴더, 다른 답안, 현재 개발 작업트리, 평가 하네스/평가 기준 파일을 여는 명령은 관찰되지 않았다.
- JSONL에 web/search/MCP 외부 조회 이벤트가 없고, shell 명령에도 다운로드·HTTP 요청은 없다. 참고문서 안의 외부 출처 URL 표기는 실제 웹 접속으로 세지 않았다.
- 이 판정은 **노출된 도구 로그에서 접근을 관찰하지 못했다**는 뜻이다. read-only sandbox가 작업 폴더 밖의 모든 읽기를 기술적으로 차단했다고 주장하지 않는다.

## 조건별 런타임 경고·실패

아래 오류는 모델/스킬 내용의 평가와 별도로 보존한다. `record.json`의 stop 없음은 보조 런타임 경고가 없었다는 뜻이 아니다.

| 실행 | JSONL context budget 경고 | stderr 보조 실패·경고 | 파일 읽기 명령 실패 |
| --- | --- | --- | --- |
| research before | `item_0 (L3)`: 설명 전부 제거·추가 69개 스킬 목록 제외 | no-thread spawn 1회; 아이콘 경고 4회; PowerShell snapshot 미지원 1회 | 0 |
| research after | 동일 `item_0 (L3)` | no-thread spawn 1회; 아이콘 경고 4회; PowerShell snapshot 미지원 1회 | 0 |
| problem/solution/team before | 동일 `item_0 (L3)` | no-thread spawn 1회; websocket idle timeout 1회; 아이콘 경고 4회; PowerShell snapshot 미지원 1회 | 0 |
| problem/solution/team after | 동일 `item_0 (L3)` | no-thread spawn 1회; websocket idle timeout 1회; 아이콘 경고 4회; PowerShell snapshot 미지원 1회 | 0 |
| quick before | 동일 `item_0 (L3)` | no-thread spawn 1회; 모델 목록 refresh child-process timeout 2회; parent transcript hook 경고 1회; 아이콘 경고 4회; PowerShell snapshot 미지원 1회 | 0 |
| quick after | 동일 `item_0 (L3)` | no-thread spawn 1회; 모델 목록 refresh child-process timeout 2회; 아이콘 경고 4회; PowerShell snapshot 미지원 1회 | 0 |

6개 모두 `--ephemeral` 실행 중 `collab spawn failed: no thread with id`가 stderr에 남았다. 각 parent의 파일 읽기는 이후에도 이어졌고 4개는 최종 턴까지 완료됐다. 이 spawn 실패는 독립 JSONL 도구 완료 이벤트 ID가 없어 stderr 메시지로 근거를 남긴다. 실패한 보조 에이전트가 정상 참여했다고 보지 않는다.

context budget 경고는 stderr가 아니라 JSONL의 `item.completed` 안 `type: error`로 나타났다. 따라서 stderr나 최상위 `error` 이벤트만 검사하면 누락된다. 지정 스킬을 명시하고 실제 파일을 읽은 증거는 있지만, 모든 설치 스킬의 설명이 정상 노출됐다는 결론이나 자동 선택 성능의 결론은 낼 수 없다.

### problem/solution/team의 비정상 중단

before는 4,177.17초, after는 4,178.59초로 기록됐다. 양쪽 stderr에는 거의 동일 시각인 `2026-09-04T05:52:18Z`에 `stream disconnected before completion: idle timeout waiting for websocket`가 남았다. before의 stop reason은 시간 제한, after는 provider/network failure로 서로 다르지만 **두 실행 모두 완료되지 않은 비정상 런타임 시도**로 분리한다. 480초 설정을 크게 넘긴 원인을 컴퓨터 sleep 등으로 단정하지 않는다.

이 두 시도의 메시지·경과 시간·usage 부재를 품질·속도·비용 우위로 해석하지 않는다. 실패 시도 2건으로 보존하고, 재시도가 있으면 별도 시도로 기록한다.

## 재시도

problem/solution/team pair를 `retry-1/runs`의 새 세션에서 한 번씩 재시도했다. 최초 실패 답안을 이어 쓰지 않았으며, 최초 시도 6개와 재시도 2개의 결과를 별도로 보존한다. 같은 설정의 모델·reasoning·CLI 옵션과 동결된 bizplan 파일·프롬프트를 사용했지만, 아래 전역 스킬 목록 경고 차이가 있어 모든 런타임 상태가 최초 실행과 같았다고 보지는 않는다.

### 완료 상태와 무결성

| 재시도 폴더 (`retry-1/runs/` 아래) | 종료·모델 턴 | 경과 시간 | 무결성 |
| --- | --- | --- | --- |
| `problem_solution_team_priority-before` | exit 0, stop 없음, `turn.completed` | 162.22초 | 스킬·프롬프트 동결 유지 |
| `problem_solution_team_priority-after` | exit 0, stop 없음, `turn.completed` | 149.69초 | 스킬·프롬프트 동결 유지 |

두 재시도 폴더의 실제 스킬 파일 목록·SHA-256을 각각 manifest의 before/after 목록과 독립적으로 대조했고 모두 일치했다. 두 prompt는 최초 해당 사례와 같은 SHA-256 `0cf42ca91ec7f4f31344ee070840d1e6fd6df760717f9a88e5019851d03ec7dd`다. `retry-1/cases.json`·`retry-1/gold.md`도 원래 manifest의 해시와 일치했다. 위 시간은 실행 기록이며, 단일 표본의 성능 우위나 최초 중단 시도와의 속도 비교로 해석하지 않는다.

### 실제 성공 읽기

아래 경로는 각 재시도 폴더의 `.agents/skills/`를 기준으로 한다. 모든 표 항목은 성공 명령이 반환한 텍스트에 동결된 파일 전문이 포함되는지 확인했다.

| 재시도 | 파일·범위 | 해당 `events.jsonl` 근거 |
| --- | --- | --- |
| before | `bizplan-problem/SKILL.md`, `bizplan-solution/SKILL.md`, `bizplan-team/SKILL.md` 각각 전체 | `item_2 (L6)`, `item_3 (L8)`, `item_4 (L10)` |
| before | `bizplan/references/common-rules.md` 전체 | `item_5 (L12)` |
| after | `bizplan-problem/SKILL.md`, `bizplan-solution/SKILL.md`, `bizplan-team/SKILL.md` 각각 전체 | `item_2 (L6)`, `item_3 (L8)`, `item_4 (L10)` |
| after | `bizplan/references/common-rules.md` 전체 | `item_5 (L12)` |
| after | `bizplan/references/author-insights.md` 전체 | `item_6 (L14)` |
| after | `bizplan-review/references/case-insights.md` 전체 | `item_7 (L17)` |
| after | `bizplan-review/references/judge-insights.md` 전체 | `item_8 (L18)` |

재시도 before의 완료 shell 명령은 4개, after는 7개이며 모두 exit 0이다. 11개 모두 해당 재시도 조건 폴더의 스킬·참고문서를 읽었다. 반환 잘림이나 잘림 복구, `gold.md`·다른 조건 폴더·다른 답안·개발 작업트리 접근, 외부 조회·다운로드·파일 쓰기 이벤트는 관찰되지 않았다. before는 J/C 원문을 별도로 읽지 않았고, after는 저자 지도·J/C 모두 전체를 읽었다. 이 차이는 문서 접근의 증거이며 본문 적용 품질은 별도 평가해야 한다.

### 재시도 런타임 경고

| 재시도 | JSONL context budget 경고 | stderr 보조 실패·경고 | 파일 읽기 명령 실패 |
| --- | --- | --- | --- |
| before | `item_0 (L3)`: 설명 전부 제거·추가 111개 스킬 목록 제외 | no-thread spawn 1회; 아이콘 경고 4회; PowerShell snapshot 미지원 1회 | 0 |
| after | 동일 `item_0 (L3)` | no-thread spawn 1회; 아이콘 경고 4회; PowerShell snapshot 미지원 1회 | 0 |

no-thread spawn 실패 시각은 before `2026-09-04T05:57:28.390454Z`, after `2026-09-04T05:57:29.121559Z`다. 두 parent는 이후 읽기와 최종 턴을 완료했다. 재시도에서는 websocket idle timeout, 모델 목록 refresh timeout, parent transcript hook 경고가 관찰되지 않았다. 보조 에이전트 참여가 정상 수행됐다고 주장하지 않는다.

**최초 실행은 추가 69개, 재시도는 추가 111개 스킬이 모델 목록에서 제외됐다.** 재시도 쌍의 경고는 같지만 최초 실행과 전역 스킬 목록 상태가 달라졌다는 관찰을 보존하며 원인은 단정하지 않는다. 이 차이는 동결된 bizplan 파일·프롬프트의 해시 일치와 별개다. 따라서 이 실험은 명시 호출 후 실제 문서 접근을 확인하는 근거로 사용할 수 있지만, 자동 라우팅 성능이나 완전히 동일한 전체 런타임 환경의 비교라고 표현해서는 안 된다.
