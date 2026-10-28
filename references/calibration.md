# Calibration

Calibration answers three questions about the rock itself, not about the product being tested:

1. **Sensitivity:** does it find blind spots that are known to be there?
2. **Restraint:** does it avoid inventing blind spots that aren't there?
3. **Fidelity:** does it behave like the persona its traits describe, no smarter and no dumber?

Without this, there's no way to tell whether a trait change improved the skill or just changed it. Run calibration when traits or presets change, when the skill version changes, and before relying on a new custom trait.

## Source 1: Planted fixtures (the rock garden)

A small staging site or set of pages with blind spots planted on purpose, each switchable on and off. One page per known pattern is enough:

| Fixture | Planted blind spot | Trait expected to expose it |
| --- | --- | --- |
| silent-submit | Submit takes 4s with no loading state and stays enabled | Fidget Clicker |
| hint-only-format | Date format required only in helper text | Helper-Text Skipper |
| decoy-primary | Big primary button does an unrelated action; real action is a text link | Visual-Path Follower |
| done-discards | "Done" closes the editor without saving | Literalist |
| scary-routine | Routine save labeled "Submit final record. This cannot be undone." | Nervous Retreater |
| dead-end | Wrong branch with no visible way back except browser Back | Low Patience |
| clean-control | The same flow with every blind spot fixed | none (restraint check) |

Run each fixture as a fresh blind tester with the full-bag preset, then with the expected trait removed. A well-calibrated rock:

- hits the planted blind spot with the trait on,
- misses it (or recovers cheaply) with the trait off,
- completes the clean control without reporting a defect.

Record results as observed counts per fixture and trait mix. Keep fixtures out of every tester packet; the tester must never know it's in the garden. A hostname like `rock-garden.test` is a blinding leak; use a neutral name.

## Source 2: Confirmed rocks as known answers

Every confirmed rock in the library is a known blind spot on a real product. While a rock is still `open`, rerunning it against the unfixed flow should reproduce it. When traits change, replay a held-out set of open rocks:

- Split rocks into a tuning set (used when adjusting traits) and a held-out set (never looked at while adjusting).
- After a trait change, run the held-out set blind and compare reproduction against the previous version.
- If the held-out set is small or has been used to tune before, report a descriptive comparison only, not a validated improvement.

## Source 3: Reviewer plausibility verdicts

The filmstrip has a verdict control on each step: **plausible**, **too smart**, **too dumb**, **random**. Selections persist in the browser until exported. The reviewer marks steps, then exports JSON to `.bag-of-rocks/calibration/verdicts/`.

Read verdicts as evidence about behavior, not about tags. A step can be plausible while its trait tag is wrong; check tag fit separately during review.

Patterns to look for:

- **Too smart** clustered on one kind of moment (reading evidence, weighing confidence, finding a hidden control) → tighten the trait that should have prevented it.
- **Too dumb** clustered on one trait → its trigger is too broad.
- **Random** anywhere → the coherence rule broke; treat it as a skill defect.
- A behavior the coordinator assumed was a harness error but the reviewer marks **plausible** (for example an early abandonment) → it's persona behavior; fix the labeling, not the behavior.

Verdicts from one reviewer on a handful of runs are expert judgment, not human-behavior evidence, and a run where nearly everything is marked plausible may reflect agreement or acquiescence. Report them as `reviewer verdicts only (<n> steps, <date>)`.

## Source 4: Human session material (optional)

If real usability sessions ever become available, they're the strongest evidence. Use them only with the user's permission and appropriate participant consent. Keep identities out of all artifacts. Extract observable events (cues, actions, stated expectations, recovery, outcome), compare only to synthetic runs with matched task and context, and treat each real person's behavior as one case, not a rule. A moderator-coached completion is not an unassisted attempt.

## Changing a trait from calibration evidence

1. Name the mismatch and its evidence (fixture results, rock replays, verdict exports).
2. Propose the narrowest wording change to one trait card.
3. Bump the skill's patch version and keep the old trait wording in a changelog.
4. Rerun the relevant fixtures and the held-out rocks blind.
5. Report what changed, why, what stayed unmatched, and which evaluation was actually run.

## Calibration note

```text
Skill version (before -> after):
Trait(s) changed:
Evidence: fixtures / rocks / verdicts / human sessions (with run IDs)
Mismatch and alternative explanations:
Change made:
Evaluation: fixture results, held-out rock replays, or descriptive only
Remaining limits:
```

Calibration status belongs in every report's Limits section, using exactly one of: `not calibrated`, `reviewer verdicts only (<n> steps, <date>)`, `fixtures v<x> + <n> held-out rocks (<date>)`. Informal tuning between runs is not calibration and must not be described as such.
