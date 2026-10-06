"""Flow #13: Host Company Info MasterList Checking.

Same shape as flow 12 (see f12_hc_supervisor_masterlist_checking.py for the full description and the sandbox design), with
host-company fields: two Office Script runs clear the Host Company MasterList template's result tables, every file in
MasterList_RawData_ToBeProcess is read (`Database` table), each row is compared with the Host Company SharePoint list and written
to the template as matched / partly not matched / exactly not matched, then each file triggers a PIC email with the template.

Fix: Try/Catch + Terminate around everything from the first script run to the last email. Matching logic is NOT changed.
Sandbox: identical stubbing to flow 12 (scripts, `Database` rows, five 'Add a row', template read, folder listing); trigger Title
ok | twofiles | scriptfail | addfail | readfail.
"""
import json

from fixes import f12_hc_supervisor_masterlist_checking as f12
from fixes import trycatch as tc

SOURCE_ZIP = "flows/[LIVE-CDO] UTPCSDCDO Host Company Info MasterList Checking.zip"
DISPLAY_NAME = "UTP/CSD/CDO Host Company Info MasterList Checking"
SITE = f12.SITE
TRY = "Try_-_Check_host_companies"
ME = f12.ME
FILES, ROWS, ADDS, INNER = f12.FILES, f12.ROWS, f12.ADDS, f12.INNER

HC = "CDO Sandbox - Host Company"
_FULL = {"TypeofHost": "Company", "Typeofplacement": "Internship", "OrganisationType": "private local", "IndustryType": "IT",
         "HCCity_x002f_Town": "Ipoh", "Postcode": "30000", "HCState_x002f_Country": "Perak"}
_HC = [{"HostCompany_x0028_HC_x0029_Name": "ZZ TEST Exact Co", "HCStreetName": "1 Test Road", **_FULL},
       {"HostCompany_x0028_HC_x0029_Name": "ZZ TEST Partial Co", "HCStreetName": "2 Test Road", **_FULL}]
# stubbed Excel rows: Exact Co (identical), Brand New Co (not in the list), Partial Co (different street)
_ROWS = [{"Host Company ": "ZZ TEST Exact Co", "Type of Host": "Company", "Type of placement": "Internship", "Organisation Type": "private local",
          "Industry Type": "IT", "HC Street Name": "1 Test Road", "HC City / Town": "Ipoh", "Postcode": "30000",
          "HC State / Country": "Perak"},
         {"Host Company ": "ZZ TEST New Co", "Type of Host": "Company", "Type of placement": "Internship", "Organisation Type": "private local",
          "Industry Type": "IT", "HC Street Name": "9 New St", "HC City / Town": "Ipoh", "Postcode": "30000",
          "HC State / Country": "Perak"},
         {"Host Company ": "ZZ TEST Partial Co", "Type of Host": "Company", "Type of placement": "Internship", "Organisation Type": "private local",
          "Industry Type": "IT", "HC Street Name": "99 Other St", "HC City / Town": "Ipoh", "Postcode": "30000",
          "HC State / Country": "Perak"}]
_COUNT = ADDS + ["Send_an_email_(V2)"]
# tools/sandbox/pw.py run 13 <name> baseline|fixed
SCENARIOS = {
    "ok": {"clear": [HC], "seed": {HC: _HC}, "trigger": "ok", "count": _COUNT,
           "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Succeeded"}}},
    "twofiles": {"clear": [HC], "seed": {HC: _HC}, "trigger": "twofiles", "count": _COUNT,
                 "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Succeeded"}}},
    "scriptfail": {"clear": [HC], "seed": {HC: _HC}, "trigger": "scriptfail", "count": _COUNT,
                   "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Failed", "failedAction": "Run_script"}}},
    "addfail": {"clear": [HC], "seed": {HC: _HC}, "trigger": "addfail", "count": _COUNT,
                "expect": {"baseline": {"status": "Succeeded"}, "fixed": {"status": "Failed"}}},
    "readfail": {"clear": [HC], "seed": {HC: _HC}, "trigger": "readfail", "count": ADDS,
                 "expect": {"fixed": {"status": "Failed", "failedAction": "Get_items"}}},
}


def apply(pkg):
    d = pkg.definition
    tc.wrap(d["properties"]["definition"], inner=INNER, try_name=TRY,
            fail_posts=["Post_message_in_a_chat_or_channel_4", "Post_message_in_a_chat_or_channel_5"],
            loops=["Apply_to_each", "Apply_to_each_4"], code="HostCompanyCheckFailed", label="Host Company MasterList Checking")
    pkg.definition = d


def sandboxify(pkg, cfg):
    if cfg.get("_realexcel"):
        return f12._real_excel(pkg, cfg, {"6A8E8DA9": "HostCompany", "08F6F0A2": "ExactlyNotMatched"},
                               "/CDO-Sandbox/F7/Template/Host Company MasterList Template.xlsx")
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
    f12._stub_adds(loop, title)
    inner = a["Apply_to_each_4"]["actions"]
    inner["Get_file_content_using_path"] = {"type": "Compose", "runAfter": {}, "inputs": "stub template workbook"}
    p = inner["Send_an_email_(V2)"]["inputs"]["parameters"]
    p["emailMessage/To"] = ME
    p["emailMessage/Cc"] = ME
    p.pop("emailMessage/Attachments", None)
    a["Delay"]["inputs"]["interval"] = {"count": 1, "unit": "Second"}
    pkg.definition = d
    pkg.remove_connector("shared_excelonlinebusiness")


_T = "Template_HostCompany_MOCK.xlsx"
_F = "RawData_HostCompany_TEST.xlsx"
_ONE = {"HostCompany": {"Matched": 2, "Partially Not Matched": 1}, "ExactlyNotMatched": {"Exactly Not Matched": 1}}
_TWO = {"HostCompany": {"Matched": 4, "Partially Not Matched": 2}, "ExactlyNotMatched": {"Exactly Not Matched": 2}}
for _n, _sc in SCENARIOS.items():
    _sc.update(f12._real_extras(_F, _T, _TWO if _n == "twofiles" else (_ONE if _n == "ok" else {}), two=(_n == "twofiles")))
    _e = _sc.get("expect", {})
    for _k, _v in (("baselinex", "baseline"), ("fixedx", "fixed")):
        if _v in _e:
            _e[_k] = _e[_v]
SCENARIOS["excelfail"] = {
    "clear": [HC], "seed": {HC: _HC}, "trigger": "excelfail", "count": _COUNT, **f12._real_extras(_F, _T, {}),
    "expect": {"baselinex": {"status": "Succeeded"}, "fixedx": {"status": "Failed", "failedAction": "List_rows_present_in_a_table"}}}
