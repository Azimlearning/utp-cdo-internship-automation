"""Flow #4: Add Host Company into MasterList.

Structurally identical to flow 3 (manual PowerApp trigger -> Get item -> RUNNING x2 -> Excel table read -> Apply_to_each
Create_item -> COMPLETED x2, with a FAILED x2 branch hanging off the last COMPLETED post; same action names). So the
proven flow 3 Try/Catch + Terminate fix is reused unchanged; only the wording of the Terminate code, the display name
and the sandbox conversion (different list + columns) differ.

Findings/tests: refdocs/issues/2026-09-30-flow-04-add-host-company.md
"""
import json

from fixes import f03_add_hc_supervisor as f03

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Add Host Company into MasterList.zip"
DISPLAY_NAME = "UTP/CSD/CDO Add Host Company into MasterList"
PROD_LIST = "06c02770-f668-4f5c-8b4f-44ab220ae9b9"


def apply(pkg):
    old, f03.TRY = f03.TRY, "Try_-_Add_host_companies"  # f03.apply reads TRY at call time
    try:
        f03.apply(pkg)
    finally:
        f03.TRY = old
    d = pkg.definition
    t = d["properties"]["definition"]["actions"]["Terminate_-_Mark_run_as_failed"]["inputs"]["runError"]
    t["code"] = "AddHostCompanyFailed"
    t["message"] = t["message"].replace("Add HC Supervisor", "Add Host Company")
    pkg.definition = d


F4_FOLDER = "/Documents/CDO-Sandbox/F4"
F4_EXCEL = "/CDO-Sandbox/F4"
HC_LIST = "CDO Sandbox - Host Company"
SCENARIOS = f03._scenarios(HC_LIST, "Rows_for_Flow4_ExactlyNotMatched.xlsx", "Rows_for_Flow4_rowfail.xlsx", F4_FOLDER)


def sandboxify(pkg, cfg):
    if cfg.get("_realexcel"):  # real Excel read of a generated workbook (see f03.real_excel); the table is `Rows`
        return f03.real_excel(pkg, cfg, F4_EXCEL, "Rows_for_Flow4_ExactlyNotMatched.xlsx", "Rows_for_Flow4_rowfail.xlsx")
    site = cfg["replace"][f03.SITE]
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = {"When_an_item_is_created": {
        "recurrence": {"frequency": "Minute", "interval": 1}, "splitOn": "@triggerOutputs()?['body/value']",
        "type": "OpenApiConnection",
        "inputs": {"host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                            "connectionName": "shared_sharepointonline", "operationId": "GetOnNewItems"},
                   "parameters": {"dataset": site, "table": cfg["harness"]["run_trigger_list"]},
                   "authentication": "@parameters('$authentication')"}}}

    def row(n, name=None):
        return {"Host Company ( HC ) Name": name or f"Test Company {n}", "Type of Host": "Private", "Type of placement": "Onsite",
                "Organisation Type": "SME", "Industry Type": "IT", "HC Street Name": "1 Test St",
                "HC City / Town": "Ipoh", "Postcode": "31750", "HC State / Country": "Perak"}
    good = [row(1), row(2)]
    bad = [row(1), row(2, "X" * 300)]
    q = lambda rows: json.dumps({"body/value": rows}).replace("'", "''")
    sample = ("@if(equals(triggerBody()?['Title'], 'readfail'), div(1, 0), "
              f"json(if(equals(triggerBody()?['Title'], 'rowfail'), '{q(bad)}', '{q(good)}')))")
    parent = f03._find_parent(defn["actions"], f03.LIST_ROWS)
    parent[f03.LIST_ROWS] = {"type": "Compose", "runAfter": parent[f03.LIST_ROWS]["runAfter"], "inputs": sample}
    f03._find_parent(defn["actions"], "Create_item")["Create_item"]["inputs"]["parameters"]["item/Title"] = "sandbox"
    pkg.definition = d
    pkg.remove_connector("shared_excelonlinebusiness")
