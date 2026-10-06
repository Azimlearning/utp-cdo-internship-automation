"""Flow #3 — Add HC Supervisor into MasterList.

Findings: refdocs/issues/2026-09-30-flow-03-add-hc-supervisor.md

Existing shape: Get_item -> RUNNING x2 -> List rows (Excel) -> Apply_to_each[Create_item] -> COMPLETED x2,
with a FAILED x2 branch that hangs off the last COMPLETED post (Failed/Skipped/TimedOut).

Problems fixed here:
  - The FAILED message names no step, error or run link.
  - The FAILED branch also fires when only the COMPLETED Teams post fails (work succeeded, message says FAILED).
  - Run status after a handled failure is not forced to Failed (observed/refuted in the sandbox, see issue doc).

Fix: wrap the work in a Try scope; COMPLETED runs on Try success; a Catch scope on Try failure finds the failed
step (top level and inside the loop), posts the two FAILED messages with step + error + run link, then Terminate(Failed).
The Excel file/script IDs (D-03 / issue 2) are NOT touched here.

Sandbox: sandboxify() swaps only the Excel read for a Compose of sample rows and the trigger for a list-item trigger,
so the Try/Catch + Teams + Create_item behaviour is exercised for real.
"""
import json

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Add HC Supervisor into MasterList.zip"
DISPLAY_NAME = "UTP/CSD/CDO Add HC Supervisor into MasterList"

SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
PROD_SUPERVISOR_LIST = "50892394-61b5-4551-86a9-20e17b33e57e"
TRY = "Try_-_Add_HC_Supervisors"
CATCH = "Catch_-_Alert_CDO_staff"
LIST_ROWS = "List_rows_present_in_a_table"
LOOP = "Apply_to_each"
FAIL_TN1 = "Post_message_in_a_chat_or_channel_4"
FAIL_TN2 = "Post_message_in_a_chat_or_channel_5"
DONE_TN1 = "Post_message_in_a_chat_or_channel_13"

F_LOOP = "Filter_array_-_Failed_in_loop"
F_TOP = "Filter_array_-_Failed_at_top_level"

STEP_EXPR = (
    f"coalesce(first(body('{F_LOOP}'))?['name'], first(body('{F_TOP}'))?['name'], 'unknown step')"
)
def _msg(filter_name):
    """Best error text for the first failed item of a Filter array, without ever navigating a wrong type.

    Sandbox lesson (2026-09-30): result() of a Foreach returns per-iteration items whose `outputs` is an ARRAY, so
    `…?['outputs']?['body']` throws 'Array elements can only be selected using an integer index' — and `?` does not
    guard against that. So `outputs.body.*` is only read when `outputs` is a JSON object.
    """
    x = f"first(body('{filter_name}'))"
    return (
        f"coalesce({x}?['error']?['message'], "
        f"if(startsWith(string({x}?['outputs']), '{{'), "
        f"coalesce({x}?['outputs']?['body']?['message'], {x}?['outputs']?['body']?['error']?['message']), null))"
    )


ERR_EXPR = f"coalesce({_msg(F_LOOP)}, {_msg(F_TOP)}, 'see the run')"
RUN_LINK = (
    "https://make.powerautomate.com/environments/@{workflow()?['tags']?['environmentName']}"
    "/flows/@{workflow()?['name']}/runs/@{workflow()?['run']?['name']}"
)
DETAIL_HTML = (
    "<br>\n<br>\nFailed step: @{" + STEP_EXPR + "}<br>\nError: @{" + ERR_EXPR + "}<br>\n"
    '<a href="' + RUN_LINK + '">Open this run</a>'
)


def _find_parent(actions, name):
    """Return the actions dict that directly contains `name` (searches nested scopes/loops/conditions)."""
    if name in actions:
        return actions
    for a in actions.values():
        for sub in (a.get("actions", {}), a.get("else", {}).get("actions", {})):
            r = _find_parent(sub, name)
            if r is not None:
                return r
    return None


def _filter(name, source, run_after):
    return {
        "type": "Query",
        "runAfter": run_after,
        "inputs": {"from": f"@result('{source}')", "where": "@equals(item()?['status'], 'Failed')"},
    }


