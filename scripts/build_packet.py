#!/usr/bin/env python3
"""Build a bag-of-rocks tester packet verbatim from the skill files.

Usage:
    python scripts/build_packet.py path/to/run-params.yaml [--strict]

Reads run parameters (YAML, or JSON if PyYAML is unavailable) and the nearest
.bag-of-rocks/config.(yaml|json) above them, then assembles:
  1. a run block generated from the parameters,
  2. the Phase 1 section of SKILL.md (between PHASE1 markers),
  3. the active trait cards from references/traits.md (between TRAIT markers),
  4. the trace schema from references/review-and-report.md (between TRACE markers),
and writes tester-packet.txt, tester-packet.sha256, and tester-packet.json (the
effective settings, for the reviewer) next to the params file.

Forces mutations to none on production-looking hosts. Prints neutrality warnings,
including answer-key labels from coordinator/intended-path.* that appear in the
run block. With --strict, exits non-zero if any warning fires.
The packet must be sent to the tester unchanged.
"""
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

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
    (r"\b(hint|tip)\b|\blook (for|under|in)\b|\b(it'?s|it is|is) (under|in|on|behind) the\b|\blocated (under|in|on)\b", "gives a navigation hint"),
    (r"\ball \d+\b|\b\d+ (records|items|rows|grantees|results)\b", "states a count the user may not know"),
    (r"\b(fix|repair|patch|change we made)\b", "mentions a fix"),
]
RUN_ID_PATTERN = (r"\b(retest|ablation|regress\w*|control|variant|without|minus|after|before)\b|\bno-[a-z]+",
                  "describes the run's design; use a neutral ID")
DEV_LABELS = {"localhost", "local", "test", "testing", "staging", "stage", "stg", "dev", "develop",
              "development", "qa", "uat", "sandbox", "preview", "demo", "internal"}
DEV_TLDS = {"localhost", "local", "test", "internal", "example", "invalid"}


def read_data(path, what):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        import yaml  # type: ignore
    except ImportError:
        sys.exit(f"PyYAML is not installed. Install it (pip install pyyaml) or provide {what} as JSON.")
    return yaml.safe_load(text)


def load_params(path):
    return read_data(path, "params") or {}


def find_config(start):
    for d in [start, *start.parents]:
        for name in ("config.yaml", "config.yml", "config.json"):
            p = d / ".bag-of-rocks" / name
            if p.exists():
                return p
    return None


def load_config(p, params_path):
    path = Path(p["config"]).expanduser() if p.get("config") else find_config(params_path.parent)
    if not path:
        return {}, None
    return read_data(path, "config") or {}, path


def load_intended(folder):
    """Return (intended path, problem). Readable by both helpers; JSON needs no PyYAML."""
    for name in ("intended-path.json", "intended-path.yaml", "intended-path.yml"):
        p = folder / "coordinator" / name
        if p.exists():
            try:
                return read_data(p, "the intended path") or {}, None
            except (SystemExit, Exception) as e:
                return {}, f"coordinator/{name} could not be read ({e})"
    return {}, None


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


def split_trait(t):
    """'FC:5' -> ('FC', 5); 'Fidget Clicker' -> ('FC', None)."""
    name, _, level = str(t).strip().partition(":")
    name = name.strip()
    return NAMES.get(name.lower(), name.upper()), (int(level) if level.strip().isdigit() else None)


def norm_trait(t):
    return split_trait(t)[0]


def resolve_traits(p, config=None):
    """Return (preset, traits, fc_intensity). Explicit fc_intensity beats a preset's FC:N."""
    config = config or {}
    preset = p.get("preset") or config.get("default_preset") or "full-bag"
    custom = {**(config.get("presets") or {}), **(p.get("presets") or {})}
    if preset in custom:
        entries = list(custom[preset])
    elif preset in PRESETS:
        entries = list(PRESETS[preset])
    else:
        sys.exit(f"Unknown preset '{preset}'. Known: {', '.join(list(PRESETS) + list(custom))}")
    base, fc = [], None
    for t in entries:
        code, level = split_trait(t)
        if code not in base:
            base.append(code)
        if code == "FC" and level:
            fc = level
    for t in p.get("traits_remove", []) or []:
        t = norm_trait(t)
        if t in base:
            base.remove(t)
    for t in p.get("traits_add", []) or []:
        code, level = split_trait(t)
        if code not in base:
            base.append(code)
        if code == "FC" and level:
            fc = level
    if p.get("fc_intensity") is not None:
        fc = int(p["fc_intensity"])
    return preset, base, fc or 3


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def looks_like_dev(host):
    host = (host or "").lower().strip("[]")
    if not host or host in ("::1", "0.0.0.0") or re.match(r"^(127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)", host):
        return True
    labels = re.split(r"\.", host)
    if labels[-1] in DEV_TLDS:
        return True
    return any(part in DEV_LABELS for label in labels[:-1] for part in re.split(r"-", label))


def apply_environment(p, config):
    """Apply config environments and the production guard. Returns notices."""
    notices = []
    start = str(p.get("start_url", ""))
    env_name, env = None, None
    for name, e in (config.get("environments") or {}).items():
        base = str((e or {}).get("base_url", "")).rstrip("/")
        if base and (start == base or start.startswith(base + "/")):
            env_name, env = name, e or {}
            break
    if env:
        extra = [x for x in as_list(env.get("prohibited")) if x not in as_list(p.get("prohibited_effects"))]
        if extra:
            p["prohibited_effects"] = as_list(p.get("prohibited_effects")) + extra
            notices.append(f"Added prohibited effects from config environment '{env_name}'.")
        if env.get("mutations") == "none" and p.get("mutations", "allowed") != "none":
            p["mutations"] = "none"
            notices.append(f"Mutations forced to none: config environment '{env_name}' allows none.")
    elif p.get("mutations", "allowed") != "none" and not looks_like_dev(urlparse(start).hostname):
        p["mutations"] = "none"
        notices.append(f"Mutations forced to none: {urlparse(start).hostname or start!r} looks like production. "
                       "Declare it in .bag-of-rocks/config.yaml environments to allow mutations.")
    return notices


