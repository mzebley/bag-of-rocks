# Bag of Rocks

Give an agent a goal without showing it the route. Watch where it gets stuck, then review an annotated timeline of what happened.

Bag of Rocks is a synthetic UX walkthrough skill. Its tester acts as someone who's unfamiliar with the product, nervous about making mistakes, and unsure around technology.

A coordinator records the intended path and keeps it from the tester. The tester works through the rendered screens, then a reviewer compares its recorded actions with that path. You get an annotated screenshot filmstrip, findings linked to evidence, and saved findings called “rocks” for later regression checks.

**Version:** 0.5.0 · [MIT license](LICENSE) · [Changelog](CHANGELOG.md) · [Provenance](docs/provenance.md)

Use the findings as hypotheses to investigate. They don't establish how real people behave, how many would fail, or whether a product meets accessibility standards.

## What it includes

- Six default behavior traits, a patient preset, and optional traits.
- Fast, multi-persona, ablation, retest, and regression workflows.
- A deterministic packet builder with a SHA-256 digest and neutrality warnings.
- A trace converter that preserves tester files and flags evidence problems.
- A self-contained HTML filmstrip with optional tester calibration controls.

The agent performs the walkthrough. These Python scripts do not launch or control a browser, create a sandbox, or enforce permissions.

## Requirements

Use an agent with screenshot-based browser control and filesystem access. Give the tester a fresh context when possible; if it already knows the intended path or prior conversation, label the run as an informed pass.

The helpers require Python 3. JSON input needs no additional packages; YAML input requires PyYAML. The skill itself does not require Node.js. Your model and browser providers may charge for usage.

## Install from a local checkout

For a project using Claude Code, from this repository root:

```sh
# Choose a real project path. Refuse to overwrite an installed copy.
destination=/path/to/project/.claude/skills/bag-of-rocks
test ! -e "$destination" && mkdir -p "$destination" && cp -R SKILL.md CHANGELOG.md LICENSE references scripts assets "$destination/"
```

For another agent, copy the same files into its configured skills directory. If your Codex installation uses `~/.codex/skills`, use `~/.codex/skills/bag-of-rocks`. Inspect an existing copy before replacing it.

Install from GitHub with the skills CLI:

```sh
npx skills add mzebley/bag-of-rocks --skill bag-of-rocks
```

This command uses the independent [skills CLI](https://github.com/vercel-labs/skills). Check its documentation for Node.js requirements. Release validation covered the unpacked files; it did not test installation through the CLI. Manual copying does not require Node.js.

## Use it

Ask your agent:

```text
Use bag-of-rocks.
Goal: Change my mailing address to 12 Elm St.
Start: https://staging.example.test/
Account: disposable sandbox user
Mutations: none
Preset: full-bag
Budget: one run, 25 actions
```

Replace the fictional URL and address with your authorized staging URL and test data. With `Mutations: none`, the tester stops before saving the address and records what it would have done. Use `Mutations: allowed` only when changes are authorized in your sandbox or staging environment.

The coordinator confirms the intended path with you, then gives a fresh tester a fixed packet of instructions that excludes that path. See [SKILL.md](SKILL.md) for the workflow and [coordinator guidance](references/coordinator.md) for modes and run structure.

To try the helper without any browser activity:

```sh
mkdir -p /tmp/bag-of-rocks-example/tester
cp examples/run-params.json /tmp/bag-of-rocks-example/run-params.json
python3 scripts/build_packet.py /tmp/bag-of-rocks-example/run-params.json --strict
```

Edit the example's `output_dir` to the absolute tester directory before a real run. Its placeholder output path is only for inspecting a packet. Keep credentials out of parameters. Include every applicable safety boundary in `prohibited_effects`; the packet builder is not a safety sandbox. A nonzero `--strict` exit still leaves packet files behind: do not hand them off until warnings are resolved.

After a tester has produced `tester/trace.json` and screenshots:

```sh
python3 scripts/trace_to_run.py /path/to/run
# Reviewer fills outcome, summary, findings, and divergences in run.json.
python3 scripts/trace_to_run.py /path/to/run --filmstrip
```

For tester calibration, add `--calibration` to the `--filmstrip` command. This enables plausibility verdicts and their export controls; ordinary reports omit them.

Convert only trusted local traces, and inspect them first. The converter is not hardened for arbitrary downloaded inputs. It reads PNG and JPEG dimensions, but cannot decode WebP dimensions. Keep the tester directory unchanged and include conversion warnings in the report’s Limits section.

## Validation and contributions

```sh
python3 -m unittest discover -s tests -v
```

Tests use disposable files to check packet blinding, hashes, trace conversion, and filmstrip generation. They do not operate a browser. See [validation](docs/validation.md) for the recorded checks and their limits.

When contributing a change, include a small reproducible fixture, the observed behavior, and any effect on the evidence trail. Keep real run screenshots, account data, credentials, and private product examples out of commits.

## Distribution and related work

Version 0.5.0 is published on [npm](https://www.npmjs.com/package/bag-of-rocks/v/0.5.0) and as a [GitHub release](https://github.com/mzebley/bag-of-rocks/releases/tag/v0.5.0). Install the skill from GitHub or a local checkout. The npm package distributes the same skill files: use `npm pack bag-of-rocks@0.5.0` to download the archive, then extract it and follow the local-copy instructions above. npm does not register the skill with your agent automatically. See the [distribution record](docs/release.md) for details.

[Related work](docs/related-work.md) covers other approaches to simulated users and UX inspection. Bag of Rocks focuses on an uncoached persona pursuing a goal, with a chronological record for review. The comparison is preliminary, not a benchmark.
