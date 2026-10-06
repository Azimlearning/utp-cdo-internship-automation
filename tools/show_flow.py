"""Print a flow's structure straight from its export, with no extraction step.

    python tools/show_flow.py 12            # flow number from guides/flow_inventory.md
    python tools/show_flow.py "Combine"     # or any part of the zip name
    python tools/show_flow.py 12 --width 900 --no-teams
    python tools/show_flow.py --build fixed 10   # inspect build/<fixed|baseline|prod|probe>/flowNN-<target>.zip instead

Replaces unzipping flows/*.zip into a scratch folder (which left a second copy of every flow lying around). Shows the trigger,
connections, and every action with its run-after, key parameters, conditions and loops, nested as in the definition.
"""
import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from flowpkg import Package  # noqa: E402

NAMES = {1: "Success Submit Email", 2: "Acknowledgement Letter", 3: "Add HC Supervisor", 4: "Add Host Company", 5: "Bulk Email",
         6: "Clear Raw Database", 7: "Combine raw data", 8: "Delete Student List", 9: "Email To Inform Student",
         10: "Report Duty Reminder", 11: "Student Report Duty Status", 12: "HC Supervisor Info", 13: "Host Company Info",
         14: "Store Student List"}


def find_zip(key):
    needle = NAMES.get(int(key)) if key.isdigit() else key
    hits = [p for p in sorted((ROOT / "flows").glob("*.zip")) if needle.lower() in p.name.lower()]
    if len(hits) != 1:
        raise SystemExit(f"'{key}' matches {len(hits)} files in flows/: {[h.name for h in hits]}")
    return hits[0]


def text(html):
    return re.sub(r"<[^>]+>", "", html or "").replace("\n", " ")


def show(actions, width, teams, depth=0):
    pad = "  " * depth
    for name, a in actions.items():
        inp = a.get("inputs") if isinstance(a.get("inputs"), dict) else {}
        params = inp.get("parameters", {}) if inp else {}
        op = (inp.get("host") or {}).get("operationId") if inp else None
        if op == "PostMessageToConversation" and not teams:
            print(f"{pad}{name} | Teams post")
            continue
        extra = ""
        if a.get("runtimeConfiguration"):
            extra = " " + json.dumps(a["runtimeConfiguration"])
        print(f"{pad}{name} | {a['type']} | after: {a.get('runAfter')}{extra}")
        if a["type"] in ("OpenApiConnection", "ApiConnection") and op:
            body = {k: (text(v) if isinstance(v, str) else v) for k, v in params.items()}
            print(f"{pad}    {op} {json.dumps(body)[:width]}")
        elif a["type"] == "If":
            print(f"{pad}    if {json.dumps(a['expression'])[:width]}")
        elif a["type"] == "Foreach":
            print(f"{pad}    foreach {a['foreach'][:width]}")
        elif a["type"] in ("Compose", "SetVariable", "InitializeVariable", "Query", "Select", "AppendToArrayVariable",
                           "IncrementVariable", "Wait", "Terminate"):
            print(f"{pad}    {json.dumps(inp)[:width]}")
        show(a.get("actions", {}), width, teams, depth + 1)
        if "else" in a:
            print(f"{pad}  ELSE")
            show(a["else"].get("actions", {}), width, teams, depth + 1)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("flow")
    ap.add_argument("--width", type=int, default=450)
    ap.add_argument("--no-teams", action="store_true", help="collapse the Teams posts")
    ap.add_argument("--build", metavar="TARGET", help="baseline | fixed | prod | probe | fixedprobe")
    a = ap.parse_args()
    if a.build:
        num = a.flow.zfill(2)
        path = ROOT / "build" / a.build / f"flow{num}-{a.build}.zip"
    else:
        path = find_zip(a.flow)
    p = Package(path).definition["properties"]
    d = p["definition"]
    print(f"{path.name}\nname: {p['displayName']}\ntrigger: {json.dumps(d['triggers'])[:a.width]}\nconnections: {list(p['connectionReferences'])}\n")
    show(d["actions"], a.width, not a.no_teams)


if __name__ == "__main__":
    main()
