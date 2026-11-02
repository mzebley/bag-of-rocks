# Changelog

## Unreleased

- **Automated releases.** Pushing a `v*` tag verifies the release, publishes to npm through trusted publishing, and creates the GitHub release with a Codex submission ZIP attached. CI runs tests and strict plugin validation on every push and pull request. See `docs/release.md`.
- `tools/release.py` checks that a tag matches every version field and the changelog, writes release notes, and builds the Codex ZIP.
- Codex listing fields now fit the directory limits: a shorter `shortDescription` and three example prompts. Tests enforce the limits.

## 0.7.0 (2026-11-02)

Packaging only: tester packets are unchanged.

- **Plugin install for Claude Code and Codex.** The repository is now a plugin and its own marketplace for both agents. Add `mzebley/bag-of-rocks` as a marketplace (named `mzebley`) and install `bag-of-rocks@mzebley`; updates arrive when `version` changes. Manifests: `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` for Claude Code, `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` for Codex.
- **Skill moved to `skills/bag-of-rocks/`** with its references, scripts, assets, and fixtures, because Codex loads plugin skills only from `skills/<name>/SKILL.md`. Paths inside the skill are unchanged relative to its folder; repository commands now start with `skills/bag-of-rocks/`. Anyone copying files by hand should copy that folder.
- `skills/bag-of-rocks/` remains a plain Agent Skills folder for other agents and the skills CLI.
- A test fails when the version in `package.json`, SKILL.md, and both plugin manifests disagree.

## 0.6.0 (2026-11-02)

Evidence: audit probes on 2026-10-31. Leaky `run_id`, fixed phrasing, and `prohibited_effects` passed `--strict`; a production URL kept `mutations: allowed`; `FC:5` presets built with intensity 3; YAML intended paths were ignored; mismatched trace headers converted silently.

Tester packets change: Phase 1 reading, dropdown, and settle-check guidance, the Helper-Text Skipper limit, and the trace schema (`click_space`). Packets built with 0.6.0 differ from 0.5.0 packets, so compare runs across versions as different conditions.

### Packet builder
- Lints every tester-visible field, including `run_id` (flags design words like `retest` or `baseline`), account, device, fixed phrasing, prohibited effects, and custom preset names. Adds a navigation-hint pattern.
- Warns when a quoted label from `coordinator/intended-path.*` appears in a tester-visible field.
- Reads `.bag-of-rocks/config.yaml`: `default_preset`, `presets`, and `environments` (merges `prohibited`, applies `mutations: none`).
- Forces `mutations: none` on hosts that don't look like dev or staging and aren't declared in the config.
- Keeps `FC:N` intensity from presets and `traits_add`; explicit `fc_intensity` wins.
- Warns when Thumb Reacher runs without a phone viewport.
- Writes `tester-packet.json` with the effective settings and hash.
- Lists instruction files a tester would load (`CLAUDE.md`, `AGENTS.md`) and warns when the run folder is inside the working directory. Ambient context is a fifth blindness dimension in SKILL.md.

### Trace converter
- Writes `tester.sha256` on first conversion and reports later drift. Verifies the packet hash and records it as `run.packet_sha256`.
- Compares the trace header (goal, start, preset, traits, mutations, phrasing, run ID) with the packet settings.
- Flags trait tags that weren't active, `ordinary` mixed with traits, unknown stop reasons, actions without before or result screenshots, and wait steps without screenshots.
- Reads YAML or JSON intended paths with either key style, and carries `assumptions` into `run.json`.
- `header.click_space: viewport` converts page-coordinate clicks correctly on high-density screenshots; a viewport/screenshot scale mismatch is reported.
- `--force` keeps reviewer-written fields instead of discarding them.
- Carries ambient instruction files and a run folder inside the working directory into Limits.
- Missing phrasing defaults to `own-words`, not `fixed`. Screenshot paths outside `tester/` are rejected.

### Persona
- **Phase 1 "Reading" no longer restates Helper-Text Skipper.** Previous: "Read headings, button and link labels, field labels, error messages, and the answer or result you came for. Don't read instructions, descriptions, hints, or explanatory paragraphs unless your traits say you would." Now: "Read what this person would naturally read on the way to their goal; your traits may narrow that." Evidence: in run-2026-10-31-d (hint-only-format fixture, HTS removed), the tester still skipped a legible date hint and tagged it `ordinary`; removing the card also removed its read-after-two-failures limit. HTS ablations were impossible under the old wording. After the change, both HTS-off testers (run-2026-11-01-a, -b) read the hint and entered `2026-11-20` on the first try; with HTS on (run-2026-10-31-a to -c), 0 of 3 did. Descriptive only: 5 runs on one fixture.

