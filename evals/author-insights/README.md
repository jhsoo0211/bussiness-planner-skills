# Author insights: explicit-invocation regression probe

Date: 2026-09-04.

**The revised skills read the required author-insight sources in all three tested writing paths, and the completed drafts met the applicable frozen content criteria. The earlier version also met most criteria, so this probe does not establish an overall writing-quality advantage.** One earlier-version market draft changed an unknown funding status into a definite “not secured” statement; the revised draft preserved the unknown status.

This tests the author's writing guidance during drafting, separately from preserving a project's source notes. It does not test Claude, native skill pickers, automatic routing, all 15 skills, a complete sequential workflow, novice usability, or original DOCX/HWP page layout.

## What changed

- Eight drafting skills now read their own instructions, common rules, the [author-insight map](../../skills/bizplan/references/author-insights.md), and the original sections required for their mode before drafting. Direct invocation follows the same contract as router-based invocation.
- Quick mode compresses the draft while retaining the core reasoning of each part: direct problem evidence, actual solution scope, verification and cost plans, concrete market entry followed by vision, and task/risk-specific team capability.
- The author's SOM 200억원 guidance remains an experience-based recommendation for general tracks, with the U300 exception. It is not an official cutoff or permission to enlarge market scope or change time units without evidence.
- Drafting and review preserve the user's priority problems, including unresolved ones. They permit meaningful many-to-many problem/function relationships and identify scope gaps without silently changing the business direction.
- Review and market visualization follow these boundaries. Hypothetical scoring weights and the review consistency target are explicitly distinguished from verified official rules or measured performance.

## Frozen setup

The earlier source is commit [`182e45a`](https://github.com/jhsoo0211/bussiness-planner-skills/commit/182e45a113ae4945cf3b5cd4eae61dfab3993dde); the revised source is the skills content in this revision. Exact before/after file hashes are in [skill-hashes.json](skill-hashes.json).

- Host: Codex CLI `0.153.0-alpha.5`, Windows/PowerShell.
- Requested model: `gpt-5.6-sol`; reasoning: `ultra`.
- Each case used a fresh session with identical prompt bytes, tools/configuration, and `--ephemeral --sandbox read-only`. At most two model runs were active at once. Only the local business-skill source differed within each pair.
- Calls used `$skill-name` strings in the CLI prompt. This is an explicit invocation probe, not a UI selector test.
- [cases.json](cases.json) contains three fully synthetic inputs. None of the market data, organizations, mock announcements, interviews, or achievements is real evidence about an actual business or application program.
- [criteria.md](criteria.md) was fixed before execution and excluded from model prompts. An independent AI reviewer evaluated completed answers under randomized A/B labels without reading the allocation or run logs. This was not a human review; visible content may still make a version guess possible.
- Logs were separately audited for successful file reads, returned content, truncation, and access to evaluation material. Read-only mode did not provide strict filesystem read isolation. No reads of the gold criteria, sibling answers, external web sources, or the changing development worktree were observed. See [access-audit.md](access-audit.md).

## Completed content observations

Each row is one synthetic case with one completed answer per version. The two program variants in the market case are not independent trials.

| Explicit path | Earlier source | Revised source | Inspection notes |
| --- | --- | --- | --- |
| `research` + `growth` | Applicable criteria met except one partial evidence-status check | Applicable criteria met | Both computed annual TAM/SAM/first-year target as 240억/72억/3억, used the leading competitor's growth, and connected entry to expansion. The revision explicitly kept the 200억 author recommendation separate from the mock requirements. |
| `problem` + `solution` + `team` | Applicable criteria met in paired retry | Applicable criteria met in paired retry | Both preserved the priority disposal-cost problem as unresolved, bounded planned material use to 0.6t/0.5%, kept unanswered inquiry emails separate from partnerships, and mapped capability gaps to responsible work. |
| `quick` | Applicable criteria met | Applicable criteria met | Both retained the unresolved diagnosis problem, separated reported search time from a test target, used market/competitor evidence, and preserved team and partnership limitations. Some test/expansion plans differed without a criterion failure. |

The revised version read the author map and the required judge/case source content in all three paths. Separate judge/case reads were not observed in the earlier version. This is evidence of reference access and observed content compliance, not causal proof that a particular source sentence produced a particular answer.

Complete outputs and version-label-masked reviews:

| Case | Earlier answer | Revised answer | Independent body review |
| --- | --- | --- | --- |
| Market/growth | [before](answers/research_growth_tracks-before.md) | [after](answers/research_growth_tracks-after.md) | [review](review-research_growth_tracks.md) |
| Problem/solution/team | [before, retry](answers/problem_solution_team_priority-before.md) | [after, retry](answers/problem_solution_team_priority-after.md) | [review](review-problem_solution_team_priority.md) |
| Quick | [before](answers/quick_integrated-before.md) | [after](answers/quick_integrated-after.md) | [review](review-quick_integrated.md) |

The A/B label allocations, answer hashes, and original/retry records are in [run-records.json](run-records.json). The reviews keep their original anonymous labels.

## Failures, timing, and runtime limits

There were **eight attempts: four completed initial runs, two incomplete initial runs, and two completed paired retries**. The initial problem/solution/team pair ended after a shared stream interruption. Its abnormal elapsed values (about 4,178 seconds despite a 480-second limit) are not valid latency observations. The original failures were retained and excluded from body/latency comparisons; both versions were rerun once with the same frozen input/skill bytes, requested model, and CLI flags. The host reported 69 omitted additional skills in the initial runs and 111 in both retries, so the global discovery context was not identical across attempts. Compare only the matched completed pairs, and do not combine original partial drafts with retry drafts.

| Completed case | Earlier source | Revised source |
| --- | ---: | ---: |
| Market/growth | 208.73 s | 207.24 s |
| Problem/solution/team, retry | 162.22 s | 149.69 s |
| Quick | 223.74 s | 269.28 s |

These times include tool use and generation, not independent grading. There is one completed sample per case/version, varied output length, shared runtime disturbances, and no claim of speed or cost superiority. Token records include cumulative cached input and reasoning output; they are not unique input size or money spent. Missing usage for interrupted runs is unknown, not zero.

The host reported context-budget omissions of skill descriptions/additional skills and auxiliary-agent spawn failures. Quick runs also reported model-list refresh timeouts. The parent sessions still read the named files and completed the four original outputs shown above. See the audit for retry warnings and exact access evidence. Do not treat these runs as proof of normal automatic discovery or successful auxiliary-agent participation.

## Remaining evaluation

The original 2026 U300 DOCX exercise remains a separate Codex automatic-quick-path experiment. Reopening the original and filled documents and visually inspecting every rendered page is still required. The synthetic Markdown probes above do not complete that file-layout goal.

Claude comparison should use the actual product and installation type, matched explicit stages, the same evidence/form packet, and documented model/tool conditions. Real novice interviews and full-workflow checks remain to be performed. Use the [evaluation procedure](../README.md) to keep those evidence classes separate.
