# Bag of Rocks

Give an agent a goal, keep it uncoached, and watch where a deliberately confused user gets stuck—then review an annotated timeline of what happened.

Bag of Rocks is a synthetic UX walkthrough skill built around an unfamiliar, nervous, low-tech-confidence persona.

A coordinator hides the intended path, a fresh tester follows a constrained persona through rendered screens, and a reviewer compares the frozen trace against the answer key. The output is an annotated screenshot filmstrip, evidence-linked findings, and reusable regression “rocks.”

**Version:** based on installed **0.4.1**, shared under the [MIT license](LICENSE). Historical observations are preserved in [CHANGELOG.md](CHANGELOG.md); see [provenance](docs/provenance.md).

This produces synthetic hypotheses, not real-user research, population failure rates, or accessibility conformance evidence.

## What it includes

- Six default behavior traits, a patient preset, and optional traits.
- Fast, multi-persona, ablation, retest, and regression workflows.
- A deterministic packet builder with a SHA-256 digest and neutrality warnings.
- A trace converter that preserves tester files and flags evidence problems.
- A self-contained HTML filmstrip with reviewer verdict export.

The agent performs the walkthrough. These Python scripts do not launch or control a browser, create a sandbox, or enforce permissions.

## Requirements

Use an agent with screenshot-based browser control, filesystem access, and preferably a fresh context for the tester. If only a shared/informed context is available, label that limitation. Python 3 runs the helpers. JSON input uses the standard library; YAML input additionally requires PyYAML. No Node runtime is required to use the skill. Agent/model or browser-provider costs are separate from distributing these files.

## Install from a local checkout

For a project using Claude Code, from this repository root:

```sh
# Choose a real project path. Refuse to overwrite an installed copy.
destination=/path/to/project/.claude/skills/bag-of-rocks
test ! -e "$destination" && mkdir -p "$destination" && cp -R SKILL.md CHANGELOG.md LICENSE references scripts assets "$destination/"
```

For another agent, copy the same files into its configured skills directory. For an existing Codex installation using `~/.codex/skills`, the destination can be `~/.codex/skills/bag-of-rocks`; inspect an existing copy before replacing it. This preparation did not change the author's installed skill.

Install from GitHub with the skills CLI:

```sh
npx skills add mzebley/bag-of-rocks --skill bag-of-rocks
```

That uses the independent [skills CLI](https://github.com/vercel-labs/skills), not a Bag of Rocks executable. The install command follows the CLI documentation; this release was tested by unpacking its files, without modifying an existing agent installation. The CLI currently documents Node.js 22.20+; manual copying does not need Node.

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

The URL and address above are fictional examples. Supply your authorized staging URL and scope. The coordinator prepares the intended path and gets it confirmed before handing the frozen packet to a fresh tester. Read [SKILL.md](SKILL.md) for the workflow and [coordinator guidance](references/coordinator.md) for modes and run structure.

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

Treat traces as trusted local inputs and inspect them before conversion. The installed converter is not hardened for arbitrary downloaded traces. It reads PNG/JPEG dimensions; WebP is recognized but lacks dimension decoding. Preserve the frozen tester directory and attach warnings to Limits.

## Validation and contributions

```sh
python3 -m unittest discover -s tests -v
```

Tests use disposable files, exercise packet blinding/hash behavior and trace/filmstrip conversion, and never operate a browser. See [validation](docs/validation.md) for evidence and limits. For a change, include a small reproducible fixture, the observed behavior, and the effect on the evidence trail. Do not commit real run screenshots, account data, credentials, or private product examples.

## Distribution and related work

GitHub plus skill installation is the simplest first release. npm can carry the same static files later; the private draft intentionally prevents publication until a publishing identity and package name are verified. No service, subscription, or install hook is introduced. See [release checklist](docs/release.md) and [public overlap research](docs/related-work.md). Related research explores simulated users too. Bag of Rocks focuses on an uncoached, goal-driven persona and a chronological evidence report; the comparison does not establish a direct substitute for that workflow.