- **Helper-Text Skipper limit:** previous "read the helper text for a field or step after it has failed twice." Now: read it after one failure whose visible error points at that field or step. Evidence: in run-2026-10-31-a to -c, Low Patience abandoned at the second failure, the same moment the old limit unlocked, so HTS never recovered in full-bag.
- **Phase 1:** native dropdowns and pickers that don't render in screenshots are chosen through the accessibility tree (`approx: true`) and don't count as failed attempts. Evidence: all six leak-test runs; run-2026-11-01-a abandoned on the dropdown alone.
- **Phase 1 settle check:** an unchanged result screenshot gets a second screenshot about a second later before counting as no change. Evidence: stale frames in 4 of 6 leak-test runs, including a false fidget in run-2026-11-01-b.

### Calibration fixtures
- Added the rock garden in `fixtures/`: seven planted-blind-spot pages, intended paths, and `new_run.py`. See `fixtures/README.md`.
- `decoy-primary` and `clean-control` goals say "Reserve" instead of "Book the Oak Room", which matched the form's submit label and was flagged by the answer-key check.

### Output
- Filmstrip shows an "Assumptions tested" section.
- SKILL.md states that the tester's browser tool must save screenshots as files, and that the skill needs a rendered URL.

## 0.5.0 (2026-10-28)

- Prepared public npm distribution as `bag-of-rocks`, with explicit package contents and archive installation guidance.

- Applied the Evidence ledger layout to filmstrips, report templates, and readable traces: system fonts, monospace evidence IDs, restrained dividers, responsive screenshots, and print styling.
- Filmstrips omit tester verdicts and export/reset controls by default. Generate with `--filmstrip --calibration` to enable tester calibration.
- Replaced verdict choices with Plausible, Too expert, Overplayed confusion, and Unmotivated action. Saved verdicts use a new browser storage key; previous labels and stored verdicts are not migrated. Historical changelog entries retain their original wording.

## Public distribution of 0.4.1 (2026-10-28)

- Imported installed 0.4.1, including its recorded 0.3.0–0.4.1 history. No earlier history reconstructed.
- Anonymized development app and organization names in this changelog and the coordinator example. Dates, run IDs, and historical observations are retained as recorded claims, not newly verified results.
- Added README, provenance, overlap research, release checklist, JSON example, and offline harness regression tests.
- Added the MIT license after the author confirmed ownership and approved the license.
- Added a private npm packaging draft with an explicit file allowlist; no runtime dependencies or install hooks. GitHub is the initial distribution channel; npm remains unpublished.
- Clarified the use case: a deliberately uncoached, goal-driven persona and a chronological evidence report. Related academic research is not classified as a direct competitor solely for using simulated users.


## 0.4.1 (2026-10-27)

Evidence: three-task sweep under 0.4.0 (run-2026-10-27-c, -d, -e). Packet builder, fresh contexts, and hashing worked as designed. Reviewer judgment on run e: accepting a 49% "Yes" without opening Review is plausible and exposed a real issue the team is now fixing, so the 0.4.0 results rule in Helper-Text Skipper stays unchanged. Calibration status: `reviewer verdicts only (28 steps, 2026-10-27)`, plus that one reviewer judgment.

### Persona and action loop
- **Strict action loop:** screenshot, decide, act on that frame, result screenshot, then write the step. No pending results; no results written into the next step. Evidence: run c recorded results one step late; run e's C2 click aimed at a stale position.
- **Fidget Clicker precondition:** a repeat only counts if the screenshot right before it still shows the busy or unchanged state. Evidence: run e C6 claimed a fidget while its screenshot already showed the loaded table.
- **Tester corrections** are new `correction` steps, never edits.
- **`mutations: none` defined:** deliberate saves, submits, confirms, pins, deletes, sends, and auto-saving typed input are commits; incidental system writes (recent history, view logs) are allowed and noted. Evidence: run d's uncertainty about history writes. The packet builder now sends this definition.

