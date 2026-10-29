# Trace, review, and report

Contents: Trace (tester) · Run data for the filmstrip · Outcome rubric · Divergence analysis · Component mapping · Report template · Errata

## Trace (tester)

The section between the TRACE markers is copied verbatim into the tester packet.

<!-- TRACE:START -->
Save `trace.json` in your output folder and screenshots in `shots/`. Write each step only after you've seen its result (see the action loop). Record only what you actually observed. Don't revise earlier steps; if you realize one was wrong, add a `correction` step that says so.

```json
{
  "header": {
    "run_id": "", "goal": "", "start": "", "preset": "", "traits": [],
    "phrasing": "own-words | fixed", "mutations": "allowed | none",
    "viewport": {"width": 0, "height": 0},
    "perception": "screenshots | mixed | text",
    "perception_note": "e.g. tool returned accessibility text automatically on tab creation",
    "started_at": ""
  },
  "steps": [
    {
      "id": "C1",
      "kind": "checkpoint | wait | correction",
      "at": "ISO time",
      "screenshot": "shots/C1.jpg",
      "result_screenshot": "shots/C1-result.jpg",
      "cue": "what you saw that drove the action",
      "expectation": "one line, written before acting",
      "action": "what you did",
      "entered_text": "exact text typed, if any",
      "clicks": [ { "px": [0, 0], "approx": false, "n": 1 } ],
      "result": "what visibly happened",
      "updated": "what you now expect",
      "traits": ["VPF"],
      "ignored": [ { "box_px": [0, 0, 0, 0], "label": "" } ],
      "busy": false
    }
  ],
  "end": {
    "belief": "what you believe about your goal",
    "supporting_cue": "",
    "stop_reason": "believed complete | blocked | abandoned (patience) | abandoned (stall) | budget | permission stop",
    "pending_effects": "",
    "untested": [],
    "screenshot": "", "ended_at": ""
  }
}
```

- `clicks[].px` are pixel coordinates on that step's `screenshot`. Set `approx: true` if the action went through an accessibility-tree target instead of a pixel. `n` above 1 means repeated clicks.
- Every checkpoint with an action needs a `result_screenshot`. `result` must describe what that screenshot shows, never "pending".
- `kind: "correction"` steps fix an earlier step by ID without editing it: `{"kind":"correction","corrects":"C5","note":"..."}`.
- `kind: "wait"` steps record a screenshot while something is busy, with no action.
- `ignored[].box_px` is `[x, y, width, height]` in pixels on the same screenshot.
- `traits` holds at most two tags, or `["ordinary"]`.
<!-- TRACE:END -->

The reviewer generates the readable trace and the filmstrip data with `scripts/trace_to_run.py`; the tester writes only `trace.json` and screenshots.

## Run data for the filmstrip

