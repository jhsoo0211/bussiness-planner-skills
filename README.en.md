# bizplan — Korean PSST business-plan skills

[한국어](README.md) | [English](README.en.md)

15 skills for drafting, reviewing, and presenting business plans for **Korean government startup-support programs**. Claude Code and Codex use the same `skills/` source.

## Scope: designed for Korean PSST applications

The workflow follows **PSST: Problem · Solution · Scale-up · Team**, commonly used in Korean startup business-plan applications:

| Section | Focus |
| --- | --- |
| Problem — 문제 인식 | Customer problems, background, and need |
| Solution — 실현 가능성 | Feasibility, implementation, and evidence |
| Scale-up — 성장 전략 | Business model, market entry, and growth |
| Team — 팀 구성 | Founder capabilities, team, and partners |

The intended context includes 예비창업패키지, 청년창업사관학교, U300, 로컬크리에이터, and 수출바우처. Their requirements differ: the current official announcement, application form, and scoring rubric take precedence over the default PSST outline. Example budgets and schedules in the skills are illustrative, not current program rules.

**This is an English usage guide. The skill instructions, default interaction, and examples remain Korean.** It does not establish an English-localized workflow or suitability for non-Korean funding programs. Investor decks and other proposals require adaptation to their own audience and requirements.

## Skills

| Skill | Use it for |
| --- | --- |
| `bizplan` | Choosing the right workflow and gathering application requirements |
| `bizplan-quick` | A full PSST draft from five inputs: industry, target, features, differentiation, weaknesses |
| `bizplan-item` | Refining an idea, customer, problem, and value proposition |
| `bizplan-problem` | Framing the problem and need with SPIN |
| `bizplan-research` | Market size, customer research, and competitor comparisons |
| `bizplan-solution` | Implementation, budget, and schedule planning |
| `bizplan-growth` | Business model, marketing, SWOT, and growth strategy |
| `bizplan-team` | Founder capabilities, team, and partners |
| `bizplan-summary` | An executive summary, naming, and brand story |
| `bizplan-visual` | Evidence visuals, charts, positioning maps, and image prompts |
| `bizplan-review` | Reviewing a draft against the rubric, checking claims, and anticipating questions |
| `bizplan-pitch` | Presentation flow, storytelling, scripts, and Q&A |
| `bizplan-slides` | Producing and checking 16:9 HTML slides |
| `bizplan-export` | Export-voucher plans and target-market analysis |
| `bizplan-analyze` | Comparing completed plans and extracting reusable writing patterns |

## Install for Codex

Prerequisites: Git, Python 3, and a working Codex environment. On Windows, use `py` instead of `python` if that is your Python launcher.

```bash
git clone https://github.com/jhsoo0211/bussiness-planner-skills.git
cd bussiness-planner-skills
python scripts/install_skills.py --agent codex
```

This copies all 15 skill folders, including their references and scripts, into `~/.agents/skills/`. It **stops before copying if any target skill already exists**. To update an installation, back up any local edits and move the old target skill folders out of the installation location before running the installer again. Avoid duplicate installations in multiple skill locations.

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
$bizplan-review 이 초안을 제공한 배점표로 검토해줘.
```

The first prompt asks to start an application and review its announcement; the second asks to review a draft against a supplied rubric. The examples intentionally use Korean.

Check that `bizplan/references/common-rules.md` is present after installation. The other skills refer to this shared document, so install the full set together. Codex uses the same source instructions as Claude Code; there is no separate prompt copy or permanent Codex fork to keep synchronized.

## Install for Claude Code

From the cloned repository:

```bash
python scripts/install_skills.py --agent claude
```

This installs into `~/.claude/skills/`. Restart Claude Code, then use `/bizplan` or a natural-language request.

The existing Claude Code marketplace installation is also available:

```text
/plugin marketplace add jhsoo0211/bussiness-planner-skills
/plugin install bizplan@business-planner-skills
```

These `/plugin` commands are **for Claude Code**. Use the local installation above for Codex. For a Claude marketplace installation, use `/plugin marketplace update` to update the marketplace.

## A typical workflow

1. Provide your idea and, when available, the official announcement, application form, and scoring rubric.
2. `bizplan` checks the target program, working mode, and output format. Choose a quick draft, a step-by-step workflow with research, or a specific section. Existing answers are reused.
3. Draft the plan. `bizplan-quick` asks for five core inputs and produces a PSST outline with a problem-to-solution consistency check. Illustrative data must remain labeled as unverified.
4. Use `bizplan-review` to identify weak claims, missing evidence, inconsistencies, and likely reviewer questions. Its scores are feedback, not an official assessment or funding prediction.
5. If presentation review is required, use `bizplan-pitch` for the narrative and Q&A, then `bizplan-slides` for HTML slides.

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

## Tools and verification

The core package contains Markdown instructions and optional Python chart templates. It does not include an API key, install external services, or grant tool access. Use the capabilities and permissions available in your agent environment:

- Web research requires browsing access or supplied source materials.
- Python charts require Python, relevant libraries, and a Korean font.
- DOCX conversion requires a document tool such as Pandoc or `python-docx`.
- HTML slide review requires an appropriate renderer/browser for visual checks.
- If a tool is unavailable, the skill should state what remains unverified and request the missing material instead of claiming completion.

Run the offline installation smoke test:

```bash
python scripts/check_installation.py
```

It checks all 15 skill folders, exact resource copying, existing-installation protection, and source/destination overlap protection in temporary directories. It does **not** run either model, measure skill discovery, or establish output quality, speed, or cost. The [evaluation guide](evals/README.md) separates installation checks, trigger tests, and controlled quality comparisons.

The ZIP files named `dist/*v0.4.0.zip` are earlier distribution artifacts. Install from the current checkout to use the Codex documentation and changes described here.

## Before submitting a plan

- Verify market statistics and material claims against original sources.
- Distinguish facts, assumptions, examples, and planned evidence collection.
- Do not invent team experience, sales, partnerships, certifications, or test results.
- Follow the supplied application form, section order, length limits, and official budget rules.
- Use anonymized school/employer details unless the official form requires names or affiliations.
- For student teams, write deeply where supporting evidence exists; identify missing evidence and how it will be obtained elsewhere.