def apply(pkg):
    d = pkg.definition
    defn = d["properties"]["definition"]
    acts = defn["actions"]
    assert TRY not in acts, "flow 3 already has the Try scope"

    list_rows, loop = acts.pop(LIST_ROWS), acts.pop(LOOP)
    list_rows["runAfter"] = {}
    acts[TRY] = {
        "type": "Scope",
        "runAfter": {"Post_message_in_a_chat_or_channel": ["Succeeded"]},
        "actions": {LIST_ROWS: list_rows, LOOP: loop},
    }
    acts[DONE_TN1]["runAfter"] = {TRY: ["Succeeded"]}

    fail1, fail2 = acts.pop(FAIL_TN1), acts.pop(FAIL_TN2)
    for f in (fail1, fail2):
        body = f["inputs"]["parameters"]["body/messageBody"]
        assert "FAILED" in body
        # append the detail block inside the last <p>
        f["inputs"]["parameters"]["body/messageBody"] = body.replace("</p>", DETAIL_HTML + "</p>", 1) if body.rstrip().endswith("</p>") else body + DETAIL_HTML
    fail1["runAfter"] = {F_TOP: ["Succeeded"]}
    fail2["runAfter"] = {FAIL_TN1: ["Succeeded", "Failed"]}
    acts[CATCH] = {
        "type": "Scope",
        "runAfter": {TRY: ["Failed", "TimedOut"]},
        "actions": {
            F_LOOP: _filter(F_LOOP, LOOP, {}),
            F_TOP: _filter(F_TOP, TRY, {F_LOOP: ["Succeeded"]}),
            FAIL_TN1: fail1,
            FAIL_TN2: fail2,
        },
    }
    acts["Terminate_-_Mark_run_as_failed"] = {
        "type": "Terminate",
        "runAfter": {CATCH: ["Succeeded", "Failed", "TimedOut"]},
        "inputs": {
            "runStatus": "Failed",
            "runError": {
                "code": "AddHCSupervisorFailed",
                "message": "Add HC Supervisor failed at: @{" + STEP_EXPR + "}",
            },
        },
    }
    # Terminate's expression references filters inside Catch; those are available there
    pkg.definition = d


F3_FOLDER = "/Documents/CDO-Sandbox/F3"   # SharePoint server-relative folder of the sandbox OneDrive (staging uploads)
F3_EXCEL = "/CDO-Sandbox/F3"               # the same folder as the Excel connector's OneDrive path
SUP_LIST = "CDO Sandbox - HC Supervisor"


def real_excel(pkg, cfg, folder, ok_file, bad_file):
    """Real-Excel sandbox variant (build.py 03|04 baselinex|fixedx): the table read is REAL (a generated workbook in the sandbox
    OneDrive, table `Rows`); only the trigger is swapped. Title picks the scenario: readfail = the workbook does not exist,
    rowfail = a workbook whose 2nd row is rejected by the SharePoint list."""
    from fixes import f12_hc_supervisor_masterlist_checking as f12
    from fixes import trycatch as tc
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = tc.list_item_trigger(cfg["replace"][SITE], cfg["harness"]["run_trigger_list"])
    t = "triggerBody()?['Title']"
    lr = _find_parent(defn["actions"], LIST_ROWS)[LIST_ROWS]
    f12._strip_file_hints(lr)
    lr["inputs"]["parameters"].update({
        "source": "me", "drive": "me", "table": "Rows",
        "file": f"@if(equals({t}, 'readfail'), '{folder}/does-not-exist.xlsx', "
                f"if(equals({t}, 'rowfail'), '{folder}/{bad_file}', '{folder}/{ok_file}'))"})
    # the sandbox list's built-in Title column is required by the connector's cached schema (same as the stubbed variant)
    _find_parent(defn["actions"], "Create_item")["Create_item"]["inputs"]["parameters"]["item/Title"] = "sandbox"
    pkg.definition = d


