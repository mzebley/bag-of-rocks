# Coordinator guide

Covers project config, the hidden intended path, the tester packet, every run mode, and the regression rock library.

Contents: Project config · Intended path · Tester packet · Modes (fast, multi-persona, ablation, retest, regression) · Rock library · Budget

## Project config

Optional file at `.bag-of-rocks/config.yaml` in the project being tested:

```yaml
environments:
  staging:
    base_url: https://staging.example.test
    mutations: allowed          # default for this host
    prohibited: [live payments, outbound email to real addresses]
  production:
    base_url: https://example.com
    mutations: none             # always forced
default_preset: full-bag
presets: { }                    # see traits.md
design_system:
  inventory: ../design-system/components.json   # or a markdown list of components
rocks_dir: .bag-of-rocks/rocks
runs_dir: .bag-of-rocks/runs
```

The config never holds credentials. Reference account aliases; the operator supplies secrets at run time.

## Intended path (the hidden answer key)

Write this before the run. It captures what the design expects, so the review can find where reality split from intent.

```yaml
goal: Change mailing address to 12 Elm St.
verification: Profile page shows 12 Elm St. as mailing address after reload.
steps:
  - id: I1
    screen: Dashboard
    intended_cue: "Account" item in top nav
    intended_action: open Account
  - id: I2
    screen: Account
    intended_cue: "Edit" link beside Mailing address
    intended_action: open address editor
  - id: I3
    screen: Address editor
    intended_cue: Save button; hint says ZIP+4 optional
    intended_action: enter address, Save
  - id: I4
    screen: Account
    intended_cue: Updated address shown with "Saved" banner
    intended_action: none (goal met)
assumptions:
  - User notices the Edit link even though it is styled as body text.
```

The `assumptions` list is the most valuable part. If the goal or scope changes between runs, update the path and get it reconfirmed; record whether it was. Every assumption the design makes about what users will notice or read is a candidate blind spot; the run tests them without the tester knowing they exist.

If the user doesn't supply a path, draft one from the design, the code, or a quick expert walkthrough, then ask the user to confirm it. Because drafting it contaminates the current context, the tester must run in a fresh context.

Store the intended path in the run folder under `coordinator/`, never anywhere the tester can read.

## Run parameters and the tester packet

The coordinator writes `run-params.yaml` in the run folder, then builds the packet with the script. Never hand-write or paraphrase a packet.

```yaml
run_id: run-2026-10-27-c
skill_dir: ~/.codex/skills/bag-of-rocks      # where SKILL.md lives
goal: Determine whether Example Organization 1, 2, or 3 had staffing-related issues.
start_url: http://localhost:4200/
account: local-tester                        # alias only, never credentials
preset: full-bag
traits_add: []
traits_remove: []
fc_intensity: 3
phrasing: own-words                          # or: {fixed: "exact text"}
mutations: allowed
allowed_effects: Create and run a test analysis on the three named records.
prohibited_effects:
  - Deleting or editing source records
  - Outbound messages, payments, permission changes, production
user_facts: []                               # facts this user would know, e.g. their new address
device: Existing desktop viewport
budget: {actions: 45, minutes: 25}
output_dir: /abs/path/.bag-of-rocks/runs/run-2026-10-27-c/tester
inherited_state: "Analysis X pinned by run-2026-10-27-c"   # coordinator-only; never sent to the tester
```

Run `python scripts/build_packet.py run-params.yaml`. It assembles, verbatim: a run block from these parameters, the Phase 1 section of SKILL.md, the active trait cards, and the trace schema. It writes `tester-packet.txt` and `tester-packet.sha256` next to the params file and prints neutrality warnings.

Resolve every warning before spawning. Then send the packet file's contents unchanged as the tester's entire instruction, and save the dispatch metadata (agent ID, fork settings, time) to `tester-dispatch.json`.

Neutrality rules the script can't fully check:

- No intended path, assumptions, prior findings, suspected defects, expected labels, or baseline/candidate labels.
- No rules derived from earlier runs. If a previous run showed the persona needs different behavior, change a trait card or a parameter (versioned and visible), not the packet text.
- No incidental facts the user wouldn't know (dataset sizes, internal names) unless they're genuinely part of the user's knowledge, in which case put them in `user_facts`.
- Keep every safety constraint. Never remove one to improve blindness. If something visible discloses what's being tested, note it as a blinding limit.

