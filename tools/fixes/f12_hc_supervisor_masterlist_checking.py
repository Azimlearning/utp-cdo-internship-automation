"""Flow #12: HC Supervisor Info MasterList Checking.

PowerApp button -> RUNNING x2 -> two Office Script runs clear the template's result tables -> lists every file in the
MasterList_RawData_ToBeProcess folder -> for each file reads its `Database` table and compares every row with the HC Supervisor
SharePoint list (exact / partial / new) writing rows into the HC Supervisor MasterList template (Excel 'Add a row') -> 30 s
delay -> for each file emails the PIC the template -> COMPLETED x2; FAILED x2 off the COMPLETED posts.

Fix: Try/Catch + Terminate (fixes/trycatch.py) around everything from the first script run to the last email.
Variable initialisations stay top-level. Matching logic is NOT changed.

Sandbox: list-item trigger. Everything Excel is stubbed (the two scripts, the file's `Database` rows, the five 'Add a row'
actions, the template read); the folder listing is stubbed too so scenarios can choose 1 or 2 files. The SharePoint HC Supervisor
list, all the matching Conditions and the loops run for real. The PIC email goes to the tester only.
  trigger Title: ok | twofiles (2 files in the folder) | scriptfail (first script step fails) | addfail (the 'new supervisor'
  row write fails, deep inside the nested loops) | readfail (the SharePoint read fails before any loop runs)
Each stubbed 'Add a row' is a Compose, so how many rows would go to which table is read from the run (counts), no workbook needed.
"""
import json
import re

from fixes import trycatch as tc

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO HC Supervisor Info MasterList Checking.zip"
DISPLAY_NAME = "UTP/CSD/CDO HC Supervisor Info MasterList Checking"
SITE = "https://utpmy.sharepoint.com/sites/CareerDevelopmentOfficeCDO"
TRY = "Try_-_Check_HC_supervisors"
ME = "fakhrul_22012087@utp.edu.my"
FILES = "Get_files_(properties_only)"
ROWS = "List_rows_present_in_a_table"
ADDS = ["Add_a_row_into_a_table", "Add_a_row_into_a_table_2", "Add_a_row_into_a_table_3", "Add_a_row_into_a_table_4",
        "Add_a_row_into_a_table_5"]
INNER = ["Run_script", "Run_script_2", FILES, "Get_items", "Apply_to_each", "Delay", "Apply_to_each_4"]

HC = "CDO Sandbox - HC Supervisor"
_SV = [{"HCSupervisorName": "ZZ TEST Exact SV", "HostSVSalutation": "Mr", "HCSVDesignation_x002f_Position": "Manager",
        "HCSVDepartment_x002f_Unit_x002f_": "HR"},
       {"HCSupervisorName": "ZZ TEST Partial SV", "HostSVSalutation": "Ms", "HCSVDesignation_x002f_Position": "Manager",
        "HCSVDepartment_x002f_Unit_x002f_": "Finance"}]
# the stubbed Excel rows (see _ROWS below): Exact Match (identical), Brand New (not in the list), Partial Match (other position)
# tools/sandbox/pw.py run 12 <name> baseline|fixed|baselinex|fixedx   (x = real Excel; the others stub it)
SCENARIOS = {
    "ok": {"clear": [HC], "seed": {HC: _SV}, "trigger": "ok", "count": ADDS + ["Send_an_email_(V2)"],
           "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Succeeded"}}},
    "twofiles": {"clear": [HC], "seed": {HC: _SV}, "trigger": "twofiles", "count": ADDS + ["Send_an_email_(V2)"],
                 "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Succeeded"}}},
    "scriptfail": {"clear": [HC], "seed": {HC: _SV}, "trigger": "scriptfail", "count": ADDS + ["Send_an_email_(V2)"],
                   "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Failed", "failedAction": "Run_script"}}},
    "addfail": {"clear": [HC], "seed": {HC: _SV}, "trigger": "addfail", "count": ADDS + ["Send_an_email_(V2)"],
                "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Failed"}}},
    "readfail": {"clear": [HC], "seed": {HC: _SV}, "trigger": "readfail", "count": ADDS,
                 "expect": {"fixed": {"status": "Failed", "failedAction": "Get_items"}}},
}

_ROWS = [{"HC SV Name": "ZZ TEST Exact SV", "Host SV Salutation": "Mr", "HC SV Designation/Position": "Manager",
          "HC SV Department/Unit/Section": "HR", "Student ID": "S1", "Student Name": "Stub A", "Email Address": "a@sandbox.test"},
         {"HC SV Name": "ZZ TEST New SV", "Host SV Salutation": "Mr", "HC SV Designation/Position": "Director",
          "HC SV Department/Unit/Section": "Ops", "Student ID": "S2", "Student Name": "Stub B", "Email Address": "b@sandbox.test"},
         {"HC SV Name": "ZZ TEST Partial SV", "Host SV Salutation": "Ms", "HC SV Designation/Position": "Director",
          "HC SV Department/Unit/Section": "Finance", "Student ID": "S3", "Student Name": "Stub C", "Email Address": "c@sandbox.test"}]


