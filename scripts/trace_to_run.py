#!/usr/bin/env python3
"""Convert a frozen bag-of-rocks tester trace into reviewer artifacts.

Usage:
    python scripts/trace_to_run.py <run-folder>               # write run.json skeleton + trace-readable.md
    python scripts/trace_to_run.py <run-folder> --force       # overwrite an existing run.json
    python scripts/trace_to_run.py <run-folder> --filmstrip   # embed the current run.json into filmstrip.html

Expects <run-folder>/tester/trace.json and screenshots under <run-folder>/tester/.
Optionally reads <run-folder>/run-params.(yaml|json) and <run-folder>/coordinator/intended-path.json.

Never modifies anything under tester/. Detects each screenshot's real format and size
from its bytes (not its extension), converts pixel clicks and ignored boxes to
percentages, and reports trace problems for the Limits section.
"""
import json
import re
import struct
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent


def sniff(path):
    """Return (format, width, height) from file bytes, or (None, None, None)."""
    try:
        data = path.read_bytes()
    except OSError:
        return None, None, None
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return "png", w, h
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return "jpeg", w, h
            i += 2 + seg_len
        return "jpeg", None, None
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", None, None
    return None, None, None


EXT_OK = {"png": {".png"}, "jpeg": {".jpg", ".jpeg"}, "webp": {".webp"}}


def load_params(folder):
    for name in ("run-params.json", "run-params.yaml", "run-params.yml"):
        p = folder / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                import yaml  # type: ignore
                return yaml.safe_load(text) or {}
            except Exception:
                return {}
    return {}


