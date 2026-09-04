# Evaluation: installation, routing, and writing quality

검증 단계를 분리해 기록한다. 설치 성공이나 예시 문서만으로 Codex와 Claude Code의 성능·품질이 같다고 주장하지 않는다.

## 1. Offline installation smoke

```bash
python scripts/check_installation.py
```

- 15개 스킬 이름과 frontmatter를 확인한다.
- Codex/Claude 목적지에 참조 문서·스크립트가 원본과 같은 해시로 복사되는지 확인한다.
- 기존 설치/사용자 수정본을 덮어쓰지 않는지, 충돌이 있으면 복사 전에 중단하는지 확인한다.
- 스킬 소스 안으로 설치하거나 소스를 덮는 목적지는 거부한다.
- 사용자 스킬 경로를 변경하거나 모델을 호출하지 않는다.

This is a deterministic installation check, not a live agent or model benchmark.

## 2. Live discovery and routing

Use a fresh session for each query in [trigger-evals.json](trigger-evals.json). Record which skill the host actually selected, the expected skill, any references opened, and pass/fail. Include negative cases where no bizplan skill should activate. Do not insert `$bizplan` or `/bizplan` in an **implicit-routing** test: that would test explicit invocation instead.

Before the full set, explicitly invoke `bizplan` and `bizplan-review` once in each host to check discovery and access to `bizplan/references/common-rules.md`. Record host version, skill commit, model, reasoning setting where applicable, and available tools. Missing discovery is an installation/runtime failure, not a writing-quality score.

## 3. Controlled writing pilot — criteria to agree first

Use a `grill-me` interview with the maintainer to settle one decision at a time: the target application, the most important failure to avoid, acceptable review time, the comparison conditions, and the threshold for a useful result. Read the repository and supplied materials first; do not ask the maintainer questions the files already answer. `grill-me` is an optional interview workflow, not a runtime dependency of bizplan.

Suggested pilot cases:

| Case | Input | What to inspect |
| --- | --- | --- |
| Quick draft | One fictional idea, all five inputs, explicit missing evidence | PSST coverage, problem-solution mapping, clear assumption labels |
| Rubric review | A fixed draft with intentionally unsupported claims and a supplied rubric | Detection of unsupported claims, actionable fixes, arithmetic |
| Form adaptation | The same evidence packet plus a non-default section order and length limits | Form precedence, no invented facts, preservation of evidence |
| Tool unavailable | A research request with browsing unavailable | Honest limitations and source requests; no fabricated verification |

Candidate Korean prompts (use identical content across conditions):

> 가상 연습 과제야. 업종은 대학생 일정관리 앱, 타겟은 팀 프로젝트가 많은 대학생, 핵심 기능은 공동 마감일과 역할 기록, 차별점 가설은 과목별 업무 분담 연결, 약점은 실제 사용자가 아직 없다는 점이야. 지원사업은 미정이고 실제 시장 수치·매출·고객 인터뷰는 제공하지 않았어. 한국 PSST 전체 초안을 채팅으로 작성해줘. 빈 근거를 실제 성과로 만들지 마.

> 첨부 초안과 배점표만 기준으로 검토해줘. 확인된 사실·가정·근거 없는 주장을 구분하고, 문제와 해결책의 불일치, 예산 합계 오류, 제공되지 않은 실적을 찾아 수정 우선순위를 알려줘. 외부 출처를 확인하지 못한 항목은 검증 완료로 쓰지 마.

> 첨부 공고 양식의 목차 순서와 항목별 분량에 맞춰 기존 초안을 재배치해줘. 기본 PSST 순서와 다르더라도 제공한 양식을 따라줘. 자료에 없는 내용은 작성 필요로 남겨줘.

Do not score an unattached draft or rubric: assemble and freeze those fixtures before running the review/adaptation cases.

For a small pilot, agree the conditions first (for example, one specified Codex model with/without the skill, or specified Codex and Claude configurations using the same skill). Use the same input packet, tool access, output length limit, and skill commit. Run each selected case at least three times in fresh sessions, randomize anonymous outputs for human review, and report the small sample size.

Record evidence integrity, PSST/form adherence, problem-solution consistency, usefulness of revisions, and Korean readability separately. Record latency and tokens only when reported by the host; missing usage is **unknown**, not zero. Do not equate tokens across providers with monetary cost or claim a winner from a single example. Save prompts, outputs, failures, judge notes, and the exact configuration with any published result.

## Current evidence boundary

The repository includes deterministic installation checks, 26 routing test cases, and illustrative Korean plan/review examples. A controlled Codex-versus-Claude writing-quality result is not included. Publish that result only after the interview criteria are agreed and the recorded runs are complete.