## Modes

### Fast (default)
One fresh tester, full-bag or the requested traits, one attempt, then review.

### Multi-persona
Run two to four different presets or trait mixes against the same goal and equivalent starting state, each in its own fresh context and its own account or reset fixture. Never run testers concurrently against shared mutable data. Compare divergence points across runs: a blind spot that appears under several trait mixes is stronger evidence than one that appears once. Runs are scenario permutations, not separate people, and agents fail in correlated ways.

### Ablation (trait or phrasing attribution)
Purpose: learn which trait, or which wording, exposes which blind spot. Change exactly one variable per run: one trait, or `phrasing` switched to a `fixed` alternative. If anything else differs (scope, budget, packet text), it's a comparison, not an ablation.
1. Run the baseline preset.
2. For each finding worth attributing, rerun with one suspected trait removed, same goal, conditions, and equivalent state.
3. If the finding disappears with the trait off and appears with it on, record: "In these runs, [finding] depended on [trait]." If it persists, the trait wasn't the driver.
4. Translate the attribution into a design implication. Example: disappears without Helper-Text Skipper → the information needed to succeed lives only in helper text; move it into the label, control, or error.
Keep ablations small: one trait removed per run, only for findings that matter. Each run costs a fresh tester.

### Sweeps (several tasks in a row)
Different goals run back to back are a sweep, not a comparison. Reset state between runs when possible; otherwise record `inherited_state` for each run and note in the review where inherited state shaped the route (for example, a pinned item created by an earlier run becoming the next run's entry point).

### Retest (after a fix)
1. Freeze the baseline run: trace, evidence, state, preset, conditions, revision.
2. Record the actual change and revision once someone authorized implements it. Note unrelated changes as confounds. A proposed fix is not authorization to apply one.
3. Match goal, preset, conditions, entry point, account permissions, and starting data.
4. Run a new fresh tester with the same sanitized packet. Never reuse the baseline tester.
5. Compare outcome, divergence points, and recovery cost. If the new run never reached the original problem area, mark the original finding **not exercised**. Conclude "improvement supported in these runs", "persists", "regressed", or "inconclusive". One clean run doesn't prove a general fix.

### Regression
Rerun saved rocks from the library (below) after a change. Each rock runs as a fresh blind tester with its stored goal, traits, conditions, and mutation setting, and is reviewed against its stored intended path and original finding.

## Rock library

A rock is a saved blind spot. Save every evidence-backed finding as a `candidate` rock. Promote it to `open` when someone intends to fix it. Hypotheses that the evidence doesn't support aren't saved.

`rocks/<id>.yaml`:

```yaml
id: rock-0007
title: Submit stays enabled during processing; duplicate requests
status: candidate | open | fixed-unverified | fixed-verified | regressed | retired
created: 2026-10-27
source_run: run-2026-10-27-a
goal: Submit a dispute form with one attachment.
start: /disputes/new
preset: full-bag
traits: [FC:3]                  # traits shown necessary by ablation, if known
conditions: [slow-network]
mutations: allowed
intended_path: coordinator/intended-path.yaml   # copied with the rock, never sent to tester
finding:
  category: breakage
  evidence: [E7, E8, C5]
  component: Button (loading state)
pass_condition: Single submission recorded; visible processing state appears before any repeat click is possible.
watch_for: Button disabled before validation errors render, trapping the user.
triggers:
  components: [Button]
  paths: [/disputes/*]
history:
  - run: run-2026-10-27-a
    result: reproduced
```

Rerun a rock when a component in its `triggers` changes, when a fix ships, or on a scheduled sweep. Update `status` and append to `history`; never rewrite earlier history entries. Retire a rock only when the flow it covers no longer exists.

Rocks in the library also serve as known-answer cases for calibration (see `calibration.md`).

## Budget

Agree on a run budget before multi-persona, ablation, or regression sweeps. Count every launched tester, including blocked or abandoned starts. Stop at the budget and report; get scope before going further.