def pct(v, total):
    return round(100.0 * v / total, 2) if total else None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    folder = Path(args[0]).expanduser().resolve()
    force = "--force" in sys.argv

    if "--filmstrip" in sys.argv:
        run_json = folder / "run.json"
        if not run_json.exists():
            sys.exit("No run.json yet. Run without --filmstrip first.")
        template = (SKILL_DIR / "assets" / "filmstrip.html").read_text(encoding="utf-8")
        data = run_json.read_text(encoding="utf-8").replace("</", "<\\/")
        out = re.sub(r'(<script id="run-data" type="application/json">)(.*?)(</script>)',
                     lambda m: m.group(1) + "\n" + data + "\n" + m.group(3), template, count=1, flags=re.S)
        (folder / "filmstrip.html").write_text(out, encoding="utf-8")
        print(f"Filmstrip written: {folder / 'filmstrip.html'}")
        return

    tester = folder / "tester"
    trace = json.loads((tester / "trace.json").read_text(encoding="utf-8"))
    header = trace.get("header", {}) or {}
    params = load_params(folder)
    problems, review_checks, dims, mismatched = [], [], {}, []

    def shot_info(rel):
        if not rel:
            return None
        if rel in dims:
            return dims[rel]
        path = tester / rel
        if not path.exists():
            problems.append(f"Screenshot missing: tester/{rel}")
            dims[rel] = (None, None, None)
            return dims[rel]
        fmt, w, h = sniff(path)
        if fmt and path.suffix.lower() not in EXT_OK.get(fmt, set()):
            mismatched.append(rel)
        if not w:
            problems.append(f"Could not read dimensions: tester/{rel}")
        dims[rel] = (fmt, w, h)
        return dims[rel]

    steps_out = []
    for s in trace.get("steps", []):
        sid = s.get("id", "?")
        kind = s.get("kind", "checkpoint")
        traits = s.get("traits", s.get("trait", []))
        if isinstance(traits, str):
            traits = [t.strip() for t in traits.split(",") if t.strip()]
        shot = s.get("screenshot", "")
        info = shot_info(shot) or (None, None, None)
        _, w, h = info
        if s.get("result_screenshot"):
            shot_info(s["result_screenshot"])

        clicks = []
        for c in s.get("clicks", []) or []:
            if "px" in c and c["px"] and w and h:
                clicks.append({"x": pct(c["px"][0], w), "y": pct(c["px"][1], h),
                               "n": c.get("n", 1), "approx": bool(c.get("approx"))})
            elif "x" in c and "y" in c:
                clicks.append({"x": c["x"], "y": c["y"], "n": c.get("n", 1), "approx": bool(c.get("approx"))})
            else:
                problems.append(f"{sid}: click without convertible coordinates")
        ignored = []
        for g in s.get("ignored", []) or []:
            b = g.get("box_px")
            if b and w and h:
                ignored.append({"x": pct(b[0], w), "y": pct(b[1], h), "w": pct(b[2], w), "h": pct(b[3], h),
                                "label": g.get("label", "")})
            elif "x" in g:
                ignored.append({k: g.get(k) for k in ("x", "y", "w", "h", "label")})

        result = str(s.get("result", "") or "")
        if kind == "checkpoint" and s.get("action"):
            if not result or re.search(r"\bpending\b", result, re.I):
                problems.append(f"{sid}: result is empty or pending")
            if clicks and not s.get("result_screenshot"):
                problems.append(f"{sid}: action with no result_screenshot")
        if len([t for t in traits if t != "ordinary"]) > 2:
            problems.append(f"{sid}: more than two trait tags")
        if "FC" in traits:
            review_checks.append(f"{sid}: Fidget Clicker step; confirm its screenshot shows a busy or unchanged state")
        if any(c["approx"] for c in clicks):
            review_checks.append(f"{sid}: approximate click marker (accessibility target)")

        steps_out.append({
            "id": sid, "kind": kind,
            "screenshot": f"tester/{shot}" if shot else "",
            "result_screenshot": f"tester/{s['result_screenshot']}" if s.get("result_screenshot") else "",
            "cue": s.get("cue", ""), "expectation": s.get("expectation", ""), "action": s.get("action", ""),
            "entered_text": s.get("entered_text", ""), "result": result, "updated": s.get("updated", ""),
            "traits": traits, "clicks": clicks, "ignored": ignored,
            "corrects": s.get("corrects", ""), "note": s.get("note", ""),
            "divergence": None, "harness_note": "", "untested": bool(s.get("untested")),
        })

    if mismatched:
        problems.append(f"{len(mismatched)} screenshot(s) have extensions that don't match their real format (renders fine; sizes read from bytes)")
    end = trace.get("end", {}) or {}
    entered = next((st["entered_text"] for st in steps_out if st["entered_text"]), "")
    intended = []
    ip = folder / "coordinator" / "intended-path.json"
    if ip.exists():
        try:
            for i in json.loads(ip.read_text(encoding="utf-8")).get("steps", []):
                intended.append({k: i.get(k, "") for k in ("id", "screen", "cue", "action")})
        except Exception:
            problems.append("coordinator/intended-path.json could not be parsed")

    skill_version = re.search(r"Version (\d+\.\d+\.\d+)", (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    run = {
        "run": {
            "id": header.get("run_id") or params.get("run_id") or folder.name,
            "date": (header.get("started_at") or "")[:10],
            "goal": header.get("goal") or params.get("goal", ""),
            "start": header.get("start") or params.get("start_url", ""),
            "preset": header.get("preset") or params.get("preset", ""),
            "traits": header.get("traits", []),
            "phrasing": header.get("phrasing") or (params.get("phrasing") if isinstance(params.get("phrasing"), str) else "fixed"),
            "entered_text": entered,
            "mutations": header.get("mutations") or params.get("mutations", ""),
            "conditions": params.get("conditions", []),
            "perception": header.get("perception", ""),
            "mode": params.get("mode", "fast"),
            "inherited_state": params.get("inherited_state", ""),
            "skill_version": skill_version.group(1) if skill_version else "",
        },
        "outcome": {"believed": end.get("belief", ""), "supported": "", "gap": ""},
        "summary": [], "intended": intended, "steps": steps_out, "findings": [], "errata": [],
        "limits": ([f"Perception: {header.get('perception')} ({header.get('perception_note', '')})"] if header.get("perception") else [])
                  + [f"Trace problem: {p}" for p in problems],
        "end": end,
    }

    out_json = folder / "run.json"
    if out_json.exists() and not force:
        print(f"run.json exists; not overwritten (use --force). Problems still reported below.")
    else:
        out_json.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Run data written: {out_json}")

    md = [f"# Trace: {run['run']['goal']}", "",
          f"Run {run['run']['id']} · preset {run['run']['preset']} · phrasing {run['run']['phrasing']} · mutations {run['run']['mutations']} · perception {run['run']['perception']}", ""]
    if entered:
        md += [f"Entered text: `{entered}`", ""]
    for st in steps_out:
        md.append(f"## {st['id']} ({st['kind']})")
        for label, key in (("Cue", "cue"), ("Expectation", "expectation"), ("Action", "action"),
                           ("Entered", "entered_text"), ("Result", "result"), ("Then", "updated"),
                           ("Corrects", "corrects"), ("Note", "note")):
            if st.get(key):
                md.append(f"- **{label}:** {st[key]}")
        if st["traits"]:
            md.append(f"- **Traits:** {', '.join(st['traits'])}")
        if st["clicks"]:
            md.append("- **Clicks:** " + ", ".join(f"({c['x']}%, {c['y']}%){' ×'+str(c['n']) if c['n'] > 1 else ''}{' approx' if c['approx'] else ''}" for c in st["clicks"]))
        if st["ignored"]:
            md.append("- **Not read:** " + "; ".join(g.get("label", "") for g in st["ignored"]))
        if st["screenshot"]:
            md.append(f"\n![{st['id']}]({st['screenshot']})")
        if st["result_screenshot"]:
            md.append(f"\n![{st['id']} result]({st['result_screenshot']})")
        md.append("")
    md += ["## End", f"- **Believed:** {end.get('belief', '')}", f"- **Cue:** {end.get('supporting_cue', '')}",
           f"- **Stop reason:** {end.get('stop_reason', '')}", f"- **Untested:** {', '.join(end.get('untested', []) or []) or 'none'}"]
    (folder / "trace-readable.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Readable trace written: {folder / 'trace-readable.md'}")

    print("\nTrace problems (carry into Limits):" if problems else "\nNo trace problems found.")
    for p in problems:
        print("  - " + p)
    if review_checks:
        print("\nReviewer checks:")
        for c in review_checks:
            print("  - " + c)
    print("\nNext: fill outcome, findings, divergences, and summary in run.json, then run with --filmstrip.")


if __name__ == "__main__":
    main()