# tools/sandbox/pw.py stage 03 ok|rowfail (once, BEFORE importing), then run 03 <name> baselinex|fixedx. The flow only READS the
# workbooks, so runs do not clear or re-upload anything (stageOnly): no Excel Online locks to wait for.
def _scenarios(lst, ok_file, bad_file, folder):
    base = {"clear": [lst], "count": ["Create_item"], "countLists": [lst], "stageOnly": True}
    return {
        "ok": {**base, "trigger": "ok", "upload": [{"folder": folder, "file": ok_file}],
               "expect": {x: {"status": "Succeeded", "counts": {"Create_item": {"Succeeded": 2}}, "after": {lst: 2}}
                          for x in ("baselinex", "fixedx")}},
        "readfail": {**base, "trigger": "readfail", "upload": [],
                     "expect": {"baselinex": {"status": "Succeeded", "failedAction": LIST_ROWS, "after": {lst: 0}},
                                "fixedx": {"status": "Failed", "failedAction": LIST_ROWS, "after": {lst: 0}}}},
        "rowfail": {**base, "trigger": "rowfail", "upload": [{"folder": folder, "file": bad_file}],
                    "expect": {"baselinex": {"status": "Succeeded", "failedAction": "Create_item",
                                             "counts": {"Create_item": {"Succeeded": 1, "Failed": 1}}, "after": {lst: 1}},
                               "fixedx": {"status": "Failed", "failedAction": "Create_item",
                                          "counts": {"Create_item": {"Succeeded": 1, "Failed": 1}}, "after": {lst: 1}}}},
    }


SCENARIOS = _scenarios(SUP_LIST, "Rows_for_Flow3_SVExactlyNotMatched.xlsx", "Rows_for_Flow3_rowfail.xlsx", F3_FOLDER)


def sandboxify(pkg, cfg):
    """Sandbox-only conversion: list-item trigger, Compose instead of the Excel read, sandbox supervisor list."""
    if cfg.get("_realexcel"):
        return real_excel(pkg, cfg, F3_EXCEL, "Rows_for_Flow3_SVExactlyNotMatched.xlsx", "Rows_for_Flow3_rowfail.xlsx")
    h = cfg["harness"]
    site = cfg["replace"][SITE]
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = {
        "When_an_item_is_created": {
            "recurrence": {"frequency": "Minute", "interval": 1},
            "splitOn": "@triggerOutputs()?['body/value']",
            "type": "OpenApiConnection",
            "inputs": {
                "host": {
                    "apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                    "connectionName": "shared_sharepointonline",
                    "operationId": "GetOnNewItems",
                },
                "parameters": {"dataset": site, "table": h["run_trigger_list"]},
                "authentication": "@parameters('$authentication')",
            },
        }
    }
    good = [
        {"HC Supervisor Name": f"Test Supervisor {n}", "Host SV Salutation": "Mr",
         "Host SV Designation/Position": "Manager", "Host SV Department/Unit/Section": "HR"}
        for n in ("One", "Two")
    ]
    bad = [dict(good[0]), dict(good[1], **{"HC Supervisor Name": "X" * 300})]  # 2nd row breaks the 255-char limit
    q = lambda rows: json.dumps({"body/value": rows}).replace("'", "''")
    sample = (
        "@if(equals(triggerBody()?['Title'], 'readfail'), div(1, 0), "
        f"json(if(equals(triggerBody()?['Title'], 'rowfail'), '{q(bad)}', '{q(good)}')))"
    )
    parent = _find_parent(defn["actions"], LIST_ROWS)
    old = parent[LIST_ROWS]
    parent[LIST_ROWS] = {"type": "Compose", "runAfter": old["runAfter"], "inputs": sample}
    # The sandbox list's built-in Title column is required by the connector's cached schema (production's isn't),
    # so the sandbox copy sets it. Same in baseline and fixed; irrelevant to the error handling under test.
    parent_loop = _find_parent(defn["actions"], "Create_item")
    parent_loop["Create_item"]["inputs"]["parameters"]["item/Title"] = "sandbox"
    pkg.definition = d
    pkg.remove_connector("shared_excelonlinebusiness")