def apply(pkg):
    d = pkg.definition
    tc.wrap(d["properties"]["definition"], inner=INNER, try_name=TRY,
            fail_posts=["Post_message_in_a_chat_or_channel_4", "Post_message_in_a_chat_or_channel_5"],
            loops=["Apply_to_each", "Apply_to_each_4"], code="HCSupervisorCheckFailed", label="HC Supervisor MasterList Checking")
    pkg.definition = d


def sandboxify(pkg, cfg):
    if cfg.get("_realexcel"):
        return _real_excel(pkg, cfg, TABLES, "/CDO-Sandbox/F7/Template/HC Supervisor MasterList Template.xlsx")
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = tc.list_item_trigger(cfg["replace"][SITE], cfg["harness"]["run_trigger_list"])
    a = defn["actions"]
    title = "triggerBody()?['Title']"
    a["Run_script"] = {"type": "Compose", "runAfter": a["Run_script"]["runAfter"],
                       "inputs": f"@if(equals({title}, 'scriptfail'), div(1, 0), 'script stub ok')"}
    a["Run_script_2"] = {"type": "Compose", "runAfter": a["Run_script_2"]["runAfter"], "inputs": "script stub ok"}
    two = json.dumps([{"FullPath": "a.xlsx"}, {"FullPath": "b.xlsx"}])
    one = json.dumps([{"FullPath": "a.xlsx"}])
    a[FILES] = {"type": "Compose", "runAfter": a[FILES]["runAfter"],
                "inputs": f"@if(equals({title}, 'twofiles'), json('{two}'), json('{one}'))"}
    a["Get_items"]["inputs"]["parameters"]["$filter"] = f"@if(equals({title}, 'readfail'), 'NoSuchColumn eq 1', 'ID gt 0')"
    a["Apply_to_each"]["foreach"] = f"@outputs('{FILES}')"
    a["Apply_to_each_4"]["foreach"] = f"@outputs('{FILES}')"
    loop = a["Apply_to_each"]["actions"]
    loop[ROWS] = {"type": "Compose", "runAfter": {}, "inputs": "@json('" + json.dumps(_ROWS) + "')"}
    loop["Apply_to_each_2"]["foreach"] = f"@outputs('{ROWS}')"
    _stub_adds(loop, title)
    inner = a["Apply_to_each_4"]["actions"]
    inner["Get_file_content_using_path"] = {"type": "Compose", "runAfter": {}, "inputs": "stub template workbook"}
    p = inner["Send_an_email_(V2)"]["inputs"]["parameters"]
    p["emailMessage/To"] = ME
    p["emailMessage/Cc"] = ME
    p.pop("emailMessage/Attachments", None)
    a["Delay"]["inputs"]["interval"] = {"count": 1, "unit": "Second"}
    pkg.definition = d
    pkg.remove_connector("shared_excelonlinebusiness")


def _stub_adds(node, title):
    """Replace every Excel 'Add a row' (any depth) by a Compose that records which table it targeted."""
    for k, v in list(node.items()):
        if k in ADDS:
            fail = f"@if(equals({title}, 'addfail'), div(1, 0), 'row stub: {k}')" if k == "Add_a_row_into_a_table_4" else f"row stub: {k}"
            node[k] = {"type": "Compose", "runAfter": v.get("runAfter", {}), "inputs": fail}
        for key in ("actions",):
            if key in v:
                _stub_adds(v[key], title)
        if "else" in v:
            _stub_adds(v["else"].get("actions", {}), title)


# ---- real-Excel sandbox variant (build.py NN baselinex|fixedx) ---------------------------------------------------------
# Excel reads/writes go to real workbooks in the sandbox OneDrive (the generated testdata files); only the Office Scripts
# (their ids belong to the flow owner's account) and the template read for the email attachment stay stubbed.
TABLES = {"05D719C3": "HCSupervisor", "CB10AEA9": "SVExactlyNotMatched"}  # production table id -> mock template table name
ONEDRIVE_PATH = ("concat('/', join(skip(split(items('Apply_to_each')?['{FullPath}'], '/'), 1), '/'))")  # 'Documents/x/y' -> '/x/y'
F7IN = "/Documents/CDO-Sandbox/F7/MasterList_RawData_ToBeProcess"
XL = "/Documents/CDO-Sandbox/Excel"


