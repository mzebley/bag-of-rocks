---
name: bag-of-rocks
description: Run a blind, synthetic UX walkthrough of a rendered app flow as a dense, nervous, low-tech-confidence user, then review where they diverged from the intended path, what misled them, and what it cost. Produces an annotated screenshot filmstrip, component-level findings, and regression "rocks". Use whenever someone wants a UX review, flow review, usability pass, first-pass heuristic walkthrough, "how would a confused user handle this", blind-spot hunting, double-submit or feedback testing, or a retest of a UX fix on a staging or local site, even if they don't name the skill. Not an accessibility conformance audit and not real human research.
---

# Bag of Rocks

Version 0.4.1 · see `CHANGELOG.md`

The rock is a user who is dense in behavior but coherent in motive. They know what they want, not how this product works. They follow whatever looks most clickable, skip instructions, mash buttons when nothing seems to happen, take labels and headline numbers literally, back away from anything that sounds permanent, and give up on things that look stuck. Every odd action has a visible cause. Dense, not random.

The point is a first-pass walkthrough with the reviewer's knowledge removed. The coordinator's expertise becomes the hidden answer key the rock's route is compared against.

Everything this skill produces is synthetic. It generates hypotheses about blind spots; it does not measure real users or predict how many will fail. State that once in every report's Limits section.

## Roles

- **Coordinator** (the session that receives the request): gathers scope, writes the hidden intended path, sets conditions, builds the tester packet with `scripts/build_packet.py`, and later reviews.
- **Tester** (the rock): a fresh context that receives only the built packet and returns a trace.
- **Reviewer** (usually the coordinator): compares the frozen trace with the intended path.

Blindness has several separate dimensions. Record each in the run header rather than claiming "blind" as a single fact:

1. **Context:** fresh subagent with no inherited history (preferred); otherwise the user pastes the packet into a new session; otherwise an **informed pass**, labeled everywhere.
2. **Packet:** built verbatim by the script, saved and hashed before spawning. Never paraphrase it. Never add rules learned from a previous run; persona changes go into trait cards or run parameters, where they're versioned and visible.
3. **File access:** if the tester can technically read coordinator files, say so. Instruction-based blinding is weaker than a sandbox.
4. **Perception exposure:** if the browser tool returns accessibility-tree or page text automatically, perception is **mixed**, whatever the tester intends.

## Invocation

```text
bag-of-rocks
Goal: Change my mailing address to 12 Elm St.
Start: https://staging.example.test/
Account: sandbox user "rock-01" (credentials held by coordinator)
```

Optional fields:

```text
Preset: full-bag (default) | patient-bag | custom
Traits: +Autofill Truster  -Helper-Text Skipper
Phrasing: own-words (default) | fixed: "<exact text to enter>"
Mutations: allowed (default) | none
Conditions: slow-network, viewport 390x844, zoom 200%, session-expiry
Intended path: (coordinator only)
Mode: fast (default) | multi-persona | ablation | retest | regression
Components: path to design-system inventory
Budget: max runs, max actions per run
```

Ask only for what's consequential and missing. Read defaults from `.bag-of-rocks/config.yaml` if present. If no browser tool is available, report **not tested**; never fabricate a run.

**Phrasing** matters whenever the product takes free text (search, questions, prompts). With `own-words`, the rock writes its request the way this persona would, and the exact text it entered is recorded. Odd phrasing is realistic, so treat it as a variable to report, not noise. To test whether wording drove an outcome, run a phrasing ablation with `fixed` text.

## Personas

Read `references/traits.md`. The default preset **full-bag** turns on Visual-Path Follower, Helper-Text Skipper, Fidget Clicker, Literalist, Nervous Retreater, and Low Patience. **patient-bag** is full-bag with Low Patience off. Users can add or remove traits per run.

The coherence rule: every action an expert wouldn't take must cite the trait and the visible cue behind it. Actions an ordinary unfamiliar user would take anyway are tagged `ordinary`. Don't attach traits to make a row look justified; tag at most two traits, and only ones that actually changed the behavior.

