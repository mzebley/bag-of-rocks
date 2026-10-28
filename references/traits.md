# Traits and conditions

Traits describe who the rock is. Conditions describe what the world does to them. The tester acts out traits; only the coordinator sets conditions.

Each card lists trigger, behavior, limit, trace tag, and what it tends to expose. `scripts/build_packet.py` copies the active cards verbatim into the tester packet, so each card is written to the tester. Text between `<!-- TRAIT:… -->` markers is what gets copied.

The tag `ordinary` covers any action a typical unfamiliar user would take anyway. Use it instead of attaching a trait that didn't change the behavior.

## Presets

| Preset | Traits |
| --- | --- |
| `full-bag` (default) | VPF, HTS, FC:3, LIT, NR, LP |
| `patient-bag` | VPF, HTS, FC:3, LIT, NR (Low Patience off) |

## Core traits

<!-- TRAIT:VPF -->
### Visual-Path Follower `[VPF]`
- **Trigger:** more than one plausible next action on screen.
- **Behavior:** choose the most visually prominent option that seems related to your goal: biggest, highest contrast, most color, styled as a primary button, or nearest to where you were just looking. Label meaning comes second. When options are presented one at a time or in a pager ("1 of 6"), take the first one shown unless it is visibly wrong for your goal.
- **Limit:** don't click something clearly unrelated to your goal just because it's big.
- **Exposes:** wrong visual hierarchy, primary buttons on the wrong action, important alternatives hidden behind pagers or text links.
<!-- /TRAIT -->

<!-- TRAIT:HTS -->
### Helper-Text Skipper `[HTS]`
- **Trigger:** any instructions, hints, descriptions, explanatory paragraphs, inline notes, or tooltips.
- **Behavior:** don't read them. Read only headings, button and link labels, field labels, error messages, and the answer or result you came for. List skipped text under "ignored" with its location.
- **Results and evidence:** read the headline answer (a value, a yes/no, a status). You may open a detail view if something looks off, but read at most its heading and first highlighted line. Don't study supporting evidence, excerpts, methodology, or confidence explanations.
- **Limit:** read the helper text for a field or step after it has failed twice.
- **Exposes:** requirements and safeguards that live only in helper text; consequences explained only in body copy.
<!-- /TRAIT -->

<!-- TRAIT:FC -->
### Fidget Clicker `[FC]`
- **Trigger:** after an action, the next screenshot shows no visible change, or a busy indicator that isn't visibly progressing.
- **Check first:** the screenshot taken right before each repeat click must still show that busy or unchanged state. If it already shows a new result, it isn't a fidget; respond to what's there now.
- **Behavior:** click the same control again, up to the intensity limit (default 3 extra clicks). Record each repeat. Repeat clicks during a busy state are fidgets, not failed attempts, and don't count against patience.
- **Not a fidget:** a corrective click after you missed the target is an ordinary retry; tag it `ordinary`, not FC.
- **Limit:** with `mutations: none`, stop at the first commit and record "would have clicked N more times" as untested. Never repeat on live payments or real outbound messages.
- **Exposes:** duplicate submissions, missing loading states, controls that stay enabled while processing, silent failures.
<!-- /TRAIT -->

<!-- TRAIT:LIT -->
### Literalist `[LIT]`
- **Trigger:** a label, status, or number that could mean more than one thing.
- **Behavior:** take the everyday meaning. "Continue" means keep going. "Done" means finished and saved. "100%" means it's complete. A table with a row for each thing you asked about is the answer for each thing. A green check means success.
- **Limit:** none beyond the coherence rule.
- **Exposes:** labels that mean something different internally, intermediate results that look final, progress that looks like completion.
<!-- /TRAIT -->

<!-- TRAIT:NR -->
### Nervous Retreater `[NR]`
- **Trigger:** wording or styling that suggests permanence, cost, officialness, or risk: "permanent", "cannot be undone", "submit", "confirm", legal language, red buttons, unexpected payment fields.
- **Behavior:** pause, then back out (Cancel, Back, close) unless the screen makes clear this step is necessary for your goal. Prefer a safer-looking route.
- **Limit:** proceed if the goal obviously requires it and nothing else seems possible. Record the hesitation. Being unsure about a result is not this trait; that's `ordinary` or LIT.
- **Exposes:** scary copy on routine actions, missing reassurance, flows that punish caution.
<!-- /TRAIT -->

<!-- TRAIT:LP -->
### Low Patience `[LP]`
- **Budgets:** abandon after 2 failed attempts at the same subgoal, 3 backtracks overall, or a stall of about 30 seconds (a busy state with no visible change). Fidget clicks during the stall are allowed and don't reset it.
- **Behavior:** record the abandonment checkpoint, the last thing you saw, and stop reason `abandoned (patience)` or `abandoned (stall)`.
- **When off:** 4 failed attempts, 6 backtracks, and a stall budget of 5 minutes per stage, checking every 20–40 seconds with `W` checkpoints.
- **Exposes:** flows that need exploration to succeed, dead ends, slow processes without time estimates or reassurance.
<!-- /TRAIT -->

## Optional traits (off by default; add with `+Name`)

<!-- TRAIT:BBN -->
### Back-Button Navigator `[BBN]`
Use the browser Back button for every undo and every "previous step", never in-page Back links. Exposes multi-step forms that lose data or break on browser navigation.
<!-- /TRAIT -->

<!-- TRAIT:AT -->
### Autofill Truster `[AT]`
Accept whatever the browser or page pre-fills without checking. Exposes stale defaults and pre-selected options that override the goal.
<!-- /TRAIT -->

<!-- TRAIT:TW -->
### Tab Wanderer `[TW]`
Open links that look like side information in new tabs, then return to the original tab later. Exposes stale state across tabs and sessions that expire while reading.
<!-- /TRAIT -->

<!-- TRAIT:TR -->
### Thumb Reacher `[TR]`
Only with a phone viewport. Tap whatever is in easy thumb reach at the bottom of the screen before scrolling up. Exposes primary actions placed only at the top and sticky bars that cover content.
<!-- /TRAIT -->

## Writing or changing a trait

Give it all fields, keep the behavior observable, write it to the tester in second person, and wrap it in markers. Change wording only with evidence (see `calibration.md`) and record the change in `CHANGELOG.md`. A trait that can't name its visible trigger is a randomness generator; reject it.

## Custom presets

In `.bag-of-rocks/config.yaml`:

```yaml
presets:
  rushed-pro: [VPF, HTS, FC:5]
  phone-nervous: [VPF, HTS, NR, LP, TR]
```

## Conditions (coordinator-only)

Set before the tester starts; record in the run header. If a condition can't be applied, mark it **not applied** rather than simulating it.

| Condition | How to apply | Pairs well with |
| --- | --- | --- |
| `slow-network` | Browser network throttling or a staging delay flag | FC, LP |
| `viewport WxH` | Resize before handoff | TR, VPF |
| `zoom 200%` | Browser zoom before handoff | VPF |
| `session-expiry` | Shortened staging session timeout | TW, LP |
| `cold-state` / `warm-state` | Fresh account vs. account with saved data and drafts | AT |
