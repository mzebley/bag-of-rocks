#!/usr/bin/env python3
"""Release helpers used by .github/workflows/release.yml. Not shipped in the package.

Usage:
    python3 tools/release.py check v0.7.0          # tag matches every version field
    python3 tools/release.py notes 0.7.0 OUT.md    # CHANGELOG section plus install lines
    python3 tools/release.py codex-zip OUT_DIR     # Codex plugin ZIP for the OpenAI portal
"""
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "bag-of-rocks"
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")
INSTALL = """### Install

Claude Code: `/plugin marketplace add mzebley/bag-of-rocks`, then `/plugin install bag-of-rocks@mzebley`.
Codex: `codex plugin marketplace add mzebley/bag-of-rocks`, then `codex plugin add bag-of-rocks@mzebley`.
"""


def versions():
    found = {"package.json": json.loads((ROOT / "package.json").read_text())["version"]}
    m = re.search(r"^Version (\d+\.\d+\.\d+)", (SKILL / "SKILL.md").read_text(), re.M)
    found["SKILL.md"] = m.group(1) if m else None
    for p in MANIFESTS:
        found[p] = json.loads((ROOT / p).read_text()).get("version")
    return found


def changelog_section(version):
    text = (ROOT / "CHANGELOG.md").read_text()
    m = re.search(rf"^## {re.escape(version)} \(\d{{4}}-\d{{2}}-\d{{2}}\)\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else None


def check(tag):
    version = tag[1:] if tag.startswith("v") else tag
    problems = [f"{name} says {v!r}" for name, v in versions().items() if v != version]
    if changelog_section(version) is None:
        problems.append(f"CHANGELOG.md has no dated '## {version} (YYYY-MM-DD)' section")
    if problems:
        sys.exit(f"Tag {tag} doesn't match the release files:\n  - " + "\n  - ".join(problems))
    print(f"{tag}: package.json, SKILL.md, both plugin manifests, and CHANGELOG.md agree.")


def notes(version, out):
    section = changelog_section(version)
    if section is None:
        sys.exit(f"No CHANGELOG.md section for {version}")
    Path(out).write_text(section + "\n\n" + INSTALL)
    print(f"Release notes written: {out}")


def codex_zip(out_dir):
    version = versions()["package.json"]
    out = Path(out_dir) / f"bag-of-rocks-codex-{version}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    files = [ROOT / ".codex-plugin" / "plugin.json", ROOT / "LICENSE"]
    files += [f for f in sorted(SKILL.rglob("*")) if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc"]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(ROOT).as_posix())
    print(f"Codex ZIP written: {out} ({len(files)} files)")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["help"]
    commands = {"check": (check, 1), "notes": (notes, 2), "codex-zip": (codex_zip, 1)}
    if cmd not in commands or len(args) != commands[cmd][1]:
        sys.exit(__doc__)
    commands[cmd][0](*args)
