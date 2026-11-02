#!/usr/bin/env python3
"""Convert a frozen bag-of-rocks tester trace into reviewer artifacts.

Usage:
    python scripts/trace_to_run.py <run-folder>               # write run.json skeleton + trace-readable.md
    python scripts/trace_to_run.py <run-folder> --force       # regenerate run.json, keeping reviewer fields
    python scripts/trace_to_run.py <run-folder> --filmstrip   # generate a read-only report
    python scripts/trace_to_run.py <run-folder> --filmstrip --calibration  # enable tester verdicts

Expects <run-folder>/tester/trace.json and screenshots under <run-folder>/tester/.
Optionally reads <run-folder>/run-params.(yaml|json), tester-packet.(txt|sha256|json),
and coordinator/intended-path.(json|yaml).

Never modifies anything under tester/. On first conversion, writes tester.sha256 (a
manifest of every tester file); later conversions verify it. Verifies the packet hash,
compares the trace header with the run settings, detects each screenshot's real format
and size from its bytes, converts pixel clicks and ignored boxes to percentages, and
reports trace problems for the Limits section.
"""
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True  # keep installed skill folders free of __pycache__
from build_packet import load_intended, norm_trait, read_data, resolve_traits  # noqa: E402

STOP_REASONS = {"believed complete", "blocked", "abandoned (patience)", "abandoned (stall)", "budget", "permission stop"}
AUTO_LIMITS = ("Perception:", "Trace problem:", "Packet:", "Tester files:", "Ambient:")


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
        if p.exists():
            try:
                return read_data(p, "params") or {}, None
            except (SystemExit, Exception) as e:
                return {}, f"{name} could not be read ({e}); header checks used the trace alone"
    return {}, None


def pct(v, total):
    return round(100.0 * v / total, 2) if total else None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tester_manifest(tester):
    return {f.relative_to(tester).as_posix(): sha(f) for f in sorted(tester.rglob("*")) if f.is_file()}


def check_freeze(folder, tester):
    """Write tester.sha256 on first conversion; afterwards report any drift."""
    current = tester_manifest(tester)
    path = folder / "tester.sha256"
    if not path.exists():
        path.write_text("".join(f"{h}  {n}\n" for n, h in current.items()), encoding="utf-8")
        return f"Tester files: {len(current)} frozen in tester.sha256 at first conversion", []
    frozen = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        h, _, n = line.partition("  ")
        if n:
            frozen[n] = h
    problems = [f"Tester file changed after freezing: tester/{n}" for n in frozen if n in current and current[n] != frozen[n]]
    problems += [f"Tester file removed after freezing: tester/{n}" for n in frozen if n not in current]
    problems += [f"Tester file added after freezing: tester/{n}" for n in current if n not in frozen]
    note = f"Tester files: {len(frozen)} frozen in tester.sha256" + ("; verified unchanged" if not problems else "")
    return note, problems


def check_packet(folder):
    """Return (sha256 or '', note, problems) for the packet the tester was given."""
    txt, rec = folder / "tester-packet.txt", folder / "tester-packet.sha256"
    if not txt.exists():
        return "", None, ["No tester-packet.txt in the run folder; packet hash unverified"]
    digest = sha(txt)
    if rec.exists() and rec.read_text(encoding="utf-8").split()[:1] != [digest]:
        return digest, None, ["tester-packet.txt no longer matches tester-packet.sha256"]
    return digest, f"Packet: SHA-256 {digest}" + (" (matches build record)" if rec.exists() else " (no build record)"), []


