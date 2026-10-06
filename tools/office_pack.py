"""Build everything the next office-laptop session needs, in one place.

    python tools/office_pack.py

Writes:
  build/office/flowNN-prod.zip           every flow with a fix module, built against production (Import -> Update only)
  build/office/flowNN-probe.zip          the same plus a first step in the Try scope that always fails (proves the alert path in
                                         production without touching data; Update with the prod zip right after)
  refdocs/updates/OFFICE-CHECKLIST.md    one ordered checklist: global prep, then per flow its readiness, package, sha256,
                                         and the "Office steps" copied from its issue doc
Readiness comes from refdocs/updates/flows.json (the flow's Stage); a flow not yet sandbox tested is listed as NOT READY.
Re-run after any fix changes: the checklist records each package's hash, so a stale zip on the office laptop is detectable.
"""
import datetime
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OFFICE = ROOT / "build" / "office"
CHECKLIST = ROOT / "refdocs" / "updates" / "OFFICE-CHECKLIST.md"

PREP = """## Before touching any flow (once per visit)

1. Sign in on the office admin laptop with the account that owns the flows. Check **Connections** for *Reconnect* first (an expired connection fails with `Unauthorized` and also silences the FAILED alerts).
2. Copy `build/office/` to the laptop (or rebuild there with `python tools/office_pack.py`). Compare each zip's sha256 with the table below.
3. **Per flow, in this order** (full detail and the stop rules: `refdocs/execution/2026-10-02-real-system-rollout.md`): export a fresh backup into `flows/` and commit it (rule 5, git is the only rollback) → Import → **Update** with the **probe** zip, re-selecting the production connections → run it once and confirm the run is **Failed**, names the Probe step and the Teams alert arrives → Import → **Update** with the **prod** zip → real test (see the rollout doc) → read the run history → re-export into `flows/` and run `python tools/compare_prod.py NN` → tick the row.
4. Never apply two flows' fixes before the first one's run history has been read (CLAUDE.md: observed, not assumed).
5. Flow 7 must run before flows 12 and 13 in any test, since they read its last output.
"""


def office_steps(doc):
    text = doc.read_text(encoding="utf-8")
    m = re.search(r"^## Office steps[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else "_No \"Office steps\" section in the issue doc yet._"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    flows = {f["no"]: f for f in json.loads((ROOT / "refdocs" / "updates" / "flows.json").read_text(encoding="utf-8"))["flows"]}
    fixes = sorted(int(p.stem[1:3]) for p in (ROOT / "tools" / "fixes").glob("f[0-9][0-9]_*.py"))
    OFFICE.mkdir(parents=True, exist_ok=True)
    rows, sections = [], []
    for n in fixes:
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), f"{n:02d}", "prod"], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"flow {n}: prod build failed:\n{r.stdout}{r.stderr}")
        src = ROOT / "build" / "prod" / f"flow{n:02d}-prod.zip"
        dst = OFFICE / src.name
        shutil.copy2(src, dst)
        sha = hashlib.sha256(dst.read_bytes()).hexdigest()[:16]
        pr = subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), f"{n:02d}", "probe"], capture_output=True, text=True)
        psrc = ROOT / "build" / "probe" / f"flow{n:02d}-probe.zip"
        if pr.returncode == 0 and psrc.exists():
            shutil.copy2(psrc, OFFICE / psrc.name)
            probe = f"`{psrc.name}`"
        else:
            probe = "— (no Try scope)"
        f = flows[n]
        ready = "sandbox tested" in f["stage"].lower()
        status = "ready" if ready else "**NOT READY**"
        rows.append(f"| ☐ | {n} | {f['name']} | {status} | {probe} | `{dst.name}` | `{sha}` |")
        doc = (ROOT / "refdocs" / "updates" / f["doc"]).resolve() if f.get("doc") else None
        steps = office_steps(doc) if doc and doc.exists() else "_No issue doc._"
        link = f"[issue doc]({f['doc']})" if f.get("doc") else "no issue doc"
        sections.append(f"### Flow {n}: {f['name']} ({status})\n\nPackage `build/office/{dst.name}` (sha256 `{sha}…`), probe: {probe}, "
                        f"{link}. Still open: {f['next']}\n\n{steps}\n")
    not_fixed = [f"{n} {flows[n]['name']}" for n in sorted(flows) if n not in fixes]
    out = [
        "# Office-Laptop Checklist",
        "",
        f"Generated {datetime.date.today().isoformat()} by `python tools/office_pack.py` from flows.json and the issue docs. "
        "Do not edit by hand; re-run it after any fix changes.",
        "",
        PREP,
        "## Packages",
        "",
        "| Done | # | Flow | Sandbox status | Probe package | Prod package | prod sha256 (first 16) |",
        "|---|---|---|---|---|---|---|",
        *rows,
        "",
        f"No fix built yet: {', '.join(not_fixed) or 'none'}.",
        "",
        "## Per-flow steps",
        "",
        *sections,
    ]
    CHECKLIST.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"{len(fixes)} packages in {OFFICE.relative_to(ROOT).as_posix()}/, checklist {CHECKLIST.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
