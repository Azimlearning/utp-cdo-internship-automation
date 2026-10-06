"""Regenerate the per-flow parts of the tracking docs from refdocs/updates/flows.json, then check the docs hang together.

    python tools/docs.py          # rewrite the generated blocks + run the checks
    python tools/docs.py check    # checks only

Generated (between <!-- generated:... --> markers, never edit inside them by hand):
  refdocs/updates/FLOW-TRACKER.md   the flow table
  refdocs/updates/ISSUES-BY-FLOW.md one section per flow
Everything outside the markers (cross-cutting findings, intro text) stays hand-written. MANUAL-TODO.md is hand-written.
"""
import datetime
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
UPD = ROOT / "refdocs" / "updates"
DATA = UPD / "flows.json"


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))["flows"]


def tracker(flows):
    out = ["| # | Flow | Main problem(s) found | Stage | Detail | Next action |", "|---|---|---|---|---|---|"]
    for f in flows:
        doc = f"[issue doc]({f['doc']})" if f.get("doc") else "—"
        out.append(f"| {f['no']} | {f['name']} | {f['problems']} | {f['stage']} | {doc} | {f['next']} |")
    return "\n".join(out)


def issues(flows):
    out = []
    for f in flows:
        out.append(f"## Flow {f['no']}: {f.get('title') or f['name']}\n")
        if f.get("issues"):
            out += ["| ID | Issue | Evidence | Fix status |", "|---|---|---|---|"]
            out += ["| " + " | ".join(r) + " |" for r in f["issues"]]
        else:
            out.append(f"Not reviewed yet. Known before review: {f.get('prereview', '—')}")
        out.append("")
    return "\n".join(out).rstrip()


def replace_block(path, name, body):
    text = path.read_text(encoding="utf-8")
    start, end = f"<!-- generated:{name} (python tools/docs.py; edit flows.json, not this block) -->", f"<!-- /generated:{name} -->"
    if start not in text:
        raise SystemExit(f"{path.name}: marker {start} missing")
    pre, rest = text.split(start, 1)
    _, post = rest.split(end, 1)
    new = pre + start + "\n" + body + "\n" + end + post
    new = re.sub(r"^Last updated: \d{4}-\d{2}-\d{2}\.", f"Last updated: {datetime.date.today().isoformat()}.", new, count=1, flags=re.M)
    if new != text:
        path.write_text(new, encoding="utf-8")
        print(f"updated {path.relative_to(ROOT).as_posix()}")


def check(flows):
    bad = []
    nums = [f["no"] for f in flows]
    if sorted(nums) != list(range(1, 15)):
        bad.append(f"flows.json should hold flows 1-14 once each, has {sorted(nums)}")
    fixes = {int(p.stem[1:3]) for p in (ROOT / "tools" / "fixes").glob("f[0-9][0-9]_*.py")}
    for f in flows:
        tested = "sandbox tested" in f["stage"].lower()
        if f.get("doc") and not (UPD / f["doc"]).resolve().exists():
            bad.append(f"flow {f['no']}: issue doc link is broken: {f['doc']}")
        if tested and f["no"] not in fixes:
            bad.append(f"flow {f['no']}: marked sandbox tested but has no tools/fixes/f{f['no']:02d}_*.py")
        if tested and not (ROOT / "refdocs" / "issues" / "evidence" / f"flow-{f['no']:02d}").exists():
            bad.append(f"flow {f['no']}: marked sandbox tested but has no evidence folder")
        if f["no"] in fixes and not f.get("doc"):
            bad.append(f"flow {f['no']}: has a fix module but no issue doc")
        ids = [r[0] for r in f.get("issues", [])]
        if len(ids) != len(set(ids)):
            bad.append(f"flow {f['no']}: duplicate issue ids")
    for b in bad:
        print("CHECK:", b)
    print("checks:", "ok" if not bad else f"{len(bad)} problem(s)")
    return not bad


def main(a):
    sys.stdout.reconfigure(encoding="utf-8")
    flows = load()
    if a[:1] != ["check"]:
        replace_block(UPD / "FLOW-TRACKER.md", "tracker", tracker(flows))
        replace_block(UPD / "ISSUES-BY-FLOW.md", "issues", issues(flows))
    sys.exit(0 if check(flows) else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
