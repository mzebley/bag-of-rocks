# Validation

## 0.7.0: plugin packaging checks (2026-11-02)

- Claude Code 2.1.312: `claude plugin validate .` passes. In an isolated config directory, adding the local repository as a marketplace and installing `bag-of-rocks@mzebley` loads one skill.
- Codex CLI 0.166.0-alpha (bundled with the ChatGPT app): in an isolated `CODEX_HOME`, adding the local repository and installing `bag-of-rocks@mzebley` lists `bag-of-rocks:bag-of-rocks` in the model's available skills. A plugin-root `SKILL.md` installed but did not load, which is why the skill moved to `skills/bag-of-rocks/`.
- The packet builder and fixture runner work from Codex's installed plugin copy.
- `npm pack` lists the skill folder and all four plugin manifests; all 21 offline tests pass from the unpacked tarball.
- After publication: installing `bag-of-rocks@mzebley` from the GitHub marketplace worked in both agents, unpinned and pinned to `v0.7.0`; `claude plugin update` and `codex plugin marketplace upgrade mzebley` ran cleanly. The registry's 0.7.0 integrity and SHA-256 match the inspected tarball, and all 21 tests pass from a fresh `--ignore-scripts` install with a fresh cache.
- Not covered: a real update from one plugin version to the next (first possible with the next release), the skills CLI, Gemini CLI, and the Codex desktop app's Plugins directory.

## 0.6.0: packaging checks (2026-11-02)

- `npm pack --dry-run` lists 47 files: the skill, helpers, references, templates, docs, examples, tests, and `fixtures/`. No bytecode, run evidence, or `.bag-of-rocks/` folders.
- All 20 offline unittest checks pass from an unpacked 0.6.0 tarball, including strict packet builds for all seven fixtures with no leaked fixture names.
- After publication: the registry's `bag-of-rocks@0.6.0` integrity and SHA-256 match the inspected local tarball. Installed from the public registry into an empty temporary project with a fresh npm cache, using `--ignore-scripts`; the installed package reports 0.6.0, includes the fixtures, and all 20 bundled tests pass. The registry lists 0.6.0 as `latest`.
- Not covered: installation through the skills CLI, and blind runs on the six fixtures other than `hint-only-format`.

## 0.6.0: leak test on the hint-only-format fixture (2026-10-31 to 2026-11-01)

- Six blind runs against `fixtures/site/reserve.html`, where the date format appears only in legible grey helper text. Full-bag (HTS on): 0 of 3 testers entered `YYYY-MM-DD` before an error. HTS off under the old Phase 1 wording: 0 of 1, because the base Reading rule repeated HTS. After moving that rule into the HTS card, HTS off: 2 of 2 entered `2026-11-20` first; one completed and one abandoned on a native dropdown that never rendered.
- Verification after the HTS-limit, dropdown, and settle-check changes (run-20261101-c2b5b6, full-bag): failed once with `20 November 2026`, read the hint because the error marked Date, entered `2026-11-20`, and completed. The dropdown fallback was used without counting as a failure, and the settle check caught two lagging frames. One run.
- Read as descriptive evidence that the HTS card suppresses visible helper text rather than leaking it, on one fixture. It does not cover results-reading cases.
- Harness observations: stale result screenshots in 4 of 6 runs (two misdirected clicks, one false fidget), native select options never rendered, and the built-in browser's tab URL exposed a state change before the screenshot showed it. Testers ran from a directory containing fixture answer keys; blinding was instruction-only.

## 0.5.0 and earlier (2026-10-28)

## Published 0.5.0: fresh install and browser verification

- Installed `bag-of-rocks@0.5.0` from the public npm registry into an empty temporary project with a fresh npm cache, using `--ignore-scripts`. The installed package reports version 0.5.0; all nine bundled unittest checks pass.
- Built a strict tester packet without neutrality warnings, converted a synthetic trace, and generated normal and `--calibration` filmstrips using only the installed package. Conversion preserved the tester files and produced the readable trace without warnings.
- Opened both generated filmstrips in Chromium and WebKit at 1100px and 320px widths, in light and dark themes. Evidence ledger step rails and monospace IDs rendered, screenshot images loaded, and no horizontal page overflow or JavaScript errors occurred.
- Normal filmstrips contained no calibration buttons or export toolbar. Calibration filmstrips showed Plausible, Too expert, Overplayed confusion, and Unmotivated action; keyboard selection, persistence after reload, clearing verdicts, and JSON download passed. Exported data retained the selected verdict and skill version 0.5.0.
- Print mode hid the calibration toolbar. These checks used generated fixtures; they did not include a live app walkthrough, VoiceOver review, full accessibility audit, or assessment of persona realism.

## Initial 0.4.1 packaging checks

- Eight offline unittest checks pass: repeatable packets and SHA-256, hidden intended path/inherited-state exclusion, patient/custom trait selection and fixed wording, invalid trait rejection, image-byte-based coordinate conversion, frozen tester-file preservation, missing/pending evidence warnings, existing review preservation, and safe JSON embedding. Several invariants share a test.
- The same eight checks pass from an unpacked npm tarball.
- Skill Creator quick_validate.py reports “Skill is valid!” using a disposable virtual environment with PyYAML 6.0.3. The default Python initially lacked PyYAML; no system dependencies were changed.
- Filmstrip JavaScript passes node --check. This is a syntax check, not a browser rendering or accessibility test.
- npm pack allowlist inspected. Python bytecode was discovered during the first pack and excluded by narrowing directory entries to file patterns. Final artifact contains no bytecode or real run evidence.
- Imported files were reviewed for credentials, private paths, private examples and ownership markers. Development names were anonymized. Source hashes allow checking the installed files remain unchanged.

The initial packaging checks did not include a live app walkthrough, browser/VoiceOver session, persona calibration, or competing product execution. These tests validate helper behavior, not usability findings or persona realism.

## Known limitations

- The packet is instruction-based isolation, not a filesystem sandbox. The coordinator must carry safety boundaries into prohibited_effects. A fresh context alone does not deny file access.
- Strict packet lint reports failure after writing output; warnings must be resolved before handing off those files.
- JSON parameters work without PyYAML. YAML depends on it; the converter now reports a YAML read error as a trace problem instead of falling back silently.
- Trace input paths and shapes are trusted; arbitrary untrusted traces are outside the tested scope. WebP dimensions are not decoded.
- Neutrality lint is pattern-based plus an answer-key label check. It catches common leaks, not every paraphrase.
- The production guard is a hostname heuristic. Declare real staging hosts in the project config.
- The installed changelog describes prior private runs and reviewer verdicts. Those claims are not a transferable calibration certificate for future runs.

These limitations were recorded against the imported 0.4.1 helpers and remain relevant to 0.5.0. The fresh-install checks above cover the updated report presentation and opt-in calibration controls.