def _real_excel(pkg, cfg, tables, template):
    d = pkg.definition
    defn = d["properties"]["definition"]
    defn["triggers"] = tc.list_item_trigger(cfg["replace"][SITE], cfg["harness"]["run_trigger_list"])
    a = defn["actions"]
    title = "triggerBody()?['Title']"
    a["Run_script"] = {"type": "Compose", "runAfter": a["Run_script"]["runAfter"],
                       "inputs": f"@if(equals({title}, 'scriptfail'), div(1, 0), 'script stub ok')"}
    a["Run_script_2"] = {"type": "Compose", "runAfter": a["Run_script_2"]["runAfter"], "inputs": "script stub ok"}
    a["Get_items"]["inputs"]["parameters"]["$filter"] = f"@if(equals({title}, 'readfail'), 'NoSuchColumn eq 1', 'ID gt 0')"
    loop = a["Apply_to_each"]["actions"]
    _strip_file_hints(loop[ROWS])
    lr = loop[ROWS]["inputs"]["parameters"]
    lr.update({"source": "me", "drive": "me", "table": "Database",
               "file": f"@if(equals({title}, 'excelfail'), '/CDO-Sandbox/F7/does-not-exist.xlsx', {ONEDRIVE_PATH})"})
    _real_adds(loop, title, tables, template)
    inner = a["Apply_to_each_4"]["actions"]
    # the template read and the email attachment stay REAL: the sandbox library holds the (mock) template under the production
    # file name, so the PIC email carries the very workbook the Excel steps just wrote into
    p = inner["Send_an_email_(V2)"]["inputs"]["parameters"]
    p["emailMessage/To"] = ME
    p["emailMessage/Cc"] = ME
    a["Delay"]["inputs"]["interval"] = {"count": 1, "unit": "Second"}
    pkg.definition = d


def _strip_file_hints(action):
    """Designer metadata maps production drive-item ids to paths; drop those hints from sandbox packages."""
    md = action.get("metadata")
    if isinstance(md, dict):
        action["metadata"] = {k: x for k, x in md.items() if not k.startswith("01")}


def _real_adds(node, title, tables, template):
    for k, v in list(node.items()):
        if k in ADDS:
            _strip_file_hints(v)
            p = v["inputs"]["parameters"]
            tid = re.search(r"\{([0-9A-F]{8})", p["table"]).group(1)
            table = tables[tid]
            p["table"] = table  # must stay static: Power Automate fetches the column schema from file + table when the flow is saved
            p.update({"source": "me", "drive": "me", "file": template})
            if k == "Add_a_row_into_a_table_4":  # 'addfail': fail just before the real 'new entry' write (deep inside the nested loops)
                gate = "Gate_-_addfail_scenario"
                node[gate] = {"type": "Compose", "runAfter": v.get("runAfter", {}),
                              "inputs": f"@if(equals({title}, 'addfail'), div(1, 0), 'go')"}
                v["runAfter"] = {gate: ["Succeeded"]}
        if "actions" in v:
            _real_adds(v["actions"], title, tables, template)
        if "else" in v:
            _real_adds(v["else"].get("actions", {}), title, tables, template)


F7TPL = "/Documents/CDO-Sandbox/F7/Template"  # where the flow reads its template (the prod folder, mapped into the sandbox)
PROD_TEMPLATE = {"Template_HCSupervisor_MOCK.xlsx": "HC Supervisor MasterList Template.xlsx",
                 "Template_HostCompany_MOCK.xlsx": "Host Company MasterList Template.xlsx"}


def _real_extras(file, template, tables_expected, two=False):
    name = PROD_TEMPLATE[template]
    up = [{"folder": F7IN, "file": file}, {"folder": F7TPL, "file": template, "name": name}]
    if two:
        up.insert(1, {"folder": F7IN, "file": file, "name": file.replace(".xlsx", "_2.xlsx")})
    return {"clearFolders": [F7IN], "upload": up, "readback": [{"folder": F7TPL, "name": name}], "workbook": tables_expected}


_T = "Template_HCSupervisor_MOCK.xlsx"
_F = "RawData_HCSupervisor_TEST.xlsx"
# what the template must hold after one file / two files: rows per table, by Status (identical row, other position, new, case variant)
_ONE = {"HCSupervisor": {"Matched": 2, "Partially Not Matched": 1}, "SVExactlyNotMatched": {"Exactly Not Matched": 1}}
_TWO = {"HCSupervisor": {"Matched": 4, "Partially Not Matched": 2}, "SVExactlyNotMatched": {"Exactly Not Matched": 2}}
for _n, _sc in SCENARIOS.items():
    _sc.update(_real_extras(_F, _T, _TWO if _n == "twofiles" else (_ONE if _n == "ok" else {}), two=(_n == "twofiles")))
    _e = _sc.get("expect", {})
    for _k, _v in (("baselinex", "baseline"), ("fixedx", "fixed")):
        if _v in _e:
            _e[_k] = _e[_v]
SCENARIOS["excelfail"] = {  # the Excel READ fails for real (file does not exist); fixed must alert, baseline hides it
    "clear": [HC], "seed": {HC: _SV}, "trigger": "excelfail", "count": ADDS + ["Send_an_email_(V2)"],
    **_real_extras(_F, _T, {}),
    "expect": {"baselinex": {"status": "Succeeded"}, "fixedx": {"status": "Failed", "failedAction": ROWS}}}