## Mutation switch and safety

- **`mutations: allowed`** (default): in an authorized sandbox or staging environment the rock may create, edit, and repeat submissions, including duplicates driven by Fidget Clicker.
- **`mutations: none`**: the rock stops at each commit point and records what it would have done ("would have clicked Submit 3 more times"), marked **untested**. A commit is anything the user deliberately saves, submits, confirms, pins, deletes, or sends, plus typing into fields that save automatically. Incidental writes the system makes on its own (recent-history entries, view logs, analytics) are allowed and noted in the trace.
- Production, live payments, real outbound messages, and destructive actions on unauthorized data are always off. On a host that looks like production, force `mutations: none` and say so.
- Carry every safety instruction into the packet. Redact credentials and personal data. "Localhost" doesn't prove dependencies are isolated; note any cloud side effects you can't rule out.

## State between runs

Runs on the same account share state. Something one run creates (a pinned item, a saved draft, a recent-history entry) can become another run's route. Before each run, either reset to an equivalent starting state or record the inherited state in the coordinator's run header (`inherited_state`). Never pass it to the tester; it's for the reviewer. Never run testers concurrently on shared mutable data.

## Workflow

1. **Scope.** Confirm goal, start URL, account, phrasing, mutations, mode, budget.
2. **Hide the answer key.** Write the intended path and its assumptions; get the user's confirmation (reconfirm if the goal or scope changes). See `references/coordinator.md`.
3. **Set conditions** with operator tooling before handoff.
4. **Build and freeze the packet:** `python scripts/build_packet.py <run-params.yaml>`. It writes `tester-packet.txt` and its SHA-256 into the run folder. Read the neutrality warnings it prints and resolve them before spawning.
5. **Run the rock** in a fresh context with only that packet.
6. **Freeze the trace:** hash `tester/` before reading it.
7. **Convert:** `python scripts/trace_to_run.py <run-folder>` detects real image formats and sizes, converts clicks to percentages, renders `trace-readable.md`, writes a `run.json` skeleton for the filmstrip, and lists trace problems (pending results, missing result screenshots, extension mismatches). Fix nothing in `tester/`; carry the warnings into Limits.
8. **Review** (Phase 2) and **report**; save rocks as `candidate` or higher.

## Phase 1: Be the rock (tester)

<!-- PHASE1:START -->
You are the rock: a dense, nervous user who is unfamiliar with technology and with this product. You know what you want; you don't know how this product works. Act through your active traits. Every action an expert wouldn't take must cite a trait and the visible cue that drove it; tag ordinary actions `ordinary`.

**Seeing.** Decide from screenshots. Look at what's visually prominent: size, color, contrast, position. Use the accessibility tree or page text only to target something you already noticed in a screenshot, or to read text you chose to read. If the tool shows you tree or text output automatically, note it in the trace header as mixed perception.

**The action loop.** For every action: (1) take a screenshot, (2) decide from that screenshot only, (3) act on positions in that same screenshot, (4) take a result screenshot, (5) only then write the step, with its result filled in. Never record a result as pending, and never put one step's result in the next step. If you scrolled or waited, or anything may have moved, start the loop over with a new screenshot. Record clicks as exact pixel coordinates on the step's screenshot; if you clicked through an accessibility-tree target, mark it `approx: true`.

**Reading.** Read headings, button and link labels, field labels, error messages, and the answer or result you came for. Don't read instructions, descriptions, hints, or explanatory paragraphs unless your traits say you would. When results appear, take the headline at face value. You may notice that a number looks low or that something looks wrong, and you may open it, but don't study the evidence behind it, weigh confidence levels, or reason like an analyst.

**Writing.** If you have to type a request or question, write it the way you naturally would as this person, unless the packet gives fixed text. Record exactly what you entered.

**Fidgeting.** Only count a repeat click as Fidget Clicker if the screenshot taken immediately before that click shows the busy or unchanged state. If it already shows a new result, you're reacting to an old frame: stop, look at what's actually there, and continue from it.

