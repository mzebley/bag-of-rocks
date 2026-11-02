# Distribution record

Version 0.7.0 is published on [npm](https://www.npmjs.com/package/bag-of-rocks/v/0.7.0) under `mzebley` and as a [GitHub release](https://github.com/mzebley/bag-of-rocks/releases/tag/v0.7.0). The annotated tag `v0.7.0` points to commit `9860966`. This version makes the repository a Claude Code and Codex plugin, served from its own `mzebley` marketplace, and moves the skill to `skills/bag-of-rocks/`; see the [changelog](../CHANGELOG.md) for details.

The npm registry identifies 0.7.0 as `latest` and `mzebley` as its maintainer. The published archive's integrity and SHA-256 match the inspected local tarball (`sha512-uP8DZiMs…nTxw==`, 51 files), and all 21 offline tests passed from a fresh install. Installing `bag-of-rocks@mzebley` from GitHub worked in Claude Code and in Codex, including installs pinned to `v0.7.0`.

Earlier releases: 0.6.0 (tag `v0.6.0`, commit `51cc82c`) enforced documented safeguards in the helpers and added the calibration fixtures. 0.5.0 (tag `v0.5.0`, commit `74c8bd4`) added the Evidence ledger templates and opt-in tester calibration. The initial public distribution used the installed 0.4.1 baseline. Mark Zebley confirmed ownership of the imported skill and approved the MIT license on 2026-10-28.

## Plugin distribution

The repository is its own marketplace. `.claude-plugin/` holds the Claude Code manifest and marketplace; `.codex-plugin/` and `.agents/plugins/` hold the Codex equivalents. Users receive a new release when the plugin `version` changes, so bump it in every release; a test keeps it in step with `package.json` and SKILL.md.

## npm distribution

The published `bag-of-rocks@0.7.0` package is public. It uses an explicit file allowlist and contains the skill folder, plugin manifests, templates, documentation, examples, calibration fixtures, and offline tests. It has no runtime dependencies, executable bin, or install lifecycle scripts.

Download the files with `npm pack bag-of-rocks@0.7.0`, extract the archive, and copy `skills/bag-of-rocks/` into your agent's skills directory as described in the README. npm installation alone does not register the skill with an agent. Python 3 runs the helpers; model and browser usage remain separate.

Before each publication, inspect the tarball, run its offline tests, and confirm the authenticated npm account. Publish the inspected tarball to the public registry after completing npm's authentication prompts.
