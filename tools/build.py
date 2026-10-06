"""Build importable flow packages from the exports in flows/.

    python tools/build.py 01 baseline   # sandbox copy, UNCHANGED logic — reproduce today's behaviour
    python tools/build.py 01 fixed      # sandbox copy WITH the fix — prove the fix works
    python tools/build.py 01 prod       # fix against production IDs — only for the office laptop (Import -> Update)
    python tools/build.py 01 probe      # prod + a first step inside the Try scope that always fails: proves the alert path
                                        # in production without touching any data (office laptop; then Update with `prod`)
    python tools/build.py 01 fixedprobe # the same on the sandbox copy, to prove the probe mechanism itself
    python tools/build.py 12 baselinex|fixedx   # sandbox copy that keeps Excel REAL (workbooks in the sandbox OneDrive; only the
                                        # Office Scripts stay stubbed). Needs the fix module's sandboxify to support cfg["_realexcel"]

Sandbox builds are retargeted using tools/sandbox.json (copy from sandbox.example.json) and refuse to
build if any production site/list/file ID is left. Output goes to build/ (gitignored).
Workflow and safety rules: refdocs/guides/sandbox_runbook.md, DECISIONS.md D-08.
"""
import importlib
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from flowpkg import Package  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXES = {p.stem.split("_", 1)[0][1:]: p.stem for p in (ROOT / "tools" / "fixes").glob("f*.py")}


def main(num, target):
    if num not in FIXES:
        raise SystemExit(f"No fix module for flow {num}. Known: {sorted(FIXES)}")
    fix = importlib.import_module(f"fixes.{FIXES[num]}")
    if target == "harness":
        return build_harness(num, fix)
    pkg = Package(ROOT / fix.SOURCE_ZIP)

    real = target in ("baselinex", "fixedx")  # real-Excel sandbox variants
    base = target[:-1] if real else target
    cfg = None
    if base in ("baseline", "fixed", "fixedprobe") and hasattr(fix, "sandboxify"):
        cfg = {**load_cfg(), "_realexcel": real}
        fix.sandboxify(pkg, cfg)  # swap the parts a sandbox can't reproduce (e.g. an Excel read) BEFORE the fix is applied
    if base in ("fixed", "prod", "probe", "fixedprobe"):
        fix.apply(pkg)
    if base in ("probe", "fixedprobe"):
        add_probe(pkg)
    if base in ("baseline", "fixed", "fixedprobe"):
        cfg_path = pathlib.Path(os.environ.get("SANDBOX_CONFIG", ROOT / "tools" / "sandbox.json"))
        if not cfg_path.exists():
            raise SystemExit(f"{cfg_path} not found — copy tools/sandbox.example.json to tools/sandbox.json and fill it in")
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        # sandbox-only GUIDs (harness lists) are allowed through the production-ID guard as-is
        allowed = {v: v for v in cfg.get("harness", {}).values() if isinstance(v, str) and not v.startswith("/")}
        if real:  # real-Excel targets: the sandbox OneDrive ('me') and mock-template table names are deliberate, not production ids
            allowed.update({v: v for v in cfg.get("excel_allowed", [])})
        pkg.retarget({**cfg["replace"], **allowed})
        pkg.set_display_name(f"[SANDBOX-{target.upper()}] {fix.DISPLAY_NAME}")
        pkg.force_create_as_new()
    elif target not in ("prod", "probe"):
        raise SystemExit("target must be baseline | fixed | prod | probe | fixedprobe | baselinex | fixedx")

    out = ROOT / "build" / target / f"flow{num}-{target}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    pkg.save(out)
    print(f"built {out.relative_to(ROOT)}")


PROBE = "Probe_-_Force_a_failure_(DELETE_AFTER_TEST)"


def add_probe(pkg):
    """Insert a Compose that always fails (div by zero) as the first step of the Try scope and make every step that used to start
    the scope wait for it. The scope then fails before any real work, so the Catch/Terminate path can be proven without side
    effects. Only for the `probe`/`fixedprobe` targets; the clean `prod` package never contains it."""
    d = pkg.definition
    acts = d["properties"]["definition"]["actions"]
    tries = [k for k, v in acts.items() if v["type"] == "Scope" and k.startswith("Try_-_")]
    if len(tries) != 1:
        raise SystemExit(f"expected exactly one Try scope to probe, found {tries}: this flow has no failure handling to test")
    scope = acts[tries[0]]["actions"]
    roots = [k for k, v in scope.items() if not v.get("runAfter")]
    scope[PROBE] = {"type": "Compose", "runAfter": {}, "inputs": "@div(1, 0)"}
    for k in roots:
        scope[k]["runAfter"] = {PROBE: ["Succeeded"]}
    pkg.definition = d


def load_cfg():
    cfg_path = pathlib.Path(os.environ.get("SANDBOX_CONFIG", ROOT / "tools" / "sandbox.json"))
    if not cfg_path.exists():
        raise SystemExit(f"{cfg_path} not found — copy tools/sandbox.example.json to tools/sandbox.json and fill it in")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def build_harness(num, fix):
    """A small sandbox-only flow that exercises the parts of a flow a real sandbox copy can't (see the fix module)."""
    if not hasattr(fix, "harness"):
        raise SystemExit(f"fix module for flow {num} has no harness()")
    cfg = load_cfg()
    if "harness" not in cfg:
        raise SystemExit("sandbox.json has no 'harness' section (library GUID + root folder) — see sandbox_runbook.md")
    pkg = Package(ROOT / fix.HARNESS_SKELETON_ZIP)
    fix.harness(pkg, cfg)
    h = cfg["harness"]
    pkg.retarget({**cfg["replace"], h["library"]: h["library"]})
    pkg.set_display_name(f"[SANDBOX-HARNESS] flow {num} trigger swap")
    pkg.force_create_as_new()
    out = ROOT / "build" / "harness" / f"flow{num}-harness.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    pkg.save(out)
    print(f"built {out.relative_to(ROOT)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1].zfill(2), sys.argv[2])