### Harness
- **`scripts/trace_to_run.py`** (new): reads the frozen trace, detects real image formats and sizes from bytes, converts pixel clicks and ignored boxes to percentages, renders `trace-readable.md`, writes a `run.json` skeleton, reports trace problems and reviewer checks, and embeds `run.json` into the filmstrip with `--filmstrip`. Evidence: JPEG-as-PNG files in runs a, b, and d; missing readable trace in run c.
- The tester now writes only `trace.json` and screenshots; the extension requirement is dropped because the converter reads the real format.
- **State between runs:** reset or record `inherited_state` (coordinator-only). New "Sweeps" guidance. Evidence: run c's pin became run d's route.

### Review and output
- Findings carry a **source** (rock-exposed or reviewer-observed). Evidence: run c's "Unnamed item" finding was spotted by the reviewer, not encountered by the rock.
- New **Recurrence** step and report section. Recurring harness artifacts on the same element get a deterministic timed-screenshot check. Evidence: the Example Organization chip was missed in runs a, b, and e; the single-record selection detour occurred in both narrowing tasks (b, e).
- Component ledger gains a Source column.
- Filmstrip shows finding source, recurrence, tester corrections, notes, and inherited state.

## 0.4.0 (2026-10-27)

Evidence: two Codex runs against a local development app (run-2026-10-27-a, run-2026-10-27-b), Codex's execution note and errata, and reviewer verdicts (28 steps: 27 plausible, 1 too smart). Calibration status after this release: `reviewer verdicts only (28 steps, 2026-10-27)`.

### Persona
- **Waiting model.** Busy states are recorded as wait checkpoints. Clicks during a busy state are fidgets, not failed attempts. A stall (no visible change past the budget) is a legitimate abandonment reason. Low Patience gets a ~30 s stall budget; off, 5 minutes per stage. Evidence: run a counted two busy-state clicks as failures, yet the reviewer marked the resulting abandonment plausible, so the behavior stays and the labeling changes.
- **Helper-Text Skipper / results.** Reads the headline answer; may open a detail view; reads at most its heading and first highlighted line; doesn't study evidence or weigh confidence. Previous: no rule for task content. Evidence: run b C15 marked too smart (read evidence passage, reasoned about 59% confidence).
- **Literalist.** Adds "100% means complete" and "a row per thing asked about is the answer for each thing."
- **Visual-Path Follower.** Takes the first option in a pager unless visibly wrong.
- **Fidget Clicker.** Corrective clicks after a miss are `ordinary`, not FC.
- **Nervous Retreater.** Being unsure about a result is not this trait.
- **`ordinary` tag** and a two-tag maximum. Evidence: Codex flagged decorative tags.
- **`patient-bag` preset** (full-bag minus Low Patience).

### Harness
- **`scripts/build_packet.py`** assembles the packet verbatim from marked sections, hashes it, and lints for neutrality. Evidence: v0.3 packets were paraphrased, and run b's carried a prior-run rule and a dataset count.
- **Blindness recorded as four dimensions:** context, packet, file access, perception exposure.
- **One frame, one decision;** clicks recorded in pixels with an `approx` flag for accessibility-tree targets. Evidence: run b C2 stale-frame miss; run a approximate markers unflagged.
- **Phrasing parameter** (`own-words` or `fixed`) and recorded entered text. Evidence: the rock's expanded question in run b, and the reviewer's hypothesis that wording drove the nine-step plan.
- **Screenshot extensions must match format.** Evidence: JPEG bytes saved as `.png`.

### Review and output
- No finding quota; merge causal chains into one finding.
- Product signal vs. harness artifact section.
- Ablation candidates per finding; ablations change exactly one variable.
- Component tags marked `inferred` or `reproduced`.
- Rocks: new `candidate` status; every evidence-backed finding is saved as a candidate.
- Append-only errata section in reports and filmstrips.
- Exact calibration-status wording.
- Filmstrip: verdicts persist in the browser, wait and reviewer-added cards, before/after screenshots, dashed markers for approximate clicks, entered text shown, harness notes.

## 0.3.0 (2026-10-27)
Preset plus traits, mutation switch, hidden intended path, filmstrip, conditions, ablation, component mapping, regression rocks, calibration against fixtures and verdicts.
