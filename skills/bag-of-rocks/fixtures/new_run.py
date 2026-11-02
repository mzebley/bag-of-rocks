#!/usr/bin/env python3
"""Set up a blind calibration run against one planted fixture.

Usage:
    python3 fixtures/new_run.py <fixture> [--without TRAIT] [--preset NAME]
                                [--base-url URL] [--root DIR]

Creates <root>/run-<date>-<hex>/ with run-params.json and coordinator/intended-path.json,
then builds the tester packet with scripts/build_packet.py --strict. The run folder name,
run ID, and start URL never contain the fixture name, so nothing in the packet reveals the test.

Fixtures: silent-submit, hint-only-format, decoy-primary, done-discards, scary-routine,
dead-end, clean-control. Serve the pages first:
    python3 -m http.server 8000 --bind 127.0.0.1 --directory fixtures/site
"""
import argparse
import datetime
import json
import secrets
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIXTURES = sorted(p.stem for p in (HERE / "paths").glob("*.json"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fixture", choices=FIXTURES)
    ap.add_argument("--without", action="append", default=[], metavar="TRAIT",
                    help="remove a trait from the preset (repeatable), for the trait-off comparison run")
    ap.add_argument("--preset", default="full-bag")
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--root", default=".bag-of-rocks/runs", help="parent folder for run folders (default: ./.bag-of-rocks/runs)")
    a = ap.parse_args()

    path = json.loads((HERE / "paths" / f"{a.fixture}.json").read_text(encoding="utf-8"))
    run_id = f"run-{datetime.date.today():%Y%m%d}-{secrets.token_hex(3)}"
    run_dir = Path(a.root).expanduser().resolve() / run_id
    (run_dir / "coordinator").mkdir(parents=True)
    (run_dir / "tester").mkdir()

    params = {
        "run_id": run_id,
        "goal": path["goal"],
        "start_url": f"{a.base_url.rstrip('/')}/{path['page']}",
        "account": "none (no sign-in)",
        "preset": a.preset,
        "traits_remove": a.without,
        "phrasing": "own-words",
        "mutations": "allowed",
        "allowed_effects": "Any change inside this local site",
        "prohibited_effects": ["Visiting any site other than the start URL's host", "Real outbound messages"],
        "budget": {"actions": 25, "minutes": 10},
        "user_facts": path["user_facts"],
        "output_dir": str(run_dir / "tester"),
    }
    (run_dir / "run-params.json").write_text(json.dumps(params, indent=2) + "\n", encoding="utf-8")
    (run_dir / "coordinator" / "intended-path.json").write_text(json.dumps(path, indent=2) + "\n", encoding="utf-8")

    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_packet.py"),
                             str(run_dir / "run-params.json"), "--strict"])
    print(f"\nFixture {a.fixture} -> {run_dir}")
    print(f"Start URL: {params['start_url']}  (open {params['start_url']}?reset once beforehand to clear saved state)")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
