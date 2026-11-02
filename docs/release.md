# Distribution record

Version 0.7.0 is published on [npm](https://www.npmjs.com/package/bag-of-rocks/v/0.7.0) under `mzebley` and as a [GitHub release](https://github.com/mzebley/bag-of-rocks/releases/tag/v0.7.0). The annotated tag `v0.7.0` points to commit `9860966`. This version makes the repository a Claude Code and Codex plugin, served from its own `mzebley` marketplace, and moves the skill to `skills/bag-of-rocks/`; see the [changelog](../CHANGELOG.md) for details.

The npm registry identifies 0.7.0 as `latest` and `mzebley` as its maintainer. The published archive's integrity and SHA-256 match the inspected local tarball (`sha512-uP8DZiMs…nTxw==`, 51 files), and all 21 offline tests passed from a fresh install. Installing `bag-of-rocks@mzebley` from GitHub worked in Claude Code and in Codex, including installs pinned to `v0.7.0`.

Earlier releases: 0.6.0 (tag `v0.6.0`, commit `51cc82c`) enforced documented safeguards in the helpers and added the calibration fixtures. 0.5.0 (tag `v0.5.0`, commit `74c8bd4`) added the Evidence ledger templates and opt-in tester calibration. The initial public distribution used the installed 0.4.1 baseline. Mark Zebley confirmed ownership of the imported skill and approved the MIT license on 2026-10-28.

## Plugin distribution

The repository is its own marketplace. `.claude-plugin/` holds the Claude Code manifest and marketplace; `.codex-plugin/` and `.agents/plugins/` hold the Codex equivalents. Users receive a new release when the plugin `version` changes, so bump it in every release; a test keeps it in step with `package.json` and SKILL.md.

## npm distribution

The published `bag-of-rocks@0.7.0` package is public. It uses an explicit file allowlist and contains the skill folder, plugin manifests, templates, documentation, examples, calibration fixtures, and offline tests. It has no runtime dependencies, executable bin, or install lifecycle scripts.

Download the files with `npm pack bag-of-rocks@0.7.0`, extract the archive, and copy `skills/bag-of-rocks/` into your agent's skills directory as described in the README. npm installation alone does not register the skill with an agent. Python 3 runs the helpers; model and browser usage remain separate.

## Release process

Releases run from a tag. Pushing `v<version>` starts `.github/workflows/release.yml`:

1. **verify**: `tools/release.py check` confirms the tag matches `package.json`, SKILL.md, both plugin manifests, and a dated CHANGELOG section. Then the offline tests, `claude plugin validate --strict`, and the tests from the packed tarball.
2. **npm**: publishes with npm trusted publishing (OIDC, with provenance). No token is stored. It skips a version that's already on npm.
3. **github-release**: creates the release from the CHANGELOG section and attaches `bag-of-rocks-codex-<version>.zip` for the OpenAI portal.
4. **release-branch**: fast-forwards the `release` branch to the tagged commit. Anthropic's directory follows that branch, so it only sees releases.

To cut a release:

```sh
# bump the version in package.json, SKILL.md, .claude-plugin/plugin.json, .codex-plugin/plugin.json
# date the CHANGELOG section, then:
python3 tools/release.py check v0.8.0
git commit -am "Release 0.8.0" && git push
git tag -a v0.8.0 -m "Bag of Rocks 0.8.0" && git push origin v0.8.0
```

`.github/workflows/ci.yml` runs the tests, strict validation, and a package dry run on every push to `main` and every pull request.

**One-time setup:**

- npmjs.com: in the package settings, under Trusted publishing, add GitHub Actions with repository `mzebley/bag-of-rocks`, workflow `release.yml`, and environment `npm`. Then, optionally, require trusted publishing and disallow tokens.
- GitHub: the `npm` environment appears on the first run. Add a required reviewer there if you want to approve each publish.

**Listing icon:** one square PNG, 512 to 2048 px and under 2 MB, meets both directories. `python3 tools/release.py icon path/to/icon.png` checks it, copies it to `assets/icon.png`, and points both plugin manifests and `package.json` at it.

**Directories:**

- Anthropic's directory: submit once at claude.ai/directory/manage with repository `mzebley/bag-of-rocks`, no plugin path, and tracked branch `release`. The `release` branch first exists after a tag runs the release workflow. After approval, new releases reach the directory by themselves.
- OpenAI's Plugins directory: upload the Codex ZIP from each GitHub release in the plugin portal. Listing requires the icon above; the privacy policy is [PRIVACY.md](../PRIVACY.md).
