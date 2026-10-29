# Distribution record

2026-10-28: Mark Zebley confirmed ownership of the imported skill and approved the MIT license. GitHub is the initial public distribution channel at https://github.com/mzebley/bag-of-rocks. The initial public distribution used the installed 0.4.1 baseline. Version 0.5.0 adds the Evidence ledger templates and opt-in tester calibration; see the changelog for details.

The release preparation checked the GitHub identity and repository availability before creation. It used the reviewed project copy, leaving the installed skill directory unchanged.

## Optional npm distribution — not published

The package.json remains deliberately `private: true`. Its MIT license and GitHub repository are set, but no npm publishing identity or owned package name/scope is verified. The prior npm whoami check returned E401. GitHub identity does not establish npm ownership.

The package contains static skill files, documentation and tests under an explicit file allowlist. No executable bin, runtime dependencies or install lifecycle scripts are present. Use npm only if colleagues need a registry artifact. Verify identity, choose an available name or owned scope, settle the registry version, inspect and test the tarball, then remove private only when publication is authorized and ready. npm installation alone does not register the skill with an agent.

[Public npm packages can be published with a free account](https://docs.npmjs.com/about-public-packages/). [Scoped public publication](https://docs.npmjs.com/creating-and-publishing-scoped-public-packages/) requires explicit public access and account authentication. No purchases or npm publication were made. Runtime model usage may still cost money under the user's provider plan.
