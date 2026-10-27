# bizplan — Korean PSST business-plan skills

[한국어](README.md) | [English](README.en.md)

17 skills for drafting, reviewing, and presenting business plans for **Korean government startup-support programs**. Claude Code and Codex use the same `skills/` source.

## Scope: designed for Korean PSST applications

The workflow follows **PSST: Problem · Solution · Scale-up · Team**, commonly used in Korean startup business-plan applications:

| Section | Focus |
| --- | --- |
| Problem — 문제 인식 | Customer problems, background, and need |
| Solution — 실현 가능성 | Feasibility, implementation, and evidence |
| Scale-up — 성장 전략 | Business model, market entry, and growth |
| Team — 팀 구성 | Founder capabilities, team, and partners |

The intended context includes 예비창업패키지, 초기창업패키지, 창업도약패키지, 청년창업사관학교, U300, 창업중심대학, 재도전성공패키지, 로컬크리에이터, TIPS, and 수출바우처. Their requirements differ: the current official announcement, application form, and scoring rubric take precedence over the default PSST outline. Example budgets and schedules in the skills are illustrative, not current program rules.

**This is an English usage guide. The skill instructions, default interaction, and examples remain Korean.** It does not establish an English-localized workflow or suitability for non-Korean funding programs. Investor decks and other proposals require adaptation to their own audience and requirements.

## Skills

| Skill | Use it for |
| --- | --- |
| `bizplan` | Choosing the right workflow and gathering application requirements |
| `bizplan-interview` | An up-front, block-by-block interview that fixes every fact, gap, and constraint in `브리프.md`; later modes read this brief instead of relying on a long chat |
| `bizplan-quick` | A full PSST draft from five inputs: industry, target, features, differentiation, weaknesses |
| `bizplan-item` | Refining an idea, customer, problem, and value proposition |
| `bizplan-outline` | Fixing the outline before drafting: headings, one-line summaries, evidence slots, and page allocation |
| `bizplan-problem` | Framing the problem and need with SPIN |
| `bizplan-research` | Market size, customer research, and competitor comparisons |
| `bizplan-solution` | Implementation, grant budget by official cost category, funding sources, and schedule |
| `bizplan-growth` | Business model, marketing, SWOT, growth strategy, and revenue/P&L/break-even projections |
| `bizplan-team` | Founder capabilities, team, and partners |
| `bizplan-summary` | An executive summary, naming, and brand story |
| `bizplan-visual` | Evidence visuals, charts, positioning maps, and image prompts |
| `bizplan-review` | Reviewing a draft against the rubric, checking claims, and anticipating questions |
| `bizplan-pitch` | Presentation flow, storytelling, scripts, and Q&A |
| `bizplan-slides` | Producing PPTX and PDF decks that keep a supplied template's design (or a built-in template / HTML), then checking renders |
| `bizplan-export` | Export-voucher plans and target-market analysis |
| `bizplan-analyze` | Comparing completed plans and extracting reusable writing patterns |

## Install for Codex

Prerequisites: Git, Python 3, and a working Codex environment. On Windows, use `py` instead of `python` if that is your Python launcher.

```bash
git clone https://github.com/jhsoo0211/bussiness-planner-skills.git
cd bussiness-planner-skills
python scripts/install_skills.py --agent codex
```

This copies all 17 skill folders, including their references and scripts, into `~/.agents/skills/`. It **stops before copying if any target skill already exists**. To update an installation, back up any local edits and move the old target skill folders out of the installation location before running the installer again. Avoid duplicate installations in multiple skill locations.

For a project-only installation, specify that project's skills directory:

```bash
python scripts/install_skills.py --agent codex --dest /path/to/project/.agents/skills
```

```powershell
# Windows PowerShell
python scripts/install_skills.py --agent codex --dest 'C:\Projects\my-project\.agents\skills'
```

