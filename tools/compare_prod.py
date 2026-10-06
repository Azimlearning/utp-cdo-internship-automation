"""Check that a flow exported from the real system matches the package that was tested.

    python tools/compare_prod.py NN [exported.zip] [--against prod|probe]

Default `exported.zip` is the repo's own copy, flows/<name>.zip, i.e. what `git` holds after you re-export a flow post-apply
(CLAUDE.md rule 5/"Running it"). It is compared with build/<against>/flowNN-<against>.zip (default prod).

Compares the action tree: names, types, run-after wiring, expressions and inputs, trigger shape and the other settings that
change behaviour (concurrency, pagination). Ignores what a re-export legitimately changes: operation/metadata ids, connection
reference names, authentication blocks, descriptions. Exit 0 = identical, 1 = differences (listed).

Self-checks worth knowing: the ORIGINAL export vs prod shows the whole fix as differences; probe vs prod shows only the probe.
"""
import importlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from flowpkg import Package  # noqa: E402

FIXES = {p.stem.split("_", 1)[0][1:]: p.stem for p in (ROOT / "tools" / "fixes").glob("f[0-9][0-9]_*.py")}
DROP = {"operationMetadataId", "metadata", "authentication", "description", "x-ms-apimTemplateParameterReference"}


def clean(v):
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            if k in DROP:
                continue
            if k == "host" and isinstance(x, dict):  # keep what the action calls, not which connection reference carries it
                out[k] = {"operationId": x.get("operationId")}
                continue
            if k in ("actions", "else"):
                continue
            out[k] = clean(x)
        return out
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, str):
        return " ".join(v.split())  # whitespace-only differences are not differences
    return v


def flatten(actions, prefix=""):
    out = {}
    for name, a in actions.items():
        path = prefix + name
        out[path] = clean(a)
        out.update(flatten(a.get("actions", {}), path + "/"))
        if "else" in a:
            out.update(flatten(a["else"].get("actions", {}), path + "/else/"))
    return out


def load(path):
    d = Package(path).definition["properties"]["definition"]
    return {"trigger": clean(d.get("triggers", {})), **{"A:" + k: v for k, v in flatten(d.get("actions", {})).items()}}


def diff(live, tested):
    out = []
    for k in sorted(set(live) | set(tested)):
        if k not in live:
            out.append(f"MISSING in the exported flow: {k}")
        elif k not in tested:
            out.append(f"EXTRA in the exported flow (not in the tested package): {k}")
        elif live[k] != tested[k]:
            a, b = live[k], tested[k]
            keys = sorted(x for x in set(a) | set(b) if a.get(x) != b.get(x)) if isinstance(a, dict) and isinstance(b, dict) else ["(value)"]
            out.append(f"DIFFERENT {k}: " + ", ".join(keys))
    return out


def main(args):
    sys.stdout.reconfigure(encoding="utf-8")
    against = "prod"
    if "--against" in args:
        i = args.index("--against")
        against = args[i + 1]
        del args[i:i + 2]
    if not args:
        raise SystemExit(__doc__)
    num = args[0].zfill(2)
    if num not in FIXES:
        raise SystemExit(f"no fix module for flow {num}")
    fix = importlib.import_module(f"fixes.{FIXES[num]}")
    exported = pathlib.Path(args[1]) if len(args) > 1 else ROOT / fix.SOURCE_ZIP
    tested = ROOT / "build" / against / f"flow{num}-{against}.zip"
    for p in (exported, tested):
        if not p.exists():
            raise SystemExit(f"missing {p} (build it with: python tools/build.py {num} {against})")
    d = diff(load(exported), load(tested))
    print(f"flow {num}: {exported.name}  vs  build/{against}/{tested.name}")
    for line in d:
        print("  " + line)
    print("IDENTICAL: what is live matches what was tested" if not d else f"{len(d)} difference(s)")
    return 0 if not d else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