def merge_review(old, new):
    """Carry reviewer-written fields from an existing run.json into a regenerated one."""
    o_out, n_out = old.get("outcome") or {}, new["outcome"]
    for k in ("supported", "gap"):
        if o_out.get(k):
            n_out[k] = o_out[k]
    for k in ("summary", "findings", "errata"):
        if old.get(k):
            new[k] = old[k]
    if old.get("intended") and not new["intended"]:
        new["intended"] = old["intended"]
    status = {a.get("text"): a.get("status", "") for a in old.get("assumptions") or [] if isinstance(a, dict)}
    for a in new["assumptions"]:
        a["status"] = status.get(a["text"], a["status"])
    if old.get("assumptions") and not new["assumptions"]:
        new["assumptions"] = old["assumptions"]
    by_id = {s.get("id"): s for s in old.get("steps") or []}
    for s in new["steps"]:
        prev = by_id.get(s["id"]) or {}
        for k in ("divergence", "harness_note"):
            if prev.get(k):
                s[k] = prev[k]
        s["untested"] = s["untested"] or bool(prev.get("untested"))
    new["steps"] += [s for s in old.get("steps") or [] if s.get("kind") == "reviewer"]
    new["limits"] += [x for x in old.get("limits") or [] if not str(x).startswith(AUTO_LIMITS)]
    for k in ("mode", "conditions"):
        if (old.get("run") or {}).get(k) and not new["run"].get(k):
            new["run"][k] = old["run"][k]
    return new


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    folder = Path(args[0]).expanduser().resolve()
    force = "--force" in sys.argv
    calibration = "--calibration" in sys.argv
    if calibration and "--filmstrip" not in sys.argv:
        sys.exit("--calibration requires --filmstrip.")

    if "--filmstrip" in sys.argv:
        run_json = folder / "run.json"
        if not run_json.exists():
            sys.exit("No run.json yet. Run without --filmstrip first.")
        template = (SKILL_DIR / "assets" / "filmstrip.html").read_text(encoding="utf-8")
        if calibration:
            template = template.replace("const CALIBRATION = false;", "const CALIBRATION = true;", 1)
        data = run_json.read_text(encoding="utf-8").replace("</", "<\\/")
        out = re.sub(r'(<script id="run-data" type="application/json">)(.*?)(</script>)',
                     lambda m: m.group(1) + "\n" + data + "\n" + m.group(3), template, count=1, flags=re.S)
        (folder / "filmstrip.html").write_text(out, encoding="utf-8")
        print(f"Filmstrip written: {folder / 'filmstrip.html'}")
        return

    tester = folder / "tester"
    freeze_note, problems = check_freeze(folder, tester)
    trace = json.loads((tester / "trace.json").read_text(encoding="utf-8"))
    header = trace.get("header", {}) or {}
    params, params_problem = load_params(folder)
    if params_problem:
        problems.append(params_problem)
    packet_sha, packet_note, packet_problems = check_packet(folder)
    problems += packet_problems
    review_checks, dims, mismatched = [], {}, []

    # Effective settings: the packet builder's record wins over raw params (it applies config and forcing).
    built = {}
    if (folder / "tester-packet.json").exists():
        try:
            built = json.loads((folder / "tester-packet.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            problems.append("tester-packet.json could not be parsed")
    active, resolved_preset = list(built.get("traits") or []), built.get("preset")
    if not active and params:
        try:
            resolved_preset, active, _ = resolve_traits(params)
        except SystemExit:
            pass
    params_phr = params.get("phrasing", "own-words") if params else None
    expected = {
        "run_id": built.get("run_id", params.get("run_id")),
        "goal": built.get("goal", params.get("goal")),
        "start": built.get("start_url", params.get("start_url")),
        "preset": resolved_preset,
        "mutations": built.get("mutations", params.get("mutations")),
        "phrasing": built.get("phrasing", "fixed" if isinstance(params_phr, dict) else params_phr),
    }
    for k, want in expected.items():
        got = header.get(k)
        if want and got and str(got).strip().rstrip("/") != str(want).strip().rstrip("/"):
            problems.append(f"Header {k} {got!r} differs from the run settings {want!r}")
    header_traits = [norm_trait(t) for t in header.get("traits", []) or []]
    if active and header_traits and sorted(header_traits) != sorted(active):
        problems.append(f"Header traits {header_traits} differ from the packet's active traits {active}")
    active = active or header_traits

    viewport = header.get("viewport") or {}
    vw, vh = viewport.get("width") or 0, viewport.get("height") or 0
    click_space = header.get("click_space", "screenshot")
    if click_space == "viewport" and not (vw and vh):
        problems.append("Header click_space is 'viewport' but viewport width/height are missing; clicks treated as screenshot pixels")
        click_space = "screenshot"
    scale_flagged = []

    def shot_info(rel):
        if not rel:
            return None
        if rel in dims:
            return dims[rel]
        path = (tester / rel).resolve()
        if not path.is_relative_to(tester.resolve()):
            problems.append(f"Screenshot path leaves tester/: {rel}")
            dims[rel] = (None, None, None)
            return dims[rel]
        if not path.exists():
            problems.append(f"Screenshot missing: tester/{rel}")
            dims[rel] = (None, None, None)
            return dims[rel]
        fmt, w, h = sniff(path)
        if fmt and path.suffix.lower() not in EXT_OK.get(fmt, set()):
            mismatched.append(rel)
        if not w:
            problems.append(f"Could not read dimensions: tester/{rel}")
        elif vw and click_space == "screenshot" and abs(w / vw - 1) > 0.05 and not scale_flagged:
            scale_flagged.append(rel)
            problems.append(f"Screenshot tester/{rel} is {w}px wide but the viewport is {vw}px (scale {w / vw:.2f}). "
                            "If clicks were recorded in page coordinates, set header.click_space to 'viewport' and reconvert")
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
        if click_space == "viewport":
            w, h = vw, vh
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
            if not shot:
                problems.append(f"{sid}: action with no screenshot")
            if not s.get("result_screenshot"):
                problems.append(f"{sid}: action with no result_screenshot")
        if kind == "wait" and not shot:
            problems.append(f"{sid}: wait step with no screenshot")
        tags = [norm_trait(t) for t in traits if str(t).lower() != "ordinary"]
        if len(tags) > 2:
            problems.append(f"{sid}: more than two trait tags")
        if tags and len(tags) != len(traits):
            problems.append(f"{sid}: mixes 'ordinary' with trait tags")
        inactive = [t for t in tags if active and t not in active]
        if inactive:
            problems.append(f"{sid}: trait tag(s) {', '.join(inactive)} weren't active in this run")
        if "FC" in tags:
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
    if end.get("stop_reason") and end["stop_reason"] not in STOP_REASONS:
        problems.append(f"Unknown stop_reason {end['stop_reason']!r}; expected one of: {', '.join(sorted(STOP_REASONS))}")
    entered = next((st["entered_text"] for st in steps_out if st["entered_text"]), "")

    intended_doc, intended_problem = load_intended(folder)
    if intended_problem:
        problems.append(intended_problem)
    intended = [{"id": i.get("id", ""), "screen": i.get("screen", ""),
                 "cue": i.get("cue") or i.get("intended_cue", ""), "action": i.get("action") or i.get("intended_action", "")}
                for i in intended_doc.get("steps", []) or [] if isinstance(i, dict)]
    assumptions = [{"text": a if isinstance(a, str) else a.get("text", ""),
                    "status": "" if isinstance(a, str) else a.get("status", "")}
                   for a in intended_doc.get("assumptions", []) or []]

    skill_version = re.search(r"Version (\d+\.\d+\.\d+)", (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))
    run = {
        "run": {
            "id": header.get("run_id") or expected["run_id"] or folder.name,
            "date": (header.get("started_at") or "")[:10],
            "goal": header.get("goal") or expected["goal"] or "",
            "start": header.get("start") or expected["start"] or "",
            "preset": header.get("preset") or expected["preset"] or "",
            "traits": header.get("traits") or active,
            "phrasing": header.get("phrasing") or expected["phrasing"] or "own-words",
            "entered_text": entered,
            "mutations": header.get("mutations") or expected["mutations"] or "",
            "conditions": params.get("conditions", []),
            "perception": header.get("perception", ""),
            "mode": params.get("mode", "fast"),
            "inherited_state": params.get("inherited_state", ""),
            "packet_sha256": packet_sha,
            "skill_version": skill_version.group(1) if skill_version else "",
        },
        "outcome": {"believed": end.get("belief", ""), "supported": "", "gap": ""},
        "summary": [], "intended": intended, "assumptions": assumptions,
        "steps": steps_out, "findings": [], "errata": [],
        "limits": ([f"Perception: {header.get('perception')} ({header.get('perception_note', '')})"] if header.get("perception") else [])
                  + ([packet_note] if packet_note else []) + [freeze_note]
                  + ([f"Ambient: instruction files likely loaded by the tester: {', '.join(built['ambient_instructions'])}"] if built.get("ambient_instructions") else [])
                  + (["Ambient: run folder was inside the tester's working directory; coordinator files were readable (instruction-only blinding)"] if built.get("run_folder_in_cwd") else [])
                  + [f"Trace problem: {p}" for p in problems],
        "end": end,
    }

    out_json = folder / "run.json"
    if out_json.exists() and not force:
        print(f"run.json exists; not overwritten (use --force to regenerate it and keep reviewer fields). Problems still reported below.")
    else:
        if out_json.exists():
            run = merge_review(json.loads(out_json.read_text(encoding="utf-8")), run)
            print("Kept reviewer fields from the existing run.json (outcome, summary, findings, errata, assumption status, divergences, harness notes, reviewer steps, added limits).")
        out_json.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Run data written: {out_json}")

    md = [f"# Trace: {run['run']['goal']}", "",
          f"Run `{run['run']['id']}` · preset {run['run']['preset']} · phrasing {run['run']['phrasing']} · mutations {run['run']['mutations']} · perception {run['run']['perception']}", ""]
    if entered:
        md += [f"Entered text: `{entered}`", ""]
    for st in steps_out:
        md.append(f"## `{st['id']}` · {st['kind']}")
        md.append("")
        for label, key in (("Cue", "cue"), ("Expectation", "expectation"), ("Action", "action"),
                           ("Entered", "entered_text"), ("Result", "result"), ("Then", "updated"),
                           ("Corrects", "corrects"), ("Note", "note")):
            if st.get(key):
                md.append(f"**{label}:** {st[key]}\n")
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
    print("\nNext: fill outcome, findings, divergences, assumption status, and summary in run.json, then run with --filmstrip.")


if __name__ == "__main__":
    main()
