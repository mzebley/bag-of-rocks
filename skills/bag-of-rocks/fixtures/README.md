# Fixtures (the rock garden)

Planted blind spots for calibration and demos, as described in `references/calibration.md`. Each page is a small static mock of a fictional community center, "Cedar Hall", with one blind spot planted. Page names, titles, and run IDs are neutral; never send the tester anything from this folder except the start URL.

Run the commands below from the skill folder (`skills/bag-of-rocks/` in the repository, or wherever the plugin is installed).

**Serve only `site/`**, so no directory listing exposes `paths/` or this README:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory fixtures/site
```

| Fixture | Page | Planted blind spot | Expected trait |
| --- | --- | --- | --- |
| silent-submit | `tours.html` | Send request takes 4s, no loading state, stays enabled | FC |
| hint-only-format | `reserve.html` | Date must be YYYY-MM-DD; format only in helper text | HTS |
| decoy-primary | `oak-room.html` | Big primary opens a photo tour; booking is an inline text link | VPF |
| done-discards | `bookings.html` | "Done" closes the editor without saving | LIT |
| scary-routine | `account.html` | Routine edit labeled "Submit final record. This cannot be undone." | NR |
| dead-end | `welcome.html` | Saturday banner leads to a page with no links; only browser Back | LP |
| clean-control | `book.html` | None: booking plus edit flow with every spot above fixed | none |

`paths/<fixture>.json` holds the goal, user facts, intended path (`steps[]` with `id`, `screen`, `cue`, `action`), assumptions, and a `reviewer_check` describing how to confirm the outcome. State lives in `localStorage` (`cedar-*` keys); open any page with `?reset` to clear it before a run.

## Run a fixture end to end

```bash
python3 fixtures/new_run.py silent-submit                # full-bag, trait on
python3 fixtures/new_run.py silent-submit --without FC   # same fixture, trait off
```

`new_run.py` creates `.bag-of-rocks/runs/run-<date>-<hex>/` with `run-params.json` and `coordinator/intended-path.json`, then runs `scripts/build_packet.py --strict`. Options: `--preset`, `--base-url` (default `http://127.0.0.1:8000`), `--root`. Then:

1. Open the printed start URL with `?reset` once to clear saved state.
2. Spawn a fresh tester with `tester-packet.txt` unchanged; it writes `tester/trace.json` and screenshots.
3. Convert and review:

```bash
python3 scripts/trace_to_run.py .bag-of-rocks/runs/<run-id>
python3 scripts/trace_to_run.py .bag-of-rocks/runs/<run-id> --filmstrip --calibration
```

The fixture name appears only in `coordinator/intended-path.json`, which the tester never reads. A well-calibrated rock hits the planted spot with the trait on, misses or recovers cheaply with it off, and finishes `clean-control` without a reported defect.
