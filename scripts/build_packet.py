#!/usr/bin/env python3
"""Build a bag-of-rocks tester packet verbatim from the skill files.

Usage:
    python scripts/build_packet.py path/to/run-params.yaml [--strict]

Reads run parameters (YAML, or JSON if PyYAML is unavailable), assembles:
  1. a run block generated from the parameters,
  2. the Phase 1 section of SKILL.md (between PHASE1 markers),
  3. the active trait cards from references/traits.md (between TRAIT markers),
  4. the trace schema from references/review-and-report.md (between TRACE markers),
and writes tester-packet.txt and tester-packet.sha256 next to the params file.

Prints neutrality warnings. With --strict, exits non-zero if any warning fires.
The packet must be sent to the tester unchanged.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

PRESETS = {
    "full-bag": ["VPF", "HTS", "FC", "LIT", "NR", "LP"],
    "patient-bag": ["VPF", "HTS", "FC", "LIT", "NR"],
}
NAMES = {
    "visual-path follower": "VPF", "helper-text skipper": "HTS", "fidget clicker": "FC",
    "literalist": "LIT", "nervous retreater": "NR", "low patience": "LP",
    "back-button navigator": "BBN", "autofill truster": "AT", "tab wanderer": "TW",
    "thumb reacher": "TR",
}
FLAG_PATTERNS = [
    (r"\bintended\b|\bexpected (path|route|flow)\b|\bhappy path\b", "mentions an intended or expected route"),
    (r"\b(bug|defect|broken|issue we|known problem)\b", "hints at a suspected defect"),
    (r"\b(previous|prior|last|earlier) run\b|\brun[- ][a-z](?=[,.;:)]|$)|\bbaseline\b|\bcandidate\b", "references another run or variant"),
    (r"\b(click|press|tap|select|choose) (the )?[\"'“][^\"'”]+[\"'”]", "names a specific control to use"),
    (r"\b(step \d|first go to|then go to|navigate to)\b", "describes a route"),
    (r"\ball \d+\b|\b\d+ (records|items|rows|grantees|results)\b", "states a count the user may not know"),
    (r"\b(fix|repair|patch|change we made)\b", "mentions a fix"),
]


def load_params(path):
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            sys.exit("PyYAML is not installed. Install it (pip install pyyaml) or provide params as JSON.")


def between(text, start, end, label):
    m = re.search(re.escape(start) + r"(.*?)" + re.escape(end), text, re.S)
    if not m:
        sys.exit(f"Could not find {label} markers ({start} … {end}). Is the skill version 0.4.0 or later?")
    return m.group(1).strip()


def trait_cards(traits_md):
    cards = {}
    for m in re.finditer(r"<!-- TRAIT:([A-Z]+) -->(.*?)<!-- /TRAIT -->", traits_md, re.S):
        cards[m.group(1)] = m.group(2).strip()
    return cards


def norm_trait(t):
    t = str(t).strip()
    return NAMES.get(t.lower(), t.upper())


def resolve_traits(p):
    preset = p.get("preset", "full-bag")
    custom = p.get("presets", {}) or {}
    if preset in custom:
        base = [norm_trait(str(x).split(":")[0]) for x in custom[preset]]
    elif preset in PRESETS:
        base = list(PRESETS[preset])
    else:
        sys.exit(f"Unknown preset '{preset}'. Known: {', '.join(list(PRESETS) + list(custom))}")
    for t in p.get("traits_remove", []) or []:
        t = norm_trait(t)
        if t in base:
            base.remove(t)
    for t in p.get("traits_add", []) or []:
        t = norm_trait(t)
        if t not in base:
            base.append(t)
    return preset, base


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def run_block(p, preset, traits):
    phr = p.get("phrasing", "own-words")
    if isinstance(phr, dict) and "fixed" in phr:
        phrasing = f'Fixed. If you need to type your request, enter exactly: "{phr["fixed"]}"'
    else:
        phrasing = "Your own words. If you need to type a request or question, write it the way you naturally would, and record exactly what you entered."
    lines = [
        "You are the rock in a bag-of-rocks UX run. Follow the instructions below exactly. Return your trace when you stop.",
        "",
        "## This run",
        f"Run ID: {p.get('run_id', '')}",
        f"Goal (in your own words as the user): {p['goal']}",
        f"Start URL: {p['start_url']}",
        f"Account: {p.get('account', 'existing session')} (credentials are handled by the operator; never write them down)",
        f"Device: {p.get('device', 'existing viewport')}",
        f"Persona: {preset}; active traits: {', '.join(traits)}",
        f"Phrasing: {phrasing}",
    ]
    if "FC" in traits:
        lines.append(f"Fidget Clicker intensity: up to {p.get('fc_intensity', 3)} extra clicks.")
    if "LP" not in traits:
        lines.append("Low Patience is off: abandon after 4 failed attempts at the same subgoal or 6 backtracks; allow stalls up to 5 minutes per stage, taking a wait screenshot every 20–40 seconds.")
    facts = as_list(p.get("user_facts"))
    if facts:
        lines.append("Things you know as this user: " + "; ".join(map(str, facts)))
    mut = p.get("mutations", "allowed")
    if mut == "none":
        lines.append("Mutations: none. Stop at every commit point and record what you would have done. A commit is anything you deliberately save, submit, confirm, pin, delete, or send, and typing into a field that saves automatically. Things the app records on its own when you just look around (recent history, view counts) are fine; note them if you see them.")
    else:
        lines.append(f"Mutations: {mut}")
    if p.get("allowed_effects"):
        lines.append(f"Allowed effects: {p['allowed_effects']}")
    proh = as_list(p.get("prohibited_effects"))
    if proh:
        lines.append("Never do: " + "; ".join(map(str, proh)) + ". If an action would cross one of these, stop.")
    b = p.get("budget", {}) or {}
    if b:
        lines.append("Budget: " + ", ".join(f"{v} {k}" for k, v in b.items()))
    lines.append(f"Output folder (write only here; read nothing else except your own files): {p['output_dir']}")
    return "\n".join(lines)


def lint(p):
    warnings = []
    fields = {"goal": p.get("goal", ""), "allowed_effects": p.get("allowed_effects", "")}
    for i, f in enumerate(as_list(p.get("user_facts"))):
        fields[f"user_facts[{i}]"] = f
    for name, val in fields.items():
        for pat, why in FLAG_PATTERNS:
            if re.search(pat, str(val), re.I):
                warnings.append(f"{name}: {why} -> {val!r}")
    for k in ("intended_path", "assumptions", "findings", "notes", "expected"):
        if k in p:
            warnings.append(f"params contain '{k}', which must not reach the tester (it is not included, but keep it out of this file)")
    return warnings


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    if not args:
        sys.exit(__doc__)
    params_path = Path(args[0]).expanduser().resolve()
    p = load_params(params_path)
    for req in ("goal", "start_url", "output_dir"):
        if not p.get(req):
            sys.exit(f"Missing required parameter: {req}")

    skill_dir = Path(p.get("skill_dir") or Path(__file__).resolve().parent.parent).expanduser()
    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    traits_md = (skill_dir / "references" / "traits.md").read_text(encoding="utf-8")
    report_md = (skill_dir / "references" / "review-and-report.md").read_text(encoding="utf-8")
    version = re.search(r"Version (\d+\.\d+\.\d+)", skill_md)
    version = version.group(1) if version else "unknown"

    preset, traits = resolve_traits(p)
    cards = trait_cards(traits_md)
    missing = [t for t in traits if t not in cards]
    if missing:
        sys.exit(f"No trait card found for: {', '.join(missing)}")

    packet = "\n\n".join([
        run_block(p, preset, traits),
        "## How to be the rock\n\n" + between(skill_md, "<!-- PHASE1:START -->", "<!-- PHASE1:END -->", "Phase 1"),
        "## Your traits\n\n" + "\n\n".join(cards[t] for t in traits),
        "## Trace format\n\n" + between(report_md, "<!-- TRACE:START -->", "<!-- TRACE:END -->", "trace"),
        f"(bag-of-rocks {version} packet)",
    ]) + "\n"

    out_dir = params_path.parent
    (out_dir / "tester-packet.txt").write_text(packet, encoding="utf-8")
    digest = hashlib.sha256(packet.encode("utf-8")).hexdigest()
    (out_dir / "tester-packet.sha256").write_text(f"{digest}  tester-packet.txt\n", encoding="utf-8")

    print(f"Packet written: {out_dir / 'tester-packet.txt'}")
    print(f"SHA-256: {digest}")
    print(f"Skill version {version}; preset {preset}; traits {', '.join(traits)}")
    warnings = lint(p)
    if warnings:
        print("\nNeutrality warnings (resolve before spawning, or record why each is acceptable):")
        for w in warnings:
            print("  - " + w)
        if strict:
            sys.exit(1)
    else:
        print("No neutrality warnings.")


if __name__ == "__main__":
    main()