Start a new turn/session and select `bizplan`, or request it by name. In Codex CLI/IDE, use `/skills` or type `$` to find a skill. Restart Codex if it does not appear. These local locations and invocation mechanisms follow the [official Codex skill documentation](https://learn.chatgpt.com/docs/build-skills).

```text
$bizplan 예비창업패키지 사업계획서를 쓰고 싶어. 공고문을 먼저 확인해줘.
$bizplan-problem 제공한 메모의 문제 우선순위를 유지해 문제 인식 파트를 써줘.
$bizplan-growth 제공한 근거와 제약을 반영해 성장 전략 파트를 써줘.
$bizplan-review 이 초안을 제공한 배점표로 검토해줘.
```

These Korean prompts start an application, draft the problem or growth section from supplied notes, and review a draft against a supplied rubric. If you know the section you need, invoke its skill directly without going through the router. With a natural-language request that names no skill, Codex selects one by its description. **Test explicit invocation and automatic selection separately**: invoking a skill does not establish that every section or reference was applied.

Check that `bizplan/references/common-rules.md` is present after installation. The other skills refer to this shared document, so install the full set together. Codex uses the same source instructions as Claude Code; there is no separate prompt copy or permanent Codex fork to keep synchronized.

## Install for Claude Code

From the cloned repository:

```bash
python scripts/install_skills.py --agent claude
```

This installs into `~/.claude/skills/`. Use `/bizplan` or a natural-language request. For a specific section in this local installation, invoke it directly:

```text
/bizplan-problem 제공한 메모의 문제 우선순위를 유지해 문제 인식 파트를 써줘.
/bizplan-growth 제공한 근거와 제약을 반영해 성장 전략 파트를 써줘.
```

Restart Claude Code if the skills do not appear.

The existing Claude Code marketplace installation is also available:

```text
/plugin marketplace add jhsoo0211/bussiness-planner-skills
/plugin install bizplan@business-planner-skills
```

The plugin's name is `bizplan`, so use namespaced commands such as `/bizplan:bizplan-problem`, `/bizplan:bizplan-growth`, and `/bizplan:bizplan-review` for a plugin installation. Claude Code supports both direct invocation and automatic selection. See the [official Claude Code skill documentation](https://code.claude.com/docs/en/skills).

These `/plugin` commands are **for Claude Code**. Use the local installation above for Codex. For a Claude marketplace installation, use `/plugin marketplace update` to update the marketplace.

**Claude.ai chat is a separate environment.** Its official help describes enabling skills under Customize → Skills and naming the desired skill in the request. This does not make this repository's Claude Code installation steps or slash commands applicable to chat. See the [official Claude.ai skill help](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

## Author insights and section writing

Each section skill and `bizplan-quick` must **read the original references linked in the [section-specific author-insight map](skills/bizplan/references/author-insights.md) before drafting** and apply them to that section's writing criteria. Do not defer this to review or substitute reading the common rules alone. Map the user's problem priorities and technical, cost, and safety constraints to the relevant form sections. Distinguish lessons from past cases from verified facts about the current team.

Evaluation must separately record **evidence that a reference was read** and **evidence that the draft applies its guidance**. Adding required-reference links is not completed validation. The earlier U300 run was one Codex drafting case that automatically selected the quick path; it was not a Claude performance comparison. See the [synthetic cases and results](evals/author-insights/README.md) for the limited explicit-invocation checks after this change. Full-workflow, Claude, and original-document page validation remain separate. See the [evaluation procedure and evidence boundary](evals/README.md).

## A typical workflow

1. Provide your idea and, when available, the official announcement, application form, and scoring rubric.
2. `bizplan` checks the target program, working mode, and output format. Choose a quick draft, a step-by-step workflow with research, or a specific section. Existing answers are reused.
3. Draft the plan. `bizplan-quick` asks for five core inputs and produces a PSST outline with a problem-to-solution consistency check. Illustrative data must remain labeled as unverified.
4. Use `bizplan-review` to identify weak claims, missing evidence, inconsistencies, and likely reviewer questions. Its scores are feedback, not an official assessment or funding prediction.
5. If presentation review is required, use `bizplan-pitch` for the narrative and Q&A, then `bizplan-slides` to fill your presentation template (or a built-in one) and export PPTX and PDF.

The detailed path is:

`item` → `problem` → `research` → `solution` → `growth` → `team` → `summary` → `visual` (if needed) → `review` → `pitch` → `slides`

Each name above uses the `bizplan-` prefix. Output can remain in chat, accumulate in Markdown, or be converted to DOCX when the required tools are available. The final submission must still use the format required by the program.

## Actual example assets

These are existing repository outputs for the fictional **PILLY** concept, not measured customer results:

| TAM / SAM / SOM | Competitive positioning |
| --- | --- |
| ![PILLY market-size diagram](examples/visuals/pilly_tam_sam_som.png) | ![PILLY positioning map](examples/visuals/pilly_positioning.png) |

- **PILLY**, an AI medication-management pillbox: [example plan](examples/예시-사업계획서-PILLY.md) · [review report](examples/예시-검토리포트-PILLY.md).
- **Re:Shell**, an oyster-shell deicer: [example plan](examples/예시-사업계획서-리쉘-굴패각제설제.md) · [review report](examples/예시-검토리포트-리쉘-굴패각제설제.md).
- [Visual reproduction scripts](examples/visuals/) and the [master PSST prompt document](docs/psst.md).

These Korean-language examples demonstrate output structure. They are not controlled Claude-versus-Codex benchmarks or evidence of application success.

## Adding templates and reference plans

This repository is **public**. Commit only material that may be redistributed.

| Material | Location | Committed |
| --- | --- | --- |
| Redistributable presentation templates (.pptx/.potx) | `skills/bizplan-slides/assets/templates/` with a same-name `.md` note | Yes |
| School/agency-mandated, paid, or branded templates | `skills/bizplan-slides/assets/templates/local/` | No (gitignored; used by local installs) |
| Original winning plans (PDF/HWP) | `자료/` or a private repository | No (gitignored) |
| Anonymized writing patterns / review lessons | `skills/bizplan/references/award-patterns.md`, `skills/bizplan-review/references/cases/` | Yes |

## Program rubrics

`skills/bizplan-review/references/rubrics.md` collects evaluation stages, criteria, cut-off scores, bonus points, page limits, and blind-review rules for ten 2026 Korean startup programs, each tagged with its verification level. The original announcement files could not be downloaded in the research environment, so the entries are provisional, based on search-index excerpts; most per-item point values were absent or unconfirmed. A supplied official announcement always takes precedence.

## Tools and verification

The core package contains Markdown instructions and optional Python scripts (form reading, table checks, DOCX/HWPX export, charts, PPTX template filling, PDF export). It does not include an API key, install external services, or grant tool access. Use the capabilities and permissions available in your agent environment:

- Web research requires browsing access or supplied source materials.
- Python charts require Python, relevant libraries, and a Korean font.
- DOCX export uses `python-docx` (Pandoc optional); HWPX/HWP export and reading use `python-hwpx`; spreadsheet checks use `openpyxl`.
- PPTX template filling uses `python-pptx`; PDF export uses LibreOffice (PPTX/DOCX) or Node + Playwright (HTML); previews use `pdftoppm`.
- HWPX files are structurally validated only; open them once in Hancom Office to confirm layout.
- If a tool is unavailable, the skill should state what remains unverified and request the missing material instead of claiming completion.

Run the offline installation smoke test:

```bash
python scripts/check_installation.py
```

It checks all 17 skill folders, exact resource copying, existing-installation protection, and source/destination overlap protection in temporary directories. It does **not** run either model, measure skill discovery, or establish output quality, speed, or cost. The [evaluation guide](evals/README.md) separates installation checks, trigger tests, and controlled quality comparisons.

The ZIP files named `dist/*v0.4.0.zip` are earlier distribution artifacts. Install from the current checkout to use the Codex documentation and changes described here.

## Before submitting a plan

- Verify market statistics and material claims against original sources.
- Distinguish facts, assumptions, examples, and planned evidence collection.
- Do not invent team experience, sales, partnerships, certifications, or test results.
- Follow the supplied application form, section order, length limits, and official budget rules.
- Use anonymized school/employer details unless the official form requires names or affiliations.
- For student teams, write deeply where supporting evidence exists; identify missing evidence and how it will be obtained elsewhere.
