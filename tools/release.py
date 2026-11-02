#!/usr/bin/env python3
"""Release helpers used by .github/workflows/release.yml. Not shipped in the package.

Usage:
    python3 tools/release.py check v0.7.0          # tag matches every version field
    python3 tools/release.py notes 0.7.0 OUT.md    # CHANGELOG section plus install lines
    python3 tools/release.py codex-zip OUT_DIR     # Codex plugin ZIP for the OpenAI portal
    python3 tools/release.py icon IMAGE            # install the listing icon for both directories
"""
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "bag-of-rocks"
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")
ICON = "assets/icon.png"
ICON_PX = (512, 2048)        # Anthropic directory: square, 512-2048 px, under 2 MB
ICON_BYTES = 2 * 1024 * 1024  # OpenAI's limits (48 px minimum, 5 MiB) are looser
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
    files = [ROOT / ".codex-plugin" / "plugin.json", ROOT / "LICENSE", ROOT / "PRIVACY.md"]
    if (ROOT / ICON).exists():
        files.append(ROOT / ICON)
    else:
        print(f"Note: no {ICON}; the OpenAI directory requires logo and composerIcon before listing.")
    files += [f for f in sorted(SKILL.rglob("*")) if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc"]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.relative_to(ROOT).as_posix())
    print(f"Codex ZIP written: {out} ({len(files)} files)")


def icon_problems(path):
    sys.path.insert(0, str(SKILL / "scripts"))
    sys.dont_write_bytecode = True
    from trace_to_run import sniff
    fmt, w, h = sniff(Path(path))
    problems = []
    if fmt != "png":
        problems.append(f"must be a PNG (found {fmt or 'unknown format'})")
    if not (w and w == h and ICON_PX[0] <= w <= ICON_PX[1]):
        problems.append(f"must be square, {ICON_PX[0]}-{ICON_PX[1]} px (found {w}x{h})")
    if Path(path).stat().st_size >= ICON_BYTES:
        problems.append("must be under 2 MB")
    return problems


def icon(image):
    problems = icon_problems(image)
    if problems:
        sys.exit(f"{image} " + "; ".join(problems))
    (ROOT / ICON).parent.mkdir(exist_ok=True)
    if Path(image).resolve() != (ROOT / ICON).resolve():
        shutil.copyfile(image, ROOT / ICON)
    for p, keys in ((".claude-plugin/plugin.json", ("icon",)), (".codex-plugin/plugin.json", ("logo", "composerIcon"))):
        m = json.loads((ROOT / p).read_text())
        target = m if p.startswith(".claude") else m["interface"]
        for k in keys:
            target[k] = "./" + ICON
        (ROOT / p).write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
    pkg = json.loads((ROOT / "package.json").read_text())
    if ICON not in pkg["files"]:
        pkg["files"].insert(pkg["files"].index("LICENSE") + 1, ICON)
        (ROOT / "package.json").write_text(json.dumps(pkg, indent=2) + "\n")
    print(f"Icon installed at {ICON} and referenced from both plugin manifests and package.json.")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["help"]
    commands = {"check": (check, 1), "notes": (notes, 2), "codex-zip": (codex_zip, 1), "icon": (icon, 1)}
    if cmd not in commands or len(args) != commands[cmd][1]:
        sys.exit(__doc__)
    commands[cmd][0](*args)
