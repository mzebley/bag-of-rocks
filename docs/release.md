# Distribution record

2026-10-28: Mark Zebley confirmed ownership of the imported skill and approved the MIT license. GitHub is the initial public distribution channel at https://github.com/mzebley/bag-of-rocks. The initial public distribution used the installed 0.4.1 baseline. Version 0.5.0 adds the Evidence ledger templates and opt-in tester calibration; see the changelog for details.

The release preparation checked the GitHub identity and repository availability before creation. It used the reviewed project copy, leaving the installed skill directory unchanged.

## npm distribution

Version 0.5.0 is prepared for public distribution as `bag-of-rocks` through the author's `mzebley` npm account. The package uses an explicit file allowlist and contains the skill, helpers, templates, documentation, examples, and offline tests. It has no runtime dependencies, executable bin, or install lifecycle scripts.

Download the files with `npm pack bag-of-rocks@0.5.0`, extract the archive, and copy the skill files into your agent's configured skills directory as described in the README. npm installation alone does not register the skill with an agent. Python 3 runs the helpers; model and browser usage remain separate.

Before each publication, inspect the tarball, run its offline tests, and confirm the authenticated npm account. Publish the inspected tarball to the public registry after completing npm's authentication prompts.
