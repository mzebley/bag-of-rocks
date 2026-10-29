# Validation — 2026-10-28

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
- JSON parameters work without PyYAML. YAML depends on it, and the converter can silently fall back to empty parameters after a YAML read error.
- Trace input paths and shapes are trusted; arbitrary untrusted traces are outside the tested scope. WebP dimensions are not decoded.
- The documented intended-path example uses intended_cue/intended_action, while the optional JSON converter expects cue/action. When producing coordinator/intended-path.json, use the converter's cue/action keys; otherwise fill the intended path during review.
- The installed changelog describes prior private runs and reviewer verdicts. Those claims are not a transferable calibration certificate for future runs.

These limitations were recorded against the imported 0.4.1 helpers and remain relevant to 0.5.0. The fresh-install checks above cover the updated report presentation and opt-in calibration controls.