def run_block(p, preset, traits, fc):
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
        lines.append(f"Fidget Clicker intensity: up to {fc} extra clicks.")
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


def tester_fields(p, preset):
    """Every coordinator-supplied value that reaches the tester."""
    fields = {k: p.get(k, "") for k in ("goal", "allowed_effects", "account", "device")}
    if preset not in PRESETS:
        fields["preset"] = preset
    phr = p.get("phrasing")
    if isinstance(phr, dict) and "fixed" in phr:
        fields["phrasing.fixed"] = phr["fixed"]
    for key in ("user_facts", "prohibited_effects"):
        for i, f in enumerate(as_list(p.get(key))):
            fields[f"{key}[{i}]"] = f
    return fields


def answer_key_labels(intended):
    """Quoted labels from the intended path's cues, e.g. "Edit" from '"Edit" link beside ...'."""
    labels = set()
    for s in intended.get("steps", []) or []:
        for k in ("intended_cue", "cue"):
            for m in re.finditer(r"[\"“]([^\"”]{2,60})[\"”]|(?<!\w)'([^']{2,60})'(?!\w)", str(s.get(k, "") or "")):
                labels.add((m.group(1) or m.group(2)).strip())
    return sorted(labels)


def lint(p, preset, intended=None):
    warnings = []
    fields = tester_fields(p, preset)
    for name, val in fields.items():
        for pat, why in FLAG_PATTERNS:
            if re.search(pat, str(val), re.I):
                warnings.append(f"{name}: {why} -> {val!r}")
    if re.search(RUN_ID_PATTERN[0], str(p.get("run_id", "")), re.I):
        warnings.append(f"run_id: {RUN_ID_PATTERN[1]} -> {p.get('run_id')!r}")
    for label in answer_key_labels(intended or {}):
        for name, val in fields.items():
            if re.search(r"(?<!\w)" + re.escape(label) + r"(?!\w)", str(val), re.I):
                warnings.append(f"{name}: contains answer-key label {label!r} from the intended path -> {val!r}")
    for k in ("intended_path", "assumptions", "findings", "notes", "expected"):
        if k in p:
            warnings.append(f"params contain '{k}', which must not reach the tester (it is not included, but keep it out of this file)")
    return warnings


def config_warnings(p, traits):
    warnings = []
    if "TR" in traits and not re.search(r"phone|mobile|iphone|android|\b[1-6]\d\d\s*[x×]\s*\d+", str(p.get("device", "")), re.I):
        warnings.append(f"Thumb Reacher needs a phone viewport; device is {p.get('device', 'unset')!r}")
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
    config, config_path = load_config(p, params_path)
    notices = apply_environment(p, config)

    skill_dir = Path(p.get("skill_dir") or Path(__file__).resolve().parent.parent).expanduser()
    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    traits_md = (skill_dir / "references" / "traits.md").read_text(encoding="utf-8")
    report_md = (skill_dir / "references" / "review-and-report.md").read_text(encoding="utf-8")
    version = re.search(r"Version (\d+\.\d+\.\d+)", skill_md)
    version = version.group(1) if version else "unknown"

    preset, traits, fc = resolve_traits(p, config)
    cards = trait_cards(traits_md)
    missing = [t for t in traits if t not in cards]
    if missing:
        sys.exit(f"No trait card found for: {', '.join(missing)}")

    packet = "\n\n".join([
        run_block(p, preset, traits, fc),
        "## How to be the rock\n\n" + between(skill_md, "<!-- PHASE1:START -->", "<!-- PHASE1:END -->", "Phase 1"),
        "## Your traits\n\n" + "\n\n".join(cards[t] for t in traits),
        "## Trace format\n\n" + between(report_md, "<!-- TRACE:START -->", "<!-- TRACE:END -->", "trace"),
        f"(bag-of-rocks {version} packet)",
    ]) + "\n"

    out_dir = params_path.parent
    (out_dir / "tester-packet.txt").write_text(packet, encoding="utf-8")
    digest = hashlib.sha256(packet.encode("utf-8")).hexdigest()
    (out_dir / "tester-packet.sha256").write_text(f"{digest}  tester-packet.txt\n", encoding="utf-8")
    phr = p.get("phrasing", "own-words")
    record = {
        "run_id": p.get("run_id", ""), "goal": p["goal"], "start_url": p["start_url"],
        "preset": preset, "traits": traits, "fc_intensity": fc if "FC" in traits else None,
        "phrasing": "fixed" if isinstance(phr, dict) else phr, "mutations": p.get("mutations", "allowed"),
        "prohibited_effects": as_list(p.get("prohibited_effects")), "sha256": digest, "skill_version": version,
        "config": str(config_path) if config_path else None, "notices": notices,
    }
    (out_dir / "tester-packet.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Packet written: {out_dir / 'tester-packet.txt'}")
    print(f"SHA-256: {digest}")
    print(f"Skill version {version}; preset {preset}; traits {', '.join(traits)}")
    if config_path:
        print(f"Config: {config_path}")
    for n in notices:
        print("Notice: " + n)
    intended, problem = load_intended(out_dir)
    warnings = lint(p, preset, intended) + config_warnings(p, traits)
    if problem:
        warnings.append(problem + "; answer-key check skipped")
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