The reviewer converts the frozen trace into the filmstrip's `RUN` object. Pixel coordinates become percentages of the screenshot's decoded dimensions (check the real format; don't assume PNG headers).

```json
{
  "run": { "id": "", "date": "", "goal": "", "start": "", "preset": "", "traits": [], "phrasing": "", "entered_text": "", "mutations": "", "conditions": [], "perception": "", "mode": "", "skill_version": "0.5.0" },
  "outcome": { "believed": "", "supported": "", "gap": "" },
  "summary": [ { "finding": "F1", "headline": "", "step": "C3" } ],
  "intended": [ { "id": "I1", "screen": "", "cue": "", "action": "" } ],
  "steps": [
    {
      "id": "C1", "kind": "checkpoint | wait | reviewer",
      "screenshot": "", "result_screenshot": "",
      "cue": "", "expectation": "", "action": "", "entered_text": "", "result": "", "updated": "",
      "traits": [], "clicks": [ { "x": 0, "y": 0, "n": 1, "approx": false } ],
      "ignored": [ { "x": 0, "y": 0, "w": 0, "h": 0, "label": "" } ],
      "divergence": { "from": "I1", "kind": "recovered|unrecovered|alternate", "note": "" },
      "harness_note": "", "untested": false
    }
  ],
  "findings": [ { "id": "", "source": "rock-exposed | reviewer-observed", "recurs_in": [], "category": "", "title": "", "steps": [], "traits": [], "component": "", "component_basis": "inferred | reproduced", "expected": "", "observed": "", "cost": "", "fix": "", "fix_signal": "", "regression_risk": "", "ablation": "" } ],
  "errata": [ { "date": "", "about": "", "correction": "" } ],
  "limits": []
}
```

Steps with `kind: "reviewer"` (an end card, a summary card) render with a "Reviewer-added" label so they're never mistaken for tester checkpoints.

## Outcome rubric

- A generic acknowledgment proves acknowledgment, not the goal. Without evidence that the right target reached the intended state: **uncertain**, or **partial** if a real intermediate result exists.
- A visible, task-specific confirmation of the right target and state supports **completed (UI-observed)**.
- Claim backend effects only with separately obtained, authorized verification. Name the method; append it.
- **Blocked** = couldn't progress. **Not tested** = permission, tooling, or mutation stop. A stall abandonment is a real outcome; check afterward whether the process finished and report both facts.

## Divergence analysis

| Intended step | Intended cue | Rock's checkpoints | What the rock did instead | Kind | Cost | Assumption tested |
| --- | --- | --- | --- | --- | --- | --- |

Kinds: **alternate** (different route, still worked), **recovered** (got back on track; record the cost), **unrecovered**. Mark every intended-path assumption held, failed, or not exercised.

## Product signal vs. harness artifact

Before writing a finding, ask whether a real user could hit it.

- **Harness artifacts:** stale-frame misclicks, tool latency, accessibility-target misplacement, mislabeled traits, packet leaks. Report them in Limits, not Findings.
- **Product signals:** misleading labels, missing feedback, unexplained stalls, hidden alternatives.
- **Both:** a click that missed because the element moved might be a stale frame, a real layout shift, or both. Report what's established and name the reproduction that would separate them.

## Component mapping

Tag a component only when evidence points at a reusable part. Mark `component_basis: inferred` unless a controlled reproduction was done. Maintain `.bag-of-rocks/component-ledger.md`:

| Component / state | Findings (run IDs) | Source | Traits | Flows affected | Basis | Status |
| --- | --- | --- | --- | --- | --- |

Copy and page-level hierarchy problems often aren't component problems; say so.

## Report template

Use the Evidence ledger hierarchy in generated reports: a goal heading, a compact run header, and one section per finding with its stable ID. Keep observations, interpretation, and proposed fixes separate. HTML uses the system-font styles in `assets/filmstrip.html`; Markdown keeps the same hierarchy with headings, code-formatted IDs, and labeled paragraphs. Avoid decorative cards, nested badges, and wide tables for prose. Screenshots keep their original aspect ratio; before/after pairs stack on narrow screens.

```markdown
# Bag of Rocks: <goal>

Run: `<run ID>` · Skill: `<version>` · Preset: `<preset>`

## In 90 seconds

**Rock believed:** <belief>

**Evidence supports:** <outcome and supporting evidence>

**Gap:** <difference, or none noted>

<The findings the evidence supports, most costly first. No quota. One sentence each, with step, trait, smallest fix.>

## Findings

### `<finding ID>` · <title>

<category> · <rock-exposed / reviewer-observed> · <candidate / open>

**Evidence:** <linked checkpoints and screenshots; intended step>

**Expected:** <expected behavior>

**Observed:** <what happened>

**Cost:** <consequence>

**Traits:** <traits that contributed>

**Component:** <component and inferred / reproduced basis>

**Interpretation:** <explanation and alternatives>

**Smallest fix:** <proposed change>

**Success signal:** <observable result after the fix>

**Watch for:** <regression risk>

**Ablation:** <one-variable test>

<Repeat the finding section as needed.>

## Recurrence
Patterns also seen in other runs (run IDs), and recurring harness artifacts that need a deterministic check.

## Phrasing
Text the rock entered, and whether it plausibly shaped the outcome (hypothesis unless a phrasing ablation was run).

## Assumptions tested
Each: held | failed | not exercised.

## Ablation candidates
Trait or phrasing changes worth running next, and what each would show.

## Limits
- Blindness: context, packet hash, file access, perception exposure.
- Inherited state from earlier runs, or the reset performed.
- Trace problems reported by trace_to_run.py.
- Conditions applied or not applied; untested commits; state mismatches; cleanup.
- Harness artifacts observed.
- Calibration status (exact wording from SKILL.md).
- This is a synthetic run: it generates hypotheses about blind spots, not evidence of how many real users would fail.

## Errata
Append-only. Date, what's corrected, the evidence. Never edit earlier sections.

## Appendix
Run header, packet hash, evidence index, trace, divergence table, verification.
```

For multi-run modes, add a comparison: run IDs, what matched and what differed (preset, phrasing, conditions, packet differences), outcomes, divergences, recovery costs, and conclusions with limits. If more than one variable changed between runs, it isn't an ablation; say so.
