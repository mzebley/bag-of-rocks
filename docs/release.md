# Distribution record

Version 0.6.0 is published on [npm](https://www.npmjs.com/package/bag-of-rocks/v/0.6.0) under `mzebley` and as a [GitHub release](https://github.com/mzebley/bag-of-rocks/releases/tag/v0.6.0). The annotated tag `v0.6.0` points to commit `51cc82c`. This version enforces documented safeguards in the helpers, adds the calibration fixtures, and changes tester packets; see the [changelog](../CHANGELOG.md) for details.

The npm registry identifies 0.6.0 as `latest` and `mzebley` as its maintainer. The published archive's integrity matches the inspected local tarball (`sha512-nSmONOCT…AyIiA==`, 47 files), and all 20 offline tests passed from its unpacked contents.

Earlier releases: 0.5.0 (tag `v0.5.0`, commit `74c8bd4`) added the Evidence ledger templates and opt-in tester calibration. The initial public distribution used the installed 0.4.1 baseline. Mark Zebley confirmed ownership of the imported skill and approved the MIT license on 2026-10-28.

## npm distribution

The published `bag-of-rocks@0.6.0` package is public. The package uses an explicit file allowlist and contains the skill, helpers, templates, documentation, examples, calibration fixtures, and offline tests. It has no runtime dependencies, executable bin, or install lifecycle scripts.

Download the files with `npm pack bag-of-rocks@0.6.0`, extract the archive, and copy the skill files into your agent's configured skills directory as described in the README. npm installation alone does not register the skill with an agent. Python 3 runs the helpers; model and browser usage remain separate.

Before each publication, inspect the tarball, run its offline tests, and confirm the authenticated npm account. Publish the inspected tarball to the public registry after completing npm's authentication prompts.
