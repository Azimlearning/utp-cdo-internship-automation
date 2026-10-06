"""Generic Try/Catch + Terminate wrapper, generalised from flows 3/4/14 (proven in the sandbox on those flows).

Shape of the flows it targets: [work actions ...] -> COMPLETED posts (run after the work succeeds) and a FAILED post chain
hanging off the last COMPLETED post (Failed/Skipped/TimedOut).

wrap():
  * moves `inner` (top-level action names) into a Scope `try_name`; the scope inherits the inner actions' outside dependencies
  * top-level actions that used to run after an inner action now run after the Try scope (same statuses)
  * moves the FAILED posts into a Catch scope (run after Try Failed/TimedOut), with filters that find the failed step, and appends
    'Failed step / Error / Open this run' to their message
  * adds Terminate(Failed) so run history stops reporting a handled failure as Succeeded

Error extraction is type-safe (sandbox lesson, flow 3): inside a Foreach, result() items have `outputs` as an ARRAY, so
`outputs.body` may only be read when `outputs` is a JSON object.
"""
import json

DETAIL_TAIL = "<br>\nFailed step: @{STEP}<br>\nError: @{ERR}<br>\n<a href=\"" \
    "https://make.powerautomate.com/environments/@{workflow()?['tags']?['environmentName']}" \
    "/flows/@{workflow()?['name']}/runs/@{workflow()?['run']?['name']}\">Open this run</a>"


def _msg(f):
    x = f"first(body('{f}'))"
    return (f"coalesce({x}?['error']?['message'], if(startsWith(string({x}?['outputs']), '{{'), "
            f"coalesce({x}?['outputs']?['body']?['message'], {x}?['outputs']?['body']?['error']?['message']), null))")


def _has_loop(action):
    kids = list(action.get("actions", {}).values()) + list(action.get("else", {}).get("actions", {}).values())
    return any(k["type"] in ("Foreach", "Until") or _has_loop(k) for k in kids)


def _filter(source, after):
    return {"type": "Query", "runAfter": after,
            "inputs": {"from": f"@result('{source}')", "where": "@equals(item()?['status'], 'Failed')"}}


def wrap(defn, *, inner, try_name, fail_posts, loops, code, label):
    acts = defn["actions"]
    inner = [n for n in inner if n in acts]
    inset = set(inner)
    assert try_name not in acts and inner, "nothing to wrap or already wrapped"

    # outside dependencies of the inner actions become the Try scope's own runAfter
    try_after = {}
    for n in inner:
        for dep, st in acts[n].get("runAfter", {}).items():
            if dep not in inset:
                try_after[dep] = st
    moved = {}
    for n in inner:
        a = acts.pop(n)
        a["runAfter"] = {d: s for d, s in a.get("runAfter", {}).items() if d in inset}
        moved[n] = a
    failed = [acts.pop(n) for n in fail_posts]

    # any remaining top-level action that ran after an inner action now runs after the Try scope
    for a in acts.values():
        ra = a.get("runAfter", {})
        hit = [d for d in ra if d in inset]
        for d in hit:
            st = ra.pop(d)
            ra[try_name] = st
    acts[try_name] = {"type": "Scope", "runAfter": try_after, "actions": moved}

    loops = [l for l in loops if l in inset]
    filters = {}
    prev = {}
    # a Condition/Scope directly inside a loop hides the real failing step (flow 10 reported "Condition", not the email);
    # check those first so the deepest failure wins the coalesce below. Only for ones with no loop inside them: Power
    # Automate rejects result() on a scope that holds further loops (flow 7 import, InvalidTemplate, 2026-10-02).
    for i, l in enumerate(loops):
        inner_scopes = [(n, a) for n, a in moved[l].get("actions", {}).items() if a["type"] in ("If", "Scope") and not _has_loop(a)]
        for j, (cn, c) in enumerate(inner_scopes):
            fn = f"Filter_array_-_Failed_in_loop_{i+1}_{j+1}"
            filters[fn] = _filter(cn, prev)
            prev = {fn: ["Succeeded"]}
    for i, l in enumerate(loops):
        fn = f"Filter_array_-_Failed_in_loop_{i+1}"
        filters[fn] = _filter(l, prev)
        prev = {fn: ["Succeeded"]}
    ftop = "Filter_array_-_Failed_at_top_level"
    filters[ftop] = _filter(try_name, prev)
    names = list(filters)
    step = "coalesce(" + ", ".join(f"first(body('{n}'))?['name']" for n in names) + ", 'unknown step')"
    err = "coalesce(" + ", ".join(_msg(n) for n in names) + ", 'see the run')"
    tail = DETAIL_TAIL.replace("@{STEP}", "@{" + step + "}").replace("@{ERR}", "@{" + err + "}")

    catch_actions = dict(filters)
    prev_name = ftop
    for i, f in enumerate(failed):
        body = f["inputs"]["parameters"]["body/messageBody"]
        assert "FAILED" in body, "FAILED post expected"
        f["inputs"]["parameters"]["body/messageBody"] = body.replace("</p>", tail + "</p>", 1) if "</p>" in body else body + tail
        nm = f"Post_message_FAILED_{i+1}"
        f["runAfter"] = {prev_name: ["Succeeded"]} if i == 0 else {prev_name: ["Succeeded", "Failed"]}
        catch_actions[nm] = f
        prev_name = nm
    acts["Catch_-_Alert_CDO_staff"] = {"type": "Scope", "runAfter": {try_name: ["Failed", "TimedOut"]}, "actions": catch_actions}
    acts["Terminate_-_Mark_run_as_failed"] = {
        "type": "Terminate", "runAfter": {"Catch_-_Alert_CDO_staff": ["Succeeded", "Failed", "TimedOut"]},
        "inputs": {"runStatus": "Failed", "runError": {"code": code, "message": f"{label} failed at: @{{{step}}}"}}}


def list_item_trigger(site, list_id):
    return {"When_an_item_is_created": {
        "recurrence": {"frequency": "Minute", "interval": 1}, "splitOn": "@triggerOutputs()?['body/value']",
        "type": "OpenApiConnection",
        "inputs": {"host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                            "connectionName": "shared_sharepointonline", "operationId": "GetOnNewItems"},
                   "parameters": {"dataset": site, "table": list_id}, "authentication": "@parameters('$authentication')"}}}