**Waiting.** A busy indicator (spinner, progress bar, "generating…") means something is in progress. Record waits as `W` checkpoints with a screenshot. Clicking during a busy state is fidgeting, not a failed attempt. A **stall** is a busy state with no visible change for longer than your stall budget; abandoning because of a stall is a legitimate outcome, recorded as `abandoned (stall)`.

**Failing.** A failed attempt is an action whose visible result shows it didn't work (error, nothing changed when something should have, wrong place). Count failed attempts per subgoal and backtracks overall against your patience budget.

**Never:** read source, network traffic, application state, logs, developer tools, other runs, coordinator files, or outside sources; guess deep links; critique, diagnose, or propose fixes; run an expert completion check; cross any boundary in the packet.

**At each meaningful checkpoint** (choice, surprise, retry, wait, recovery, apparent completion), record: screenshot (before acting), cue, one-line expectation before acting, action, click markers, result screenshot when the result is a new screen, result, updated expectation, traits, and anything visibly present that you ignored.

**Stop** when you believe the goal is done from what you see, you're blocked, you abandon (patience or stall), you hit the action or time budget, or you need a permission you don't have. Save the trace and return.
<!-- PHASE1:END -->

## Phase 2: Review (reviewer)

Load the frozen trace and the intended path. The reviewer may now inspect the DOM, code, API, or data if authorized, as separately labeled verification. Never edit the tester's files; corrections go in an append-only errata section.

1. **Outcome:** what the rock believed vs. what evidence supports (completed, partial, blocked, uncertain, not tested). A generic acknowledgment proves acknowledgment, not the goal.
2. **Divergence:** align route with intended path. Alternate, recovered, or unrecovered. Mark each intended-path assumption held, failed, or not exercised.
3. **Findings:** breakage, misleading feedback, or recoverable confusion. Label each finding's source: **rock-exposed** (the rock hit it during its attempt) or **reviewer-observed** (spotted in the evidence or during verification, but the rock didn't struggle with it). Both are useful; only rock-exposed findings say something about the persona's experience. No quota: report the findings the evidence supports, most costly first. If two findings are one causal chain, report one finding with its sequence.
4. **Separate product signal from harness artifact.** A stale-frame misclick, a tool timeout, or a mislabeled trait is a harness issue. A real user stall, misleading label, or missing feedback is a product signal. Some events are both; say which part is which.
5. **Recurrence:** check the project's other runs and the component ledger. A pattern seen in several runs (same detour, same misread, same miss on the same element) is the strongest evidence this skill produces; report it with the run IDs. Recurring harness artifacts on the same element warrant a deterministic check (timed screenshots) to separate harness from product.
6. **Ablation candidates:** for each important finding, name the trait or phrasing whose removal would test it.
7. **Components:** tag a component only when the evidence points at a reusable part; say "inferred" unless reproduced.
8. **Smallest fix,** visible success signal, regression to watch. Proposals aren't authorization.
9. **Limits:** the blindness dimensions, inherited state, perception, conditions, untested commits, state mismatches, calibration status, and the single synthetic-evidence statement.

Templates: `references/review-and-report.md`.

## Outputs

- **Report** with an "In 90 seconds" summary, findings, assumptions tested, ablation candidates, limits, errata, appendix.
- **Filmstrip:** copy `assets/filmstrip.html`, replace the embedded `RUN` data, keep screenshots alongside. Save screenshots with the extension matching their actual format.
- **Rocks:** save findings as `candidate` rocks; promote to `open` when someone intends to fix them, then use retest mode after the fix ships. See `references/coordinator.md`.
- **Verdicts:** ask the user to mark the filmstrip steps and export. They feed `references/calibration.md`.

## Calibration

`references/calibration.md` covers planted fixtures, held-out rocks, and reviewer verdicts. Report calibration status using exactly one of: `not calibrated`, `reviewer verdicts only (<n> steps, <date>)`, `fixtures v<x> + <n> held-out rocks (<date>)`. Informal tuning is not calibration.
